

import json
import streamlit as st
import pandas as pd
from src.prediction import predict_sla_risk
 
 
# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------
 
st.set_page_config(
    page_title="P2P SLA Risk Predictor",
    page_icon="📊",
    layout="wide"
)
 
 
# --------------------------------------------------
# SESSION STATE DEFAULTS
# --------------------------------------------------
 
defaults = {
    "purchase_amount": 75000.0,
    "priority": "Low",
    "category": "Software",
    "vendor_id": "V001",
    "elapsed_hours": 120.0,
    "activities_completed": 3,
    "unique_activities": 3,
    "has_budget_review": 0,
    "approval_rework_count": 0,
    "total_rework_events": 0,
    "average_transition_time": 50.0,
    "maximum_transition_time": 80.0,
    "paste_input": "",
    "single_result": None,
    "single_case_data": None,
    "batch_results": None,
    "batch_errors": [],
    "input_method": "⚡ Quick Paste",
}
 
for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value
 
 
# --------------------------------------------------
# RESET / NEW PREDICTION
# --------------------------------------------------
 
def reset_prediction():
    """Clear current results and restore default input values."""
    for key, value in defaults.items():
        st.session_state[key] = value
 
    st.session_state["batch_file_uploader"] = None
 
 
# --------------------------------------------------
# QUICK PASTE PARSER
# --------------------------------------------------
 
def parse_case_text(text):
    parsed = {}
 
    field_mapping = {
        "Purchase Amount": "purchase_amount",
        "Priority": "priority",
        "Category": "category",
        "Vendor": "vendor_id",
        "Elapsed Hours": "elapsed_hours",
        "Activities Completed": "activities_completed",
        "Unique Activities": "unique_activities",
        "Budget Review": "has_budget_review",
        "Approval Rework Count": "approval_rework_count",
        "Total Rework Events": "total_rework_events",
        "Average Transition Time": "average_transition_time",
        "Maximum Transition Time": "maximum_transition_time",
    }
 
    for line in text.splitlines():
        if ":" not in line:
            continue
 
        label, value = line.split(":", 1)
        label = label.strip()
        value = value.strip()
 
        if label in field_mapping:
            parsed[field_mapping[label]] = value
 
    try:
        if "purchase_amount" in parsed:
            parsed["purchase_amount"] = float(parsed["purchase_amount"])
 
        if "elapsed_hours" in parsed:
            parsed["elapsed_hours"] = float(parsed["elapsed_hours"])
 
        if "activities_completed" in parsed:
            parsed["activities_completed"] = int(parsed["activities_completed"])
 
        if "unique_activities" in parsed:
            parsed["unique_activities"] = int(parsed["unique_activities"])
 
        if "approval_rework_count" in parsed:
            parsed["approval_rework_count"] = int(parsed["approval_rework_count"])
 
        if "total_rework_events" in parsed:
            parsed["total_rework_events"] = int(parsed["total_rework_events"])
 
        if "average_transition_time" in parsed:
            parsed["average_transition_time"] = float(
                parsed["average_transition_time"]
            )
 
        if "maximum_transition_time" in parsed:
            parsed["maximum_transition_time"] = float(
                parsed["maximum_transition_time"]
            )
 
        if "has_budget_review" in parsed:
            budget_value = str(parsed["has_budget_review"]).lower()
 
            if budget_value in ["yes", "1", "true"]:
                parsed["has_budget_review"] = 1
            elif budget_value in ["no", "0", "false"]:
                parsed["has_budget_review"] = 0
            else:
                raise ValueError("Budget Review must be Yes or No.")
 
        if "priority" in parsed:
            if parsed["priority"] not in ["Low", "Medium", "High"]:
                raise ValueError("Priority must be Low, Medium, or High.")
 
        if "category" in parsed:
            valid_categories = [
                "Software",
                "Services",
                "Maintenance",
                "Office Supplies",
                "IT Equipment",
            ]
 
            if parsed["category"] not in valid_categories:
                raise ValueError("Invalid category.")
 
        if "vendor_id" in parsed:
            valid_vendors = [f"V{i:03d}" for i in range(1, 51)]
 
            if parsed["vendor_id"] not in valid_vendors:
                raise ValueError(
                    "Vendor must be between V001 and V050."
                )
 
    except (ValueError, TypeError) as e:
        return None, str(e)
 
    return parsed, None
 
 
