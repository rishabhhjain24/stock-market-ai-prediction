# ════════════════════════════════════════════════════════════════════════════════
# 📱 MOBILE-FRIENDLY API SERVER
# Flask backend for trading dashboard - accessible from web & mobile
# ════════════════════════════════════════════════════════════════════════════════

from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
import pandas as pd
import yfinance as yf
from datetime import datetime, time
import pytz
import logging
import json
from functools import lru_cache

# Import your existing engines
from trading_forecast_engine import TradingForecastEngine
from news_sentiment_unified import analyze_news_sentiment, get_latest_news

# ════════════════════════════════════════════════════════════════════════════════
# 🔧 SETUP
# ════════════════════════════════════════════════════════════════════════════════

app = Flask(__name__)
CORS(app)  # Enable CORS for mobile & cross-origin requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global engine instance
forecast_engine = None

def get_forecast_engine():
    global forecast_engine
    if forecast_engine is None:
        forecast_engine = TradingForecastEngine()
    return forecast_engine

# ════════════════════════════════════════════════════════════════════════════════
# 🌍 HELPER FUNCTIONS
# ════════════════════════════════════════════════════════════════════════════════

def validate_market_hours():
    """Check if market is currently open"""
    tz = pytz.timezone('Asia/Kolkata')
    now = datetime.now(tz)
    market_open = time(9, 15)
    market_close = time(15, 30)
    is_weekday = now.weekday() < 5
    is_open = is_weekday and market_open <= now.time() < market_close
    return {"is_open": is_open, "current_time": now.isoformat(), "market_hours": "9:15 AM - 3:30 PM IST"}

def get_global_market_sentiment():
    """Fetch global market context"""
    try:
        indices = {
            '^GSPC': 'S&P 500',
            '^DJI': 'Dow Jones',
            '^NSEI': 'NIFTY 50',
            '^BSESN': 'Sensex'
        }
        
        sentiment = {}
        for ticker, name in indices.items():
            try:
                data = yf.download(ticker, period="5d", interval="1d", progress=False)
                if data is not None and not data.empty and data.shape[0] >= 2:
                    change = float((data['Close'].iloc[-1] - data['Close'].iloc[-2]) / data['Close'].iloc[-2] * 100)
                    sentiment[ticker] = {
                        'name': name,
                        'change': round(change, 2),
                        'current_price': float(data['Close'].iloc[-1])
                    }
            except:
                continue
        
        return sentiment if sentiment else None
    except Exception as e:
        logger.error(f"Market sentiment error: {str(e)}")
        return None

# ════════════════════════════════════════════════════════════════════════════════
# 📡 API ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════════

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'version': '2.0'
    })

