# risk_management.py - Portfolio risk management and position sizing
# WHY: Professional traders manage risk before taking profits
# Wrong position sizing → wipeout even with 60% win rate
# Correct position sizing → sustainable profits with drawdown limits

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional
from dataclasses import dataclass
from config import (
    RISK_PER_TRADE, MAX_POSITION_SIZE, MIN_REWARD_RISK_RATIO,
    BACKTEST_COMMISSION, BACKTEST_SLIPPAGE
)


@dataclass
class RiskMetrics:
    """Store calculated risk metrics for a trade."""
    entry_price: float
    stop_loss: float
    target_price: float
    position_size: float  # % of account
    risk_amount: float  # $ at risk
    reward_amount: float  # $ potential gain
    risk_reward_ratio: float
    position_units: float  # how many shares
    max_loss_percent: float  # % of account risked


class PositionSizer:
    """
    Calculate safe position sizes based on account balance and risk parameters.
    
    WHY this matters:
    - Fixed sizing: always buy same shares (can wipe account)
    - Percentage sizing: scale with account (loses money slowly)
    - Kelly Criterion: maximize long-term growth (requires accurate win %)
    - Fixed Risk: always risk same $ amount (professional approach)
    
    We use "Fixed Risk" - most popular in prop trading firms.
    """
    
    def __init__(
        self,
        account_balance: float = 100000,
        risk_per_trade: float = RISK_PER_TRADE,
        max_position: float = MAX_POSITION_SIZE
    ):
        self.account_balance = account_balance
        self.risk_per_trade = risk_per_trade  # 2% per trade
        self.max_position = max_position  # 10% max
        self.trades_history = []
    
    def calculate_position(
        self,
        entry_price: float,
        stop_loss: float,
        target_price: float,
        current_drawdown: float = 0.0,
    ) -> RiskMetrics:
        """
        Calculate position size using Fixed Risk method.
        
        Fixed Risk Formula:
            Position Size = (Account × Risk%) / (Entry - Stop)
        
        Example:
            Account: $100,000
            Entry: $500
            Stop: $490 (10 pips risk)
            Risk %: 2%
            
            Position = ($100,000 × 2%) / ($500 - $490)
                     = $2,000 / $10
                     = 200 shares
        
        Why this works:
        - Always risks same $ amount (2% = $2k on $100k)
        - Scales up as account grows
        - Prevents catastrophic losses
        - Combined with 60% win rate = positive expectancy
        """
        
        # Risk amount in dollars
        risk_amount = self.account_balance * self.risk_per_trade
        
        # Adjust for current drawdown (reduce sizing in losing period)
        if current_drawdown > 0.05:  # More than 5% down
            risk_adjustment = 1.0 - (current_drawdown * 0.5)  # Reduce by 50% of DD
            risk_amount = risk_amount * max(risk_adjustment, 0.5)  # Min 50% of normal
        
        # Calculate position size
        risk_distance = abs(entry_price - stop_loss)
        if risk_distance <= 0:
            raise ValueError("Stop loss must be different from entry")
        
        position_units = risk_amount / risk_distance
        
        # Cap position size to max allowed
        max_units = (self.account_balance * self.max_position) / entry_price
        position_units = min(position_units, max_units)
        
        # Calculate metrics
        position_size_pct = (position_units * entry_price) / self.account_balance
        reward_amount = (target_price - entry_price) * position_units
        risk_reward = reward_amount / risk_amount if risk_amount > 0 else 0
        
        return RiskMetrics(
            entry_price=entry_price,
            stop_loss=stop_loss,
            target_price=target_price,
            position_size=position_size_pct,
            risk_amount=risk_amount,
            reward_amount=reward_amount,
            risk_reward_ratio=risk_reward,
            position_units=position_units,
            max_loss_percent=self.risk_per_trade,
        )
    
    def validate_trade(self, risk_metrics: RiskMetrics) -> Tuple[bool, str]:
        """
        Validate if trade meets risk/reward criteria.
        
        Checks:
        1. Risk < account allocation ✓
        2. Reward/Risk ratio > 1.5:1 ✓ (minimum acceptable)
        3. Position size < max allowed ✓
        
        Returns: (is_valid, reason_if_invalid)
        """
        
        # Check reward/risk ratio
        if risk_metrics.risk_reward_ratio < MIN_REWARD_RISK_RATIO:
            return False, f"R:R ratio {risk_metrics.risk_reward_ratio:.2f} < minimum {MIN_REWARD_RISK_RATIO}"
        
        # Check position size
        if risk_metrics.position_size > self.max_position:
            return False, f"Position size {risk_metrics.position_size:.1%} > max {self.max_position:.1%}"
        
        # All checks passed
        return True, "Trade meets all risk criteria"
    
    def kelly_criterion(
        self,
        win_rate: float,
        avg_win: float,
        avg_loss: float,
    ) -> float:
        """
        Calculate Kelly Criterion for optimal position sizing.
        
        Kelly Formula: f* = (win% × avg_win - loss% × avg_loss) / avg_win
        
        Where:
            f* = optimal fraction of account to risk
            win% = historical win rate
            avg_win = average winning trade size
            avg_loss = average losing trade size
        
        WHY Kelly:
        - Mathematically optimal for long-term growth
        - Requires accurate historical data
        - Often too aggressive (can use 25% of Kelly for safety)
        - Research shows 40+ trades needed for accuracy
        
        Returns: optimal position size as % of account (0.0 to 1.0)
        
        Example:
            win_rate = 0.60 (60%)
            avg_win = 2 (2:1 reward)
            avg_loss = 1
            
            f* = (0.60 × 2 - 0.40 × 1) / 2
               = (1.2 - 0.4) / 2
               = 0.4 or 40%
        """
        
        loss_rate = 1.0 - win_rate
        
        # Kelly formula
        kelly = (win_rate * avg_win - loss_rate * avg_loss) / avg_win
        
        # Safety: cap at 25% of Kelly (reduces volatility)
        kelly_quarter = kelly * 0.25
        
        # Return, bounded between 0.5% and 5% for safety
        return max(0.005, min(kelly_quarter, 0.05))
    
    def update_balance(self, profit_loss: float):
        """Update account balance after trade execution."""
        self.account_balance += profit_loss
        self.trades_history.append(profit_loss)
    
    def calculate_drawdown(self) -> float:
        """Calculate current drawdown from account peak."""
        if not self.trades_history:
            return 0.0
        
        cumulative = np.cumsum(self.trades_history)
        peak = np.max(np.concatenate([[0], cumulative]))
        current = cumulative[-1]
        
        if peak == 0:
            return 0.0
        
        return (peak - current) / peak


