"""
Feature Engineering – The 4 Pillars
────────────────────────────────────
Transforms a raw Pandas DataFrame (date, merchant/vendor, amount, account_id)
into four mathematical risk-feature columns that feed every downstream model.

Columns produced:
  velocity   – 7-day rolling sum of amounts per vendor   (Smurfing)
  pattern    – exponential decay since last txn + weekend flag (Ghost Activity)
  rarity     – vendor frequency × log²(amount)            (Material Shell)
  magnitude  – log²(amount / global_max)                  (Fat Finger)
"""

from __future__ import annotations

import numpy as np
import pandas as pd


# ── helpers ──────────────────────────────────────────────

def _safe_log2(x: pd.Series) -> pd.Series:
    """log₂ that clamps values ≥ 1 to avoid -inf / NaN."""
    return np.log2(x.clip(lower=1.0))


# ── public API ───────────────────────────────────────────

def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Accepts a DataFrame with at least:
        date (str/datetime), merchant (str), amount (float), account_id (str)
    Returns the same DataFrame with four new float columns:
        velocity, pattern, rarity, magnitude
    """
    df = df.copy()

    # ── normalise types ──
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0.0)
    df.sort_values("date", inplace=True)
    df.reset_index(drop=True, inplace=True)

    # ── 1. Velocity (Smurfing) ───────────────────────────
    # 7-day rolling sum of amounts per vendor
    df["velocity"] = (
        df.set_index("date")
          .groupby("merchant")["amount"]
          .transform(lambda s: s.rolling("7D", min_periods=1).sum())
          .values
    )

    # ── 2. Pattern (Ghost Activity) ──────────────────────
    # Exponential decay based on hours since last txn + weekend probability
    df["hours_since_last"] = (
        df.groupby("merchant")["date"]
          .diff()
          .dt.total_seconds()
          .div(3600)
          .fillna(0)
    )
    decay_rate = 0.1  # λ for exp(-λ·h)
    df["time_decay"] = np.exp(-decay_rate * df["hours_since_last"])
    df["is_weekend"] = df["date"].dt.dayofweek.isin([5, 6]).astype(float)
    df["pattern"] = df["time_decay"] + df["is_weekend"]  # higher = more suspicious

    # ── 3. Rarity (Material Shell) ───────────────────────
    # How unusual is this vendor × how big is the amount?
    vendor_freq = df["merchant"].map(df["merchant"].value_counts(normalize=True))
    df["rarity"] = (1 - vendor_freq) * (_safe_log2(df["amount"]) ** 2)

    # ── 4. Magnitude (Fat Finger) ────────────────────────
    global_max = df["amount"].max() or 1.0
    df["magnitude"] = (_safe_log2(df["amount"] / global_max + 1)) ** 2

    # ── clean up temp cols ───────────────────────────────
    df.drop(columns=["hours_since_last", "time_decay", "is_weekend"], inplace=True)

    # ── normalise features to [0, 1] ────────────────────
    for col in ("velocity", "pattern", "rarity", "magnitude"):
        col_min = df[col].min()
        col_max = df[col].max()
        if col_max - col_min > 0:
            df[col] = (df[col] - col_min) / (col_max - col_min)
        else:
            df[col] = 0.0

    return df
