# sentiment_engine.py - News sentiment analysis for trading decisions
# WHY: Sentiment analysis converts raw news into trading signals
# A positive earnings surprise should bias toward BUY, while bankruptcies toward SELL

import numpy as np
import pandas as pd
from textblob import TextBlob
from typing import List, Tuple, Dict
from config import USE_FINBERT_SENTIMENT

# If you want better accuracy (FinBERT), install: pip install torch transformers
if USE_FINBERT_SENTIMENT:
    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        import torch
        FINBERT_MODEL = AutoModelForSequenceClassification.from_pretrained(
            "ProsusAI/finbert"
        )
        FINBERT_TOKENIZER = AutoTokenizer.from_pretrained("ProsusAI/finbert")
        USE_FINBERT = True
    except ImportError:
        print("[sentiment_engine] FinBERT not installed. Falling back to TextBlob.")
        USE_FINBERT = False
else:
    USE_FINBERT = False


def analyze_textblob(text: str) -> float:
    """
    Use TextBlob for simple sentiment analysis.
    
    WHY TextBlob:
    - No API key required (free)
    - Returns polarity score: [-1.0 (negative) to 1.0 (positive)]
    - Good for financial news headlines
    - Very fast and lightweight
    
    Returns sentiment score from -1.0 (very negative) to 1.0 (very positive)
    """
    try:
        analysis = TextBlob(text)
        return float(analysis.sentiment.polarity)
    except Exception as e:
        print(f"[sentiment_engine] TextBlob error: {e}")
        return 0.0  # Neutral if error


def analyze_finbert(text: str) -> float:
    """
    Use FinBERT (Financial BERT) for advanced sentiment analysis.
    
    WHY FinBERT:
    - Fine-tuned on financial texts (earnings calls, news)
    - Better at understanding financial context
    - Returns: negative (-1), neutral (0), positive (1)
    - More accurate than general models but slower
    
    Returns score from -1.0 (very negative) to 1.0 (very positive)
    """
    if not USE_FINBERT:
        return analyze_textblob(text)
    
    try:
        inputs = FINBERT_TOKENIZER(
            text[:512],  # FinBERT max 512 tokens
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )
        
        with torch.no_grad():
            outputs = FINBERT_MODEL(**inputs)
            logits = outputs.logits
        
        # Convert logits to probabilities
        probs = torch.nn.functional.softmax(logits, dim=-1)
        
        # Return weighted score: negative * -1 + neutral * 0 + positive * 1
        negative_prob = float(probs[0, 0])
        neutral_prob = float(probs[0, 1])
        positive_prob = float(probs[0, 2])
        
        score = (positive_prob - negative_prob)
        return score
        
    except Exception as e:
        print(f"[sentiment_engine] FinBERT error: {e}")
        return analyze_textblob(text)


def analyze_sentiment(text: str) -> float:
    """Main sentiment analysis function - routes to appropriate model."""
    if USE_FINBERT:
        return analyze_finbert(text)
    else:
        return analyze_textblob(text)


def batch_analyze(texts: List[str]) -> List[float]:
    """Analyze multiple texts efficiently."""
    return [analyze_sentiment(text) for text in texts]


def aggregate_news_sentiment(
    news_articles: List[Dict], 
    weights: str = "recency"
) -> Tuple[float, str, Dict]:
    """
    Aggregate sentiment from multiple news articles.
    
    Args:
        news_articles: List of dicts with 'title', 'description', 'publishedAt'
        weights: "recency" (recent articles weighted more), "equal" (uniform weights)
    
    Returns:
        tuple: (aggregate_score, sentiment_label, detailed_breakdown)
    
    WHY weighting:
    - Recent news is more relevant for trading decisions
    - News from 1 week ago is less actionable
    - Recency weighting = 75% to current, 25% to older news
    """
    if not news_articles:
        return 0.0, "NEUTRAL", {"count": 0, "scores": []}
    
    scores = []
    weights_list = []
    
    for i, article in enumerate(news_articles):
        # Combine title + description for richer sentiment
        text = f"{article.get('title', '')} {article.get('description', '')}"
        score = analyze_sentiment(text)
        scores.append(score)
        
        # Recent articles get higher weight
        if weights == "recency":
            # More recent = higher weight
            weight = 1.0 + (len(news_articles) - i - 1) * 0.1
        else:
            weight = 1.0
        
        weights_list.append(weight)
    
    # Normalize weights
    weights_list = np.array(weights_list) / sum(weights_list)
    
    # Calculate weighted average
    aggregate_score = float(np.average(scores, weights=weights_list))
    
    # Classify sentiment
    if aggregate_score > 0.2:
        label = "POSITIVE"
    elif aggregate_score < -0.2:
        label = "NEGATIVE"
    else:
        label = "NEUTRAL"
    
    return aggregate_score, label, {
        "count": len(scores),
        "scores": scores,
        "aggregate": aggregate_score,
        "label": label,
        "newest_score": scores[0] if scores else 0.0,
        "oldest_score": scores[-1] if scores else 0.0,
    }


