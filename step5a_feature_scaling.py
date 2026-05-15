# step5a_feature_scaling.py
# FIXED: scaler.fit() ONLY on X_train — never on test data
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from config import DEFAULT_STOCK, DATA_DIR, TRAIN_RATIO

symbol_safe = DEFAULT_STOCK.replace(".", "_")
df = pd.read_csv(f"{DATA_DIR}/{symbol_safe}_ml_dataset.csv", index_col=0, parse_dates=True)

DROP_COLS = ["Target", "Open", "High", "Low", "Close", "Volume"]
X = df.drop(columns=[c for c in DROP_COLS if c in df.columns])
y = df["Target"]

split     = int(len(df) * TRAIN_RATIO)
X_train   = X.iloc[:split];  X_test  = X.iloc[split:]
y_train   = y.iloc[:split];  y_test  = y.iloc[split:]

# ── FIT scaler on train only ───────────────────────────────────────────────────
scaler       = StandardScaler()
X_train_s    = scaler.fit_transform(X_train)   # fit + transform
X_test_s     = scaler.transform(X_test)        # transform only (no fit!)

lr = LogisticRegression(max_iter=1000, C=0.1)
lr.fit(X_train_s, y_train)
preds = lr.predict(X_test_s)

print(f"✅ STEP-5A: Scaled Logistic Regression Accuracy: {accuracy_score(y_test, preds):.4f}")
print(classification_report(y_test, preds, digits=3))