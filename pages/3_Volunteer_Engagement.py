import streamlit as st
import pandas as pd
from utils.db import get_client
from utils.layout import inject_global_styles, render_sidebar

# --------------------------------------------------------
# SETUP
# --------------------------------------------------------


if "session" not in st.session_state or not st.session_state.session:
    st.switch_page("app.py")


st.set_page_config(layout="wide")

inject_global_styles()
render_sidebar()

supabase = get_client()

st.header("Volunteer Engagement Analytics")

# --------------------------------------------------------
# FETCH DATA
# --------------------------------------------------------

donors_res = supabase.table("donors").select("*").execute()
donors_df = pd.DataFrame(donors_res.data)

project_donors_res = supabase.table("project_donors").select("*").execute()
project_donors_df = pd.DataFrame(project_donors_res.data)

projects_res = supabase.table("projects").select("project_id, project_name, school_id").execute()
projects_df = pd.DataFrame(projects_res.data)

schools_res = supabase.table("schools").select("id, school_name").execute()
schools_df = pd.DataFrame(schools_res.data)

if donors_df.empty:
    st.warning("No donor data available.")
    st.stop()

if "supports_volunteering" not in donors_df.columns:
    st.error("Column 'supports_volunteering' not found in donors table.")
    st.stop()

# ====================================================
# VOLUNTEER PARTNER OVERVIEW
# ====================================================

st.subheader("Volunteer Partner Overview")

total_partners = len(donors_df)

volunteer_partners_df = donors_df[
    donors_df["supports_volunteering"] == True
]

volunteer_partners = len(volunteer_partners_df)

engagement_percent = round((volunteer_partners / total_partners) * 100, 1)

c1, c2, c3 = st.columns(3)

c1.metric("Total Partners", total_partners)
c2.metric("Volunteering Partners", volunteer_partners)
c3.metric("Engagement %", f"{engagement_percent}%")

# Donut chart (cleaner than true/false bars)
st.subheader("Volunteering Support Split")

donut_df = pd.DataFrame({
    "Category": ["Volunteering Partners", "Non-Volunteering Partners"],
    "Count": [volunteer_partners, total_partners - volunteer_partners]
})

st.plotly_chart(
    {
        "data": [{
            "values": donut_df["Count"],
            "labels": donut_df["Category"],
            "type": "pie",
            "hole": 0.6
        }],
        "layout": {"showlegend": True}
    }
)
# --------------------------------------------------------
#  PROJECTS INVOLVING VOLUNTEER PARTNERS
# --------------------------------------------------------

st.subheader("Projects Involving Volunteer Partners")

if not project_donors_df.empty:

    volunteer_donor_ids = volunteer_partners_df["id"].tolist()

    volunteer_project_ids = project_donors_df[
        project_donors_df["donor_id"].isin(volunteer_donor_ids)
    ]["project_id"].unique()

    project_count = len(volunteer_project_ids)

    st.metric("Projects Supported by Volunteer Partners", project_count)

else:
    st.info("No project-donor data available.")

# --------------------------------------------------------
#  TOP VOLUNTEER PARTNERS (BY PROJECT COUNT)
# --------------------------------------------------------

st.subheader("Top Volunteer Partners")

if not project_donors_df.empty:

    merged = (
        project_donors_df
        .merge(donors_df, left_on="donor_id", right_on="id", how="left")
    )

    volunteer_only = merged[
        merged["supports_volunteering"] == True
    ]

    if not volunteer_only.empty:

        top_volunteers = (
            volunteer_only
            .groupby("donor_name")["project_id"]
            .nunique()
            .sort_values(ascending=False)
        )

        st.bar_chart(top_volunteers)

    else:
        st.info("No volunteer-linked projects found.")

# --------------------------------------------------------
# SCHOOLS BENEFITING FROM VOLUNTEER PARTNERS
# --------------------------------------------------------

st.subheader("Schools Benefiting from Volunteer Partners")

if not project_donors_df.empty:

    merged_full = (
        project_donors_df
        .merge(projects_df, on="project_id", how="left")
        .merge(schools_df, left_on="school_id", right_on="id", how="left")
        .merge(donors_df, left_on="donor_id", right_on="id", how="left")
    )

    volunteer_school = merged_full[
        merged_full["supports_volunteering"] == True
    ]

    if not volunteer_school.empty:

        school_counts = (
            volunteer_school
            .groupby("school_name")["project_id"]
            .nunique()
            .sort_values(ascending=False)
        )

        st.bar_chart(school_counts)

    else:
        st.info("No school-volunteer linkage available.")

# --------------------------------------------------------
#  VOLUNTEER PARTNER DIRECTORY
# --------------------------------------------------------

st.subheader("Volunteer Partner Directory")

with st.expander("View Volunteering Partners"):

    cols_to_show = ["donor_name", "notes"]

    # Only show columns that exist
    cols_to_show = [
        col for col in cols_to_show if col in volunteer_partners_df.columns
    ]

    if not volunteer_partners_df.empty:
        st.dataframe(
            volunteer_partners_df[cols_to_show]
            .reset_index(drop=True)
        )
    else:
        st.info("No volunteering partners available.")
