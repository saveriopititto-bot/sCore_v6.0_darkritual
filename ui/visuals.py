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

# --- 2. NEON RENDERING COMPONENTS (v4.1) ---

def render_neon_score(score):
    try: val = float(score)
    except: val = 0.0
    
    color = get_score_color(val)
    # Determine gradient/border color class or inline style
    # For simplicity, we use the color directly in style
    
    return f"""
    <div class="relative w-40 h-40 md:w-48 md:h-48 flex items-center justify-center transform hover:scale-105 transition-transform duration-500 z-20 mx-[-10px]">
        <div class="absolute inset-0 rounded-full bg-gradient-to-br from-green-100 to-transparent dark:from-green-900/20 opacity-50 blur-xl"></div>
        <div class="absolute inset-0 rounded-full border-[6px] border-green-50 dark:border-green-900/30"></div>
        <div class="absolute inset-0 rounded-full border-[6px]" style="border-color: {color}; border-left-color: transparent; border-bottom-color: transparent; transform: rotate(-45deg); filter: drop-shadow(0 4px 6px rgba(0,0,0,0.1));"></div>
        <div class="text-center z-10 bg-white dark:bg-surface-dark rounded-full w-32 h-32 flex flex-col items-center justify-center shadow-2xl border border-gray-100 dark:border-gray-700">
            <span class="text-[0.55rem] font-bold text-gray-400 uppercase tracking-[0.15em] mb-0.5 leading-none">Score</span>
            <span class="text-4xl md:text-5xl font-black tracking-tighter leading-none" style="color: {color};">{val:.1f}</span>
        </div>
    </div>
    """

def render_neon_drift(drift):
    try: val = float(drift)
    except: val = 0.0
    
    color = get_drift_color(val)
    
    return f"""
    <div class="relative w-24 h-24 md:w-28 md:h-28 flex items-center justify-center transform hover:scale-105 transition-transform duration-500">
        <div class="absolute inset-0 rounded-full border-[3px] border-yellow-100 dark:border-yellow-900/30"></div>
        <div class="absolute inset-0 rounded-full border-[3px] border-transparent" style="border-top-color: {color}; transform: rotate(-90deg);"></div>
        <div class="text-center z-10 bg-white/80 dark:bg-surface-dark/80 backdrop-blur-sm rounded-full w-20 h-20 flex flex-col items-center justify-center shadow-soft ring-1 ring-gray-100 dark:ring-gray-700">
            <span class="text-[0.45rem] font-bold text-gray-400 uppercase tracking-wider mb-0 leading-none">Drift</span>
            <span class="text-lg md:text-xl font-extrabold leading-tight" style="color: {color};">{val:.1f}%</span>
        </div>
        <div class="absolute inset-0 rounded-full shadow-glow-yellow opacity-20 animate-pulse"></div>
    </div>
    """

def render_neon_percentile(pct):
    try: val = float(pct)
    except: val = 0.0
    
    color = get_percentile_color(val)
    
    return f"""
    <div class="relative w-24 h-24 md:w-28 md:h-28 flex items-center justify-center transform hover:scale-105 transition-transform duration-500">
        <div class="absolute inset-0 rounded-full border-[3px] border-red-100 dark:border-red-900/30"></div>
        <div class="absolute inset-0 rounded-full border-[3px] border-transparent" style="border-top-color: {color}; transform: rotate(45deg);"></div>
        <div class="text-center z-10 bg-white/80 dark:bg-surface-dark/80 backdrop-blur-sm rounded-full w-20 h-20 flex flex-col items-center justify-center shadow-soft ring-1 ring-gray-100 dark:ring-gray-700">
            <span class="text-[0.45rem] font-bold text-gray-400 uppercase tracking-wider mb-0 leading-none">Percentile</span>
            <span class="text-lg md:text-xl font-extrabold leading-tight" style="color: {color};">{val:.1f}%</span>
        </div>
        <div class="absolute inset-0 rounded-full shadow-glow-red opacity-20 animate-pulse"></div>
    </div>
    """

