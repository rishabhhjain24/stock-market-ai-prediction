# dashboard.py - Professional Streamlit dashboard for the AI trading system
# WHY: Clean, organized multi-page dashboard for traders to monitor multiple features
# Instead of launching scripts, scroll through professional charts and metrics

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import yfinance as yf

from controller import run_pipeline
from watchlist_scanner import WatchlistScanner
from market_regime import MarketRegimeAnalyzer, MarketRegime
from paper_trading import PaperTradingEngine
from sentiment_engine import sentiment_analysis_report
from chart_patterns import detect_all_patterns
from data_engine import get_features
from config import DEFAULT_STOCK, WATCHLIST, ACTIVE_STRATEGY

# ════════════════════════════════════════════════════════════════════════════════
# PAGE CONFIG
# ════════════════════════════════════════════════════════════════════════════════

st.set_page_config(
    page_title="🤖 AI Stock Trading System",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main {
        padding: 0rem 0rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .signal-strong-buy { color: #00cc00; font-weight: bold; }
    .signal-buy { color: #66ff66; font-weight: bold; }
    .signal-sell { color: #ff6666; font-weight: bold; }
    .signal-strong-sell { color: #cc0000; font-weight: bold; }
    .signal-neutral { color: #999999; }
</style>
""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
# INITIALIZE SESSION STATE
# ════════════════════════════════════════════════════════════════════════════════

if "paper_trading_engine" not in st.session_state:
    st.session_state.paper_trading_engine = PaperTradingEngine(initial_balance=100000)

if "scan_results" not in st.session_state:
    st.session_state.scan_results = None

if "last_selected_stock" not in st.session_state:
    st.session_state.last_selected_stock = DEFAULT_STOCK


# ════════════════════════════════════════════════════════════════════════════════
# SIDEBAR NAVIGATION
# ════════════════════════════════════════════════════════════════════════════════

st.sidebar.title("🎯 Navigation")
page = st.sidebar.radio(
    "Select Page",
    [
        "📊 Main Dashboard",
        "🎯 Single Stock Analysis",
        "📈 Watchlist Scanner",
        "📝 Paper Trading",
        "⚙️ Settings & Info"
    ]
)

st.sidebar.divider()
st.sidebar.subheader("⚡ Quick Stats")

engine = st.session_state.paper_trading_engine
stats = engine.calculate_stats()

if stats:
    st.sidebar.metric("💰 Account Balance", f"${stats.get('current_balance', 100000):,.0f}")
    st.sidebar.metric("📊 Return", f"{stats.get('return_since_start', 0):.1f}%")
    st.sidebar.metric("🏆 Win Rate", f"{stats.get('win_rate', 0):.1%}")
    st.sidebar.metric("📈 Profit Factor", f"{stats.get('profit_factor', 0):.2f}")

st.sidebar.divider()
st.sidebar.subheader("🛠️ System Info")
st.sidebar.caption(f"Active Strategy: {ACTIVE_STRATEGY}")
st.sidebar.caption(f"Watchlist: {len(WATCHLIST)} stocks")
st.sidebar.info("Data updates daily at market close.")


# ════════════════════════════════════════════════════════════════════════════════
# PAGE 1: MAIN DASHBOARD
# ════════════════════════════════════════════════════════════════════════════════

if page == "📊 Main Dashboard":
    st.title("🤖 AI Stock Trading System")
    st.markdown("Real-time AI-powered trading signals powered by ML, sentiment, and technicals")
    
    # Key metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        index_data = yf.download("^NSEI", period="1y", progress=False)
        # Enrich with indicators
        import pandas as pd
        if "ATR" not in index_data.columns:
            high_low = index_data['High'] - index_data['Low']
            high_close = abs(index_data['High'] - index_data['Close'].shift())
            low_close = abs(index_data['Low'] - index_data['Close'].shift())
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            index_data["ATR"] = tr.rolling(14).mean()
        
        with col1:
            # Market regime
            regime = MarketRegimeAnalyzer.detect_regime(index_data)
            st.metric("Market Regime", regime.value.upper(), help="NSE Nifty 50 regime")
        
        with col2:
            vol_regime = MarketRegimeAnalyzer.detect_volatility_regime(index_data)
            st.metric("Volatility", vol_regime.value.upper(), help="Current market volatility level")
        
        with col3:
            health = MarketRegimeAnalyzer.market_health_check(index_data)
            status = "✅ HEALTHY" if health["is_healthy"] else "⚠️ CAUTION"
            st.metric("Market Health", status, help=f"Warnings: {len(health['warnings'])}")
    except Exception as e:
        st.warning(f"Market analysis unavailable: {str(e)[:50]}...")
    
    with col4:
        st.metric("Last Update", datetime.now().strftime("%H:%M:%S"), help="Latest scan time")
    
    st.divider()
    
    # Quick scan results
    st.subheader("📊 Today's Top Signals")
    
    col_scan, col_refresh = st.columns([4, 1])
    with col_refresh:
        if st.button("🔄 Refresh", use_container_width=True):
            st.session_state.scan_results = None
    
    if st.session_state.scan_results is None:
        with st.spinner("Scanning watchlist..."):
            scanner = WatchlistScanner(stocks=WATCHLIST[:10])  # Demo with 10 stocks
            st.session_state.scan_results = scanner.scan_watchlist()
    
    # Display top signals
    results = st.session_state.scan_results
    
    if results:
        # Separate bullish and bearish
        bullish = [r for r in results if r["score"] > 0.2]
        bearish = [r for r in results if r["score"] < -0.2]
        neutral = [r for r in results if abs(r["score"]) <= 0.2]
        
        tab1, tab2, tab3 = st.tabs([
            f"🟢 BUY Signals ({len(bullish)})",
            f"🔴 SELL Signals ({len(bearish)})",
            f"⚪ NEUTRAL ({len(neutral)})"
        ])
        
        with tab1:
            if bullish:
                df_display = pd.DataFrame([{
                    "Stock": r["stock"],
                    "Signal Score": f"{r['score']:.3f}",
                    "ML Prob": f"{r['ml_probability']:.2f}",
                    "Sentiment": f"{r['sentiment']:.2f}",
                    "Price": f"₹{r['price']:.2f}",
                    "Pattern": r["pattern_detected"] or "None",
                    "RSI": f"{r['rsi']:.1f}",
                } for r in bullish[:10]])
                
                st.dataframe(df_display, use_container_width=True, hide_index=True)
            else:
                st.info("No buy signals currently")
        
        with tab2:
            if bearish:
                df_display = pd.DataFrame([{
                    "Stock": r["stock"],
                    "Signal Score": f"{r['score']:.3f}",
                    "ML Prob": f"{r['ml_probability']:.2f}",
                    "Sentiment": f"{r['sentiment']:.2f}",
                    "Price": f"₹{r['price']:.2f}",
                    "Pattern": r["pattern_detected"] or "None",
                    "RSI": f"{r['rsi']:.1f}",
                } for r in bearish[:10]])
                
                st.dataframe(df_display, use_container_width=True, hide_index=True)
            else:
                st.info("No sell signals currently")
        
        with tab3:
            if neutral:
                df_display = pd.DataFrame([{
                    "Stock": r["stock"],
                    "Signal Score": f"{r['score']:.3f}",
                    "ML Prob": f"{r['ml_probability']:.2f}",
                    "Price": f"₹{r['price']:.2f}",
                } for r in neutral[:10]])
                
                st.dataframe(df_display, use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════════════════════
# PAGE 2: SINGLE STOCK ANALYSIS
# ════════════════════════════════════════════════════════════════════════════════

elif page == "🎯 Single Stock Analysis":
    st.title("📈 Single Stock Detailed Analysis")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        stock = st.text_input(
            "Enter Stock Symbol",
            value=st.session_state.last_selected_stock,
            placeholder="e.g., RELIANCE.NS, TCS.NS, INFY.NS"
        )
    with col2:
        if st.button("🔍 Analyze", use_container_width=True):
            st.session_state.last_selected_stock = stock
    
    if stock and st.button("Analyze", key="analyze_btn"):
        with st.spinner("Analyzing..."):
            result = run_pipeline(stock)
            
            if result is None:
                st.error("❌ Could not fetch data for this stock. Check symbol.")
            else:
                # Main metrics
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Decision", result["decision"], "Signal")
                with col2:
                    st.metric("Confidence", f"{result['confidence']:.1%}", "ML Probability")
                with col3:
                    st.metric("Price", f"₹{result['price']:.2f}", "Current")
                with col4:
                    st.metric("RSI(14)", f"{result['rsi']:.1f}", f"Strength: {'Weak' if result['rsi'] < 30 else 'Strong' if result['rsi'] > 70 else 'Normal'}")
                
                st.divider()
                
                # AI Analysis
                st.subheader("🤖 AI Analysis")
                st.info(result["explanation"])
                
                # Technical indicators
                st.subheader("📊 Technical Indicators")
                ind_col1, ind_col2, ind_col3 = st.columns(3)
                
                with ind_col1:
                    st.metric("EMA 20", f"₹{result['ema20']:.2f}")
                    st.metric("EMA 50", f"₹{result['ema50']:.2f}")
                
                with ind_col2:
                    st.metric("MACD", f"{result['macd']:.4f}")
                    st.metric("MACD Signal", f"{result['macd_signal']:.4f}")
                
                with ind_col3:
                    st.metric("ATR(14)", f"₹{result['atr']:.2f}")
                    st.metric("Stoch %K", f"{result['stoch_k']:.1f}")
                
                # Regimes
                st.subheader("🎯 Market Regimes")
                regime_col1, regime_col2, regime_col3 = st.columns(3)
                
                with regime_col1:
                    st.metric(
                        "Trend",
                        "📈 Bullish" if result["trend_regime"] == 1 else "📉 Bearish",
                        "EMA 20 vs EMA 50"
                    )
                
                with regime_col2:
                    st.metric(
                        "Volatility",
                        "🔴 High" if result["volatility_regime"] == 1 else "🟢 Low",
                        "Bollinger Band Width"
                    )
                
                with regime_col3:
                    st.metric(
                        "Volume",
                        "📊 Above Avg" if result["volume_regime"] == 1 else "📉 Below Avg",
                        "20-day MA"
                    )
                
                # Feature importances
                if result["importances"]:
                    st.subheader("🔍 Key Decision Drivers")
                    top_features = sorted(result["importances"].items(), key=lambda x: x[1], reverse=True)[:5]
                    
                    feature_names = [f[0] for f in top_features]
                    feature_scores = [f[1] for f in top_features]
                    
                    fig = go.Figure(data=[
                        go.Bar(x=feature_scores, y=feature_names, orientation='h')
                    ])
                    fig.update_layout(title="Feature Importance", height=300)
                    st.plotly_chart(fig, use_container_width=True)
                
                # News sentiment
                if result["news"]:
                    st.subheader("📰 Recent News")
                    for i, news in enumerate(result["news"][:5]):
                        st.caption(f"• {news}")


# ════════════════════════════════════════════════════════════════════════════════
# PAGE 3: WATCHLIST SCANNER
# ════════════════════════════════════════════════════════════════════════════════

elif page == "📈 Watchlist Scanner":
    st.title("📈 Multi-Stock Watchlist Scanner")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("🔄 Scan All", use_container_width=True):
            st.session_state.scan_results = None
    
    if st.session_state.scan_results is None:
        with st.spinner("Scanning all watchlist stocks..."):
            scanner = WatchlistScanner(stocks=WATCHLIST[:15])  # Scan top 15
            st.session_state.scan_results = scanner.scan_watchlist()
    
    scanner = WatchlistScanner()
    scanner.scan_results = st.session_state.scan_results
    report = scanner.generate_report()
    
    # Summary stats
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("📊 Total Scanned", report["total_scanned"])
    with col2:
        st.metric("🟢 Strong Buys", report["signals"]["strong_buy"])
    with col3:
        st.metric("🟡 Buys", report["signals"]["buy"])
    with col4:
        st.metric("🔴 Sells", report["signals"]["sell"])
    with col5:
        st.metric("🟠 Consensus", report["statistics"]["consensus_signals"])
    
    st.divider()
    
    # Display signal distribution
    st.subheader("📊 Signal Distribution")
    
    signal_data = {
        "Signal Type": ["Strong Buy", "Buy", "Sell", "Strong Sell", "Neutral"],
        "Count": [
            report["signals"]["strong_buy"],
            report["signals"]["buy"],
            report["signals"]["sell"],
            report["signals"]["strong_sell"],
            report["signals"]["neutral"],
        ],
        "Color": ["darkgreen", "lightgreen", "lightcoral", "darkred", "gray"]
    }
    
    fig = go.Figure(data=[go.Bar(
        x=signal_data["Signal Type"],
        y=signal_data["Count"],
        marker_color=signal_data["Color"]
    )])
    fig.update_layout(title="Trading Signals Distribution", height=400)
    st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════════
# PAGE 4: PAPER TRADING
# ════════════════════════════════════════════════════════════════════════════════

elif page == "📝 Paper Trading":
    st.title("📝 Paper Trading Simulator")
    
    engine = st.session_state.paper_trading_engine
    
    # Account stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("💰 Account Balance", f"${engine.current_balance:,.0f}")
    with col2:
        st.metric("📈 Initial Balance", f"${engine.initial_balance:,.0f}")
    with col3:
        st.metric("📊 Return %", f"{(engine.current_balance - engine.initial_balance) / engine.initial_balance * 100:.1f}%")
    with col4:
        st.metric("📋 Open Trades", len(engine.open_trades))
    
    st.divider()
    
    # Enter new trade
    st.subheader("📥 Enter New Trade")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        trade_stock = st.text_input("Stock Symbol", "RELIANCE.NS", key="trade_stock")
    with col2:
        trade_type = st.selectbox("Type", ["long", "short"])
    with col3:
        trade_qty = st.number_input("Quantity", min_value=1, value=10)
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        entry = st.number_input("Entry Price", min_value=0.01, value=2500.0)
    with col2:
        stop = st.number_input("Stop Loss", min_value=0.01, value=2450.0)
    with col3:
        target = st.number_input("Target", min_value=0.01, value=2600.0)
    with col4:
        reason = st.text_input("Reason", "ML Signal")
    
    if st.button("📝 Enter Trade", use_container_width=True):
        try:
            trade = engine.enter_trade(
                stock=trade_stock,
                entry_price=entry,
                quantity=trade_qty,
                stop_loss=stop,
                target_price=target,
                trade_type=trade_type,
                reason=reason
            )
            st.success(f"✅ Trade {trade.id} entered!")
            st.rerun()
        except ValueError as e:
            st.error(f"❌ {e}")
    
    st.divider()
    
    # Open trades
    st.subheader("📂 Open Trades")
    if engine.open_trades:
        open_trades_data = []
        for t in engine.open_trades:
            open_trades_data.append({
                "ID": t.id,
                "Stock": t.stock,
                "Type": t.trade_type.upper(),
                "Entry": f"₹{t.entry_price:.2f}",
                "Qty": t.quantity,
                "Stop": f"₹{t.stop_loss:.2f}",
                "Target": f"₹{t.target_price:.2f}",
                "Status": t.status,
            })
        
        st.dataframe(open_trades_data, use_container_width=True, hide_index=True)
    else:
        st.info("No open trades")


# ════════════════════════════════════════════════════════════════════════════════
# PAGE 5: SETTINGS & INFO
# ════════════════════════════════════════════════════════════════════════════════

elif page == "⚙️ Settings & Info":
    st.title("⚙️ System Settings & Information")
    
    tab1, tab2, tab3 = st.tabs(["📋 Documentation", "🔧 Configuration", "ℹ️ About"])
    
    with tab1:
        st.subheader("📖 How to Use")
        st.markdown("""
        ### 🎯 Main Dashboard
        - Quick overview of market regime and top trading signals
        - Refresh button to update watchlist scans
        - See which stocks have the strongest signals
        
        ### 📈 Single Stock Analysis
        - Deep dive into any stock
        - AI explanation powered by Gemini
        - Technical indicators breakdown
        - Feature importance analysis
        
        ### 📊 Watchlist Scanner
        - Automatically scan all watchlist stocks
        - Multi-threading for fast analysis
        - Sorted by signal strength
        - Consensus signal detection
        
        ### 📝 Paper Trading
        - Test strategies without real money
        - Track P&L across trades
        - Forward test the system
        """)
    
    with tab2:
        st.subheader("⚙️ Current Configuration")
        
        config_data = {
            "Parameter": [
                "Active Strategy",
                "BUY Threshold",
                "Watchlist Size",
                "Risk Per Trade",
                "Max Position Size",
            ],
            "Value": [
                ACTIVE_STRATEGY,
                "0.60 (60% probability)",
                f"{len(WATCHLIST)} stocks",
                "2% of account",
                "10% max",
            ]
        }
        
        st.dataframe(config_data, use_container_width=True, hide_index=True)
    
    with tab3:
        st.subheader("🤖 About This System")
        st.markdown("""
        **AI Stock Trading System** - Educational trading platform
        
        **Features:**
        - ML-based price prediction (GradientBoosting)
        - News sentiment analysis
        - Technical analysis with 18+ indicators
        - Chart pattern detection
        - Market regime analysis
        - Risk management & position sizing
        - Paper trading simulation
        - Professional Streamlit dashboard
        
        **Data Sources:**
        - yfinance for market data
        - NewsAPI for news & sentiment
        - Gemini API for AI analysis
        
        **Educational Use Only**
        This system is for learning and research purposes.
        Past performance does not guarantee future results.
        """)


# ════════════════════════════════════════════════════════════════════════════════
# FOOTER
# ════════════════════════════════════════════════════════════════════════════════

st.divider()
st.caption(
    "🎓 Educational Trading System | "
    "Not financial advice | "
    f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
)
