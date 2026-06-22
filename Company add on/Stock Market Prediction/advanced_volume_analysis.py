# advanced_volume_analysis.py - Advanced volume-based market analysis
# WHY: Real smart money moves are confirmed by volume - price without volume is unreliable
# Implements: volume spikes, accumulation, OBV, VWAP, supply/demand

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Dict, Optional, List
from enum import Enum

class VolumeSignal(Enum):
    """Volume-based trading signals"""
    ACCUMULATION = "accumulation"  # Smart money buying
    DISTRIBUTION = "distribution"  # Smart money selling
    VOLUME_SPIKE = "volume_spike"  # Unusual volume
    BREAKOUT_CONFIRMED = "breakout_confirmed"
    BREAKOUT_UNCONFIRMED = "breakout_unconfirmed"
    NORMAL = "normal"
    NO_DEMAND = "no_demand"

@dataclass
class VolumeProfile:
    """Volume at different price levels"""
    price_level: float
    volume: float
    relative_strength: float  # vs average
    
@dataclass
class VolumeAnalysis:
    """Complete volume analysis"""
    signal: VolumeSignal
    signal_confidence: float  # 0-1
    volume_trend: str  # "increasing", "decreasing", "stable"
    accumulation_score: float  # 0-1
    distribution_score: float  # 0-1
    volume_spike_strength: float  # 0-1  
    obv_trend: str  # "bullish", "bearish", "neutral"
    vwap_relationship: str  # "above", "below", "touching"
    supply_demand_ratio: float  # supply/demand
    volume_profile: List[VolumeProfile]

