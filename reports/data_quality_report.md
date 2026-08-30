# Data Quality Report - Phase 2: Data Understanding

## Scope

This report profiles the raw synthetic Purchase-to-Pay event log in `data/raw/p2p_event_log.csv` and the case-level summary in `data/raw/p2p_case_summary.csv`. The raw CSV files were inspected but not modified.

## Dataset Inventory

| Dataset | Rows | Columns |
|---|---:|---:|
| `p2p_event_log.csv` | 149,467 | 11 |
| `p2p_case_summary.csv` | 20,000 | 12 |

Both files exist under `data/raw/`.

## Schema and Missing Values

| dataset | column | dtype | missing_values |
| --- | --- | --- | --- |
| p2p_event_log.csv | case_id | str | 0 |
| p2p_event_log.csv | event_id | str | 0 |
| p2p_event_log.csv | activity | str | 0 |
| p2p_event_log.csv | timestamp | str | 0 |
| p2p_event_log.csv | department | str | 0 |
| p2p_event_log.csv | vendor_id | str | 0 |
| p2p_event_log.csv | purchase_amount | float64 | 0 |
| p2p_event_log.csv | priority | str | 0 |
| p2p_event_log.csv | category | str | 0 |
| p2p_event_log.csv | resource | str | 0 |
| p2p_event_log.csv | status | str | 0 |
| p2p_case_summary.csv | case_id | str | 0 |
| p2p_case_summary.csv | start_time | str | 0 |
| p2p_case_summary.csv | end_time | str | 0 |
| p2p_case_summary.csv | duration_hours | float64 | 0 |
| p2p_case_summary.csv | duration_days | float64 | 0 |
| p2p_case_summary.csv | sla_days | int64 | 0 |
| p2p_case_summary.csv | sla_breached | int64 | 0 |
| p2p_case_summary.csv | priority | str | 0 |
| p2p_case_summary.csv | category | str | 0 |
| p2p_case_summary.csv | vendor_id | str | 0 |
| p2p_case_summary.csv | purchase_amount | float64 | 0 |
| p2p_case_summary.csv | event_count | int64 | 0 |

## Core Quality Checks

| metric | value |
| --- | --- |
| event_log_rows | 149467 |
| event_log_columns | 11 |
| case_summary_rows | 20000 |
| case_summary_columns | 12 |
| event_log_duplicate_rows | 0 |
| case_summary_duplicate_rows | 0 |
| unique_cases_event_log | 20000 |
| unique_cases_case_summary | 20000 |
| unique_activities | 8 |
| unique_vendors_event_log | 50 |
| unique_vendors_case_summary | 50 |
| event_timestamp_parse_failures | 0 |
| case_start_parse_failures | 0 |
| case_end_parse_failures | 0 |
| event_time_min | 2025-01-01 09:35:45.177603502 |
| event_time_max | 2026-03-03 12:12:52.500198844 |
| case_start_min | 2025-01-01 08:00:00 |
| case_end_max | 2026-03-03 12:12:52.500198844 |
| chronological_order_violating_cases | 0 |
| process_variant_count | 16 |
| cases_with_repeated_activities | 4334 |
| cases_with_repeated_activities_pct | 21.67 |
| sla_breached_cases | 4014 |
| sla_breach_rate | 0.20 |
| event_count_mismatches_between_files | 0 |
| event_id_duplicates | 0 |
| duplicate_case_ids_in_case_summary | 0 |

## Activity Distribution

| activity | events | pct |
| --- | --- | --- |
| Invoice Verification | 21997 | 14.72 |
| Manager Approval | 21418 | 14.33 |
| Vendor Confirmation | 21221 | 14.20 |
| Purchase Request | 20000 | 13.38 |
| Purchase Order | 20000 | 13.38 |
| Goods Receipt | 20000 | 13.38 |
| Payment | 20000 | 13.38 |
| Budget Review | 4831 | 3.23 |

The most frequent activities are Invoice Verification, Manager Approval, and Vendor Confirmation. Their counts exceed the 20,000-case baseline because some cases repeat those activities.

## Priority, Category, Department, and Status Distributions

### Priority

| priority | events | pct |
| --- | --- | --- |
| Medium | 82121 | 54.94 |
| Low | 37026 | 24.77 |
| High | 30320 | 20.29 |

### Category

