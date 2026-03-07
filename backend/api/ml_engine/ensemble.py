"""
Ensemble Orchestrator  (Phase 3 ✓ – all models active)
───────────────────────────────────────────────────────
Master pipeline that is triggered by the GraphQL ``analyzeReport`` mutation.

Flow
----
1. Build 4-pillar features from the raw transaction DataFrame.
2. For trusted vendors, dampen only magnitude/rarity features.
2. Run LOF   → lof_score   (Phase 1 ✓)
3. Run AE    → ae_score    (Phase 2 ✓)
4. Run Graph → graph_score (Phase 3 ✓)
5. Aggregate into ``total_risk_index`` via weighted sum.
6. Threshold with robust z-score (median + MAD) → anomalies.
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
# W_LOF = 0.6    <-- DELETE OR COMMENT OUT
# W_AE = 0.2     <-- DELETE OR COMMENT OUT
# W_GRAPH = 0.2  <-- DELETE OR COMMENT OUT

ROBUST_Z_SCORE_THRESHOLD = 3.5
MAD_FALLBACK_EPSILON = 1e-6


def run_pipeline(
    raw_records: list[dict[str, Any]],
    report_id: str,
    trusted_vendors: list[str] | None = None,
    amount_threshold: float | None = None,
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
    amount_threshold : float | None
        Optional user-defined amount threshold. Any transaction with
        amount above this value is included in anomalies.

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

    """# ── 1. Feature Engineering ──────────────────────────
    df = build_features(df)

    # ── 2. Trusted-vendor feature dampening ─────────────
    # Security fix: do NOT zero out final risk for trusted vendors.
    # Only dampen Magnitude + Rarity while preserving Pattern + Velocity.
    df_for_scoring = df.copy()
    if trusted_vendors:
        trusted_set = {v.strip().lower() for v in trusted_vendors}
        trusted_mask = df_for_scoring["merchant"].str.strip().str.lower().isin(trusted_set)
        df_for_scoring.loc[trusted_mask, "magnitude"] = 0.0
        df_for_scoring.loc[trusted_mask, "rarity"] = 0.0

        for col in ["lof_score", "ae_score", "graph_score"]:
            col_max = df[col].max()
            if col_max > 0:
                df[col] = df[col] / col_max

    # ── 3. Model scores (Run on RAW data) ───────────────────────
    df["lof_score"] = run_lof(df)
    df["ae_score"] = run_autoencoder(df)
    df["graph_score"] = run_graph_analysis(df)

    # ── 4. Max-Pooling (Raw Scores) ─────────────────────────
    df["total_risk_index"] = df["total_risk_index"] = pd.concat([df["lof_score"], df["ae_score"], df["graph_score"], df_for_scoring["velocity"], df_for_scoring["rarity"] ], axis=1).max(axis=1)
    if trusted_vendors:
        trusted_set = {v.strip().lower() for v in trusted_vendors}
        trusted_mask = df["merchant"].str.strip().str.lower().isin(trusted_set)
        
        # If trusted, completely ignore LOF, AE, Graph, and Rarity.
        # ONLY flag them if they violate Velocity (Smurfs) or Pattern (3 AM hacks).
        df.loc[trusted_mask, "total_risk_index"] = df.loc[trusted_mask, ["velocity", "pattern"]].max(axis=1)
    
    # ── 5. Robust Thresholding (The Dynamic Failsafe) ──────
    risk_scores = df["total_risk_index"]
    risk_median = float(risk_scores.median())
    mad = float((risk_scores - risk_median).abs().median())
    if mad == 0:
        mad = MAD_FALLBACK_EPSILON

    df["robust_z_score"] = 0.6745 * (risk_scores - risk_median) / mad
    
    # Now it dynamically adapts to ANY dataset shape!
    anomalies = df[df["robust_z_score"] > 3.0].copy()"""

    # ── 1. Feature Engineering ──────────────────────────
    df = build_features(df)

    # ── 2. Run Models (UNBOUNDED) ───────────────────────
    df["lof_score"] = run_lof(df)
    df["ae_score"] = run_autoencoder(df)
    df["graph_score"] = run_graph_analysis(df)

    # ── 3. Model scores (UNBOUNDED) ──────────────────────────────
    df["lof_score"] = run_lof(df)
    df["ae_score"] = run_autoencoder(df)
    df["graph_score"] = run_graph_analysis(df)

   # ── 4. Independent Decision Matrix ───────────────────────────
    is_lof_anomaly = df["lof_score"] > 4.0     
    is_ae_anomaly = df["ae_score"] > 3.0       
    is_smurf = df["velocity"] > 0.8            

    is_graph_anomaly = (df["graph_score"] > 0.8) & ((df["rarity"] > 0.5) | (df["magnitude"] > 0.5))

    # Catches low-dollar account takeovers. If the behavior is slightly weird (AE > 1.5) 
    # AND the vendor is highly unusual (Rarity > 0.8), flag it immediately.
    is_ato_anomaly = (df["ae_score"] > 1.8) & ((df["pattern"] > 0.8) | (df["rarity"] > 0.85))
    # Base anomaly condition: ANY model caught something severe
    df["is_anomaly"] = is_lof_anomaly | is_ae_anomaly | is_graph_anomaly | is_smurf | is_ato_anomaly


    # ── 5. Enterprise Whitelist Veto ─────────────────────────────
    if trusted_vendors:
        trusted_set = {v.strip().lower() for v in trusted_vendors}
        trusted_mask = df["merchant"].str.strip().str.lower().isin(trusted_set)
        
        # Silence the AI panic for trusted vendors
        df.loc[trusted_mask, "is_anomaly"] = False
        
        # Re-flag ONLY if they broke the hard behavioral rules (The Azure Hack)
        hacked_mask = trusted_mask & is_smurf
        df.loc[hacked_mask, "is_anomaly"] = True

    # ── 6. Formatting for the UI ─────────────────────────────────
    df["total_risk_index"] = df[["lof_score", "ae_score"]].max(axis=1)
    df.loc[df["is_anomaly"], "total_risk_index"] = 99.0 # Force anomalies to the top
    
    if trusted_vendors:
        df.loc[trusted_mask & ~hacked_mask, "total_risk_index"] = 0.0

    # Only return the rows that tripped the matrix
    anomalies = df[df["is_anomaly"]].copy()
    
    # ── 6. Explanations ─────────────────────────────────
    explanations = generate_explanations(anomalies)
    anomalies["explanation"] = explanations

    if amount_threshold is not None and amount_threshold > 0:
        threshold_note = f"Amount exceeds user threshold ({float(amount_threshold):.2f})."
        high_amount_mask = anomalies["amount"].astype(float) > float(amount_threshold)
        anomalies.loc[high_amount_mask, "explanation"] = anomalies.loc[
            high_amount_mask, "explanation"
        ].apply(lambda text: f"{threshold_note} {text}".strip())

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
