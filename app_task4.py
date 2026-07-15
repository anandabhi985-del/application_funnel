"""
Application Funnel — Live Dashboard (Streamlit)
--------------------------------------------------
Run with:  streamlit run app_task4.py

Company selector + live-updating application funnel (Applied -> Screened ->
Shortlisted -> Interview Scheduled -> Selected), with conversion metrics.
"""

import streamlit as st
import matplotlib.pyplot as plt

from application_funnel import FUNNEL_STAGES, load_data, build_funnel

st.set_page_config(page_title="PlaceMux — Application Funnel", layout="wide")

st.title("PlaceMux — Application Funnel View")
st.caption("Applications & Shortlisting · Task 4 · Application review pipeline")

data = load_data("application_funnel_dataset.csv")
funnel = build_funnel(data)

companies = funnel["company_name"].unique().tolist()
selected_company = st.selectbox("Select a company", companies)

sub = funnel[funnel["company_name"] == selected_company].copy()

top_count = sub.iloc[0]["count"]
selected_count = sub.iloc[-1]["count"]
overall_conv = round((selected_count / top_count * 100), 1) if top_count else 0

col1, col2, col3 = st.columns(3)
col1.metric("Applications received", int(top_count))
col2.metric("Candidates selected", int(selected_count))
col3.metric("Overall conversion", f"{overall_conv}%")

fig, ax = plt.subplots(figsize=(8, 4))
ax.barh(sub["stage"].astype(str), sub["count"], color="#DD8452")
ax.invert_yaxis()
ax.set_xlabel("Applications")
ax.set_title(f"{selected_company} — Application Funnel")
for i, (count, pct) in enumerate(zip(sub["count"], sub["conv_vs_top_%"])):
    ax.text(count, i, f"  {count} ({pct}%)", va="center")
st.pyplot(fig)

st.subheader("Stage-by-stage breakdown")
st.dataframe(
    sub[["stage", "count", "conv_vs_prev_%", "conv_vs_top_%"]]
    .rename(columns={
        "stage": "Stage",
        "count": "Applications",
        "conv_vs_prev_%": "Conversion vs Previous Stage (%)",
        "conv_vs_top_%": "Conversion vs Top of Funnel (%)",
    })
    .reset_index(drop=True)
)

st.subheader("Compare all companies")
pivot = funnel.pivot(index="stage", columns="company_name", values="count")
st.bar_chart(pivot)
