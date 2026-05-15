# step8b_backtesting.py
# FIXED: proper returns alignment (use next-day return for today's BUY signal),
#        added Sharpe ratio, max drawdown, annualised return
import pandas as pd
import numpy as np
from config import DEFAULT_STOCK, DATA_DIR

symbol_safe = DEFAULT_STOCK.replace(".", "_")
df = pd.read_csv(f"{DATA_DIR}/final_trade_decisions.csv", index_col=0, parse_dates=True)
df.sort_index(inplace=True)

# ── Daily market return ────────────────────────────────────────────────────────
df["Market_Return"] = df["Close"].pct_change()

# ── Strategy return ────────────────────────────────────────────────────────────
# BUY signal on day T → we hold and earn the return on day T+1
df["Signal"]          = (df["Decision"] == "BUY").astype(int).shift(1).fillna(0)
df["Strategy_Return"] = df["Signal"] * df["Market_Return"]

df.dropna(subset=["Market_Return"], inplace=True)

# ── Equity curves ──────────────────────────────────────────────────────────────
df["Market_Equity"]   = (1 + df["Market_Return"]).cumprod()
df["Strategy_Equity"] = (1 + df["Strategy_Return"]).cumprod()

# ── Metrics helper ─────────────────────────────────────────────────────────────
def max_drawdown(equity: pd.Series) -> float:
    peak = equity.cummax()
    dd   = (equity - peak) / peak
    return dd.min()

def sharpe(returns: pd.Series, rf_annual: float = 0.06) -> float:
    rf_daily = (1 + rf_annual) ** (1 / 252) - 1
    excess   = returns - rf_daily
    return (excess.mean() / excess.std()) * np.sqrt(252) if excess.std() > 0 else 0.0

trade_mask   = df["Decision"] == "BUY"
total_trades = trade_mask.sum()
win_trades   = ((df["Strategy_Return"] > 0) & trade_mask).sum()
win_rate     = win_trades / total_trades if total_trades > 0 else 0

n_years      = (df.index[-1] - df.index[0]).days / 365.25

strat_total  = df["Strategy_Equity"].iloc[-1] - 1
market_total = df["Market_Equity"].iloc[-1]   - 1
strat_cagr   = (df["Strategy_Equity"].iloc[-1] ** (1 / max(n_years, 1))) - 1
market_cagr  = (df["Market_Equity"].iloc[-1]   ** (1 / max(n_years, 1))) - 1
strat_sharpe = sharpe(df["Strategy_Return"])
market_sharpe= sharpe(df["Market_Return"])
strat_mdd    = max_drawdown(df["Strategy_Equity"])
market_mdd   = max_drawdown(df["Market_Equity"])

print("\n╔══════════════════════════════════════════════════════╗")
print("║           STEP-8B  BACKTEST  RESULTS                ║")
print("╠══════════════════════════════════════════════════════╣")
print(f"║  Period          : {df.index[0].date()} → {df.index[-1].date()}")
print(f"║  Total Trades    : {total_trades}")
print(f"║  Win Rate        : {win_rate:.2%}")
print(f"║  Strategy Return : {strat_total:+.2%}   (CAGR {strat_cagr:+.2%})")
print(f"║  Market Return   : {market_total:+.2%}   (CAGR {market_cagr:+.2%})")
print(f"║  Strategy Sharpe : {strat_sharpe:.2f}")
print(f"║  Market Sharpe   : {market_sharpe:.2f}")
print(f"║  Strategy MaxDD  : {strat_mdd:.2%}")
print(f"║  Market MaxDD    : {market_mdd:.2%}")
print("╚══════════════════════════════════════════════════════╝")

df.to_csv(f"{DATA_DIR}/backtest_results.csv")
print(f"✅ STEP-8B SUCCESS: results saved → {DATA_DIR}/backtest_results.csv")