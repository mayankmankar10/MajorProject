# ui_demo.py
import streamlit as st
import requests
import pandas as pd

# -------------------------------
# CONFIG
# -------------------------------
BACKEND_URL = "http://127.0.0.1:8000/api/scheduler/run"

# Streamlit Page Setup
st.set_page_config(page_title="Manpower Connector - AI Agents Demo", layout="wide")

st.title("🤖 Manpower Connector - Agent Demo Dashboard")
st.caption("Automated Employer ↔ Employee Matching & Interview Scheduling")

# -------------------------------
# UI Controls
# -------------------------------
st.sidebar.header("Agent Controls")
if st.sidebar.button("🚀 Run Scheduler Agent"):
    with st.spinner("Running AI Scheduler Agent... Please wait ⏳"):
        try:
            response = requests.get(BACKEND_URL, timeout=60)
            if response.status_code == 200:
                data = response.json()
                result = data.get("result", {})

                st.success("✅ Scheduler executed successfully!")

                # Summary
                st.subheader("📊 Summary Report")
                summary_df = pd.DataFrame({
                    "Metric": ["Total Jobs", "Total Candidates", "Matches Made", "Interviews Scheduled"],
                    "Count": [
                        result.get("total_jobs", 0),
                        result.get("total_candidates", 0),
                        result.get("matches_made", 0),
                        result.get("interviews_scheduled", 0),
                    ]
                })
                st.table(summary_df)

                # Show interview details
                if "interviews" in result and result["interviews"]:
                    st.subheader("🗓️ Scheduled Interviews")
                    interviews_df = pd.DataFrame(result["interviews"])
                    st.dataframe(interviews_df, use_container_width=True)
                else:
                    st.info("No interviews scheduled yet.")
            else:
                st.error(f"❌ API Error: {response.status_code}")
        except Exception as e:
            st.error(f"⚠️ Backend not reachable: {str(e)}")
else:
    st.info("👈 Click 'Run Scheduler Agent' to begin the demo.")
