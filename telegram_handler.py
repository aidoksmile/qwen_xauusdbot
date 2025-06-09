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
        """Инициализация Telegram-бота"""
        self.bot = telegram.Bot(token=token)
        self.chat_id = chat_id
        self.strategy = strategy
        self.updater = Updater(bot=self.bot)
        self._setup_handlers()
        self.signal_history = []
        self.history_file = history_file
        os.makedirs(os.path.dirname(history_file), exist_ok=True)

    def _setup_handlers(self):
        """Настройка обработчиков команд"""
        dp = self.updater.dispatcher
        dp.add_handler(CommandHandler('start', self.start))
        dp.add_handler(CommandHandler('signal', self.get_signal))
        dp.add_handler(CommandHandler('history', self.get_history))
        dp.add_handler(CommandHandler('accuracy', self.get_accuracy))

    def start(self, update, context):
        """Обработчик команды /start"""
        context.bot.send_message(chat_id=update.effective_chat.id, text="XAU Trading Bot запущен! Используйте /signal для получения торговых сигналов.")

    def get_signal(self, update, context):
        """Обработчик команды /signal"""
        daily_data, fifteen_min_data = get_xau_data()
        signal = self.strategy.generate_signal(daily_data, fifteen_min_data)
        if signal:
            self.send_signal(signal)
            self._save_signal(signal)
            message = self._format_signal(signal)
            context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode='Markdown')
        else:
            context.bot.send_message(chat_id=update.effective_chat.id, text="Сигнал не найден.")

    def send_signal(self, signal):
        """Отправка сигнала с графиком в Telegram"""
        try:
            # Генерация графика
            plt.figure(figsize=(12, 6))
            plt.plot(signal['data']['Close'][-100:])
            plt.title(f"Signal: {signal['signal']}")
            plt.grid(True)
            plt.savefig('images/latest_signal.png')
            plt.close()

            # Отправка графика
            with open('images/latest_signal.png', 'rb') as photo:
                self.bot.send_photo(chat_id=self.chat_id, photo=photo)

            # Отправка текстового сообщения
            message = self._format_signal(signal)
            self.bot.send_message(chat_id=self.chat_id, text=message, parse_mode='Markdown')

        except Exception as e:
            logger.error(f"Ошибка при отправке сигнала в Telegram: {e}")

    def _format_signal(self, signal):
        """Форматирование сигнала в Markdown"""
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
        """Сохранение сигнала в историю сделок"""
        df = pd.DataFrame([{
            'timestamp': datetime.now(),
            'signal': signal['signal'],
            'entry': signal['entry'],
            'tp': signal['tp'],
            'sl': signal['sl'],
            'risk': signal['risk'],
            'accuracy': signal['accuracy']
        }])
        file_exists = os.path.exists(self.history_file)
        df.to_csv(self.history_file, mode='a', header=not file_exists, index=False)

    def get_history(self, update, context):
        """Отправка истории сделок через команду /history"""
        if not os.path.exists(self.history_file):
            context.bot.send_message(chat_id=update.effective_chat.id, text="История сделок не найдена.")
            return

        df = pd.read_csv(self.history_file)
        if df.empty:
            context.bot.send_message(chat_id=update.effective_chat.id, text="История сделок пуста.")
            return

        history_text = "📜 *История сделок*\n\n"
        for _, trade in df.tail(10).iterrows():
            history_text += f"🕒 {trade['timestamp']}\n"
            history_text += f"📈 {trade['signal']} @ {trade['entry']:.2f}\n"
            history_text += f"🎯 TP: {trade['tp']:.2f}, SL: {trade['sl']:.2f}\n"
            history_text += f"💰 Риск: {trade['risk']:.2f}\n"
            history_text += f"📊 Точность: {trade['accuracy']:.2%}\n\n"

        context.bot.send_message(chat_id=update.effective_chat.id, text=history_text, parse_mode='Markdown')

    def get_accuracy(self, update, context):
        """Отправка точности модели по команде /accuracy"""
        accuracy = self.strategy.model.accuracy if hasattr(self.strategy.model, 'accuracy') else 0
        message = f"*Точность модели*: {accuracy:.2%}"
        context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode='Markdown')

    def start(self):
        """Запуск Telegram-бота"""
        self.updater.start_polling()
        logger.info("Telegram-бот успешно запущен")
