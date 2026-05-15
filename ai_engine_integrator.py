# ai_engine_integrator.py - Integrates all 12 AI engines into unified pipeline
# WHY: Combines advanced price action, volume, timeframe, confidence for production-ready signals
# Unified signal generation

import pandas as pd
import yfinance as yf
from typing import Dict, Optional, List
from dataclasses import asdict
import numpy as np
import logging

from advanced_price_action import AdvancedPriceAction, PriceActionAnalysis
from advanced_volume_analysis import AdvancedVolumeAnalysis, VolumeAnalysis
from multi_timeframe_analyzer import MultiTimeframeAnalyzer, MultiTimeframeResult
from scalp_engine import ScalpEngine, ScalpOpportunity
from ai_confidence_engine import AIConfidenceEngine, ConfidenceComponents
from data_engine import get_features
from market_regime import MarketRegimeAnalyzer
from chart_patterns import detect_all_patterns
from sentiment_engine import sentiment_analysis_report

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class UnifiedSignal:
    """Complete AI signal with all components"""
    
    def __init__(self):
        self.symbol: str = ""
        self.timestamp: str = ""
        self.current_price: float = 0
        
        # Core analyses
        self.price_action: Optional[PriceActionAnalysis] = None
        self.volume_analysis: Optional[VolumeAnalysis] = None
        self.multi_timeframe: Optional[MultiTimeframeResult] = None
        self.scalp_opportunities: List[ScalpOpportunity] = []
        
        # AI confidence
        self.confidence: Optional[ConfidenceComponents] = None
        
        # Final recommendation
        self.recommendation: str = "NEUTRAL"  # BUY, SELL, HOLD, NEUTRAL
        self.target_price: float = 0
        self.stop_loss: float = 0
        self.risk_reward: float = 0
        
        # Reasons
        self.reasons: List[str] = []

