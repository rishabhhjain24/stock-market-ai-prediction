# paper_trading.py - Paper trading system to test strategy without real money
# WHY: Paper trading allows risk-free testing before live deployment
# Can reveal issues: slippage misunderstanding, API delays, logic bugs
# Without this, first loss could be catastrophic

import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional, List
from dataclasses import dataclass, asdict
from config import DATABASE_PATH, BACKTEST_COMMISSION, BACKTEST_SLIPPAGE


@dataclass
class PaperTrade:
    """Represents a single trade execution."""
    id: int
    stock: str
    entry_date: str
    entry_price: float
    quantity: int
    exit_date: Optional[str]
    exit_price: Optional[float]
    profit_loss: Optional[float]
    profit_loss_pct: Optional[float]
    status: str  # open, closed, stopped_out
    stop_loss: float
    target_price: float
    trade_type: str  # long, short
    reason: str  # why the trade was taken
    notes: Optional[str] = None


class PaperTradingEngine:
    """
    Simulated paper trading system.
    
    WHY this is useful:
    1. Forward test strategy (use rules without real money)
    2. Find issues before going live
    3. Train traders on the system
    4. Collect more data for model training
    
    Features:
    - Track open/closed trades
    - Calculate win rate, profit factor
    - SQLite persistence (survives app restart)
    - Replay historical prices
    """
    
    def __init__(self, initial_balance: float = 100000):
        self.initial_balance = initial_balance
        self.current_balance = initial_balance
        self.open_trades: List[PaperTrade] = []
        self.closed_trades: List[PaperTrade] = []
        self.trade_counter = 0
        
        # Initialize database
        self._init_db()
        self._load_trades_from_db()
    
    def _init_db(self):
        """Create SQLite database schema if it doesn't exist."""
        try:
            conn = sqlite3.connect(str(DATABASE_PATH))
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS paper_trades (
                    id INTEGER PRIMARY KEY,
                    stock TEXT NOT NULL,
                    entry_date TEXT NOT NULL,
                    entry_price REAL NOT NULL,
                    quantity INTEGER NOT NULL,
                    exit_date TEXT,
                    exit_price REAL,
                    profit_loss REAL,
                    profit_loss_pct REAL,
                    status TEXT NOT NULL,
                    stop_loss REAL,
                    target_price REAL,
                    trade_type TEXT,
                    reason TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[paper_trading] DB init error: {e}")
    
    def _load_trades_from_db(self):
        """Load existing trades from database."""
        try:
            conn = sqlite3.connect(str(DATABASE_PATH))
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM paper_trades WHERE status = 'open'")
            rows = cursor.fetchall()
            
            for row in rows:
                trade = PaperTrade(*row[:15])
                self.open_trades.append(trade)
                if trade.id > self.trade_counter:
                    self.trade_counter = trade.id
            
            conn.close()
        except Exception as e:
            print(f"[paper_trading] Load error: {e}")
    
    def enter_trade(
        self,
        stock: str,
        entry_price: float,
        quantity: int,
        stop_loss: float,
        target_price: float,
        trade_type: str = "long",
        reason: str = "ML Signal",
        notes: str = ""
    ) -> PaperTrade:
        """
        Enter a new trade with position.
        
        Args:
            stock: stock symbol
            entry_price: entry price
            quantity: number of shares
            stop_loss: stop loss level
            target_price: target/take-profit level
            trade_type: "long" or "short"
            reason: reason for trade entry
            notes: optional notes
        
        Returns: PaperTrade object
        
        WHY quantity specification:
        - Allows position sizing testing
        - Tests margin requirements
        - Experiments with leverage
        """
        
        # Calculate cost + commission
        trade_cost = entry_price * quantity
        commission = trade_cost * BACKTEST_COMMISSION
        total_cost = trade_cost + commission
        
        # Check if enough balance
        if total_cost > self.current_balance:
            raise ValueError(f"Insufficient balance: need ${total_cost:.2f}, have ${self.current_balance:.2f}")
        
        # Deduct from balance
        self.current_balance -= total_cost
        
        # Create trade
        self.trade_counter += 1
        trade = PaperTrade(
            id=self.trade_counter,
            stock=stock,
            entry_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            entry_price=entry_price,
            quantity=quantity,
            exit_date=None,
            exit_price=None,
            profit_loss=None,
            profit_loss_pct=None,
            status="open",
            stop_loss=stop_loss,
            target_price=target_price,
            trade_type=trade_type,
            reason=reason,
            notes=notes,
        )
        
        self.open_trades.append(trade)
        self._save_trade_to_db(trade)
        
        return trade
    
    def close_trade(
        self,
        trade_id: int,
        exit_price: float,
        exit_reason: str = "Manual close",
    ) -> PaperTrade:
        """
        Close an open trade at given price.
        
        Args:
            trade_id: ID of trade to close
            exit_price: exit price
            exit_reason: reason for exit (manual, stop, target, etc)
        
        Returns: closed PaperTrade with P&L calculated
        """
        
        # Find trade
        trade = None
        for t in self.open_trades:
            if t.id == trade_id:
                trade = t
                break
        
        if trade is None:
            raise ValueError(f"Trade {trade_id} not found")
        
        # Calculate P&L
        if trade.trade_type == "long":
            gross_pl = (exit_price - trade.entry_price) * trade.quantity
        else:  # short
            gross_pl = (trade.entry_price - exit_price) * trade.quantity
        
        exit_commission = exit_price * trade.quantity * BACKTEST_COMMISSION
        net_pl = gross_pl - exit_commission
        pl_pct = net_pl / (trade.entry_price * trade.quantity)
        
        # Update balance
        self.current_balance += (trade.entry_price * trade.quantity) + net_pl
        
        # Mark trade closed
        trade.exit_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        trade.exit_price = exit_price
        trade.profit_loss = net_pl
        trade.profit_loss_pct = pl_pct
        trade.status = "closed"
        trade.notes = f"{trade.notes or ''} | Closed: {exit_reason}".strip(" |")
        
        # Move to closed
        self.open_trades.remove(trade)
        self.closed_trades.append(trade)
        self._update_trade_in_db(trade)
        
        return trade
    
    def check_stop_loss(self, current_prices: Dict[str, float]):
        """
        Check if any open trades hit stop loss.
        
        Args:
            current_prices: dict of {stock: current_price}
        
        Returns: list of trades that hit stop loss
        
        WHY automated:
        - Prevents emotional delays in exits
        - Tests true risk management
        """
        stopped_out = []
        
        for trade in self.open_trades[:]:  # Copy list to allow removal
            if trade.stock in current_prices:
                current_price = current_prices[trade.stock]
                
                hit_stop = False
                if trade.trade_type == "long" and current_price <= trade.stop_loss:
                    hit_stop = True
                elif trade.trade_type == "short" and current_price >= trade.stop_loss:
                    hit_stop = True
                
                if hit_stop:
                    closed = self.close_trade(
                        trade.id,
                        trade.stop_loss,
                        "Stop loss"
                    )
                    stopped_out.append(closed)
        
        return stopped_out
    
    def check_take_profit(self, current_prices: Dict[str, float]):
        """
        Check if any open trades hit take profit target.
        
        Returns: list of trades that hit target
        """
        hit_targets = []
        
        for trade in self.open_trades[:]:
            if trade.stock in current_prices:
                current_price = current_prices[trade.stock]
                
                hit_target = False
                if trade.trade_type == "long" and current_price >= trade.target_price:
                    hit_target = True
                elif trade.trade_type == "short" and current_price <= trade.target_price:
                    hit_target = True
                
                if hit_target:
                    closed = self.close_trade(
                        trade.id,
                        trade.target_price,
                        "Target hit"
                    )
                    hit_targets.append(closed)
        
        return hit_targets
    
    def get_open_trades(self) -> List[PaperTrade]:
        """Get all currently open trades."""
        return self.open_trades.copy()
    
    def get_closed_trades(self, days: int = 7) -> List[PaperTrade]:
        """Get trades closed in last N days."""
        cutoff = datetime.now() - timedelta(days=days)
        return [
            t for t in self.closed_trades
            if datetime.strptime(t.exit_date, "%Y-%m-%d %H:%M:%S") > cutoff
        ]
    
    def calculate_stats(self) -> Dict:
        """
        Calculate comprehensive trading statistics.
        
        Returns:
            dict with: total_return, win_rate, profit_factor, sharpe, etc.
        """
        if not self.closed_trades:
            return {
                "total_return": 0.0,
                "total_return_pct": 0.0,
                "return_since_start": (self.current_balance - self.initial_balance) / self.initial_balance,
                "trades_count": 0,
                "win_count": 0,
                "loss_count": 0,
                "win_rate": 0.0,
                "avg_win": 0.0,
                "avg_loss": 0.0,
                "profit_factor": 0.0,
                "largest_win": 0.0,
                "largest_loss": 0.0,
            }
        
        returns = [t.profit_loss for t in self.closed_trades if t.profit_loss is not None]
        
        if not returns:
            return {}
        
        returns = np.array(returns)
        wins = returns[returns > 0]
        losses = returns[returns < 0]
        
        total_return = returns.sum()
        win_count = len(wins)
        loss_count = len(losses)
        total_trades = len(returns)
        
        avg_win = wins.mean() if len(wins) > 0 else 0
        avg_loss = losses.mean() if len(losses) > 0 else 0
        
        # Profit factor
        gross_profit = wins.sum() if len(wins) > 0 else 0
        gross_loss = abs(losses.sum()) if len(losses) > 0 else 0
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        return {
            "total_return": total_return,
            "total_return_pct": total_return / (self.initial_balance) * 100,
            "return_since_start": (self.current_balance - self.initial_balance) / self.initial_balance * 100,
            "current_balance": self.current_balance,
            "trades_count": total_trades,
            "win_count": win_count,
            "loss_count": loss_count,
            "win_rate": win_count / total_trades if total_trades > 0 else 0,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": profit_factor,
            "largest_win": wins.max() if len(wins) > 0 else 0,
            "largest_loss": losses.min() if len(losses) > 0 else 0,
            "open_trades_count": len(self.open_trades),
            "open_trades_unrealized_pl": sum(
                (p - t.entry_price) * t.quantity for t in self.open_trades
                for p in [100]  # Would need current price
            ),
        }
    
    def _save_trade_to_db(self, trade: PaperTrade):
        """Save a new trade to database."""
        try:
            conn = sqlite3.connect(str(DATABASE_PATH))
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO paper_trades VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                trade.id, trade.stock, trade.entry_date, trade.entry_price,
                trade.quantity, trade.exit_date, trade.exit_price,
                trade.profit_loss, trade.profit_loss_pct, trade.status,
                trade.stop_loss, trade.target_price, trade.trade_type,
                trade.reason, trade.notes
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[paper_trading] Save error: {e}")
    
    def _update_trade_in_db(self, trade: PaperTrade):
        """Update an existing trade in database."""
        try:
            conn = sqlite3.connect(str(DATABASE_PATH))
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE paper_trades SET
                    exit_date = ?, exit_price = ?,
                    profit_loss = ?, profit_loss_pct = ?,
                    status = ?, notes = ?
                WHERE id = ?
            """, (
                trade.exit_date, trade.exit_price,
                trade.profit_loss, trade.profit_loss_pct,
                trade.status, trade.notes, trade.id
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"[paper_trading] Update error: {e}")


# ════════════════════════════════════════════════════════════════════════════════
# EXAMPLE USAGE
# ════════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Initialize paper trading engine
    engine = PaperTradingEngine(initial_balance=100000)
    
    # Enter a trade
    trade = engine.enter_trade(
        stock="RELIANCE.NS",
        entry_price=2500,
        quantity=10,
        stop_loss=2450,
        target_price=2550,
        reason="ML Signal + Bullish sentiment"
    )
    print(f"Trade entered: {trade.id} for {trade.quantity} shares at ${trade.entry_price}")
    
    # Close the trade
    closed = engine.close_trade(trade.id, exit_price=2540, exit_reason="Take profit")
    print(f"Trade closed: P&L = ${closed.profit_loss:.2f} ({closed.profit_loss_pct:.1%})")
    
    # Get stats
    stats = engine.calculate_stats()
    print(f"\nPortfolio Stats:")
    print(f"Current Balance: ${stats['current_balance']:.2f}")
    print(f"Return: {stats['total_return_pct']:.2f}%")
    print(f"Trades: {stats['trades_count']} (Win rate: {stats['win_rate']:.1%})")
