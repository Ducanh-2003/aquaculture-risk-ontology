import streamlit as st
import pandas as pd
import plotly.express as px
import joblib
import os

st.set_page_config(
    page_title="AQUA-RISK Dashboard",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
.alert-box-high {
    background-color: #ffe6e6;
    border-left: 8px solid #ff0000;
    padding: 20px;
    border-radius: 5px;
    margin-bottom: 15px;
    animation: blinker 1.5s linear infinite;
}
@keyframes blinker {
  50% { opacity: 0.85; }
}
.alert-box-shacl {
    background-color: #fff3cd;
    border-left: 8px solid #ffa500;
    padding: 20px;
    border-radius: 5px;
    margin-bottom: 15px;
}
.alert-box-medium {
    background-color: #fff8e6;
    border-left: 8px solid #ffcc00;
    padding: 20px;
    border-radius: 5px;
    margin-bottom: 15px;
}
.alert-box-safe {
    background-color: #e6ffed;
    border-left: 8px solid #00c04b;
    padding: 20px;
    border-radius: 5px;
    margin-bottom: 15px;
}
.metric-card {
    background-color: #f8f9fa;
    padding: 15px;
    border-radius: 10px;
    border: 1px solid #dee2e6;
    text-align: center;
}
</style>
""", unsafe_allow_html=True)

# Load dataset
@st.cache_data
def load_pipeline_data():
    if not os.path.exists("Dataset_Mocked_MultiPond.csv"):
        return pd.DataFrame()

    df = pd.read_csv("Dataset_Mocked_MultiPond.csv")
    df["Timestamp"] = pd.to_datetime(df["Timestamp"])
    df = df.sort_values(by=["Pond_ID", "Timestamp"]).reset_index(drop=True)

    return df

@st.cache_data
def build_sliding_window(df):
    env_cols = ["Temp", "DO", "pH", "Turbidity"]

    kg_cols = [
        "RiskLevel_encoded",
        "DataConfidenceScore",
        "RiskFactorsCount",
        "HighRisk_Triggered",
        "MediumRisk_Triggered",
        "SHACL_Violation_Count",
        "SHACL_pH_Violation",
        "SHACL_DO_Violation"
    ]

    feature_cols = []
    window_steps = [1, 2, 3, 4, 5, 6]

    for col in env_cols + kg_cols:
        if col in df.columns:
            for i in window_steps:
                t_col = f"{col}_t-{i}"
                df[t_col] = df.groupby("Pond_ID")[col].shift(i)
                feature_cols.append(t_col)

    df = df.dropna(subset=feature_cols).reset_index(drop=True)

    return df, feature_cols

df_pipeline = load_pipeline_data()

if df_pipeline.empty:
    st.error("Không tìm thấy file Dataset_Mocked_MultiPond.csv")
    st.stop()

df_pipeline, feature_cols = build_sliding_window(df_pipeline)

# Load models
def load_pickle(path):
    return joblib.load(path) if os.path.exists(path) else None

classifier_model = load_pickle("best_classifier_model.pkl")
classifier_features = load_pickle("classifier_features.pkl")

regressor_model = load_pickle("best_regressor_model.pkl")
regressor_features = load_pickle("regressor_features.pkl")

# SHACL validation
def evaluate_realtime_shacl(temp, do, ph, turb):

    violations = []
    ph_violation = 0
    do_violation = 0
    temp_violation = 0
    turb_violation = 0

    # 1. pH (0–14 + required)
    if ph is None or ph < 0 or ph > 14:
        ph_violation = 1
        violations.append("SHACL: pH out of valid range [0–14] or missing value")

    # 2. DO (required + must not be negative)
    if do is None or do < 0:
        do_violation = 1
        violations.append("SHACL: Dissolved Oxygen missing or negative value detected")

    # 3. Temperature (only check missing sensor)
    if temp is None:
        temp_violation = 1
        violations.append("SHACL: Temperature sensor disconnected or missing data")

    # 4. Turbidity (must be >= 0)
    if turb is None or turb < 0:
        turb_violation = 1
        violations.append("SHACL: Turbidity sensor error (negative or missing value)")

    total_viol = ph_violation + do_violation + temp_violation + turb_violation

    # confidence score
    if total_viol == 0:
        score = 1.0
    elif total_viol == 1:
        score = 0.75
    elif total_viol == 2:
        score = 0.5
    else:
        score = 0.25

    return total_viol, ph_violation, do_violation, temp_violation, turb_violation, score, violations

# SWRL reasoning
def evaluate_realtime_swrl(temp, do, turb, cases, oxy):

    triggered_rules = []
    high_risk = False

    # High Risk Rules
    if cases > 2 and oxy == 0:
        triggered_rules.append(
            "High Risk detected: Disease cases are increasing (>2) and no oxygenation intervention is applied."
        )
        high_risk = True

    if do < 6 and temp > 29:
        triggered_rules.append(
            "High Risk detected: Dissolved oxygen is critically low (<6 mg/L) while temperature is high (>29°C), creating lethal conditions for aquatic life."
        )
        high_risk = True

    if turb > 4:
        triggered_rules.append(
            "High Risk detected: Water turbidity is extremely high (>4 NTU), indicating severe pollution or suspended solids."
        )
        high_risk = True

    # Medium Risk Rules
    if cases == 2 and oxy == 0:
        triggered_rules.append(
            "Medium Risk detected: Disease occurrence at threshold level with no oxygenation intervention."
        )

    if 28.35 < temp <= 29 and 6 <= do <= 6.34:
        triggered_rules.append(
            "Medium Risk detected: Environmental stress detected. Temperature is elevated (28.35-29°C) and DO is at critical threshold (6-6.34 mg/L)."
        )

    if 3.71 < turb <= 4:
        triggered_rules.append(
            "Medium Risk detected: Water turbidity is moderately high (3.71-4 NTU), turbidity is approaching unsafe levels."
        )

    # Risk Classification
    if high_risk:
        risk = "High"
    elif len(triggered_rules) > 0:
        risk = "Medium"
    else:
        risk = "Low"
        triggered_rules = [
            "SAFE: All environmental and biological parameters are stable."
        ]

    return risk, triggered_rules

# Dashboard
st.title("AQUA-RISK PROACTIVE EARLY WARNING SYSTEM")
st.caption("Real-time SWRL/SHACL Ontology Monitoring & Machine Learning Predictions")

st.sidebar.markdown("---")
st.sidebar.header("Location Selection")

selected_pond = st.sidebar.selectbox(
    "Select Target Pond",
    options=df_pipeline["Pond_ID"].unique()
)

df_pond = (
    df_pipeline[df_pipeline["Pond_ID"] == selected_pond]
    .sort_values("Timestamp")
)

current_record = df_pond.iloc[-1].copy()


# Real-time ontology alerts
st.header("1. REAL-TIME ONTOLOGY ALERTS")

if current_record["SHACL_Violation_Count"] > 0:

    shacl_msg = "HARDWARE INTEGRITY WARNING (SHACL Detected): "

    if current_record["SHACL_pH_Violation"] > 0:
        shacl_msg += f"Invalid pH reading ({current_record['pH']}). "

    if current_record["SHACL_DO_Violation"] > 0:
        shacl_msg += f"Negative DO reading ({current_record['DO']}). "

    st.markdown(
        f'''
        <div class="alert-box-shacl">
        {shacl_msg}
        <br>
        <em>
        Action: Check sensor calibration immediately.
        Data confidence reduced to
        {current_record["DataConfidenceScore"]*100}%.
        </em>
        </div>
        ''',
        unsafe_allow_html=True
    )

else:
    st.markdown(
        '<div class="alert-box-safe">Sensor Integrity: Data is Verified. No physical violations detected.</div>',
        unsafe_allow_html=True
    )

risk_level, triggered_rules = evaluate_realtime_swrl(
    current_record["Temp"],
    current_record["DO"],
    current_record["Turbidity"],
    current_record["DiseaseOccurrence"],
    current_record.get("OxygenationInterventions", 0)
)

risk_label = {"High": "HIGH RISK", "Medium": "MEDIUM RISK", "Low": "LOW RISK"}
risk_class  = {"High": "alert-box-high", "Medium": "alert-box-medium", "Low": "alert-box-safe"}

st.markdown(
    f'<div class="{risk_class[risk_level]}">'
    f'<strong>{risk_label[risk_level]}</strong><br>'
    f'{"; ".join(triggered_rules)}'
    f'</div>',
    unsafe_allow_html=True
)

st.markdown("---")

# Phân biệt cảnh báo sensor lỗi vs rủi ro dịch bệnh
if current_record["SHACL_Violation_Count"] > 0:
    st.info("Note: Active SHACL violations detected — above risk assessment "
            "may be based on degraded sensor data. Verify sensor calibration before acting.")

# Machine learning predictions
st.header("2. MACHINE LEARNING PREDICTIONS (NEXT 4 HOURS)")

pred_class = 0
pred_cases = 0.0

if classifier_model and classifier_features:
    try:
        X_clf = pd.DataFrame([current_record[classifier_features]])
        pred_class = int(classifier_model.predict(X_clf)[0])
    except:
        pass

if regressor_model and regressor_features:
    try:
        X_reg = pd.DataFrame([current_record[regressor_features]])
        pred_cases = float(regressor_model.predict(X_reg)[0])
    except:
        pass

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Model Confidence Score",
        f"{current_record['DataConfidenceScore']*100:.0f}%"
    )

with col2:
    status_text = (
        "OUTBREAK EXPECTED"
        if pred_class == 1
        else "STABLE EXPECTED"
    )
    st.metric("Predicted Next State", status_text)

with col3:
    st.metric(
        "Predicted Disease Occurrence Level",
        f"{pred_cases:.2f}"
    )

st.markdown("---")

# Time-series charts
st.header("3. TIME-SERIES MONITORING CHARTS")

g1, g2 = st.columns(2)
g3, g4 = st.columns(2)

with g1:
    fig_do = px.line(
        df_pond,
        x="Timestamp",
        y="DO",
        title="Dissolved Oxygen (mg/L)",
        markers=True
    )
    fig_do.add_hline(y=6.0, line_dash="dash", line_color="red")
    st.plotly_chart(fig_do, use_container_width=True)

with g2:
    fig_temp = px.line(
        df_pond,
        x="Timestamp",
        y="Temp",
        title="Temperature (°C)",
        markers=True
    )
    fig_temp.add_hline(y=29.0, line_dash="dash", line_color="red")
    st.plotly_chart(fig_temp, use_container_width=True)

with g3:
    fig_disease = px.line(
        df_pond,
        x="Timestamp",
        y="DiseaseOccurrence",
        title="Disease Cases Over Time",
        markers=True
    )
    fig_disease.add_hline(
        y=101,
        line_dash="dash",
        annotation_text="Pandemic Threshold (P90)"
    )
    st.plotly_chart(fig_disease, use_container_width=True)

with g4:
    fig_turb = px.line(
        df_pond,
        x="Timestamp",
        y="Turbidity",
        title="Turbidity (NTU)",
        markers=True
    )
    fig_turb.add_hline(
        y=50.0,
        line_dash="dash",
        annotation_text="SWRL Turbidity Threshold"
    )
    st.plotly_chart(fig_turb, use_container_width=True)

st.markdown("---")
st.header("4. MANUAL OBSERVATION INPUT (Early Warning Simulation)")
with st.expander("Simulate a custom observation"):
    col_a, col_b = st.columns(2)
    with col_a:
        sim_temp = st.slider(
            "Temperature (°C)",
            -10.0, 50.0, 28.0, 0.1
        )

        sim_do = st.slider(
            "DO (mg/L)",
            -5.0, 20.0, 6.5, 0.1
        )

        sim_pH = st.slider(
            "pH",
            -2.0, 16.0, 7.0, 0.1
        )

    with col_b:
        sim_turb = st.slider(
            "Turbidity (NTU)",
            -5.0, 20.0, 2.0, 0.1
        )

        sim_cases = st.number_input(
            "Disease Occurrence",
            0, 10, 1
        )

        sim_oxy = st.selectbox(
            "Oxygenation Intervention?",
            [0, 1]
        )
    
    sim_risk, sim_rules = evaluate_realtime_swrl(
        sim_temp, sim_do, sim_turb, sim_cases, sim_oxy
    )
    viol_count, ph_v, do_v, temp_v, turb_v, score, viol_list = evaluate_realtime_shacl(
        sim_temp, sim_do, sim_pH, sim_turb
    )
    
    st.markdown(f"**Simulated Risk Level: `{sim_risk}`**")
    for r in sim_rules:
        st.write(f"- {r}")

    # DISPLAY SHACL RESULT
    st.markdown("### SHACL Data Quality Validation")

    if viol_count == 0:
        st.success("All sensor readings are valid according to SHACL constraints.")
    else:
        for v in viol_list:
            st.warning(v)


# Raw dataset
with st.expander("View Raw Monitoring Dataset"):

    display_cols = [
        "Timestamp",
        "Temp",
        "DO",
        "pH",
        "Turbidity",
        "DiseaseOccurrence",
        "RiskLevel",
        "SHACL_Violation_Count"
    ]

    st.dataframe(
        df_pond[display_cols]
        .sort_values(by="Timestamp", ascending=False)
        .head(15)
        .style.format({
            "Temp": "{:.2f}",
            "DO": "{:.2f}",
            "pH": "{:.2f}",
            "Turbidity": "{:.2f}"
        })
    )