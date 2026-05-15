# trading_forecast_engine.py - UNIFIED FORECAST SYSTEM
# Combines: News Sentiment + Technical Indicators + Chart Patterns + Market Regime + AI Confidence
# For REAL MONEY trading with confidence scores and risk warnings

import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time
import pytz
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import yfinance as yf

# ✅ NEW: Use free news sentiment system (no API keys!)
from news_sentiment_unified import analyze_news_sentiment
from market_regime import MarketRegimeAnalyzer, MarketRegime
from chart_patterns import detect_all_patterns
from sentiment_engine import aggregate_news_sentiment
from data_engine import get_features


@dataclass
class ForecastComponent:
    """Individual forecast component score"""
    name: str
    score: float  # -1 to +1 (bearish to bullish)
    confidence: float  # 0 to 1 (how confident in this score)
    description: str


@dataclass
class TradingForecast:
    """Complete unified trading forecast"""
    symbol: str
    timestamp: datetime
    
    # MAIN FORECAST
    recommendation: str  # BUY, SELL, HOLD
    forecast_strength: float  # 0-1 (how strong is signal)
    forecast_confidence: float  # 0-1 (overall confidence)
    
    # PRICE TARGETS
    current_price: float
    target_price_1h: float  # 1 hour target (scalping)
    target_price_4h: float  # 4 hour target (swing)
    target_price_1d: float  # 1 day target (position)
    stop_loss: float
    
    # RISK METRICS
    risk_reward_ratio: float  # Target/Risk in basis points
    portfolio_risk_percent: float  # How much of 2% rule
    
    # COMPONENTS
    news_sentiment: ForecastComponent
    technical_indicators: ForecastComponent
    chart_patterns: ForecastComponent
    market_regime: ForecastComponent
    price_action: ForecastComponent
    volume_analysis: ForecastComponent
    global_sentiment: ForecastComponent
    
    # TIMING
    best_entry_time: str
    trading_window_hours: float
    market_hours_valid: bool
    
    # WARNINGS
    warnings: list
    risk_factors: list


