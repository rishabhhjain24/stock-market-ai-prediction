# news_sentiment_unified.py
# ✅ UNIFIED NEWS SENTIMENT ENGINE
# Combines free news sources + HuggingFace models for complete solution
# Handles company news, market news, economic news, and global events

from typing import List, Dict, Optional
from dataclasses import asdict
from datetime import datetime
import json

from news_engine_free import FreeNewsEngine, NewsArticle, NewsCategory
from sentiment_analyzer_hf import HFSentimentAnalyzer, SentimentResult


class UnifiedNewsSentimentEngine:
    """
    Complete news sentiment engine combining multiple free sources and models.
    Provides actionable insights for trading decisions.
    """
    
    def __init__(self):
        self.news_engine = FreeNewsEngine()
        self.sentiment_analyzer = HFSentimentAnalyzer()
        self.cache = {}

    def analyze_stock_sentiment(self, symbol: str, include_market: bool = True,
                               include_economic: bool = True) -> Dict:
        """
        Comprehensive sentiment analysis for a stock.
        
        Returns:
            {
                "symbol": str,
                "company_sentiment": {...},
                "market_sentiment": {...} (if include_market),
                "economic_sentiment": {...} (if include_economic),
                "composite_score": float (-1 to +1),
                "trading_signal": str ("strong_buy", "buy", "hold", "sell", "strong_sell"),
                "confidence": float (0-1),
                "timestamp": str,
                "detailed_analysis": {...}
            }
        """
        
        results = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat(),
            "detailed_analysis": {}
        }
        
        # 1. COMPANY-SPECIFIC NEWS
        print(f"[Analysis] Fetching company news for {symbol}...")
        company_news = self.news_engine.fetch_company_news(symbol)
        company_sentiment = self._analyze_news_batch(company_news, category="company")
        results["company_sentiment"] = company_sentiment
        results["detailed_analysis"]["company"] = {
            "news_count": len(company_news),
            "articles": [asdict(n) for n in company_news[:5]]
        }
        
        # 2. SECTOR & MARKET NEWS (if requested)
        if include_market:
            print("[Analysis] Fetching market news...")
            market_news = self.news_engine.fetch_market_news()
            market_sentiment = self._analyze_news_batch(market_news, category="market")
            results["market_sentiment"] = market_sentiment
            results["detailed_analysis"]["market"] = {
                "news_count": len(market_news),
                "articles": [asdict(n) for n in market_news[:5]]
            }
        
        # 3. ECONOMIC & GLOBAL NEWS (if requested)
        if include_economic:
            print("[Analysis] Fetching economic news...")
            econ_news = self.news_engine.fetch_economic_news()
            econ_sentiment = self._analyze_news_batch(econ_news, category="economic")
            results["economic_sentiment"] = econ_sentiment
            results["detailed_analysis"]["economic"] = {
                "news_count": len(econ_news),
                "articles": [asdict(n) for n in econ_news[:5]]
            }
        
        # 4. COMPOSITE ANALYSIS
        all_sentiments = [results["company_sentiment"]]
        if include_market:
            all_sentiments.append(results["market_sentiment"])
        if include_economic:
            all_sentiments.append(results["economic_sentiment"])
        
        composite = self._calculate_composite(all_sentiments)
        results["composite_score"] = composite["score"]
        results["trading_signal"] = composite["signal"]
        results["confidence"] = composite["confidence"]
        results["signal_breakdown"] = composite["breakdown"]
        
        return results

    def _analyze_news_batch(self, news_articles: List[NewsArticle],
                            category: str = "general") -> Dict:
        """Analyze a batch of news articles"""
        if not news_articles:
            return {
                "score": 0.0,
                "label": "neutral",
                "confidence": 0.0,
                "article_count": 0,
                "bullish_articles": 0,
                "bearish_articles": 0,
                "neutral_articles": 0
            }
        
        # Convert articles to dicts for sentiment analysis
        news_dicts = [asdict(a) for a in news_articles]
        
        # Analyze sentiment for each article
        analyzed = []
        for article in news_dicts:
            text = f"{article['title']} {article['description']}"
            sentiment = self.sentiment_analyzer.analyze_text(text, use_ensemble=True)
            
            analyzed.append({
                **article,
                "sentiment_score": sentiment.score,
                "sentiment_label": sentiment.label,
                "sentiment_confidence": sentiment.confidence
            })
        
        # Calculate composite
        composite = self.sentiment_analyzer.calculate_composite_score(analyzed)
        
        return {
            **composite,
            "category": category
        }

    def _calculate_composite(self, sentiment_results: List[Dict]) -> Dict:
        """
        Calculate final trading signal from all sentiment sources.
        
        Weights:
        - Company news: 50% (most directly affects stock)
        - Market news: 30% (affects overall portfolio)
        - Economic news: 20% (macro backdrop)
        """
        
        scores = []
        weights = []
        
        # Weight by importance
        if len(sentiment_results) >= 1:
            scores.append(sentiment_results[0].get("weighted_score", 0))
            weights.append(0.5)  # Company: 50%
        
        if len(sentiment_results) >= 2:
            scores.append(sentiment_results[1].get("weighted_score", 0))
            weights.append(0.3)  # Market: 30%
        
        if len(sentiment_results) >= 3:
            scores.append(sentiment_results[2].get("weighted_score", 0))
            weights.append(0.2)  # Economic: 20%
        
        if not scores:
            return {
                "score": 0.0,
                "signal": "hold",
                "confidence": 0.0,
                "breakdown": {}
            }
        
        import numpy as np
        weights = np.array(weights) / sum(weights)  # Normalize
        composite_score = np.average(scores, weights=weights[:len(scores)])
        
        # Determine confidence
        confidence_scores = [s.get("confidence", 0.5) for s in sentiment_results]
        avg_confidence = np.mean(confidence_scores)
        
        # Map score to trading signal
        signal = self._score_to_signal(composite_score)
        
        return {
            "score": float(composite_score),
            "signal": signal,
            "confidence": float(avg_confidence),
            "breakdown": {
                f"source_{i}": s.get("weighted_score", 0)
                for i, s in enumerate(sentiment_results)
            }
        }

    def _score_to_signal(self, score: float) -> str:
        """Convert sentiment score to trading signal"""
        if score >= 0.6:
            return "strong_buy"
        elif score >= 0.2:
            return "buy"
        elif score >= -0.2:
            return "hold"
        elif score >= -0.6:
            return "sell"
        else:
            return "strong_sell"

    def get_news_for_dashboard(self, symbol: str, max_articles: int = 10) -> Dict:
        """Get formatted news for dashboard display"""
        company_news = self.news_engine.fetch_company_news(symbol)
        
        analyzed = []
        for news in company_news[:max_articles]:
            text = f"{news.title} {news.description}"
            sentiment = self.sentiment_analyzer.analyze_text(text)
            
            analyzed.append({
                "title": news.title,
                "description": news.description,
                "source": news.source,
                "url": news.url,
                "published_at": news.published_at,
                "sentiment": sentiment.label,
                "sentiment_score": sentiment.score,
                "emoji": self._sentiment_to_emoji(sentiment.label)
            })
        
        return {
            "symbol": symbol,
            "total_articles": len(company_news),
            "articles": analyzed,
            "last_updated": datetime.now().isoformat()
        }

    def _sentiment_to_emoji(self, sentiment_label: str) -> str:
        """Convert sentiment to emoji"""
        emojis = {
            "very_bullish": "🚀",
            "bullish": "📈",
            "neutral": "➡️",
            "bearish": "📉",
            "very_bearish": "💥"
        }
        return emojis.get(sentiment_label, "➡️")

    def get_market_snapshot(self) -> Dict:
        """Get overall market sentiment snapshot"""
        market_news = self.news_engine.fetch_market_news()
        econ_news = self.news_engine.fetch_economic_news()
        
        market_sentiment = self._analyze_news_batch(market_news, category="market")
        econ_sentiment = self._analyze_news_batch(econ_news, category="economic")
        
        return {
            "timestamp": datetime.now().isoformat(),
            "market_sentiment": market_sentiment,
            "economic_sentiment": econ_sentiment,
            "overall_market_signal": self._score_to_signal(
                market_sentiment.get("weighted_score", 0)
            ),
            "economic_backdrop": self._score_to_signal(
                econ_sentiment.get("weighted_score", 0)
            )
        }


