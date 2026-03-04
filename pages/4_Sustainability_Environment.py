import streamlit as st
import pandas as pd
from utils.db import get_client
from utils.layout import inject_global_styles, render_sidebar



if "session" not in st.session_state or not st.session_state.session:
    st.switch_page("app.py")


st.set_page_config(layout="wide")

inject_global_styles()
render_sidebar()

supabase = get_client()

st.header("Sustainability & Environmental Impact")



#
import time

# ===================================================
# ADD SUSTAINABILITY ENTRY BUTTON
# ===================================================

if "show_sustainability_form" not in st.session_state:
    st.session_state.show_sustainability_form = False

if st.button("➕ Add Sustainability Entry"):
    st.session_state.show_sustainability_form = True


# ===================================================
# SUSTAINABILITY FORM
# ===================================================

if st.session_state.show_sustainability_form:

    st.markdown("---")
    st.subheader("New Sustainability Entry")

    # Fetch required tables
    projects_res = supabase.table("projects").select("*").execute()
    projects_df = pd.DataFrame(projects_res.data)

    schools_res = supabase.table("schools").select("*").execute()
    schools_df = pd.DataFrame(schools_res.data)

    donors_res = supabase.table("donors").select("*").execute()
    donors_df = pd.DataFrame(donors_res.data)

    if projects_df.empty:
        st.warning("No projects available.")
        st.stop()

    col1, col2 = st.columns(2)

    # -----------------------------------
    # LEFT COLUMN – PROJECT SELECTION
    # -----------------------------------

    with col1:

        project_name = st.selectbox(
            "Select Project *",
            projects_df["project_name"].sort_values().tolist(),
            key="sust_project"
        )

        project_row = projects_df[
            projects_df["project_name"] == project_name
        ].iloc[0]

        project_id = int(project_row["project_id"])
        school_id = project_row["school_id"]

        school_row = schools_df[
            schools_df["id"] == school_id
        ]

        if not school_row.empty:
            school_name = school_row.iloc[0]["school_name"]
            district = school_row.iloc[0]["district"]
        else:
            school_name = None
            district = None

        st.markdown(f"**School:** {school_name}")
        st.markdown(f"**District:** {district}")

        year_supported = st.number_input(
            "Year Supported *",
            min_value=2000,
            max_value=2100,
            step=1,
            key="sust_year"
        )

        sustainability_type = st.text_input(
            "Sustainability Type *",
            key="sust_type"
        )

    # -----------------------------------
    # RIGHT COLUMN – IMPACT DETAILS
    # -----------------------------------

    with col2:

        impact_metric = st.text_input(
            "Impact Metric (e.g., Solar Installed, Trees Planted)",
            key="sust_metric"
        )

        impact_value = st.number_input(
            "Impact Value (Numeric)",
            min_value=0.0,
            step=1.0,
            key="sust_value"
        )

        impact_unit = st.text_input(
            "Impact Unit (e.g., units, kWh/year, liters)",
            key="sust_unit"
        )

        donor_name = None
        if not donors_df.empty:
            donor_name = st.selectbox(
                "Supporting Donor (Optional)",
                ["None"] + donors_df["donor_name"].tolist(),
                key="sust_donor"
            )

        notes = st.text_area("Notes", key="sust_notes")

    # -----------------------------------
    # SUBMIT
    # -----------------------------------

    if st.button("Create Sustainability Entry"):

        try:

            if not sustainability_type.strip():
                st.error("Sustainability type is required.")
                st.stop()

            if year_supported is None:
                st.error("Year is required.")
                st.stop()

            supabase.table("sustainability_projects").insert({
                "project_id": project_id,
                "project_name": project_name,
                "school_id": int(school_id) if school_id else None,
                "school_name": school_name,
                "district": district,
                "year_supported": int(year_supported),
                "donor_name": donor_name if donor_name != "None" else None,
                "sustainability_type": sustainability_type,
                "impact_metric": impact_metric if impact_metric else None,
                "impact_value": float(impact_value) if impact_value else None,
                "impact_unit": impact_unit if impact_unit else None,
                "notes": notes if notes else None
            }).execute()

            st.success("Sustainability entry created successfully!")

            st.session_state.show_sustainability_form = False
            st.rerun()

        except Exception as e:
            st.error(f"Insertion failed: {e}")
#



# =========================================================
# FETCH DATA
# =========================================================

res = supabase.table("sustainability_projects").select("*").execute()
df = pd.DataFrame(res.data)

if df.empty:
    st.warning("No sustainability data available.")
    st.stop()

df["impact_value"] = pd.to_numeric(df["impact_value"], errors="coerce")

# =========================================================
# FILTERS
# =========================================================

st.subheader("Filters")

col1, col2 = st.columns(2)