# --------------------------------------------------
# BATCH JSON
# --------------------------------------------------
 
REQUIRED_JSON_FIELDS = [
    "purchase_amount",
    "priority",
    "category",
    "vendor_id",
    "elapsed_hours_to_purchase_order",
    "activities_completed_to_purchase_order",
    "unique_activities_completed",
    "has_budget_review",
    "approval_rework_count",
    "total_rework_events_so_far",
    "average_transition_time_so_far",
    "maximum_transition_time_so_far",
]
 
DISPLAY_TO_MODEL_FIELDS = {
    "Purchase Amount": "purchase_amount",
    "Priority": "priority",
    "Category": "category",
    "Vendor": "vendor_id",
    "Elapsed Hours": "elapsed_hours_to_purchase_order",
    "Activities Completed": "activities_completed_to_purchase_order",
    "Unique Activities": "unique_activities_completed",
    "Budget Review": "has_budget_review",
    "Approval Rework Count": "approval_rework_count",
    "Total Rework Events": "total_rework_events_so_far",
    "Average Transition Time": "average_transition_time_so_far",
    "Maximum Transition Time": "maximum_transition_time_so_far",
}
 
 
def normalize_json_case(raw_case):
    """Convert JSON data into the exact model input schema."""
    if not isinstance(raw_case, dict):
        raise ValueError("Each JSON record must be an object.")
 
    case = {}
 
    for key, value in raw_case.items():
        mapped_key = DISPLAY_TO_MODEL_FIELDS.get(key, key)
        case[mapped_key] = value
 
    missing = [
        field for field in REQUIRED_JSON_FIELDS
        if field not in case
    ]
 
    if missing:
        raise ValueError(
            "Missing required fields: " + ", ".join(missing)
        )
 
    try:
        case["purchase_amount"] = float(case["purchase_amount"])
 
        case["elapsed_hours_to_purchase_order"] = float(
            case["elapsed_hours_to_purchase_order"]
        )
 
        case["activities_completed_to_purchase_order"] = int(
            case["activities_completed_to_purchase_order"]
        )
 
        case["unique_activities_completed"] = int(
            case["unique_activities_completed"]
        )
 
        case["approval_rework_count"] = int(
            case["approval_rework_count"]
        )
 
        case["total_rework_events_so_far"] = int(
            case["total_rework_events_so_far"]
        )
 
        case["average_transition_time_so_far"] = float(
            case["average_transition_time_so_far"]
        )
 
        case["maximum_transition_time_so_far"] = float(
            case["maximum_transition_time_so_far"]
        )
 
    except (ValueError, TypeError):
        raise ValueError(
            "One or more numeric fields contain invalid values."
        )
 
    budget = str(case["has_budget_review"]).strip().lower()
 
    if budget in ["yes", "1", "true"]:
        case["has_budget_review"] = 1
    elif budget in ["no", "0", "false"]:
        case["has_budget_review"] = 0
    else:
        raise ValueError("Budget Review must be Yes or No.")
 
    if case["priority"] not in ["Low", "Medium", "High"]:
        raise ValueError("Priority must be Low, Medium, or High.")
 
    if case["category"] not in [
        "Software",
        "Services",
        "Maintenance",
        "Office Supplies",
        "IT Equipment",
    ]:
        raise ValueError("Invalid category.")
 
    if case["vendor_id"] not in [
        f"V{i:03d}" for i in range(1, 51)
    ]:
        raise ValueError(
            "Vendor must be between V001 and V050."
        )
 
    return case
 
 
def process_batch_json(records):
    """Predict SLA risk for every JSON record."""
    results = []
    errors = []
 
    for index, raw_case in enumerate(records, start=1):
 
        try:
            case = normalize_json_case(raw_case)
            result = predict_sla_risk(case)
 
            results.append(
                {
                    "Case": index,
                    "Purchase Amount": case["purchase_amount"],
                    "Priority": case["priority"],
                    "Category": case["category"],
                    "Vendor": case["vendor_id"],
                    "Elapsed Hours": case[
                        "elapsed_hours_to_purchase_order"
                    ],
                    "Breach Probability (%)": result[
                        "breach_probability"
                    ],
                    "Risk Level": result["risk_level"],
                    "Predicted SLA Breach": (
                        "Yes"
                        if result["prediction"] == 1
                        else "No"
                    ),
                }
            )
 
        except Exception as e:
 
            errors.append(
                {
                    "Case": index,
                    "Error": str(e),
                }
            )
 
    return results, errors
 
 
