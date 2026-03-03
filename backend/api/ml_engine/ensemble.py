"""
Ensemble Orchestrator  (Phase 3 ✓ – all models active)
───────────────────────────────────────────────────────
Master pipeline that is triggered by the GraphQL ``analyzeReport`` mutation.

Flow
----
1. Build 4-pillar features from the raw transaction DataFrame.
2. Run LOF   → lof_score   (Phase 1 ✓)
3. Run AE    → ae_score    (Phase 2 ✓)
4. Run Graph → graph_score (Phase 3 ✓)
5. Aggregate into ``total_risk_index`` via weighted sum.
6. Mask trusted vendors   → risk = 0.
7. Threshold to top-1%   → anomalies.
8. Generate human-readable explanations.
9. Return list[dict] ready for MongoDB insertion.

Weights
-------
W_LOF = 0.6, W_AE = 0.2, W_GRAPH = 0.2  (all three models active).
"""

from __future__ import annotations

import pandas as pd
import numpy as np
from typing import Any

from .feature_engineering import build_features
from .models_lof import run_lof
from .models_autoencoder import run_autoencoder
from .models_graph import run_graph_analysis
from .narrator import generate_explanations


# ── Tunable ensemble weights ────────────────────────────
W_LOF = 0.6
W_AE = 0.2       # effectively 0 until Phase 2 (stub returns 0)
W_GRAPH = 0.2    # effectively 0 until Phase 3 (stub returns 0)

# Top percentile to flag
TOP_PERCENTILE = 0.01   # top 1%


def run_pipeline(
    raw_records: list[dict[str, Any]],
    report_id: str,
    trusted_vendors: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    End-to-end unsupervised fraud-detection pipeline.

    Parameters
    ----------
    raw_records : list[dict]
        Transaction dicts as stored in MongoDB (must have at minimum:
        transaction_id, date, amount, merchant, account_id).
    report_id : str
        Mongo ObjectId string of the parent audit report.
    trusted_vendors : list[str] | None
        HITL whitelist loaded from MongoDB.

    Returns
    -------
    list[dict]
        Flagged anomalies ready for insertion into
        ``flagged_transactions_col``.  Each dict contains:
            report_id, transaction_id, amount, risk_score,
            decision, explanation
    """
    if not raw_records:
        return []

    df = pd.DataFrame(raw_records)

    # ── 1. Feature Engineering ──────────────────────────
    df = build_features(df)

    # ── 2. Model scores ─────────────────────────────────
    df["lof_score"] = run_lof(df, trusted_vendors=trusted_vendors)
    df["ae_score"] = run_autoencoder(df)
    df["graph_score"] = run_graph_analysis(df)

    # ── 3. Weighted aggregation ─────────────────────────
    df["total_risk_index"] = (
        W_LOF * df["lof_score"]
        + W_AE * df["ae_score"]
        + W_GRAPH * df["graph_score"]
    )

    # ── 4. HITL Masking (belt-and-suspenders) ───────────
    if trusted_vendors:
        trusted_set = {v.strip().lower() for v in trusted_vendors}
        mask = df["merchant"].str.strip().str.lower().isin(trusted_set)
        df.loc[mask, "total_risk_index"] = 0.0

    # ── 5. Threshold: keep only top 1 % ────────────────
    if len(df) < 5:
        # Tiny dataset: flag anything above 0
        threshold = 0.01
    else:
        threshold = df["total_risk_index"].quantile(1 - TOP_PERCENTILE)
    anomalies = df[df["total_risk_index"] > threshold].copy()

    if anomalies.empty:
        return []

    # ── 6. Explanations ─────────────────────────────────
    explanations = generate_explanations(anomalies)
    anomalies["explanation"] = explanations

    # ── 7. Build output dicts ───────────────────────────
    results: list[dict[str, Any]] = []
    for _, row in anomalies.iterrows():
        results.append({
            "report_id": report_id,
            "transaction_id": row.get("transaction_id", ""),
            "amount": float(row.get("amount", 0)),
            "risk_score": round(float(row["total_risk_index"]), 4),
            "decision": "review_required",
            "explanation": row["explanation"],
        })

    return results
