import logging
import pandas as pd
import numpy as np
from config import RISK_PERCENT, DEBUG

logger = logging.getLogger(__name__)

class XAUTradingStrategy:
    def __init__(self, model):
        """Инициализация торговой стратегии"""
        self.model = model
        self.risk_percent = RISK_PERCENT
    
    def generate_signal(self, daily_data, fifteen_min_data):
        """
        Генерация торгового сигнала
        
        Args:
            daily_data: Дневные данные
            fifteen_min_data: 15-минутные данные
            
        Returns:
            dict: Сигнал с уровнями входа, стоп-лосса и тейк-профита
        """
        try:
            # Получаем предсказание от модели
            prediction = self.model.predict(daily_data)
            
            if prediction is None:
                logger.error("Модель не обучена")
                return None
                
            signal = 'BUY' if prediction == 1 else 'SELL'
            current_price = fifteen_min_data['Close'][-1]
            
            # Определяем тренд на младшем ТФ
            recent_data = fifteen_min_data[-100:]
            trend = self._determine_trend(recent_data)
            
            # Проверяем, соответствует ли сигнал тренду
            if not self._validate_signal(signal, trend):
                logger.info(f"Сигнал отклонен из-за несоответствия тренду: {signal} vs {trend}")
                return None
                
            # Расчет уровней
            atr = self._calculate_atr(fifteen_min_data)
            sl_multiplier = 1.5
            tp_multiplier = 2
            
            if signal == 'BUY':
                sl = current_price * (1 - sl_multiplier * self.risk_percent / 100)
                tp = current_price + (current_price - sl) * tp_multiplier
            else:  # SELL
                sl = current_price * (1 + sl_multiplier * self.risk_percent / 100)
                tp = current_price - (sl - current_price) * tp_multiplier
                
            risk = self.risk_percent * current_price / 100
            
            return {
                'signal': signal,
                'entry': current_price,
                'tp': tp,
                'sl': sl,
                'risk': risk,
                'atr': atr,
                'accuracy': self.model.accuracy if hasattr(self.model, 'accuracy') else 0,
                'data': fifteen_min_data  # Для отрисовки графика
            }
            
        except Exception as e:
            logger.error(f"Ошибка при генерации сигнала: {str(e)}")
            return None
    
    def _determine_trend(self, data, window=20):
        """Определение тренда на младшем ТФ"""
        try:
            sma = data['Close'].rolling(window).mean()
            last_price = data['Close'][-1]
            
            if last_price > sma[-1]:
                return 'UP'
            elif last_price < sma[-1]:
                return 'DOWN'
            else:
                return 'SIDEWAYS'
        except Exception as e:
            logger.error(f"Ошибка при определении тренда: {str(e)}")
            return 'UNKNOWN'
    
    def _validate_signal(self, signal, trend):
        """Проверка соответствия сигнала тренду"""
        try:
            if signal == 'BUY' and trend == 'UP':
                return True
            elif signal == 'SELL' and trend == 'DOWN':
                return True
            return False
        except Exception as e:
            logger.error(f"Ошибка при валидации сигнала: {str(e)}")
            return False
    
    def _calculate_atr(self, data, period=14):
        """Рассчитываем ATR"""
        try:
            high_low = data['High'] - data['Low']
            high_close = abs(data['High'] - data['Close'].shift())
            low_close = abs(data['Low'] - data['Close'].shift())
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            return tr.rolling(period).mean().iloc[-1]
        except Exception as e:
            logger.error(f"Ошибка при расчете ATR: {str(e)}")
            return 0