# --------------------------------------------------
# CUSTOM STYLING
# --------------------------------------------------
 
st.markdown(
    """
<style>
 
.hero {
    padding: 34px 38px 30px 38px;
    border-radius: 22px;
    margin-bottom: 28px;
    background:
        linear-gradient(
            135deg,
            #172033 0%,
            #10141d 55%,
            #25151a 100%
        );
    border: 1px solid #303848;
    box-shadow: 0 8px 28px rgba(0, 0, 0, 0.22);
}
 
.hero-badge {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.08);
    color: #c9d2e3;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.4px;
    margin-bottom: 14px;
}
 
.hero-title {
    font-size: 42px;
    line-height: 1.1;
    font-weight: 800;
    margin: 0;
    letter-spacing: -1px;
}
 
.hero-title span {
    color: #ff5964;
}
 
.hero-subtitle {
    color: #aeb7c7;
    font-size: 17px;
    margin-top: 12px;
    max-width: 850px;
}
 
.hero-pills {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin-top: 22px;
}
 
.hero-pill {
    padding: 8px 13px;
    border-radius: 10px;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: #d7deea;
    font-size: 13px;
}
 
.section-title {
    font-size: 25px;
    font-weight: 700;
    margin-top: 10px;
    margin-bottom: 12px;
}
 
.risk-card {
    padding: 25px;
    border-radius: 14px;
    margin-top: 18px;
}
 
.high-risk {
    background-color: #3b2025;
    border: 1px solid #7f303b;
}
 
.medium-risk {
    background-color: #40351f;
    border: 1px solid #806b2f;
}
 
.low-risk {
    background-color: #173b2b;
    border: 1px solid #2d7955;
}
 
.risk-text {
    font-size: 27px;
    font-weight: 750;
}
 
.small-text {
    color: #9aa0a6;
    font-size: 14px;
}
 
.batch-banner {
    padding: 18px 20px;
    border-radius: 14px;
    background: #171d29;
    border: 1px solid #303848;
    margin: 8px 0 18px 0;
}
 
.batch-title {
    font-size: 21px;
    font-weight: 700;
}
 
.batch-subtitle {
    color: #aeb7c7;
    margin-top: 5px;
}
 
</style>
""",
    unsafe_allow_html=True,
)
 
 
# --------------------------------------------------
# HERO HEADER
# --------------------------------------------------
# NOTE: every line below starts at column 0. Markdown treats 4+ spaces
# of leading indentation as a code block, which was turning this whole
# banner into a literal <pre> block instead of rendering as HTML.
 
st.markdown(
    """
<div class="hero">
<div class="hero-badge">P2P PROCESS INTELLIGENCE</div>
<div class="hero-title">
📊 P2P <span>SLA Risk</span> Predictor
</div>
</div>
""",
    unsafe_allow_html=True,
)
 
 
# --------------------------------------------------
# INPUT METHOD
# --------------------------------------------------
 
st.markdown(
    '<div class="section-title">📥 Choose Input Method</div>',
    unsafe_allow_html=True,
)
 
input_method = st.radio(
    "How would you like to provide P2P case data?",
    [
        "⚡ Quick Paste",
        "📝 Manual Entry",
        "📦 Batch JSON",
    ],
    horizontal=True,
    key="input_method",
)
 
st.divider()
 
 
# --------------------------------------------------
# QUICK PASTE
# --------------------------------------------------
 
if input_method == "⚡ Quick Paste":
 
    st.markdown(
        '<div class="section-title">⚡ Quick Paste</div>',
        unsafe_allow_html=True,
    )
 
    st.write(
        "Paste one complete P2P case. The values will be extracted "
        "into the fields automatically."
    )
 
    st.text_area(
        "Case Data",
        key="paste_input",
        height=280,
        placeholder="""Purchase Amount: 115025.09
Priority: Low
Category: Maintenance
Vendor: V050
Elapsed Hours: 748.64
Activities Completed: 4
Unique Activities: 3
Budget Review: No
Approval Rework Count: 1
Total Rework Events: 1
Average Transition Time: 243.23
Maximum Transition Time: 657.69""",
    )
 
    if st.button(
        "⚡ Load Case Data",
        use_container_width=True,
    ):
 
        parsed, error = parse_case_text(
            st.session_state.paste_input
        )
 
        if error:
            st.error(f"⚠️ {error}")
 
        elif not parsed:
            st.warning(
                "⚠️ No valid case fields were detected."
            )
 
        else:
 
            for key, value in parsed.items():
                st.session_state[key] = value
 
            st.success(
                f"✅ {len(parsed)} case fields loaded successfully. "
                "Review the values below and run the prediction."
            )
 
 
