import streamlit as st
from config import Config
from ui import visuals

def render_kpi_grid(cur_run, quality_data, trend_data, consistency_data, ef_data, zones_data):
    """
    Renders the full Neon KPI Grid:
    - Top Row: Percentile | Score | Drift
    - Bottom Row: Quality | Trend | Constcy | EF | Z5
    """
    
    # --- 1. PREPARE DATA ---
    details = cur_run.get('SCORE_DETAIL', {})
    pb_val = details.get('pb_pct', cur_run.get('WR_Pct', 0.0))
    
    # Top Row Components
    html_pct = visuals.render_kpi_percentile(pb_val)
    html_score = visuals.render_kpi_score(cur_run.get('SCORE', 0.0))
    html_drift = visuals.render_kpi_drift(cur_run.get('Decoupling', 0.0))
    
    # Bottom Row Components
    html_quality = visuals.quality_circle(quality_data)
    html_trend = visuals.trend_circle(trend_data)
    html_constcy = visuals.consistency_circle(consistency_data)
    html_ef = visuals.efficiency_circle(ef_data)
    
    # Z5 Badge Logic
    # We find the max zone for the Badge, or just default to Z5 as per request?
    # HTML says "Z5" with ring-gradient-orange-red. 
    # Let's find the dominant zone or Z5.
    # Logic: Find max zone 
    dom_zone = "Z5"
    if zones_data:
        dom_zone = max(zones_data, key=zones_data.get)
    
    # Map colors/rings for Zones
    ring_class = "ring-gradient-orange-red" # Default red/yellow
    if dom_zone == "Z2" or dom_zone == "Z1": ring_class = "border-[2px] border-blue-400"
    elif dom_zone == "Z3": ring_class = "ring-gradient-green"
    
    html_zones = visuals.zones_circle_badge(dom_zone, "", pct=0) # pct unused in badge


    # --- 2. RENDER CONTAINER ---
    st.markdown(f"""
    <div class="flex flex-col items-center justify-center gap-2 mb-6 mt-4">
        
        <!-- TOP ROW: CIRCLES -->
        <div class="flex flex-row justify-center items-center gap-1 md:gap-2 -mb-2 z-10 scale-95 origin-bottom">
            {html_pct}
            {html_score}
            {html_drift}
        </div>
        
        <!-- BOTTOM ROW: BADGES -->
        <div class="flex flex-wrap justify-center gap-1 md:gap-2 mt-0 z-0">
            {html_quality}
            {html_trend}
            {html_constcy}
            {html_ef}
            {html_zones}
        </div>
        
    </div>
    """, unsafe_allow_html=True)
