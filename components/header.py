import streamlit as st

def render_header():
    # Logout and Theme moved to athlete section or hidden
    col_header, _ = st.columns([1, 0.1])
    with col_header:
        try: st.image("assets/sCore.png", width=220) 
        except: st.title("sCore Lab 4.1")
