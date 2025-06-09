import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

class XAUTradingStrategy:
    def __init__(self, model, risk_percent=2):
        self.model = model
        self.risk_percent = risk_percent

    def generate_signal(self, daily_data, fifteen_min_data):
        prediction = self.model.predict(daily_data)
        if prediction is None:
            return None

        signal = 'BUY' if prediction == 1 else 'SELL'
        current_price = fifteen_min_data['Close'][-1]
        atr = self._calculate_atr(fifteen_min_data)

        sl_multiplier = 1.5
        tp_multiplier = 2

        if signal == 'BUY':
            sl = current_price * (1 - sl_multiplier * self.risk_percent / 100)
            tp = current_price + (current_price - sl) * tp_multiplier
        else:
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
            'data': fifteen_min_data
        }

    def _calculate_atr(self, data, period=14):
        high_low = data['High'] - data['Low']
        high_close = abs(data['High'] - data['Close'].shift())
        low_close = abs(data['Low'] - data['Close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(period).mean().iloc[-1]
