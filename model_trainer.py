import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
import joblib
import os
import logging

logger = logging.getLogger(__name__)

class XAUModel:
    def __init__(self, model_path='models/xau_model.pkl'):
        self.model_path = model_path
        self.model = None
        self.accuracy_threshold = 0.8
        self.load_model()

    def load_model(self):
        if os.path.exists(self.model_path):
            try:
                self.model = joblib.load(self.model_path)
                logger.info("Модель успешно загружена")
            except Exception as e:
                logger.error(f"Ошибка загрузки модели: {e}")

    def save_model(self):
        if self.model:
            try:
                joblib.dump(self.model, self.model_path)
                logger.info("Модель сохранена")
            except Exception as e:
                logger.error(f"Ошибка сохранения модели: {e}")

    def prepare_data(self, data):
        data['target'] = (data['Close'].shift(-5) > data['Close']).astype(int)
        features = ['Open', 'High', 'Low', 'Close', 'Volume']
        X = data[features].values[:-5]
        y = data['target'].values[:-5]
        return X, y

    def train(self, X, y):
        if len(X) < 5:
            logger.error("Недостаточно данных для обучения")
            return 0
        tscv = TimeSeriesSplit(n_splits=5)
        best_acc = 0
        best_model = None
        for train_idx, test_idx in tscv.split(X):
            model = self._build_model(X.shape[1])
            model.fit(X[train_idx], y[train_idx], epochs=10, verbose=0)
            pred = (model.predict(X[test_idx]) > 0.5).astype(int)
            acc = accuracy_score(y[test_idx], pred)
            if acc > best_acc:
                best_acc = acc
                best_model = model
        self.model = best_model
        self.save_model()
        return best_acc

    def _build_model(self, input_shape):
        model = Sequential()
        model.add(LSTM(50, input_shape=(input_shape, 1)))
        model.add(Dense(1, activation='sigmoid'))
        model.compile(loss='binary_crossentropy', optimizer='adam')
        return model

    def predict(self, data):
        if self.model is None:
            logger.error("Модель не обучена")
            return None
        X, _ = self.prepare_data(data.copy())
        if len(X) == 0:
            return None
        prediction = self.model.predict(X[-1].reshape(1, -1, 1))
        return (prediction > 0.5).astype(int)[0][0]
