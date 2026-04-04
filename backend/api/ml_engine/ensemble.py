"""
Ensemble Orchestrator  (Phase 1 Final)
───────────────────────────────────────────────────────
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

# 🚨 Reverted back to the hardcoded enterprise threshold
ROBUST_Z_SCORE_THRESHOLD = 3.0
MAD_FALLBACK_EPSILON = 1e-6

def run_pipeline(
    raw_records: list[dict[str, Any]],
    report_id: str,
    trusted_vendors: list[str] | None = None,
    amount_threshold: float | None = None,
) -> list[dict[str, Any]]:
    
    if not raw_records:
        return []

    df = pd.DataFrame(raw_records)
    df = build_features(df)

    df_for_scoring = df.copy()
    if trusted_vendors:
        trusted_set = {v.strip().lower() for v in trusted_vendors}
        trusted_mask = df_for_scoring["merchant"].str.strip().str.lower().isin(trusted_set)
        df_for_scoring.loc[trusted_mask, "magnitude"] = 0.0
        df_for_scoring.loc[trusted_mask, "rarity"] = 0.0

    df["lof_score"] = run_lof(df)
    df["ae_score"] = run_autoencoder(df)
    df["graph_score"] = run_graph_analysis(df)

    if trusted_vendors:
        for col in ["lof_score", "ae_score", "graph_score"]:
            col_max = df[col].max()
            if col_max > 0:
                df[col] = df[col] / col_max

    df["total_risk_index"] = pd.concat([
        df["lof_score"], df["ae_score"], df["graph_score"], 
        df_for_scoring["velocity"], df_for_scoring["rarity"] 
    ], axis=1).max(axis=1)
    
    if trusted_vendors:
        trusted_set = {v.strip().lower() for v in trusted_vendors}
        trusted_mask = df["merchant"].str.strip().str.lower().isin(trusted_set)
        df.loc[trusted_mask, "total_risk_index"] = df.loc[trusted_mask, ["velocity", "pattern"]].max(axis=1)
    
    vendor_counts = df.groupby("merchant")["amount"].transform("count")
    vendor_means = df.groupby("merchant")["amount"].transform("mean")
    salami_mask = (vendor_counts > 50) & (vendor_means < 5.0)

    clean_scores = df.loc[~salami_mask, "total_risk_index"]
    if len(clean_scores) == 0:
        risk_median = 0.0
        mad = MAD_FALLBACK_EPSILON
    else:
        risk_median = float(clean_scores.median())
        mad = float((clean_scores - risk_median).abs().median())
        if mad == 0:
            mad = MAD_FALLBACK_EPSILON

    df["robust_z_score"] = 0.6745 * (df["total_risk_index"] - risk_median) / mad
    anomalies = df[(df["robust_z_score"] > ROBUST_Z_SCORE_THRESHOLD) | salami_mask].copy()
    
    explanations = generate_explanations(anomalies)
    anomalies["explanation"] = explanations

    if amount_threshold is not None and amount_threshold > 0:
        threshold_note = f"Amount exceeds user threshold ({float(amount_threshold):.2f})."
        high_amount_mask = anomalies["amount"].astype(float) > float(amount_threshold)
        anomalies.loc[high_amount_mask, "explanation"] = anomalies.loc[
            high_amount_mask, "explanation"
        ].apply(lambda text: f"{threshold_note} {text}".strip())

    results: list[dict[str, Any]] = []
    # 🚨 Reverted output map (removed robust_z_score and is_salami)
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