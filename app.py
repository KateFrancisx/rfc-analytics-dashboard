import streamlit as st
from utils.db import get_client

st.set_page_config(
    page_title="RFC Admin Login",
    layout="centered",
    initial_sidebar_state="collapsed"
)

supabase = get_client()

# Initialize session
if "session" not in st.session_state:
    st.session_state.session = None

# Try restoring existing Supabase session
if st.session_state.session is None:
    try:
        session = supabase.auth.get_session()
        if session:
            st.session_state.session = session
    except:
        pass


def login(email, password):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        st.session_state.session = response
        return True
    except:
        return False


# --------------------------------------------------
# IF NOT LOGGED IN → SHOW LOGIN
# --------------------------------------------------
if not st.session_state.session:

    # Hide sidebar completely
    st.markdown("""
        <style>
        [data-testid="stSidebar"] {display: none;}
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        st.markdown("<div style='text-align:center;'>", unsafe_allow_html=True)
        st.image("rfclogo.png", width=140)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<h1 style='text-align:center;'>Ride For Cause</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:gray;'>Admin Intelligence Dashboard</p>", unsafe_allow_html=True)

    st.markdown("### Admin Login")
    
    
    # ✅ FORM START (this enables Enter key login)
    with st.form("login_form"):

        email = st.text_input("Email")
        password = st.text_input("Password", type="password")

        submitted = st.form_submit_button("Login", use_container_width=True)

        if submitted:
            if login(email, password):
                st.rerun()
            else:
                st.error("Invalid credentials")
        st.markdown("""
        <style>
        div[data-testid="stFormSubmitButton"] > button {
            background-color: #7600bc;
            color: white;
            border-radius: 8px;
        }
        div[data-testid="stFormSubmitButton"] > button:hover {
            background-color: #4c00b0;
            color: white;
        }
        </style>
        """, unsafe_allow_html=True)
    st.stop()


# --------------------------------------------------
# IF LOGGED IN → REDIRECT TO OVERVIEW
# --------------------------------------------------
st.switch_page("pages/1_Overview.py")