import streamlit as st
import pandas as pd
import datetime
from utils.db import get_client
from utils.layout import inject_global_styles, render_sidebar



if "session" not in st.session_state or not st.session_state.session:
    st.switch_page("app.py")


st.set_page_config(layout="wide")

inject_global_styles()
render_sidebar()

supabase = get_client()


st.header("Reports & Documents Management")


# =====================================================
# FETCH DROPDOWN DATA
# =====================================================

projects_df = pd.DataFrame(
    supabase.table("projects").select("project_id, project_name").execute().data
)

schools_df = pd.DataFrame(
    supabase.table("schools").select("id, school_name").execute().data
)

donors_df = pd.DataFrame(
    supabase.table("donors").select("id, donor_name").execute().data
)

# =====================================================
# UPLOAD SECTION
# =====================================================

st.subheader("Upload New Document")

# -----------------------------
# SELECT SOURCE OUTSIDE FORM
# -----------------------------
source_type = st.radio(
    "Select Document Source",
    ["Upload PDF", "External Link"]
)

# -----------------------------
# SESSION STATE INIT
# -----------------------------

# Initialize form reset counter
if "form_reset_counter" not in st.session_state:
    st.session_state.form_reset_counter = 0

# Track upload state
if "is_uploading" not in st.session_state:
    st.session_state.is_uploading = False

# Show success message after rerun
if "upload_success" in st.session_state:
    st.success("Document saved successfully!")
    del st.session_state["upload_success"]

# Dynamic form key for full reset
with st.form(f"upload_form_{st.session_state.form_reset_counter}"):

    col1, col2 = st.columns(2)

    with col1:
        title = st.text_input("Document Title")

        document_type = st.selectbox(
            "Document Type",
            ["Project Report", "Event Report", "Sustainability Report", "Financial Report"]
        )

        report_year = st.number_input(
            "Report Year",
            min_value=2000,
            max_value=2100,
            value=datetime.datetime.now().year
        )

    with col2:
        project = st.selectbox(
            "Project (Optional)",
            ["None"] + projects_df["project_name"].tolist()
        )

        school = st.selectbox(
            "School (Optional)",
            ["None"] + schools_df["school_name"].tolist()
        )

        donor = st.selectbox(
            "Donor (Optional)",
            ["None"] + donors_df["donor_name"].tolist()
        )

    description = st.text_area("Description")
    
    

    uploaded_file = None
    external_link = None

    if source_type == "Upload PDF":
        uploaded_file = st.file_uploader("Upload PDF", type=["pdf"])
    else:
        external_link = st.text_input("Paste External Link")

    submitted = st.form_submit_button(
        "Save Document",
        disabled=st.session_state.is_uploading
    )


    if submitted:

        if not title.strip():
            st.error("Title is required.")
            st.stop()

        st.session_state.is_uploading = True

        with st.spinner("Uploading document..."):

            file_name = None
            file_url = None
            source = None
            file_size = None

            # ============================
            # HANDLE FILE UPLOAD
            # ============================

            if source_type == "Upload PDF":

                if uploaded_file is None:
                    st.error("Please upload a PDF file.")
                    st.session_state.is_uploading = False
                    st.stop()

                file_name = f"{datetime.datetime.now().timestamp()}_{uploaded_file.name}"
                file_size = uploaded_file.size  

                supabase.storage.from_("reports").upload(
                    file_name,
                    uploaded_file.getvalue(),
                    {"content-type": "application/pdf"}
                )

                file_url = supabase.storage.from_("reports").get_public_url(file_name)
                source = "storage"

            # ============================
            # HANDLE EXTERNAL LINK
            # ============================

            else:

                if not external_link:
                    st.error("Please enter a valid link.")
                    st.session_state.is_uploading = False
                    st.stop()

                file_url = external_link
                source = "external_link"
                file_name = None
                file_size = None

            # ============================
            # GET OPTIONAL FOREIGN KEYS
            # ============================

            project_id = None
            school_id = None
            donor_id = None

            if project != "None":
                project_id = int(
                    projects_df[
                        projects_df["project_name"] == project
                    ]["project_id"].values[0]
                )

            if school != "None":
                school_id = int(
                    schools_df[
                        schools_df["school_name"] == school
                    ]["id"].values[0]
                )

            if donor != "None":
                donor_id = int(
                    donors_df[
                        donors_df["donor_name"] == donor
                    ]["id"].values[0]
                )

            # ============================
            # INSERT INTO DATABASE
            # ============================

            data = {
                "title": title.strip(),
                "description": description.strip() if description else None,
                "document_type": document_type,
                "project_id": project_id,
                "school_id": school_id,
                "donor_id": donor_id,
                "report_year": int(report_year),
                "source_type": source,
                "file_name": file_name,
                "file_url": file_url,
                "file_size": file_size  
            }

            response = supabase.table("reports").insert(data).execute()

            # Store newly uploaded ID for highlight later
            if response.data:
                st.session_state["new_uploaded_id"] = response.data[0]["id"]

        # Reset uploading state
        st.session_state.is_uploading = False

        # Trigger success message
        st.session_state["upload_success"] = True

        # Reset entire form
        st.session_state.form_reset_counter += 1

        st.rerun()

