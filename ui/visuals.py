import streamlit as st
import pandas as pd
import altair as alt
from config import Config

# --- 1. BUSINESS LOGIC (COLOR HELPERS) ---

def get_score_color(score):
    try: val = float(score)
    except: val = 0.0
    if val <= Config.Thresholds.WEAK: return Config.Theme.SCORE_WEAK
    if val <= Config.Thresholds.SOLID: return Config.Theme.SCORE_SOLID
    if val <= Config.Thresholds.GREAT: return Config.Theme.SCORE_GREAT
    return Config.Theme.SCORE_EPIC

def get_percentile_color(pct):
    try: val = float(pct)
    except: val = 0.0
    if val > 75: return Config.SCORE_COLORS['good']
    if val > 50: return Config.SCORE_COLORS['ok']
    if val > 25: return Config.SCORE_COLORS['neutral']
    return Config.SCORE_COLORS['bad']

def get_drift_color(drift):
    try: val = float(drift)
    except: val = 0.0
    if val > 5.0: return Config.SCORE_COLORS['bad']
    if val > 3.0: return Config.SCORE_COLORS['ok']
    return Config.SCORE_COLORS['good']

def get_score_tier(value, metric_type="score"):
    """Returns tier name (epic/great/solid/weak) for CSS data-attribute."""
    try: 
        val = float(value)
    except: 
        return "weak"
    
    if metric_type == "score":
        if val >= Config.Thresholds.EPIC: return "epic"
        if val >= Config.Thresholds.GREAT: return "great"
        if val >= Config.Thresholds.SOLID: return "solid"
        return "weak"
    elif metric_type == "drift":
        if val <= 3.0: return "epic"
        if val <= 5.0: return "great"
        if val <= 7.0: return "solid"
        return "weak"
    elif metric_type == "percentile":
        if val > 75: return "epic"
        if val > 50: return "great"
        if val > 25: return "solid"
        return "weak"
    return "weak"

# --- 2. UNIVERSAL RENDERING COMPONENT ---

def render_stat_card(value, label, color, size=155, variant="simple", progress=0.0, margin_fix=None, tier=None):
    """
    Universal component to render a circular stat card.
    
    Args:
        variant (str): "simple" (border), "glass" (border+glass), "progress" (svg dash)
        margin_fix (str): "left" | "right" | None (for negative margins)
        tier (str): Score tier for dynamic hover (epic/great/solid/weak)
    """
    # Style Overrides
    margin_style = ""
    if margin_fix == "right": margin_style = "margin-right: -25px; z-index: 1;"
    elif margin_fix == "left": margin_style = "margin-left: -25px; z-index: 1;"
    
    # Base CSS Classes
    container_class = "stat-circle"
    if variant == "glass": container_class += " glass-card"
    
    # Data attribute for tier-based hover
    tier_attr = f'data-score-tier="{tier}"' if tier else ""
    
    # 1. VARIANT: SCORE PROGRESS (Central SVG)
    if variant == "progress":
        circumference = 691
        dash_val = (progress / 100) * circumference
        return f"""<div class="score-circle-container" {tier_attr} style="display: flex; justify-content: center; cursor: default; position: relative; z-index: 10;">
<div style="position: relative; width: {size}px; height: {size}px;">
<svg class="score-circle-svg" width="{size}" height="{size}" style="position: absolute; top:0; left:0; transform: rotate(-90deg);">
<circle cx="{size/2}" cy="{size/2}" r="{size/2 - 5}" stroke="rgba(255,255,255,0.15)" stroke-width="8" fill="transparent" />
<circle class="progress" cx="{size/2}" cy="{size/2}" r="{size/2 - 5}" style="stroke: {color} !important; stroke-dasharray: {dash_val}, 1000; stroke-width: 8px !important;" />
</svg>
<div style="position: absolute; top:15px; left:15px; width: {size-30}px; height: {size-30}px; border-radius: 50%; display: flex; flex-direction: column; align-items: center; justify-content: center; z-index: 10; padding:0; box-shadow:none; border: 5.5px solid {color}; background: #FFFFFF;">
<span style="opacity: 0.7; font-size: 0.9rem; font-weight: 700; letter-spacing: 1px;">{label}</span>
<span style="color: {color}; font-size: 5rem; font-weight: 800; line-height: 0.9;">{value}</span>
</div>
</div>
</div>"""

    # 2. VARIANT: GLASS / SIMPLE (Border Based)
    # Glass variant uses 'glass-card' class and thinner font for Label
    return f"""<div class="{container_class}" {tier_attr} style="--border-color: {color}; width: {size}px; height: {size}px; border: 4px solid {color}; display: flex; flex-direction: column; align-items: center; justify-content: center; padding:0; {margin_style}">
<span style="opacity: 0.7; font-size: 0.70rem; font-weight: 700;">{label}</span>
<span style="color: {color}; font-size: 2.5rem; font-weight: 800; line-height: 1;">{value}</span>
</div>"""

