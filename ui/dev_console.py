import streamlit as st
import pandas as pd

def render_dev_console():
    st.title("🛠 Developer Console")
    st.caption("Internal diagnostics — SCORE Lab")

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📥 Import",
        "🧮 Formula",
        "❤️ Drift",
        "🚦 Rate Limit",
        "🌦 Weather & Baseline Audit",
        "☁️ Analisi Meteo Strava",
        "🔧 Debug Temporaneo"
    ])

    # Instantiate DB Service locally since app.py might not have passed it
    from config import Config
    from services.db import DatabaseService
    try:
        supa_creds = Config.get_supabase_creds()
        db = DatabaseService(supa_creds["url"], supa_creds["key"])
    except:
        db = None


    with tab1:
        st.subheader("Strava Import Debug")
        st.json(st.session_state.get("last_strava_response", {}))
        st.write(f"Activities fetched: {len(st.session_state.get('last_activities', []))}")

    with tab2:
        st.subheader("SCORE Breakdown")
        st.json(st.session_state.get("last_score_math", {}))

    with tab3:
        st.subheader("Drift Debug")
        st.json(st.session_state.get("last_drift_debug", {}))

    with tab4:
        st.subheader("Rate Limit")
        st.json(st.session_state.get("rate_limit_headers", {}))

    with tab5:
        st.subheader("🌦 Forecast & Weather Audit")
        
        # Access global runs from session state
        df = st.session_state.get("runs_df")
        
        if df is not None and not df.empty:
            total = len(df)
            
            # Count how many have valid 'Meteo' string
            # We assume empty string "" means missing
            if "Meteo" in df.columns:
                labeled_count = df["Meteo"].apply(lambda x: 1 if x and len(str(x)) > 0 else 0).sum()
            else:
                labeled_count = 0
            
            c1, c2 = st.columns(2)
            c1.metric("Total Runs in Session", total)
            c2.metric("Runs with Weather Data", f"{labeled_count}/{total}", 
                      delta="Coverage" if labeled_count == total else f"{labeled_count - total}")

            # Preview Table
            cols_to_show = ["Data", "Dist (km)", "Meteo", "WCF"]
            # Ensure columns exist properly
            preview_df = df[ [c for c in cols_to_show if c in df.columns] ].copy()
            
            # Sort by Date desc
            if "Data" in preview_df.columns:
                preview_df.sort_values(by="Data", ascending=False, inplace=True)

            st.dataframe(
                preview_df,
                width='stretch',
                hide_index=True,
                column_config={
                     "Data": st.column_config.TextColumn("Data"),
                     "Dist (km)": st.column_config.NumberColumn("Dist (km)", format="%.2f"),
                     "Meteo": st.column_config.TextColumn("Meteo (Real/Fallback)"),
                     "WCF": st.column_config.NumberColumn("WCF", format="%.2f")
                }
            )
            
        else:
            st.info("No runs loaded in session state (runs_df is empty).")

    with tab6:
        st.subheader("🔍 OpenMeteo Debugger")
        debug = st.session_state.get("last_weather_debug", {})
        
        if not debug:
            st.info("Nessuna chiamata meteo registrata in questa sessione. (Lancia 'Reset DB' per forzare una chiamata)")
        else:
            c1, c2 = st.columns(2)
            c1.metric("Archive Status", debug.get("archive_status", "N/A"))
            c2.metric("Forecast Status", debug.get("forecast_status", "N/A"))
            
            st.markdown("#### 📡 Request Params")
            st.json(debug.get("request_params"))
            
            st.markdown("#### 🛑 Error Logs (Last Request)")
            if debug.get("archive_status") != 200:
                st.error(f"Archive API Error: {debug.get('archive_response')}")
            else:
                st.success("Archive API: OK")
                
            if debug.get("forecast_attempted"):
                if debug.get("forecast_status") != 200:
                    st.error(f"Forecast API Error: {debug.get('forecast_response')}")
                else:
                    st.success("Forecast API: OK")
            else:
                st.info("Forecast API not attempted (Archive was successful).")

    with tab7:
        st.subheader("Debug Temporaneo")
        from engine.core import ScoreEngine
        eng = ScoreEngine()
        
        if st.checkbox("Mostra Debug Engine", value=False):
             st.write(f"Has gaming_feedback: {hasattr(eng, 'gaming_feedback')}")
             st.write(f"Has compute_score_v6_darkritual_wrapper: {hasattr(eng, 'compute_score_v6_darkritual_wrapper')}")



    if st.button("⬅️ Torna alla app"):
        st.session_state.dev_mode = False
        st.rerun()
