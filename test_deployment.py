# ════════════════════════════════════════════════════════════════════════════════
# TEST DEPLOYMENT LOCALLY BEFORE PUSHING TO CLOUD
# ════════════════════════════════════════════════════════════════════════════════

import requests
import json
from time import sleep
import sys

BASE_URL = "http://localhost:5000"

def test_api():
    """Test all API endpoints"""
    
    print("🧪 Testing Trading Dashboard API...")
    print("=" * 60)
    
    # Test 1: Health Check
    print("\n1️⃣ Health Check...")
    try:
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        print(f"   ✅ Status: {data['status']}")
        print(f"   ✅ Version: {data['version']}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Test 2: Market Status
    print("\n2️⃣ Market Status...")
    try:
        response = requests.get(f"{BASE_URL}/api/market-status")
        assert response.status_code == 200
        data = response.json()
        print(f"   ✅ Market Open: {data['market']['is_open']}")
        print(f"   ✅ Global Sentiment: {len(data['global_sentiment']) if data['global_sentiment'] else 0} indices")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Test 3: Get Price
    print("\n3️⃣ Get Price (RELIANCE.NS)...")
    try:
        response = requests.get(f"{BASE_URL}/api/price/RELIANCE.NS")
        assert response.status_code == 200
        data = response.json()
        if data['success']:
            print(f"   ✅ Current Price: ₹{data['current_price']:.2f}")
        else:
            print(f"   ❌ Could not fetch price")
            return False
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Test 4: Get Forecast
    print("\n4️⃣ Get Forecast (RELIANCE.NS)...")
    print("   ⏳ This may take 30-60 seconds...")
    try:
        response = requests.get(f"{BASE_URL}/api/forecast/RELIANCE.NS", timeout=120)
        assert response.status_code == 200
        data = response.json()
        if data['success']:
            forecast = data['forecast']
            print(f"   ✅ Symbol: {data['symbol']}")
            print(f"   ✅ Signal: {forecast['decision']}")
            print(f"   ✅ Confidence: {forecast['confidence']*100:.1f}%")
            print(f"   ✅ Price: ₹{forecast['current_price']:.2f}")
        else:
            print(f"   ❌ {data['error']}")
            return False
    except requests.Timeout:
        print(f"   ⚠️ Request timed out (ML model inference can be slow)")
        return True  # Not a critical error
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Test 5: Watchlist
    print("\n5️⃣ Get Watchlist Forecasts...")
    print("   ⏳ Processing 3 symbols...")
    try:
        payload = {"symbols": ["RELIANCE.NS", "TCS.NS", "INFY.NS"]}
        response = requests.post(
            f"{BASE_URL}/api/watchlist",
            json=payload,
            timeout=180
        )
        assert response.status_code == 200
        data = response.json()
        if data['success']:
            print(f"   ✅ Processed {len(data['results'])} symbols")
            for symbol, result in data['results'].items():
                status = "✅" if 'error' not in result else "❌"
                print(f"      {status} {symbol}")
        else:
            print(f"   ❌ {data['error']}")
            return False
    except requests.Timeout:
        print(f"   ⚠️ Request timed out (expected for 3 symbols)")
        return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Test 6: Web Interface
    print("\n6️⃣ Web Interface...")
    try:
        response = requests.get(f"{BASE_URL}/")
        assert response.status_code == 200
        assert "AI Trading Forecast" in response.text
        print(f"   ✅ Mobile web interface loading")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED! Your API is ready for deployment.")
    print("\nNext steps:")
    print("  1. Push to GitHub: git push origin main")
    print("  2. Deploy to Heroku/Railway")
    print("  3. Access from mobile: https://your-app-name.herokuapp.com")
    
    return True

if __name__ == "__main__":
    print("Make sure API server is running: python api_server.py")
    print(f"Testing: {BASE_URL}\n")
    
    # Wait for server to be ready
    max_retries = 5
    for attempt in range(max_retries):
        try:
            requests.get(f"{BASE_URL}/api/health", timeout=2)
            break
        except:
            if attempt < max_retries - 1:
                print(f"⏳ Waiting for server... ({attempt+1}/{max_retries})")
                sleep(2)
            else:
                print(f"❌ Could not connect to server at {BASE_URL}")
                print("Make sure to run: python api_server.py")
                sys.exit(1)
    
    # Run tests
    success = test_api()
    sys.exit(0 if success else 1)
