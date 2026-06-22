# market_regime.py - Identify current market regime for context-aware trading
# WHY: Same strategy works differently in trending vs consolidating markets
# Breakout strategies work in trending markets (miss money in consolidation)
# Mean reversion strategies work in consolidation (get whipsawed in trends)
# Knowing regime → adapt strategy dynamically

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional
from enum import Enum


class MarketRegime(Enum):
    """Market regime classification."""
    STRONG_UPTREND = "strong_uptrend"      # +20%+ volatility, clear up direction
    UPTREND = "uptrend"                    # EMA20 > EMA50 > EMA200, positive slope
    CONSOLIDATION = "consolidation"       # Range-bound, no clear direction
    DOWNTREND = "downtrend"                # EMA20 < EMA50 < EMA200, negative slope
    STRONG_DOWNTREND = "strong_downtrend"  # -20%+ volatility, clear down direction
    CRASH = "crash"                        # Extreme downside (>10% in short period)


class VolatilityRegime(Enum):
    """Volatility classification."""
    VERY_LOW = "very_low"      # Historical volatility < 10%/year
    LOW = "low"                # HV 10-15%/year (calm market)
    NORMAL = "normal"          # HV 15-25%/year (typical)
    HIGH = "high"              # HV 25-35%/year (nervous market)
    EXTREME = "extreme"        # HV > 35%/year (panic/euphoria)


