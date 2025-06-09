# Конфигурационные параметры для бота

# Параметры модели
MODEL_UPDATE_THRESHOLD = 0.8  # Порог обновления модели (80% точности)
RISK_PERCENT = 2  # Процент риска на сделку
LOOKAHEAD_PERIOD = 5  # Прогноз на 5 дней вперед

# Параметры торговли
MINIMUM_DATA_LENGTH = 100  # Минимальное количество свечей для анализа
SIGNAL_CHECK_INTERVAL = 15 * 60  # Интервал проверки сигналов (в секундах)

# Пути к файлам
MODEL_PATH = 'models/xau_model.pkl'
HISTORY_PATH = 'data/history.csv'
LOG_PATH = 'logs/trading_bot.log'

# Telegram
TELEGRAM_TOKEN_ENV = 'TELEGRAM_TOKEN'
CHAT_ID_ENV = 'CHAT_ID'

# Флаг отладки
DEBUG = False
