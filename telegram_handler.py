import telegram
from telegram.ext import Updater, CommandHandler
import matplotlib.pyplot as plt
import pandas as pd
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def get_xau_data():
    import yfinance as yf
    daily = yf.download('GC=F', interval='1d', period='1y')
    return daily, daily  # Упрощённая реализация для теста

class TelegramHandler:
    def __init__(self, token, chat_id, strategy):
        self.bot = telegram.Bot(token=token)
        self.chat_id = chat_id
        self.strategy = strategy
        self.updater = Updater(bot=self.bot)
        self._setup_handlers()

    def _setup_handlers(self):
        dp = self.updater.dispatcher
        dp.add_handler(CommandHandler('start', self.start))
        dp.add_handler(CommandHandler('signal', self.get_signal))

    def start(self, update, context):
        context.bot.send_message(chat_id=update.effective_chat.id, text="XAU Trading Bot запущен!")

    def get_signal(self, update, context):
        daily_data, fifteen_min_data = get_xau_data()
        signal = self.strategy.generate_signal(daily_data, fifteen_min_data)
        if signal:
            self.send_signal(signal)
            message = self._format_signal(signal)
            context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode='Markdown')
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Сигнал не найден.")

    def send_signal(self, signal):
        try:
            plt.figure(figsize=(12, 6))
            plt.plot(signal['data']['Close'][-100:])
            plt.title(f"Signal: {signal['signal']}")
            plt.grid(True)
            plt.savefig('latest_signal.png')
            plt.close()

            with open('latest_signal.png', 'rb') as photo:
                self.bot.send_photo(chat_id=self.chat_id, photo=photo)

            message = self._format_signal(signal)
            self.bot.send_message(chat_id=self.chat_id, text=message, parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Ошибка при отправке сигнала: {e}")

    def _format_signal(self, signal):
        return f"""
*Сигнал*: {signal['signal']}
*Цена входа*: {signal['entry']:.2f}
*Take Profit*: {signal['tp']:.2f}
*Stop Loss*: {signal['sl']:.2f}
*Риск*: {signal['risk']:.2f}
*Точность модели*: {signal['accuracy']:.2%}
*Дата*: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
