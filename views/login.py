import streamlit as st
import time
from config import Config

def render_login():
    """
    Renders the Login Page with Glassmorphic UI.
    Returns True if login is successful (simulated), False otherwise.
    """
    
    # Center the login card
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown(f"""
        <div style="
            background: rgba(255, 255, 255, 0.05);
            backdrop-filter: blur(20px);
            -webkit-backdrop-filter: blur(20px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            border-radius: 20px;
            padding: 40px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.2);
            text-align: center;
        ">
            <h2 style="color: {Config.Theme.PRIMARY}; margin-bottom: 20px; font-weight: 800; letter-spacing: -1px;">WELCOME BACK</h2>
            <p style="color: #888; margin-bottom: 30px; font-size: 0.9rem;">Sign in to access your dashboard</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Placeholder Form
        with st.form("login_form"):
            username = st.text_input("Username", placeholder="admin")
            password = st.text_input("Password", type="password", placeholder="••••••")
            
            submitted = st.form_submit_button("SIGN IN", type="primary", width='stretch')
            
            if submitted:
                if username == "admin" and password == "1234":
                    st.success("Login successful! Redirecting...")
                    time.sleep(1)
                    from ui.state_manager import get_state
                    get_state().authenticated = True
                    st.rerun()
                else:
                    st.error("Invalid credentials. Try admin / 1234")
    
    from ui.state_manager import get_state
    return get_state().authenticated