class AdvancedVolumeAnalysis:
    """Advanced volume analysis engine"""
    
    @staticmethod
    def calculate_vwap(df: pd.DataFrame) -> pd.Series:
        """
        Volume Weighted Average Price (VWAP).
        
        VWAP = Σ(Price × Volume) / Σ(Volume)
        
        WHY: Shows fair value based on volume-weighted trades
        Breakouts below/above VWAP show strength/weakness
        """
        df = df.copy()
        
        df['Typical_Price'] = (df['High'] + df['Low'] + df['Close']) / 3
        df['TP_Volume'] = df['Typical_Price'] * df['Volume']
        df['Cumulative_TP_Vol'] = df['TP_Volume'].cumsum()
        df['Cumulative_Vol'] = df['Volume'].cumsum()
        
        vwap = df['Cumulative_TP_Vol'] / df['Cumulative_Vol']
        
        return vwap
    
    @staticmethod
    def calculate_obv(df: pd.DataFrame) -> pd.Series:
        """
        On-Balance Volume (OBV).
        
        Algorithm:
        - If Close > Previous Close: OBV += Volume
        - If Close < Previous Close: OBV -= Volume
        - If Close = Previous Close: OBV unchanged
        
        WHY: Accumulation (OBV rising) should validate uptrends
        Distribution (OBV falling) warns of reversals
        """
        obv = pd.Series(index=df.index, dtype='float64')
        obv.iloc[0] = df['Volume'].iloc[0]
        
        for i in range(1, len(df)):
            if df['Close'].iloc[i] > df['Close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + df['Volume'].iloc[i]
            elif df['Close'].iloc[i] < df['Close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - df['Volume'].iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        return obv
    
    @staticmethod
    def detect_volume_spike(df: pd.DataFrame, lookback: int = 20, threshold: float = 1.5) -> Dict:
        """
        Detect unusual volume spikes.
        
        Algorithm:
        - Compare recent volume to 20-day average
        - If > 1.5x average = volume spike
        - Indicates smart money entry/exit
        """
        if len(df) < lookback:
            return {"is_spike": False, "spike_strength": 0}
        
        recent_volumes = df['Volume'].tail(lookback).values
        avg_volume = recent_volumes[:-1].mean()
        current_volume = recent_volumes[-1]
        
        spike_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        is_spike = spike_ratio > threshold
        
        spike_strength = min(1.0, (spike_ratio - 1) / 1) if spike_ratio > 1 else 0
        
        return {
            "is_spike": is_spike,
            "spike_strength": spike_strength,
            "spike_ratio": spike_ratio,
            "avg_volume": avg_volume,
            "current_volume": current_volume
        }
    
    @staticmethod
    def detect_accumulation_distribution(df: pd.DataFrame, lookback: int = 20) -> Dict:
        """
        Detect accumulation (buying) vs distribution (selling).
        
        Algorithm:
        - Close near High + High Volume = Accumulation
        - Close near Low + High Volume = Distribution
        """
        if len(df) < lookback:
            return {"accumulation_score": 0, "distribution_score": 0}
        
        recent = df.tail(lookback)
        
        accumulation_score = 0
        distribution_score = 0
        
        for idx, row in recent.iterrows():
            close = row['Close']
            high = row['High']
            low = row['Low']
            volume = row['Volume']
            
            # Normalize close position (0=low, 1=high)
            range_size = high - low
            if range_size > 0:
                close_position = (close - low) / range_size
            else:
                close_position = 0.5
            
            # Accumulation: close near high
            if close_position > 0.7:
                accumulation_score += volume * close_position
            
            # Distribution: close near low
            if close_position < 0.3:
                distribution_score += volume * (1 - close_position)
        
        total_volume = recent['Volume'].sum()
        
        acc_ratio = accumulation_score / total_volume if total_volume > 0 else 0
        dist_ratio = distribution_score / total_volume if total_volume > 0 else 0
        
        return {
            "accumulation_score": acc_ratio,
            "distribution_score": dist_ratio,
            "accumulation_dominance": acc_ratio > dist_ratio
        }
    
    @staticmethod
    def detect_obv_trend(df: pd.DataFrame, lookback: int = 20) -> str:
        """
        Detect OBV trend - is OBV rising or falling?
        
        Bullish: OBV making higher highs with price
        Bearish: OBV making lower lows while price rises (divergence)
        """
        if len(df) < lookback:
            return "neutral"
        
        obv = AdvancedVolumeAnalysis.calculate_obv(df)
        recent_obv = obv.tail(lookback).values
        
        obv_slope = (recent_obv[-1] - recent_obv[0]) / lookback
        
        if obv_slope > 0:
            return "bullish"
        elif obv_slope < 0:
            return "bearish"
        else:
            return "neutral"
    
    @staticmethod
    def analyze_vwap_relationship(df: pd.DataFrame) -> str:
        """
        Price relationship to VWAP.
        
        - Above VWAP: Bullish (fair value is lower)
        - Below VWAP: Bearish (fair value is higher)
        - Touching: Consolidation
        """
        if len(df) < 20:
            return "touching"
        
        vwap = AdvancedVolumeAnalysis.calculate_vwap(df)
        current_price = df['Close'].iloc[-1]
        current_vwap = vwap.iloc[-1]
        
        diff_pct = abs(current_price - current_vwap) / current_vwap * 100
        
        if current_price > current_vwap:
            if diff_pct > 1:
                return "above"
            else:
                return "touching"
        elif current_price < current_vwap:
            if diff_pct > 1:
                return "below"
            else:
                return "touching"
        else:
            return "touching"
    
    @staticmethod
    def calculate_supply_demand_ratio(df: pd.DataFrame, lookback: int = 20) -> float:
        """
        Supply/Demand ratio based on volume at different price levels.
        
        Returns:
        - > 1: More supply (bearish)
        - < 1: More demand (bullish)
        - = 1: Balanced
        """
        if len(df) < lookback:
            return 1.0
        
        recent = df.tail(lookback)
        
        # Selling volume (close < open)
        selling = ((recent['Open'] - recent['Close']) * recent['Volume']).sum()
        
        # Buying volume (close > open)
        buying = ((recent['Close'] - recent['Open']) * recent['Volume']).sum()
        
        supply_demand = selling / buying if buying > 0 else 1.0
        
        return supply_demand
    
    @staticmethod
    def check_breakout_volume_confirmation(df: pd.DataFrame, lookback_price: int = 20, lookback_vol: int = 20) -> Dict:
        """
        Check if breakout is confirmed by volume.
        
        Breakout is valid if:
        - Price breaks above/below resistance/support
        - Volume is > average (ideally 1.5x+)
        """
        if len(df) < max(lookback_price, lookback_vol):
            return {"confirmed": False, "confidence": 0}
        
        # Check price breakout
        price_recent = df['Close'].tail(lookback_price).values
        high_range = price_recent.max()
        low_range = price_recent.min()
        current_price = df['Close'].iloc[-1]
        
        is_breakout_up = current_price > high_range
        is_breakout_down = current_price < low_range
        
        # Check volume
        vol_recent = df['Volume'].tail(lookback_vol).values
        avg_volume = vol_recent[:-1].mean()
        current_volume = vol_recent[-1]
        
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        is_volume_confirmed = volume_ratio > 1.2
        
        is_breakout = is_breakout_up or is_breakout_down
        is_confirmed = is_breakout and is_volume_confirmed
        
        confidence = volume_ratio / 2 if is_confirmed else 0
        confidence = min(1.0, confidence)
        
        return {
            "confirmed": is_confirmed,
            "confidence": confidence,
            "is_breakout": is_breakout,
            "is_volume_confirmed": is_volume_confirmed,
            "volume_ratio": volume_ratio
        }
    
    @staticmethod
    def analyze(df: pd.DataFrame, lookback: int = 20) -> VolumeAnalysis:
        """Complete volume analysis"""
        
        volume_spike = AdvancedVolumeAnalysis.detect_volume_spike(df, lookback)
        acc_dist = AdvancedVolumeAnalysis.detect_accumulation_distribution(df, lookback)
        obv_trend_val = AdvancedVolumeAnalysis.detect_obv_trend(df, lookback)
        vwap_rel = AdvancedVolumeAnalysis.analyze_vwap_relationship(df)
        sd_ratio = AdvancedVolumeAnalysis.calculate_supply_demand_ratio(df, lookback)
        breakout_conf = AdvancedVolumeAnalysis.check_breakout_volume_confirmation(df, lookback, lookback)
        
        # Determine overall signal
        if acc_dist["accumulation_dominance"] and obv_trend_val == "bullish":
            signal = VolumeSignal.ACCUMULATION
            confidence = 0.7
        elif not acc_dist["accumulation_dominance"] and obv_trend_val == "bearish":
            signal = VolumeSignal.DISTRIBUTION
            confidence = 0.7
        elif volume_spike["is_spike"]:
            signal = VolumeSignal.VOLUME_SPIKE
            confidence = volume_spike["spike_strength"]
        elif breakout_conf["confirmed"]:
            signal = VolumeSignal.BREAKOUT_CONFIRMED
            confidence = breakout_conf["confidence"]
        elif breakout_conf["is_breakout"]:
            signal = VolumeSignal.BREAKOUT_UNCONFIRMED
            confidence = 0.3
        else:
            signal = VolumeSignal.NORMAL
            confidence = 0.5
        
        # Volume trend
        vol_recent = df['Volume'].tail(lookback).values
        vol_slope = (vol_recent[-1] - vol_recent[0]) / lookback
        
        if vol_slope > 0:
            volume_trend = "increasing"
        elif vol_slope < 0:
            volume_trend = "decreasing"
        else:
            volume_trend = "stable"
        
        return VolumeAnalysis(
            signal=signal,
            signal_confidence=confidence,
            volume_trend=volume_trend,
            accumulation_score=acc_dist["accumulation_score"],
            distribution_score=acc_dist["distribution_score"],
            volume_spike_strength=volume_spike["spike_strength"],
            obv_trend=obv_trend_val,
            vwap_relationship=vwap_rel,
            supply_demand_ratio=sd_ratio,
            volume_profile=[]
        )