class MarketRegimeAnalyzer:
    """
    Analyze market structure to understand current regime.
    
    WHY this is important:
    - Bull market: buy dips, hold winners
    - Bear market: sell rallies, avoid catches
    - Consolidation: sell resistance, buy support
    - Breakout: momentum accelerates
    - Reversal: 2x risk often worth taking
    """
    
    @staticmethod
    def detect_regime(df: pd.DataFrame) -> MarketRegime:
        """
        Classify market regime based on EMAs and recent price action.
        
        Logic:
        1. EMA order: uptrend="20>50>200", downtrend="20<50<200"
        2. Recent return: if >10% up/down last 20 bars = strong trend
        3. Default: consolidation
        """
        if len(df) < 200:
            return MarketRegime.CONSOLIDATION
        
        latest = df.iloc[-1]
        
        ema20 = latest.get("EMA_20", np.nan)
        ema50 = latest.get("EMA_50", np.nan)
        ema200 = latest.get("EMA_200", np.nan)
        close = latest.get("Close", np.nan)
        
        # Check if EMAs are ordered properly
        if ema20 > ema50 > ema200:  # Bullish EMA order
            # Check for strong uptrend
            prev_close = df.iloc[-20]["Close"]
            recent_return = (close - prev_close) / prev_close
            
            if recent_return > 0.05:  # 5%+ in 20 bars
                return MarketRegime.STRONG_UPTREND
            else:
                return MarketRegime.UPTREND
        
        elif ema20 < ema50 < ema200:  # Bearish EMA order
            # Check for strong downtrend
            prev_close = df.iloc[-20]["Close"]
            recent_return = (close - prev_close) / prev_close
            
            if recent_return < -0.05:  # 5%+ down in 20 bars
                return MarketRegime.STRONG_DOWNTREND
            else:
                return MarketRegime.DOWNTREND
        
        else:
            # Not clearly ordered - consolidation
            return MarketRegime.CONSOLIDATION
    
    @staticmethod
    def calculate_regime_score(
        df: pd.DataFrame,
        lookback: int = 50
    ) -> Dict[str, float]:
        """
        Calculate numerical scores for each regime (0.0 to 1.0).
        
        Allows softer classification instead of hard categories.
        E.g., 0.6 bullish, 0.3 consolidation, 0.1 bearish
        """
        if len(df) < lookback:
            return {"bullish": 0.33, "neutral": 0.33, "bearish": 0.33}
        
        recent = df.iloc[-lookback:]
        
        # Price slope
        X = np.arange(len(recent))
        y = recent["Close"].values
        z = np.polyfit(X, y, 1)  # Linear regression coefficient
        slope_score = np.tanh(z[0] * 100)  # Normalize to [-1, 1]
        
        # EMA alignment
        latest = df.iloc[-1]
        ema20, ema50, ema200 = (
            latest.get("EMA_20", latest["Close"]),
            latest.get("EMA_50", latest["Close"]),
            latest.get("EMA_200", latest["Close"]),
        )
        
        # Score EMA order
        if ema20 > ema50 > ema200:
            ema_score = 0.8
        elif ema20 > ema50:  # Partial alignment
            ema_score = 0.5
        elif ema50 > ema200:  # Partial alignment
            ema_score = 0.3
        else:
            ema_score = -0.5
        
        # Combine scores
        combined_bullish = (slope_score + ema_score) / 2
        
        # Normalize to probabilities
        bullish = max(0, min(1, (combined_bullish + 1) / 2))
        bearish = 1 - bullish
        neutral = 1 - abs(combined_bullish) / 2
        
        # Renormalize to sum to 1
        total = bullish + neutral + bearish
        
        return {
            "bullish": bullish / total,
            "neutral": neutral / total,
            "bearish": bearish / total,
        }
    
    @staticmethod
    def detect_volatility_regime(df: pd.DataFrame, window: int = 30) -> VolatilityRegime:
        """
        Classify volatility using ATR percentile or HV calculation.
        
        ATR-based approach:
        - Low: ATR in bottom 25% of history
        - Normal: ATR 25-75 percentile
        - High: ATR in top 25% of history
        
        WHY: High volatility = larger stops/targets needed
        """
        if len(df) < window + 50:
            return VolatilityRegime.NORMAL
        
        # Ensure ATR exists
        if "ATR" not in df.columns:
            # Calculate ATR manually
            high_low = df['High'] - df['Low']
            high_close = abs(df['High'] - df['Close'].shift())
            low_close = abs(df['Low'] - df['Close'].shift())
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            df["ATR"] = tr.rolling(14).mean()
        
        atr = df["ATR"].tail(window)
        atr_history = df["ATR"].tail(window + 50)
        
        current_atr = atr.mean()
        p25 = np.percentile(atr_history, 25)
        p75 = np.percentile(atr_history, 75)
        p90 = np.percentile(atr_history, 90)
        
        if current_atr < p25:
            return VolatilityRegime.VERY_LOW
        elif current_atr < p75 * 0.8:
            return VolatilityRegime.LOW
        elif current_atr < p75:
            return VolatilityRegime.NORMAL
        elif current_atr < p90:
            return VolatilityRegime.HIGH
        else:
            return VolatilityRegime.EXTREME
    
    @staticmethod
    def detect_reversals(df: pd.DataFrame, lookback: int = 20) -> Dict[str, bool]:
        """
        Detect potential reversal patterns.
        
        Signals:
        - Price near bollinger band extremes
        - RSI extreme (>80 or <20)
        - MACD divergence (price high but MACD low)
        """
        if len(df) < lookback:
            return {"near_bollinger_top": False, "near_bollinger_bottom": False}
        
        latest = df.iloc[-1]
        
        close = latest["Close"]
        bb_high = latest.get("BB_HIGH", close)
        bb_low = latest.get("BB_LOW", close)
        bb_mid = latest.get("BB_MID", close)
        
        rsi = latest.get("RSI", 50)
        
        # Bollinger Band extremes
        bb_range = bb_high - bb_low
        pct_to_top = (close - bb_mid) / (bb_range / 2) if bb_range > 0 else 0
        
        signals = {
            "near_bollinger_top": pct_to_top > 0.9,      # Price touching top band
            "near_bollinger_bottom": pct_to_top < -0.9,  # Price touching bottom band
            "rsi_overbought": rsi > 80,                  # RSI > 80
            "rsi_oversold": rsi < 20,                    # RSI < 20
        }
        
        # MACD divergence detection
        if len(df) >= lookback * 2:
            recent_closes = df["Close"].tail(lookback)
            recent_macd = df["MACD"].tail(lookback)
            
            close_max_idx = recent_closes.idxmax()
            macd_max_idx = recent_macd.idxmax()
            
            # Divergence = prices making new high but MACD doesn't
            if close_max_idx != macd_max_idx:
                signals["bearish_divergence"] = close_max_idx > macd_max_idx
            else:
                signals["bearish_divergence"] = False
        
        return signals
    
    @staticmethod
    def regime_based_strategy_params(regime: MarketRegime) -> Dict:
        """
        Adapt trading parameters based on market regime.
        
        WHY different params:
        - Uptrend: bigger stops, follow momentum
        - Downtrend: opposite
        - Consolidation: tight stops, reversal trades
        - Crash: avoid, preserve capital
        
        These are multipliers for your base strategy parameters.
        """
        
        params = {
            MarketRegime.STRONG_UPTREND: {
                "buy_threshold": 0.55,      # Lower threshold, momentum favors us
                "sell_threshold": 0.45,
                "position_size_multiplier": 1.2,  # Larger positions
                "stop_distance_multiplier": 1.0,  # Normal stops
                "target_multiplier": 1.5,   # Bigger targets (let winners run)
                "trade_type": "trend_following",
            },
            MarketRegime.UPTREND: {
                "buy_threshold": 0.60,
                "sell_threshold": 0.40,
                "position_size_multiplier": 1.0,
                "stop_distance_multiplier": 1.0,
                "target_multiplier": 1.2,
                "trade_type": "trend_following",
            },
            MarketRegime.CONSOLIDATION: {
                "buy_threshold": 0.70,      # Higher threshold needed
                "sell_threshold": 0.30,
                "position_size_multiplier": 0.7,  # Smaller positions
                "stop_distance_multiplier": 0.8,  # Tighter stops
                "target_multiplier": 0.8,   # Smaller targets (quick scalps)
                "trade_type": "mean_reversion",
            },
            MarketRegime.DOWNTREND: {
                "buy_threshold": 0.70,      # Much higher - go short instead
                "sell_threshold": 0.30,
                "position_size_multiplier": 0.8,
                "stop_distance_multiplier": 1.0,
                "target_multiplier": 1.2,
                "trade_type": "trend_following",
            },
            MarketRegime.STRONG_DOWNTREND: {
                "buy_threshold": 0.80,      # Almost never buy
                "sell_threshold": 0.20,
                "position_size_multiplier": 0.5,  # Avoid market
                "stop_distance_multiplier": 1.5,  # Bigger stops
                "target_multiplier": 0.8,   # Smaller targets
                "trade_type": "trend_following",
            },
            MarketRegime.CRASH: {
                "buy_threshold": 0.99,      # Don't trade (buy threshold almost impossible)
                "sell_threshold": -0.99,
                "position_size_multiplier": 0.1,  # Avoid entirely
                "stop_distance_multiplier": 2.0,
                "target_multiplier": 0.5,
                "trade_type": "avoid",
            },
        }
        
        return params.get(regime, params[MarketRegime.CONSOLIDATION])
    
    @staticmethod
    def market_health_check(df: pd.DataFrame) -> Dict:
        """
        Overall market health assessment.
        
        Returns warning flags for dangerous conditions:
        - Gap down opening (high slippage risk)
        - Extreme volume (distribution/accumulation)
        - Volatility spike (fundamental event)
        """
        if len(df) < 20:
            return {"is_healthy": True, "warnings": []}
        
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        
        warnings = []
        
        # Check for gaps
        gap_pct = abs(latest["Open"] - prev["Close"]) / prev["Close"]
        if gap_pct > 0.03:  # 3%+ gap
            warnings.append(f"Large gap ({gap_pct:.1%}) - beware of slippage")
        
        # Check volume spike
        avg_volume = df["Volume"].tail(20).mean()
        volume_spike = latest["Volume"] / avg_volume
        if volume_spike > 2.0:
            warnings.append(f"Volume spike ({volume_spike:.1f}x) - strong conviction move")
        
        # Check for extreme moves
        recent_range = df.iloc[-5:]["High"].max() - df.iloc[-5:]["Low"].min()
        typical_range = df["ATR"].tail(20).mean() * 2
        if recent_range > typical_range * 1.5:
            warnings.append("Extreme volatility - expect wider stops/targets")
        
        is_healthy = len(warnings) == 0
        
        return {
            "is_healthy": is_healthy,
            "warnings": warnings,
            "safe_to_trade": len(warnings) <= 1,
        }


# ════════════════════════════════════════════════════════════════════════════════
# EXAMPLE USAGE
# ════════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Market Regime Analyzer module loaded.")
    print("Features:")
    print("  • Detect market regime (trend/consolidation/crash)")
    print("  • Classify volatility (low/normal/extreme)")
    print("  • Detect reversals and divergences")
    print("  • Adapt strategy parameters by regime")
    print("  • Market health checks")
