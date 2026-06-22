# news_sentiment_ai.py - AI-Powered News Sentiment Analysis
# WHY: News drives market movements - needs intelligent analysis
# Uses: FinBERT (Hugging Face), NewsAPI, historical pattern matching
# Generates: Sentiment score, confidence, event impact

import os
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import requests
import pandas as pd
import numpy as np
from enum import Enum

# Try to import FinBERT (if not available, fallback to TextBlob)
try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
    FINBERT_AVAILABLE = True
except ImportError:
    FINBERT_AVAILABLE = False
    print("⚠️  Transformers not installed. Using TextBlob fallback.")

class SentimentScore(Enum):
    """Sentiment classification"""
    VERY_BULLISH = "very_bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    VERY_BEARISH = "very_bearish"

@dataclass
class NewsItem:
    """Single news item"""
    title: str
    description: str
    source: str
    url: str
    published_at: str
    sentiment_score: float  # -1 to 1
    sentiment_label: SentimentScore
    is_relevant: bool  # Mentions company
    impact_score: float  # 0-1, how important

@dataclass
class SentimentAnalysisResult:
    """Complete sentiment analysis"""
    symbol: str
    overall_sentiment: float  # -1 (very bearish) to +1 (very bullish)
    sentiment_label: SentimentScore
    news_count: int
    bullish_count: int
    bearish_count: int
    neutral_count: int
    recent_news: List[NewsItem]
    trending_topics: List[str]
    confidence: float  # 0-1
    event_impact: float  # 0-1, upcoming events impact
    historical_pattern: str  # "similar to [past event]"