with col1:
    years = ["All"] + sorted(df["year_supported"].dropna().unique().tolist())
    selected_year = st.selectbox("Filter by Year", years)

with col2:
    types = ["All"] + sorted(df["sustainability_type"].dropna().unique().tolist())
    selected_type = st.selectbox("Filter by Sustainability Type", types)

if selected_year != "All":
    df = df[df["year_supported"] == selected_year]

if selected_type != "All":
    df = df[df["sustainability_type"] == selected_type]

if df.empty:
    st.info("No data for selected filters.")
    st.stop()

# =========================================================
# OVERVIEW KPIs (UNCHANGED CORE LOGIC)
# =========================================================

st.markdown("---")
st.subheader("Sustainability Overview")

total_projects = len(df)
unique_schools = df["school_name"].nunique()
unique_districts = df["district"].nunique()
unique_types = df["sustainability_type"].nunique()
active_donors = df["donor_name"].nunique()

k1, k2, k3, k4, k5 = st.columns(5)

k1.metric("Total Sustainability Interventions", total_projects)
k2.metric("Schools Impacted", unique_schools)
k3.metric("Districts Covered", unique_districts)
k4.metric("Sustainability Categories", unique_types)
k5.metric("Active Sustainability Donors", active_donors)

# =========================================================
# ADDITIONAL ADVANCED KPIs
# =========================================================

st.markdown("### Advanced Impact Indicators")

colA, colB, colC = st.columns(3)

# Average interventions per school
avg_per_school = round(total_projects / unique_schools, 2) if unique_schools else 0
colA.metric("Avg Interventions per School", avg_per_school)

# Most active district
top_district = df["district"].value_counts().idxmax()
colB.metric("Most Active District", top_district)

# Most common sustainability type
top_type = df["sustainability_type"].value_counts().idxmax()
colC.metric("Most Common Sustainability Type", top_type)

# =========================================================
# TYPE DISTRIBUTION (IMPROVED)
# =========================================================

st.markdown("---")
st.subheader("Sustainability Type Distribution")

type_counts = df["sustainability_type"].value_counts()
st.bar_chart(type_counts)

# =========================================================
# DISTRICT VS TYPE HEATMAP STYLE TABLE
# =========================================================

st.subheader("District vs Sustainability Category")

cross_tab = pd.crosstab(df["district"], df["sustainability_type"])
st.dataframe(cross_tab)

# =========================================================
# YEAR-WISE TREND
# =========================================================

st.markdown("---")
st.subheader("Year-wise Sustainability Growth")

year_trend = df.groupby("year_supported")["id"].count()
st.line_chart(year_trend)

# =========================================================
# DONOR CONTRIBUTION INTENSITY
# =========================================================

st.markdown("---")
st.subheader("Sustainability Donor Engagement")

donor_counts = (
    df.groupby("donor_name")["id"]
    .count()
    .sort_values(ascending=False)
)

st.bar_chart(donor_counts)

# Add donor diversity score
donor_diversity = len(donor_counts)
st.metric("Total Unique Sustainability Donors", donor_diversity)

# =========================================================
# IMPACT VALUE ANALYTICS (UNIT AWARE)
# =========================================================

st.markdown("---")
st.subheader("Measured Environmental Impact")

impact_df = df.dropna(subset=["impact_value"])

if not impact_df.empty:

    total_measured = impact_df["impact_value"].sum()
    st.metric("Total Measured Impact (All Units Combined)", round(total_measured, 2))

    st.markdown("#### Impact by Sustainability Type")
    st.bar_chart(
        impact_df.groupby("sustainability_type")["impact_value"].sum()
    )

    st.markdown("#### Impact by Unit")
    st.bar_chart(
        impact_df.groupby("impact_unit")["impact_value"].sum()
    )

    st.markdown("#### Impact Intensity per School")
    impact_per_school = (
        impact_df.groupby("school_name")["impact_value"]
        .sum()
        .sort_values(ascending=False)
    )
    st.bar_chart(impact_per_school)

else:
    st.info("No quantified impact values added yet.")

# =========================================================
# SCHOOL SUSTAINABILITY INTENSITY
# =========================================================

st.markdown("---")
st.subheader("Sustainability Intensity per School")

school_counts = (
    df.groupby("school_name")["id"]
    .count()
    .sort_values(ascending=False)
)

st.bar_chart(school_counts)

# =========================================================
# PROJECT LINK ANALYSIS
# =========================================================

st.markdown("---")
st.subheader("Project-Level Sustainability Distribution")

project_counts = (
    df.groupby("project_name")["id"]
    .count()
    .sort_values(ascending=False)
)

st.bar_chart(project_counts)

# =========================================================
# RAW DATA VIEW
# =========================================================

st.markdown("---")
with st.expander("View Sustainability Dataset"):
    st.dataframe(df.reset_index(drop=True))