class AIEngineIntegrator:
    """Integrates all 12 engines into unified trading signal"""
    
    @staticmethod
    def enrich_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Add all indicators to dataframe"""
        if df is None or len(df) == 0:
            return df
        
        df = df.copy()
        
        # Reset index if needed
        if not isinstance(df.index, pd.RangeIndex):
            df.reset_index(inplace=True)
        
        # Add EMA if missing
        if 'EMA_20' not in df.columns:
            df['EMA_20'] = df['Close'].ewm(span=20).mean()
        if 'EMA_50' not in df.columns:
            df['EMA_50'] = df['Close'].ewm(span=50).mean()
        if 'EMA_200' not in df.columns:
            df['EMA_200'] = df['Close'].ewm(span=200).mean()
        
        # Add RSI if missing
        if 'RSI' not in df.columns:
            close = df['Close']
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
            rs = gain / loss
            df['RSI'] = 100 - (100 / (1 + rs))
        
        # Add ATR if missing (for volatility)
        if 'ATR' not in df.columns:
            high_low = df['High'] - df['Low']
            high_close = abs(df['High'] - df['Close'].shift())
            low_close = abs(df['Low'] - df['Close'].shift())
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            df['ATR'] = tr.rolling(14).mean()
        
        # Add MACD if missing
        if 'MACD' not in df.columns:
            exp1 = df['Close'].ewm(span=12).mean()
            exp2 = df['Close'].ewm(span=26).mean()
            df['MACD'] = exp1 - exp2
            df['MACD_SIGNAL'] = df['MACD'].ewm(span=9).mean()
        
        # Add Bollinger Bands if missing
        if 'BB_HIGH' not in df.columns:
            sma = df['Close'].rolling(20).mean()
            std = df['Close'].rolling(20).std()
            df['BB_HIGH'] = sma + (std * 2)
            df['BB_LOW'] = sma - (std * 2)
            df['BB_MID'] = sma
        
        return df
    
    @staticmethod
    def generate_unified_signal(symbol: str, timeframe: str = "1h") -> Optional[UnifiedSignal]:
        """
        Generate complete unified signal across all 12 engines.
        
        Process:
        1. Fetch data for timeframe
        2. Run price action analysis
        3. Run volume analysis
        4. Run multi-timeframe (1m-weekly)
        5. Detect scalp opportunities
        6. Calculate AI confidence
        7. Generate final recommendation
        """
        
        try:
            # Fetch data
            logger.info(f"Fetching data for {symbol}...")
            
            # Map timeframe
            tf_map = {
                "1m": "1m", "3m": "3m", "5m": "5m", "15m": "15m",
                "1h": "1h", "daily": "1d", "1d": "1d",
                "weekly": "1wk", "1w": "1wk"
            }
            tf_mapped = tf_map.get(timeframe, "1h")
            
            # Get historical data (try multiple windows for robustness)
            df = None
            attempts = [("1y", tf_mapped), ("90d", tf_mapped), ("60d", tf_mapped), ("30d", tf_mapped)]
            for period, interval in attempts:
                try:
                    logger.info(f"Trying yfinance download: {symbol} period={period} interval={interval}")
                    tmp = yf.download(symbol, period=period, interval=interval, progress=False)
                    if tmp is not None and len(tmp) >= 20:
                        df = tmp
                        logger.info(f"Data fetched for {symbol} with period={period}, rows={len(df)}")
                        break
                    else:
                        logger.warning(f"Not enough rows for {symbol} with period={period} (rows={0 if tmp is None else len(tmp)})")
                except Exception as e:
                    logger.warning(f"yfinance attempt failed for {symbol} period={period}: {e}")

            if df is None or len(df) < 20:
                logger.error(f"Insufficient data for {symbol} after multiple attempts")
                return None
            
            # Enrich with indicators
            df = AIEngineIntegrator.enrich_dataframe(df)
            
            # Create signal object
            signal = UnifiedSignal()
            signal.symbol = symbol
            signal.timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
            signal.current_price = df['Close'].iloc[-1]
            
            # Engine 1: Price Action
            logger.info("Running price action analysis...")
            signal.price_action = AdvancedPriceAction.analyze(df, lookback_trend=20, lookback_sr=100)
            
            # Engine 2: Volume Analysis
            logger.info("Running volume analysis...")
            signal.volume_analysis = AdvancedVolumeAnalysis.analyze(df, lookback=20)
            
            # Engine 3: Multi-Timeframe Alignment
            logger.info("Running multi-timeframe analysis...")
            signal.multi_timeframe = MultiTimeframeAnalyzer.analyze_multiframe(symbol, timeframes=["1m", "5m", "15m", "1h", "daily", "1wk"])
            
            # Engine 4: Scalping Opportunities
            logger.info("Detecting scalp opportunities...")
            signal.scalp_opportunities = ScalpEngine.find_all_scalp_opportunities(df, symbol=symbol)
            
            # Engine 7: Market Regime (for confidence)
            logger.info("Analyzing market regime...")
            regime = MarketRegimeAnalyzer.detect_regime(df)
            volatility = MarketRegimeAnalyzer.detect_volatility_regime(df)
            
            # Engine 8: Chart Patterns
            logger.info("Detecting chart patterns...")
            patterns = detect_all_patterns(df)
            
            # Prepare data for confidence scoring
            price_action_data = {
                "trend_strength": signal.price_action.trend_strength.value if signal.price_action else "weak",
                "higher_highs": signal.price_action.higher_highs if signal.price_action else 0,
                "breakout": {
                    "quality": signal.price_action.breakout.quality.value
                } if signal.price_action and signal.price_action.breakout else None,
                "momentum_strength": signal.price_action.momentum_strength if signal.price_action else 0.5,
                "wick_rejection": signal.price_action.wick_rejection if signal.price_action else False
            }
            
            volume_data = {
                "signal": signal.volume_analysis.signal.value if signal.volume_analysis else "normal",
                "volume_trend": signal.volume_analysis.volume_trend if signal.volume_analysis else "stable",
                "accumulation_score": signal.volume_analysis.accumulation_score if signal.volume_analysis else 0.5,
                "signal_confidence": signal.volume_analysis.signal_confidence if signal.volume_analysis else 0.5
            }
            
            regime_data = {
                "regime": regime.value if regime else "consolidation",
                "volatility": volatility.value if volatility else "normal"
            }
            
            mtf_data = {
                "alignment": signal.multi_timeframe.alignment.value if signal.multi_timeframe else "none",
                "alignment_score": signal.multi_timeframe.alignment_score if signal.multi_timeframe else 0
            }
            
            # Engine 5-6: AI Confidence Scoring
            logger.info("Calculating AI confidence...")
            signal.confidence = AIConfidenceEngine.calculate_overall_confidence(
                price_action=price_action_data,
                volume=volume_data,
                regime=regime_data,
                timeframe=mtf_data,
                pattern={"detected_patterns": patterns if patterns else []}
            )
            
            # Engine 13: Generate Final Recommendation
            signal = AIEngineIntegrator._generate_recommendation(signal, df)
            
            logger.info(f"Signal generated: {signal.recommendation} (confidence: {signal.confidence.overall_score:.1f}%)")
            
            return signal
        
        except Exception as e:
            logger.error(f"Error generating signal for {symbol}: {e}", exc_info=True)
            return None
    
    @staticmethod
    def _generate_recommendation(signal: UnifiedSignal, df: pd.DataFrame) -> UnifiedSignal:
        """Generate final buy/sell/hold recommendation"""
        
        if not signal.price_action or not signal.volume_analysis or not signal.confidence:
            signal.recommendation = "NEUTRAL"
            return signal
        
        confidence_score = signal.confidence.overall_score / 100
        
        # Determine direction
        bullish_signals = 0
        bearish_signals = 0
        
        # Price action
        if signal.price_action.trend_strength.value == "strong" or signal.price_action.trend_strength.value == "very_strong":
            if signal.price_action.higher_highs > signal.price_action.lower_highs:
                bullish_signals += 2
            else:
                bearish_signals += 2
        
        # Volume
        if signal.volume_analysis.signal.value in ["accumulation", "breakout_confirmed"]:
            bullish_signals += 1
        elif signal.volume_analysis.signal.value == "distribution":
            bearish_signals += 1
        
        # Timeframe alignment
        if signal.multi_timeframe and signal.multi_timeframe.overall_direction == "bullish":
            bullish_signals += 2
        elif signal.multi_timeframe and signal.multi_timeframe.overall_direction == "bearish":
            bearish_signals += 2
        
        # Final recommendation
        if bullish_signals > bearish_signals and confidence_score > 0.55:
            signal.recommendation = "BUY"
            
            # Calculate target (support + 2x risk)
            if signal.price_action.support_levels:
                support = signal.price_action.support_levels[0].price
                stop_loss = support - (support * 0.01)  # 1% below support
            else:
                stop_loss = df['Close'].iloc[-1] * 0.97
            
            signal.stop_loss = stop_loss
            risk = signal.current_price - stop_loss
            signal.target_price = signal.current_price + (risk * 2)
            signal.risk_reward = 2.0
            
            signal.reasons = [
                f"Bullish trend: {signal.price_action.trend_strength.value}",
                f"Volume signal: {signal.volume_analysis.signal.value}",
                f"Timeframe alignment: {signal.multi_timeframe.alignment.value}",
                f"AI Confidence: {signal.confidence.signal_type}"
            ]
        
        elif bearish_signals > bullish_signals and confidence_score > 0.55:
            signal.recommendation = "SELL"
            
            # Calculate target
            if signal.price_action.resistance_levels:
                resistance = signal.price_action.resistance_levels[0].price
                stop_loss = resistance + (resistance * 0.01)
            else:
                stop_loss = df['Close'].iloc[-1] * 1.03
            
            signal.stop_loss = stop_loss
            risk = stop_loss - signal.current_price
            signal.target_price = signal.current_price - (risk * 2)
            signal.risk_reward = 2.0
            
            signal.reasons = [
                f"Bearish trend: {signal.price_action.trend_strength.value}",
                f"Volume signal: {signal.volume_analysis.signal.value}",
                f"Timeframe alignment: {signal.multi_timeframe.alignment.value}",
                f"AI Confidence: {signal.confidence.signal_type}"
            ]
        
        else:
            signal.recommendation = "HOLD"
            signal.reasons = [
                "Mixed signals or insufficient confidence",
                "Wait for clearer setup"
            ]
        
        return signal