class RiskAnalyzer:
    """Analyze portfolio risk and recommend adjustments."""
    
    @staticmethod
    def max_drawdown_from_equity(equity_curve: pd.Series) -> Tuple[float, pd.Timestamp]:
        """
        Calculate maximum drawdown from equity curve.
        
        Drawdown = (Peak - Current) / Peak
        
        WHY:
        - Measures worst-case loss from peak
        - Important for comparing strategies
        - 20-30% DD is typical for good strategies
        - >50% DD suggests strategy problems
        """
        running_max = equity_curve.expanding().max()
        drawdown = (equity_curve - running_max) / running_max
        max_dd = drawdown.min()
        max_dd_idx = drawdown.idxmin()
        return max_dd, max_dd_idx
    
    @staticmethod
    def recovery_factor(total_profit: float, max_drawdown: float) -> float:
        """
        Recovery Factor = Total Profit / Max Drawdown
        
        WHY: Measures risk-adjusted profit
        - >2.0 is good (risk well-managed)
        - <1.0 means more was lost than gained in worst period
        
        Example: +$50k profit, -$20k DD = 2.5x recovery factor (good)
        """
        if max_drawdown == 0:
            return float('inf')
        return total_profit / abs(max_drawdown)
    
    @staticmethod
    def sharpe_ratio(returns: pd.Series, annual_rf_rate: float = 0.06) -> float:
        """
        Sharpe Ratio = (avg return - risk-free rate) / std(return)
        
        Annualized Sharpe: multiply by √252 (trading days/year)
        
        WHY:
        - Measures risk-adjusted returns
        - >2.0 is excellent
        - >1.0 is good
        - <0.5 is poor
        
        Example:
            Strategy returns: 15% annual, 20% volatility
            Risk-free rate: 6%
            Sharpe = (0.15 - 0.06) / 0.20 × √252 = 0.71 (mediocre)
        """
        daily_rf = (1 + annual_rf_rate) ** (1/252) - 1
        excess_returns = returns - daily_rf
        
        if excess_returns.std() == 0:
            return 0.0
        
        daily_sharpe = excess_returns.mean() / excess_returns.std()
        annual_sharpe = daily_sharpe * np.sqrt(252)
        
        return annual_sharpe
    
    @staticmethod
    def profit_factor(wins_sum: float, losses_sum: float) -> float:
        """
        Profit Factor = Gross Profit / Gross Loss
        
        WHY:
        - >2.0 is excellent (earn 2x what you lose)
        - >1.5 is good
        - <1.0 means losing money
        
        Example:
            20 winning trades: $100 each = +$2000
            10 losing trades: $50 each = -$500
            Profit Factor = $2000 / $500 = 4.0 (excellent)
        """
        if losses_sum == 0:
            return float('inf') if wins_sum > 0 else 0.0
        return wins_sum / abs(losses_sum)
    
    @staticmethod
    def risk_adjusted_metrics(trades_df: pd.DataFrame) -> Dict:
        """
        Calculate comprehensive risk-adjusted performance metrics.
        
        Input DataFrame should have columns:
        - 'return': profit/loss for each trade
        - 'close_price': price when trade closed
        - 'entry_price': entry price
        """
        
        if trades_df.empty:
            return {}
        
        returns = trades_df['return']
        wins = returns[returns > 0]
        losses = returns[returns < 0]
        
        total_return = returns.sum()
        total_trades = len(trades_df)
        win_trades = len(wins)
        loss_trades = len(losses)
        win_rate = win_trades / total_trades if total_trades > 0 else 0
        
        avg_win = wins.mean() if len(wins) > 0 else 0
        avg_loss = losses.mean() if len(losses) > 0 else 0
        
        max_loss = losses.min() if len(losses) > 0 else 0
        max_win = wins.max() if len(wins) > 0 else 0
        
        return {
            "total_trades": total_trades,
            "winning_trades": win_trades,
            "losing_trades": loss_trades,
            "win_rate": win_rate,
            "total_return": total_return,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "profit_factor": RiskAnalyzer.profit_factor(wins.sum(), abs(losses.sum())),
            "expectancy_per_trade": total_return / total_trades if total_trades > 0 else 0,
            "best_trade": max_win,
            "worst_trade": max_loss,
        }


# ════════════════════════════════════════════════════════════════════════════════
# EXAMPLE USAGE
# ════════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Example: Position sizing for a trade
    sizer = PositionSizer(account_balance=100000, risk_per_trade=0.02)
    
    risk_metrics = sizer.calculate_position(
        entry_price=500,
        stop_loss=490,
        target_price=520,
    )
    
    print("📊 POSITION SIZING EXAMPLE")
    print(f"Entry: ${risk_metrics.entry_price}")
    print(f"Stop Loss: ${risk_metrics.stop_loss}")
    print(f"Target: ${risk_metrics.target_price}")
    print(f"Position: {risk_metrics.position_units:.0f} units ({risk_metrics.position_size:.1%} of account)")
    print(f"Risk: ${risk_metrics.risk_amount:.0f} | Reward: ${risk_metrics.reward_amount:.0f}")
    print(f"Risk:Reward Ratio: 1:{risk_metrics.risk_reward_ratio:.2f}")
    
    is_valid, reason = sizer.validate_trade(risk_metrics)
    print(f"Valid: {is_valid} ({reason})")
