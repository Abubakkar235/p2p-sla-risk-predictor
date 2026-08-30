# Phase 5 — SLA Breach Prediction & Model Training Report

## 1. Objective

The objective of Phase 5 is to develop a machine learning model that predicts whether a Procure-to-Pay (P2P) case is likely to breach its SLA.

The model is designed to identify high-risk cases early enough to support proactive process intervention.

---

## 2. Dataset

The feature-engineered dataset contains:

- 20,000 P2P cases
- 17 columns
- One row per case
- Target variable: `sla_breached`

Target distribution:

| Outcome | Count | Percentage |
|---|---:|---:|
| No SLA breach | 15,986 | 79.93% |
| SLA breach | 4,014 | 20.07% |

The dataset therefore contains a class imbalance, with SLA breaches representing approximately 20% of cases.

---

## 3. Prediction Point

The prediction point is the Purchase Order stage.

The model uses information available up to the prediction timestamp and excludes features that would introduce future information or data leakage.

The following columns were treated as audit/reference fields rather than predictive features:

- `case_id`
- `prediction_timestamp`
- `purchase_order_event_id`

Potential leakage columns such as final case duration were excluded from model features.

---

## 4. Train, Validation and Test Split

The data was divided chronologically into three datasets:

| Dataset | Records | Percentage |
|---|---:|---:|
| Training | 14,000 | 70% |
| Validation | 3,000 | 15% |
| Test | 3,000 | 15% |

The chronological split was used to better represent a realistic prediction scenario in which historical cases are used to predict future cases.

The SLA breach rate remained approximately 20% across all three datasets, indicating a consistent target distribution.

---

## 5. Input Features

The model uses 12 predictive input features:

- `purchase_amount`
- `priority`
- `category`
- `vendor_id`
- `elapsed_hours_to_purchase_order`
- `activities_completed_to_purchase_order`
- `unique_activities_completed`
- `has_budget_review`
- `approval_rework_count`
- `total_rework_events_so_far`
- `average_transition_time_so_far`
- `maximum_transition_time_so_far`

Categorical variables were transformed using one-hot encoding, while numerical variables were passed through the preprocessing pipeline.

The resulting model matrix contained 67 features.

---

## 6. Models Evaluated

Three classification algorithms were evaluated:

1. Logistic Regression
2. Random Forest
3. XGBoost

The primary evaluation focus was SLA-breach class performance because identifying actual breach cases is the main business objective.

---

## 7. Model Comparison

The following results were obtained on the validation dataset using the selected/tuned model configurations:

| Model | Precision | Recall | F1 | ROC-AUC |
|---|---:|---:|---:|---:|
| Logistic Regression | 0.377 | 0.697 | **0.490** | **0.781** |
| Random Forest | 0.386 | 0.618 | 0.475 | 0.768 |
| XGBoost | **0.699** | 0.224 | 0.339 | 0.774 |

### Model Selection

Logistic Regression was selected as the final model.

Although XGBoost achieved substantially higher precision, its recall for SLA breaches was only 22.4%. This means that it missed a large proportion of actual breach cases.

Logistic Regression achieved:

- Highest breach recall: 69.7%
- Highest breach F1-score: 49.0%
- Highest ROC-AUC: 0.781

Because the business objective is to identify as many potential SLA breaches as reasonably possible, Logistic Regression provides the most suitable balance between precision and recall.

---

## 8. Hyperparameter Tuning

Logistic Regression hyperparameters were optimized using cross-validation.

The selected configuration was:

```text
C = 0.1