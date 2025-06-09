import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
import joblib
import os
import logging

# Установка кэша перед импортом yfinance
os.environ["PY_YFINANCE_CACHE_DIR"] = "/tmp/yfinance-cache"

logger = logging.getLogger(__name__)

class XAUModel:
    def __init__(self, model_path='models/xau_model.pkl'):
        self.model_path = model_path
        self.model = None
        self.accuracy_threshold = 0.8
        self.load_model()

    def load_model(self):
        """Загрузка сохраненной модели из файла"""
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                logger.info("Модель успешно загружена из файла")
            except Exception as e:
                logger.error(f"Ошибка загрузки модели: {str(e)}")
                self.model = None

    def save_model(self):
        """Сохранение модели в файл"""
        if self.model:
            try:
                joblib.dump(self.model, self.model_path)
                logger.info("Модель успешно сохранена")
            except Exception as e:
                logger.error(f"Ошибка сохранения модели: {str(e)}")

    def prepare_data(self, data):
        """Подготовка данных для обучения модели"""
        try:
            # Добавляем технические индикаторы
            data['target'] = (data['Close'].shift(-5) > data['Close']).astype(int)
            data['SMA_20'] = data['Close'].rolling(20).mean()
            data['RSI'] = self._calculate_rsi(data['Close'])
            data['MACD'] = self._calculate_macd(data['Close'])
            data['ATR'] = self._calculate_atr(data)

            # Убираем пропущенные значения
            data = data.dropna()

            # Выбираем признаки
            features = ['Open', 'High', 'Low', 'Close', 'Volume', 'SMA_20', 'RSI', 'MACD', 'ATR']
            X = data[features].values[:-5]
            y = data['target'].values[:-5]
            return X, y

        except Exception as e:
            logger.error(f"Ошибка при подготовке данных: {str(e)}")
            return np.array([]), np.array([])

    def _calculate_rsi(self, series, period=14):
        """Рассчитываем RSI"""
        delta = series.diff()
        gain = delta.where(delta > 0, 0)
        loss = -delta.where(delta < 0, 0)
        avg_gain = gain.rolling(period).mean()
        avg_loss = loss.rolling(period).mean()
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def _calculate_macd(self, series, fast_period=12, slow_period=26, signal_period=9):
        """Рассчитываем MACD"""
        ema_fast = series.ewm(span=fast_period, adjust=False).mean()
        ema_slow = series.ewm(span=slow_period, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
        return macd_line - signal_line

    def _calculate_atr(self, data, period=14):
        """Рассчитываем ATR"""
        high_low = data['High'] - data['Low']
        high_close = abs(data['High'] - data['Close'].shift())
        low_close = abs(data['Low'] - data['Close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(period).mean()

    def train(self, X, y):
        """Обучение модели с волкфорвард кросс-валидацией"""
        if len(X) < 5:
            logger.error("Недостаточно данных для обучения")
            return 0

        tscv = TimeSeriesSplit(n_splits=5)
        best_acc = 0
        best_model = None

        for train_idx, test_idx in tscv.split(X):
            X_train, X_test = X[train_idx], X[test_idx]
            y_train, y_test = y[train_idx], y[test_idx]

            model = self._build_model(X_train.shape[1])
            model.fit(X_train, y_train, epochs=10, verbose=0)

            pred = (model.predict(X_test) > 0.5).astype(int)
            acc = accuracy_score(y_test, pred)
            logger.info(f"Точность модели на валидации: {acc}")

            if acc > best_acc:
                best_acc = acc
                best_model = model

        self.model = best_model
        self.save_model()
        return best_acc

    def _build_model(self, input_shape):
        """Создание LSTM модели"""
        model = Sequential()
        model.add(LSTM(50, input_shape=(input_shape, 1)))
        model.add(Dense(1, activation='sigmoid'))
        model.compile(loss='binary_crossentropy', optimizer='adam')
        return model

    def predict(self, data):
        """Предсказание на новых данных"""
        if self.model is None:
            logger.error("Модель не обучена")
            return None

        X, _ = self.prepare_data(data.copy())

        if len(X) == 0:
            logger.error("Нет данных для предсказания")
            return None

        prediction = self.model.predict(X[-1].reshape(1, -1, 1))
        return (prediction > 0.5).astype(int)[0][0]