# =====================================================
# DOCUMENT BROWSER
# =====================================================

st.subheader("Browse Documents")

# Fetch ordered data
response = (
    supabase
    .table("reports")
    .select("*")
    .order("uploaded_at", desc=True)
    .execute()
)

docs_df = pd.DataFrame(response.data)

if not docs_df.empty:

    # ----------------------------
    # CLEAN NULLS FOR SAFE FILTERING
    # ----------------------------

    docs_df["document_type"] = docs_df["document_type"].fillna("Unknown")
    docs_df["report_year"] = docs_df["report_year"].fillna(0)

    # ----------------------------
    # FILTER VALUES
    # ----------------------------

    year_values = sorted(
        [y for y in docs_df["report_year"].unique().tolist() if y != 0],
        reverse=True
    )

    type_values = sorted(
        docs_df["document_type"].unique().tolist()
    )

    col1, col2 = st.columns(2)

    with col1:
        year_filter = st.selectbox(
            "Filter by Year",
            ["All"] + year_values
        )

    with col2:
        type_filter = st.selectbox(
            "Filter by Type",
            ["All"] + type_values
        )

    # ----------------------------
    # APPLY FILTERS
    # ----------------------------

    filtered = docs_df.copy()

    if year_filter != "All":
        filtered = filtered[filtered["report_year"] == year_filter]

    if type_filter != "All":
        filtered = filtered[filtered["document_type"] == type_filter]

    if filtered.empty:
        st.info("No documents match selected filters.")

    else:

        # ----------------------------
        # DELETE CONFIRM STATE
        # ----------------------------

        if "confirm_delete_id" not in st.session_state:
            st.session_state.confirm_delete_id = None

        # ----------------------------
        # DISPLAY AS 2 CARDS PER ROW
        # ----------------------------

        cols = st.columns(3)

        for i, (_, row) in enumerate(filtered.iterrows()):

            with cols[i % 3]:

                with st.container(border=True):

                    st.markdown(f"### 📄 {row['title']}")

                    st.caption(
                        f"{row['document_type']} • {row['report_year']}"
                    )

                    if row.get("description"):
                        st.write(row["description"])

                    if row.get("file_url"):

                        if row.get("source_type") == "external_link":
                            st.markdown(
                                f"🌐 [Open External Link]({row['file_url']})",
                                unsafe_allow_html=True
                            )
                            st.caption("External Source")

                        else:
                            st.markdown(
                                f"📄 [Open Document]({row['file_url']})",
                                unsafe_allow_html=True
                            )
                            st.caption("Stored in RFC Repository")

                    if row.get("file_size") and pd.notna(row["file_size"]):
                        st.caption(f"{round(row['file_size'] / (1024*1024), 2)} MB")

                    st.divider()

                    # ----------------------------
                    # DELETE BUTTON
                    # ----------------------------

                    if st.button("🗑 Delete", key=f"delete_{row['id']}"):
                        st.session_state.confirm_delete_id = row["id"]

                    # ----------------------------
                    # CONFIRMATION BLOCK
                    # ----------------------------

                    if st.session_state.confirm_delete_id == row["id"]:

                        st.warning("Are you sure you want to delete this document?")

                        colA, colB = st.columns(2)

                        with colA:
                            if st.button("✅ Yes", key=f"yes_{row['id']}"):

                                try:
                                    # Delete storage file (if needed)
                                    if row.get("source_type") == "storage" and row.get("file_name"):
                                        supabase.storage.from_("reports").remove([row["file_name"]])

                                    # Delete DB row
                                    delete_response = (
                                        supabase
                                        .table("reports")
                                        .delete()
                                        .eq("id", row["id"])
                                        .execute()
                                    )

                                    # Force check
                                    if delete_response.data is not None:

                                        st.session_state.confirm_delete_id = None

                                        # Remove row locally BEFORE rerun
                                        docs_df = docs_df[docs_df["id"] != row["id"]]

                                        st.success("Document deleted successfully!")

                                        st.rerun()

                                    else:
                                        st.error("Delete failed — check RLS or ID.")

                                except Exception as e:
                                    st.error(f"Delete error: {e}")

                        with colB:
                            if st.button("❌ Cancel", key=f"cancel_{row['id']}"):
                                st.session_state.confirm_delete_id = None

else:
    st.info("No documents uploaded yet.")