import streamlit as st
from datetime import datetime


def render_legal_section():
    year = datetime.now().year
    
    # Wrapper per font Montserrat + Responsive CSS
    st.markdown("""
        <style>
        .footer-minimal {
            font-family: 'Montserrat', sans-serif !important;
            margin-top: 50px;
        }
        
        /* Responsive Footer Bottom */
        .footer-bottom {
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 15px;
            font-size: 0.8rem;
            color: #636E72;
            margin-top: 20px;
        }
        
        .footer-bottom span {
            flex: 1 1 auto;
            min-width: 200px;
            text-align: center;
        }
        
        @media (max-width: 768px) {
            .footer-bottom {
                flex-direction: column;
                text-align: center;
                gap: 10px;
            }
            
            .footer-bottom span {
                min-width: 100%;
            }
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.divider()
    
    with st.container():
        st.markdown('<div class="footer-minimal">', unsafe_allow_html=True)
        # Grid minimale con Streamlit native - responsive ratios
        col1, col2 = st.columns([3, 1.5])
        
        with col1:
            titolo = "sCore Lab v1.0"
            descrizione = "Powered by <strong>sCorengine 4.1</strong>"
            testo = f"{titolo}<br>{descrizione}"

            st.markdown(f"""
            <div style="text-align: left; margin-bottom: 30px;">
                <p style="color: #636E72; font-size: 1.1rem; margin: 0;">
                    {testo}<br>
                    Il nuovo standard per l'analisi della corsa.
                </p>
            </div>
            """, unsafe_allow_html=True)
                
        with col2:
            st.markdown("**Legale**")
            st.page_link("pages/privacy.py", label="Privacy Policy", icon="🔒")
            st.page_link("pages/terms.py", label="Terms of Service", icon="📜")

        st.markdown("---")
        st.markdown(f"""
<div class="footer-bottom">
    <span>© {year} Progetto indipendente sviluppato in Python</span>
    <span>Non è uno strumento medico. Interpreta i dati con consapevolezza.</span>
    <span>All rights reserved · sCore Lab</span>
</div>
""", unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)
