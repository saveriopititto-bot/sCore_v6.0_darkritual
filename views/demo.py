import streamlit as st
from services.demo_data import generate_demo_data, get_demo_athlete

def render_demo():
    """
    Pagina dedicata alla Demo Mode.
    Genera dati demo realistici e simula l'esperienza completa della dashboard.
    """
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Layout - Centered Container
    col_spacer_left, col_content, col_spacer_right = st.columns([1, 2, 1])

    with col_content:
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Logo
        try: 
            st.image("assets/sCore.png", use_column_width=True) 
        except: 
            st.markdown("<h1 style='text-align: center; color: #FFCF96;'>sCore Lab</h1>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Demo Info
        st.markdown("""
        <div style='text-align: center; padding: 20px; background: rgba(255,207,150,0.1); border-radius: 12px;'>
            <h3 style='color: #FFCF96; margin: 0;'>🎯 Modalità Demo</h3>
            <p style='color: #888; margin-top: 10px;'>
                Esplora sCore con dati realistici generati automaticamente.<br>
                30 corse simulate con l'algoritmo <strong>ScoreEngine v6 Darkritual</strong>.
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Avvia Demo Button
        if st.button("🚀 Avvia Demo", use_container_width=True, type="primary"):
            # Genera dati demo
            st.session_state["demo_mode"] = True
            st.session_state["authenticated"] = True
            st.session_state["strava_token"] = get_demo_athlete()
            st.session_state["data"] = generate_demo_data()
            st.session_state["initial_sync_done"] = True  # Skip auto-sync
            st.session_state["show_demo_page"] = False  # Exit demo page, go to dashboard
            st.rerun()
        
        # Torna alla Landing
        if st.button("⬅️ Torna alla Home", use_container_width=True):
            st.session_state["demo_mode"] = False
            st.session_state["authenticated"] = False
            st.session_state["strava_token"] = None
            st.session_state["data"] = []
            st.rerun()
