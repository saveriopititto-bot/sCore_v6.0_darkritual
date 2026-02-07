import streamlit as st
import logging

# --- 1. CONFIG & VALIDATION ---
from config import Config

# Setup Logging
logger = Config.setup_logging()
logger.info("Starting sCore App...")

missing_secrets = Config.check_secrets()
if missing_secrets:
    st.error(f"❌ Segreti mancanti: {', '.join(missing_secrets)}")
    st.stop()

import sys
import os

# Ensure root is in path
root_path = os.path.dirname(__file__)
if root_path not in sys.path:
    sys.path.append(root_path)

try:
    from services.strava_api import StravaService
except ImportError as e:
    st.error(f"❌ Import Error: {e}")
    st.error(f"Current Path: {sys.path}")
    # Check if requests is installed
    try:
        import requests
        st.success("Requests module is installed.")
    except ImportError:
        st.error("Requests module is NOT installed.")
    st.stop()
from services.db import DatabaseService
from ui.state_manager import get_state

# Initialize State
state = get_state()

# Views
from views.landing import render_landing
from views.demo import render_demo
from views.dashboard import render_dashboard

# --- 3. PAGE SETUP ---
st.set_page_config(
    page_title=Config.APP_TITLE, 
    page_icon=Config.APP_ICON, 
    layout="wide", 
    initial_sidebar_state="collapsed"
)

# Apply Theme
from ui.style import apply_theme
apply_theme(state.theme)

# --- DEV MODE ROUTING ---
if state.dev_mode:
    from ui.dev_console import render_dev_console
    render_dev_console()
    st.stop()


# --- 4. SERVIZI ---
strava_creds = Config.get_strava_creds()
supa_creds = Config.get_supabase_creds()
auth_svc = StravaService(strava_creds["client_id"], strava_creds["client_secret"])
db_svc = DatabaseService(supa_creds["url"], supa_creds["key"])

# --- 5. STATE ---
# Initialize data only AFTER authentication
if not state.data:
    if state.strava_token:
        # Get athlete ID from token
        ath = state.strava_token.get("athlete", {})
        athlete_id = ath.get("id")
        state.data = db_svc.get_history(athlete_id) if athlete_id else []
    else:
        state.data = []

# Callback Strava
if "code" in st.query_params and not state.strava_token:
    tk = auth_svc.exchange_token(st.query_params["code"])
    if tk: 
        state.strava_token = tk
        st.query_params.clear()
        st.rerun()

# =========================================================
# LOGICA PRINCIPALE (ROUTING)
# =========================================================

# Demo Page Routing
if state.show_demo_page:
    render_demo()
elif not state.strava_token:
    render_landing(auth_svc)
else:
    render_dashboard(auth_svc, db_svc)
