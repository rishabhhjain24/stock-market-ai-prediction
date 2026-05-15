# advanced_price_action.py - Advanced market structure and price action analysis
# WHY: Price action reveals true market bias before indicators confirm
# Implements: higher highs/lows, breakout strength, support/resistance, momentum

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional
from enum import Enum

class TrendStrength(Enum):
    VERY_STRONG = "very_strong"
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"
    FLAT = "flat"

class BreakoutQuality(Enum):
    VERY_STRONG = "very_strong"
    STRONG = "strong"
    MODERATE = "moderate"
    WEAK = "weak"

@dataclass
class PriceLevel:
    """Support/Resistance level"""
    price: float
    strength: float  # 0-1, how many times tested
    tests: int
    last_tested: pd.Timestamp
    is_support: bool

@dataclass
class BreakoutSignal:
    """Breakout detection result"""
    is_breakout: bool
    direction: str  # "up" or "down"
    quality: BreakoutQuality
    confirmation_strength: float  # 0-1
    body_strength: float  # how much of candle is solid
    volume_confirmation: float  # 0-1
    price_level: float
    distance_pct: float

@dataclass
class PriceActionAnalysis:
    """Complete price action analysis"""
    trend_strength: TrendStrength
    higher_highs: int  # count of consecutive higher highs
    higher_lows: int  # count of consecutive higher lows
    lower_highs: int
    lower_lows: int
    support_levels: List[PriceLevel]
    resistance_levels: List[PriceLevel]
    breakout: Optional[BreakoutSignal]
    momentum_strength: float  # 0-1
    wick_rejection: bool
    consolidation_zone: Tuple[float, float]
    is_exhaustion: bool


