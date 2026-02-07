import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
from config import Config

def render_top_section(auth_svc, db_svc):

    """
    Renderizza Avatar, Parametri Fisiologici e il Calendario Interattivo.
    Layout: Navbar style (Split Sinistra/Destra).
    """
    
    # 1. Recupero Contesto Atleta
    ath = st.session_state.strava_token.get("athlete", {})
    athlete_id = ath.get("id")
    athlete_name = f"{ath.get('firstname', 'Atleta')} {ath.get('lastname', '')}"
    
    # Demo mode indicator
    if st.session_state.get("demo_mode", False):
        athlete_name = f"🎮 {athlete_name} (Demo)"
    
    
    if not athlete_id:
        st.error("Errore: ID Atleta non trovato.")
        return {}, False, 0

    # 2. Recupero Profilo dal DB
    saved_profile = db_svc.get_athlete_profile(athlete_id)
    
    # Impostazione Valori (Default o DB)
    weight = saved_profile.get('weight', Config.DEFAULT_WEIGHT) if saved_profile else Config.DEFAULT_WEIGHT
    ftp = saved_profile.get('ftp', Config.DEFAULT_FTP) if saved_profile else Config.DEFAULT_FTP
    hr_max = saved_profile.get('hr_max', Config.DEFAULT_HR_MAX) if saved_profile else Config.DEFAULT_HR_MAX
    hr_rest = saved_profile.get('hr_rest', Config.DEFAULT_HR_REST) if saved_profile else Config.DEFAULT_HR_REST
    age = saved_profile.get('age', Config.DEFAULT_AGE) if saved_profile else Config.DEFAULT_AGE
    sex = saved_profile.get('sex', 'M') if saved_profile else 'M'
    
    # --- UI LAYOUT: CUSTOM NAVBAR ---
    # CSS styles are now in ui/style.css
    
    # Start Navbar HTML
    st.markdown('<div class="custom-navbar">', unsafe_allow_html=True)
    
    # Left Section (Avatar + Name) - usando HTML puro
    st.markdown(f"""
        <div class="navbar-left">
            <img src="{ath.get('profile_medium', 'https://via.placeholder.com/150')}" 
                 class="navbar-avatar" 
                 alt="Avatar">
            <div class="navbar-name">
                <div class="navbar-name-text">{athlete_name}</div>
                <div class="navbar-id">ID: {athlete_id}</div>
            </div>
        </div>
        <div class="navbar-spacer"></div>
    """, unsafe_allow_html=True)
    
    # Right Section (Buttons) - usando Streamlit columns per i bottoni interattivi
    st.markdown('<div class="navbar-right">', unsafe_allow_html=True)
    
    # Uso columns per mantenere i bottoni Streamlit funzionanti
    btn_period, btn_logout = st.columns(2, gap="small")
    
    # Period Button

    with btn_period:
        default_start = datetime.now().date() - timedelta(days=90)
        default_end = datetime.now().date()
        current_start = st.session_state.get("filter_start_date", default_start)
        current_end = st.session_state.get("filter_end_date", default_end)
        days_diff = (current_end - current_start).days
        
        with st.popover(f"📅 {days_diff} gg", width='stretch'):
            st.markdown("### Intervallo")
            d1, d2 = st.columns(2)
            new_start = d1.date_input("Dal", current_start, max_value=datetime.now().date(), format="DD/MM/YYYY")
            new_end = d2.date_input("Al", current_end, max_value=datetime.now().date(), min_value=new_start, format="DD/MM/YYYY")
            
            st.divider()
            if st.button("🔎 Analizza", type="primary", width='stretch'):
                st.session_state.filter_start_date = new_start
                st.session_state.filter_end_date = new_end
                with st.spinner("Sync..."):
                    from controllers.sync_controller import SyncController
                    SyncController(auth_svc, db_svc).sync_activities(max((datetime.now().date() - new_start).days, 1))
                st.rerun()
            
            if st.button("⬅️ Reset", width='stretch'):
                st.session_state.filter_start_date = default_start
                st.session_state.filter_end_date = default_end
                st.rerun()
    
    # Logout Button
    with btn_logout:
        if st.button("eSci", help="Esci / Logout", key="logout_btn_top", width='stretch'):
            st.session_state.strava_token = None
            st.session_state.demo_mode = False
            if "strava_zones" in st.session_state: del st.session_state.strava_zones
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)  # Close navbar-right
    st.markdown('</div>', unsafe_allow_html=True)  # Close custom-navbar

    # Preparazione Output per Dashboard
    phys_params = {
        "weight": weight,
        "ftp": ftp,
        "hr_max": hr_max,
        "hr_rest": hr_rest,
        "age": age,
        "sex": sex
    }
    
    return phys_params, False, 0