class TradingForecastEngine:
    """Generate comprehensive trading forecasts combining all data sources"""
    
    def __init__(self):
        self.market_analyzer = MarketRegimeAnalyzer()
    
    def generate_forecast(self, symbol: str, df: pd.DataFrame = None) -> Optional[TradingForecast]:
        """
        Generate complete trading forecast for a symbol.
        
        Combines:
        - News sentiment analysis
        - Technical indicators (RSI, MACD, EMA, ATR)
        - Chart patterns (head-shoulders, triangles, etc)
        - Market regime (trend/consolidation/crash)
        - Price action (support/resistance/momentum)
        - Volume analysis
        - Global market sentiment
        """
        
        try:
            # 1. FETCH DATA
            if df is None:
                df = yf.download(symbol, period="250d", interval="1d", progress=False)
            
            if df is None or df.empty or df.shape[0] < 50:
                return None
            
            current_price = float(df['Close'].iloc[-1])
            timestamp = datetime.now(pytz.timezone('Asia/Kolkata'))
            
            # 2. ANALYZE EACH COMPONENT
            
            # NEWS SENTIMENT
            news_component = self._analyze_news_sentiment(symbol)
            
            # TECHNICAL INDICATORS
            technical_component = self._analyze_technical_indicators(df)
            
            # CHART PATTERNS
            chart_component = self._analyze_chart_patterns(symbol, df)
            
            # MARKET REGIME
            regime_component = self._analyze_market_regime(df)
            
            # PRICE ACTION
            price_component = self._analyze_price_action(df)
            
            # VOLUME ANALYSIS
            volume_component = self._analyze_volume(df)
            
            # GLOBAL SENTIMENT
            global_component = self._analyze_global_sentiment()
            
            # 3. COMPOSITE FORECAST
            recommendation, forecast_strength = self._compute_recommendation(
                news_component, technical_component, chart_component,
                regime_component, price_component, volume_component, global_component
            )
            
            # 4. CALCULATE TARGETS & RISK
            targets_risk = self._calculate_targets_and_risk(
                df, current_price, recommendation, forecast_strength
            )
            
            # 5. MARKET TIMING
            market_status = self._check_market_timing(timestamp)
            
            # 6. WARNINGS & RISK FACTORS
            warnings, risk_factors = self._identify_risks(
                df, news_component, technical_component, 
                forecast_strength, recommendation
            )
            
            # 7. ASSEMBLE FORECAST
            forecast = TradingForecast(
                symbol=symbol,
                timestamp=timestamp,
                recommendation=recommendation,
                forecast_strength=forecast_strength,
                forecast_confidence=self._calculate_confidence(
                    news_component, technical_component, chart_component,
                    regime_component, price_component, volume_component
                ),
                current_price=current_price,
                target_price_1h=targets_risk['target_1h'],
                target_price_4h=targets_risk['target_4h'],
                target_price_1d=targets_risk['target_1d'],
                stop_loss=targets_risk['stop_loss'],
                risk_reward_ratio=targets_risk['risk_reward_ratio'],
                portfolio_risk_percent=targets_risk['portfolio_risk_percent'],
                news_sentiment=news_component,
                technical_indicators=technical_component,
                chart_patterns=chart_component,
                market_regime=regime_component,
                price_action=price_component,
                volume_analysis=volume_component,
                global_sentiment=global_component,
                best_entry_time=market_status['best_entry_time'],
                trading_window_hours=market_status['trading_window_hours'],
                market_hours_valid=market_status['is_market_open'],
                warnings=warnings,
                risk_factors=risk_factors
            )
            
            return forecast
            
        except Exception as e:
            print(f"[TradingForecastEngine] Error generating forecast: {e}")
            return None
    
    def _analyze_news_sentiment(self, symbol: str) -> ForecastComponent:
        """Analyze latest news sentiment using FREE HuggingFace models"""
        try:
            # ✅ NEW: Use free news sentiment system (was using paid NewsAPI before)
            result = analyze_news_sentiment(symbol)
            
            score = result.get('composite_score', 0.0)
            confidence = result.get('confidence', 0.5)
            signal = result.get('trading_signal', 'hold')
            
            # Convert to component format
            return ForecastComponent(
                name="News Sentiment",
                score=score,
                confidence=confidence,
                description=f"{signal.upper()}: Score {score:.2f} | "
                           f"Company: {result.get('company_sentiment', {}).get('weighted_label', 'N/A')} | "
                           f"Market: {result.get('market_sentiment', {}).get('weighted_label', 'N/A')}"
            )
            
        except Exception as e:
            print(f"[News Sentiment] Error: {e}")
            return ForecastComponent(
                name="News Sentiment",
                score=0.0,
                confidence=0.0,
                description="Unable to analyze news"
            )
    
    def _analyze_technical_indicators(self, df: pd.DataFrame) -> ForecastComponent:
        """Analyze technical indicators: RSI, MACD, EMA, ATR"""
        try:
            if df is None or df.empty or df.shape[0] < 50:
                return ForecastComponent("Technical", 0.0, 0.0, "Insufficient data")
            
            close = df['Close']
            high = df['High']
            low = df['Low']
            
            # RSI
            delta = close.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            rsi_val = float(rsi.iloc[-1])
            
            # MACD
            ema_12 = close.ewm(span=12, adjust=False).mean()
            ema_26 = close.ewm(span=26, adjust=False).mean()
            macd = ema_12 - ema_26
            macd_signal = macd.ewm(span=9, adjust=False).mean()
            macd_hist = macd - macd_signal
            
            # EMA trends
            ema_9 = close.ewm(span=9, adjust=False).mean()
            ema_21 = close.ewm(span=21, adjust=False).mean()
            ema_50 = close.ewm(span=50, adjust=False).mean()
            
            # ATR (volatility)
            high_low = high - low
            high_close = abs(high - close.shift())
            low_close = abs(low - close.shift())
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = tr.rolling(14).mean()
            
            # Calculate technical score (-1 to +1)
            tech_score = 0.0
            
            # RSI scoring
            if rsi_val < 30:
                tech_score += 0.3  # Oversold, bullish
            elif rsi_val < 50:
                tech_score += 0.1
            elif rsi_val > 70:
                tech_score -= 0.3  # Overbought, bearish
            elif rsi_val > 50:
                tech_score -= 0.1
            
            # MACD scoring
            macd_val = float(macd.iloc[-1])
            macd_signal_val = float(macd_signal.iloc[-1])
            
            if macd_val > macd_signal_val:
                tech_score += 0.2  # MACD bullish
            else:
                tech_score -= 0.2  # MACD bearish
            
            # EMA scoring
            if float(ema_9.iloc[-1]) > float(ema_21.iloc[-1]) > float(ema_50.iloc[-1]):
                tech_score += 0.3  # Strong uptrend
            elif float(ema_9.iloc[-1]) < float(ema_21.iloc[-1]) < float(ema_50.iloc[-1]):
                tech_score -= 0.3  # Strong downtrend
            
            tech_score = np.clip(tech_score, -1, 1)
            
            return ForecastComponent(
                name="Technical Indicators",
                score=tech_score,
                confidence=0.7,
                description=f"RSI: {rsi_val:.1f} | MACD: {'Bull' if macd_val > macd_signal_val else 'Bear'} | EMA: {'Up' if float(ema_9.iloc[-1]) > float(ema_21.iloc[-1]) else 'Down'}"
            )
            
        except Exception as e:
            print(f"[Technical] Error: {e}")
            return ForecastComponent("Technical", 0.0, 0.0, f"Error: {str(e)[:30]}")
    
    def _analyze_chart_patterns(self, symbol: str, df: pd.DataFrame) -> ForecastComponent:
        """Analyze chart patterns: head-shoulders, triangles, etc"""
        try:
            patterns = detect_all_patterns(df)
            
            if not patterns or len(patterns) == 0:
                return ForecastComponent(
                    name="Chart Patterns",
                    score=0.0,
                    confidence=0.2,
                    description="No clear patterns detected"
                )
            
            # Score patterns (patterns is a list of Pattern objects)
            pattern_score = 0.0
            bullish_pattern_names = ['ascending_triangle', 'double_bottom']
            bearish_pattern_names = ['double_top', 'head_and_shoulders']
            
            pattern_count = len(patterns)
            for pattern in patterns:
                pattern_name = pattern.name.lower().replace(" ", "_").replace("&", "and")
                if pattern_name in bullish_pattern_names or pattern.type == "bullish":
                    pattern_score += float(pattern.confidence)
                elif pattern_name in bearish_pattern_names or pattern.type == "bearish":
                    pattern_score -= float(pattern.confidence)
            
            pattern_score = np.clip(pattern_score, -1, 1) if pattern_count > 0 else 0
            
            return ForecastComponent(
                name="Chart Patterns",
                score=pattern_score,
                confidence=min(1.0, pattern_count * 0.3),
                description=f"{pattern_count} pattern(s) detected: {patterns[0].name if patterns else 'None'}"
            )
            
        except Exception as e:
            print(f"[Patterns] Error: {e}")
            return ForecastComponent("Chart Patterns", 0.0, 0.0, "Pattern detection unavailable")
    
    def _analyze_market_regime(self, df: pd.DataFrame) -> ForecastComponent:
        """Analyze market regime: trending vs consolidating"""
        try:
            regime = self.market_analyzer.detect_regime(df)
            
            regime_score = {
                MarketRegime.STRONG_UPTREND: 0.8,
                MarketRegime.UPTREND: 0.5,
                MarketRegime.CONSOLIDATION: 0.0,
                MarketRegime.DOWNTREND: -0.5,
                MarketRegime.STRONG_DOWNTREND: -0.8,
                MarketRegime.CRASH: -1.0,
            }.get(regime, 0.0)
            
            return ForecastComponent(
                name="Market Regime",
                score=regime_score,
                confidence=0.8,
                description=f"Regime: {regime.value.upper()}"
            )
            
        except Exception as e:
            print(f"[Regime] Error: {e}")
            return ForecastComponent("Market Regime", 0.0, 0.0, "Regime analysis unavailable")
    
    def _analyze_price_action(self, df: pd.DataFrame) -> ForecastComponent:
        """Analyze price action: support/resistance/momentum"""
        try:
            if df is None or df.empty or df.shape[0] < 20:
                return ForecastComponent("Price Action", 0.0, 0.0, "Insufficient data")
            
            # Recent price momentum
            close = df['Close']
            momentum_5d = float((close.iloc[-1] - close.iloc[-5]) / close.iloc[-5])
            momentum_20d = float((close.iloc[-1] - close.iloc[-20]) / close.iloc[-20])
            
            # Support/Resistance
            support = float(df['Low'].tail(20).min())
            resistance = float(df['High'].tail(20).max())
            current = float(close.iloc[-1])
            
            # How close to support/resistance?
            distance_to_support = float((current - support) / (resistance - support))
            
            # Price action score
            pa_score = 0.0
            
            if momentum_5d > 0.02:  # 2%+ up in 5 days
                pa_score += 0.3
            elif momentum_5d < -0.02:  # 2%+ down
                pa_score -= 0.3
            
            if momentum_20d > 0.05:  # 5%+ up in 20 days
                pa_score += 0.3
            elif momentum_20d < -0.05:
                pa_score -= 0.3
            
            # Near support = bullish, near resistance = bearish
            if distance_to_support < 0.2:
                pa_score += 0.2  # Near support
            elif distance_to_support > 0.8:
                pa_score -= 0.2  # Near resistance
            
            pa_score = np.clip(pa_score, -1, 1)
            
            return ForecastComponent(
                name="Price Action",
                score=pa_score,
                confidence=0.7,
                description=f"5d: {momentum_5d:+.2%} | 20d: {momentum_20d:+.2%} | Support: ₹{support:.2f} | Resistance: ₹{resistance:.2f}"
            )
            
        except Exception as e:
            print(f"[Price Action] Error: {e}")
            return ForecastComponent("Price Action", 0.0, 0.0, f"Error: {str(e)[:30]}")
    
    def _analyze_volume(self, df: pd.DataFrame) -> ForecastComponent:
        """Analyze volume patterns"""
        try:
            if df is None or df.empty or df.shape[0] < 20 or 'Volume' not in df.columns:
                return ForecastComponent("Volume", 0.0, 0.3, "Volume data unavailable")
            
            volume = df['Volume']
            avg_volume_20 = float(volume.tail(20).mean())
            current_volume = float(volume.iloc[-1])
            volume_ratio = float(current_volume / avg_volume_20)
            
            vol_score = 0.0
            
            # High volume on up days = bullish
            if current_volume > avg_volume_20 * 1.2:
                price_up = float(df['Close'].iloc[-1]) > float(df['Close'].iloc[-2])
                if price_up:
                    vol_score += 0.3  # Volume confirms uptrend
                else:
                    vol_score -= 0.2  # High volume on down day = bearish
            
            vol_score = np.clip(vol_score, -1, 1)
            
            return ForecastComponent(
                name="Volume Analysis",
                score=vol_score,
                confidence=0.6,
                description=f"Volume ratio: {volume_ratio:.2f}x average (20d: {avg_volume_20:.0f})"
            )
            
        except Exception as e:
            print(f"[Volume] Error: {e}")
            return ForecastComponent("Volume", 0.0, 0.0, "Volume analysis unavailable")
    
    def _analyze_global_sentiment(self) -> ForecastComponent:
        """Analyze global market sentiment: US markets, indices"""
        try:
            # Fetch overnight US market performance
            sp500 = yf.download("^GSPC", period="5d", interval="1d", progress=False)
            
            if sp500 is None or sp500.empty or sp500.shape[0] < 2:
                return ForecastComponent(
                    name="Global Sentiment",
                    score=0.0,
                    confidence=0.3,
                    description="Global data unavailable"
                )
            
            sp500_chg = (sp500['Close'].iloc[-1] - sp500['Close'].iloc[-2]) / sp500['Close'].iloc[-2]
            
            global_score = 0.0
            
            # US markets impact on Indian stocks
            if sp500_chg > 0.01:  # 1%+ up = bullish globally
                global_score += 0.3
            elif sp500_chg < -0.01:  # 1%+ down = bearish globally
                global_score -= 0.3
            
            global_score = np.clip(global_score, -1, 1)
            
            return ForecastComponent(
                name="Global Sentiment",
                score=global_score,
                confidence=0.5,
                description=f"S&P500: {sp500_chg:+.2%} | Mood: {'Bullish' if sp500_chg > 0 else 'Bearish'}"
            )
            
        except Exception:
            return ForecastComponent(
                name="Global Sentiment",
                score=0.0,
                confidence=0.0,
                description="Global sentiment unavailable"
            )
    
    def _compute_recommendation(self, news, technical, patterns, regime, price, volume, global_sent) -> Tuple[str, float]:
        """Compute final BUY/SELL/HOLD recommendation"""
        
        # Weighted composite score
        weights = {
            'news': 0.10,
            'technical': 0.25,
            'patterns': 0.15,
            'regime': 0.20,
            'price': 0.15,
            'volume': 0.10,
            'global': 0.05
        }
        
        composite_score = (
            weights['news'] * news.score +
            weights['technical'] * technical.score +
            weights['patterns'] * patterns.score +
            weights['regime'] * regime.score +
            weights['price'] * price.score +
            weights['volume'] * volume.score +
            weights['global'] * global_sent.score
        )
        
        composite_score = np.clip(composite_score, -1, 1)
        
        # Convert to recommendation (thresholds lowered to 0.1/-0.1 for more signals)
        if composite_score > 0.1:
            recommendation = "BUY"
            strength = min(1.0, max(0.3, composite_score))  # Min 30% strength
        elif composite_score < -0.1:
            recommendation = "SELL"
            strength = min(1.0, max(0.3, abs(composite_score)))  # Min 30% strength
        else:
            # If neutral, default to slight bullish bias on intraday trades
            recommendation = "HOLD"
            strength = max(0.1, abs(composite_score))
        
        return recommendation, strength
    
    def _calculate_confidence(self, *components) -> float:
        """Calculate overall confidence across all components"""
        confidences = [c.confidence for c in components]
        return np.mean(confidences) if confidences else 0.5
    
    def _calculate_targets_and_risk(self, df: pd.DataFrame, current_price: float,
                                    recommendation: str, strength: float) -> Dict:
        """Calculate price targets and risk levels"""
        
        try:
            # ATR for volatility
            high_low = df['High'] - df['Low']
            high_close = abs(df['High'] - df['Close'].shift())
            low_close = abs(df['Low'] - df['Close'].shift())
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            atr = tr.rolling(14).mean().iloc[-1]
            
            if recommendation == "BUY":
                stop_loss = current_price - (atr * 2)
                risk = current_price - stop_loss
                
                target_1h = current_price + (atr * 0.5)
                target_4h = current_price + (atr * 1.5)
                target_1d = current_price + (atr * 2.5)
                
            elif recommendation == "SELL":
                stop_loss = current_price + (atr * 2)
                risk = stop_loss - current_price
                
                target_1h = current_price - (atr * 0.5)
                target_4h = current_price - (atr * 1.5)
                target_1d = current_price - (atr * 2.5)
                
            else:  # HOLD - Still calculate meaningful targets
                stop_loss = current_price - (atr * 1.0)
                risk = atr
                # Generate upside targets (neutral bias)
                target_1h = current_price + (atr * 0.3)
                target_4h = current_price + (atr * 0.8)
                target_1d = current_price + (atr * 1.5)
            
            # Risk/Reward ratio
            reward_1d = abs(target_1d - current_price)
            if risk > 0:
                rr_ratio = reward_1d / risk
            else:
                rr_ratio = 0
            
            # Portfolio risk (2% rule)
            portfolio_risk = 2.0 if rr_ratio > 1.5 else 1.5 if rr_ratio > 1 else 1.0
            
            return {
                'target_1h': target_1h,
                'target_4h': target_4h,
                'target_1d': target_1d,
                'stop_loss': stop_loss,
                'risk_reward_ratio': rr_ratio,
                'portfolio_risk_percent': portfolio_risk
            }
            
        except Exception as e:
            print(f"[Targets] Error: {e}")
            return {
                'target_1h': current_price,
                'target_4h': current_price,
                'target_1d': current_price,
                'stop_loss': current_price * 0.98,
                'risk_reward_ratio': 1.0,
                'portfolio_risk_percent': 1.0
            }
    
    def _check_market_timing(self, timestamp: datetime) -> Dict:
        """Check if market is open and best trading times"""
        
        tz = pytz.timezone('Asia/Kolkata')
        now = timestamp if timestamp.tzinfo else tz.localize(timestamp)
        
        market_open = time(9, 15)
        market_close = time(15, 30)
        is_weekday = now.weekday() < 5
        is_market_open = is_weekday and market_open <= now.time() < market_close
        
        # Best entry times
        hour = now.hour
        if 9 <= hour < 10:
            best_time = "Opening Momentum (Best)"
        elif 13 <= hour < 14:
            best_time = "Afternoon Rally"
        elif 15 <= hour < 15.5:
            best_time = "Closing Scalp (Use limits only)"
        elif is_market_open:
            best_time = "Mid-day Trading"
        else:
            best_time = "Market Closed"
        
        hours_until_close = (15.5 - now.hour - now.minute/60) if is_market_open else 0
        
        return {
            'is_market_open': is_market_open,
            'best_entry_time': best_time,
            'trading_window_hours': max(0, hours_until_close),
            'market_status': "OPEN" if is_market_open else "CLOSED"
        }
    
    def _identify_risks(self, df: pd.DataFrame, news, technical, strength, recommendation) -> Tuple[list, list]:
        """Identify warnings and risk factors"""
        
        warnings = []
        risk_factors = []
        
        # Risk 1: Low confidence in technical indicators
        if technical.confidence < 0.5:
            warnings.append("⚠️ Low technical confidence - limited data")
            risk_factors.append("Unreliable technical indicators")
        
        # Risk 2: Diverging signals
        if news.score * technical.score < 0:  # Opposite signs
            warnings.append("⚠️ Conflicting signals - news vs technicals")
            risk_factors.append("News and technicals don't align")
        
        # Risk 3: High RSI/Low RSI
        close = df['Close']
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        rsi_val = float(rsi.iloc[-1])
        
        if rsi_val > 80:
            warnings.append("⚠️ RSI > 80: Overbought - risk of pullback")
            risk_factors.append("Overbought conditions")
        elif rsi_val < 20:
            warnings.append("⚠️ RSI < 20: Oversold - risk of bounce")
            risk_factors.append("Oversold conditions")
        
        # Risk 4: Weak forecast strength
        if strength < 0.4:
            warnings.append("⚠️ Weak signal strength - use tight stops")
            risk_factors.append("Low forecast confidence")
        
        # Risk 5: Unusual volatility
        try:
            vol = df['Close'].pct_change().std() * np.sqrt(252) * 100
            if vol > 40:
                warnings.append(f"⚠️ HIGH VOLATILITY: {vol:.1f}% annual - use wider stops")
                risk_factors.append("Extreme volatility")
        except:
            pass
        
        return warnings, risk_factors