class AdvancedPriceAction:
    """Advanced price action analysis engine"""
    
    @staticmethod
    def detect_higher_highs_lows(df: pd.DataFrame, lookback: int = 20) -> Tuple[int, int, int, int]:
        """
        Detect consecutive higher highs/lows and lower highs/lows.
        
        Higher High: Peak higher than previous peak
        Lower High: Peak lower than previous peak
        
        Returns: (higher_highs, higher_lows, lower_highs, lower_lows)
        """
        if len(df) < lookback:
            return 0, 0, 0, 0
        
        recent = df.tail(lookback)
        highs = recent['High'].values
        lows = recent['Low'].values
        
        higher_highs = 0
        higher_lows = 0
        lower_highs = 0
        lower_lows = 0
        
        # Count consecutive higher/lower patterns
        for i in range(1, len(highs)):
            if highs[i] > highs[i-1]:
                higher_highs += 1
            elif highs[i] < highs[i-1]:
                lower_highs += 1
            
            if lows[i] > lows[i-1]:
                higher_lows += 1
            elif lows[i] < lows[i-1]:
                lower_lows += 1
        
        return higher_highs, higher_lows, lower_highs, lower_lows
    
    @staticmethod
    def detect_trend_strength(df: pd.DataFrame, lookback: int = 20) -> TrendStrength:
        """
        Measure trend strength using:
        - How many consecutive higher highs/lows
        - How steep the trend
        - ADX-like concept without indicator
        """
        if len(df) < lookback:
            return TrendStrength.FLAT
        
        hh, hl, lh, ll = AdvancedPriceAction.detect_higher_highs_lows(df, lookback)
        
        uptrend_score = hh + hl
        downtrend_score = lh + ll
        
        # If alternating: weak/flat
        max_score = max(uptrend_score, downtrend_score)
        
        if max_score < 5:
            return TrendStrength.FLAT
        elif max_score < 10:
            return TrendStrength.WEAK
        elif max_score < 15:
            return TrendStrength.MODERATE
        elif max_score < 20:
            return TrendStrength.STRONG
        else:
            return TrendStrength.VERY_STRONG
    
    @staticmethod
    def find_support_resistance(df: pd.DataFrame, lookback: int = 100, sensitivity: int = 5) -> Tuple[List[PriceLevel], List[PriceLevel]]:
        """
        Find support and resistance zones using local minima/maxima.
        
        Algorithm:
        1. Find local peaks (resistance)
        2. Find local troughs (support)
        3. Score by how many times price tested
        4. Filter noise
        """
        if len(df) < lookback:
            return [], []
        
        recent = df.tail(lookback)
        highs = recent['High'].values
        lows = recent['Low'].values
        closes = recent['Close'].values
        times = recent.index
        
        # Find local extrema
        resistance_levels = []
        support_levels = []
        
        for i in range(sensitivity, len(highs) - sensitivity):
            # Check if peak
            if highs[i] > np.max(highs[i-sensitivity:i]) and highs[i] > np.max(highs[i+1:i+sensitivity+1]):
                resistance_levels.append((highs[i], i, times[i]))
            
            # Check if trough
            if lows[i] < np.min(lows[i-sensitivity:i]) and lows[i] < np.min(lows[i+1:i+sensitivity+1]):
                support_levels.append((lows[i], i, times[i]))
        
        # Cluster and score levels
        def cluster_levels(levels: List[Tuple], tolerance_pct: float = 0.02) -> List[PriceLevel]:
            if not levels:
                return []
            
            levels_sorted = sorted(levels, key=lambda x: x[0])
            clusters = []
            current_cluster = [levels_sorted[0]]
            
            for level in levels_sorted[1:]:
                if abs(level[0] - current_cluster[0][0]) / current_cluster[0][0] < tolerance_pct:
                    current_cluster.append(level)
                else:
                    # Process cluster
                    avg_price = np.mean([l[0] for l in current_cluster])
                    strength = len(current_cluster) / len(levels)
                    last_tested = max(current_cluster, key=lambda x: x[2])[2]
                    
                    clusters.append(PriceLevel(
                        price=avg_price,
                        strength=strength,
                        tests=len(current_cluster),
                        last_tested=last_tested,
                        is_support=False
                    ))
                    current_cluster = [level]
            
            return clusters
        
        resistance = cluster_levels(resistance_levels)
        support = cluster_levels(support_levels)
        
        # Mark as support/resistance
        for s in support:
            s.is_support = True
        
        return support, resistance
    
    @staticmethod
    def detect_breakout(df: pd.DataFrame, lookback: int = 20, volume_df: Optional[pd.DataFrame] = None) -> Optional[BreakoutSignal]:
        """
        Detect breakouts with quality assessment.
        
        Signals:
        - Price breaks above/below recent resistance/support
        - Candle body is substantial (not just wick)
        - Volume confirms (if available)
        - Distance from level indicates strength
        """
        if len(df) < lookback:
            return None
        
        recent = df.tail(lookback)
        latest = df.iloc[-1]
        
        # Get recent high/low
        recent_high = recent['High'].max()
        recent_low = recent['Low'].min()
        current_close = float(latest['Close'])
        current_open = float(latest['Open'])
        
        # Check breakout
        breakout_up = current_close > recent_high
        breakout_down = current_close < recent_low
        
        if not (breakout_up or breakout_down):
            return None
        
        # Calculate body strength (how much of candle is solid body vs wick)
        candle_range = latest['High'] - latest['Low']
        body_size = abs(latest['Close'] - latest['Open'])
        body_strength = body_size / candle_range if candle_range > 0 else 0
        
        # Distance from previous consolidation
        if breakout_up:
            distance = (current_close - recent_high) / recent_high
            direction = "up"
        else:
            distance = (recent_low - current_close) / recent_low
            direction = "down"
        
        # Volume confirmation
        volume_conf = 0.5  # Default
        if volume_df is not None and len(volume_df) > 0:
            recent_vol_avg = volume_df.tail(lookback)['Volume'].mean()
            current_vol = latest.get('Volume', recent_vol_avg)
            volume_conf = min(1.0, current_vol / recent_vol_avg) if recent_vol_avg > 0 else 0.5
        
        # Quality assessment
        confirmation = (body_strength * 0.5 + min(1.0, distance * 100) * 0.5)
        
        if confirmation > 0.7:
            quality = BreakoutQuality.VERY_STRONG
        elif confirmation > 0.5:
            quality = BreakoutQuality.STRONG
        elif confirmation > 0.3:
            quality = BreakoutQuality.MODERATE
        else:
            quality = BreakoutQuality.WEAK
        
        return BreakoutSignal(
            is_breakout=True,
            direction=direction,
            quality=quality,
            confirmation_strength=confirmation,
            body_strength=body_strength,
            volume_confirmation=volume_conf,
            price_level=recent_high if breakout_up else recent_low,
            distance_pct=distance * 100
        )
    
    @staticmethod
    def detect_wick_rejection(df: pd.DataFrame) -> bool:
        """
        Detect wick rejection - price touches level but gets rejected.
        
        Signal: Large wick at extremes with small body in opposite direction
        (Hammer, shooting star, etc.)
        """
        if len(df) < 2:
            return False
        
        latest = df.iloc[-1]
        
        body_size = abs(latest['Close'] - latest['Open'])
        candle_range = latest['High'] - latest['Low']
        
        if candle_range == 0:
            return False
        
        body_ratio = body_size / candle_range
        
        # Rejection if wick is 2x+ body size and body is small
        upper_wick = latest['High'] - max(latest['Open'], latest['Close'])
        lower_wick = min(latest['Open'], latest['Close']) - latest['Low']
        
        is_hammer = lower_wick > upper_wick * 2 and body_ratio < 0.4
        is_shooter = upper_wick > lower_wick * 2 and body_ratio < 0.4
        
        return is_hammer or is_shooter
    
    @staticmethod
    def detect_consolidation(df: pd.DataFrame, lookback: int = 20) -> Tuple[float, float]:
        """
        Detect consolidation zones (tight ranges).
        
        Returns: (support_line, resistance_line)
        """
        if len(df) < lookback:
            return df.iloc[-1]['Low'], df.iloc[-1]['High']
        
        recent = df.tail(lookback)
        low = recent['Low'].min()
        high = recent['High'].max()
        
        return low, high
    
    @staticmethod
    def detect_exhaustion(df: pd.DataFrame, lookback: int = 20) -> bool:
        """
        Detect trend exhaustion signals.
        
        Signals:
        - Small candles after large move (momentum fading)
        - RSI divergence pattern
        - Price reaching extreme levels
        """
        if len(df) < lookback:
            return False
        
        recent = df.tail(lookback)
        
        # Get candle sizes
        ranges = (recent['High'] - recent['Low']).values
        avg_range = ranges[:-5].mean() if len(ranges) > 5 else ranges.mean()
        
        # Last few candles increasingly smaller = exhaustion
        recent_ranges = ranges[-5:]
        is_shrinking = all(recent_ranges[i] > recent_ranges[i+1] for i in range(len(recent_ranges)-1))
        
        # Check RSI extremes
        rsi = recent.get('RSI', pd.Series(50, index=recent.index))
        rsi_extreme = (rsi.iloc[-1] > 80 or rsi.iloc[-1] < 20)
        
        exhaustion = is_shrinking and rsi_extreme
        
        return exhaustion
    
    @staticmethod
    def calculate_momentum_strength(df: pd.DataFrame, lookback: int = 14) -> float:
        """
        Calculate momentum strength (0-1).
        
        Based on:
        - Rate of change
        - Consecutive up/down days
        - Candle size trend
        """
        if len(df) < lookback:
            return 0.5
        
        recent = df.tail(lookback)
        closes = recent['Close'].values
        
        # Price momentum
        price_change = (closes[-1] - closes[0]) / closes[0]
        momentum = min(1.0, max(-1.0, price_change * 100)) / 100
        
        # Consecutive moves
        up_days = (closes > closes.shift(1)).sum()
        momentum_score = abs(momentum) * 0.5 + (up_days / lookback) * 0.5
        
        return min(1.0, max(0.0, momentum_score))
    
    @staticmethod
    def analyze(df: pd.DataFrame, lookback_trend: int = 20, lookback_sr: int = 100) -> PriceActionAnalysis:
        """Main price action analysis"""
        
        hh, hl, lh, ll = AdvancedPriceAction.detect_higher_highs_lows(df, lookback_trend)
        trend_strength = AdvancedPriceAction.detect_trend_strength(df, lookback_trend)
        support, resistance = AdvancedPriceAction.find_support_resistance(df, lookback_sr)
        breakout = AdvancedPriceAction.detect_breakout(df, lookback_trend)
        momentum = AdvancedPriceAction.calculate_momentum_strength(df)
        wick_rej = AdvancedPriceAction.detect_wick_rejection(df)
        consolidation = AdvancedPriceAction.detect_consolidation(df, lookback_trend)
        exhaustion = AdvancedPriceAction.detect_exhaustion(df, lookback_trend)
        
        return PriceActionAnalysis(
            trend_strength=trend_strength,
            higher_highs=hh,
            higher_lows=hl,
            lower_highs=lh,
            lower_lows=ll,
            support_levels=support,
            resistance_levels=resistance,
            breakout=breakout,
            momentum_strength=momentum,
            wick_rejection=wick_rej,
            consolidation_zone=consolidation,
            is_exhaustion=exhaustion
        )
