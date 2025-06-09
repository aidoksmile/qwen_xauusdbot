import os
import yfinance as yf
import pandas as pd
import logging

# Отключаем внутреннее кэширование yfinance
os.environ["PY_YFINANCE_DISABLE_CACHE"] = "1"

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_xau_data():
    """Получает данные по XAU/USD на разных таймфреймах"""
    logger.info("Загрузка данных XAU/USD")
    daily_data = download_data('GC=F', '1d')
    fifteen_min_data = download_data('GC=F', '15m')
    return daily_data, fifteen_min_data

def download_data(symbol='GC=F', interval='1d', retries=3, delay=10):
    """Загружает данные по золоту/доллару"""
    for attempt in range(retries):
        try:
            logger.info(f"Попытка {attempt+1} загрузить данные {symbol} {interval}")
            data = yf.download(tickers=symbol, interval=interval, period='max', progress=False)
            if not data.empty:
                logger.info(f"Успешно загружено {len(data)} строк для {symbol} {interval}")
                return data
            time.sleep(delay)
        except Exception as e:
            logger.error(f"Ошибка загрузки {symbol} {interval}: {str(e)}")
            time.sleep(delay)
    logger.error(f"Не удалось загрузить данные для {symbol} после {retries} попыток")
    return pd.DataFrame()
