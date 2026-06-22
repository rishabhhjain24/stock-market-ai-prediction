# chart_patterns.py - Detect technical chart patterns for trading signals
# WHY: Chart patterns are visual formations that predict likely price movements
# Head & Shoulders = reversal pattern (strong bearish)
# Double Top/Bottom = reversal pattern  
# Triangles = continuation pattern
# These patterns have 60-70% accuracy when combined with volume confirmation

import numpy as np
import pandas as pd
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass


@dataclass
class Pattern:
    """Dataclass to store pattern detection results."""
    name: str
    type: str  # "bullish", "bearish", "neutral"
    confidence: float  # 0.0 to 1.0
    start_idx: int
    end_idx: int
    description: str
    entry_price: float
    target_price: float
    stop_loss: float


def find_local_maxima(data: np.ndarray, window: int = 5) -> np.ndarray:
    """
    Find local peaks (maxima) in price data.
    WHY: Peaks are resistance levels and potential reversals.
    """
    maxima = np.array([False] * len(data))
    for i in range(window, len(data) - window):
        if data[i] == np.max(data[i - window : i + window + 1]):
            maxima[i] = True
    return maxima


def find_local_minima(data: np.ndarray, window: int = 5) -> np.ndarray:
    """
    Find local troughs (minima) in price data.
    WHY: Troughs are support levels and potential bounces.
    """
    minima = np.array([False] * len(data))
    for i in range(window, len(data) - window):
        if data[i] == np.min(data[i - window : i + window + 1]):
            minima[i] = True
    return minima


def detect_head_and_shoulders(
    df: pd.DataFrame, 
    lookback: int = 50
) -> Optional[Pattern]:
    """
    Detect Head & Shoulders pattern - a strong bearish reversal.
    
    Structure:
    - Left shoulder: peak
    - Head: higher peak
    - Right shoulder: lower peak than head, similar to left shoulder
    - Neckline: support level connecting the shoulders
    - Prediction: Price breaks neckline → strong downtrend
    
    WHY important:
    - One of the most reliable reversal patterns
    - Appears after uptrends
    - Provides clear entry (neckline break) and stop (head)
    - Win rate: ~65-70% historically
    """
    if len(df) < lookback:
        return None
    
    closes = df["Close"].values[-lookback:]
    highs = df["High"].values[-lookback:]
    lows = df["Low"].values[-lookback:]
    volume = df["Volume"].values[-lookback:]
    
    # Find local maxima for shoulders and head
    maxima_idx = np.where(find_local_maxima(highs, window=5))[0]
    
    # Need at least 3 peaks
    if len(maxima_idx) < 3:
        return None
    
    # Look at last 3 peaks
    idx_right_shoulder = maxima_idx[-1]
    idx_head = maxima_idx[-2]
    idx_left_shoulder = maxima_idx[-3]
    
    left_peak = highs[idx_left_shoulder]
    head_peak = highs[idx_head]
    right_peak = highs[idx_right_shoulder]
    
    left_trough = np.min(lows[idx_left_shoulder:idx_head])
    head_trough = np.min(lows[idx_head:idx_right_shoulder])
    right_trough = np.min(lows[idx_right_shoulder:])
    
    neckline = (left_trough + head_trough) / 2
    
    # Validation checks
    # Head should be highest
    if head_peak <= max(left_peak, right_peak):
        return None
    
    # Shoulders should be similar height (within 5%)
    shoulder_ratio = abs(left_peak - right_peak) / min(left_peak, right_peak)
    if shoulder_ratio > 0.05:
        return None
    
    # Right shoulder neckline touch (volume should decrease)
    right_shoulder_volume = np.mean(volume[idx_right_shoulder : idx_right_shoulder + 5])
    head_volume = np.mean(volume[idx_head : idx_head + 5])
    
    if right_shoulder_volume > head_volume:  # Volume confirmation
        confidence = 0.75
    else:
        confidence = 0.65
    
    # Target: distance from head to neckline, projected downward
    distance = head_peak - neckline
    target = neckline - distance
    
    current_price = closes[-1]
    
    return Pattern(
        name="Head & Shoulders",
        type="bearish",
        confidence=min(confidence, 1.0),
        start_idx=len(df) - lookback + idx_left_shoulder,
        end_idx=len(df) - lookback + idx_right_shoulder,
        description=f"Bearish reversal at neckline {neckline:.2f}",
        entry_price=neckline,
        target_price=target,
        stop_loss=head_peak + (head_peak - neckline) * 0.1,
    )