# --------------------------------------------------
# BATCH JSON
# --------------------------------------------------
 
if input_method == "📦 Batch JSON":
 
    st.markdown(
        '<div class="section-title">📦 Batch JSON Prediction</div>',
        unsafe_allow_html=True,
    )
 
    st.markdown(
        """
<div class="batch-banner">
<div class="batch-title">
Predict multiple P2P cases at once
</div>
<div class="batch-subtitle">
Upload one JSON file containing your cases. The model will
score every case and return a consolidated SLA risk report.
</div>
</div>
""",
        unsafe_allow_html=True,
    )
 
    with st.expander(
        "📄 Required JSON format",
        expanded=False,
    ):
 
        st.code(
            """[
  {
    "purchase_amount": 115025.09,
    "priority": "Low",
    "category": "Maintenance",
    "vendor_id": "V050",
    "elapsed_hours_to_purchase_order": 748.64,
    "activities_completed_to_purchase_order": 4,
    "unique_activities_completed": 3,
    "has_budget_review": 0,
    "approval_rework_count": 1,
    "total_rework_events_so_far": 1,
    "average_transition_time_so_far": 243.23,
    "maximum_transition_time_so_far": 657.69
  }
]""",
            language="json",
        )
 
        st.caption(
            "For 50 cases, place all 50 case objects inside "
            "the same JSON array."
        )
 
    uploaded_file = st.file_uploader(
        "Upload JSON file",
        type=["json"],
        key="batch_file_uploader",
        help="Upload a JSON array containing one or more P2P cases.",
    )
 
    if uploaded_file is not None:
 
        if st.button(
            "🚀 Predict All Cases",
            use_container_width=True,
            type="primary",
        ):
 
            try:
 
                uploaded_file.seek(0)
                data = json.load(uploaded_file)
 
                if isinstance(data, dict) and "cases" in data:
                    records = data["cases"]
                else:
                    records = data
 
                if not isinstance(records, list):
                    raise ValueError(
                        "The JSON must contain a list of case objects."
                    )

                if len(records) > 1000:
                    raise ValueError(
                        "The uploaded JSON contains more than 1,000 cases. "
                        "Please upload 1,000 cases or fewer at a time."
                    )
 
                if not records:
                    raise ValueError(
                        "The uploaded JSON contains no cases."
                    )
 
                results, errors = process_batch_json(records)
 
                st.session_state.batch_results = results
                st.session_state.batch_errors = errors
 
            except json.JSONDecodeError:
 
                st.session_state.batch_results = None
 
                st.session_state.batch_errors = [
                    {
                        "Case": "-",
                        "Error": "Invalid JSON file.",
                    }
                ]
 
            except Exception as e:
 
                st.session_state.batch_results = None
 
                st.session_state.batch_errors = [
                    {
                        "Case": "-",
                        "Error": str(e),
                    }
                ]
 
    # ----------------------------------------------
    # BATCH RESULTS
# ----------------------------------------------

