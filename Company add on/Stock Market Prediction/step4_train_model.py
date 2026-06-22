# step4_train_model.py
# FIXED: proper time-based split (no data leakage), added XGBoost,
#        feature importance printed, models saved for reuse
import os
import pickle
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score

try:
    from xgboost import XGBClassifier
    USE_XGB = True
except ImportError:
    USE_XGB = False
    print("⚠  xgboost not installed — skipping XGB model")

from config import DEFAULT_STOCK, DATA_DIR, TRAIN_RATIO

symbol_safe = DEFAULT_STOCK.replace(".", "_")
df = pd.read_csv(f"{DATA_DIR}/{symbol_safe}_ml_dataset.csv", index_col=0, parse_dates=True)

# ── Features / target ─────────────────────────────────────────────────────────
# Drop non-numeric / raw price columns that would leak future info
DROP_COLS = ["Target", "Open", "High", "Low", "Close", "Volume"]
X = df.drop(columns=[c for c in DROP_COLS if c in df.columns])
y = df["Target"]

# ── Time-based train/test split ───────────────────────────────────────────────
split = int(len(df) * TRAIN_RATIO)
X_train, X_test = X.iloc[:split], X.iloc[split:]
y_train, y_test = y.iloc[:split], y.iloc[split:]
print(f"Train: {X_train.shape}  |  Test: {X_test.shape}")

# ── Scaling (fit on train only!) ──────────────────────────────────────────────
scaler = StandardScaler()
X_train_s = scaler.fit_transform(X_train)
X_test_s  = scaler.transform(X_test)

# ── Models ─────────────────────────────────────────────────────────────────────
models = {
    "Logistic Regression": LogisticRegression(max_iter=1000, C=0.1),
    "Random Forest":       RandomForestClassifier(n_estimators=300, max_depth=6,
                                                   min_samples_leaf=10, random_state=42),
    "Gradient Boosting":   GradientBoostingClassifier(n_estimators=200, max_depth=4,
                                                       learning_rate=0.05, random_state=42),
}
if USE_XGB:
    models["XGBoost"] = XGBClassifier(n_estimators=300, max_depth=4, learning_rate=0.05,
                                       use_label_encoder=False, eval_metric="logloss",
                                       random_state=42)

best_auc   = 0
best_name  = ""
best_model = None

for name, model in models.items():
    # Logistic Regression needs scaled features; tree models work on raw too
    Xtr = X_train_s if name == "Logistic Regression" else X_train.values
    Xte = X_test_s  if name == "Logistic Regression" else X_test.values
    model.fit(Xtr, y_train)
    preds = model.predict(Xte)
    proba = model.predict_proba(Xte)[:, 1]
    acc   = accuracy_score(y_test, preds)
    auc   = roc_auc_score(y_test, proba)
    print(f"\n── {name} ──")
    print(f"   Accuracy : {acc:.4f}   AUC-ROC : {auc:.4f}")
    print(classification_report(y_test, preds, digits=3))
    if auc > best_auc:
        best_auc, best_name, best_model = auc, name, model

print(f"\n🏆 Best model: {best_name}  (AUC {best_auc:.4f})")

# ── Save best model + scaler ───────────────────────────────────────────────────
os.makedirs(DATA_DIR, exist_ok=True)
with open(f"{DATA_DIR}/{symbol_safe}_model.pkl",  "wb") as f: pickle.dump(best_model, f)
with open(f"{DATA_DIR}/{symbol_safe}_scaler.pkl", "wb") as f: pickle.dump(scaler,     f)
with open(f"{DATA_DIR}/{symbol_safe}_features.pkl","wb") as f: pickle.dump(list(X.columns), f)

print(f"✅ STEP-4 SUCCESS: model & scaler saved to {DATA_DIR}/")

# ── Feature importance (tree models) ──────────────────────────────────────────
if hasattr(best_model, "feature_importances_"):
    imp = pd.Series(best_model.feature_importances_, index=X.columns)
    print("\nTop-10 features:")
    print(imp.nlargest(10).to_string())