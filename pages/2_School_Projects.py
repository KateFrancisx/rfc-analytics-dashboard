import streamlit as st
import pandas as pd
import numpy as np
from utils.db import get_client, load_all_data
from utils.layout import inject_global_styles, render_sidebar


# ---------------------------------------------------
# INITIAL SETUP
# ---------------------------------------------------



if "session" not in st.session_state or not st.session_state.session:
    st.switch_page("app.py")


st.set_page_config(layout="wide")

inject_global_styles()
render_sidebar()

supabase = get_client()

st.title("Schools & Projects Analytics")




#
# ===================================================
# ➕ ADD NEW PROJECT BUTTON
# ===================================================

if "show_project_form" not in st.session_state:
    st.session_state.show_project_form = False

if "components_data" not in st.session_state:
    st.session_state.components_data = []

if st.button("➕ Add New Project"):
    st.session_state.show_project_form = True


# ===================================================
# PROJECT FORM (DYNAMIC)
# ===================================================

if st.session_state.show_project_form:

    st.markdown("---")
    st.subheader("New Project Entry")

    # Load fresh dropdown data
    data_raw = load_all_data(supabase)
    schools_df = data_raw["schools"]
    project_types_df = data_raw["project_types"]
    donors_df = data_raw["donors"]

    # -------------------------------
    # PROJECT BASIC INFO
    # -------------------------------

    project_name = st.text_input("Project Name *")

    is_school_project = st.checkbox("Is this a School Project?")

    school_name = None
    district = None
    taluk = None
    latitude = None
    longitude = None

    if is_school_project:

        st.markdown("### School Details")

        school_name = st.text_input("School Name *")
        district = st.text_input("District")
        taluk = st.text_input("Taluk")

        latitude = st.number_input(
            "Latitude (Optional)",
            format="%.6f",
            help="Google Maps → Right click → copy coordinates"
        )

        longitude = st.number_input(
            "Longitude (Optional)",
            format="%.6f"
        )

    start_date = st.date_input("Start Date")
    end_date = st.date_input("End Date")

    project_status = st.selectbox(
        "Project Status",
        ["completed", "ongoing", "pending"]
    )

    students_before = st.number_input("Students Before", min_value=0)
    students_after = st.number_input("Students After", min_value=0)

    description = st.text_area("Project Description")

    # -------------------------------
    # PROJECT TYPES
    # -------------------------------

    st.markdown("### Project Types")

    selected_types = st.multiselect(
        "Select Project Types",
        project_types_df["type_name"].sort_values().tolist()
    )

    # -------------------------------
    # COMPONENTS (DYNAMIC)
    # -------------------------------

    # -------------------------------
    # COMPONENTS (DYNAMIC WITH REMOVE)
    # -------------------------------

    st.markdown("### Components")

    if st.button("➕ Add Component"):
        st.session_state.components_data.append({})
        st.rerun()

    # Display components
    for idx in range(len(st.session_state.components_data)):

        col1, col2 = st.columns([6, 1])

        with col1:
            st.markdown(f"**Component {idx+1}**")

        with col2:
            if st.button("❌", key=f"remove_{idx}"):
                st.session_state.components_data.pop(idx)

                # Clean related keys
                for key in list(st.session_state.keys()):
                    if key.startswith(f"ctype_{idx}") or \
                    key.startswith(f"cspec_{idx}") or \
                    key.startswith(f"cstatus_{idx}") or \
                    key.startswith(f"cnotes_{idx}"):
                        del st.session_state[key]

                st.rerun()

        comp_type = st.text_input("Component Type", key=f"ctype_{idx}")
        comp_spec = st.text_input("Specification", key=f"cspec_{idx}")
        comp_status = st.text_input("Status (lowercase only)", key=f"cstatus_{idx}")
        comp_notes = st.text_input("Notes", key=f"cnotes_{idx}")

        st.session_state.components_data[idx] = {
            "component_type": comp_type,
            "specification": comp_spec,
            "status": comp_status.lower() if comp_status else None,
            "notes": comp_notes
        }

    # -------------------------------
    # DONORS
    # -------------------------------

    st.markdown("### Donors")

    selected_donors = st.multiselect(
        "Select Donors",
        donors_df["donor_name"].sort_values().tolist()
    )

    donor_rows = []

    for donor in selected_donors:
        role = st.text_input(f"Role for {donor}", key=f"role_{donor}")
        contribution = st.number_input(
            f"Contribution for {donor}",
            min_value=0.0,
            step=1000.0,
            key=f"amount_{donor}"
        )

        donor_rows.append({
            "donor_name": donor,
            "role": role,
            "contribution": contribution
        })

    # -------------------------------
    # FINAL SUBMIT BUTTON
    # -------------------------------

    if st.button("Create Project"):

        try:

            if not project_name.strip():
                st.error("Project name is required.")
                st.stop()

            if students_after < students_before:
                st.error("Students after cannot be less than students before.")
                st.stop()

            school_id = None

            # -------------------------------
            # SCHOOL INSERT
            # -------------------------------

            if is_school_project:

                if not school_name.strip():
                    st.error("School name is required.")
                    st.stop()

                existing_school = schools_df[
                    schools_df["school_name"].str.lower() == school_name.lower()
                ]

                if not existing_school.empty:
                    school_id = int(existing_school.iloc[0]["id"])
                else:
                    school_insert = supabase.table("schools").insert({
                        "school_name": str(school_name),
                        "district": str(district) if district else None,
                        "taluk": str(taluk) if taluk else None,
                        "latitude": float(latitude) if latitude else None,
                        "longitude": float(longitude) if longitude else None
                    }).execute()

                    school_id = int(school_insert.data[0]["id"])

            # -------------------------------
            # PROJECT INSERT
            # -------------------------------

            project_insert = supabase.table("projects").insert({
                "project_name": str(project_name),
                "school_id": int(school_id) if school_id is not None else None,
                "start_date": str(start_date),
                "end_date": str(end_date),
                "project_status": str(project_status),
                "students_before": int(students_before),
                "students_after": int(students_after),
                "description": str(description) if description else None
            }).execute()

            project_id = int(project_insert.data[0]["project_id"])

            # -------------------------------
            # PROJECT TYPES
            # -------------------------------

            type_rows = []

            for type_name in selected_types:
                type_row = project_types_df[
                    project_types_df["type_name"] == type_name
                ]
                if not type_row.empty:
                    type_rows.append({
                        "project_id": int(project_id),
                        "project_type_id": int(type_row.iloc[0]["id"])
                    })

            if type_rows:
                supabase.table("project_project_types").insert(type_rows).execute()

            # -------------------------------
            # COMPONENTS
            # -------------------------------

            component_rows = []

            for comp in st.session_state.components_data:
                if comp.get("component_type"):
                    component_rows.append({
                        "project_id": int(project_id),
                        "school_name": str(school_name) if is_school_project else None,
                        "component_type": str(comp["component_type"]),
                        "specification": str(comp["specification"]) if comp["specification"] else None,
                        "status": str(comp["status"]) if comp["status"] else None,
                        "notes": str(comp["notes"]) if comp["notes"] else None
                    })

            if component_rows:
                supabase.table("project_components").insert(component_rows).execute()

            # -------------------------------
            # DONORS
            # -------------------------------

            donor_insert_rows = []

            for donor in donor_rows:
                donor_row = donors_df[
                    donors_df["donor_name"] == donor["donor_name"]
                ]

                if not donor_row.empty:
                    donor_insert_rows.append({
                        "project_id": int(project_id),
                        "donor_id": int(donor_row.iloc[0]["id"]),
                        "role": str(donor["role"]) if donor["role"] else None,
                        "contribution_amount": float(donor["contribution"])
                    })

            if donor_insert_rows:
                supabase.table("project_donors").insert(donor_insert_rows).execute()

            st.success("Project successfully created!")

            # Reset form state
            st.session_state.show_project_form = False
            st.session_state.components_data = []

            # Clear all dynamic widget keys
            for key in list(st.session_state.keys()):
                if key.startswith("ctype_") or \
                key.startswith("cspec_") or \
                key.startswith("cstatus_") or \
                key.startswith("cnotes_") or \
                key.startswith("role_") or \
                key.startswith("amount_"):
                    del st.session_state[key]

            st.rerun()

        except Exception as e:
            st.error(f"Insertion failed: {e}")
