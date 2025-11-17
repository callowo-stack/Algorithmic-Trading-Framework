"""
Base Strategy Class
All trading strategies inherit from this class.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Trade:
    """Represents a completed trade"""
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    size: float
    pnl: float
    return_pct: float


class BaseStrategy(ABC):
    """
    Abstract base class for all trading strategies.
    
    Implements the core trading loop and provides hooks for
    strategy-specific logic.
    """
    
    def __init__(self, name: str):
        self.name = name
        self.position = 0  # Current position size
        self.trades: List[Trade] = []
        self.equity_curve: List[float] = []
        self.current_capital = 0
        
    @abstractmethod
    def on_data(self, data: Dict):
        """
        Called on each new bar of data.
        
        Args:
            data: Dictionary with 'open', 'high', 'low', 'close', 'volume'
        """
        pass
    
    def buy(self, size: float, price: Optional[float] = None):
        """
        Execute a buy order.
        
        Args:
            size: Number of shares/contracts
            price: Limit price (None for market order)
        """
        self.position += size
        
    def sell(self, size: Optional[float] = None, price: Optional[float] = None):
        """
        Execute a sell order.
        
        Args:
            size: Number of shares/contracts (None = close entire position)
            price: Limit price (None for market order)
        """
        if size is None:
            size = self.position
        self.position -= size
    
    def calculate_position_size(self, risk_per_trade: float = 0.02) -> float:
        """
        Calculate position size based on risk parameters.
        
        Args:
            risk_per_trade: Fraction of capital to risk (default 2%)
            
        Returns:
            Position size in shares/contracts
        """
        risk_amount = self.current_capital * risk_per_trade
        # Simple fixed-fractional sizing
        # In production, incorporate stop-loss distance
        return risk_amount / 100  # Placeholder logic
    
    def get_metrics(self) -> Dict:
        """Calculate strategy performance metrics"""
        if not self.trades:
            return {"total_trades": 0}
        
        winning_trades = [t for t in self.trades if t.pnl > 0]
        losing_trades = [t for t in self.trades if t.pnl < 0]
        
        total_pnl = sum(t.pnl for t in self.trades)
        win_rate = len(winning_trades) / len(self.trades)
        
        avg_win = sum(t.pnl for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t.pnl for t in losing_trades) / len(losing_trades) if losing_trades else 0
        
        return {
            "total_trades": len(self.trades),
            "winning_trades": len(winning_trades),
            "losing_trades": len(losing_trades),
            "win_rate": round(win_rate, 3),
            "total_pnl": round(total_pnl, 2),
            "average_win": round(avg_win, 2),
            "average_loss": round(avg_loss, 2),
        }
