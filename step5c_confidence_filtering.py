# step5c_confidence_filtering.py
# FIXED: accuracy computed against Actual, not against the threshold label itself
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from config import DEFAULT_STOCK, DATA_DIR, TRAIN_RATIO, CONFIDENCE_LEVELS

symbol_safe = DEFAULT_STOCK.replace(".", "_")
df = pd.read_csv(f"{DATA_DIR}/{symbol_safe}_ml_dataset.csv", index_col=0, parse_dates=True)

DROP_COLS = ["Target", "Open", "High", "Low", "Close", "Volume"]
X = df.drop(columns=[c for c in DROP_COLS if c in df.columns])
y = df["Target"]

split   = int(len(df) * TRAIN_RATIO)
X_train = X.iloc[:split]; X_test = X.iloc[split:]
y_train = y.iloc[:split]; y_test = y.iloc[split:]

scaler      = StandardScaler()
X_train_s   = scaler.fit_transform(X_train)
X_test_s    = scaler.transform(X_test)

model = LogisticRegression(max_iter=1000, C=0.1)
model.fit(X_train_s, y_train)
probs = model.predict_proba(X_test_s)[:, 1]

results = pd.DataFrame({
    "Actual":         y_test.values,
    "UP_Probability": probs,
}, index=y_test.index)

print("\n╔══ CONFIDENCE FILTERING RESULTS ═════════════════════╗")
for t in CONFIDENCE_LEVELS:
    filtered = results[results["UP_Probability"] >= t].copy()
    if len(filtered) == 0:
        print(f"  Threshold {t:.2f} → no trades taken")
        continue
    # Predict BUY (1) for every row that passed the threshold
    preds_t = pd.Series(1, index=filtered.index)
    acc     = accuracy_score(filtered["Actual"], preds_t)
    print(f"  Threshold {t:.2f} → trades: {len(filtered):>4d}  "
          f"| precision on BUY: {acc:.3f}  "
          f"| coverage: {len(filtered)/len(results):.1%}")
print("╚══════════════════════════════════════════════════════╝")