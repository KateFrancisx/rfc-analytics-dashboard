import streamlit as st
import pandas as pd
from utils.layout import inject_global_styles, render_sidebar
from utils.db import get_client



if "session" not in st.session_state or not st.session_state.session:
    st.switch_page("app.py")


st.set_page_config(layout="wide")

inject_global_styles()
render_sidebar()

supabase = get_client()

@st.cache_data
def get_map_data():
    # We only need lat and lon for the basic map
    res = supabase.table("schools").select("school_name, latitude, longitude, district").execute()
    df = pd.DataFrame(res.data)
    # Ensure coordinates are numbers and not empty
    df = df.dropna(subset=['latitude', 'longitude'])
    return df

st.title("📍 Project Locations")
st.markdown("Project areas accross the globe.")

df = get_map_data()

# 3. Simple Map
# st.map automatically looks for columns named 'latitude' and 'longitude'
if not df.empty:
    st.map(df, color="#DC1E1E", size=20) 
else:
    st.error("No coordinate data found in Supabase.")

# 4. Data Table for Details
st.subheader("Project Directory")
st.dataframe(df[['school_name', 'district']], use_container_width=True)