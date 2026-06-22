# multi_timeframe_analyzer.py - Multi-timeframe trend alignment
# WHY: Trends on different timeframes create confluence (stronger signals)
# Implements: 1m-weekly timeframe analysis, alignment scoring, conflict detection

import pandas as pd
import yfinance as yf
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
import numpy as np

class TimeframeAlignment(Enum):
    """How well do timeframes align?"""
    PERFECT_ALIGNMENT = "perfect"  # All bullish/bearish
    STRONG_ALIGNMENT = "strong"  # 5+ frames aligned
    MODERATE_ALIGNMENT = "moderate"  # 3-4 frames aligned
    WEAK_ALIGNMENT = "weak"  # 2 frames aligned
    NO_ALIGNMENT = "none"  # Conflicting
    NO_TREND = "no_trend"  # Neutral

@dataclass
class TimeframeAnalysis:
    """Single timeframe analysis"""
    timeframe: str
    trend_direction: str  # "up", "down", "neutral"
    trend_strength: float  # 0-1
    support: float
    resistance: float
    confidence: float  # 0-1

@dataclass
class MultiTimeframeResult:
    """Multi-timeframe analysis result"""
    analyses: Dict[str, TimeframeAnalysis]
    alignment: TimeframeAlignment
    alignment_score: float  # 0-1
    overall_direction: str  # "bullish", "bearish", "neutral"
    highest_tf_direction: str  # Higher TF opinion
    lowest_tf_direction: str  # Lower TF opinion
    conflicts: List[str]  # Conflicting timeframes

