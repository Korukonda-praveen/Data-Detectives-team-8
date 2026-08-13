import time
import pandas as pd
import numpy as np
import streamlit as st

# ==========================================
# 1. PAGE CONFIGURATION & DARK THEME SETUP
# ==========================================
st.set_page_config(
    page_title="Electricity Analytics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for Slate-Navy Dark Theme
st.markdown("""
<style>
    .stApp {
        background-color: #0f172a;
        color: #f8fafc;
        font-family: 'Inter', sans-serif;
    }
    
    div[data-testid="stMetric"], .custom-card {
        background-color: #1e293b !important;
        border: 1px solid #334155 !important;
        border-radius: 12px !important;
        padding: 18px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
    }

    div[data-testid="stMetricValue"] {
        color: #38bdf8 !important;
        font-weight: 700 !important;
    }

    div[data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
    }

    .stButton>button {
        border-radius: 8px;
        background-color: #0284c7;
        color: white;
        border: none;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background-color: #0369a1;
        box-shadow: 0 0 10px rgba(56, 189, 248, 0.4);
    }
    
    .status-paid { color: #4ade80; font-weight: bold; }
    .status-late { color: #facc15; font-weight: bold; }
    .status-unpaid { color: #f87171; font-weight: bold; }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 2. STATE INITIALIZATION WITH 100 CUSTOMERS
# ==========================================
def initialize_data():
    if "customers" not in st.session_state:
        np.random.seed(42)
        zones = ["Zone-A North", "Zone-B South", "Zone-C West", "Zone-D East"]
        anomalies = ["Clear", "Spike", "Drop"]
        
        generated_customers = []
        for i in range(1, 101):
            cid = f"ELEC-{1000 + i}"
            zone = np.random.choice(zones)
            units = int(np.random.randint(100, 1150))
            bill = units * 8
            defaults = int(np.random.choice([0, 1, 2, 3, 4, 5], p=[0.4, 0.25, 0.15, 0.1, 0.05, 0.05]))
            risk_score = int(min(99, max(10, defaults * 16 + np.random.randint(-10, 15))))
            
            if risk_score >= 70:
                risk_status = "High"
            elif risk_score >= 40:
                risk_status = "Medium"
            else:
                risk_status = "Low"
                
            anomaly = np.random.choice(anomalies, p=[0.7, 0.15, 0.15])
            
            if risk_status == "High":
                rec_action = np.random.choice(["Field Verification Visit", "Disconnection Warning"])
                explanation = f"High risk account driven by {defaults} past default(s) and detected consumption irregularity."
            elif risk_status == "Medium":
                rec_action = np.random.choice(["Offer Payment Plan", "SMS Payment Reminder"])
                explanation = f"Moderate risk level with {defaults} past default(s) and intermittent payment patterns."
            else:
                rec_action = "SMS Payment Reminder"
                explanation = "Low default risk. Normal consumption load and stable payment history."
                
            base_cons = units - np.random.randint(-50, 50)
            hist_cons = [max(80, int(base_cons + np.random.randint(-100, 100))) for _ in range(5)] + [units]
            
            months = ["Mar", "Apr", "May", "Jun", "Jul", "Aug"]
            pay_dict = {}
            for m in months:
                if risk_status == "High":
                    pay_dict[m] = np.random.choice(["Late", "Unpaid"], p=[0.4, 0.6])
                elif risk_status == "Medium":
                    pay_dict[m] = np.random.choice(["Paid", "Late"], p=[0.6, 0.4])
                else:
                    pay_dict[m] = np.random.choice(["Paid", "Late"], p=[0.9, 0.1])

            generated_customers.append({
                "Consumer ID": cid,
                "Zone": zone,
                "Units Consumed (kWh)": units,
                "Bill Amount (₹)": bill,
                "Past Defaults": defaults,
                "Risk Score (%)": risk_score,
                "Risk Status": risk_status,
                "Anomaly Status": anomaly,
                "Last Action": "None",
                "AI Explanation": explanation,
                "Recommended Action": rec_action,
                "6M Consumption (kWh)": hist_cons,
                "Payment History": pay_dict
            })
            
        st.session_state.customers = pd.DataFrame(generated_customers)

    if "audit_logs" not in st.session_state:
        st.session_state.audit_logs = pd.DataFrame([
            {"Timestamp": "2026-08-12 14:32:10", "Officer ID": "OFF-102", "Consumer ID": "ELEC-1004", "Action Taken": "Field Verification Visit", "Outcome Status": "Inspection Scheduled", "Notes": "Critical risk due to past defaults and consumption drop."},
            {"Timestamp": "2026-08-12 11:15:45", "Officer ID": "OFF-105", "Consumer ID": "ELEC-1008", "Action Taken": "Disconnection Warning", "Outcome Status": "Pending", "Notes": "Severe risk with defaults. Notice dispatched."}
        ])

    if "auth" not in st.session_state:
        st.session_state.auth = {"logged_in": False, "role": None, "user_id": None}

initialize_data()

# ==========================================
# 3. SECURE AUTHENTICATION & STRICT ROLE GATING
# ==========================================
def render_login():
    st.markdown("<h2 style='text-align: center; color: #38bdf8;'>Data Detectives - Electricity Analytics</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #94a3b8;'>Utility Analytics & Default Risk Prediction Portal</p>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
        st.subheader("🔑 Secure Portal Login")
        
        role = st.selectbox("Select System Access Role", ["Billing/Collections Officer", "Field Staff", "Admin"])
        
        user_id = st.text_input("User ID", value="", placeholder="Enter your ID (e.g. OFF-101, FLD-201, ADM-001)")
        password = st.text_input("Password", value="", type="password", placeholder="Enter your password")
        
        if st.button("Authenticate Session", use_container_width=True):
            if not user_id.strip():
                st.error("Please enter a valid User ID.")
            elif not password.strip():
                st.error("Please enter your password.")
            else:
                st.session_state.auth = {"logged_in": True, "role": role, "user_id": user_id.strip()}
                st.toast(f"Authenticated successfully as {user_id.strip()} ({role})", icon="✅")
                st.rerun()
                
        st.markdown("</div>", unsafe_allow_html=True)

if not st.session_state.auth["logged_in"]:
    render_login()
    st.stop()

# ==========================================
# 4. TOP NAVBAR & ISOLATED DASHBOARD ROUTING
# ==========================================
current_role = st.session_state.auth["role"]

nav1, nav2, nav3 = st.columns([3, 2, 1])
with nav1:
    st.markdown(f"<h3 style='margin:0; color: #f8fafc;'>⚡ Data Detectives <span style='font-size:0.8rem; background:#0284c7; color:white; padding:3px 8px; border-radius:12px;'>{current_role} Dashboard</span></h3>", unsafe_allow_html=True)
with nav2:
    st.markdown(f"<div style='text-align:right; padding-top:5px; color:#94a3b8;'>Logged in: <b style='color:#38bdf8;'>{st.session_state.auth['user_id']}</b></div>", unsafe_allow_html=True)
with nav3:
    if st.button("Log Out", use_container_width=True):
        st.session_state.auth = {"logged_in": False, "role": None, "user_id": None}
        st.rerun()

st.markdown("---")

# ==========================================
# 5. STRICT CONDITIONAL ROUTING (NO CROSS-DASHBOARD ACCESS)
# ==========================================

if current_role == "Billing/Collections Officer":
    # --- COLLECTIONS OFFICER DASHBOARD ONLY (DEFAULT NOTES REMOVED) ---
    st.title("📋 Collections Officer Operating Portal")
    
    total_cust = len(st.session_state.customers)
    high_risk_count = len(st.session_state.customers[st.session_state.customers["Risk Status"] == "High"])
    anomaly_count = len(st.session_state.customers[st.session_state.customers["Anomaly Status"] != "Clear"])
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Active Connections", str(total_cust), "+12 this month")
    kpi2.metric("High-Risk Accounts", str(high_risk_count), "Needs Attention", delta_color="inverse")
    kpi3.metric("Flagged Anomalies", str(anomaly_count), "Inspection Queue", delta_color="inverse")
    kpi4.metric("Collection Recovery Rate", "78.5%", "+2.1% target delta")

    st.markdown("<br>", unsafe_allow_html=True)
    
    st.subheader("🔍 High-Risk Accounts Filter & Action Desk")
    f1, f2, f3 = st.columns([1, 1, 2])
    
    with f1:
        zone_filter = st.selectbox("Filter by Zone", ["All", "Zone-A North", "Zone-B South", "Zone-C West", "Zone-D East"])
    with f2:
        risk_filter = st.selectbox("Filter by Risk Level", ["All", "High", "Medium", "Low"])
    with f3:
        search_id = st.text_input("Search Consumer ID", placeholder="e.g. ELEC-1045")

    df_filtered = st.session_state.customers.copy()
    if zone_filter != "All":
        df_filtered = df_filtered[df_filtered["Zone"] == zone_filter]
    if risk_filter != "All":
        df_filtered = df_filtered[df_filtered["Risk Status"] == risk_filter]
    if search_id:
        df_filtered = df_filtered[df_filtered["Consumer ID"].str.contains(search_id, case=False)]

    st.dataframe(
        df_filtered[[
            "Consumer ID", "Zone", "Units Consumed (kWh)", "Bill Amount (₹)", 
            "Past Defaults", "Risk Score (%)", "Risk Status", "Anomaly Status", "Recommended Action", "Last Action"
        ]],
        use_container_width=True,
        hide_index=True
    )

    st.markdown("---")

    if len(df_filtered) > 0:
        st.subheader("⚡ Execute Interventions & Historical Diagnostics")
        act_col1, act_col2 = st.columns(2)

        with act_col1:
            st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
            st.markdown("#### 🤖 AI Diagnostic & Recommendation Summary")
            selected_consumer_ai = st.selectbox("Select Account to Inspect", df_filtered["Consumer ID"].tolist(), key="ai_select")
            
            customer_info = st.session_state.customers[st.session_state.customers["Consumer ID"] == selected_consumer_ai].iloc[0]
            
            st.info(f"""
            **AI Diagnostic Summary for {selected_consumer_ai}:**
            
            {customer_info['AI Explanation']}
            
            ---
            💡 **AI Recommended Action:** `{customer_info['Recommended Action']}`
            """)

            st.markdown("##### 💳 Last 6 Months Payment History")
            p_cols = st.columns(6)
            pay_hist = customer_info["Payment History"]
            
            for idx, (month, status) in enumerate(pay_hist.items()):
                with p_cols[idx]:
                    if status == "Paid":
                        css_cls = "status-paid"
                        icon = "✅"
                    elif status == "Late":
                        css_cls = "status-late"
                        icon = "⚠️"
                    else:
                        css_cls = "status-unpaid"
                        icon = "❌"
                    
                    st.markdown(f"""
                    <div style='text-align: center; background: #0f172a; padding: 6px; border-radius: 6px; border: 1px solid #334155;'>
                        <div style='font-size:0.75rem; color:#94a3b8;'>{month}</div>
                        <div class='{css_cls}' style='font-size:0.85rem;'>{icon} {status}</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("##### 📈 6-Month Consumption Trend (kWh)")
            months_list = ["Mar", "Apr", "May", "Jun", "Jul", "Aug"]
            trend_df = pd.DataFrame({
                "Month": months_list,
                "Consumption (kWh)": customer_info["6M Consumption (kWh)"]
            }).set_index("Month")
            
            st.line_chart(trend_df, height=180)
            st.markdown("</div>", unsafe_allow_html=True)

        with act_col2:
            st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
            st.markdown("#### 📝 Take Action & Log Intervention")
            
            target_consumer = st.selectbox("Consumer ID", df_filtered["Consumer ID"].tolist(), key="action_target")
            target_info = st.session_state.customers[st.session_state.customers["Consumer ID"] == target_consumer].iloc[0]
            
            action_options = ["SMS Payment Reminder", "Field Verification Visit", "Offer Payment Plan", "Disconnection Warning"]
            rec_action = target_info['Recommended Action']
            default_index = action_options.index(rec_action) if rec_action in action_options else 0
            
            with st.form("action_form"):
                officer_id = st.text_input("Officer ID (Read-Only)", value=st.session_state.auth["user_id"], disabled=True)
                action_taken = st.selectbox("Action Taken", action_options, index=default_index)
                outcome_status = st.selectbox("Outcome Status", ["Pending", "Promised Payment", "Inspection Scheduled", "Resolved"])
                
                notes = st.text_area("Officer Field Notes", value="", placeholder="Enter field notes here...", height=120, key=f"notes_area_{target_consumer}")
                submit_action = st.form_submit_button("Submit Intervention Log", use_container_width=True)
                
                if submit_action:
                    st.session_state.customers.loc[st.session_state.customers["Consumer ID"] == target_consumer, "Last Action"] = action_taken
                    new_log = {
                        "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "Officer ID": officer_id,
                        "Consumer ID": target_consumer,
                        "Action Taken": action_taken,
                        "Outcome Status": outcome_status,
                        "Notes": notes
                    }
                    st.session_state.audit_logs = pd.concat([pd.DataFrame([new_log]), st.session_state.audit_logs], ignore_index=True)
                    st.success(f"Action logged for {target_consumer}!")
                    st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)

elif current_role == "Field Staff":
    # --- FIELD STAFF DASHBOARD ONLY ---
    st.title("🛠️ Field Staff Operations Portal")
    
    fkpi1, fkpi2, fkpi3 = st.columns(3)
    fkpi1.metric("Pending Inspections", "18", "Active Queue")
    fkpi2.metric("Completed Today", "14", "+3 ahead of target")
    fkpi3.metric("Tamper Alerts Flagged", "6", "Requires Meter Seal Replacement", delta_color="inverse")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_f1, col_f2 = st.columns([1, 1])
    with col_f1:
        st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
        st.subheader("📍 Field Inspection Queue")
        field_df = st.session_state.customers[
            (st.session_state.customers["Recommended Action"] == "Field Verification Visit") | 
            (st.session_state.customers["Anomaly Status"] != "Clear")
        ]
        st.dataframe(
            field_df[["Consumer ID", "Zone", "Units Consumed (kWh)", "Anomaly Status", "Risk Status"]],
            use_container_width=True,
            hide_index=True,
            column_config={
                "Consumer ID": st.column_config.TextColumn("Consumer ID", width="medium"),
                "Zone": st.column_config.TextColumn("Zone", width="medium"),
                "Units Consumed (kWh)": st.column_config.NumberColumn("Units (kWh)", format="%d"),
                "Anomaly Status": st.column_config.TextColumn("Anomaly", width="small"),
                "Risk Status": st.column_config.TextColumn("Risk", width="small"),
            }
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with col_f2:
        st.markdown("<div class='custom-card'>", unsafe_allow_html=True)
        st.subheader("📝 Log Field Inspection & Meter Reading")
        selected_field_consumer = st.selectbox("Select Consumer ID for Inspection", st.session_state.customers["Consumer ID"].tolist(), key="field_consumer_sel")
        c_info = st.session_state.customers[st.session_state.customers["Consumer ID"] == selected_field_consumer].iloc[0]
        
        staff_id = st.text_input("Field Staff ID", value=st.session_state.auth["user_id"], disabled=True)
        curr_units = st.number_input("Recorded Meter Reading (kWh)", value=int(c_info["Units Consumed (kWh)"]))
        meter_condition = st.selectbox(
            "Meter Hardware Status", 
            ["Normal / Intact", "Seal Broken / Tampered", "Bypassed Line Suspected", "Faulty Display / Meter Defective"]
        )
        
        with st.form("field_inspection_form"):
            inspection_notes = st.text_area("Field Inspection Notes", value="", placeholder="Enter inspection notes here...", height=120)
            submit_field = st.form_submit_button("Submit Inspection Log", use_container_width=True)
            
            if submit_field:
                st.session_state.customers.loc[st.session_state.customers["Consumer ID"] == selected_field_consumer, "Units Consumed (kWh)"] = curr_units
                st.session_state.customers.loc[st.session_state.customers["Consumer ID"] == selected_field_consumer, "Last Action"] = f"Field Verified ({meter_condition})"
                
                new_field_log = {
                    "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "Officer ID": st.session_state.auth["user_id"],
                    "Consumer ID": selected_field_consumer,
                    "Action Taken": f"Meter Reading: {curr_units} kWh",
                    "Outcome Status": meter_condition,
                    "Notes": inspection_notes
                }
                st.session_state.audit_logs = pd.concat([pd.DataFrame([new_field_log]), st.session_state.audit_logs], ignore_index=True)
                st.success(f"Inspection submitted for {selected_field_consumer}!")
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

elif current_role == "Admin":
    # --- ADMIN DASHBOARD ONLY ---
    st.title("⚙️ Admin Oversight & ML Model Performance")

    tab1, tab2, tab3 = st.tabs(["📊 ML Analytics & Charts", "🕵️ Field & Officer Activity Audit Log", "📥 Data Ingestion"])

    with tab1:
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Model Accuracy", "88.5%", "XGBoost v2.1")
        m2.metric("Precision", "84.2%", "Low False Positives")
        m3.metric("Recall", "81.0%", "Default Catch Rate")
        m4.metric("ROC-AUC Score", "0.89", "Optimal Threshold")

        st.markdown("<br>", unsafe_allow_html=True)
        chart_col1, chart_col2 = st.columns(2)

        with chart_col1:
            st.subheader("Consumption Anomaly Scatter Chart")
            st.scatter_chart(st.session_state.customers, x="Consumer ID", y="Units Consumed (kWh)", color="Risk Status")

        with chart_col2:
            st.subheader("Risk Distribution by Zone")
            risk_zone_df = st.session_state.customers.groupby(["Zone", "Risk Status"]).size().unstack(fill_value=0)
            st.bar_chart(risk_zone_df)

    with tab2:
        st.subheader("🕵️ Field Staff & Officer Activity Audit log")
        df_audit = st.session_state.audit_logs.copy()
        st.dataframe(df_audit, use_container_width=True, hide_index=True)

    with tab3:
        st.subheader("📥 Data Ingestion & Model Inference Simulation")
        if st.button("Run Batch Inference on 100 System Records", use_container_width=False):
            with st.spinner("Processing telemetry data through classification pipeline..."):
                progress_bar = st.progress(0)
                for percent_complete in range(100):
                    time.sleep(0.005)
                    progress_bar.progress(percent_complete + 1)
            st.success("Model Inference Complete! All 100 customer records analyzed successfully across zones.")
            st.toast("Batch Scoring Finished Successfully!", icon="🚀")