# Backward compatibility wrappers
def get_latest_news(stock: str, max_articles: int = 6) -> List[Dict]:
    """Compatibility wrapper for existing code"""
    engine = UnifiedNewsSentimentEngine()
    news = engine.news_engine.fetch_company_news(stock)
    return [asdict(n) for n in news[:max_articles]]


def get_news_titles(stock: str) -> List[str]:
    """Compatibility wrapper"""
    articles = get_latest_news(stock)
    return [a["title"] for a in articles]


# Sentiment analysis wrapper
def analyze_news_sentiment(stock: str) -> Dict:
    """
    Quick function to get stock sentiment.
    
    Usage:
        result = analyze_news_sentiment("RELIANCE")
        print(result["trading_signal"])
        print(result["composite_score"])
    """
    engine = UnifiedNewsSentimentEngine()
    return engine.analyze_stock_sentiment(stock)


if __name__ == "__main__":
    print("=" * 70)
    print("UNIFIED NEWS SENTIMENT ENGINE TEST")
    print("=" * 70)
    
    engine = UnifiedNewsSentimentEngine()
    
    # Test 1: Company analysis
    print("\n[TEST 1] Analyzing RELIANCE stock sentiment...\n")
    result = engine.analyze_stock_sentiment("RELIANCE", include_market=True, include_economic=True)
    
    print(f"Symbol: {result['symbol']}")
    print(f"Composite Score: {result['composite_score']:.2f}")
    print(f"Trading Signal: {result['trading_signal'].upper()}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"\nCompany Sentiment: {result['company_sentiment'].get('weighted_label', 'N/A')}")
    if 'market_sentiment' in result:
        print(f"Market Sentiment: {result['market_sentiment'].get('weighted_label', 'N/A')}")
    if 'economic_sentiment' in result:
        print(f"Economic Sentiment: {result['economic_sentiment'].get('weighted_label', 'N/A')}")
    
    # Test 2: Dashboard news
    print("\n[TEST 2] News for dashboard...\n")
    news = engine.get_news_for_dashboard("RELIANCE", max_articles=3)
    for article in news["articles"]:
        print(f"{article['emoji']} {article['title']}")
        print(f"   Score: {article['sentiment_score']:.2f}")
    
    # Test 3: Market snapshot
    print("\n[TEST 3] Market snapshot...\n")
    snapshot = engine.get_market_snapshot()
    print(f"Market Signal: {snapshot['overall_market_signal'].upper()}")
    print(f"Economic Backdrop: {snapshot['economic_backdrop'].upper()}")