def sentiment_to_signal(score: float) -> Dict:
    """
    Convert sentiment score to trading signal bias.
    
    WHY this mapping:
    - Sentiment alone doesn't trade (needs confirmation from technicals)
    - But it provides a bias for position sizing and entry timing
    - Positive sentiment = increase position size
    - Negative sentiment = reduce position size or wait for confirmation
    
    Returns: {"bias": "BULLISH"/"BEARISH"/"NEUTRAL", "signal_boost": float}
    signal_boost: add this to ML model's probability for combined signal
    """
    if score > 0.3:
        return {
            "bias": "BULLISH",
            "signal_boost": 0.05,  # +5% probability boost
            "interpretation": "News is positive - increases buy conviction"
        }
    elif score < -0.3:
        return {
            "bias": "BEARISH", 
            "signal_boost": -0.05,  # -5% probability boost
            "interpretation": "News is negative - decreases buy conviction"
        }
    else:
        return {
            "bias": "NEUTRAL",
            "signal_boost": 0.0,
            "interpretation": "Neutral news - follow technical setup"
        }


def sentiment_analysis_report(
    stock: str, 
    news_articles: List[Dict]
) -> Dict:
    """
    Generate a comprehensive sentiment report for a stock.
    
    Returns full analysis suitable for dashboard display.
    """
    aggregate_score, label, details = aggregate_news_sentiment(news_articles)
    signal = sentiment_to_signal(aggregate_score)
    
    # Classify individual articles
    article_classifications = []
    for article in news_articles:
        text = f"{article.get('title', '')} {article.get('description', '')}"
        score = analyze_sentiment(text)
        
        if score > 0.2:
            sentiment = "POSITIVE"
        elif score < -0.2:
            sentiment = "NEGATIVE"
        else:
            sentiment = "NEUTRAL"
        
        article_classifications.append({
            "title": article.get("title", "")[:100],
            "sentiment": sentiment,
            "score": round(score, 3),
        })
    
    return {
        "stock": stock,
        "aggregate_sentiment": aggregate_score,
        "sentiment_label": label,
        "signal_bias": signal,
        "article_count": len(news_articles),
        "articles": article_classifications,
        "details": details,
        "interpretation": f"Overall {label} sentiment - {signal['interpretation']}"
    }


# ════════════════════════════════════════════════════════════════════════════════
# EXAMPLE USAGE
# ════════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Test TextBlob sentiment
    test_news = [
        {
            "title": "Reliance Industries beats profit expectations",
            "description": "Strong Q3 results with 15% profit growth",
            "publishedAt": "2024-01-15"
        },
        {
            "title": "Oil prices surge, impacting Reliance stock",
            "description": "Geopolitical tensions push crude prices higher",
            "publishedAt": "2024-01-14"
        },
        {
            "title": "Reliance Q4 guidance disappoints analysts",
            "description": "Management lowers full-year earnings forecast",
            "publishedAt": "2024-01-13"
        }
    ]
    
    report = sentiment_analysis_report("RELIANCE.NS", test_news)
    print("\n📰 SENTIMENT ANALYSIS REPORT")
    print(f"Stock: {report['stock']}")
    print(f"Overall Sentiment: {report['sentiment_label']} ({report['aggregate_sentiment']:.3f})")
    print(f"Signal Bias: {report['signal_bias']['bias']}")
    print(f"\nArticle Breakdown:")
    for article in report['articles']:
        print(f"  • {article['title']}: {article['sentiment']} ({article['score']})")