#





# ---------------------------------------------------
# LOAD ALL DATA (CACHED)
# ---------------------------------------------------

data = load_all_data(supabase)

schools = data["schools"]
projects = data["projects"]
project_types = data["project_types"]
project_types_map = data["project_project_types"]
components = data["project_components"]
project_donors = data["project_donors"]
donors = data["donors"]

if projects.empty:
    st.warning("No project data available.")
    st.stop()

# ---------------------------------------------------
# DATA CLEANING
# ---------------------------------------------------

projects["start_date"] = pd.to_datetime(projects["start_date"], errors="coerce")
projects["year"] = projects["start_date"].dt.year
projects["project_status"] = projects["project_status"].astype(str).str.lower()

# Merge school info
projects_full = projects.merge(
    schools,
    left_on="school_id",
    right_on="id",
    how="left"
)

# ---------------------------------------------------
# EXECUTIVE METRICS
# ---------------------------------------------------

st.subheader("Executive Summary")

col1, col2, col3, col4, col5, col6 = st.columns(6)

col1.metric("Total Schools", schools.shape[0])
col2.metric("Total Projects", projects["project_id"].nunique())
col3.metric("School-Based Projects", projects["school_id"].notna().sum())
col4.metric("Non-School Projects", projects["school_id"].isna().sum())
col5.metric("Components Installed", components.shape[0])
col6.metric("Active Donors", donors.shape[0])