class MultiTimeframeAnalyzer:
    """Multi-timeframe analysis engine"""
    
    TIMEFRAMES_MAP = {
        "1m": "1m",
        "3m": "3m",
        "5m": "5m",
        "15m": "15m",
        "1h": "1h",
        "daily": "1d",
        "1d": "1d",
        "weekly": "1wk",
        "1w": "1wk"
    }
    
    TIMEFRAME_PRIORITY = {
        "1w": 9,    # Highest
        "1wk": 9,
        "1d": 8,
        "1h": 7,
        "15m": 6,
        "5m": 5,
        "3m": 4,
        "1m": 3     # Lowest
    }
    
    @staticmethod
    def fetch_data(symbol: str, timeframe: str, period: str = "60d") -> Optional[pd.DataFrame]:
        """
        Fetch data for specific timeframe.
        
        Maps: "daily" -> "1d", "1h" -> "1h", etc.
        """
        try:
            tf_mapped = MultiTimeframeAnalyzer.TIMEFRAMES_MAP.get(timeframe, timeframe)
            df = yf.download(symbol, interval=tf_mapped, period=period, progress=False)
            if df.empty:
                return None
            return df
        except Exception as e:
            print(f"Error fetching {timeframe} for {symbol}: {e}")
            return None
    
    @staticmethod
    def analyze_timeframe(df: pd.DataFrame) -> TimeframeAnalysis:
        """
        Analyze single timeframe.
        
        Returns: Trend direction, support/resistance, confidence
        """
        if df is None or len(df) < 10:
            return TimeframeAnalysis(
                timeframe="unknown",
                trend_direction="neutral",
                trend_strength=0,
                support=0,
                resistance=0,
                confidence=0
            )
        
        latest = df.iloc[-1]
        
        # Calculate EMAs if not present
        if 'EMA_20' not in df.columns:
            df['EMA_20'] = df['Close'].ewm(span=20).mean()
        if 'EMA_50' not in df.columns:
            df['EMA_50'] = df['Close'].ewm(span=50).mean()
        if 'RSI' not in df.columns:
            df['RSI'] = MultiTimeframeAnalyzer._calculate_rsi(df, 14)
        
        # Calculate support/resistance
        recent_low = df['Low'].tail(20).min()
        recent_high = df['High'].tail(20).max()
        
        # Trend direction
        ema20 = df['EMA_20'].iloc[-1]
        ema50 = df['EMA_50'].iloc[-1]
        close = latest['Close']
        rsi = df['RSI'].iloc[-1]
        
        # Determine trend
        if close > ema20 > ema50:
            trend = "up"
            strength = 0.8
        elif close > ema20:
            trend = "up"
            strength = 0.5
        elif close < ema20 < ema50:
            trend = "down"
            strength = 0.8
        elif close < ema20:
            trend = "down"
            strength = 0.5
        else:
            trend = "neutral"
            strength = 0
        
        # RSI as additional confidence
        if rsi > 70:
            strength = min(1.0, strength + 0.2)
        elif rsi < 30:
            strength = min(1.0, strength + 0.2)
        
        confidence = min(1.0, strength)
        
        return TimeframeAnalysis(
            timeframe="multiple",
            trend_direction=trend,
            trend_strength=strength,
            support=recent_low,
            resistance=recent_high,
            confidence=confidence
        )
    
    @staticmethod
    def _calculate_rsi(df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate RSI"""
        close = df['Close']
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @staticmethod
    def detect_alignment(analyses: Dict[str, TimeframeAnalysis]) -> tuple:
        """
        Detect timeframe alignment.
        
        Perfect: All same direction
        Strong: 5+ same direction
        Moderate: 3-4 same direction
        Weak: 2 same direction
        """
        if not analyses:
            return TimeframeAlignment.NO_TREND, 0, []
        
        bullish_count = sum(1 for a in analyses.values() if a.trend_direction == "up")
        bearish_count = sum(1 for a in analyses.values() if a.trend_direction == "down")
        neutral_count = sum(1 for a in analyses.values() if a.trend_direction == "neutral")
        
        total = len(analyses)
        
        # Calculate alignment
        if bullish_count == total:
            alignment = TimeframeAlignment.PERFECT_ALIGNMENT
        elif bearish_count == total:
            alignment = TimeframeAlignment.PERFECT_ALIGNMENT
        elif bullish_count >= 5 or bearish_count >= 5:
            alignment = TimeframeAlignment.STRONG_ALIGNMENT
        elif bullish_count >= 3 or bearish_count >= 3:
            alignment = TimeframeAlignment.MODERATE_ALIGNMENT
        elif bullish_count >= 2 or bearish_count >= 2:
            alignment = TimeframeAlignment.WEAK_ALIGNMENT
        elif neutral_count == total:
            alignment = TimeframeAlignment.NO_TREND
        else:
            alignment = TimeframeAlignment.NO_ALIGNMENT
        
        # Alignment score
        max_same = max(bullish_count, bearish_count)
        alignment_score = max_same / total if total > 0 else 0
        
        # Conflicts
        conflicts = []
        if bullish_count > 0 and bearish_count > 0:
            conflicts.append(f"Bullish ({bullish_count}) vs Bearish ({bearish_count})")
        
        return alignment, alignment_score, conflicts
    
    @staticmethod
    def get_overall_direction(analyses: Dict[str, TimeframeAnalysis], weights: Optional[Dict] = None) -> str:
        """
        Weighted overall direction based on timeframe priority.
        
        Higher timeframes (daily, weekly) weighted more.
        """
        if not analyses:
            return "neutral"
        
        if weights is None:
            weights = MultiTimeframeAnalyzer.TIMEFRAME_PRIORITY
        
        bullish_weight = 0
        bearish_weight = 0
        total_weight = 0
        
        for tf, analysis in analyses.items():
            weight = weights.get(tf, 1)
            total_weight += weight
            
            if analysis.trend_direction == "up":
                bullish_weight += weight
            elif analysis.trend_direction == "down":
                bearish_weight += weight
        
        if bullish_weight > bearish_weight:
            return "bullish"
        elif bearish_weight > bullish_weight:
            return "bearish"
        else:
            return "neutral"
    
    @staticmethod
    def analyze_multiframe(symbol: str, timeframes: List[str] = None) -> MultiTimeframeResult:
        """
        Main multi-timeframe analysis.
        
        Default timeframes: 1m, 5m, 15m, 1h, daily, weekly
        """
        if timeframes is None:
            timeframes = ["1m", "5m", "15m", "1h", "daily", "1w"]
        
        analyses = {}
        
        # Fetch and analyze each timeframe
        for tf in timeframes:
            df = MultiTimeframeAnalyzer.fetch_data(symbol, tf)
            if df is not None and len(df) > 10:
                analysis = MultiTimeframeAnalyzer.analyze_timeframe(df)
                analysis.timeframe = tf
                analyses[tf] = analysis
        
        if not analyses:
            return MultiTimeframeResult(
                analyses={},
                alignment=TimeframeAlignment.NO_TREND,
                alignment_score=0,
                overall_direction="neutral",
                highest_tf_direction="neutral",
                lowest_tf_direction="neutral",
                conflicts=[]
            )
        
        # Detect alignment
        alignment, alignment_score, conflicts = MultiTimeframeAnalyzer.detect_alignment(analyses)
        
        # Get overall direction
        overall_dir = MultiTimeframeAnalyzer.get_overall_direction(analyses)
        
        # Get highest and lowest TF directions
        sorted_tf = sorted(analyses.items(), key=lambda x: MultiTimeframeAnalyzer.TIMEFRAME_PRIORITY.get(x[0], 1), reverse=True)
        highest_tf_dir = sorted_tf[0][1].trend_direction if sorted_tf else "neutral"
        lowest_tf_dir = sorted_tf[-1][1].trend_direction if sorted_tf else "neutral"
        
        return MultiTimeframeResult(
            analyses=analyses,
            alignment=alignment,
            alignment_score=alignment_score,
            overall_direction=overall_dir,
            highest_tf_direction=highest_tf_dir,
            lowest_tf_direction=lowest_tf_dir,
            conflicts=conflicts
        )