# --- 3. PUBLIC API (CONSUMERS) ---

# Legacy / Simple Circles (Dashboard Bottom)
def score_circle(score):
    tier = get_score_tier(score, "score")
    return render_stat_card(f"{float(score):.1f}", "", get_score_color(score), size=150, variant="simple", tier=tier)

def drift_circle(drift):
    tier = get_score_tier(drift, "drift")
    return render_stat_card(f"{float(drift):.1f}%", "", get_drift_color(drift), size=115, variant="simple", tier=tier)

def quality_circle(q):
    if not isinstance(q, dict): return render_stat_card(str(q) if q else "N/A", "QUALITY", "#888", size=115)
    
    label = q.get("label", "N/A").split()[0]
    color = q.get("color", "#888")
    return render_stat_card(label, "QUALITY", color, size=115)

def trend_circle(tr):
    direction = tr.get("direction", "flat")
    if direction == "up": icon, color = "▲", Config.Theme.SECONDARY
    elif direction == "down": icon, color = "▼", Config.Theme.DANGER
    else: icon, color = "●", Config.Theme.SCORE_EPIC
    return render_stat_card(icon, "TREND", color, size=115)

def consistency_circle(cons_data):
    if not cons_data or "score" not in cons_data:
        return render_stat_card("N/A", "CONSTCY", Config.Theme.SCORE_EPIC, size=115)
    
    score = cons_data.get("score", 0)
    color = Config.Theme.DANGER
    if score >= 80: color = Config.Theme.SECONDARY
    elif score >= 60: color = Config.Theme.PRIMARY
    elif score >= 40: color = Config.Theme.ACCENT
    
    return render_stat_card(f"{int(score)}", "CONSTCY", color, size=115)

def efficiency_circle(ef_data):
    if not ef_data or ef_data.get("ef", 0) == 0:
        return render_stat_card("—", "EF", Config.Theme.SCORE_EPIC, size=115)
    
    ef = ef_data.get("ef", 0)
    interpretation = ef_data.get("interpretation", "")
    
    color = "#6B7280"
    if "Elite" in interpretation or "Pro" in interpretation: color = "#8B5CF6"
    elif "Very Good" in interpretation: color = Config.Theme.PRIMARY
    elif "Good" in interpretation: color = Config.Theme.SECONDARY
    
    return render_stat_card(f"{ef}", "EF", color, size=115)

# Modern KPI Renderers (Top Grid)
def render_kpi_percentile(val):
    tier = get_score_tier(val, "percentile")
    return render_stat_card(
        f"{float(val):.1f}%", 
        "PERCENTILE", 
        get_percentile_color(val), 
        size=155, 
        variant="glass",
        tier=tier
    )

def render_kpi_drift(val):
    tier = get_score_tier(val, "drift")
    return render_stat_card(
        f"{float(val):.1f}%", 
        "DRIFT", 
        get_drift_color(val), 
        size=155, 
        variant="glass",
        tier=tier
    )

def render_kpi_score(score):
    try: s_val = float(score)
    except: s_val = 0.0
    tier = get_score_tier(s_val, "score")
    return render_stat_card(
        f"{s_val:.1f}", 
        "SCORE", 
        get_score_color(s_val), 
        size=230, 
        variant="progress", 
        progress=s_val,
        tier=tier
    )

def render_quality_badge(label, color_key="neutral"): pass 
def render_trend_card(delta): pass
def get_coach_feedback(trend): return "Analysis running..."

# --- CHARTS ---

def _apply_chart_style(chart):
    return chart.configure_view(
        strokeWidth=0
    ).configure_axis(
        grid=False,
        domain=False,
        labelFont='Manrope',
        titleFont='Manrope',
        labelColor='#888',
        titleColor='#888'
    ).configure_legend(
        labelFont='Manrope',
        titleFont='Manrope',
        labelColor='#888',
        titleColor='#888'
    ).properties(
        
    )