def detect_double_top(
    df: pd.DataFrame,
    lookback: int = 50
) -> Optional[Pattern]:
    """
    Detect Double Top pattern - bearish reversal at resistance.
    
    Structure:
    - Two peaks at approximately same height
    - Valley between peaks (support level)
    - Break below support confirms reversal
    
    WHY important:
    - Reversal from uptrend
    - Clear entry (valley break)
    - Well-defined stops (above peaks)
    - Win rate: ~55-60%
    """
    if len(df) < lookback:
        return None
    
    closes = df["Close"].values[-lookback:]
    highs = df["High"].values[-lookback:]
    lows = df["Low"].values[-lookback:]
    
    maxima_idx = np.where(find_local_maxima(highs, window=5))[0]
    
    if len(maxima_idx) < 2:
        return None
    
    idx_first_top = maxima_idx[-2]
    idx_second_top = maxima_idx[-1]
    
    first_top = highs[idx_first_top]
    second_top = highs[idx_second_top]
    
    # Tops should be very similar (within 3%)
    top_ratio = abs(first_top - second_top) / min(first_top, second_top)
    if top_ratio > 0.03:
        return None
    
    # Valley between tops
    valley = np.min(lows[idx_first_top:idx_second_top])
    
    support = valley
    resistance = (first_top + second_top) / 2
    current_price = closes[-1]
    
    distance = resistance - support
    target = support - distance
    
    return Pattern(
        name="Double Top",
        type="bearish",
        confidence=0.60,
        start_idx=len(df) - lookback + idx_first_top,
        end_idx=len(df) - lookback + idx_second_top,
        description=f"Double top at {resistance:.2f}, break support at {support:.2f}",
        entry_price=support,
        target_price=target,
        stop_loss=resistance * 1.02,
    )


def detect_double_bottom(
    df: pd.DataFrame,
    lookback: int = 50
) -> Optional[Pattern]:
    """
    Detect Double Bottom pattern - bullish reversal at support.
    
    This is the inverse of Double Top.
    - Two troughs at approximately same level
    - Peak between troughs
    - Break above peak confirms reversal
    
    WHY important:
    - Reversal from downtrend  
    - Clear entry (peak break)
    - Similar to double top but bullish
    - Win rate: ~55-60%
    """
    if len(df) < lookback:
        return None
    
    closes = df["Close"].values[-lookback:]
    highs = df["High"].values[-lookback:]
    lows = df["Low"].values[-lookback:]
    
    minima_idx = np.where(find_local_minima(lows, window=5))[0]
    
    if len(minima_idx) < 2:
        return None
    
    idx_first_bottom = minima_idx[-2]
    idx_second_bottom = minima_idx[-1]
    
    first_bottom = lows[idx_first_bottom]
    second_bottom = lows[idx_second_bottom]
    
    # Bottoms should be very similar (within 3%)
    bottom_ratio = abs(first_bottom - second_bottom) / min(first_bottom, second_bottom)
    if bottom_ratio > 0.03:
        return None
    
    # Peak between bottoms
    peak = np.max(highs[idx_first_bottom:idx_second_bottom])
    
    support = (first_bottom + second_bottom) / 2
    
    distance = peak - support
    target = peak + distance
    
    return Pattern(
        name="Double Bottom",
        type="bullish",
        confidence=0.60,
        start_idx=len(df) - lookback + idx_first_bottom,
        end_idx=len(df) - lookback + idx_second_bottom,
        description=f"Double bottom at {support:.2f}, break resistance at {peak:.2f}",
        entry_price=peak,
        target_price=target,
        stop_loss=support * 0.98,
    )


