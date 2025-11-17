"""
Mean Reversion Strategy
Uses RSI to identify oversold/overbought conditions for mean reversion trades.
"""

import numpy as np
from typing import Dict
from strategies.base_strategy import BaseStrategy


class MeanReversionStrategy(BaseStrategy):
    """
    RSI-based mean reversion strategy.
    
    Entry Rules:
    - BUY when RSI < oversold_threshold
    - SELL when RSI > overbought_threshold or position exists
    
    Exit Rules:
    - Exit long when RSI > overbought_threshold
    - Stop loss at 5% below entry
    """
    
    def __init__(
        self,
        name: str = "RSI Mean Reversion",
        rsi_period: int = 14,
        rsi_oversold: float = 30,
        rsi_overbought: float = 70
    ):
        super().__init__(name)
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.price_history = []
        self.entry_price = None
        
    def on_data(self, data: Dict):
        """
        Process new market data and generate signals.
        
        Args:
            data: Dict with 'close', 'high', 'low', 'volume' keys
        """
        close_price = data['close']
        self.price_history.append(close_price)
        
        # Need enough history for RSI calculation
        if len(self.price_history) < self.rsi_period + 1:
            return
        
        # Calculate RSI
        rsi = self._calculate_rsi()
        
        # Entry Logic
        if self.position == 0:  # No position
            if rsi < self.rsi_oversold:
                # Oversold - potential buy signal
                size = self.calculate_position_size()
                self.buy(size, price=close_price)
                self.entry_price = close_price
                
        # Exit Logic  
        elif self.position > 0:  # Long position
            # Exit on overbought or stop loss
            if rsi > self.rsi_overbought:
                self.sell(price=close_price)
                self._record_trade(close_price)
                self.entry_price = None
            
            # Stop loss (5% below entry)
            elif self.entry_price and close_price < self.entry_price * 0.95:
                self.sell(price=close_price)
                self._record_trade(close_price)
                self.entry_price = None
    
    def _calculate_rsi(self) -> float:
        """
        Calculate Relative Strength Index.
        
        RSI = 100 - (100 / (1 + RS))
        where RS = Average Gain / Average Loss over period
        """
        prices = np.array(self.price_history[-(self.rsi_period + 1):])
        deltas = np.diff(prices)
        
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains)
        avg_loss = np.mean(losses)
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    def _record_trade(self, exit_price: float):
        """Record completed trade for analysis"""
        if self.entry_price:
            pnl = (exit_price - self.entry_price) * self.position
            return_pct = (exit_price - self.entry_price) / self.entry_price
            
            # Would create Trade object here in full implementation
            # For now, just track in simple list
            self.trades.append({
                'pnl': pnl,
                'return': return_pct,
                'entry': self.entry_price,
                'exit': exit_price
            })