def render_benchmark_chart(df):
    st.markdown("##### 📊 Distribuzione Punteggi")
    if df.empty:
        st.info("Dati insufficienti.")
        return

    base = alt.Chart(df).encode(
        x=alt.X('SCORE:Q', bin=alt.Bin(maxbins=10), title='Score'),
        y=alt.Y('count()', title='Frequency')
    )
    chart = base.mark_bar(color=Config.SCORE_COLORS['neutral'], cornerRadiusTopLeft=5, cornerRadiusTopRight=5).properties(
        height=200,
        background='rgba(0,0,0,0)'
    )
    
    st.altair_chart(_apply_chart_style(chart), width='stretch')

    st.altair_chart(_apply_chart_style(chart), width='stretch')

def zones_circle(zones_data: dict):
    """
    Renders a donut chart using CSS conic-gradient representing 5 zones.
    zones_data: {'Z1': 20.0, 'Z2': 30.0, ...}
    """
    if not zones_data:
         return render_stat_card("N/A", "ZONES", Config.Theme.SCORE_WEAK, size=155, variant="simple")

    # 1. Parse Data & Determine Dominant Zone
    # Standardize keys to Z1..Z5
    labels = ["Z1", "Z2", "Z3", "Z4", "Z5"]
    values = [zones_data.get(k, 0.0) for k in labels]
    
    # Normalize if needed (should sum to 100)
    total = sum(values)
    if total <= 0: return render_stat_card("N/A", "ZONES", Config.Theme.SCORE_WEAK, size=155, variant="simple")
    
    # Colors for Z1-Z5 (Matching reference image: Blue, Orange, Green)
    # Z1=Gray, Z2=Blue, Z3=Green, Z4=Orange, Z5=Red
    palette = ["#A0AEC0", "#4A90E2", "#10B981", "#F59E0B", "#EF4444"]
    
    # 2. Build Gradient String with gaps for visibility
    gradient_parts = []
    current_pct = 0.0
    
    max_val = -1
    dom_zone = "Z1"
    dom_color = palette[0]
    
    for i, val in enumerate(values):
        if val > 0:
            color = palette[i]
            start = current_pct
            end = current_pct + val
            
            # Add small gap (0.5%) between segments for better visibility
            if gradient_parts:
                gap_start = current_pct - 0.5
                gradient_parts.append(f"transparent {gap_start:.1f}% {start:.1f}%")
            
            gradient_parts.append(f"{color} {start:.1f}% {end:.1f}%")
            current_pct = end
            
            if val > max_val:
                max_val = val
                dom_zone = labels[i]
                dom_color = color

    gradient_css = f"conic-gradient({', '.join(gradient_parts)})"
    
    # 3. Render HTML - Thicker donut to match reference
    size_px = 115
    thickness = 26  # Scaled thickness
    inner_size = size_px - (thickness * 2)
    
    return f"""
    <div style="display:flex; justify-content:center;">
      <div class="stat-circle-zones" style="
        position: relative;
        width: {size_px}px; 
        height: {size_px}px; 
        border-radius: 50%; 
        background: {gradient_css};
        display: flex; align-items: center; justify-content: center;
        padding: 0;
      ">
        <!-- Inner Circle (Hole) -->
        <div style="
            width: {inner_size}px; 
            height: {inner_size}px; 
            background: white; 
            border-radius: 50%;
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            color: {dom_color};
            box-shadow: inset 0 2px 8px rgba(0,0,0,0.08);
        ">
            <span style="font-size: 24px; font-weight: 800; line-height: 1; letter-spacing: -0.5px;">{dom_zone}</span>
        </div>
      </div>
    </div>
    """

def render_zones_chart(zones, title="⚡ Zone Potenza"):
    st.markdown(f"##### {title}")
    if not zones:
        st.info("Dati non disponibili.")
        return

    df_zones = pd.DataFrame(list(zones.items()), columns=['Zona', 'Percentuale'])
    
    # Custom Palette for Zones
    colors = [Config.SCORE_COLORS['ok'], Config.SCORE_COLORS['ok'], Config.SCORE_COLORS['neutral'], Config.SCORE_COLORS['neutral'], Config.SCORE_COLORS['bad']]
    
    chart = alt.Chart(df_zones).mark_bar(cornerRadiusEnd=5).encode(
        x=alt.X('Zona', sort=None, axis=alt.Axis(labelAngle=0)),
        y=alt.Y('Percentuale', title=None),
        color=alt.Color('Zona', scale=alt.Scale(range=colors), legend=None),
        tooltip=['Zona', 'Percentuale']
    ).properties(
        height=200,
        background='rgba(0,0,0,0)'
    )

    st.altair_chart(_apply_chart_style(chart), width='stretch')

