import os
from flask import Flask
from data_loader import get_xau_data
from model_trainer import XAUModel
from strategy import XAUTradingStrategy

app = Flask(__name__)

# Инициализация компонентов
xau_model = XAUModel()
trading_strategy = XAUTradingStrategy(xau_model)

@app.route('/signal', methods=['GET'])
def get_signal():
    """API для получения последнего торгового сигнала"""
    daily_data, fifteen_min_data = get_xau_data()
    if daily_data.empty or fifteen_min_data.empty:
        return {'error': 'Не удалось загрузить данные'}, 503

    signal = trading_strategy.generate_signal(daily_data, fifteen_min_data)
    if not signal:
        return {'error': 'Не удалось сгенерировать сигнал'}, 503

    return {
        'signal': signal['signal'],
        'entry': signal['entry'],
        'tp': signal['tp'],
        'sl': signal['sl'],
        'risk': signal['risk'],
        'accuracy': signal['accuracy'],
        'timestamp': signal.get('timestamp', None)
    }

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    print(f"Запуск Flask-сервера на порту {port}")
    app.run(host="0.0.0.0", port=port)
