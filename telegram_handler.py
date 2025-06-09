import os
import telegram
from telegram.ext import Updater, CommandHandler
import matplotlib.pyplot as plt
import pandas as pd
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class TelegramHandler:
    def __init__(self, token, chat_id, strategy, history_file='data/history.csv'):
        self.bot = telegram.Bot(token=token)
        self.chat_id = chat_id
        self.strategy = strategy
        self.updater = Updater(bot=self.bot)
        self._setup_handlers()
        self.signal_history = []

    def _setup_handlers(self):
        dp = self.updater.dispatcher
        dp.add_handler(CommandHandler('start', self.start))
        dp.add_handler(CommandHandler('signal', self.get_signal))

    def start(self, update, context):
        context.bot.send_message(chat_id=update.effective_chat.id, text="XAU Trading Bot запущен!")

    def get_signal(self, update, context):
        daily, fifteen_min = get_xau_data()
        signal = self.strategy.generate_signal(daily, fifteen_min)
        if signal:
            self.send_signal(signal)
            self._save_signal(signal)
            update.message.reply_text(self._format_signal(signal), parse_mode='Markdown')
        else:
            update.message.reply_text("Сигнал не найден.")

    def send_signal(self, signal):
        plt.figure(figsize=(12, 6))
        plt.plot(signal['data']['Close'][-100:])
        plt.title(f"Signal: {signal['signal']}")
        plt.savefig('images/latest_signal.png')
        plt.close()

        try:
            with open('images/latest_signal.png', 'rb') as photo:
                self.bot.send_photo(chat_id=self.chat_id, photo=photo)
            self.bot.send_message(chat_id=self.chat_id, text=self._format_signal(signal), parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Ошибка отправки сигнала: {e}")

    def _format_signal(self, signal):
        return f"*Сигнал*: {signal['signal']}\n*Цена входа*: {signal['entry']:.2f}\n*Take Profit*: {signal['tp']:.2f}\n*Stop Loss*: {signal['sl']:.2f}"

    def _save_signal(self, signal):
        df = pd.DataFrame([{
            'timestamp': datetime.now(),
            'signal': signal['signal'],
            'entry': signal['entry'],
            'tp': signal['tp'],
            'sl': signal['sl'],
            'risk': signal['risk'],
            'accuracy': signal['accuracy']
        }])
        df.to_csv('data/history.csv', mode='a', header=False, index=False)

    def start(self):
        self.updater.start_polling()
        logger.info("Telegram бот запущен")