from engine.metrics import MetricsCalculator

def calculate_efficiency_factor(watts: list, hr: list) -> dict:
    """Wrapper for MetricsCalculator.calculate_efficiency_factor"""
    return MetricsCalculator.calculate_efficiency_factor(watts, hr)

def render_scatter_chart(watts, hr):
    st.markdown("##### ❤️ Power vs HR")
    if not watts or not hr:
        st.info("Stream dati mancanti.")
        return

    # Calcola Efficiency Factor
    ef_data = calculate_efficiency_factor(watts, hr)
    
    df = pd.DataFrame({'Watts': watts[::10], 'HR': hr[::10]}) # Sampled
    
    chart = alt.Chart(df).mark_circle(size=60, opacity=0.4).encode(
        x=alt.X('Watts', title='Power (W)'),
        y=alt.Y('HR', title='Heart Rate (bpm)', scale=alt.Scale(zero=False)),
        color=alt.value(Config.SCORE_COLORS['neutral']),
        tooltip=['Watts', 'HR']
    ).interactive().properties(
        height=300,
        background='rgba(0,0,0,0)'
    )
    
    st.altair_chart(_apply_chart_style(chart), width='stretch')
    
    # Mostra Efficiency Factor sotto il grafico
    if ef_data['ef'] > 0:
        st.caption(f"**Efficiency Factor:** {ef_data['ef']} ({ef_data['interpretation']}) | Avg: {ef_data['avg_power_clean']}W @ {ef_data['avg_hr_clean']} bpm")

def render_history_table(df):
    if df.empty:
        st.text("Nessun dato.")
        return

    cols_to_show = ['Data', 'Dist (km)', 'Time', 'Pace', 'HR', 'Power', 'SCORE']
    rename_map = {'Dist (km)': 'KM'}
    
    # Filtro colonne disponibili
    available_cols = [c for c in cols_to_show if c in df.columns]
    display_df = df[available_cols].rename(columns=rename_map).copy()
    
    # Format Date DD/MM/YYYY
    if 'Data' in display_df.columns:
        display_df['Data'] = pd.to_datetime(display_df['Data']).dt.strftime('%d/%m/%Y')
    
    st.dataframe(
        display_df,
        width='stretch',
        hide_index=True,
        height=300,
        column_config={
            "SCORE": st.column_config.NumberColumn("Score", format="%.1f"),
            "Power": st.column_config.NumberColumn("Watt", format="%d w"),
            "HR": st.column_config.NumberColumn("FC", format="%d bpm"),
            "KM": st.column_config.NumberColumn("KM", format="%.1f km")
        }
    )

def render_trend_chart(df):
    st.markdown("##### 📈 Smart Trend")
    if df.empty:
        st.info("Nessun dato SCORE disponibile.")
        return

    cols = ['Data', 'SCORE']
    if 'SCORE_MA_7' in df.columns: cols.append('SCORE_MA_7')
        
    chart_data = df[cols].copy().dropna(subset=["SCORE"]).sort_values("Data")
    chart_data['Data'] = pd.to_datetime(chart_data['Data'])
    
    y_col = 'SCORE_MA_7' if 'SCORE_MA_7' in df.columns else 'SCORE'

    base = alt.Chart(chart_data).encode(x='Data:T')

    # Line Chart using Neutral Color (Focus)
    line = base.mark_line(color=Config.SCORE_COLORS['neutral'], strokeWidth=3).encode(
        y=alt.Y(y_col, scale=alt.Scale(zero=False), title=None)
    )
    
    # Area gradient
    area = base.mark_area(
        line=False,
        color=alt.Gradient(
            gradient='linear',
            stops=[alt.GradientStop(color=Config.SCORE_COLORS['neutral'], offset=0),
                   alt.GradientStop(color='rgba(255,255,255,0)', offset=1)],
            x1=1, x2=1, y1=1, y2=0
        ),
        opacity=0.2
    ).encode(y=alt.Y(y_col))

    points = base.mark_circle(color=Config.SCORE_COLORS['good']).encode(
        y=y_col, tooltip=['Data', y_col]
    )

    chart = (area + line + points).properties(
        height=250,
        background='rgba(0,0,0,0)'
    )
    
    st.altair_chart(_apply_chart_style(chart), width='stretch')