| category | events | pct |
| --- | --- | --- |
| Software | 30300 | 20.27 |
| Office Supplies | 29963 | 20.05 |
| Services | 29827 | 19.96 |
| IT Equipment | 29821 | 19.95 |
| Maintenance | 29556 | 19.77 |

### Department

| department | events | pct |
| --- | --- | --- |
| Finance | 68246 | 45.66 |
| Procurement | 61221 | 40.96 |
| Operations | 20000 | 13.38 |

### Status

| status | events | pct |
| --- | --- | --- |
| Completed | 149467 | 100.00 |

All event statuses are `Completed`; this column has no variation in the current dataset.

## Chronological Ordering

Cases with events out of chronological order in the current file order: **0**.

No chronological ordering violations were detected.

## Process Variants

Observed process variants: **16**.

Top variants:

| variant_id | case_count | case_pct | activity_sequence |
| --- | --- | --- | --- |
| 1 | 11918 | 59.59 | Purchase Request -> Manager Approval -> Purchase Order -> Vendor Confirmation -> Goods Receipt -> Invoice Verification -> Payment |
| 2 | 3748 | 18.74 | Purchase Request -> Budget Review -> Manager Approval -> Purchase Order -> Vendor Confirmation -> Goods Receipt -> Invoice Verification -> Payment |
| 3 | 1330 | 6.65 | Purchase Request -> Manager Approval -> Purchase Order -> Vendor Confirmation -> Goods Receipt -> Invoice Verification -> Invoice Verification -> Payment |
| 4 | 944 | 4.72 | Purchase Request -> Manager Approval -> Manager Approval -> Purchase Order -> Vendor Confirmation -> Goods Receipt -> Invoice Verification -> Payment |
| 5 | 761 | 3.81 | Purchase Request -> Manager Approval -> Purchase Order -> Vendor Confirmation -> Vendor Confirmation -> Goods Receipt -> Invoice Verification -> Payment |
| 6 | 438 | 2.19 | Purchase Request -> Budget Review -> Manager Approval -> Purchase Order -> Vendor Confirmation -> Goods Receipt -> Invoice Verification -> Invoice Verification -> Payment |
| 7 | 286 | 1.43 | Purchase Request -> Budget Review -> Manager Approval -> Purchase Order -> Vendor Confirmation -> Vendor Confirmation -> Goods Receipt -> Invoice Verification -> Payment |
| 8 | 281 | 1.41 | Purchase Request -> Budget Review -> Manager Approval -> Manager Approval -> Purchase Order -> Vendor Confirmation -> Goods Receipt -> Invoice Verification -> Payment |
| 9 | 94 | 0.47 | Purchase Request -> Manager Approval -> Manager Approval -> Purchase Order -> Vendor Confirmation -> Goods Receipt -> Invoice Verification -> Invoice Verification -> Payment |
| 10 | 65 | 0.33 | Purchase Request -> Manager Approval -> Purchase Order -> Vendor Confirmation -> Vendor Confirmation -> Goods Receipt -> Invoice Verification -> Invoice Verification -> Payment |

The dominant happy path is `Purchase Request -> Manager Approval -> Purchase Order -> Vendor Confirmation -> Goods Receipt -> Invoice Verification -> Payment`.

## Potential Rework from Repeated Activities

Cases containing repeated activities: **4,334** (21.67%).

| repeated_activity | cases |
| --- | --- |
| Invoice Verification | 1997 |
| Manager Approval | 1418 |
| Vendor Confirmation | 1221 |

Repeated activities should be retained for process mining because they likely encode rework loops rather than bad duplicate rows.

## SLA Breach Distribution

| sla_breached | cases | pct |
| --- | --- | --- |
| 0.00 | 15986.00 | 79.93 |
| 1.00 | 4014.00 | 20.07 |

Overall SLA breach rate: **20.07%**.

### SLA Breach Rate by Priority

| priority | cases | breaches | breach_rate |
| --- | --- | --- | --- |
| Low | 4954 | 1084 | 0.22 |
| Medium | 10987 | 2297 | 0.21 |
| High | 4059 | 633 | 0.16 |

### SLA Breach Rate by Category

| category | cases | breaches | breach_rate |
| --- | --- | --- | --- |
| Services | 3989 | 1106 | 0.28 |
| Maintenance | 3959 | 1070 | 0.27 |
| Software | 4052 | 652 | 0.16 |
| IT Equipment | 3996 | 616 | 0.15 |
| Office Supplies | 4004 | 570 | 0.14 |

