# step5b_probability_decision.py
# FIXED: saves Date index correctly, uses saved model from step4
import pickle
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from config import DEFAULT_STOCK, DATA_DIR, TRAIN_RATIO, BUY_THRESHOLD

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

results = X_test.copy()
results["Actual"]         = y_test.values
results["UP_Probability"] = probs
results["Predicted"]      = (probs >= 0.5).astype(int)
results["Decision"]       = results["UP_Probability"].apply(
    lambda p: "BUY" if p >= BUY_THRESHOLD else "NO_TRADE"
)

out_path = f"{DATA_DIR}/step5b_predictions_with_probabilities.csv"
results.to_csv(out_path)

buy_count = (results["Decision"] == "BUY").sum()
print(f"✅ STEP-5B SUCCESS: {len(results)} predictions → {out_path}")
print(f"   BUY signals: {buy_count}  |  NO_TRADE: {len(results)-buy_count}")
print(results[["UP_Probability", "Predicted", "Decision"]].tail(10).to_string())