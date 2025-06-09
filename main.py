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
from config import SIGNAL_CHECK_INTERVAL, MODEL_UPDATE_THRESHOLD, DEBUG

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='logs/trading_bot.log',
    filemode='a'
)
logger = logging.getLogger(__name__)

# Flask приложение
app = Flask(__name__)
port = int(os.environ.get('PORT', 5000))

# Инициализация компонентов
xau_model = XAUModel()
trading_strategy = XAUTradingStrategy(xau_model)

@app.route('/signal', methods=['GET'])
def get_signal():
    """API для получения последнего сигнала"""
    try:
        daily_data, fifteen_min_data = get_xau_data()
        
        if daily_data.empty or fifteen_min_data.empty:
            logger.error("Не удалось загрузить данные")
            return {'error': 'Не удалось загрузить данные'}, 503
            
        signal = trading_strategy.generate_signal(daily_data, fifteen_min_data)
        
        if not signal:
            logger.error("Не удалось сгенерировать сигнал")
            return {'error': 'Не удалось сгенерировать сигнал'}, 503
            
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
        logger.error(f"Ошибка в API: {str(e)}")
        return {'error': 'Внутренняя ошибка сервера'}, 500

def start_flask():
    """Запуск Flask-сервера"""
    try:
        logger.info(f"Запуск Flask-сервера на порту {port}")
        app.run(host='0.0.0.0', port=port)
    except Exception as e:
        logger.error(f"Ошибка запуска Flask-сервера: {str(e)}")

def market_monitor():
    """Фоновый мониторинг рынка"""
    logger.info("Запуск мониторинга рынка")
    
    while True:
        try:
            # Получение данных
            daily_data, fifteen_min_data = get_xau_data()
            
            if daily_data.empty or fifteen_min_data.empty:
                logger.error("Не удалось загрузить последние данные")
                time.sleep(60)
                continue
            
            # Обновление модели при необходимости
            if xau_model.model:
                X, y = xau_model.prepare_data(daily_data)
                
                if len(X) > 0 and len(y) > 0:
                    pred = (xau_model.model.predict(X[-1].reshape(1, -1, 1)) > 0.5).astype(int)
                    accuracy = accuracy_score(y[-1:], pred)
                    
                    if accuracy < MODEL_UPDATE_THRESHOLD:
                        logger.info("Переобучение модели из-за низкой точности")
                        xau_model.train(X, y)
            
            # Генерация и обработка сигнала
            signal = trading_strategy.generate_signal(daily_data, fifteen_min_data)
            
            if signal:
                logger.info(f"Сигнал сгенерирован: {signal}")
                
        except Exception as e:
            logger.error(f"Ошибка в мониторинге рынка: {str(e)}")
        
        # Ожидание 15 минут
        time.sleep(SIGNAL_CHECK_INTERVAL)

if __name__ == '__main__':
    # Запуск Flask в отдельном потоке
    flask_thread = threading.Thread(target=start_flask, daemon=True)
    flask_thread.start()
    
    # Инициализация Telegram-бота
    telegram_token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')
    
    if telegram_token and chat_id:
        telegram_handler = TelegramHandler(telegram_token, chat_id, trading_strategy)
        telegram_handler.start()
        logger.info("Telegram-бот запущен")
        
        # Запуск мониторинга рынка
        market_monitor()
    else:
        logger.error("TELEGRAM_TOKEN или CHAT_ID не установлены")
