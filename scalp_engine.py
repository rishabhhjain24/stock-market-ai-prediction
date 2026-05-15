# scalp_engine.py - Advanced scalping signals and intraday trading
# WHY: Quick profits from small price moves using tight risk management
# Generates: Buy price/time, Sell price, Expected move %, Risk/Reward

import pandas as pd
import numpy as np
import yfinance as yf
from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from enum import Enum

class ScalpSignal(Enum):
    """Scalping signal types"""
    VWAP_BREAKOUT = "vwap_breakout"  # Price breaks above/below VWAP
    EMA_CROSSOVER = "ema_crossover"  # Fast EMA crosses slow
    RSI_MOMENTUM = "rsi_momentum"  # RSI divergence or extremes
    VOLUME_SPIKE = "volume_spike"  # Unusual volume spike
    LIQUIDITY_BREAKOUT = "liquidity_breakout"  # Break of recent high/low
    CONSOLIDATION_BREAKOUT = "consolidation_breakout"  # Break of tight range
    CANDLE_PATTERN = "candle_pattern"  # Specific candle pattern

@dataclass
class ScalpOpportunity:
    """Single scalping opportunity"""
    symbol: str
    signal: ScalpSignal
    direction: str  # "up" or "down"
    entry_price: float
    entry_price_max: float  # Buy up to this price
    stop_loss: float
    target_price: float
    expected_move_pct: float
    expected_move_time: str  # "5m", "15m", "30m"
    confidence: float  # 0-1
    risk_reward_ratio: float
    entry_window_minutes: int  # How long window valid
    entry_window_end: datetime
    reasons: List[str]
    current_price: float
    rsi: float
    volume_ratio: float