if st.session_state.batch_results is not None:

    batch_df = pd.DataFrame(
        st.session_state.batch_results
    )

    st.markdown(
        '<div class="section-title">'
        '📊 Batch Prediction Results'
        '</div>',
        unsafe_allow_html=True,
    )

    if not batch_df.empty:

        total_cases = len(batch_df)

        high_count = int(
            (batch_df["Risk Level"] == "HIGH RISK").sum()
        )

        medium_count = int(
            (batch_df["Risk Level"] == "MEDIUM RISK").sum()
        )

        low_count = int(
            (batch_df["Risk Level"] == "LOW RISK").sum()
        )

        breach_count = int(
            (batch_df["Predicted SLA Breach"] == "Yes").sum()
        )

        avg_probability = batch_df[
            "Breach Probability (%)"
        ].mean()

        m1, m2, m3, m4, m5 = st.columns(5)

        with m1:
            st.metric("Cases Processed", total_cases)

        with m2:
            st.metric("🔴 High Risk", high_count)

        with m3:
            st.metric("🟡 Medium Risk", medium_count)

        with m4:
            st.metric("🟢 Low Risk", low_count)

        with m5:
            st.metric("Predicted Breaches", breach_count)

        st.caption(
            f"Average predicted breach probability: "
            f"{avg_probability:.2f}%"
        )

        st.divider()

        st.subheader("📈 Risk Distribution")

        risk_distribution = pd.DataFrame(
            {
                "Risk Level": [
                    "HIGH RISK",
                    "MEDIUM RISK",
                    "LOW RISK",
                ],
                "Cases": [
                    high_count,
                    medium_count,
                    low_count,
                ],
            }
        ).set_index("Risk Level")

        st.bar_chart(risk_distribution)

        st.divider()

        st.subheader("🔎 Filter Results")

        filter_col1, filter_col2, filter_col3 = st.columns(3)

        with filter_col1:
            risk_options = sorted(
                batch_df["Risk Level"].dropna().unique()
            )
            selected_risk = st.multiselect(
                "Risk Level",
                risk_options,
                default=risk_options,
            )

        with filter_col2:
            category_options = sorted(
                batch_df["Category"].dropna().unique()
            )
            selected_category = st.multiselect(
                "Category",
                category_options,
                default=category_options,
            )

        with filter_col3:
            vendor_options = sorted(
                batch_df["Vendor"].dropna().unique()
            )
            selected_vendor = st.multiselect(
                "Vendor",
                vendor_options,
                default=vendor_options,
            )

        filtered_df = batch_df[
            batch_df["Risk Level"].isin(selected_risk)
            & batch_df["Category"].isin(selected_category)
            & batch_df["Vendor"].isin(selected_vendor)
        ].copy()

        st.caption(
            f"Showing {len(filtered_df)} of "
            f"{len(batch_df)} processed cases."
        )

        st.dataframe(
            filtered_df,
            use_container_width=True,
            hide_index=True,
        )

        csv_data = filtered_df.to_csv(
            index=False
        ).encode("utf-8")

        st.download_button(
            "⬇️ Download Filtered Results (CSV)",
            data=csv_data,
            file_name="p2p_sla_batch_predictions.csv",
            mime="text/csv",
            use_container_width=True,
        )

    else:
        st.info("No valid cases were processed.")

st.divider()

st.button(
    "🔄 New Prediction",
    use_container_width=True,
    on_click=reset_prediction,
    key="start_new_prediction_button",
)

# SINGLE CASE INPUT
# --------------------------------------------------
 
