"""
Simple Moving Average Crossover Backtest Example

This demonstrates a basic momentum strategy using SMA crossovers.
When the fast SMA crosses above the slow SMA, we buy (bullish signal).
When the fast SMA crosses below the slow SMA, we sell (bearish signal).
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta


class SimpleBacktester:
    """
    Minimal backtest engine for demonstrating strategy logic.
    
    In production, you'd want more sophisticated features:
    - Slippage modeling
    - Commission tracking
    - Portfolio management
    - Risk controls
    """
    
    def __init__(self, initial_capital=10000, commission=0.001):
        self.initial_capital = initial_capital
        self.commission = commission
        self.reset()
    
    def reset(self):
        """Reset backtest state"""
        self.capital = self.initial_capital
        self.position = 0  # shares held
        self.trades = []
        self.equity_curve = []
    
    def execute_trade(self, price, shares, timestamp):
        """Execute a buy or sell trade"""
        cost = abs(shares * price)
        commission_cost = cost * self.commission
        
        if shares > 0:  # Buy
            total_cost = cost + commission_cost
            if total_cost <= self.capital:
                self.capital -= total_cost
                self.position += shares
                self.trades.append({
                    'timestamp': timestamp,
                    'type': 'BUY',
                    'price': price,
                    'shares': shares,
                    'cost': total_cost
                })
        else:  # Sell
            shares_to_sell = abs(shares)
            if shares_to_sell <= self.position:
                proceeds = cost - commission_cost
                self.capital += proceeds
                self.position -= shares_to_sell
                self.trades.append({
                    'timestamp': timestamp,
                    'type': 'SELL',
                    'price': price,
                    'shares': shares_to_sell,
                    'proceeds': proceeds
                })
    
    def get_portfolio_value(self, current_price):
        """Calculate total portfolio value"""
        return self.capital + (self.position * current_price)


def calculate_sma(prices, period):
    """Calculate Simple Moving Average"""
    return prices.rolling(window=period).mean()


def run_sma_crossover_backtest(data, fast_period=20, slow_period=50):
    """
    Run SMA crossover strategy backtest
    
    Args:
        data: DataFrame with 'close' prices
        fast_period: Fast SMA period
        slow_period: Slow SMA period
    
    Returns:
        Dictionary with backtest results
    """
    # Calculate SMAs
    data['sma_fast'] = calculate_sma(data['close'], fast_period)
    data['sma_slow'] = calculate_sma(data['close'], slow_period)
    
    # Generate signals
    data['signal'] = 0
    data.loc[data['sma_fast'] > data['sma_slow'], 'signal'] = 1  # Bullish
    data.loc[data['sma_fast'] < data['sma_slow'], 'signal'] = -1  # Bearish
    
    # Detect crossovers (signal changes)
    data['position'] = data['signal'].diff()
    
    # Initialize backtester
    backtester = SimpleBacktester(initial_capital=10000, commission=0.001)
    
    # Execute trades on crossovers
    for idx, row in data.iterrows():
        if pd.notna(row['position']) and row['position'] != 0:
            if row['position'] > 0:  # Buy signal
                # Buy with 50% of capital
                shares_to_buy = (backtester.capital * 0.5) // row['close']
                if shares_to_buy > 0:
                    backtester.execute_trade(row['close'], shares_to_buy, idx)
            
            elif row['position'] < 0:  # Sell signal
                # Sell all shares
                if backtester.position > 0:
                    backtester.execute_trade(row['close'], -backtester.position, idx)
        
        # Track equity curve
        portfolio_value = backtester.get_portfolio_value(row['close'])
        backtester.equity_curve.append({
            'timestamp': idx,
            'value': portfolio_value
        })
    
    # Calculate performance metrics
    equity_curve_df = pd.DataFrame(backtester.equity_curve)
    final_value = equity_curve_df['value'].iloc[-1]
    total_return = (final_value - backtester.initial_capital) / backtester.initial_capital
    
    # Calculate max drawdown
    running_max = equity_curve_df['value'].expanding().max()
    drawdown = (equity_curve_df['value'] - running_max) / running_max
    max_drawdown = drawdown.min()
    
    # Win rate
    winning_trades = sum(1 for t in backtester.trades if t['type'] == 'SELL' and 
                        t.get('proceeds', 0) > t.get('cost', float('inf')))
    total_trades = len([t for t in backtester.trades if t['type'] == 'SELL'])
    win_rate = winning_trades / total_trades if total_trades > 0 else 0
    
    return {
        'initial_capital': backtester.initial_capital,
        'final_value': final_value,
        'total_return': total_return,
        'max_drawdown': max_drawdown,
        'total_trades': len(backtester.trades),
        'win_rate': win_rate,
        'equity_curve': equity_curve_df,
        'trades': backtester.trades
    }


def generate_sample_data(days=365):
    """
    Generate sample OHLCV data for demonstration.
    In production, use real market data.
    """
    dates = pd.date_range(start='2023-01-01', periods=days, freq='D')
    
    # Generate random walk price data
    np.random.seed(42)
    returns = np.random.normal(0.0005, 0.02, days)
    prices = 100 * np.exp(np.cumsum(returns))
    
    df = pd.DataFrame({
        'timestamp': dates,
        'open': prices * 0.995,
        'high': prices * 1.015,
        'low': prices * 0.985,
        'close': prices,
        'volume': np.random.randint(1000000, 5000000, days)
    })
    df.set_index('timestamp', inplace=True)
    
    return df


if __name__ == "__main__":
    print("=" * 60)
    print("SMA Crossover Strategy Backtest")
    print("=" * 60)
    print()
    
    # Generate sample data
    print("📊 Generating sample market data...")
    data = generate_sample_data(days=365)
    print(f"   Data period: {data.index[0].date()} to {data.index[-1].date()}")
    print(f"   Starting price: ${data['close'].iloc[0]:.2f}")
    print(f"   Ending price: ${data['close'].iloc[-1]:.2f}")
    print()
    
    # Run backtest
    print("🔄 Running backtest...")
    results = run_sma_crossover_backtest(
        data, 
        fast_period=20, 
        slow_period=50
    )
    
    # Display results
    print()
    print("📈 Backtest Results:")
    print("-" * 60)
    print(f"   Initial Capital: ${results['initial_capital']:,.2f}")
    print(f"   Final Value: ${results['final_value']:,.2f}")
    print(f"   Total Return: {results['total_return']:.2%}")
    print(f"   Max Drawdown: {results['max_drawdown']:.2%}")
    print(f"   Total Trades: {results['total_trades']}")
    print(f"   Win Rate: {results['win_rate']:.1%}")
    print()
    
    # Interpretation
    if results['total_return'] > 0.2:
        print("✅ Strong performance - strategy shows promise")
    elif results['total_return'] > 0:
        print("⚠️  Positive but modest returns")
    else:
        print("🛑 Negative returns - needs optimization")
    
    print()
    print("=" * 60)
    print()
    print("Note: This uses simulated data. Test with real market data")
    print("before deploying any strategy.")
    print()
