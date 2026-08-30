import joblib
import pandas as pd
import shap
from pathlib import Path


# Find the project root
PROJECT_ROOT = Path(__file__).resolve().parents[1]


# --------------------------------------------------
# LOAD SAVED ML ARTIFACTS
# --------------------------------------------------

PREPROCESSOR_PATH = (
    PROJECT_ROOT / "models" / "p2p_preprocessor.joblib"
)

MODEL_PATH = (
    PROJECT_ROOT / "models" / "p2p_logistic_regression.joblib"
)

THRESHOLD_PATH = (
    PROJECT_ROOT / "models" / "p2p_threshold.joblib"
)


preprocessor = joblib.load(
    PREPROCESSOR_PATH
)

model = joblib.load(
    MODEL_PATH
)

threshold = joblib.load(
    THRESHOLD_PATH
)


# --------------------------------------------------
# SHAP BACKGROUND DATA
# --------------------------------------------------

BACKGROUND_DATA_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "p2p_ml_dataset.csv"
)


# Load the processed P2P dataset
background_df = pd.read_csv(
    BACKGROUND_DATA_PATH
)


# Get the columns that were used by the preprocessor
expected_columns = list(
    preprocessor.feature_names_in_
)


# Keep only the model input columns
background_df = background_df[
    expected_columns
].copy()


# Use a representative sample of real P2P cases
background_df = background_df.sample(
    n=min(100, len(background_df)),
    random_state=42
)


# Apply the same preprocessing used during training
background_processed = preprocessor.transform(
    background_df
)


# --------------------------------------------------
# SHAP EXPLAINER
# --------------------------------------------------

explainer = shap.LinearExplainer(
    model,
    background_processed
)


# Get names of processed features
feature_names = (
    preprocessor.get_feature_names_out()
)


# --------------------------------------------------
# PREDICTION FUNCTION
# --------------------------------------------------

def predict_sla_risk(case_data):
    """
    Predict SLA breach risk for one P2P case
    and provide SHAP-based explanations.
    """

    case_df = pd.DataFrame(
        [case_data]
    )


    # --------------------------------------------------
    # APPLY PREPROCESSING
    # --------------------------------------------------

    processed_case = preprocessor.transform(
        case_df
    )


    # --------------------------------------------------
    # PREDICT PROBABILITY
    # --------------------------------------------------

    probability = model.predict_proba(
        processed_case
    )[0, 1]


    # --------------------------------------------------
    # APPLY OPTIMIZED THRESHOLD
    # --------------------------------------------------

    prediction = int(
        probability >= threshold
    )


    # --------------------------------------------------
    # BUSINESS RISK LEVEL
    # --------------------------------------------------

    if probability >= 0.70:

        risk_level = "HIGH RISK"

    elif probability >= threshold:

        risk_level = "MEDIUM RISK"

    else:

        risk_level = "LOW RISK"


    # --------------------------------------------------
    # SHAP EXPLANATION
    # --------------------------------------------------

    shap_result = explainer(
        processed_case
    )


    shap_values = shap_result.values[0]


    # Create explanation dataframe
    explanation_df = pd.DataFrame({

        "feature": feature_names,

        "shap_value": shap_values

    })


    # Absolute SHAP value determines importance
    explanation_df["abs_shap"] = (
        explanation_df["shap_value"].abs()
    )


    # Sort strongest contributors first
    explanation_df = explanation_df.sort_values(
        "abs_shap",
        ascending=False
    )


    # Keep top 5 contributors
    top_features = (
        explanation_df
        .head(5)
        .copy()
    )


    # --------------------------------------------------
    # RETURN RESULT
    # --------------------------------------------------

    return {

        "breach_probability": round(
            probability * 100,
            2
        ),

        "prediction": prediction,

        "risk_level": risk_level,

        "top_features": top_features[
            ["feature", "shap_value"]
        ].to_dict("records")

    }