if input_method in [
    "⚡ Quick Paste",
    "📝 Manual Entry",
]:
 
    st.markdown(
        '<div class="section-title">📋 Case Information</div>',
        unsafe_allow_html=True,
    )
 
    st.write(
        "Review the current values before running the prediction."
    )
 
    col1, col2, col3 = st.columns(3)
 
    with col1:
 
        purchase_amount = st.number_input(
            "Purchase Amount",
            min_value=5000.0,
            step=1000.0,
            key="purchase_amount",
        )
 
        priority = st.selectbox(
            "Priority",
            ["Low", "Medium", "High"],
            key="priority",
        )
 
        category = st.selectbox(
            "Category",
            [
                "Software",
                "Services",
                "Maintenance",
                "Office Supplies",
                "IT Equipment",
            ],
            key="category",
        )
 
    with col2:
 
        vendor_id = st.selectbox(
            "Vendor",
            [f"V{i:03d}" for i in range(1, 51)],
            key="vendor_id",
        )
 
        elapsed_hours = st.number_input(
            "Elapsed Hours to Purchase Order",
            min_value=0.0,
            step=1.0,
            key="elapsed_hours",
        )
 
        activities_completed = st.number_input(
            "Activities Completed",
            min_value=3,
            max_value=5,
            step=1,
            key="activities_completed",
        )
 
        unique_activities = st.number_input(
            "Unique Activities Completed",
            min_value=3,
            max_value=4,
            step=1,
            key="unique_activities",
        )
 
    with col3:
 
        has_budget_review = st.selectbox(
            "Budget Review Completed",
            [0, 1],
            format_func=lambda x: (
                "Yes" if x == 1 else "No"
            ),
            key="has_budget_review",
        )
 
        approval_rework_count = st.number_input(
            "Approval Rework Count",
            min_value=0,
            max_value=10,
            step=1,
            key="approval_rework_count",
        )
 
        total_rework_events = st.number_input(
            "Total Rework Events",
            min_value=0,
            max_value=10,
            step=1,
            key="total_rework_events",
        )
 
        average_transition_time = st.number_input(
            "Average Transition Time (hours)",
            min_value=0.0,
            step=1.0,
            key="average_transition_time",
        )
 
        maximum_transition_time = st.number_input(
            "Maximum Transition Time (hours)",
            min_value=0.0,
            step=1.0,
            key="maximum_transition_time",
        )
 
    st.divider()
 
    action_col1, action_col2 = st.columns(
        [4, 1]
    )
 
    with action_col1:
 
        predict_button = st.button(
            "🔍 Predict SLA Risk",
            use_container_width=True,
            type="primary",
        )
 
    with action_col2:
 
        st.button(
            "🔄 New Prediction",
            use_container_width=True,
            on_click=reset_prediction,
            key="new_prediction_button",
        )
 
    if predict_button:
 
        case_data = {
            "purchase_amount": purchase_amount,
            "priority": priority,
            "category": category,
            "vendor_id": vendor_id,
            "elapsed_hours_to_purchase_order": elapsed_hours,
            "activities_completed_to_purchase_order":
                activities_completed,
            "unique_activities_completed":
                unique_activities,
            "has_budget_review": has_budget_review,
            "approval_rework_count":
                approval_rework_count,
            "total_rework_events_so_far":
                total_rework_events,
            "average_transition_time_so_far":
                average_transition_time,
            "maximum_transition_time_so_far":
                maximum_transition_time,
        }
 
        try:
 
            st.session_state.single_result = (
                predict_sla_risk(case_data)
            )
 
            st.session_state.single_case_data = (
                case_data
            )
 
        except Exception as e:
 
            st.session_state.single_result = None
 
            st.error(
                f"Prediction failed: {e}"
            )
 
 
# --------------------------------------------------
# SINGLE CASE RESULTS
# --------------------------------------------------
 