def detect_ascending_triangle(
    df: pd.DataFrame,
    lookback: int = 50
) -> Optional[Pattern]:
    """
    Detect Ascending Triangle - bullish continuation pattern.
    
    Structure:
    - Higher lows (rising trendline)
    - Flat resistance level (multiple touches)
    - Volatile breakout above resistance
    
    WHY important:
    - Signals building momentum
    - Before big breakout moves
    - Clear short-term momentum
    """
    if len(df) < lookback:
        return None
    
    closes = df["Close"].values[-lookback:]
    highs = df["High"].values[-lookback:]
    lows = df["Low"].values[-lookback:]
    
    # Look for series of higher lows
    lows_recent = lows[-40:]
    
    # Find resistance (flat top)
    resistance = np.percentile(highs[-40:], 90)
    
    # Check for higher lows
    minima_indices = np.where(find_local_minima(lows_recent, window=3))[0]
    if len(minima_indices) < 3:
        return None
    
    # Verify higher lows
    minima_values = lows_recent[minima_indices]
    if not all(minima_values[i] < minima_values[i + 1] for i in range(len(minima_values) - 1)):
        return None
    
    target = resistance + (resistance - minima_values[-1])
    
    return Pattern(
        name="Ascending Triangle",
        type="bullish",
        confidence=0.58,
        start_idx=len(df) - 40,
        end_idx=len(df) - 1,
        description=f"Bullish triangle with breakout target at {target:.2f}",
        entry_price=resistance,
        target_price=target,
        stop_loss=minima_values[-1],
    )


def detect_all_patterns(df: pd.DataFrame, lookback: int = 50) -> List[Pattern]:
    """
    Scan for all chart patterns in the given data.
    
    WHY this consolidated function:
    - Single call to get all patterns
    - Easy integration into trading system
    - Patterns can be weighted/scored
    
    Returns: list of detected patterns sorted by confidence
    """
    patterns: List[Pattern] = []
    
    # Try each pattern detection
    h_s = detect_head_and_shoulders(df, lookback)
    if h_s:
        patterns.append(h_s)
    
    double_top = detect_double_top(df, lookback)
    if double_top:
        patterns.append(double_top)
    
    double_bottom = detect_double_bottom(df, lookback)
    if double_bottom:
        patterns.append(double_bottom)
    
    asc_tri = detect_ascending_triangle(df, lookback)
    if asc_tri:
        patterns.append(asc_tri)
    
    # Sort by confidence
    patterns.sort(key=lambda p: p.confidence, reverse=True)
    
    return patterns


def patterns_to_signal(patterns: List[Pattern]) -> Dict:
    """
    Convert detected patterns into a trading signal.
    
    WHY:
    - Multiple patterns increase signal confidence
    - Patterns with same direction are more reliable
    - Use for bias adjustment to ML model
    """
    if not patterns:
        return {
            "direction": None,
            "confidence": 0.0,
            "patterns": [],
            "recommendation": "No clear patterns detected"
        }
    
    bullish_count = sum(1 for p in patterns if p.type == "bullish")
    bearish_count = sum(1 for p in patterns if p.type == "bearish")
    
    if bullish_count > bearish_count:
        direction = "BULLISH"
        confidence = min(bullish_count * 0.2 + patterns[0].confidence, 1.0)
    elif bearish_count > bullish_count:
        direction = "BEARISH"
        confidence = min(bearish_count * 0.2 + patterns[0].confidence, 1.0)
    else:
        direction = "NEUTRAL"
        confidence = 0.5
    
    return {
        "direction": direction,
        "confidence": confidence,
        "pattern_count": len(patterns),
        "strongest_pattern": patterns[0].name if patterns else None,
        "patterns": [
            {
                "name": p.name,
                "type": p.type,
                "confidence": p.confidence,
                "entry": p.entry_price,
                "target": p.target_price,
                "stop": p.stop_loss,
                "description": p.description,
            }
            for p in patterns
        ],
    }


# ════════════════════════════════════════════════════════════════════════════════
# EXAMPLE USAGE
# ════════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # This would be used with your data_engine
    # from data_engine import get_features
    # df = get_features("RELIANCE.NS")
    # patterns = detect_all_patterns(df)
    # signal = patterns_to_signal(patterns)
    print("Chart pattern detection module loaded successfully.")
    print("Detects: Head & Shoulders, Double Top/Bottom, Ascending Triangle")
