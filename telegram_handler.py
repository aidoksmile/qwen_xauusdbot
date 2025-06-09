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
        
        # Создание директорий если их нет
        os.makedirs('images', exist_ok=True)
        os.makedirs('data', exist_ok=True)
    
    def _setup_handlers(self):
        """Настройка обработчиков команд"""
        dp = self.updater.dispatcher
        dp.add_handler(CommandHandler('start', self.start))
        dp.add_handler(CommandHandler('signal', self.get_signal))
        dp.add_handler(CommandHandler('history', self.get_history))
        dp.add_handler(CommandHandler('accuracy', self.get_accuracy))
        dp.add_handler(CommandHandler('graph', self.send_graph))
    
    def start(self, update, context):
        """Обработчик команды /start"""
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Welcome to XAU Trading Bot! Use /signal to get the latest trading signal.'
        )
    
    def get_signal(self, update, context):
        """Обработчик команды /signal"""
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
                text="No signal generated."
            )
    
    def send_signal(self, signal):
        """Отправка сигнала в Telegram"""
        try:
            # Генерация графика
            plt.figure(figsize=(12, 6))
            plt.plot(signal['data']['Close'][-100:])
            plt.title(f"Signal: {signal['signal']}")
            plt.savefig('images/latest_signal.png')
            plt.close()
            
            # Отправка графика
            with open('images/latest_signal.png', 'rb') as photo:
                self.bot.send_photo(chat_id=self.chat_id, photo=photo)
            
            # Отправка сообщения с уровнями
            self.bot.send_message(
                chat_id=self.chat_id,
                text=self._format_signal(signal),
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error sending signal: {e}")
    
    def _format_signal(self, signal):
        """Форматирование сигнала в Markdown"""
        return f"""
*Signal*: {signal['signal']}
*Entry*: {signal['entry']:.2f}
*TP*: {signal['tp']:.2f}
*SL*: {signal['sl']:.2f}
*Risk*: {signal['risk']:.2f}
*Model Accuracy*: {signal['accuracy']:.2%}
*Timestamp*: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
    
    def _save_signal(self, signal):
        """Сохранение сигнала в историю"""
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
    
    def get_history(self, update, context):
        """Отправка истории сделок"""
        if not os.path.exists(self.history_file):
            context.bot.send_message(chat_id=update.effective_chat.id, text="No trade history found.")
            return
            
        df = pd.read_csv(self.history_file)
        history_text = "📜 *Trade History*\n\n"
        
        for _, trade in df.tail(10).iterrows():
            history_text += f"🕒 {trade['timestamp']}\n"
            history_text += f"📈 {trade['signal']} @ {trade['entry']}\n"
            history_text += f"🎯 TP: {trade['tp']}, SL: {trade['sl']}\n"
            history_text += f"💰 Risk: ${trade['risk']:.2f}\n"
            history_text += f"📊 Accuracy: {trade['accuracy']:.1%}\n\n"
        
        context.bot.send_message(chat_id=update.effective_chat.id, text=history_text, parse_mode='Markdown')
    
    def get_accuracy(self, update, context):
        """Отправка точности модели"""
        accuracy = self.strategy.model.accuracy
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"*Model Accuracy*: {accuracy:.2%}",
            parse_mode='Markdown'
        )
    
    def send_graph(self, update, context):
        """Отправка графика equity"""
        # Здесь можно добавить логику для генерации и отправки графика equity
        context.bot.send_message(chat_id=update.effective_chat.id, text="Equity graph functionality coming soon!")
    
    def start(self):
        """Запуск Telegram-бота"""
        self.updater.start_polling()
        logger.info("Telegram bot started")