def render_neon_badge(label, value, icon=None, color_hex=None, sub_label=None, ring_class=None):
    """
    Renders small Grid items (Quality, Trend, Constcy, EF, Z5).
    """
    if not color_hex: color_hex = "#888"
    
    # Ring Logic
    ring_html = ""
    if ring_class:
        ring_html = f'<div class="absolute inset-0 rounded-full {ring_class} p-[1.5px] shadow-sm group-hover:shadow-glow-red transition-shadow"></div>'
        bg_class = "absolute inset-[1.5px] z-10" # Inner container needs to fit inside ring
    else:
        # Standard Border
        ring_html = f'<div class="absolute inset-0 rounded-full border-[2px]" style="border-color: {color_hex};" class="shadow-sm group-hover:shadow-glow-green transition-shadow"></div>'
        bg_class = "flex flex-col items-center justify-center w-12 h-12 shadow-soft"

    # Content Logic
    content = ""
    if icon:
        if len(icon) == 1: # Unicode char
             content = f'<span class="text-sm leading-tight" style="color: {color_hex}">{icon}</span>'
        else: # Material Icon
             content = f'<span class="material-icons-round text-base leading-none" style="color: {color_hex}">{icon}</span>'
    else:
        content = f'<span class="text-sm font-bold leading-tight" style="color: {color_hex}">{value}</span>'
        
    return f"""
    <div class="relative w-16 h-16 flex items-center justify-center group cursor-pointer transition-all hover:-translate-y-1">
        {ring_html}
        <div class="{bg_class} bg-white dark:bg-surface-dark rounded-full flex flex-col items-center justify-center">
            <span class="text-[0.4rem] font-bold text-gray-400 uppercase mb-0 leading-none">{label}</span>
            {content}
        </div>
    </div>
    """

# --- 3. PUBLIC API (CONSUMERS) ---

# Re-mapped to Neon Renderers

def render_kpi_score(score):
    return render_neon_score(score)

def render_kpi_drift(val):
    return render_neon_drift(val)

def render_kpi_percentile(val):
    return render_neon_percentile(val)

def quality_circle(q):
    if not isinstance(q, dict): return render_neon_badge("Quality", "N/A", icon="?", color_hex="#888")
    label = q.get("label", "N/A").split()[0] # e.g. "Solid"
    color = q.get("color", "#888")
    # Icon mapping
    icon = "🏆"
    if "Weak" in label: icon = "🐌"
    elif "Solid" in label: icon = "⚡"
    elif "Great" in label: icon = "💎"
    
    return render_neon_badge("Quality", label, icon=icon, color_hex=color)

def trend_circle(tr):
    direction = tr.get("direction", "flat")
    if direction == "up": icon, color = "arrow_drop_up", Config.Theme.SECONDARY
    elif direction == "down": icon, color = "arrow_drop_down", Config.Theme.DANGER
    else: icon, color = "remove", Config.Theme.ACCENT
    return render_neon_badge("Trend", "", icon=icon, color_hex=color)

def consistency_circle(cons_data):
    # Just render scalar badge
    score = cons_data.get("score", 0) if cons_data else 0
    color = Config.Theme.DANGER
    if score >= 80: color = Config.Theme.SECONDARY
    elif score >= 60: color = Config.Theme.PRIMARY
    elif score >= 40: color = Config.Theme.ACCENT
    return render_neon_badge("Constcy", str(int(score)), color_hex=color)

def efficiency_circle(ef_data):
    ef = ef_data.get("ef", 0) if ef_data else 0
    return render_neon_badge("EF", f"{ef:.2f}", color_hex="#5C5CFF")

def zones_circle_badge(zone_label, pct):
    """Small badge for max zone (e.g. Z5)"""
    return render_neon_badge(zone_label, "", icon="", color_hex="#FB4141", ring_class="ring-gradient-orange-red")

# Stub for compatibility if anything calls generic render_stat_card (deprecated)
def render_stat_card(*args, **kwargs):
    return render_neon_badge("Legacy", "N/A", color_hex="#888")

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