if (
    input_method in [
        "⚡ Quick Paste",
        "📝 Manual Entry",
    ]
    and st.session_state.single_result is not None
):
 
    result = st.session_state.single_result
 
    probability = result["breach_probability"]
    risk_level = result["risk_level"]
    prediction = result["prediction"]
 
    case_for_display = (
        st.session_state.get(
            "single_case_data",
            {}
        )
        or {}
    )
 
    st.divider()
 
    # --------------------------------------------------
    # RESULT
    # --------------------------------------------------
 
    st.markdown(
        '<div class="section-title">'
        '🎯 Prediction Result'
        '</div>',
        unsafe_allow_html=True,
    )
 
    metric1, metric2, metric3 = st.columns(3)
 
    with metric1:
        st.metric(
            "SLA Breach Probability",
            f"{probability:.2f}%",
        )
 
    with metric2:
        st.metric(
            "Decision Threshold",
            "55%",
        )
 
    with metric3:
        st.metric(
            "Predicted Breach",
            "Yes" if prediction == 1 else "No",
        )
 
    # --------------------------------------------------
    # RISK CARD
    # --------------------------------------------------
 
    if risk_level == "HIGH RISK":
 
        st.markdown(
            """
<div class="risk-card high-risk">
<div class="risk-text">
🔴 HIGH RISK
</div>
<p>
This case has a high probability of breaching the SLA.
Proactive intervention is recommended.
</p>
</div>
""",
            unsafe_allow_html=True,
        )
 
    elif risk_level == "MEDIUM RISK":
 
        st.markdown(
            """
<div class="risk-card medium-risk">
<div class="risk-text">
🟡 MEDIUM RISK
</div>
<p>
This case requires monitoring because its predicted
breach probability exceeds the decision threshold.
</p>
</div>
""",
            unsafe_allow_html=True,
        )
 
    else:
 
        st.markdown(
            """
<div class="risk-card low-risk">
<div class="risk-text">
🟢 LOW RISK
</div>
<p>
The current case characteristics indicate a relatively
low probability of SLA breach.
</p>
</div>
""",
            unsafe_allow_html=True,
        )
 
    # --------------------------------------------------
    # PROBABILITY
    # --------------------------------------------------
 
    st.write("")
    st.subheader("Risk Probability")
 
    st.progress(
        min(probability / 100, 1.0)
    )
 
    st.caption(
        f"Predicted breach probability: "
        f"{probability:.2f}%"
    )
 
    # --------------------------------------------------
    # SHAP EXPLANATION
    # --------------------------------------------------
 
    st.subheader(
        "🔎 Why did the model make this prediction?"
    )
 
    top_features = result.get(
        "top_features",
        []
    )
 
    if top_features:
 
        st.write(
            "The following factors had the strongest influence "
            "on this individual case prediction."
        )
 
        for i, item in enumerate(
            top_features,
            start=1
        ):
 
            feature = item["feature"]
            shap_value = item["shap_value"]
 
            display_name = feature
            display_name = display_name.replace(
                "num__",
                ""
            )
            display_name = display_name.replace(
                "cat__",
                ""
            )
            display_name = display_name.replace(
                "_",
                " "
            )
            display_name = display_name.title()
 
            if shap_value > 0:
                direction = (
                    "Increases SLA breach risk"
                )
                icon = "🔴"
            else:
                direction = (
                    "Decreases SLA breach risk"
                )
                icon = "🟢"
 
            abs_value = abs(shap_value)
 
            if abs_value >= 1.0:
                impact = "Strong"
            elif abs_value >= 0.3:
                impact = "Moderate"
            elif abs_value >= 0.1:
                impact = "Low"
            else:
                impact = "Very Low"
 
            col_a, col_b = st.columns(
                [3, 1]
            )
 
            with col_a:
 
                st.markdown(
                    f"**{i}. {icon} {display_name}**"
                )
 
                st.caption(
                    f"{direction} • {impact} impact"
                )
 
            with col_b:
 
                st.metric(
                    "Impact",
                    f"{shap_value:+.3f}",
                )
 
            if i < len(top_features):
                st.divider()
 
    else:
        st.info(
            "No SHAP explanation was returned "
            "for this case."
        )
 
    # --------------------------------------------------
    # BUSINESS INTERPRETATION
    # --------------------------------------------------
 
    st.subheader(
        "💡 Business Interpretation"
    )
 
    if risk_level == "HIGH RISK":
 
        st.write(
            "The model identifies this case as a high-priority case. "
            "Process owners should investigate the key risk drivers "
            "identified above, particularly process delays, transition "
            "times, and rework activity."
        )
 
    elif risk_level == "MEDIUM RISK":
 
        st.write(
            "The case should be monitored closely. The identified risk "
            "drivers can help process owners determine where early "
            "intervention may prevent an SLA breach."
        )
 
    else:
 
        st.write(
            "The case currently appears to be within a relatively safe "
            "risk range. The identified factors can still be monitored "
            "as the case progresses."
        )
 
    # --------------------------------------------------
    # KEY CASE INDICATORS
    # --------------------------------------------------
 
    st.subheader(
        "📌 Key Case Indicators"
    )
 
    indicator1, indicator2, indicator3, indicator4 = (
        st.columns(4)
    )
 
    with indicator1:
        st.metric(
            "Elapsed Hours",
            f"{case_for_display.get('elapsed_hours_to_purchase_order', 0):.1f}",
        )
 
    with indicator2:
        st.metric(
            "Max Transition",
            f"{case_for_display.get('maximum_transition_time_so_far', 0):.1f} hrs",
        )
 
    with indicator3:
        st.metric(
            "Rework Events",
            case_for_display.get(
                "total_rework_events_so_far",
                0
            ),
        )
 
    with indicator4:
        st.metric(
            "Purchase Amount",
            f"₹{case_for_display.get('purchase_amount', 0):,.0f}",
        )
 
    st.write("")
 
    st.button(
        "🔄 New Prediction",
        use_container_width=True,
        on_click=reset_prediction,
        key="batch_new_prediction_button",
    )
 
 
# --------------------------------------------------
# FOOTER
# --------------------------------------------------
 
st.divider()
 
st.markdown(
    '<div class="small-text">'
    'P2P Process Intelligence • Logistic Regression • '
    'Optimized classification threshold: 0.55'
    '</div>',
    unsafe_allow_html=True,
)
 
