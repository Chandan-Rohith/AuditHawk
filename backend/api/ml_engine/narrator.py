"""
Narrator – Human-Readable Explanations  (Phase 3 ✓)
───────────────────────────────────────────────────────────
Will call an LLM (e.g. Gemini) to produce plain-English explanations
of *why* each flagged transaction was considered anomalous.

For Phase 1 we generate rule-based explanations from the feature
scores so the pipeline is already end-to-end functional.
"""

from __future__ import annotations

import pandas as pd


def generate_explanations(anomalies: pd.DataFrame) -> list[str]:
    """
    Given a DataFrame of anomalous rows (with score columns), return a
    list of human-readable explanation strings, one per row.

    Phase 1 uses heuristic templates.  Phase 2+ will integrate Gemini.
    """
    explanations: list[str] = []

    for _, row in anomalies.iterrows():
        parts: list[str] = []

        # Velocity
        vel = row.get("velocity", 0.0)
        if vel > 0.7:
            parts.append(
                f"High transaction velocity (score {vel:.2f}): "
                "rapid repeated payments to this vendor within 7 days, "
                "consistent with smurfing/structuring."
            )

        # Pattern
        pat = row.get("pattern", 0.0)
        if pat > 0.7:
            parts.append(
                f"Unusual temporal pattern (score {pat:.2f}): "
                "activity outside normal business hours or on weekends."
            )

        # Rarity
        rar = row.get("rarity", 0.0)
        if rar > 0.7:
            parts.append(
                f"Rare vendor/amount combination (score {rar:.2f}): "
                "this merchant is seldom seen and the amount is disproportionately large."
            )

        # Magnitude
        mag = row.get("magnitude", 0.0)
        if mag > 0.7:
            parts.append(
                f"Abnormal magnitude (score {mag:.2f}): "
                "the transaction amount is an extreme outlier relative to the dataset."
            )

        # LOF
        lof = row.get("lof_score", 0.0)
        if lof > 0.5:
            parts.append(
                f"Local density anomaly (LOF score {lof:.2f}): "
                "this transaction's feature profile is unlike its nearest neighbours."
            )

        # Autoencoder (Phase 2)
        ae = row.get("ae_score", 0.0)
        if ae > 0.5:
            parts.append(
                f"Autoencoder reconstruction anomaly (AE score {ae:.2f}): "
                "this transaction's behavioural profile deviates significantly "
                "from the learned normal patterns."
            )

        # Graph (Phase 3)
        graph = row.get("graph_score", 0.0)
        if graph > 0.5:
            parts.append(
                f"Graph topology anomaly (graph score {graph:.2f}): "
                "this transaction involves nodes with unusual connectivity, "
                "low PageRank, or bridges separate graph communities."
            )

        if not parts:
            parts.append(
                "Composite risk index exceeded the top-1% threshold "
                "across multiple weak signals."
            )

        explanation = " | ".join(parts)
        explanations.append(explanation)

    return explanations
