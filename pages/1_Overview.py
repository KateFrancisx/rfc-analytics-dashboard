import streamlit as st
import pandas as pd
import plotly.express as px
from utils.db import get_client
from utils.layout import inject_global_styles, render_sidebar

# =========================================================
# INITIAL SETUP
# =========================================================


# AUTH CHECK
if "session" not in st.session_state or not st.session_state.session:
    st.switch_page("app.py")


st.set_page_config(layout="wide")

inject_global_styles()
render_sidebar()

supabase = get_client()

# =========================================================
# HEADER
# =========================================================

st.markdown("""
# Ride For Cause: Impact Overview
A unified intelligence dashboard tracking **Infrastructure, Sustainability, and Student Outcomes**.
""")

st.markdown("")

# =========================================================
# LOAD CORE DATA
# =========================================================

schools = pd.DataFrame(supabase.table("schools").select("*").execute().data)
projects = pd.DataFrame(supabase.table("projects").select("*").execute().data)
donors = pd.DataFrame(supabase.table("donors").select("*").execute().data)
project_types = pd.DataFrame(supabase.table("project_types").select("*").execute().data)
project_type_map = pd.DataFrame(supabase.table("project_project_types").select("*").execute().data)
project_donors = pd.DataFrame(supabase.table("project_donors").select("*").execute().data)
sustainability = pd.DataFrame(supabase.table("sustainability_projects").select("*").execute().data)
reports = pd.DataFrame(supabase.table("reports").select("*").execute().data)

if projects.empty:
    st.warning("No project data available.")
    st.stop()

# =========================================================
# DATA PREPARATION
# =========================================================

projects["start_date"] = pd.to_datetime(projects["start_date"], errors="coerce")
projects["year"] = projects["start_date"].dt.year
projects["project_status"] = projects["project_status"].astype(str).str.lower()


projects_full = projects.merge(
    schools,
    left_on="school_id",
    right_on="id",
    how="left"
)

# =========================================================
# KPI CALCULATIONS (UNCHANGED LOGIC)
# =========================================================

total_schools = schools["id"].nunique()
total_projects = projects["project_id"].nunique()
total_donors = donors["id"].nunique()
total_reports = len(reports)
total_sustainability = len(sustainability)

students_before = projects["students_before"].fillna(0).sum()
students_after = projects["students_after"].fillna(0).sum()
student_growth = students_after - students_before

# =========================================================
# KPI SECTION (POLISHED STRIP)
# =========================================================

st.markdown("## Key Impact Indicators")

k1, k2, k3, k4, k5, k6 = st.columns(6)

k1.metric("Schools Supported", f"{total_schools:,}")
k2.metric("Projects Executed", f"{total_projects:,}")
k3.metric("Donors Engaged", f"{total_donors:,}")
k4.metric("Students Impacted", f"{int(students_after):,}", delta=f"{int(student_growth):,}")
k5.metric("Sustainability Actions", f"{total_sustainability:,}")
k6.metric("Reports Published", f"{total_reports:,}")

st.markdown("---")

# =========================================================
# PROJECT GROWTH TREND
# =========================================================

st.markdown("### Project Growth Over Time")

year_counts = projects.groupby("year")["project_id"].count().reset_index()

fig_projects = px.line(
    year_counts,
    x="year",
    y="project_id",
    markers=True
)

fig_projects.update_layout(
    template="plotly_dark",
    height=400,
    xaxis_title="Year",
    yaxis_title="Number of Projects"
)

st.plotly_chart(fig_projects, use_container_width=True)

# =========================================================
# TWO COLUMN ANALYTICS ROW
# =========================================================

left, right = st.columns(2)

# -----------------------------
# PROJECT STATUS DISTRIBUTION
# -----------------------------

with left:
    st.markdown("### Project Status Distribution")

    status_counts = projects["project_status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]

    fig_status = px.pie(
        status_counts,
        names="Status",
        values="Count",
        hole=0.6
    )

    fig_status.update_layout(
        template="plotly_dark",
        height=400
    )

    st.plotly_chart(fig_status, use_container_width=True)

# -----------------------------
# INTERVENTION TYPE MIX
# -----------------------------

with right:
    st.markdown("### Intervention Type Mix")

    type_merge = project_type_map.merge(
        project_types,
        left_on="project_type_id",
        right_on="id",
        how="left"
    )

    type_counts = type_merge["type_name"].value_counts().reset_index()
    type_counts.columns = ["Type", "Count"]

    fig_types = px.bar(
        type_counts,
        x="Count",
        y="Type",
        orientation="h"
    )

    fig_types.update_layout(
        template="plotly_dark",
        height=400
    )

    st.plotly_chart(fig_types, use_container_width=True)

# =========================================================
# GEOGRAPHIC COVERAGE
# =========================================================

st.markdown("### Geographic Coverage")

district_counts = (
    projects_full["district"]
    .dropna()
    .value_counts()
    .reset_index()
)

district_counts.columns = ["District", "Projects"]

fig_district = px.bar(
    district_counts,
    x="Projects",
    y="District",
    orientation="h"
)

fig_district.update_layout(
    template="plotly_dark",
    height=400
)

st.plotly_chart(fig_district, use_container_width=True)

# =========================================================
# DONOR ENGAGEMENT
# =========================================================

st.markdown("### Donor Contribution Distribution")

donor_counts = project_donors.groupby("donor_id")["project_id"].count().reset_index()

donor_counts = donor_counts.merge(
    donors,
    left_on="donor_id",
    right_on="id",
    how="left"
)

donor_counts = donor_counts.sort_values("project_id", ascending=False)

fig_donors = px.bar(
    donor_counts,
    x="project_id",
    y="donor_name",
    orientation="h"
)

fig_donors.update_layout(
    template="plotly_dark",
    height=450,
    xaxis_title="Projects Supported",
    yaxis_title="Donor"
)

st.plotly_chart(fig_donors, use_container_width=True)

# =========================================================
# SUSTAINABILITY SNAPSHOT
# =========================================================

st.markdown("### Sustainability Snapshot")

if not sustainability.empty:

    sustainability_counts = (
        sustainability["sustainability_type"]
        .value_counts()
        .reset_index()
    )

    sustainability_counts.columns = ["Category", "Count"]

    fig_sus = px.bar(
        sustainability_counts,
        x="Count",
        y="Category",
        orientation="h"
    )

    fig_sus.update_layout(
        template="plotly_dark",
        height=400
    )

    st.plotly_chart(fig_sus, use_container_width=True)

# =========================================================
# STRATEGIC INSIGHTS
# =========================================================

st.markdown("---")
st.markdown("## Strategic Insights")

completed_projects = len(projects[projects["project_status"] == "completed"])
completion_rate = round((completed_projects / total_projects) * 100, 1)

avg_students_per_project = round(students_after / total_projects, 1)

top_district = (
    district_counts.iloc[0]["District"]
    if not district_counts.empty else "N/A"
)

insight_col1, insight_col2 = st.columns(2)

with insight_col1:
    st.success(
        f"• {completion_rate}% of projects have been completed successfully.\n\n"
        f"• Average impact per project: {avg_students_per_project} students."
    )

with insight_col2:
    st.info(
        f"• Highest intervention activity observed in **{top_district}**.\n\n"
        f"• {total_sustainability} sustainability-focused actions recorded."
    )