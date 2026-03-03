"""Quick smoke-test for the ML pipeline (run from backend/)."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "audithawk_core.settings")

import django
django.setup()

import pandas as pd
from api.ml_engine.feature_engineering import build_features
from api.ml_engine.models_lof import run_lof
from api.ml_engine.ensemble import run_pipeline

records = [
    {"transaction_id": "T1",  "date": "2026-02-01T09:30:00", "amount": 250.50,   "merchant": "Amazon",           "category": "Shopping",    "account_id": "A1"},
    {"transaction_id": "T2",  "date": "2026-02-01T10:15:00", "amount": 1500.00,   "merchant": "Dell",             "category": "Electronics", "account_id": "A2"},
    {"transaction_id": "T3",  "date": "2026-02-01T14:22:00", "amount": 85.75,     "merchant": "Starbucks",        "category": "Food",        "account_id": "A1"},
    {"transaction_id": "T4",  "date": "2026-02-01T23:45:00", "amount": 15000.00,  "merchant": "Midnight Wire Co", "category": "Wire",        "account_id": "A3"},
    {"transaction_id": "T5",  "date": "2026-02-02T08:10:00", "amount": 450.00,    "merchant": "Office Depot",     "category": "Office",      "account_id": "A2"},
    {"transaction_id": "T6",  "date": "2026-02-02T11:30:00", "amount": 75000.00,  "merchant": "Suspicious LLC",   "category": "Unknown",     "account_id": "A4"},
    {"transaction_id": "T7",  "date": "2026-02-02T15:20:00", "amount": 125.00,    "merchant": "Walmart",          "category": "Groceries",   "account_id": "A1"},
    {"transaction_id": "T8",  "date": "2026-02-02T16:45:00", "amount": 3200.00,   "merchant": "Apple Store",      "category": "Electronics", "account_id": "A2"},
    {"transaction_id": "T9",  "date": "2026-02-03T02:15:00", "amount": 8500.50,   "merchant": "Offshore Inc",     "category": "Wire",        "account_id": "A3"},
    {"transaction_id": "T10", "date": "2026-02-03T12:00:00", "amount": 95.25,     "merchant": "Target",           "category": "Retail",      "account_id": "A1"},
]

print("=" * 60)
print("TEST 1: Feature Engineering")
print("=" * 60)
df = build_features(pd.DataFrame(records))
print("Columns:", list(df.columns))
print(df[["merchant", "velocity", "pattern", "rarity", "magnitude"]].to_string(index=False))

print("\n" + "=" * 60)
print("TEST 2: LOF Scoring (Amazon masked as trusted)")
print("=" * 60)
scores = run_lof(df, trusted_vendors=["Amazon"])
for i, s in enumerate(scores):
    merchant = records[i]["merchant"]
    print(f"  {merchant:25s}  lof_score = {s:.4f}")

print("\n" + "=" * 60)
print("TEST 3: Full Ensemble Pipeline")
print("=" * 60)
flagged = run_pipeline(records, "test-report-123", trusted_vendors=["Amazon"])
print(f"Flagged {len(flagged)} anomalies out of {len(records)} transactions:")
for f in flagged:
    print(f"  {f['transaction_id']}  risk={f['risk_score']:.4f}")
    print(f"    Explanation: {f['explanation'][:120]}...")

print("\n*** ALL TESTS PASSED ***")
