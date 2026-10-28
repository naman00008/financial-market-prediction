import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

class Backtester:
    """
    A simple historical simulation engine for the next-day directional classification strategy.
    
    Assumptions:
    - Target: 1 means predicting Close_{t+1} > Close_t.
    - Entry: If prediction is 1, buy at Open_{t+1}.
    - Exit: Sell at Close_{t+1}.
    - This is an intraday position to strictly align with the next-day directional prediction.
    - If a gap is preferred (buy at Close_t), it requires assuming we can trade exactly at Close_t.
      For realism in daily data, we assume trading at Open_{t+1} to Close_{t+1} (Intraday Return),
      or Close_t to Close_{t+1} (Daily Return) if we can trade at the exact close.
    """
    
    def __init__(self, df, predictions, transaction_cost=0.001, trade_on='close_to_close'):
        """
        Args:
            df: DataFrame containing at least 'Date', 'Open', 'Close' for the test period.
            predictions: Array of binary predictions (1 for UP, 0 for DOWN) corresponding to the rows in df.
            transaction_cost: Fractional cost per trade (e.g., 0.001 for 0.1%).
            trade_on: 'close_to_close' (Buy at Close_t, Sell at Close_{t+1}) 
                      or 'open_to_close' (Buy at Open_{t+1}, Sell at Close_{t+1}).
        """
        self.df = df.copy()
        
        # Ensure Date is sorted
        if 'Date' in self.df.columns:
            self.df = self.df.sort_values('Date').reset_index(drop=True)
            
        self.predictions = predictions
        self.transaction_cost = transaction_cost
        self.trade_on = trade_on
        
        # Calculate possible returns for the next day
        if self.trade_on == 'close_to_close':
            # (Close_{t+1} - Close_t) / Close_t
            self.df['Strategy_Base_Return'] = self.df['Close'].pct_change().shift(-1)
        elif self.trade_on == 'open_to_close':
            # (Close_{t+1} - Open_{t+1}) / Open_{t+1}
            self.df['Strategy_Base_Return'] = (self.df['Close'].shift(-1) - self.df['Open'].shift(-1)) / self.df['Open'].shift(-1)
        else:
            raise ValueError("trade_on must be 'close_to_close' or 'open_to_close'")
            
        # The last row won't have a next day to calculate return for
        self.df.loc[self.df.index[-1], 'Strategy_Base_Return'] = 0.0
        
    def run(self):
        """
        Executes the backtest and returns a DataFrame with the equity curve and trade logs.
        """
        # Align predictions with the DataFrame
        self.df['Signal'] = self.predictions
        
        # Calculate Strategy Return
        # We only realize the return if Signal is 1 (UP)
        # We also subtract transaction costs. (1 cost for entry, 1 for exit = 2 * cost per round trip)
        round_trip_cost = 2 * self.transaction_cost
        
        # Vectorized backtest
        self.df['Strategy_Return'] = np.where(
            self.df['Signal'] == 1, 
            self.df['Strategy_Base_Return'] - round_trip_cost, 
            0.0
        )
        
        # Buy and Hold Baseline Return (always in the market)
        self.df['Buy_Hold_Return'] = self.df['Strategy_Base_Return']
        
        # Calculate Equity Curves (starting at 1.0)
        self.df['Strategy_Equity'] = (1 + self.df['Strategy_Return']).cumprod()
        self.df['Buy_Hold_Equity'] = (1 + self.df['Buy_Hold_Return']).cumprod()
        
        return self.df
        
    def get_metrics(self):
        """
        Calculates standard financial metrics for the strategy vs Buy and Hold.
        """
        strategy_returns = self.df['Strategy_Return']
        buy_hold_returns = self.df['Buy_Hold_Return']
        
        metrics = {
            'Strategy': self._calculate_metrics(strategy_returns),
            'Buy_Hold': self._calculate_metrics(buy_hold_returns)
        }
        
        return pd.DataFrame(metrics).round(4)
        
    def _calculate_metrics(self, returns):
        """Helper to calculate performance metrics from a returns series."""
        total_return = (1 + returns).prod() - 1
        
        # Assuming 252 trading days in a year
        annualized_return = (1 + total_return) ** (252 / max(1, len(returns))) - 1
        
        annualized_volatility = returns.std() * np.sqrt(252)
        
        # Sharpe Ratio (assuming risk-free rate of 0 for simplicity)
        if annualized_volatility > 0:
            sharpe_ratio = annualized_return / annualized_volatility
        else:
            sharpe_ratio = 0.0
            
        # Maximum Drawdown
        cumulative_returns = (1 + returns).cumprod()
        rolling_max = cumulative_returns.cummax()
        drawdown = (cumulative_returns - rolling_max) / rolling_max
        max_drawdown = drawdown.min()
        
        # Win Rate (percentage of positive return days out of all traded days)
        traded_days = returns[returns != 0]
        if len(traded_days) > 0:
            win_rate = len(traded_days[traded_days > 0]) / len(traded_days)
        else:
            win_rate = 0.0
            
        return {
            'Total Return': total_return,
            'Annualized Return': annualized_return,
            'Annualized Volatility': annualized_volatility,
            'Sharpe Ratio': sharpe_ratio,
            'Max Drawdown': max_drawdown,
            'Win Rate': win_rate,
            'Trades Executed': len(traded_days)
        }

    def plot_equity_curve(self, save_path=None):
        """Plots the equity curve of the Strategy vs Buy and Hold."""
        plt.figure(figsize=(12, 6))
        
        if 'Date' in self.df.columns:
            plt.plot(self.df['Date'], self.df['Strategy_Equity'], label='ML Strategy', linewidth=2)
            plt.plot(self.df['Date'], self.df['Buy_Hold_Equity'], label='Buy & Hold', alpha=0.7)
            plt.xlabel('Date')
        else:
            plt.plot(self.df.index, self.df['Strategy_Equity'], label='ML Strategy', linewidth=2)
            plt.plot(self.df.index, self.df['Buy_Hold_Equity'], label='Buy & Hold', alpha=0.7)
            plt.xlabel('Trade Step')
            
        plt.title('Strategy vs Buy & Hold Equity Curve')
        plt.ylabel('Cumulative Equity')
        plt.legend()
        plt.grid(True, alpha=0.3)
        
        if save_path:
            plt.savefig(save_path, bbox_inches='tight')
            plt.close()
        else:
            plt.show()
