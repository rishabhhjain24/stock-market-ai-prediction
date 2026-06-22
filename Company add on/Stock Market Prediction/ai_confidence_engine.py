# ai_confidence_engine.py - Comprehensive confidence scoring for all signals
# WHY: Combines all data sources into single confidence metric
# Scoring: Price action, volume, technicals, sentiment, patterns, regime = Final AI Score

import pandas as pd
import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum

@dataclass
class ConfidenceComponents:
    """Breakdown of confidence scoring"""
    price_action_score: float
    volume_score: float
    technical_score: float
    pattern_score: float
    sentiment_score: float
    regime_score: float
    timeframe_score: float
    overall_score: float  # 0-100
    signal_type: str  # "VERY_STRONG", "STRONG", "MODERATE", "WEAK", "INVALID"

class AIConfidenceEngine:
    """AI-powered confidence scoring engine"""
    
    SCORE_WEIGHTS = {
        "price_action": 0.25,    # 25% weight
        "volume": 0.20,          # 20% weight
        "technical": 0.20,       # 20% weight
        "pattern": 0.10,         # 10% weight
        "sentiment": 0.15,       # 15% weight
        "regime": 0.10           # 10% weight
    }
    
    @staticmethod
    def score_price_action(price_action_data: Dict) -> float:
        """
        Score price action quality.
        
        Inputs:
        - trend_strength: "very_strong" to "flat" (convert to 0-1)
        - higher_highs: count
        - breakout: quality + confirmation
        - momentum_strength: 0-1
        - wick_rejection: bool
        """
        if not price_action_data:
            return 0.5
        
        score = 0
        
        # Trend strength component
        trend_map = {
            "very_strong": 1.0,
            "strong": 0.8,
            "moderate": 0.6,
            "weak": 0.3,
            "flat": 0.0
        }
        trend_val = price_action_data.get("trend_strength", "weak")
        if isinstance(trend_val, str):
            trend_score = trend_map.get(trend_val, 0.5)
        else:
            trend_score = 0.5
        
        score += trend_score * 0.4
        
        # Breakout component
        if price_action_data.get("breakout"):
            breakout = price_action_data["breakout"]
            quality_map = {
                "very_strong": 1.0,
                "strong": 0.8,
                "moderate": 0.5,
                "weak": 0.2
            }
            quality_score = quality_map.get(breakout.get("quality", "weak"), 0.2)
            score += quality_score * 0.3
        
        # Momentum component
        momentum = price_action_data.get("momentum_strength", 0.5)
        score += momentum * 0.2
        
        # Wick rejection bonus
        if price_action_data.get("wick_rejection"):
            score += 0.1
        
        return min(1.0, score)
    
    @staticmethod
    def score_volume(volume_data: Dict) -> float:
        """
        Score volume quality.
        
        Inputs:
        - signal: accumulation/distribution/volume_spike/breakout_confirmed/normal
        - volume_trend: increasing/decreasing/stable
        - accumulation_score: 0-1
        - breakout_confirmation: bool + confidence
        """
        if not volume_data:
            return 0.5
        
        score = 0
        
        # Signal quality
        signal = volume_data.get("signal", "normal")
        signal_scores = {
            "accumulation": 0.9,
            "distribution": 0.7,
            "volume_spike": 0.8,
            "breakout_confirmed": 0.95,
            "breakout_unconfirmed": 0.4,
            "normal": 0.3,
            "no_demand": 0.1
        }
        
        score += signal_scores.get(signal, 0.3) * 0.6
        
        # Volume trend
        trend = volume_data.get("volume_trend", "stable")
        trend_scores = {
            "increasing": 0.8,
            "stable": 0.5,
            "decreasing": 0.2
        }
        
        score += trend_scores.get(trend, 0.5) * 0.3
        
        # Accumulation score
        acc_score = volume_data.get("accumulation_score", 0.5)
        score += acc_score * 0.1
        
        # Confidence boost
        confidence = volume_data.get("signal_confidence", 0.5)
        score = score * 0.7 + confidence * 0.3
        
        return min(1.0, score)
    
    @staticmethod
    def score_technical(technical_data: Dict) -> float:
        """
        Score technical indicators alignment.
        
        Inputs:
        - rsi_signal: 0-1
        - macd_signal: 0-1
        - bollinger_position: 0-1
        - ema_alignment: 0-1
        - indicator_count: how many aligned
        """
        if not technical_data:
            return 0.5
        
        indicators_count = 0
        total_score = 0
        
        # RSI score
        if "rsi" in technical_data:
            rsi = technical_data["rsi"]
            if 40 <= rsi <= 60:
                rsi_score = 0.5
            elif (30 < rsi < 40) or (60 < rsi < 70):
                rsi_score = 0.7
            elif rsi < 20 or rsi > 80:
                rsi_score = 0.9
            else:
                rsi_score = 0.3
            total_score += rsi_score
            indicators_count += 1
        
        # MACD score
        if "macd_histogram" in technical_data:
            macd = abs(technical_data["macd_histogram"])
            macd_score = min(1.0, macd / 100)  # Normalize
            total_score += macd_score
            indicators_count += 1
        
        # EMA alignment
        if "ema_aligned" in technical_data:
            ema_score = 0.9 if technical_data["ema_aligned"] else 0.3
            total_score += ema_score
            indicators_count += 1
        
        # Bollinger position
        if "bb_position" in technical_data:
            bb = technical_data["bb_position"]
            if bb > 0.7 or bb < 0.3:
                bb_score = 0.8
            elif bb > 0.5 or bb < 0.5:
                bb_score = 0.5
            else:
                bb_score = 0.3
            total_score += bb_score
            indicators_count += 1
        
        if indicators_count == 0:
            return 0.5
        
        return min(1.0, total_score / indicators_count)
    
    @staticmethod
    def score_pattern(pattern_data: Dict) -> float:
        """
        Score chart pattern quality.
        
        Inputs:
        - detected_patterns: list with confidence scores
        - pattern_count: how many patterns confirmed
        """
        if not pattern_data or "detected_patterns" not in pattern_data:
            return 0
        
        patterns = pattern_data.get("detected_patterns", [])
        
        if not patterns:
            return 0
        
        # Best pattern confidence
        best_confidence = max([p.get("confidence", 0) for p in patterns])
        
        # Pattern count bonus (more = better)
        pattern_bonus = min(0.2, len(patterns) * 0.05)
        
        return min(1.0, best_confidence + pattern_bonus)
    
    @staticmethod
    def score_sentiment(sentiment_data: Dict) -> float:
        """
        Score sentiment.
        
        Inputs:
        - news_sentiment: -1 to 1
        - sentiment_confidence: 0-1
        - social_sentiment: -1 to 1 (if available)
        """
        if not sentiment_data:
            return 0.5
        
        score = 0.5
        
        # News sentiment
        if "news_sentiment" in sentiment_data:
            news = sentiment_data["news_sentiment"]
            if news > 0.3:
                score += 0.25
            elif news > 0:
                score += 0.1
            elif news < -0.3:
                score -= 0.25
            elif news < 0:
                score -= 0.1
        
        # Confidence
        if "sentiment_confidence" in sentiment_data:
            conf = sentiment_data["sentiment_confidence"]
            score = score * 0.7 + conf * 0.3
        
        return min(1.0, max(0, score))
    
    @staticmethod
    def score_regime(regime_data: Dict) -> float:
        """
        Score market regime favorability.
        
        Inputs:
        - regime: "strong_uptrend" to "crash"
        - volatility: "very_low" to "extreme"
        """
        if not regime_data:
            return 0.5
        
        score = 0
        
        # Market regime
        regime = regime_data.get("regime", "neutral")
        regime_scores = {
            "strong_uptrend": 0.9,
            "uptrend": 0.7,
            "consolidation": 0.5,
            "downtrend": 0.3,
            "strong_downtrend": 0.1,
            "crash": 0.0
        }
        
        score += regime_scores.get(regime, 0.5) * 0.6
        
        # Volatility
        vol = regime_data.get("volatility", "normal")
        vol_scores = {
            "very_low": 0.3,
            "low": 0.5,
            "normal": 0.8,
            "high": 0.6,
            "extreme": 0.2
        }
        
        score += vol_scores.get(vol, 0.5) * 0.4
        
        return min(1.0, score)
    
    @staticmethod
    def score_timeframe_alignment(mtf_data: Dict) -> float:
        """
        Score multi-timeframe alignment.
        
        Inputs:
        - alignment: "perfect" to "none"
        - alignment_score: 0-1
        """
        if not mtf_data:
            return 0.5
        
        alignment = mtf_data.get("alignment", "weak")
        alignment_map = {
            "perfect": 1.0,
            "strong": 0.85,
            "moderate": 0.65,
            "weak": 0.4,
            "none": 0.0,
            "no_trend": 0.3
        }
        
        score = alignment_map.get(alignment, 0.5)
        
        # Bonus for explicit alignment score
        if "alignment_score" in mtf_data:
            score = score * 0.7 + mtf_data["alignment_score"] * 0.3
        
        return min(1.0, score)
    
    @staticmethod
    def calculate_overall_confidence(
        price_action: Dict = None,
        volume: Dict = None,
        technical: Dict = None,
        pattern: Dict = None,
        sentiment: Dict = None,
        regime: Dict = None,
        timeframe: Dict = None
    ) -> ConfidenceComponents:
        """
        Calculate overall AI confidence score.
        
        Combines all components with defined weights.
        """
        # Individual scores
        pa_score = AIConfidenceEngine.score_price_action(price_action or {})
        vol_score = AIConfidenceEngine.score_volume(volume or {})
        tech_score = AIConfidenceEngine.score_technical(technical or {})
        patt_score = AIConfidenceEngine.score_pattern(pattern or {})
        sent_score = AIConfidenceEngine.score_sentiment(sentiment or {})
        reg_score = AIConfidenceEngine.score_regime(regime or {})
        tf_score = AIConfidenceEngine.score_timeframe_alignment(timeframe or {})
        
        # Weighted overall score
        overall = (
            pa_score * 0.25 +
            vol_score * 0.20 +
            tech_score * 0.20 +
            patt_score * 0.10 +
            sent_score * 0.15 +
            reg_score * 0.10
        )
        
        # Timeframe alignment as multiplier
        if timeframe:
            overall = overall * (0.7 + tf_score * 0.3)
        
        overall = min(1.0, max(0, overall))
        overall_pct = overall * 100
        
        # Signal type
        if overall_pct >= 85:
            signal_type = "VERY_STRONG"
        elif overall_pct >= 70:
            signal_type = "STRONG"
        elif overall_pct >= 55:
            signal_type = "MODERATE"
        elif overall_pct >= 40:
            signal_type = "WEAK"
        else:
            signal_type = "INVALID"
        
        return ConfidenceComponents(
            price_action_score=pa_score * 100,
            volume_score=vol_score * 100,
            technical_score=tech_score * 100,
            pattern_score=patt_score * 100,
            sentiment_score=sent_score * 100,
            regime_score=reg_score * 100,
            timeframe_score=tf_score * 100,
            overall_score=overall_pct,
            signal_type=signal_type
        )
