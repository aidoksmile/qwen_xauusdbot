import logging
import telegram
from telegram.ext import Updater, CommandHandler
import matplotlib.pyplot as plt
import pandas as pd
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class TelegramHandler:
    def __init__(self, token, chat_id, strategy, history_file='data/history.csv'):
        self.bot = telegram.Bot(token=token)
        self.chat_id = chat_id
        self.strategy = strategy
        self.history_file = history_file
        self.updater = Updater(token=token, use_context=True)
        self._setup_handlers()
        self.signal_history = []

        os.makedirs('images', exist_ok=True)
        os.makedirs('data', exist_ok=True)

    def _setup_handlers(self):
        dp = self.updater.dispatcher
        dp.add_handler(CommandHandler('start', self.start))
        dp.add_handler(CommandHandler('signal', self.get_signal))
        dp.add_handler(CommandHandler('history', self.get_history))
        dp.add_handler(CommandHandler('accuracy', self.get_accuracy))
        dp.add_handler(CommandHandler('graph', self.send_graph))

    def start(self, update, context):
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Добро пожаловать в XAU Trading Bot! Используйте /signal, чтобы получить последний торговый сигнал.'
        )

    def get_signal(self, update, context):
        daily, fifteen_min = get_xau_data()
        signal = self.strategy.generate_signal(daily, fifteen_min)
        if signal:
            self.send_signal(signal)
            self._save_signal(signal)
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=self._format_signal(signal),
                parse_mode='Markdown'
            )
        else:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Сигнал не сгенерирован."
            )

    def send_signal(self, signal):
        try:
            plt.figure(figsize=(12, 6))
            plt.plot(signal['data']['Close'][-100:])
            plt.title(f"Сигнал: {signal['signal']}")
            plt.savefig('images/latest_signal.png')
            plt.close()

            with open('images/latest_signal.png', 'rb') as photo:
                self.bot.send_photo(chat_id=self.chat_id, photo=photo)

            self.bot.send_message(
                chat_id=self.chat_id,
                text=self._format_signal(signal),
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Ошибка при отправке сигнала: {str(e)}")

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
        df.to_csv(self.history_file, mode='a', header=not os.path.exists(self.history_file), index=False)
