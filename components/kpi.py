import streamlit as st
from config import Config
from ui import visuals

def render_kpi_grid(cur_run, score_color_override=None):
    """
    Renders the main KPI grid using Circular Design.
    Uses Glassmorphic class for background consistency.
    Now includes FULL MOBILE RESPONSIVENESS for text scaling.
    """

    MAX_WIDTH_MOBILE = "768px"

    MAX_WIDTH_MOBILE = "768px"

    # 1. GENERATE HTML USING VISUALS HELPERS
    # Usiamo pb_pct (Personal Best %) dai dettagli, con fallback su WR_Pct
    details = cur_run.get('SCORE_DETAIL', {})
    pb_val = details.get('pb_pct', cur_run.get('WR_Pct', 0.0))
    
    html_pct = visuals.render_kpi_percentile(pb_val)
    html_score = visuals.render_kpi_score(cur_run.get('SCORE', 0.0))
    html_drift = visuals.render_kpi_drift(cur_run.get('Decoupling', 0.0))

    # 2. RENDER FLEX CONTAINER
    st.markdown(f"""
    <div style="display: flex; justify-content: center; align-items: center; margin-top: 10px; flex-wrap: wrap; gap: 10px;">
        {html_pct}
        {html_score}
        {html_drift}
    </div>
    """, unsafe_allow_html=True)
