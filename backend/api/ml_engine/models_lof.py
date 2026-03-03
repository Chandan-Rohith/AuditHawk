"""
Local Outlier Factor + HITL Active Learning (Masking)
─────────────────────────────────────────────────────
Uses sklearn.neighbors.LocalOutlierFactor to find local density anomalies.

After scoring, any transaction whose merchant appears in the MongoDB
trusted-vendors list has its anomaly score **masked to 0**.  The whitelist
is never used to train a classifier – only to post-filter.

Returns
-------
pd.Series  – non-negative anomaly scores (higher = more anomalous).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.neighbors import LocalOutlierFactor


# Feature columns produced by feature_engineering.build_features()
FEATURE_COLS = ["velocity", "pattern", "rarity", "magnitude"]


def run_lof(
    df: pd.DataFrame,
    trusted_vendors: list[str] | None = None,
    n_neighbors: int = 20,
    contamination: float = 0.05,
) -> pd.Series:
    """
    Run LOF on the engineered features and return an anomaly score series.

    Parameters
    ----------
    df : DataFrame
        Must contain the four feature columns.
    trusted_vendors : list[str], optional
        Vendor names whose scores will be masked to 0 (HITL whitelist).
    n_neighbors : int
        LOF neighbour count – auto-capped to len(df)-1 when the dataset
        is small.
    contamination : float
        Expected proportion of outliers (only affects the internal
        threshold; we use the raw negative_outlier_factor_ for scoring).

    Returns
    -------
    pd.Series of float – anomaly score per row (0 = normal, higher = worse).
    """
    X = df[FEATURE_COLS].values

    # Adapt n_neighbors when dataset is tiny
    effective_neighbours = min(n_neighbors, max(2, len(X) - 1))

    lof = LocalOutlierFactor(
        n_neighbors=effective_neighbours,
        contamination=contamination,
        novelty=False,
    )
    lof.fit_predict(X)

    # negative_outlier_factor_ is negative (closer to -1 = normal).
    # Flip & shift so 0 = perfectly normal, higher = worse.
    raw_scores = -lof.negative_outlier_factor_          # positive, ≥ 1 for normal
    shifted = np.maximum(raw_scores - 1.0, 0.0)        # 0 for normal points

    # Normalise to [0, 1]
    score_max = shifted.max() or 1.0
    scores = shifted / score_max

    scores = pd.Series(scores, index=df.index, name="lof_score")

    # ── HITL Active Learning: Mask trusted vendors ──────
    if trusted_vendors:
        trusted_set = {v.strip().lower() for v in trusted_vendors}
        mask = df["merchant"].str.strip().str.lower().isin(trusted_set)
        scores.loc[mask] = 0.0

    return scores
