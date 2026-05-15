# entry_exit_engine.py - AI-Powered Entry/Exit Level Calculation
# WHY: Users need EXACT prices to buy/sell at, not just predictions
# Generates: Buy Above, Sell Below, Targets, Stoploss
# Uses: ATR, support/resistance, volatility, candle structure

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional, Tuple
from enum import Enum

class EntryType(Enum):
    """Entry types"""
    BREAKOUT_UP = "breakout_up"
    BREAKOUT_DOWN = "breakout_down"
    SUPPORT_BOUNCE = "support_bounce"
    RESISTANCE_BOUNCE = "resistance_bounce"
    CONSOLIDATION_BREAK = "consolidation_break"
    EMA_CROSS = "ema_cross"
    VWAP_CROSS = "vwap_cross"

@dataclass
class EntryExitLevels:
    """Complete entry/exit level structure"""
    entry_type: EntryType
    
    # ENTRY ZONES (Most important for user!)
    buy_above: float  # "BUY above this price"
    buy_below: float  # "But not below this" (cancel zone)
    
    sell_below: float  # "SELL below this price"
    sell_above: float  # "But not above this" (cancel zone)
    
    # RISK MANAGEMENT
    stoploss: float
    risk_points: float  # Entry - SL in points
    
    # TARGETS (Profit taking)
    target1: float
    target1_pct: float
    target2: float
    target2_pct: float
    
    # QUALITY
    risk_reward_1: float  # Target1 / SL ratio
    risk_reward_2: float  # Target2 / SL ratio
    strength: float  # 0-1, how strong is setup
    
    current_price: float
    entry_action: str  # "BUY above" or "SELL below"

