"""
Behavioral Profiling Autoencoder  (Phase 2 ✓)
──────────────────────────────────────────────
PyTorch nn.Module trained on-the-fly per CSV upload.

Architecture
────────────
  Input(4) → Dense(8) → ReLU → Bottleneck(2) → ReLU → Dense(8) → ReLU → Output(4)

Training
────────
~50 epochs over the entire dataset (assumption: ≥99 % of rows are
"normal", so the autoencoder learns to reconstruct normal patterns).

Scoring
───────
Per-row Mean Squared Error (MSE) reconstruction loss:
  MSE_i = (1/n) Σ (X_i - X̂_i)²
Normalised to [0, 1] across the dataset.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset

FEATURE_COLS = ["velocity", "pattern", "rarity", "magnitude"]


# ── PyTorch Model ────────────────────────────────────────

class TransactionAutoencoder(nn.Module):
    """
    Symmetric autoencoder:
        4 → 8 → 2 (bottleneck) → 8 → 4
    """

    def __init__(self):
        super().__init__()
        self.encoder = nn.Sequential(
            nn.Linear(4, 8),
            nn.ReLU(),
            nn.Linear(8, 2),
            nn.ReLU(),
        )
        self.decoder = nn.Sequential(
            nn.Linear(2, 8),
            nn.ReLU(),
            nn.Linear(8, 4),
            nn.Sigmoid()  # <-- Forces output to be exactly between 0 and 1
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        z = self.encoder(x)
        return self.decoder(z)


# ── Public API ───────────────────────────────────────────

def run_autoencoder(
    df: pd.DataFrame,
    epochs: int = 50,
    lr: float = 1e-3,
    batch_size: int = 64,
) -> pd.Series:
    """
    Train an autoencoder on the feature-engineered DataFrame and return
    per-row MSE reconstruction loss normalised to [0, 1].

    Parameters
    ----------
    df : DataFrame
        Must contain the four feature columns (already [0,1]-scaled by
        feature_engineering.build_features).
    epochs : int
        Training epochs (default 50).
    lr : float
        Adam learning rate.
    batch_size : int
        Mini-batch size for DataLoader.

    Returns
    -------
    pd.Series  – anomaly scores in [0, 1], higher = more anomalous.
    """
    X = df[FEATURE_COLS].values.astype(np.float32)

    # Guard: if fewer than 3 rows, AE is meaningless
    if len(X) < 3:
        return pd.Series(np.zeros(len(df)), index=df.index, name="ae_score")

    tensor_x = torch.from_numpy(X)
    dataset = TensorDataset(tensor_x, tensor_x)  # input == target
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    model = TransactionAutoencoder()
    optimiser = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.MSELoss(reduction="none")  # per-element loss

    # ── Training loop ────────────────────────────────────
    model.train()
    for _epoch in range(epochs):
        for batch_x, batch_target in loader:
            reconstructed = model(batch_x)
            loss = criterion(reconstructed, batch_target).mean()
            optimiser.zero_grad()
            loss.backward()
            optimiser.step()

    # ── Scoring ──────────────────────────────────────────
    model.eval()
    with torch.no_grad():
        reconstructed = model(tensor_x)
        # per-row MSE: mean over the 4 feature dimensions
        mse = criterion(reconstructed, tensor_x).mean(dim=1).numpy()

    # REMOVE the mse / mse_max logic. Just return the raw error multiplied by a constant.
    # We multiply by 10 just to bring tiny decimals (0.005) up to a readable baseline (0.05)
    scores = mse * 10.0 
    return pd.Series(scores, index=df.index, name="ae_score")
