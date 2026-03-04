import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv
import pandas as pd

# Load environment variables 
#load_dotenv()
#SUPABASE_URL = st.secrets.get("SUPABASE_URL", os.getenv("SUPABASE_URL"))
#SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", os.getenv("SUPABASE_KEY"))
load_dotenv()

try:
    SUPABASE_URL = st.secrets["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
except:
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

@st.cache_resource
def get_client() -> Client:
    """Initializes and caches the Supabase client."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("Supabase credentials not found. Check your .env file or Streamlit secrets.")
        st.stop()
    return create_client(SUPABASE_URL, SUPABASE_KEY)


@st.cache_data(ttl=300)
def load_all_data(_supabase):
    return {
        "schools": pd.DataFrame(
            _supabase.table("schools").select("*").execute().data
        ),
        "projects": pd.DataFrame(
            _supabase.table("projects").select("*").execute().data
        ),
        "project_types": pd.DataFrame(
            _supabase.table("project_types").select("*").execute().data
        ),
        "project_project_types": pd.DataFrame(
            _supabase.table("project_project_types").select("*").execute().data
        ),
        "project_components": pd.DataFrame(
            _supabase.table("project_components").select("*").execute().data
        ),
        "project_donors": pd.DataFrame(
            _supabase.table("project_donors").select("*").execute().data
        ),
        "donors": pd.DataFrame(
            _supabase.table("donors").select("*").execute().data
        ),
    }