# ---------------------------------------------------
# FILTER SECTION
# ---------------------------------------------------

st.subheader("Filters")

f1, f2, f3 = st.columns(3)

with f1:
    district_filter = st.selectbox(
        "District",
        ["All"] + sorted(schools["district"].dropna().unique())
    )

with f2:
    status_filter = st.selectbox(
        "Project Status",
        ["All"] + sorted(projects["project_status"].dropna().unique())
    )

with f3:
    type_filter = st.selectbox(
        "Project Type",
        ["All"] + sorted(project_types["type_name"].unique())
    )

filtered_projects = projects_full.copy()

if district_filter != "All":
    filtered_projects = filtered_projects[
        filtered_projects["district"] == district_filter
    ]

if status_filter != "All":
    filtered_projects = filtered_projects[
        filtered_projects["project_status"] == status_filter
    ]

if type_filter != "All":
    type_ids = project_types[
        project_types["type_name"] == type_filter
    ]["id"]

    project_ids = project_types_map[
        project_types_map["project_type_id"].isin(type_ids)
    ]["project_id"]

    filtered_projects = filtered_projects[
        filtered_projects["project_id"].isin(project_ids)
    ]

if filtered_projects.empty:
    st.info("No data for selected filters.")
    st.stop()

# ---------------------------------------------------
# GEOGRAPHIC SPREAD
# ---------------------------------------------------

st.subheader("Geographic Coverage")

district_counts = filtered_projects["district"].value_counts()

st.bar_chart(district_counts)

# ---------------------------------------------------
# PROJECT PORTFOLIO ANALYSIS
# ---------------------------------------------------

st.subheader("Project Status Distribution")
st.bar_chart(filtered_projects["project_status"].value_counts())

if filtered_projects["year"].notna().any():
    st.subheader("Projects Started per Year")
    st.line_chart(
        filtered_projects.groupby("year")["project_id"].count()
    )

# ---------------------------------------------------
# PROJECT TYPE ANALYSIS
# ---------------------------------------------------

type_analysis = project_types_map[
    project_types_map["project_id"].isin(filtered_projects["project_id"])
].merge(
    project_types,
    left_on="project_type_id",
    right_on="id",
    how="left"
)

if not type_analysis.empty:
    st.subheader("Project Type Distribution")
    st.bar_chart(type_analysis["type_name"].value_counts())

# ---------------------------------------------------
# INFRASTRUCTURE DEPTH
# ---------------------------------------------------

if not components.empty:

    comp_filtered = components[
        components["project_id"].isin(filtered_projects["project_id"])
    ]

    st.subheader("Components per Project")

    comp_counts = comp_filtered.groupby("project_id")[
        "component_id"
    ].count().sort_values(ascending=False)

    st.bar_chart(comp_counts)

    st.subheader("Component Type Distribution")

    if "component_type" in comp_filtered.columns:
        st.bar_chart(comp_filtered["component_type"].value_counts())

    st.subheader("Component Completion Status")

    if "status" in comp_filtered.columns:
        st.bar_chart(comp_filtered["status"].value_counts())

# ---------------------------------------------------
# DONOR IMPACT ANALYSIS
# ---------------------------------------------------

if not project_donors.empty:

    donor_merge = project_donors[
        project_donors["project_id"].isin(filtered_projects["project_id"])
    ].merge(
        donors,
        left_on="donor_id",
        right_on="id",
        how="left"
    )

    st.subheader("Projects Supported per Donor")
    st.bar_chart(
        donor_merge.groupby("donor_name")["project_id"]
        .nunique()
        .sort_values(ascending=False)
    )

    if "contribution_amount" in donor_merge.columns:
        st.subheader("Total Contribution per Donor")
        st.bar_chart(
            donor_merge.groupby("donor_name")[
                "contribution_amount"
            ].sum().sort_values(ascending=False)
        )

# ---------------------------------------------------
# INTERACTIVE DRILLDOWN
# ---------------------------------------------------

st.subheader("Explore Specific Project")

project_select = st.selectbox(
    "Select a Project",
    filtered_projects["project_name"].unique()
)

project_detail = filtered_projects[
    filtered_projects["project_name"] == project_select
]

st.write("### Project Details")
st.dataframe(project_detail)

if not components.empty:
    st.write("### Components Installed")
    st.dataframe(
        components[
            components["project_id"] ==
            project_detail["project_id"].values[0]
        ]
    )

if not project_donors.empty:
    st.write("### Supporting Donors")
    st.dataframe(
        donor_merge[
            donor_merge["project_id"] ==
            project_detail["project_id"].values[0]
        ][["donor_name", "contribution_amount"]]
    )

# ---------------------------------------------------
# FULL DATA EXPORT
# ---------------------------------------------------

with st.expander("View Filtered Dataset"):
    st.dataframe(filtered_projects)