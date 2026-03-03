"""
Unsupervised Graph Network  (Phase 3 ✓)
───────────────────────────────────────
Builds a bipartite transaction graph:

    [Account] ──(PAID)──▶ [Merchant]

Each edge carries the transaction amount as weight.

Graph-derived anomaly signals
─────────────────────────────
1. **Degree centrality** – accounts/merchants that transact with very
   few counterparties are "isolated" and harder to cross-validate.
2. **Weighted PageRank** – high-PageRank merchants that attract funds
   from many accounts are normal; low-PR merchants receiving a single
   large transfer look suspicious.
3. **Community isolation (Louvain)** – transactions that bridge two
   different communities score higher (inter-community edges are
   unusual in normal commerce flows).
4. **Edge-weight outlier** – for each merchant, flag edges whose
   amount is > 2σ above that merchant's mean edge weight.

Final per-row graph_score = mean of the four normalised sub-scores,
re-normalised to [0, 1].

Dependencies:  networkx, python-louvain (community)
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import networkx as nx

try:
    import community as community_louvain  # python-louvain
except ImportError:  # pragma: no cover
    community_louvain = None  # type: ignore[assignment]


# ── Helpers ──────────────────────────────────────────────

def _normalise(arr: np.ndarray) -> np.ndarray:
    """Min-max normalise to [0, 1]. Returns zeros if constant."""
    mn, mx = arr.min(), arr.max()
    if mx - mn < 1e-9:
        return np.zeros_like(arr, dtype=np.float64)
    return (arr - mn) / (mx - mn)


def _build_graph(df: pd.DataFrame) -> nx.Graph:
    """
    Build an undirected weighted bipartite graph.
    Nodes are prefixed to avoid collisions:
        account nodes  → "acc:<account_id>"
        merchant nodes → "mer:<merchant>"
    Edge weight = transaction amount.
    """
    G = nx.Graph()
    for _, row in df.iterrows():
        acc_node = f"acc:{row['account_id']}"
        mer_node = f"mer:{row['merchant']}"
        amt = float(row.get("amount", 0))
        # If edge already exists, sum the weights (multi-edge proxy)
        if G.has_edge(acc_node, mer_node):
            G[acc_node][mer_node]["weight"] += amt
        else:
            G.add_edge(acc_node, mer_node, weight=amt)
    return G


# ── Sub-scores ───────────────────────────────────────────

def _degree_score(G: nx.Graph, df: pd.DataFrame) -> np.ndarray:
    """
    Low degree centrality → more isolated → higher anomaly score.
    We invert: score = 1 - normalised_degree.
    """
    dc = nx.degree_centrality(G)
    raw = np.array([
        (dc.get(f"acc:{row['account_id']}", 0) +
         dc.get(f"mer:{row['merchant']}", 0)) / 2
        for _, row in df.iterrows()
    ])
    normed = _normalise(raw)
    return 1.0 - normed  # invert: low centrality = high score


def _pagerank_score(G: nx.Graph, df: pd.DataFrame) -> np.ndarray:
    """
    Low merchant PageRank + high amount → anomalous.
    Score per row = (1 - normalised_merchant_PR) * normalised_amount.
    """
    pr = nx.pagerank(G, weight="weight")
    mer_pr = np.array([
        pr.get(f"mer:{row['merchant']}", 0) for _, row in df.iterrows()
    ])
    amounts = df["amount"].values.astype(np.float64)
    normed_pr = _normalise(mer_pr)
    normed_amt = _normalise(amounts)
    return (1.0 - normed_pr) * normed_amt


def _community_score(G: nx.Graph, df: pd.DataFrame) -> np.ndarray:
    """
    Louvain community detection. Transactions whose account and
    merchant live in *different* communities get score = 1; same
    community → 0.
    """
    if community_louvain is None:
        return np.zeros(len(df))

    partition = community_louvain.best_partition(G, weight="weight",
                                                  random_state=42)
    scores = np.array([
        0.0 if partition.get(f"acc:{row['account_id']}", -1)
              == partition.get(f"mer:{row['merchant']}", -2)
        else 1.0
        for _, row in df.iterrows()
    ])
    return scores


def _edge_weight_outlier(G: nx.Graph, df: pd.DataFrame) -> np.ndarray:
    """
    For each merchant, compute mean and std of incoming edge weights.
    Transactions > 2σ above the merchant's mean score = 1;
    otherwise scale linearly.
    """
    # Gather per-merchant edge weight stats
    merchant_weights: dict[str, list[float]] = {}
    for u, v, data in G.edges(data=True):
        node = v if v.startswith("mer:") else u
        merchant_weights.setdefault(node, []).append(data["weight"])

    mer_stats: dict[str, tuple[float, float]] = {}
    for mer, weights in merchant_weights.items():
        arr = np.array(weights)
        mer_stats[mer] = (float(arr.mean()), float(arr.std()) or 1.0)

    scores = np.zeros(len(df))
    for i, (_, row) in enumerate(df.iterrows()):
        mer_node = f"mer:{row['merchant']}"
        mean, std = mer_stats.get(mer_node, (0.0, 1.0))
        amt = float(row.get("amount", 0))
        if std < 1e-9:
            scores[i] = 0.0
        else:
            z = (amt - mean) / std
            scores[i] = min(max(z / 2.0, 0.0), 1.0)  # clip to [0, 1]

    return scores


# ── Public API ───────────────────────────────────────────

def run_graph_analysis(df: pd.DataFrame) -> pd.Series:
    """
    Build a transaction graph from the feature-engineered DataFrame
    and return per-row graph anomaly scores normalised to [0, 1].

    Parameters
    ----------
    df : DataFrame
        Must contain columns: account_id, merchant, amount.

    Returns
    -------
    pd.Series – anomaly scores in [0, 1], higher = more anomalous.
    """
    # Guard: too few rows for meaningful graph
    if len(df) < 3:
        return pd.Series(np.zeros(len(df)), index=df.index,
                         name="graph_score")

    G = _build_graph(df)

    # Four sub-scores
    s_degree = _degree_score(G, df)
    s_pr = _pagerank_score(G, df)
    s_comm = _community_score(G, df)
    s_edge = _edge_weight_outlier(G, df)

    # Equal-weight average of the four sub-scores
    composite = (s_degree + s_pr + s_comm + s_edge) / 4.0
    final = _normalise(composite)

    return pd.Series(final, index=df.index, name="graph_score")