### Top Vendor SLA Breach Rates

| vendor_id | cases | breaches | breach_rate |
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

Low-priority cases have the highest breach rate by priority in this synthetic dataset. Services and Maintenance have materially higher breach rates than the other categories. Vendor-level rates vary noticeably, with V031, V023, and V004 having the highest observed rates among vendors.

## Duration Statistics

| metric | count | mean | std | min | 25% | 50% | 75% | 90% | 95% | max |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| duration_hours | 20000.00 | 545.78 | 171.68 | 72.71 | 425.18 | 525.95 | 647.49 | 763.09 | 848.27 | 2015.86 |
| duration_days | 20000.00 | 22.74 | 7.15 | 3.03 | 17.72 | 21.91 | 26.98 | 31.80 | 35.34 | 83.99 |

Case duration ranges from 3.03 to 83.99 days. The median duration is 21.91 days and the 95th percentile is 35.34 days.

## Potential Bottlenecks

Potential bottlenecks were estimated from elapsed time between consecutive events within each case. Because the event log has one timestamp per activity and no explicit start/end timestamps per activity, these are waiting-time approximations rather than true task processing times.

### Longest Average Transition Gaps

| prev_activity | activity | transitions | avg_gap_hours | median_gap_hours | p90_gap_hours |
| --- | --- | --- | --- | --- | --- |
| Purchase Order | Vendor Confirmation | 20000 | 134.80 | 121.34 | 240.75 |
| Vendor Confirmation | Goods Receipt | 20000 | 134.04 | 140.28 | 233.16 |
| Budget Review | Manager Approval | 4831 | 85.47 | 71.57 | 146.42 |
| Invoice Verification | Payment | 20000 | 81.83 | 76.35 | 140.95 |
| Purchase Request | Manager Approval | 15169 | 68.75 | 50.31 | 122.92 |
| Vendor Confirmation | Vendor Confirmation | 1221 | 65.75 | 52.91 | 117.39 |
| Invoice Verification | Invoice Verification | 1997 | 63.55 | 52.61 | 115.09 |
| Manager Approval | Manager Approval | 1418 | 63.26 | 52.19 | 115.12 |
| Goods Receipt | Invoice Verification | 20000 | 58.65 | 48.55 | 114.85 |
| Purchase Request | Budget Review | 4831 | 46.80 | 43.10 | 93.92 |

### Average Hours from Activity to Next Event

| activity | events | avg_hours_to_next | median_hours_to_next | p90_hours_to_next |
| --- | --- | --- | --- | --- |
| Purchase Order | 20000 | 134.80 | 121.34 | 240.75 |
| Vendor Confirmation | 21221 | 130.11 | 134.95 | 220.32 |
| Budget Review | 4831 | 85.47 | 71.57 | 146.42 |
| Invoice Verification | 21997 | 80.17 | 74.68 | 139.91 |
| Purchase Request | 20000 | 63.45 | 48.38 | 118.47 |
| Goods Receipt | 20000 | 58.65 | 48.55 | 114.85 |
| Manager Approval | 21418 | 28.98 | 22.61 | 71.15 |

The largest average transition gaps occur after Purchase Order before Vendor Confirmation and after Vendor Confirmation before Goods Receipt. These are likely candidate bottleneck areas for Phase 3 process mining.

## Data-Quality Issues and Assumptions

- No missing values were found in either CSV.
- No full-row duplicate records were found in either CSV.
- No event_id duplicates were found, and case_id values align exactly across both files.
- All event rows are chronologically ordered within case_id in the current file order.
- All statuses in the event log are Completed, so status is not useful as a predictive feature unless later data introduces non-completed states.
- The event timestamp range extends beyond the case start range because case start_time can precede the first logged activity timestamp.
- Repeated Manager Approval, Vendor Confirmation, and Invoice Verification activities appear in 21.67% of cases and should be treated as potential rework rather than duplicates.
- SLA breach labels are present in the case summary. Before ML, confirm whether sla_breached is the target and exclude leakage fields such as duration_hours, duration_days, end_time, and any post-outcome timestamps from predictive feature sets.

## Recommended Next Step for Phase 3

Proceed to process mining and feature engineering. Recommended Phase 3 tasks are: construct case variants and directly-follows paths, quantify rework loops, analyze bottleneck paths by SLA outcome, and create leakage-safe case-level features for later SLA breach prediction. Do not train the model until the feature set and target definition are finalized.
