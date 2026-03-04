import streamlit as st
from groq import Groq
import pandas as pd
from utils.db import get_client
from utils.layout import inject_global_styles, render_sidebar
import os
from dotenv import load_dotenv

if "session" not in st.session_state or not st.session_state.session:
    st.switch_page("app.py")


st.set_page_config(layout="wide")

inject_global_styles()
render_sidebar()

#supabase = get_client()



load_dotenv()

# Initialize Groq Client (works locally and in deployment)
if "GROQ_API_KEY" in st.secrets:
    groq_key = st.secrets["GROQ_API_KEY"]
else:
    groq_key = os.getenv("GROQ_API_KEY")

client = Groq(api_key=groq_key)


st.title("RFC Assistant")

# Fetch data context from Supabase
def get_dashboard_context():
    supabase = get_client()
    # Fetching school and donor data as context
    schools = supabase.table("schools").select("*").execute().data
    donors = supabase.table("donors").select("*").execute().data
    
    context = "You are the RFC Assistant. Here is our database info:\n"
    context += f"SCHOOLS DATA: {pd.DataFrame(schools).to_string()}\n"
    context += f"DONORS DATA: {pd.DataFrame(donors).to_string()}\n"
    return context

# Chat History
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

#  Chat Logic
if prompt := st.chat_input("Ask about our impact..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        # send the context + the prompt to Groq
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": get_dashboard_context()},
                {"role": "user", "content": prompt}
            ],
            model="llama-3.3-70b-versatile", # High performance model
        )
        response = chat_completion.choices[0].message.content
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})