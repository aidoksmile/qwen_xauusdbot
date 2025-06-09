import os
import time
import logging
from data_loader import get_xau_data
from model_trainer import XAUModel
from strategy import XAUTradingStrategy

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_background_monitor():
    xau_model = XAUModel()
    trading_strategy = XAUTradingStrategy(xau_model)

    telegram_token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('CHAT_ID')

    if telegram_token and chat_id:
        try:
            from telegram.ext import Updater
            from telegram_handler import TelegramHandler

            # Инициализация Telegram-бота
            telegram_handler = TelegramHandler(telegram_token, chat_id, trading_strategy)
            telegram_handler.start()
            logging.info("Telegram-бот запущен")

            while True:
                try:
                    daily_data, fifteen_min_data = get_xau_data()

                    if not daily_data.empty and not fifteen_min_data.empty:
                        signal = trading_strategy.generate_signal(daily_data, fifteen_min_data)
                        if signal:
                            logging.info(f"Сигнал сгенерирован: {signal['signal']}")
                            telegram_handler.send_signal(signal)
                        else:
                            logging.info("Сигнал не найден")
                    else:
                        logging.warning("Нет данных для генерации сигнала")

                except Exception as e:
                    logging.error(f"Ошибка в цикле мониторинга: {e}")

                # Ждём 15 минут перед следующей проверкой
                time.sleep(15 * 60)

        except Exception as e:
            logging.error(f"Критическая ошибка: {e}")
    else:
        logging.error("TELEGRAM_TOKEN или CHAT_ID не установлены")

if __name__ == '__main__':
    run_background_monitor()
