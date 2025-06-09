import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import logging
from config import DEBUG

logger = logging.getLogger(__name__)

class Backtester:
    def __init__(self, signals=None, returns=None):
        """Инициализация бэктестера"""
        self.signals = signals if signals is not None else []
        self.returns = returns if returns is not None else pd.Series()
    
    def calculate_metrics(self):
        """Рассчитываем метрики стратегии"""
        try:
            if not self.signals or self.returns.empty:
                return {}
            
            # Рассчитываем Win Rate
            win_rate = len(self.returns[self.returns > 0]) / len(self.returns)
            
            # Рассчитываем Profit Factor
            total_profit = self.returns[self.returns > 0].sum()
            total_loss = abs(self.returns[self.returns < 0].sum())
            profit_factor = total_profit / total_loss if total_loss != 0 else float('inf')
            
            # Рассчитываем общий доход
            total_return = self.returns.sum()
            
            # Рассчитываем Sharpe Ratio
            sharpe_ratio = self.returns.mean() / self.returns.std() * np.sqrt(252) if self.returns.std() != 0 else 0
            
            return {
                'win_rate': win_rate,
                'profit_factor': profit_factor,
                'total_return': total_return,
                'sharpe_ratio': sharpe_ratio,
                'trade_count': len(self.returns)
            }
            
        except Exception as e:
            logger.error(f"Ошибка при расчете метрик: {str(e)}")
            return {}
    
    def plot_equity_curve(self, filename='images/equity_curve.png'):
        """Отрисовываем график equity"""
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            plt.figure(figsize=(12, 6))
            self.returns.cumsum().plot()
            plt.title('Кривая капитала')
            plt.xlabel('Сделки')
            plt.ylabel('Доходность')
            plt.grid(True)
            plt.savefig(filename)
            plt.close()
            
            return filename
            
        except Exception as e:
            logger.error(f"Ошибка при построении графика equity: {str(e)}")
            return None
    
    def compare_with_buy_and_hold(self, price_data, filename='images/comparison.png'):
        """Сравнение со стратегией Buy and Hold"""
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            
            # Рассчитываем доходность стратегии
            strategy_returns = self.returns.cumsum()
            
            # Рассчитываем доходность Buy and Hold
            buy_and_hold_returns = (price_data['Close'] / price_data['Close'][0] - 1).loc[strategy_returns.index]
            
            # Строим график сравнения
            plt.figure(figsize=(12, 6))
            strategy_returns.plot(label='Стратегия')
            buy_and_hold_returns.plot(label='Buy and Hold')
            plt.title('Сравнение стратегии с Buy and Hold')
            plt.xlabel('Время')
            plt.ylabel('Доходность')
            plt.legend()
            plt.grid(True)
            plt.savefig(filename)
            plt.close()
            
            return filename
            
        except Exception as e:
            logger.error(f"Ошибка при сравнении с Buy and Hold: {str(e)}")
            return None
