import logging
import telegram
from telegram.ext import Updater, CommandHandler
import matplotlib.pyplot as plt
import pandas as pd
import os
from datetime import datetime
from config import DEBUG

logger = logging.getLogger(__name__)

class TelegramHandler:
    def __init__(self, token, chat_id, strategy, history_file='data/history.csv'):
        """Инициализация Telegram-бота"""
        self.bot = telegram.Bot(token=token)
        self.chat_id = chat_id
        self.strategy = strategy
        self.history_file = history_file
        self.updater = Updater(token=token, use_context=True)
        self._setup_handlers()
        self.signal_history = []
        
        # Создаем необходимые директории
        os.makedirs('images', exist_ok=True)
        os.makedirs('data', exist_ok=True)
    
    def _setup_handlers(self):
        """Настройка обработчиков команд"""
        try:
            dp = self.updater.dispatcher
            dp.add_handler(CommandHandler('start', self.start))
            dp.add_handler(CommandHandler('signal', self.get_signal))
            dp.add_handler(CommandHandler('history', self.get_history))
            dp.add_handler(CommandHandler('accuracy', self.get_accuracy))
            dp.add_handler(CommandHandler('graph', self.send_graph))
        except Exception as e:
            logger.error(f"Ошибка при настройке обработчиков команд: {str(e)}")
    
    def start(self, update, context):
        """Обработчик команды /start"""
        try:
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='Добро пожаловать в XAU Trading Bot! Используйте /signal, чтобы получить последний торговый сигнал.'
            )
        except Exception as e:
            logger.error(f"Ошибка при обработке команды /start: {str(e)}")
    
    def get_signal(self, update, context):
        """Обработчик команды /signal"""
        try:
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
        except Exception as e:
            logger.error(f"Ошибка при обработке команды /signal: {str(e)}")
    
    def send_signal(self, signal):
        """Отправка сигнала в Telegram"""
        try:
            # Генерация графика
            plt.figure(figsize=(12, 6))
            plt.plot(signal['data']['Close'][-100:])
            plt.title(f"Сигнал: {signal['signal']}")
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
            logger.error(f"Ошибка при отправке сигнала: {str(e)}")
    
    def _format_signal(self, signal):
        """Форматирование сигнала в Markdown"""
        try:
            return f"""
*Сигнал*: {signal['signal']}
*Цена входа*: {signal['entry']:.2f}
*Take Profit*: {signal['tp']:.2f}
*Stop Loss*: {signal['sl']:.2f}
*Риск*: {signal['risk']:.2f}
*Точность модели*: {signal['accuracy']:.2%}
*Дата*: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
        except Exception as e:
            logger.error(f"Ошибка при форматировании сигнала: {str(e)}")
            return "Ошибка форматирования сигнала"
    
    def _save_signal(self, signal):
        """Сохранение сигнала в историю"""
        try:
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
        except Exception as e:
            logger.error(f"Ошибка при сохранении сигнала: {str(e)}")
    
    def get_history(self, update, context):
        """Отправка истории сделок"""
        try:
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
                history_text += f"📈 {trade['signal']} @ {trade['entry']}\n"
                history_text += f"🎯 TP: {trade['tp']}, SL: {trade['sl']}\n"
                history_text += f"💰 Риск: ${trade['risk']:.2f}\n"
                history_text += f"📊 Точность: {trade['accuracy']:.1%}\n\n"
            
            context.bot.send_message(chat_id=update.effective_chat.id, text=history_text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Ошибка при получении истории сделок: {str(e)}")
    
    def get_accuracy(self, update, context):
        """Отправка точности модели"""
        try:
            accuracy = self.strategy.model.accuracy if hasattr(self.strategy.model, 'accuracy') else 0
            context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f"*Точность модели*: {accuracy:.2%}",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Ошибка при получении точности модели: {str(e)}")
    
    def send_graph(self, update, context):
        """Отправка графика equity"""
        try:
            # Здесь можно добавить логику для генерации и отправки графика equity
            context.bot.send_message(chat_id=update.effective_chat.id, text="Функционал графика equity в разработке!")
        except Exception as e:
            logger.error(f"Ошибка при отправке графика: {str(e)}")
    
    def start(self):
        """Запуск Telegram-бота"""
        try:
            self.updater.start_polling()
            logger.info("Telegram-бот успешно запущен")
        except Exception as e:
            logger.error(f"Ошибка запуска Telegram-бота: {str(e)}")