class EntryExitEngine:
    """Generates exact entry/exit levels for trades"""
    
    @staticmethod
    def calculate_levels(
        df: pd.DataFrame,
        direction: str,  # "up" or "down"
        entry_type: EntryType = EntryType.BREAKOUT_UP,
        current_price: float = None,
        atr_multiplier_sl: float = 1.0,
        atr_multiplier_t1: float = 1.0,
        atr_multiplier_t2: float = 2.0
    ) -> Optional[EntryExitLevels]:
        """
        Calculate entry/exit levels based on price action and ATR.
        
        Formula example (Buy Setup):
        - Buy Above  = Resistance + (0.2 × ATR)
        - SL         = Support - (1.0 × ATR)
        - Target1    = Entry + (1.0 × ATR)
        - Target2    = Entry + (2.0 × ATR)
        
        Returns: EntryExitLevels with exact prices
        """
        
        if df is None or len(df) < 20:
            return None
        
        if current_price is None:
            current_price = df['Close'].iloc[-1]
        
        # Calculate ATR (core risk measure)
        atr = EntryExitEngine._calculate_atr(df, period=14)
        
        if atr is None or atr == 0:
            return None
        
        # Get recent support/resistance
        recent_high = df['High'].tail(20).max()
        recent_low = df['Low'].tail(20).min()
        recent_close = df['Close'].iloc[-1]
        
        # Get current candle info
        latest = df.iloc[-1]
        latest_high = latest['High']
        latest_low = latest['Low']
        latest_close = latest['Close']
        latest_body = abs(latest_close - latest['Open'])
        
        # ════════════════════════════════════════════════════════════════
        # BULLISH SETUP (BUY)
        # ════════════════════════════════════════════════════════════════
        
        if direction == "up":
            # Entry zone
            buy_above = recent_high + (atr * 0.2)  # Above resistance
            buy_below = recent_high - (atr * 0.5)  # Cancel if drops below
            
            # Stoploss
            stoploss = recent_low - (atr * atr_multiplier_sl)
            risk = buy_above - stoploss
            
            # Take profit targets
            target1 = buy_above + (atr * atr_multiplier_t1)
            target2 = buy_above + (atr * atr_multiplier_t2)
            
            target1_pct = ((target1 - buy_above) / buy_above) * 100
            target2_pct = ((target2 - buy_above) / buy_above) * 100
            
            # Risk/Reward ratios
            rr1 = (target1 - buy_above) / risk if risk > 0 else 0
            rr2 = (target2 - buy_above) / risk if risk > 0 else 0
            
            # Setup strength (how strong is candle)
            if latest_body > 0:
                body_ratio = latest_body / (latest_high - latest_low)
            else:
                body_ratio = 0
            
            strength = min(1.0, body_ratio + 0.3)  # Candle strength + bonus
            
            return EntryExitLevels(
                entry_type=entry_type,
                buy_above=buy_above,
                buy_below=buy_below,
                sell_below=current_price,  # Not applicable
                sell_above=current_price,  # Not applicable
                stoploss=stoploss,
                risk_points=risk,
                target1=target1,
                target1_pct=target1_pct,
                target2=target2,
                target2_pct=target2_pct,
                risk_reward_1=rr1,
                risk_reward_2=rr2,
                strength=strength,
                current_price=current_price,
                entry_action=f"BUY above ₹{buy_above:.2f}"
            )
        
        # ════════════════════════════════════════════════════════════════
        # BEARISH SETUP (SELL)
        # ════════════════════════════════════════════════════════════════
        
        elif direction == "down":
            # Entry zone
            sell_below = recent_low - (atr * 0.2)  # Below support
            sell_above = recent_low + (atr * 0.5)  # Cancel if rises above
            
            # Stoploss
            stoploss = recent_high + (atr * atr_multiplier_sl)
            risk = stoploss - sell_below
            
            # Take profit targets
            target1 = sell_below - (atr * atr_multiplier_t1)
            target2 = sell_below - (atr * atr_multiplier_t2)
            
            target1_pct = ((sell_below - target1) / sell_below) * 100
            target2_pct = ((sell_below - target2) / sell_below) * 100
            
            # Risk/Reward ratios
            rr1 = (sell_below - target1) / risk if risk > 0 else 0
            rr2 = (sell_below - target2) / risk if risk > 0 else 0
            
            # Setup strength
            if latest_body > 0:
                body_ratio = latest_body / (latest_high - latest_low)
            else:
                body_ratio = 0
            
            strength = min(1.0, body_ratio + 0.3)
            
            return EntryExitLevels(
                entry_type=entry_type,
                buy_above=current_price,  # Not applicable
                buy_below=current_price,  # Not applicable
                sell_below=sell_below,
                sell_above=sell_above,
                stoploss=stoploss,
                risk_points=risk,
                target1=target1,
                target1_pct=target1_pct,
                target2=target2,
                target2_pct=target2_pct,
                risk_reward_1=rr1,
                risk_reward_2=rr2,
                strength=strength,
                current_price=current_price,
                entry_action=f"SELL below ₹{sell_below:.2f}"
            )
        
        return None
    
    @staticmethod
    def _calculate_atr(df: pd.DataFrame, period: int = 14) -> Optional[float]:
        """Calculate Average True Range"""
        if len(df) < period:
            return None
        
        # True Range
        high_low = df['High'] - df['Low']
        high_close = abs(df['High'] - df['Close'].shift())
        low_close = abs(df['Low'] - df['Close'].shift())
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        
        # ATR
        atr = tr.rolling(window=period).mean()
        
        return atr.iloc[-1]
    
    @staticmethod
    def generate_for_signal(df: pd.DataFrame, signal_direction: str, current_price: float = None) -> Optional[EntryExitLevels]:
        """
        Quick version - just pass signal direction ("up" or "down")
        
        Returns ready-to-use entry/exit levels
        """
        return EntryExitEngine.calculate_levels(
            df=df,
            direction=signal_direction,
            current_price=current_price
        )
    
    @staticmethod
    def format_for_display(levels: EntryExitLevels) -> Dict:
        """Format levels for dashboard display"""
        
        if levels.entry_action.startswith("BUY"):
            return {
                "action": "🟢 BUY SIGNAL",
                "entry_instruction": f"BUY above ₹{levels.buy_above:.2f}",
                "entry_cancel": f"(Cancel if drops below ₹{levels.buy_below:.2f})",
                "target1_instruction": f"SELL at ₹{levels.target1:.2f} (+{levels.target1_pct:.2f}%)",
                "target2_instruction": f"SELL at ₹{levels.target2:.2f} (+{levels.target2_pct:.2f}%)",
                "stoploss_instruction": f"SET STOP LOSS AT ₹{levels.stoploss:.2f}",
                "risk_reward_1": f"1:{levels.risk_reward_1:.2f}",
                "risk_reward_2": f"1:{levels.risk_reward_2:.2f}",
                "strength": f"{levels.strength*100:.0f}%"
            }
        else:
            return {
                "action": "🔴 SELL SIGNAL",
                "entry_instruction": f"SELL below ₹{levels.sell_below:.2f}",
                "entry_cancel": f"(Cancel if rises above ₹{levels.sell_above:.2f})",
                "target1_instruction": f"BUY at ₹{levels.target1:.2f} ({levels.target1_pct:.2f}%)",
                "target2_instruction": f"BUY at ₹{levels.target2:.2f} ({levels.target2_pct:.2f}%)",
                "stoploss_instruction": f"SET STOP LOSS AT ₹{levels.stoploss:.2f}",
                "risk_reward_1": f"1:{levels.risk_reward_1:.2f}",
                "risk_reward_2": f"1:{levels.risk_reward_2:.2f}",
                "strength": f"{levels.strength*100:.0f}%"
            }