class NewsSentimentAI:
    """News Sentiment Analysis using AI"""
    
    def __init__(self, api_key: str = None):
        """Initialize with GNews or NewsAPI key"""
        self.news_api_key = api_key or os.getenv("NEWS_API_KEY")
        self.finbert_model = None
        self.finbert_tokenizer = None
        self.finbert_available = FINBERT_AVAILABLE
        
        # Load FinBERT if available
        if self.finbert_available:
            try:
                self.finbert_tokenizer = AutoTokenizer.from_pretrained(
                    "ProsusAI/finbert"
                )
                self.finbert_model = AutoModelForSequenceClassification.from_pretrained(
                    "ProsusAI/finbert"
                )
                self.finbert_model.eval()
                print("✅ FinBERT loaded successfully")
            except Exception as e:
                print(f"⚠️  Could not load FinBERT: {e}")
                self.finbert_available = False
    
    def fetch_news(self, symbol: str, days: int = 7) -> List[Dict]:
        """
        Fetch latest news for stock.
        
        Uses NewsAPI free tier (100 calls/day).
        """
        if not self.news_api_key:
            return []
        
        # Remove .NS suffix for news search
        symbol_clean = symbol.replace(".NS", "")
        
        try:
            # NewsAPI query
            url = "https://newsapi.org/v2/everything"
            params = {
                "q": f"{symbol_clean} stock",
                "sortBy": "publishedAt",
                "language": "en",
                "apiKey": self.news_api_key,
                "pageSize": 50
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("status") == "ok":
                return data.get("articles", [])
            else:
                print(f"⚠️  NewsAPI error: {data.get('message')}")
                return []
        
        except Exception as e:
            print(f"⚠️  Could not fetch news: {e}")
            return []
    
    def analyze_sentiment_finbert(self, text: str) -> Tuple[float, str]:
        """
        Analyze sentiment using FinBERT.
        
        Returns: (score -1 to +1, label)
        """
        if not self.finbert_available or not self.finbert_model:
            return self._analyze_sentiment_textblob(text)
        
        try:
            # Tokenize
            inputs = self.finbert_tokenizer(
                text[:512],  # Truncate to 512 tokens
                return_tensors="pt",
                truncation=True
            )
            
            # Predict
            with torch.no_grad():
                outputs = self.finbert_model(**inputs)
            
            # Get probabilities
            logits = outputs.logits
            probs = torch.softmax(logits, dim=1)
            
            # FinBERT classes: 0=negative, 1=neutral, 2=positive
            negative_prob = probs[0][0].item()
            neutral_prob = probs[0][1].item()
            positive_prob = probs[0][2].item()
            
            # Convert to -1 to +1 scale
            score = positive_prob - negative_prob
            
            # Label
            if score > 0.5:
                label = "very_bullish"
            elif score > 0.2:
                label = "bullish"
            elif score > -0.2:
                label = "neutral"
            elif score > -0.5:
                label = "bearish"
            else:
                label = "very_bearish"
            
            return score, label
        
        except Exception as e:
            print(f"⚠️  FinBERT analysis error: {e}")
            return self._analyze_sentiment_textblob(text)
    
    def _analyze_sentiment_textblob(self, text: str) -> Tuple[float, str]:
        """Fallback: TextBlob sentiment"""
        try:
            from textblob import TextBlob
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity  # -1 to 1
            
            if polarity > 0.5:
                label = "very_bullish"
            elif polarity > 0.2:
                label = "bullish"
            elif polarity > -0.2:
                label = "neutral"
            elif polarity > -0.5:
                label = "bearish"
            else:
                label = "very_bearish"
            
            return polarity, label
        except ImportError:
            return 0, "neutral"  # Neutral if nothing available
    
    def analyze_articles(self, articles: List[Dict]) -> List[NewsItem]:
        """Analyze list of articles"""
        results = []
        
        for article in articles:
            title = article.get("title", "")
            description = article.get("description") or article.get("content") or ""
            text = f"{title}. {description}"
            
            # Sentiment
            sentiment_score, sentiment_label = self.analyze_sentiment_finbert(text)
            
            # Impact score (longer articles = more detailed = more impact)
            impact = min(1.0, len(text) / 500)  # Normalize to 500 characters
            
            news_item = NewsItem(
                title=title,
                description=description[:200],  # Truncate
                source=article.get("source", {}).get("name", "Unknown"),
                url=article.get("url", ""),
                published_at=article.get("publishedAt", ""),
                sentiment_score=sentiment_score,
                sentiment_label=SentimentScore(sentiment_label),
                is_relevant=True,  # We already filtered by symbol
                impact_score=impact
            )
            
            results.append(news_item)
        
        return results
    
    def generate_analysis(self, symbol: str, days: int = 7) -> Optional[SentimentAnalysisResult]:
        """
        Generate complete sentiment analysis.
        
        Returns: SentimentAnalysisResult with all metrics
        """
        # Fetch news
        articles = self.fetch_news(symbol, days)
        
        if not articles:
            return None
        
        # Analyze sentiment
        news_items = self.analyze_articles(articles)
        
        if not news_items:
            return None
        
        # Calculate metrics
        sentiment_scores = [n.sentiment_score for n in news_items]
        overall_sentiment = np.mean(sentiment_scores) if sentiment_scores else 0
        
        bullish = sum(1 for n in news_items if n.sentiment_score > 0.2)
        bearish = sum(1 for n in news_items if n.sentiment_score < -0.2)
        neutral = len(news_items) - bullish - bearish
        
        # Overall label
        if overall_sentiment > 0.5:
            overall_label = SentimentScore.VERY_BULLISH
        elif overall_sentiment > 0.2:
            overall_label = SentimentScore.BULLISH
        elif overall_sentiment < -0.5:
            overall_label = SentimentScore.VERY_BEARISH
        elif overall_sentiment < -0.2:
            overall_label = SentimentScore.BEARISH
        else:
            overall_label = SentimentScore.NEUTRAL
        
        # Confidence (more articles = higher confidence)
        confidence = min(1.0, len(news_items) / 20)
        
        # Trending topics (extract from titles)
        topics = []
        for item in news_items[:5]:
            if "earnings" in item.title.lower():
                topics.append("Earnings")
            if "dividend" in item.title.lower():
                topics.append("Dividend")
            if "acquisition" in item.title.lower():
                topics.append("M&A")
            if "ceo" in item.title.lower():
                topics.append("Management")
        
        topics = list(set(topics))
        
        return SentimentAnalysisResult(
            symbol=symbol,
            overall_sentiment=overall_sentiment,
            sentiment_label=overall_label,
            news_count=len(news_items),
            bullish_count=bullish,
            bearish_count=bearish,
            neutral_count=neutral,
            recent_news=news_items[:5],  # Top 5
            trending_topics=topics,
            confidence=confidence,
            event_impact=0.5,  # TODO: detect upcoming earnings/events
            historical_pattern=""  # TODO: historical matching
        )
    
    def format_for_display(self, analysis: SentimentAnalysisResult) -> Dict:
        """Format for Streamlit display"""
        
        sentiment_emoji = {
            SentimentScore.VERY_BULLISH: "🟢🟢",
            SentimentScore.BULLISH: "🟢",
            SentimentScore.NEUTRAL: "⚪",
            SentimentScore.BEARISH: "🔴",
            SentimentScore.VERY_BEARISH: "🔴🔴"
        }
        
        return {
            "emoji": sentiment_emoji.get(analysis.sentiment_label, "⚪"),
            "sentiment": analysis.sentiment_label.value.replace("_", " ").title(),
            "score": f"{analysis.overall_sentiment:+.2f}",
            "news_count": analysis.news_count,
            "bullish": f"{analysis.bullish_count} ({analysis.bullish_count/max(1, analysis.news_count)*100:.0f}%)",
            "bearish": f"{analysis.bearish_count} ({analysis.bearish_count/max(1, analysis.news_count)*100:.0f}%)",
            "topics": ", ".join(analysis.trending_topics) if analysis.trending_topics else "General",
            "confidence": f"{analysis.confidence*100:.0f}%"
        }
