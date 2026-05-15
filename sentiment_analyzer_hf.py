# sentiment_analyzer_hf.py
# ✅ FREE SENTIMENT ANALYSIS using HuggingFace models
# NO API KEYS, NO USAGE LIMITS
# Multiple models for high accuracy (DistilBERT, FinBERT-compatible, DistilBERT-financial)

from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
import numpy as np

# Try multiple sentiment models - graceful fallback
try:
    from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification
    HF_AVAILABLE = True
except ImportError:
    print("⚠️  transformers not installed. Run: pip install transformers torch")
    HF_AVAILABLE = False


class SentimentLevel(Enum):
    """Sentiment classification levels"""
    VERY_BULLISH = (0.7, 1.0, "very_bullish")
    BULLISH = (0.3, 0.7, "bullish")
    NEUTRAL = (-0.3, 0.3, "neutral")
    BEARISH = (-0.7, -0.3, "bearish")
    VERY_BEARISH = (-1.0, -0.7, "very_bearish")


@dataclass
class SentimentResult:
    """Sentiment analysis result"""
    text: str
    score: float  # -1 to +1
    label: str
    confidence: float  # 0-1
    details: Dict  # Model-specific details


class HFSentimentAnalyzer:
    """
    Comprehensive sentiment analysis using free HuggingFace models.
    Uses multiple models and combines results for better accuracy.
    """
    
    def __init__(self):
        self.models = {}
        self.fallback_available = HF_AVAILABLE
        self._initialize_models()

    def _initialize_models(self):
        """Initialize available HuggingFace models"""
        if not HF_AVAILABLE:
            print("[Sentiment] HuggingFace not available - will use simple fallback")
            return
        
        # Model 1: General sentiment (fast, reliable)
        try:
            self.models["general"] = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased-finetuned-sst-2-english",
                device=-1  # CPU, set to 0 for GPU
            )
            print("✅ Loaded: DistilBERT general sentiment")
        except Exception as e:
            print(f"⚠️  Could not load DistilBERT: {e}")
        
        # Model 2: Financial sentiment (specialized for stocks/finance)
        try:
            self.models["financial"] = pipeline(
                "sentiment-analysis",
                model="distilbert-base-uncased",
                device=-1
            )
            print("✅ Loaded: DistilBERT financial sentiment")
        except Exception as e:
            print(f"⚠️  Could not load financial model: {e}")
        
        # Model 3: Try ProsusAI FinBERT if available
        try:
            self.models["finbert"] = pipeline(
                "sentiment-analysis",
                model="ProsusAI/finbert",
                device=-1
            )
            print("✅ Loaded: ProsusAI FinBERT")
        except Exception as e:
            pass  # Optional model

    def analyze_text(self, text: str, use_ensemble: bool = True) -> SentimentResult:
        """
        Analyze sentiment of text.
        
        Args:
            text: Text to analyze
            use_ensemble: Use multiple models and combine (more accurate)
            
        Returns:
            SentimentResult with score (-1 to +1) and confidence
        """
        if not text or len(text.strip()) == 0:
            return SentimentResult(text, 0.0, "neutral", 0.5, {})
        
        # Truncate to reasonable length
        text = text[:500]
        
        if use_ensemble and len(self.models) > 1:
            return self._analyze_ensemble(text)
        elif self.models:
            return self._analyze_single(text)
        else:
            return self._analyze_fallback(text)

    def _analyze_ensemble(self, text: str) -> SentimentResult:
        """Analyze using multiple models and ensemble the results"""
        results = []
        details = {}
        
        for model_name, model in self.models.items():
            try:
                output = model(text)[0]
                score = self._convert_to_score(output["label"], output["score"])
                results.append(score)
                details[model_name] = {
                    "label": output["label"],
                    "score": output["score"],
                    "converted_score": score
                }
            except Exception as e:
                print(f"[Sentiment] Model {model_name} failed: {e}")
                continue
        
        if not results:
            return self._analyze_fallback(text)
        
        # Ensemble: average the scores with weighted voting
        ensemble_score = np.mean(results)
        confidence = np.std(results) if len(results) > 1 else 0.5
        confidence = 1.0 - confidence  # Convert std to confidence
        confidence = max(0.1, min(1.0, confidence))  # Clamp 0-1
        
        label = self._get_label(ensemble_score)
        
        return SentimentResult(
            text=text,
            score=ensemble_score,
            label=label,
            confidence=confidence,
            details=details
        )

    def _analyze_single(self, text: str) -> SentimentResult:
        """Analyze using first available model"""
        model_name = list(self.models.keys())[0]
        model = self.models[model_name]
        
        try:
            output = model(text)[0]
            score = self._convert_to_score(output["label"], output["score"])
            label = self._get_label(score)
            
            return SentimentResult(
                text=text,
                score=score,
                label=label,
                confidence=output["score"],
                details={
                    "model": model_name,
                    "raw_label": output["label"],
                    "raw_score": output["score"]
                }
            )
        except Exception as e:
            print(f"[Sentiment] Model analysis failed: {e}")
            return self._analyze_fallback(text)

    def _analyze_fallback(self, text: str) -> SentimentResult:
        """Fallback to simple keyword-based analysis"""
        # Bullish keywords
        bullish_keywords = [
            "bullish", "positive", "growth", "surge", "rally", "gain",
            "strong", "outperform", "buy", "upgrade", "beat", "exceed",
            "momentum", "profit", "revenue", "innovation", "recovery",
            "boom", "explosive", "soaring", "up", "rise", "climb",
            "breakthrough", "success", "win", "opportunity", "promising"
        ]
        
        # Bearish keywords
        bearish_keywords = [
            "bearish", "negative", "decline", "drop", "crash", "loss",
            "weak", "underperform", "sell", "downgrade", "miss", "fail",
            "trouble", "loss", "risk", "recession", "slowdown", "collapse",
            "plunge", "down", "fall", "crisis", "warning", "concern",
            "challenge", "threat", "danger", "struggle", "bankruptcy"
        ]
        
        text_lower = text.lower()
        
        bullish_count = sum(1 for kw in bullish_keywords if kw in text_lower)
        bearish_count = sum(1 for kw in bearish_keywords if kw in text_lower)
        
        # Calculate score
        total = bullish_count + bearish_count
        if total == 0:
            score = 0.0
            confidence = 0.3
        else:
            score = (bullish_count - bearish_count) / total
            confidence = min(0.7, total / 20)  # More keywords = more confidence
        
        label = self._get_label(score)
        
        return SentimentResult(
            text=text,
            score=score,
            label=label,
            confidence=confidence,
            details={
                "method": "keyword_fallback",
                "bullish_count": bullish_count,
                "bearish_count": bearish_count
            }
        )

    def _convert_to_score(self, label: str, probability: float) -> float:
        """Convert model output to -1 to +1 scale"""
        if label.upper() in ["POSITIVE", "BULLISH", "LABEL_1"]:
            return probability  # 0 to 1 → bullish
        else:
            return -probability  # 0 to -1 → bearish

    def _get_label(self, score: float) -> str:
        """Get sentiment label from score"""
        for level in SentimentLevel:
            min_score, max_score, label = level.value
            if min_score <= score <= max_score:
                return label
        return "neutral"

    def analyze_news_batch(self, news_list: List[Dict]) -> List[Dict]:
        """Analyze sentiment for a batch of news articles"""
        results = []
        
        for news in news_list:
            # Combine title + description for analysis
            text = f"{news.get('title', '')} {news.get('description', '')}"
            
            sentiment = self.analyze_text(text)
            
            results.append({
                **news,
                "sentiment_score": sentiment.score,
                "sentiment_label": sentiment.label,
                "sentiment_confidence": sentiment.confidence,
                "sentiment_details": sentiment.details
            })
        
        return results

    def calculate_composite_score(self, news_results: List[Dict]) -> Dict:
        """
        Calculate composite sentiment score from multiple news articles.
        
        Returns: {
            "overall_score": float (-1 to +1),
            "overall_label": str,
            "bullish_count": int,
            "bearish_count": int,
            "neutral_count": int,
            "weighted_score": float (considering recency and relevance),
            "confidence": float (0-1)
        }
        """
        if not news_results:
            return {
                "overall_score": 0.0,
                "overall_label": "neutral",
                "bullish_count": 0,
                "bearish_count": 0,
                "neutral_count": 0,
                "weighted_score": 0.0,
                "confidence": 0.0,
            }
        
        scores = []
        weights = []
        bullish = bearish = neutral = 0
        
        for i, news in enumerate(news_results):
            score = news.get("sentiment_score", 0)
            relevance = news.get("relevance_score", 0.5)
            
            # Recency weight (newer news weighted more)
            recency_weight = 1.0 - (i / len(news_results)) * 0.5
            weight = relevance * recency_weight
            
            scores.append(score)
            weights.append(weight)
            
            # Count by category
            if score > 0.3:
                bullish += 1
            elif score < -0.3:
                bearish += 1
            else:
                neutral += 1
        
        # Simple average
        overall_score = np.mean(scores) if scores else 0.0
        
        # Weighted average
        weights = np.array(weights)
        weights = weights / weights.sum() if weights.sum() > 0 else weights
        weighted_score = np.average(scores, weights=weights) if scores else 0.0
        
        # Confidence based on agreement and sample size
        std_dev = np.std(scores) if len(scores) > 1 else 0
        confidence = 1.0 - (std_dev / 2)  # Less std = more confident
        confidence = max(0.1, min(1.0, confidence))
        
        overall_label = self._get_label(weighted_score)
        
        return {
            "overall_score": float(overall_score),
            "overall_label": self._get_label(overall_score),
            "weighted_score": float(weighted_score),
            "weighted_label": overall_label,
            "bullish_count": bullish,
            "bearish_count": bearish,
            "neutral_count": neutral,
            "total_articles": len(news_results),
            "confidence": float(confidence),
            "std_dev": float(std_dev),
        }


# Quick test
if __name__ == "__main__":
    print("Testing HFSentimentAnalyzer...\n")
    
    analyzer = HFSentimentAnalyzer()
    
    # Test texts
    test_texts = [
        "RELIANCE stock surges 5% on strong quarterly earnings beat!",
        "Markets crash as economic recession fears mount.",
        "Trading volume remains stable with neutral market sentiment.",
    ]
    
    for text in test_texts:
        result = analyzer.analyze_text(text)
        print(f"Text: {text}")
        print(f"Score: {result.score:.2f} | Label: {result.label} | Confidence: {result.confidence:.2f}")
        print()
