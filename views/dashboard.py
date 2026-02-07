import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
from config import Config
from engine.core import ScoreEngine, RunMetrics
from engine.dashboard_logic import DashboardLogic
from ui.visuals import (
    render_history_table, render_trend_chart, render_scatter_chart, 
    render_zones_chart, render_quality_badge, render_trend_card, 
    get_coach_feedback, quality_circle, trend_circle, 
    consistency_circle, efficiency_circle, 
    zones_circle
)
from ui.feedback import render_feedback_form

# Components
from components.header import render_header
from components.athlete import render_top_section
from components.kpi import render_kpi_grid

def render_dashboard(auth_svc, db_svc):
    # 1. HEADER
    render_header()

    # 2. TOP SECTION (Profile & Controls)
    phys_params, start_sync, days_to_fetch = render_top_section(auth_svc, db_svc)
    ftp = phys_params.get('ftp', Config.DEFAULT_FTP)
    
    # context
    ath = st.session_state.strava_token.get("athlete", {})
    athlete_name = f"{ath.get('firstname', 'Atleta')} {ath.get('lastname', '')}"
    athlete_id = ath.get("id")

    # --- 1. AUTO-AGGIORNAMENTO ALL'AVVIO (3 MESI) ---
    # FIX: Controlla anche se il DB è effettivamente vuoto, non solo il flag di sessione
    # Questo previene problemi di cache quando il DB viene svuotato
    import logging
    logger = logging.getLogger("sCore")
    
    should_sync = (
        "initial_sync_done" not in st.session_state or
        (not st.session_state.data)  # Force sync if data is empty even if flag is set
    )
    
    logger.info(f"🔍 Sync check: should_sync={should_sync}, data_count={len(st.session_state.data)}, demo={st.session_state.get('demo_mode')}")
    
    if should_sync and not st.session_state.get("demo_mode", False):
        logger.info("🚀 Triggering initial sync...")
        try:
            with st.spinner("⏳ Sincronizzazione ultimi 3 mesi in corso..."):
                logger.info("📥 Spinner shown, importing SyncController...")
                # Inizializziamo il controller
                from controllers.sync_controller import SyncController
                sync_service = SyncController(auth_svc, db_svc)
                
                logger.info(f"🔄 Starting sync for athlete {athlete_id}...")
                # Default 90 giorni (3 mesi)
                result = sync_service.sync_activities(days_lookback=90)
                logger.info(f"✅ Sync completed: {result}")
                
                # Segniamo che l'abbiamo fatto, così non lo rifà ad ogni click
                st.session_state.initial_sync_done = True
                st.session_state.filter_start_date = datetime.now().date() - timedelta(days=90)
                
                # Refresh dati
                st.session_state.data = db_svc.get_history(athlete_id)
                logger.info(f"📊 Data refreshed: {len(st.session_state.data)} runs")
                
                # Rerunning to apply newly synced profile params (FTP, Weight, etc.) to the UI
                st.rerun()
        except Exception as e:
            logger.error(f"❌ Sync failed: {e}", exc_info=True) 

    # --- Recupero dati dal DB filtrati per data ---
    # Usiamo la data salvata nello stato (o default 120gg)
    start_date = st.session_state.get("filter_start_date", datetime.now().date() - timedelta(days=90))
    
    # Filter functionality handled by passing start_date to DB or filtering DF
    # The existing code uses st.session_state.data which is all history.
    # We will filter the DF below.

    # --- VISUALIZZAZIONE DASHBOARD ---
    # Refresh data from DB to catch any recent syncs
    if not st.session_state.get("demo_mode", False):
        fresh_data = db_svc.get_history(athlete_id)
        if fresh_data:
            st.session_state.data = fresh_data
    
    if st.session_state.data:
        df = pd.DataFrame(st.session_state.data)
        df['Data'] = pd.to_datetime(df['Data'], errors='coerce')
        if pd.api.types.is_datetime64_any_dtype(df['Data']) and df['Data'].dt.tz is not None:
             df['Data'] = df['Data'].dt.tz_localize(None)

        # Initialize Logic
        logic = DashboardLogic(ScoreEngine())
        df = logic.prepare_trend_data(df)
        
        # Filtro Temporale Dinamico
        if 'start_date' in locals():
            # Convert start_date to datetime for comparison
            cutoff = pd.to_datetime(start_date)
            # Ensure timezone awareness matches (remove tz from df if needed, done above)
            df = df[df['Data'] >= cutoff]
        
        if df.empty:
            st.warning("Nessuna corsa nel periodo selezionato.")
        else:
            cur_run = df.iloc[0]
            delta_val = logic.calculate_delta(df)
            
            score_color = "#FFCF96" # Statico
            if delta_val > 0.005: score_color = "#CDFAD5" 
            elif delta_val < -0.005: score_color = "#FF8080" 

            # eng already initialized in logic
            
            
            # --- MIDDLE SECTION: METRICHE PRINCIPALI (KPI)
            render_kpi_grid(cur_run, score_color)
        
            if st.session_state.get("dev_mode"):
                with st.expander("⚙️ Score Process Logs (Debug Formula)", expanded=False):
                    st.write("**Dati Corsa (Input)**")
                    st.json({
                        "Date": str(cur_run['Data']),
                        "Distance": cur_run['Dist (km)'],
                        "Power (Avg)": cur_run['Power'],
                        "HR (Avg)": cur_run['HR'],
                        "Drift (Decoupling)": cur_run['Decoupling'],
                        "Weight": phys_params.get('weight'),
                        "Age": phys_params.get('age')
                    })
                    st.write("**Dettagli Calcolo Score**")
                    st.json(cur_run.get('SCORE_DETAIL', {}))
                    st.write("**Raw Row Data**")
                    st.json(cur_run.to_dict())
            
        
            # --- GAMING FEEDBACK LAYER (Fix: Mapping Colonne Corretto) ---
            
            # 1. Recupera Score Numerico
            current_score = cur_run.get('SCORE', 0)
            
            # 2. CALCOLO QUALITÀ (Strategia Ibrida)
            quality_data = logic.get_run_quality(current_score)

            # 3. Recupera Trend dal DB
            trend_data = cur_run.get("Trend", {})
            
            # 4. CALCOLO CONSISTENZA
            consistency_data = logic.prepare_consistency_score(df)
            
            # 6. Efficiency Factor (Watt / Cuore)
            ef_data = logic.get_efficiency_factor(cur_run)

            # 7. Distribuzione Zone (per il Cerchio)
            # Calcoliamo le zone potenza (o cardio se mancano i watt) per il cerchio riassuntivo
            zones_pwr = logic.get_zones(cur_run, ftp)
            
            # 8. Generazione HTML e Rendering
            html_quality = quality_circle(quality_data)
            html_trend = trend_circle(trend_data)
            html_consistency = consistency_circle(consistency_data)
            html_efficiency = efficiency_circle(ef_data)
            html_zones = zones_circle(zones_pwr)

            st.markdown("""
            <style>
                .metric-row { display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; margin-top: -10px; margin-bottom: 20px; }
                .metric-row > div { transform: scale(0.95); }
            </style>
            """, unsafe_allow_html=True)

            st.markdown(f"""
            <div class="metric-row">
                <div>{html_quality}</div>
                <div>{html_trend}</div>
                <div>{html_consistency}</div>
                <div>{html_efficiency}</div>
                <div>{html_zones}</div>
            </div>
            """, unsafe_allow_html=True)
            
        
            
            # --- SEZIONE DETTAGLI UNIFICATA (Responsive Horizontal Row) ---
            st.markdown('<div class="details-row">', unsafe_allow_html=True)
            c_achieve, c_arch, c_bug, c_leg = st.columns(4, gap="small")
                        
            with c_achieve:
                with st.popover("🏆 Awards", width='stretch'):
                    achieve_list = cur_run.get('Achievements', [])
                    if achieve_list:
                        for a in achieve_list:
                            st.markdown(f"**{a}**")
                    else:
                        st.caption("Nessuno oggi.")

            with c_arch:
                with st.popover("📂 Archivio", width='stretch'):
                    render_history_table(df)

            with c_bug:
                with st.popover("🛠️ Bug/Idea", width='stretch'):
                    render_feedback_form(db_svc, ath.get("id"), athlete_name)
                    st.divider()
                    if st.button("Reset DB", type="primary", width='stretch'):
                        if db_svc.reset_history(ath.get("id")):
                            st.session_state.data = []
                            # FORCE RE-SYNC DEFAULT ANALYSIS
                            if "initial_sync_done" in st.session_state:
                                del st.session_state["initial_sync_done"]
                            if "filter_start_date" in st.session_state:
                                del st.session_state["filter_start_date"]
                                
                            st.success("Resettato! Ricarico l'analisi di default...")
                            time.sleep(1)
                            st.rerun()

            with c_leg:
                with st.popover("📖 Legenda", width='stretch'):
                    st.markdown(f"""
                    **Efficienza:**
                    - <span style="color:{Config.Theme.SECONDARY}">●</span> <3% Top
                    - <span style="color:{Config.Theme.ACCENT}">●</span> 3-5% Ok
                    - <span style="color:{Config.Theme.DANGER}">●</span> >5% No

                    **Efficiency Factor (EF):**
                    - <span style="color:{Config.Theme.SCORE_WASTED}">●</span> <1.1 Low
                    - <span style="color:{Config.Theme.SCORE_EPIC}">●</span> 1.1-1.3 Good
                    - <span style="color:{Config.Theme.SCORE_GREAT}">●</span> >1.5 Elite
                    """, unsafe_allow_html=True)
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            render_legal_section()
    else:
        # Empty state: nessuna attività sincronizzata
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.info("🏃 **Nessuna attività trovata**")
        st.markdown("""
        Possibili motivi:
        1. **Primo accesso:** Il sync iniziale potrebbe richiedere alcuni secondi
        2. **Nessuna attività su Strava:** Aggiungi delle corse con dati GPS, potenza e cardio
        3. **Errore di sincronizzazione:** Prova a ricaricare la pagina
        
        Se il problema persiste, usa il popover "🛠️ Bug/Idea" per segnalare il problema.
        """)
        st.markdown("<br>", unsafe_allow_html=True)
        render_legal_section()