@app.route('/api/market-status', methods=['GET'])
def market_status():
    """Get current market status"""
    try:
        status = validate_market_hours()
        sentiment = get_global_market_sentiment()
        return jsonify({
            'success': True,
            'market': status,
            'global_sentiment': sentiment
        })
    except Exception as e:
        logger.error(f"Market status error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/forecast/<symbol>', methods=['GET'])
def get_forecast(symbol):
    """Get AI trading forecast for a symbol"""
    try:
        symbol = symbol.upper()
        
        # Get forecast
        engine = get_forecast_engine()
        forecast_result = engine.generate_forecast(symbol)
        
        if forecast_result is None:
            return jsonify({'success': False, 'error': 'Could not generate forecast'}), 400
        
        # Get news sentiment
        news_data = None
        try:
            news = get_latest_news(symbol, limit=5)
            news_sentiment = analyze_news_sentiment(news)
            news_data = {
                'articles': news[:3],  # Limit to 3 articles
                'sentiment': news_sentiment
            }
        except:
            pass
        
        return jsonify({
            'success': True,
            'symbol': symbol,
            'forecast': forecast_result,
            'news': news_data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Forecast error for {symbol}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/price/<symbol>', methods=['GET'])
def get_price(symbol):
    """Get current price and basic info"""
    try:
        symbol = symbol.upper()
        data = yf.download(symbol, period="1d", interval="1h", progress=False)
        
        if data is None or data.empty:
            return jsonify({'success': False, 'error': 'Invalid symbol'}), 400
        
        current_price = float(data['Close'].iloc[-1])
        return jsonify({
            'success': True,
            'symbol': symbol,
            'current_price': current_price,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Price error for {symbol}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/watchlist', methods=['POST'])
def get_watchlist_forecast():
    """Get forecasts for multiple symbols"""
    try:
        data = request.json
        symbols = data.get('symbols', [])
        
        if not symbols or len(symbols) > 20:
            return jsonify({'success': False, 'error': 'Invalid symbols list'}), 400
        
        engine = get_forecast_engine()
        results = {}
        
        for symbol in symbols:
            try:
                results[symbol] = engine.generate_forecast(symbol.upper())
            except:
                results[symbol] = {'error': 'Could not forecast'}
        
        return jsonify({
            'success': True,
            'results': results,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Watchlist error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ════════════════════════════════════════════════════════════════════════════════
# 📱 MOBILE WEB INTERFACE
# ════════════════════════════════════════════════════════════════════════════════

MOBILE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📈 AI Trading Forecast - Mobile</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 10px;
        }
        .container { max-width: 100%; margin: 0 auto; }
        .header {
            background: rgba(0, 0, 0, 0.3);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 20px;
        }
        .search-box {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        .search-box input {
            flex: 1;
            padding: 12px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
        }
        .search-box button {
            padding: 12px 24px;
            background: #00ff99;
            border: none;
            border-radius: 8px;
            font-weight: bold;
            cursor: pointer;
        }
        .market-status {
            background: rgba(0, 0, 0, 0.2);
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
        }
        .market-open { color: #00ff99; }
        .market-closed { color: #ff7b7b; }
        .card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .forecast-card {
            border-left: 5px solid #667eea;
        }
        .buy { border-left-color: #00ff99; }
        .sell { border-left-color: #ff7b7b; }
        .hold { border-left-color: #9aa3b2; }
        .signal {
            font-size: 24px;
            font-weight: bold;
            margin: 10px 0;
        }
        .confidence {
            font-size: 18px;
            color: #667eea;
            margin: 10px 0;
        }
        .price {
            font-size: 28px;
            font-weight: bold;
            color: #FFD700;
        }
        .timestamp {
            color: #999;
            font-size: 12px;
            margin-top: 10px;
        }
        .loader {
            text-align: center;
            color: white;
            padding: 20px;
        }
        .error {
            background: #ff7b7b;
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
        }
        .global-sentiment {
            background: white;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
        }
        .sentiment-row {
            display: flex;
            justify-content: space-between;
            padding: 10px 0;
            border-bottom: 1px solid #eee;
        }
        .sentiment-up { color: #00ff99; }
        .sentiment-down { color: #ff7b7b; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📈 AI Trading Forecast</h1>
            <p>Real-time predictions powered by AI</p>
        </div>
        
        <div id="marketStatus" class="market-status"></div>
        
        <div class="search-box">
            <input type="text" id="symbolInput" placeholder="Enter Stock (e.g., RELIANCE.NS)" value="RELIANCE.NS">
            <button onclick="searchForecast()">Search</button>
        </div>
        
        <div id="globalSentiment"></div>
        <div id="error"></div>
        <div id="forecast"></div>
    </div>

    <script>
        // Load market status
        async function loadMarketStatus() {
            try {
                const response = await fetch('/api/market-status');
                const data = await response.json();
                const statusDiv = document.getElementById('marketStatus');
                
                if (data.market.is_open) {
                    statusDiv.innerHTML = '<span class="market-open">🟢 MARKET OPEN - Real-time signals active</span>';
                } else {
                    statusDiv.innerHTML = '<span class="market-closed">🔴 MARKET CLOSED - Analysis only</span>';
                }
                
                // Display global sentiment
                if (data.global_sentiment) {
                    let html = '<div class="global-sentiment"><h3>Global Market Sentiment</h3>';
                    for (const [ticker, info] of Object.entries(data.global_sentiment)) {
                        const changeClass = info.change > 0 ? 'sentiment-up' : 'sentiment-down';
                        html += `
                            <div class="sentiment-row">
                                <span>${info.name}</span>
                                <span class="${changeClass}">${info.change > 0 ? '↑' : '↓'} ${Math.abs(info.change).toFixed(2)}%</span>
                            </div>
                        `;
                    }
                    html += '</div>';
                    document.getElementById('globalSentiment').innerHTML = html;
                }
            } catch (error) {
                console.error('Error loading market status:', error);
            }
        }

        async function searchForecast() {
            const symbol = document.getElementById('symbolInput').value.trim();
            if (!symbol) return;
            
            const forecastDiv = document.getElementById('forecast');
            const errorDiv = document.getElementById('error');
            errorDiv.innerHTML = '';
            forecastDiv.innerHTML = '<div class="loader">🔄 Loading forecast...</div>';
            
            try {
                const response = await fetch(`/api/forecast/${symbol}`);
                const data = await response.json();
                
                if (!data.success) {
                    errorDiv.innerHTML = `<div class="error">⚠️ Error: ${data.error}</div>`;
                    forecastDiv.innerHTML = '';
                    return;
                }
                
                const forecast = data.forecast;
                const signalClass = forecast.decision.toLowerCase();
                
                let html = `
                    <div class="card forecast-card ${signalClass}">
                        <h2>${data.symbol}</h2>
                        <div class="price">₹${forecast.current_price.toFixed(2)}</div>
                        <div class="signal" style="color: ${signalClass === 'buy' ? '#00ff99' : signalClass === 'sell' ? '#ff7b7b' : '#9aa3b2'}">
                            ${forecast.decision.toUpperCase()}
                        </div>
                        <div class="confidence">Confidence: ${(forecast.confidence * 100).toFixed(1)}%</div>
                        <p><strong>Technical:</strong> ${forecast.technical_signal}</p>
                        <p><strong>AI Analysis:</strong> ${forecast.explanation.substring(0, 200)}...</p>
                        <div class="timestamp">${new Date(data.timestamp).toLocaleString()}</div>
                    </div>
                `;
                
                if (data.news && data.news.sentiment) {
                    html += `
                        <div class="card">
                            <h3>📰 News Sentiment</h3>
                            <p>${data.news.sentiment}</p>
                        </div>
                    `;
                }
                
                forecastDiv.innerHTML = html;
            } catch (error) {
                errorDiv.innerHTML = `<div class="error">⚠️ Connection error: ${error.message}</div>`;
                forecastDiv.innerHTML = '';
            }
        }

        // Load on page load
        loadMarketStatus();
        setInterval(loadMarketStatus, 60000); // Refresh every minute
        
        // Enter key support
        document.getElementById('symbolInput').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') searchForecast();
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve mobile web interface"""
    return render_template_string(MOBILE_HTML)

# ════════════════════════════════════════════════════════════════════════════════
# 🚀 RUN SERVER
# ════════════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
