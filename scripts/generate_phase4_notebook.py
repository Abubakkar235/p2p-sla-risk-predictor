from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = ROOT / "notebooks" / "03_feature_engineering.ipynb"


def main() -> None:
    cells = []

    def md(text: str) -> None:
        cells.append({"cell_type": "markdown", "metadata": {}, "source": text.strip().splitlines(True)})

    def code(text: str) -> None:
        cells.append(
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": text.strip().splitlines(True),
            }
        )

    md(
        """
# Phase 4 - Leakage-Safe Feature Engineering

Prediction scenario: **At the moment a Purchase Order has been created, predict whether the case will eventually breach its SLA.**

This notebook builds one ML observation per case using only information available at or before the first `Purchase Order` timestamp. It does not modify `data/raw/` and does not train any model.
"""
    )
    code(
        """
from pathlib import Path
import sys

import pandas as pd

PROJECT_ROOT = Path.cwd() if (Path.cwd() / "data" / "raw").exists() else Path.cwd().parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.features.build_features import (
    BUSINESS_FEATURES,
    PROCESS_FEATURES,
    TARGET,
    analyze_features,
    build_feature_dataset,
    load_raw_data,
    write_report,
)

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
OUTPUT_PATH = PROCESSED_DIR / "p2p_ml_dataset.csv"

pd.set_option("display.max_columns", 100)
pd.set_option("display.max_colwidth", 180)
"""
    )
    md(
        """
## 1. Load Raw Data

The raw event log and case summary are read into memory. No raw file is modified.
"""
    )
    code(
        """
events, cases = load_raw_data()

pd.DataFrame([
    {"dataset": "p2p_event_log.csv", "rows": len(events), "columns": events.drop(columns=["timestamp_dt"]).shape[1]},
    {"dataset": "p2p_case_summary.csv", "rows": len(cases), "columns": cases.drop(columns=["start_time_dt"]).shape[1]},
])
"""
    )
    md(
        """
## 2. Prediction Point

For every case, the prediction point is the first occurrence of `Purchase Order`. The features are computed from the prefix of events whose timestamp is less than or equal to that first Purchase Order timestamp.
"""
    )
    code(
        """
purchase_order_counts = (
    events[events["activity"] == "Purchase Order"]
    .groupby("case_id")
    .size()
    .rename("purchase_order_events")
    .reset_index()
)

pd.DataFrame({
    "cases_in_event_log": [events["case_id"].nunique()],
    "cases_with_purchase_order": [purchase_order_counts["case_id"].nunique()],
    "cases_with_multiple_purchase_orders": [(purchase_order_counts["purchase_order_events"] > 1).sum()],
})
"""
    )
    md(
        """
## 3. Build Leakage-Safe Dataset

The builder creates one observation per case and includes only:

- Business attributes known on the Purchase Order event.
- Process-prefix features available at or before the Purchase Order timestamp.
- The eventual `sla_breached` label from the case summary.

Forbidden future/outcome fields such as `end_time`, `duration_hours`, and `duration_days` are excluded.
"""
    )
    code(
        """
ml_dataset, validation = build_feature_dataset(events, cases)
ml_dataset.head()
"""
    )
    md(
        """
## 4. Validate Leakage Safety

These checks prove that the dataset has one row per case and that all feature-producing timestamps are at or before the prediction timestamp.
"""
    )
    code(
        """
validation
"""
    )
    code(
        """
assert validation["passed"].all()
assert len(ml_dataset) == ml_dataset["case_id"].nunique()
assert {"end_time", "duration_hours", "duration_days"}.isdisjoint(ml_dataset.columns)
assert len(ml_dataset) == cases["case_id"].nunique()
"""
    )
    md(
        """
## 5. Feature Set

The final dataset keeps identifiers and audit columns (`case_id`, `prediction_timestamp`, `purchase_order_event_id`) but these should not be used as model features. The feature columns below are the candidate predictors.
"""
    )
    code(
        """
feature_inventory = pd.DataFrame({
    "feature": BUSINESS_FEATURES + PROCESS_FEATURES + [TARGET],
    "role": ["business"] * len(BUSINESS_FEATURES) + ["process"] * len(PROCESS_FEATURES) + ["target"],
})
feature_inventory
"""
    )
    md("## 6. Save Processed Dataset")
    code(
        """
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
ml_dataset.to_csv(OUTPUT_PATH, index=False)
OUTPUT_PATH
"""
    )
    md("## 7. Target Class Balance")
    code(
        """
analysis = analyze_features(ml_dataset)
analysis["class_balance"]
"""
    )
    md("## 8. Numeric Feature Distributions")
    code(
        """
analysis["numeric_distribution"]
"""
    )
    md(
        """
## 9. Numeric Correlation With Target

These correlations are descriptive only. They should not be interpreted as causal relationships.
"""
    )
    code(
        """
analysis["numeric_target_correlation"]
"""
    )
    md("## 10. Categorical Distributions")
    code(
        """
analysis["categorical_distribution"].head(30)
"""
    )
    md("## 11. SLA Breach Rate by Priority and Category")
    code('analysis["breach_by_priority"]')
    code('analysis["breach_by_category"]')
    md(
        """
## 12. Vendor Analysis and High Cardinality

`vendor_id` is useful but should be handled carefully in modeling because it is a higher-cardinality categorical feature. Avoid naive target encoding unless it is computed out-of-fold or from prior historical data only.
"""
    )
    code('analysis["vendor_cardinality"]')
    code('analysis["breach_by_vendor"].head(15)')
    md(
        """
## 13. Write Feature Engineering Report

The report summarizes the prediction point, target, feature definitions, leakage-prevention checks, class balance, and modeling considerations.
"""
    )
    code(
        """
write_report(ml_dataset, validation, analysis)
PROJECT_ROOT / "reports" / "feature_engineering_report.md"
"""
    )
    md(
        """
## 14. Modeling Notes for Later

Do not train a model in this phase. For the next phase, use leakage-safe preprocessing: split data before target/frequency encoding, keep audit columns out of the model matrix, and ensure any vendor historical aggregates are computed using only training-fold or prior-case information.
"""
    )

    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.12"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    NOTEBOOK_PATH.write_text(json.dumps(notebook, indent=2), encoding="utf-8")
    print(f"Wrote {NOTEBOOK_PATH}")


if __name__ == "__main__":
    main()