class ScalpEngine:
    """Advanced scalping opportunity detection engine"""
    
    @staticmethod
    def calculate_vwap(df: pd.DataFrame) -> pd.Series:
        """Calculate VWAP"""
        df = df.copy()
        df['TP'] = (df['High'] + df['Low'] + df['Close']) / 3
        df['TP_Vol'] = df['TP'] * df['Volume']
        df['Cum_TP_Vol'] = df['TP_Vol'].cumsum()
        df['Cum_Vol'] = df['Volume'].cumsum()
        vwap = df['Cum_TP_Vol'] / df['Cum_Vol']
        return vwap
    
    @staticmethod
    def calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        close = df['Close']
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def detect_vwap_breakout(df: pd.DataFrame) -> Optional[ScalpOpportunity]:
        """
        Detect VWAP breakout scalp setups.
        
        Setup:
        - Price breaks above VWAP with volume
        - Quick target = VWAP + 0.5% to 1%
        - Stop below VWAP
        """
        if len(df) < 20:
            return None
        
        df = df.copy()
        vwap = ScalpEngine.calculate_vwap(df)
        df['VWAP'] = vwap
        df['RSI'] = ScalpEngine.calculate_rsi(df)
        
        current = df.iloc[-1]
        close = current['Close']
        vwap_val = current['VWAP']
        rsi = current['RSI']
        
        # Check for breakout
        above_vwap = close > vwap_val
        below_vwap = close < vwap_val
        
        # Volume confirmation
        vol_avg = df['Volume'].tail(20).mean()
        vol_ratio = current['Volume'] / vol_avg if vol_avg > 0 else 1
        
        if vol_ratio < 1.2:
            return None
        
        if above_vwap and rsi > 50:
            # Bullish VWAP breakout
            entry = close
            entry_max = close + (close * 0.005)
            target = vwap_val + (vwap_val * 0.010)
            stop_loss = vwap_val - (vwap_val * 0.004)
            
            move = target - entry
            move_pct = (move / entry) * 100
            
            if move <= 0:
                return None
            
            rr = move / max(entry - stop_loss, 0.01)
            
            return ScalpOpportunity(
                symbol="",
                signal=ScalpSignal.VWAP_BREAKOUT,
                direction="up",
                entry_price=entry,
                entry_price_max=entry_max,
                stop_loss=stop_loss,
                target_price=target,
                expected_move_pct=move_pct,
                expected_move_time="15m",
                confidence=min(1.0, vol_ratio / 2),
                risk_reward_ratio=rr,
                entry_window_minutes=5,
                entry_window_end=datetime.now() + timedelta(minutes=5),
                reasons=[
                    f"Price above VWAP",
                    f"Volume spike {vol_ratio:.1f}x normal",
                    f"RSI momentum {rsi:.0f}"
                ],
                current_price=close,
                rsi=rsi,
                volume_ratio=vol_ratio
            )
        
        elif below_vwap and rsi < 50:
            # Bearish VWAP breakout
            entry = close
            entry_max = close - (close * 0.005)
            target = vwap_val - (vwap_val * 0.010)
            stop_loss = vwap_val + (vwap_val * 0.004)
            
            move = entry - target
            move_pct = (move / entry) * 100
            
            if move <= 0:
                return None
            
            rr = move / max(stop_loss - entry, 0.01)
            
            return ScalpOpportunity(
                symbol="",
                signal=ScalpSignal.VWAP_BREAKOUT,
                direction="down",
                entry_price=entry,
                entry_price_max=entry_max,
                stop_loss=stop_loss,
                target_price=target,
                expected_move_pct=move_pct,
                expected_move_time="15m",
                confidence=min(1.0, vol_ratio / 2),
                risk_reward_ratio=rr,
                entry_window_minutes=5,
                entry_window_end=datetime.now() + timedelta(minutes=5),
                reasons=[
                    f"Price below VWAP",
                    f"Volume spike {vol_ratio:.1f}x normal",
                    f"RSI momentum {rsi:.0f}"
                ],
                current_price=close,
                rsi=rsi,
                volume_ratio=vol_ratio
            )
        
        return None
    
    @staticmethod
    def detect_ema_crossover(df: pd.DataFrame) -> Optional[ScalpOpportunity]:
        """
        Detect EMA crossover scalp setup.
        
        Setup:
        - Fast EMA (9) crosses Slow EMA (21)
        - Entry on crossover confirmation
        - Target = entry + 2 x risk
        """
        if len(df) < 25:
            return None
        
        df = df.copy()
        df['EMA_9'] = df['Close'].ewm(span=9).mean()
        df['EMA_21'] = df['Close'].ewm(span=21).mean()
        df['RSI'] = ScalpEngine.calculate_rsi(df)
        
        current = df.iloc[-1]
        previous = df.iloc[-2]
        
        close = current['Close']
        ema9 = current['EMA_9']
        ema21 = current['EMA_21']
        rsi = current['RSI']
        
        ema9_prev = previous['EMA_9']
        ema21_prev = previous['EMA_21']
        
        # Bullish crossover
        if ema9_prev <= ema21_prev and ema9 > ema21 and rsi > 40:
            entry = close
            stop_loss = ema21 - (ema21 * 0.005)
            risk = entry - stop_loss
            target = entry + (risk * 2)
            
            move_pct = ((target - entry) / entry) * 100
            
            return ScalpOpportunity(
                symbol="",
                signal=ScalpSignal.EMA_CROSSOVER,
                direction="up",
                entry_price=entry,
                entry_price_max=entry + (entry * 0.003),
                stop_loss=stop_loss,
                target_price=target,
                expected_move_pct=move_pct,
                expected_move_time="15m",
                confidence=min(1.0, (rsi - 40) / 60),
                risk_reward_ratio=2.0,
                entry_window_minutes=3,
                entry_window_end=datetime.now() + timedelta(minutes=3),
                reasons=[
                    "EMA 9 crossed above EMA 21 (bullish)",
                    f"RSI momentum {rsi:.0f}",
                    "1:2 Risk Reward ratio"
                ],
                current_price=close,
                rsi=rsi,
                volume_ratio=1.0
            )
        
        # Bearish crossover
        elif ema9_prev >= ema21_prev and ema9 < ema21 and rsi < 60:
            entry = close
            stop_loss = ema21 + (ema21 * 0.005)
            risk = stop_loss - entry
            target = entry - (risk * 2)
            
            move_pct = ((entry - target) / entry) * 100
            
            return ScalpOpportunity(
                symbol="",
                signal=ScalpSignal.EMA_CROSSOVER,
                direction="down",
                entry_price=entry,
                entry_price_max=entry - (entry * 0.003),
                stop_loss=stop_loss,
                target_price=target,
                expected_move_pct=move_pct,
                expected_move_time="15m",
                confidence=min(1.0, (60 - rsi) / 60),
                risk_reward_ratio=2.0,
                entry_window_minutes=3,
                entry_window_end=datetime.now() + timedelta(minutes=3),
                reasons=[
                    "EMA 9 crossed below EMA 21 (bearish)",
                    f"RSI momentum {rsi:.0f}",
                    "1:2 Risk Reward ratio"
                ],
                current_price=close,
                rsi=rsi,
                volume_ratio=1.0
            )
        
        return None
    
    @staticmethod
    def detect_liquidity_breakout(df: pd.DataFrame, lookback: int = 10) -> Optional[ScalpOpportunity]:
        """
        Detect liquidity zone breakout.
        
        Setup:
        - Price breaks recent high/low
        - Quick spike expected
        """
        if len(df) < lookback:
            return None
        
        df = df.copy()
        df['RSI'] = ScalpEngine.calculate_rsi(df)
        
        recent = df.tail(lookback)
        current = df.iloc[-1]
        
        recent_high = recent['High'].max()
        recent_low = recent['Low'].min()
        close = current['Close']
        rsi = current['RSI']
        
        vol_avg = df['Volume'].tail(20).mean()
        vol_ratio = current['Volume'] / vol_avg if vol_avg > 0 else 1
        
        # Breakout confirmation: close above high with volume
        if close > recent_high and vol_ratio > 1.3 and rsi > 50:
            entry = close
            stop_loss = recent_high - (recent_high * 0.003)
            target = close + ((close - stop_loss) * 1.5)
            
            move_pct = ((target - entry) / entry) * 100
            rr = 1.5
            
            return ScalpOpportunity(
                symbol="",
                signal=ScalpSignal.LIQUIDITY_BREAKOUT,
                direction="up",
                entry_price=entry,
                entry_price_max=entry + (entry * 0.002),
                stop_loss=stop_loss,
                target_price=target,
                expected_move_pct=move_pct,
                expected_move_time="10m",
                confidence=min(1.0, vol_ratio / 2),
                risk_reward_ratio=rr,
                entry_window_minutes=5,
                entry_window_end=datetime.now() + timedelta(minutes=5),
                reasons=[
                    f"Breakout of recent high ₹{recent_high:.2f}",
                    f"Volume spike {vol_ratio:.1f}x",
                    f"Clear liquidity move"
                ],
                current_price=close,
                rsi=rsi,
                volume_ratio=vol_ratio
            )
        
        # Breakout below
        elif close < recent_low and vol_ratio > 1.3 and rsi < 50:
            entry = close
            stop_loss = recent_low + (recent_low * 0.003)
            target = close - ((stop_loss - close) * 1.5)
            
            move_pct = ((entry - target) / entry) * 100
            rr = 1.5
            
            return ScalpOpportunity(
                symbol="",
                signal=ScalpSignal.LIQUIDITY_BREAKOUT,
                direction="down",
                entry_price=entry,
                entry_price_max=entry - (entry * 0.002),
                stop_loss=stop_loss,
                target_price=target,
                expected_move_pct=move_pct,
                expected_move_time="10m",
                confidence=min(1.0, vol_ratio / 2),
                risk_reward_ratio=rr,
                entry_window_minutes=5,
                entry_window_end=datetime.now() + timedelta(minutes=5),
                reasons=[
                    f"Breakout of recent low ₹{recent_low:.2f}",
                    f"Volume spike {vol_ratio:.1f}x",
                    f"Clear liquidity move"
                ],
                current_price=close,
                rsi=rsi,
                volume_ratio=vol_ratio
            )
        
        return None
    
    @staticmethod
    def find_all_scalp_opportunities(df: pd.DataFrame, symbol: str = "") -> List[ScalpOpportunity]:
        """
        Scan for all scalping opportunities.
        
        Returns sorted list by confidence score.
        """
        opportunities = []
        
        # Check each signal type
        vwap_opp = ScalpEngine.detect_vwap_breakout(df)
        if vwap_opp:
            vwap_opp.symbol = symbol
            opportunities.append(vwap_opp)
        
        ema_opp = ScalpEngine.detect_ema_crossover(df)
        if ema_opp:
            ema_opp.symbol = symbol
            opportunities.append(ema_opp)
        
        liquidity_opp = ScalpEngine.detect_liquidity_breakout(df)
        if liquidity_opp:
            liquidity_opp.symbol = symbol
            opportunities.append(liquidity_opp)
        
        # Sort by confidence
        opportunities.sort(key=lambda x: x.confidence, reverse=True)
        
        return opportunities
