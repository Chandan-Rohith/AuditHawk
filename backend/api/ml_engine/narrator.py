"""
Narrator – Human-Readable Explanations  (Phase 3 ✓)
───────────────────────────────────────────────────────────
Translates raw machine learning anomaly scores into actionable, 
auditor-friendly threat intelligence. Ranks signals by severity.
"""

from __future__ import annotations
import pandas as pd

def generate_explanations(anomalies: pd.DataFrame, max_reasons: int = 2) -> list[str]:
    """
    Given a DataFrame of anomalous rows, rank the triggered rules by score 
    and return only the top `max_reasons` to prevent UI alert fatigue.
    """
    explanations: list[str] = []

    for _, row in anomalies.iterrows():
        # Store tuples of (score, explanation_text)
        signals: list[tuple[float, str]] = []

        # Velocity
        vel = row.get("velocity", 0.0)
        if vel > 0.7:
            signals.append((vel, f"Velocity Risk ({vel:.2f}): Rapid, repeated payments to this vendor."))

        # Pattern
        pat = row.get("pattern", 0.0)
        if pat > 0.7:
            signals.append((pat, f"Time Anomaly ({pat:.2f}): Transaction occurred outside normal business hours."))

        # Rarity
        rar = row.get("rarity", 0.0)
        if rar > 0.7:
            signals.append((rar, f"Unusual Vendor ({rar:.2f}): Payment made to an unrecognized or rare merchant."))

        # Magnitude
        mag = row.get("magnitude", 0.0)
        if mag > 0.7:
            signals.append((mag, f"Massive Outlier ({mag:.2f}): Abnormally large amount compared to corporate baselines."))

        # LOF
        lof = row.get("lof_score", 0.0)
        if lof > 0.5:
            signals.append((lof, f"Data Deviation (LOF {lof:.2f}): Metadata strongly breaks historical purchasing patterns."))

        # Autoencoder (Phase 2)
        ae = row.get("ae_score", 0.0)
        if ae > 0.5:
            signals.append((ae, f"Behavioral Anomaly (AI {ae:.2f}): Deep learning detected a break in established normal behavior."))

        # Graph (Phase 3)
        graph = row.get("graph_score", 0.0)
        if graph > 0.5:
            signals.append((graph, f"Suspicious Network (Graph {graph:.2f}): Funds moving between isolated accounts or sinkholes."))

        # Fallback if nothing explicitly crossed the high thresholds
        if not signals:
            explanations.append("Composite Risk: Flagged by multiple weak risk signals reaching the anomaly threshold.")
            continue

        # 🚨 THE TRIAGE LOGIC: Sort by score (highest first) and slice the top N
        signals.sort(key=lambda x: x[0], reverse=True)
        top_signals = signals[:max_reasons]

        # Extract just the text from the top signals and join them
        parts = [text for score, text in top_signals]
        explanation = " • ".join(parts)
        
        explanations.append(explanation)

    return explanations