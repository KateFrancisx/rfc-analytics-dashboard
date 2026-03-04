import streamlit as st
from utils.db import get_client


# =========================================================
# GLOBAL STYLES
# =========================================================

def inject_global_styles():
    st.markdown("""
    <style>

        /* ------------------------------------------------- */
        /* HIDE DEFAULT STREAMLIT MULTIPAGE NAVIGATION      */
        /* ------------------------------------------------- */
        section[data-testid="stSidebarNav"] {
            display: none;
        }

        /* Remove extra top spacing in sidebar */
        section[data-testid="stSidebar"] > div:first-child {
            padding-top: 1rem;
        }

        /* Optional: improve sidebar scroll behavior */
        section[data-testid="stSidebar"] {
            overflow-y: auto;
        }


        /* ----------------------------- */
        /* SIDEBAR NAVIGATION STYLING   */
        /* ----------------------------- */

        /* Target sidebar navigation items container */
        section[data-testid="stSidebar"] ul {
            padding-left: 0;
        }

        /* Remove default grey highlight */
        section[data-testid="stSidebar"] li {
            list-style: none;
            border-radius: 10px;
            transition: all 0.2s ease-in-out;
        }

        /* Hover effect (apply to li, not a) */
        section[data-testid="stSidebar"] li:hover {
            background-color: #ca5cdd !important;
        }

        /* Active tab (Streamlit sets data-active on the <a>) */
        section[data-testid="stSidebar"] li:has(a[data-active="true"]) {
            background-color: #b100cd !important;
            border-radius: 10px;
        }

        /* Make active text white */
        section[data-testid="stSidebar"] a[data-active="true"],
        section[data-testid="stSidebar"] a[data-active="true"] span {
            color: white !important;
            font-weight: 600 !important;
        }
                    
        
        /* ---------------------------
        LOGOUT BUTTON STYLING
        ----------------------------*/

        /* Logout button only */
        section[data-testid="stSidebar"] div.stButton > button {
            background-color: #b100cd !important;
            color: white !important;
            border-radius: 8px !important;
            border: none !important;
            width: 100%;
        }

        section[data-testid="stSidebar"] div.stButton > button:hover {
            background-color: #ca5cdd !important;
            color: white !important;
        }

        section[data-testid="stSidebar"] button:hover {
            background-color: #ca5cdd !important;
            color: white !important;
        }


    </style>
    """, unsafe_allow_html=True)


# =========================================================
# CUSTOM SIDEBAR
# =========================================================

def render_sidebar():

    # Do not render sidebar if not logged in
    if "session" not in st.session_state or not st.session_state.session:
        return

    supabase = get_client()

    with st.sidebar:

        # -----------------------------
        # LOGO + TITLE
        # -----------------------------
        st.image("rfclogo.png", width=120)
        st.markdown("## Ride For Cause")

        st.divider()

        # -----------------------------
        # NAVIGATION (ONLY THESE PAGES)
        # -----------------------------
        st.page_link("pages/1_Overview.py", label="Overview")
        st.page_link("pages/2_School_Projects.py", label="Schools & Projects")
        st.page_link("pages/3_Volunteer_Engagement.py", label="Volunteer Engagement")
        st.page_link("pages/4_Sustainability_Environment.py", label="Sustainability & Environment")
        st.page_link("pages/5_Geo_Spatial_GIS.py", label="Geo Spatial GIS")
        st.page_link("pages/6_Donors_Sponsors.py", label="Donors Sponsors")
        st.page_link("pages/7_AI_Chat_Assistant.py", label="AI Chat Assistant")
        st.page_link("pages/8_Reports_Documents.py", label="Reports & Documents")

        st.divider()

        # -----------------------------
        # SESSION STATUS
        # -----------------------------
        st.success("Logged in")

        if st.button("Logout", use_container_width=True):
            supabase.auth.sign_out()
            st.session_state.session = None
            st.session_state.user = None
            st.switch_page("app.py")

