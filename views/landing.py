import streamlit as st
from ui.legal import render_legal_section

def render_landing(auth_svc):
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Layout - Centered Container using Columns
    # Using [1, 2, 1] ratio for desktop, effectively centering the content in the middle 50%
    col_spacer_left, col_content, col_spacer_right = st.columns([1, 2, 1])

    with col_content:
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Logo
        try: 
            st.image("assets/sCore.png", use_column_width=True) 
        except: 
            st.markdown("<h1 style='text-align: center; color: #FFCF96;'>sCore Lab</h1>", unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)

        # Bottone Strava
        redirect_url = "https://scorerun.streamlit.app/" 
        link_strava = auth_svc.get_auth_url(redirect_url)
        st.link_button("Connetti Strava", link_strava, type="primary", use_container_width=True)
        
        # Demo Mode Link
        if st.button("Prova la Demo", use_container_width=True):
            st.session_state["show_demo_page"] = True
            st.rerun()

    # Footer
    st.markdown("<br><br>", unsafe_allow_html=True)
    render_legal_section()
