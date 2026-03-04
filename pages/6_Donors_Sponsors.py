import streamlit as st
import pandas as pd
import time
from utils.db import get_client
from utils.layout import inject_global_styles, render_sidebar



if "session" not in st.session_state or not st.session_state.session:
    st.switch_page("app.py")


st.set_page_config(layout="wide")

inject_global_styles()
render_sidebar()

supabase = get_client()

st.header("Donor & Funding Intelligence")



#
import time

# ===================================================
# ➕ ADD NEW DONOR BUTTON
# ===================================================

if "show_donor_form" not in st.session_state:
    st.session_state.show_donor_form = False

if "donor_success_time" not in st.session_state:
    st.session_state.donor_success_time = None

if "donor_recently_submitted" not in st.session_state:
    st.session_state.donor_recently_submitted = False


if st.button("➕ Add New Donor"):
    st.session_state.show_donor_form = True


# ===================================================
# DONOR FORM
# ===================================================

if st.session_state.show_donor_form:

    st.markdown("---")
    st.subheader("New Donor Entry")

    # Fetch fresh data
    donor_types_res = supabase.table("donor_types").select("*").execute()
    donor_types_df = pd.DataFrame(donor_types_res.data)

    donors_res = supabase.table("donors").select("*").execute()
    donors_df = pd.DataFrame(donors_res.data)

    col1, col2 = st.columns(2)

    # -----------------------------------
    # LEFT COLUMN – DONOR DETAILS
    # -----------------------------------

    with col1:
        donor_name = st.text_input("Donor Name *", key="donor_name")
        supports_volunteering = st.checkbox("Supports Volunteering", key="supports_volunteering")
        notes = st.text_area("Notes", key="donor_notes")

    # -----------------------------------
    # RIGHT COLUMN – DONOR TYPE
    # -----------------------------------

    with col2:
        st.markdown("### Donor Type")

        create_new_type = st.checkbox("Create New Donor Type", key="create_new_type")

        donor_type_id = None

        if create_new_type:

            if "selected_type" in st.session_state:
                del st.session_state["selected_type"]

            new_type_name = st.text_input("New Type Name *", key="new_type_name")
            new_type_description = st.text_input("Type Description", key="new_type_description")

        else:

            if not donor_types_df.empty:
                selected_type = st.selectbox(
                    "Select Existing Type",
                    donor_types_df["type_name"].sort_values().tolist(),
                    key="selected_type"
                )
            else:
                selected_type = None
                st.warning("No donor types available. Please create one.")

    # -----------------------------------
    # SUBMIT BUTTON
    # -----------------------------------

    if st.button("Create Donor"):

        try:

            if not donor_name.strip():
                st.error("Donor name is required.")
                st.stop()

            # Duplicate check
            if not donors_df.empty:
                existing_donor = donors_df[
                    donors_df["donor_name"].str.lower() == donor_name.lower()
                ]
                if not existing_donor.empty:
                    st.error("Donor already exists.")
                    st.stop()

            # -----------------------------------
            # HANDLE DONOR TYPE
            # -----------------------------------

            if create_new_type:

                if not new_type_name.strip():
                    st.error("New donor type name is required.")
                    st.stop()

                existing_type = donor_types_df[
                    donor_types_df["type_name"].str.lower() == new_type_name.lower()
                ]

                if existing_type.empty:

                    type_insert = supabase.table("donor_types").insert({
                        "type_name": str(new_type_name),
                        "description": str(new_type_description) if new_type_description else None
                    }).execute()

                    donor_type_id = int(type_insert.data[0]["id"])

                else:
                    donor_type_id = int(existing_type.iloc[0]["id"])

            else:

                if not selected_type:
                    st.error("Please select a donor type.")
                    st.stop()

                type_row = donor_types_df[
                    donor_types_df["type_name"] == selected_type
                ]

                donor_type_id = int(type_row.iloc[0]["id"])

            # -----------------------------------
            # INSERT DONOR
            # -----------------------------------

            supabase.table("donors").insert({
                "donor_name": str(donor_name),
                "donor_type_id": int(donor_type_id),
                "supports_volunteering": bool(supports_volunteering),
                "notes": str(notes) if notes else None
            }).execute()

            # Mark success
            st.session_state.donor_recently_submitted = True
            st.session_state.donor_success_time = time.time()

        except Exception as e:
            st.error(f"Insertion failed: {e}")


# ===================================================
# AUTO CLOSE FORM AFTER SUCCESS
# ===================================================

if st.session_state.donor_recently_submitted:

    st.success("Donor successfully created!")

    elapsed = time.time() - st.session_state.donor_success_time

    if elapsed > 1.5:

        # Close form
        st.session_state.show_donor_form = False
        st.session_state.donor_recently_submitted = False

        # Clear form keys
        for key in [
            "donor_name",
            "supports_volunteering",
            "donor_notes",
            "create_new_type",
            "new_type_name",
            "new_type_description",
            "selected_type"
        ]:
            if key in st.session_state:
                del st.session_state[key]

        st.rerun()
