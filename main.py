import os
import time
import logging
import threading
from flask import Flask
from telegram.ext import Updater, CommandHandler
import pandas as pd
from data_loader import get_xau_data
from model_trainer import XAUModel
from strategy import XAUTradingStrategy
from telegram_handler import TelegramHandler

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Flask приложение
app = Flask(__name__)
port = int(os.environ.get('PORT', 5000))

# Инициализация компонентов
xau_model = XAUModel()
trading_strategy = XAUTradingStrategy(xau_model)

# Инициализация Telegram-бота
telegram_token = os.getenv('TELEGRAM_TOKEN')
chat_id = os.getenv('CHAT_ID')
telegram_handler = TelegramHandler(telegram_token, chat_id, trading_strategy)

def start_flask():
    """Запуск Flask-сервера"""
    logger.info(f"Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port)

@app.route('/signal', methods=['GET'])
def get_signal():
    """API для получения последнего сигнала"""
    try:
        daily_data, fifteen_min_data = get_xau_data()
        if daily_data.empty or fifteen_min_data.empty:
            return {'error': 'Failed to fetch data'}, 503
            
        signal = trading_strategy.generate_signal(daily_data, fifteen_min_data)
        if not signal:
            return {'error': 'No signal generated'}, 503
            
        return {
            'signal': signal['signal'],
            'entry': signal['entry'],
            'tp': signal['tp'],
            'sl': signal['sl'],
            'risk': signal['risk'],
            'accuracy': signal['accuracy'],
            'timestamp': pd.Timestamp.now().isoformat()
        }
    except Exception as e:
        logger.error(f"API error: {e}")
        return {'error': 'Internal server error'}, 500

def market_monitor():
    """Фоновый мониторинг рынка"""
    logger.info("Starting market monitor")
    while True:
        try:
            # Получение данных
            daily_data, fifteen_min_data = get_xau_data()
            
            if daily_data.empty or fifteen_min_data.empty:
                logger.error("Failed to fetch latest data")
                time.sleep(60)
                continue
            
            # Обновление модели при необходимости
            if xau_model.model:
                X, y = xau_model.prepare_data(daily_data)
                if len(X) > 0 and len(y) > 0:
                    pred = (xau_model.model.predict(X[-1].reshape(1, -1, 1)) > 0.5).astype(int)
                    accuracy = accuracy_score(y[-1:], pred)
                    if accuracy < xau_model.accuracy_threshold:
                        logger.info("Re-training model due to low accuracy")
                        xau_model.train(X, y)
            
            # Генерация и обработка сигнала
            signal = trading_strategy.generate_signal(daily_data, fifteen_min_data)
            if signal:
                logger.info(f"Signal generated: {signal}")
                telegram_handler.send_signal(signal)
                
        except Exception as e:
            logger.error(f"Error in market monitor: {e}")
        
        # Ожидание 15 минут
        time.sleep(15 * 60)

if __name__ == '__main__':
    # Запуск Flask в отдельном потоке
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()
    
    # Запуск Telegram-бота и фонового монитора
    if telegram_token and chat_id:
        telegram_handler.start()
        logger.info("Telegram bot started")
        
        # Запуск мониторинга рынка
        market_monitor()
    else:
        logger.error("TELEGRAM_TOKEN or CHAT_ID not set")
