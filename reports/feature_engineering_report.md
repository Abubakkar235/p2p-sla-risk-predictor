# Feature Engineering Report - Phase 4

## Prediction Point

The prediction point is the first occurrence of `Purchase Order` for each case. The dataset contains exactly one ML observation per case, built only from information available at or before that Purchase Order timestamp.

Output dataset: `data/processed/p2p_ml_dataset.csv`

Rows: **20,000**  
Unique cases: **20,000**

## Target Definition

The target is `sla_breached`, copied from `p2p_case_summary.csv`. It represents whether the case eventually breached its SLA. This is allowed as the supervised-learning label, but no outcome-derived fields are used as features.

## Feature Definitions

| name | type | definition |
| --- | --- | --- |
| purchase_amount | Business | Purchase amount known at or before Purchase Order; sourced from the PO event. |
| priority | Business | Case priority as recorded on the PO event. |
| category | Business | Purchase category as recorded on the PO event. |
| vendor_id | Business | Vendor identifier as recorded on the PO event. |
| elapsed_hours_to_purchase_order | Process | Hours from case start_time to first Purchase Order timestamp. |
| activities_completed_to_purchase_order | Process | Count of events up to and including the first Purchase Order. |
| unique_activities_completed | Process | Unique activity count up to and including first Purchase Order. |
| has_budget_review | Process | Whether Budget Review occurred by the prediction point. |
| manager_approval_completed | Process | Whether Manager Approval occurred by the prediction point. |
| approval_rework_count | Process | Extra Manager Approval events beyond the first before or at prediction. |
| total_rework_events_so_far | Process | Extra repeated events across all activities before or at prediction. |
| average_transition_time_so_far | Process | Average elapsed hours between observed prefix events. |
| maximum_transition_time_so_far | Process | Maximum elapsed hours between observed prefix events. |
| sla_breached | Target | Eventual SLA outcome from case summary; used only as label. |

## Leakage Prevention

Forbidden fields were excluded from the ML dataset: `end_time`, `duration_hours`, and `duration_days`. Future activities, future timestamps, future transition durations, and future rework after Purchase Order were not used. Business attributes are sourced from the Purchase Order event, and process features are computed only from prefix events where `event_timestamp <= prediction_timestamp`.

Validation checks:

| check | passed | detail |
| --- | --- | --- |
| one_row_per_case | True | rows=20000, unique_cases=20000 |
| one_observation_for_each_case_with_purchase_order | True | dataset_cases=20000, purchase_order_cases=20000 |
| prefix_event_timestamps_not_after_prediction | True | max prefix timestamp is <= prediction timestamp for every case |
| prefix_event_timestamps_not_before_case_start | True | first logged prefix event is >= case start_time for every case |
| case_start_not_after_prediction | True | case start_time is <= prediction timestamp for every case |
| target_present | True | missing_targets=0 |
| no_forbidden_outcome_columns | True | end_time, duration_hours, and duration_days are absent |
| feature_timestamps_at_or_before_prediction | True | elapsed features are non-negative and computed only from prefix events |

## Class Balance

| sla_breached | cases | pct |
| --- | --- | --- |
| 0.00 | 15986.00 | 79.93 |
| 1.00 | 4014.00 | 20.07 |

The positive SLA-breach class contains **4,014** cases (**20.07%**).

## Numeric Feature Distributions

