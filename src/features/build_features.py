from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"

EVENT_LOG_PATH = RAW_DIR / "p2p_event_log.csv"
CASE_SUMMARY_PATH = RAW_DIR / "p2p_case_summary.csv"
OUTPUT_PATH = PROCESSED_DIR / "p2p_ml_dataset.csv"
REPORT_PATH = REPORTS_DIR / "feature_engineering_report.md"

RANDOM_SEED = 42
PREDICTION_ACTIVITY = "Purchase Order"

BUSINESS_FEATURES = ["purchase_amount", "priority", "category", "vendor_id"]
PROCESS_FEATURES = [
    "elapsed_hours_to_purchase_order",
    "activities_completed_to_purchase_order",
    "unique_activities_completed",
    "has_budget_review",
    "manager_approval_completed",
    "approval_rework_count",
    "total_rework_events_so_far",
    "average_transition_time_so_far",
    "maximum_transition_time_so_far",
]
TARGET = "sla_breached"


def load_raw_data(
    event_log_path: Path = EVENT_LOG_PATH,
    case_summary_path: Path = CASE_SUMMARY_PATH,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    events = pd.read_csv(event_log_path)
    cases = pd.read_csv(case_summary_path)
    events["timestamp_dt"] = pd.to_datetime(events["timestamp"], errors="coerce")
    cases["start_time_dt"] = pd.to_datetime(cases["start_time"], errors="coerce")
    return events, cases


def _safe_bool(value: bool) -> int:
    return int(bool(value))


def build_feature_dataset(events: pd.DataFrame, cases: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    required_event_columns = {
        "case_id",
        "event_id",
        "activity",
        "timestamp_dt",
        "purchase_amount",
        "priority",
        "category",
        "vendor_id",
    }
    required_case_columns = {"case_id", "start_time_dt", "sla_breached"}
    missing_event_columns = required_event_columns - set(events.columns)
    missing_case_columns = required_case_columns - set(cases.columns)
    if missing_event_columns:
        raise ValueError(f"Missing event columns: {sorted(missing_event_columns)}")
    if missing_case_columns:
        raise ValueError(f"Missing case columns: {sorted(missing_case_columns)}")

    if events["timestamp_dt"].isna().any():
        raise ValueError("At least one event timestamp failed to parse.")
    if cases["start_time_dt"].isna().any():
        raise ValueError("At least one case start_time failed to parse.")

    events_sorted = events.sort_values(["case_id", "timestamp_dt", "event_id"]).copy()
    purchase_orders = events_sorted[events_sorted["activity"] == PREDICTION_ACTIVITY].copy()
    if purchase_orders.empty:
        raise ValueError(f"No '{PREDICTION_ACTIVITY}' events found.")

    prediction_points = (
        purchase_orders.sort_values(["case_id", "timestamp_dt", "event_id"])
        .groupby("case_id", as_index=False)
        .first()
        .rename(
            columns={
                "timestamp_dt": "purchase_order_timestamp",
                "event_id": "purchase_order_event_id",
                "purchase_amount": "purchase_amount_at_prediction",
                "priority": "priority_at_prediction",
                "category": "category_at_prediction",
                "vendor_id": "vendor_id_at_prediction",
            }
        )
    )

    merged = events_sorted.merge(
        prediction_points[
            [
                "case_id",
                "purchase_order_timestamp",
                "purchase_order_event_id",
                "purchase_amount_at_prediction",
                "priority_at_prediction",
                "category_at_prediction",
                "vendor_id_at_prediction",
            ]
        ],
        on="case_id",
        how="inner",
    )
    prefix_events = merged[merged["timestamp_dt"] <= merged["purchase_order_timestamp"]].copy()
    prefix_events = prefix_events.sort_values(["case_id", "timestamp_dt", "event_id"])
    prefix_events["previous_prefix_timestamp"] = prefix_events.groupby("case_id")["timestamp_dt"].shift(1)
    prefix_events["transition_hours"] = (
        prefix_events["timestamp_dt"] - prefix_events["previous_prefix_timestamp"]
    ).dt.total_seconds() / 3600

    case_start = cases[["case_id", "start_time_dt", TARGET]].copy()
    feature_base = prediction_points[
        [
            "case_id",
            "purchase_order_timestamp",
            "purchase_order_event_id",
            "purchase_amount_at_prediction",
            "priority_at_prediction",
            "category_at_prediction",
            "vendor_id_at_prediction",
        ]
    ].merge(case_start, on="case_id", how="left")

    if feature_base[TARGET].isna().any():
        raise ValueError("Some cases with prediction points are missing SLA targets.")

    rows: list[dict[str, object]] = []
    for case_id, group in prefix_events.groupby("case_id", sort=False):
        group = group.sort_values(["timestamp_dt", "event_id"])
        activities = group["activity"]
        activity_counts = activities.value_counts()
        po_row = group[group["activity"] == PREDICTION_ACTIVITY].iloc[0]
        transition_hours = group["transition_hours"].dropna()

        rows.append(
            {
                "case_id": case_id,
                "prediction_timestamp": po_row["purchase_order_timestamp"],
                "purchase_order_event_id": po_row["purchase_order_event_id"],
                "purchase_amount": po_row["purchase_amount_at_prediction"],
                "priority": po_row["priority_at_prediction"],
                "category": po_row["category_at_prediction"],
                "vendor_id": po_row["vendor_id_at_prediction"],
                "activities_completed_to_purchase_order": int(len(group)),
                "unique_activities_completed": int(activities.nunique()),
                "has_budget_review": _safe_bool((activities == "Budget Review").any()),
                "manager_approval_completed": _safe_bool((activities == "Manager Approval").any()),
                "approval_rework_count": int(max(activity_counts.get("Manager Approval", 0) - 1, 0)),
                "total_rework_events_so_far": int(sum(max(count - 1, 0) for count in activity_counts)),
                "average_transition_time_so_far": float(transition_hours.mean()) if len(transition_hours) else 0.0,
                "maximum_transition_time_so_far": float(transition_hours.max()) if len(transition_hours) else 0.0,
            }
        )

    process_features = pd.DataFrame(rows)
    ml_dataset = process_features.merge(
        feature_base[["case_id", "start_time_dt", TARGET]],
        on="case_id",
        how="left",
    )
    ml_dataset["elapsed_hours_to_purchase_order"] = (
        ml_dataset["prediction_timestamp"] - ml_dataset["start_time_dt"]
    ).dt.total_seconds() / 3600

    ordered_columns = [
        "case_id",
        "prediction_timestamp",
        "purchase_order_event_id",
        *BUSINESS_FEATURES,
        "elapsed_hours_to_purchase_order",
        "activities_completed_to_purchase_order",
        "unique_activities_completed",
        "has_budget_review",
        "manager_approval_completed",
        "approval_rework_count",
        "total_rework_events_so_far",
        "average_transition_time_so_far",
        "maximum_transition_time_so_far",
        TARGET,
    ]
    ml_dataset = ml_dataset[ordered_columns].sort_values("case_id").reset_index(drop=True)

    validation = validate_leakage_safety(events_sorted, cases, ml_dataset, prefix_events)
    failures = validation[validation["passed"] == False]
    if not failures.empty:
        raise ValueError("Leakage-safety validation failed:\n" + failures.to_string(index=False))

    return ml_dataset, validation


def validate_leakage_safety(
    events_sorted: pd.DataFrame,
    cases: pd.DataFrame,
    ml_dataset: pd.DataFrame,
    prefix_events: pd.DataFrame,
) -> pd.DataFrame:
    prediction_times = ml_dataset.set_index("case_id")["prediction_timestamp"]
    prefix_max = prefix_events.groupby("case_id")["timestamp_dt"].max()
    prefix_min = prefix_events.groupby("case_id")["timestamp_dt"].min()
    start_times = cases.set_index("case_id").loc[ml_dataset["case_id"], "start_time_dt"]

    all_po_cases = set(events_sorted.loc[events_sorted["activity"] == PREDICTION_ACTIVITY, "case_id"])
    dataset_cases = set(ml_dataset["case_id"])

    checks = [
        {
            "check": "one_row_per_case",
            "passed": len(ml_dataset) == ml_dataset["case_id"].nunique(),
            "detail": f"rows={len(ml_dataset)}, unique_cases={ml_dataset['case_id'].nunique()}",
        },
        {
            "check": "one_observation_for_each_case_with_purchase_order",
            "passed": dataset_cases == all_po_cases,
            "detail": f"dataset_cases={len(dataset_cases)}, purchase_order_cases={len(all_po_cases)}",
        },
        {
            "check": "prefix_event_timestamps_not_after_prediction",
            "passed": bool((prefix_max <= prediction_times.loc[prefix_max.index]).all()),
            "detail": "max prefix timestamp is <= prediction timestamp for every case",
        },
        {
            "check": "prefix_event_timestamps_not_before_case_start",
            "passed": bool((prefix_min >= cases.set_index('case_id').loc[prefix_min.index, 'start_time_dt']).all()),
            "detail": "first logged prefix event is >= case start_time for every case",
        },
        {
            "check": "case_start_not_after_prediction",
            "passed": bool((start_times.values <= ml_dataset["prediction_timestamp"].values).all()),
            "detail": "case start_time is <= prediction timestamp for every case",
        },
        {
            "check": "target_present",
            "passed": not ml_dataset[TARGET].isna().any(),
            "detail": f"missing_targets={int(ml_dataset[TARGET].isna().sum())}",
        },
        {
            "check": "no_forbidden_outcome_columns",
            "passed": not {"end_time", "duration_hours", "duration_days"}.intersection(ml_dataset.columns),
            "detail": "end_time, duration_hours, and duration_days are absent",
        },
        {
            "check": "feature_timestamps_at_or_before_prediction",
            "passed": bool(
                (
                    ml_dataset[
                        [
                            "elapsed_hours_to_purchase_order",
                            "average_transition_time_so_far",
                            "maximum_transition_time_so_far",
                        ]
                    ]
                    >= 0
                )
                .all()
                .all()
            ),
            "detail": "elapsed features are non-negative and computed only from prefix events",
        },
    ]
    return pd.DataFrame(checks)


def analyze_features(ml_dataset: pd.DataFrame) -> dict[str, pd.DataFrame]:
    numeric_columns = [
        "purchase_amount",
        "elapsed_hours_to_purchase_order",
        "activities_completed_to_purchase_order",
        "unique_activities_completed",
        "has_budget_review",
        "manager_approval_completed",
        "approval_rework_count",
        "total_rework_events_so_far",
        "average_transition_time_so_far",
        "maximum_transition_time_so_far",
    ]
    categorical_columns = ["priority", "category", "vendor_id"]

    numeric_distribution = ml_dataset[numeric_columns].describe(percentiles=[0.25, 0.5, 0.75, 0.9, 0.95]).T
    categorical_distribution = pd.concat(
        [
            ml_dataset[col]
            .value_counts(dropna=False)
            .rename_axis(col)
            .reset_index(name="count")
            .assign(feature=col, pct=lambda df: df["count"] / len(ml_dataset) * 100)
            .rename(columns={col: "value"})[["feature", "value", "count", "pct"]]
            for col in categorical_columns
        ],
        ignore_index=True,
    )
    numeric_target_correlation = (
        ml_dataset[numeric_columns + [TARGET]]
        .corr(numeric_only=True)[TARGET]
        .drop(TARGET)
        .sort_values(key=lambda s: s.abs(), ascending=False)
        .rename("correlation_with_target")
        .reset_index()
        .rename(columns={"index": "feature"})
    )
    class_balance = (
        ml_dataset[TARGET]
        .value_counts()
        .sort_index()
        .rename_axis(TARGET)
        .reset_index(name="cases")
        .assign(pct=lambda df: df["cases"] / len(ml_dataset) * 100)
    )

    def breach_rate_by(col: str) -> pd.DataFrame:
        return (
            ml_dataset.groupby(col)
            .agg(cases=("case_id", "count"), sla_breaches=(TARGET, "sum"), sla_breach_rate=(TARGET, "mean"))
            .reset_index()
            .sort_values(["sla_breach_rate", "cases"], ascending=[False, False])
        )

    vendor_cardinality = pd.DataFrame(
        [
            {
                "feature": "vendor_id",
                "unique_values": ml_dataset["vendor_id"].nunique(),
                "min_cases_per_vendor": int(ml_dataset["vendor_id"].value_counts().min()),
                "max_cases_per_vendor": int(ml_dataset["vendor_id"].value_counts().max()),
            }
        ]
    )

    return {
        "numeric_distribution": numeric_distribution.reset_index().rename(columns={"index": "feature"}),
        "categorical_distribution": categorical_distribution,
        "numeric_target_correlation": numeric_target_correlation,
        "class_balance": class_balance,
        "breach_by_priority": breach_rate_by("priority"),
        "breach_by_category": breach_rate_by("category"),
        "breach_by_vendor": breach_rate_by("vendor_id"),
        "vendor_cardinality": vendor_cardinality,
    }


def _fmt(value: object) -> str:
    if pd.isna(value):
        return ""
    if isinstance(value, (float, np.floating)):
        return f"{value:.2f}"
    if isinstance(value, (int, np.integer)):
        return str(value)
    return str(value)


def markdown_table(df: pd.DataFrame, max_rows: int | None = None) -> str:
    view = df.head(max_rows).copy() if max_rows else df.copy()
    columns = list(view.columns)
    rows = [[_fmt(value) for value in row] for row in view.to_numpy()]
    return "\n".join(
        ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
        + ["| " + " | ".join(row) + " |" for row in rows]
    )


def write_report(ml_dataset: pd.DataFrame, validation: pd.DataFrame, analysis: dict[str, pd.DataFrame]) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    class_balance = analysis["class_balance"]
    breached = class_balance.loc[class_balance[TARGET] == 1, "cases"].iloc[0]
    breach_rate = class_balance.loc[class_balance[TARGET] == 1, "pct"].iloc[0]
    vendor_cardinality = analysis["vendor_cardinality"].iloc[0]

    feature_rows = pd.DataFrame(
        [
            ["purchase_amount", "Business", "Purchase amount known at or before Purchase Order; sourced from the PO event."],
            ["priority", "Business", "Case priority as recorded on the PO event."],
            ["category", "Business", "Purchase category as recorded on the PO event."],
            ["vendor_id", "Business", "Vendor identifier as recorded on the PO event."],
            ["elapsed_hours_to_purchase_order", "Process", "Hours from case start_time to first Purchase Order timestamp."],
            ["activities_completed_to_purchase_order", "Process", "Count of events up to and including the first Purchase Order."],
            ["unique_activities_completed", "Process", "Unique activity count up to and including first Purchase Order."],
            ["has_budget_review", "Process", "Whether Budget Review occurred by the prediction point."],
            ["manager_approval_completed", "Process", "Whether Manager Approval occurred by the prediction point."],
            ["approval_rework_count", "Process", "Extra Manager Approval events beyond the first before or at prediction."],
            ["total_rework_events_so_far", "Process", "Extra repeated events across all activities before or at prediction."],
            ["average_transition_time_so_far", "Process", "Average elapsed hours between observed prefix events."],
            ["maximum_transition_time_so_far", "Process", "Maximum elapsed hours between observed prefix events."],
            ["sla_breached", "Target", "Eventual SLA outcome from case summary; used only as label."],
        ],
        columns=["name", "type", "definition"],
    )

    report = f"""# Feature Engineering Report - Phase 4

## Prediction Point

The prediction point is the first occurrence of `Purchase Order` for each case. The dataset contains exactly one ML observation per case, built only from information available at or before that Purchase Order timestamp.

Output dataset: `data/processed/p2p_ml_dataset.csv`

Rows: **{len(ml_dataset):,}**  
Unique cases: **{ml_dataset['case_id'].nunique():,}**

## Target Definition

The target is `sla_breached`, copied from `p2p_case_summary.csv`. It represents whether the case eventually breached its SLA. This is allowed as the supervised-learning label, but no outcome-derived fields are used as features.

## Feature Definitions

{markdown_table(feature_rows)}

## Leakage Prevention

Forbidden fields were excluded from the ML dataset: `end_time`, `duration_hours`, and `duration_days`. Future activities, future timestamps, future transition durations, and future rework after Purchase Order were not used. Business attributes are sourced from the Purchase Order event, and process features are computed only from prefix events where `event_timestamp <= prediction_timestamp`.

Validation checks:

{markdown_table(validation)}

## Class Balance

{markdown_table(class_balance)}

The positive SLA-breach class contains **{int(breached):,}** cases (**{breach_rate:.2f}%**).

## Numeric Feature Distributions

{markdown_table(analysis['numeric_distribution'])}

## Numeric Correlation With Target

{markdown_table(analysis['numeric_target_correlation'])}

Correlations are descriptive only and should not be interpreted causally.

## SLA Breach Rate by Important Categorical Features

### Priority

{markdown_table(analysis['breach_by_priority'])}

### Category

{markdown_table(analysis['breach_by_category'])}

### Vendor, Top 15 by Breach Rate

{markdown_table(analysis['breach_by_vendor'].head(15))}

## Modeling Considerations

- `vendor_id` has {int(vendor_cardinality.unique_values)} unique values, with {int(vendor_cardinality.min_cases_per_vendor)} to {int(vendor_cardinality.max_cases_per_vendor)} cases per vendor. Treat it as a high-cardinality categorical feature; use cross-validated target encoding, frequency encoding, regularized entity embeddings, or one-hot encoding only if model choice and validation support it.
- Any vendor historical breach-rate feature must be computed using only prior cases or out-of-fold training data to avoid target leakage.
- `has_budget_review`, `elapsed_hours_to_purchase_order`, and early transition timing features are available by the Purchase Order timestamp and are good candidates for modeling.
- `manager_approval_completed` may have little or no variance because Manager Approval generally precedes Purchase Order in this process.
- Keep `case_id`, `prediction_timestamp`, and `purchase_order_event_id` as identifiers/audit columns, not predictive model features.
- Do not use full-case duration, case end time, or post-Purchase-Order events during modeling.

## Reproducibility

The feature-generation code is implemented in `src/features/build_features.py` with fixed `RANDOM_SEED = {RANDOM_SEED}`. No sampling is required for the final dataset.
"""
    REPORT_PATH.write_text(report, encoding="utf-8")


def main() -> None:
    np.random.seed(RANDOM_SEED)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    events, cases = load_raw_data()
    ml_dataset, validation = build_feature_dataset(events, cases)
    analysis = analyze_features(ml_dataset)

    ml_dataset.to_csv(OUTPUT_PATH, index=False)
    write_report(ml_dataset, validation, analysis)

    print(f"Wrote {OUTPUT_PATH}")
    print(f"Wrote {REPORT_PATH}")
    print(f"Rows: {len(ml_dataset):,}")
    print(f"Unique cases: {ml_dataset['case_id'].nunique():,}")


if __name__ == "__main__":
    main()