#

# =========================================================
# FETCH DATA
# =========================================================

donors_res = supabase.table("donors").select("*").execute()
donors_df = pd.DataFrame(donors_res.data)

project_donors_res = supabase.table("project_donors").select("*").execute()
project_donors_df = pd.DataFrame(project_donors_res.data)

if donors_df.empty:
    st.warning("No donor data available.")
    st.stop()

if project_donors_df.empty:
    project_donors_df = pd.DataFrame(
        columns=["project_id", "donor_id", "contribution_amount"]
    )

project_donors_df["contribution_amount"] = pd.to_numeric(
    project_donors_df.get("contribution_amount", 0),
    errors="coerce"
).fillna(0)

# =========================================================
# FUNDING AGGREGATION
# =========================================================

funding_df = (
    project_donors_df.groupby("donor_id")
    .agg(
        total_projects=("project_id", "nunique"),
        total_funding=("contribution_amount", "sum")
    )
    .reset_index()
)

funding_df = funding_df.merge(
    donors_df,
    left_on="donor_id",
    right_on="id",
    how="right"
)

funding_df["total_projects"] = funding_df["total_projects"].fillna(0)
funding_df["total_funding"] = funding_df["total_funding"].fillna(0)

# =========================================================
# EXECUTIVE KPIs
# =========================================================

st.subheader("Funding Overview")

total_donors = donors_df["donor_name"].nunique()
active_donors = funding_df[funding_df["total_projects"] > 0].shape[0]
total_funding = funding_df["total_funding"].sum()
avg_donation = total_funding / active_donors if active_donors > 0 else 0

k1, k2, k3, k4 = st.columns(4)

k1.metric("Total Donors", total_donors)
k2.metric("Active Donors", active_donors)
k3.metric("Total Funds Raised", f"₹ {int(total_funding):,}")
k4.metric("Avg Funding per Active Donor", f"₹ {int(avg_donation):,}")

# =========================================================
# TOP DONORS BY FUNDING
# =========================================================

st.subheader("Top Donors by Contribution")

top_funders = funding_df.sort_values(
    "total_funding", ascending=False
).head(10)

st.bar_chart(
    top_funders.set_index("donor_name")["total_funding"]
)

with st.expander("View Funding Leaderboard"):
    st.dataframe(
        top_funders[
            ["donor_name", "total_projects", "total_funding"]
        ].reset_index(drop=True)
    )

# =========================================================
# DONATION SHARE (% OF TOTAL)
# =========================================================

st.subheader("Funding Share Distribution")

funding_df["share_percent"] = (
    funding_df["total_funding"] / total_funding * 100
    if total_funding > 0 else 0
)

top_share = funding_df.sort_values(
    "share_percent", ascending=False
).head(5)

st.bar_chart(
    top_share.set_index("donor_name")["share_percent"]
)

# Funding concentration risk
top_3_share = top_share["share_percent"].sum()

if top_3_share > 60:
    st.warning(
        f"⚠ High Funding Concentration Risk: Top donors contribute {round(top_3_share,1)}% of total funds."
    )
elif top_3_share > 40:
    st.info(
        f"Moderate concentration: Top donors contribute {round(top_3_share,1)}% of funds."
    )
else:
    st.success("Funding diversified across donors.")

# =========================================================
# DONOR ENGAGEMENT MATRIX
# =========================================================

st.subheader("Donor Engagement Matrix")

matrix_df = funding_df[
    ["donor_name", "total_projects", "total_funding"]
].sort_values(
    ["total_funding", "total_projects"],
    ascending=False
)

st.dataframe(matrix_df.reset_index(drop=True))

# =========================================================
# PROJECT SPREAD ANALYSIS
# =========================================================

st.subheader("Projects Supported per Donor")

st.bar_chart(
    funding_df.sort_values("total_projects", ascending=False)
    .set_index("donor_name")["total_projects"]
)

# =========================================================
# INACTIVE DONOR ALERT
# =========================================================

st.subheader("Inactive Donors")

inactive = funding_df[funding_df["total_projects"] == 0]

if not inactive.empty:
    st.warning(f"{len(inactive)} donors currently inactive.")
    with st.expander("View Inactive Donors"):
        st.dataframe(
            inactive[["donor_name"]]
            .reset_index(drop=True)
        )
else:
    st.success("All donors actively contributing.")

# =========================================================
# FUNDING DISTRIBUTION CURVE
# =========================================================

st.subheader("Funding Distribution Curve")

distribution = funding_df["total_funding"].sort_values()

st.line_chart(distribution.reset_index(drop=True))
