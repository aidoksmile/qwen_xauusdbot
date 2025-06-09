import yfinance as yf
import pandas as pd
import time
import logging
from config import DEBUG

logger = logging.getLogger(__name__)

def download_data(symbol='GC=F', interval='1d', period='max', retries=3, delay=10):
    """
    Загружает данные по золоту/доллару с yfinance
    
    Args:
        symbol: Тикер актива
        interval: Таймфрейм ('1d' для дневных данных, '15m' для 15-минутных)
        period: Период загрузки ('max' для максимального доступного)
        retries: Количество попыток при неудачной загрузке
        delay: Задержка между попытками (в секундах)
    
    Returns:
        pd.DataFrame: Исторические данные по активу
    """
    for attempt in range(retries):
        try:
            logger.info(f"Попытка {attempt+1} загрузить данные {symbol} {interval}")
            data = yf.download(symbol, interval=interval, period=period)
            
            if not data.empty:
                logger.info(f"Успешно загружено {len(data)} строк для {symbol} {interval}")
                return data
            else:
                logger.warning(f"Пустой ответ при загрузке данных {symbol} {interval}")
            
            time.sleep(delay)
        except Exception as e:
            logger.error(f"Ошибка загрузки {symbol} {interval}: {str(e)}")
            time.sleep(delay)
    
    logger.error(f"Не удалось загрузить данные для {symbol} {interval} после {retries} попыток")
    return pd.DataFrame()

def get_xau_data():
    """
    Получает данные по XAU/USD (золото к доллару) на разных таймфреймах
    
    Returns:
        tuple: (дневные данные, 15-минутные данные)
    """
    logger.info("Загрузка данных XAU/USD")
    daily_data = download_data('GC=F', '1d')
    fifteen_min_data = download_data('GC=F', '15m')
    
    return daily_data, fifteen_min_data