| feature | count | mean | std | min | 25% | 50% | 75% | 90% | 95% | max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| purchase_amount | 20000.00 | 76926.94 | 52096.68 | 5000.00 | 38518.70 | 65510.69 | 102791.79 | 146627.22 | 178092.17 | 422459.26 |
| elapsed_hours_to_purchase_order | 20000.00 | 126.09 | 72.53 | 3.67 | 72.90 | 117.87 | 165.27 | 208.95 | 259.77 | 748.64 |
| activities_completed_to_purchase_order | 20000.00 | 3.31 | 0.50 | 3.00 | 3.00 | 3.00 | 4.00 | 4.00 | 4.00 | 5.00 |
| unique_activities_completed | 20000.00 | 3.24 | 0.43 | 3.00 | 3.00 | 3.00 | 3.00 | 4.00 | 4.00 | 4.00 |
| has_budget_review | 20000.00 | 0.24 | 0.43 | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 | 1.00 | 1.00 |
| manager_approval_completed | 20000.00 | 1.00 | 0.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 |
| approval_rework_count | 20000.00 | 0.07 | 0.26 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 | 1.00 |
| total_rework_events_so_far | 20000.00 | 0.07 | 0.26 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 1.00 | 1.00 |
| average_transition_time_so_far | 20000.00 | 49.17 | 28.59 | 0.50 | 27.27 | 46.98 | 61.19 | 79.58 | 94.46 | 357.01 |
| maximum_transition_time_so_far | 20000.00 | 80.87 | 57.33 | 0.50 | 44.47 | 71.26 | 98.83 | 139.11 | 168.79 | 690.90 |

## Numeric Correlation With Target

| feature | correlation_with_target |
| --- | --- |
| elapsed_hours_to_purchase_order | 0.37 |
| maximum_transition_time_so_far | 0.34 |
| average_transition_time_so_far | 0.32 |
| activities_completed_to_purchase_order | 0.19 |
| unique_activities_completed | 0.17 |
| has_budget_review | 0.17 |
| purchase_amount | 0.15 |
| total_rework_events_so_far | 0.09 |
| approval_rework_count | 0.09 |
| manager_approval_completed |  |

Correlations are descriptive only and should not be interpreted causally.

## SLA Breach Rate by Important Categorical Features

### Priority

| priority | cases | sla_breaches | sla_breach_rate |
| --- | --- | --- | --- |
| Low | 4954 | 1084 | 0.22 |
| Medium | 10987 | 2297 | 0.21 |
| High | 4059 | 633 | 0.16 |

### Category

| category | cases | sla_breaches | sla_breach_rate |
| --- | --- | --- | --- |
| Services | 3989 | 1106 | 0.28 |
| Maintenance | 3959 | 1070 | 0.27 |
| Software | 4052 | 652 | 0.16 |
| IT Equipment | 3996 | 616 | 0.15 |
| Office Supplies | 4004 | 570 | 0.14 |

### Vendor, Top 15 by Breach Rate

| vendor_id | cases | sla_breaches | sla_breach_rate |
| --- | --- | --- | --- |
| V031 | 399 | 129 | 0.32 |
| V023 | 415 | 124 | 0.30 |
| V004 | 443 | 127 | 0.29 |
| V047 | 418 | 111 | 0.27 |
| V003 | 386 | 101 | 0.26 |
| V036 | 396 | 103 | 0.26 |
| V019 | 406 | 102 | 0.25 |
| V027 | 408 | 102 | 0.25 |
| V001 | 355 | 86 | 0.24 |
| V014 | 391 | 94 | 0.24 |
| V042 | 425 | 101 | 0.24 |
| V015 | 403 | 94 | 0.23 |
| V028 | 397 | 92 | 0.23 |
| V030 | 387 | 89 | 0.23 |
| V040 | 387 | 88 | 0.23 |

## Modeling Considerations

- `vendor_id` has 50 unique values, with 349 to 445 cases per vendor. Treat it as a high-cardinality categorical feature; use cross-validated target encoding, frequency encoding, regularized entity embeddings, or one-hot encoding only if model choice and validation support it.
- Any vendor historical breach-rate feature must be computed using only prior cases or out-of-fold training data to avoid target leakage.
- `has_budget_review`, `elapsed_hours_to_purchase_order`, and early transition timing features are available by the Purchase Order timestamp and are good candidates for modeling.
- `manager_approval_completed` may have little or no variance because Manager Approval generally precedes Purchase Order in this process.
- Keep `case_id`, `prediction_timestamp`, and `purchase_order_event_id` as identifiers/audit columns, not predictive model features.
- Do not use full-case duration, case end time, or post-Purchase-Order events during modeling.

## Reproducibility

The feature-generation code is implemented in `src/features/build_features.py` with fixed `RANDOM_SEED = 42`. No sampling is required for the final dataset.
