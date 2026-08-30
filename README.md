# 📊 P2P SLA Risk Predictor

An intelligent **Procure-to-Pay (P2P) Process Intelligence application** that predicts the probability of SLA breaches, classifies cases by risk level, and explains the key factors influencing each prediction.

The application combines **Machine Learning, SHAP Explainability, Process Intelligence, and Batch JSON Prediction** to help process owners identify high-risk P2P cases before an SLA breach occurs.

---

## 🚀 Project Overview

SLA breaches in Procure-to-Pay processes can result from process delays, excessive transition times, rework, approval issues, and other operational factors.

This project provides a predictive solution that:

- Predicts the probability of an SLA breach
- Classifies cases into **Low, Medium, and High Risk**
- Identifies the strongest factors influencing each prediction
- Uses **SHAP** to provide model explainability
- Supports prediction of multiple cases through a single JSON file
- Provides an interactive **Streamlit** dashboard
- Helps process owners prioritize cases requiring intervention

---

## 🧠 Machine Learning Approach

The project uses **Logistic Regression** as the classification model.

### Prediction Pipeline

```text
P2P Case Data
      ↓
Data Preprocessing
      ↓
Feature Engineering
      ↓
Logistic Regression
      ↓
SLA Breach Probability
      ↓
Optimized Decision Threshold
      ↓
Risk Classification
      ↓
SHAP Explanation