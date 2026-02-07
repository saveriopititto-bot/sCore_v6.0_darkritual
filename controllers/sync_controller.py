import streamlit as st
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from config import Config
from engine.core import ScoreEngine, RunMetrics
from services.meteo_svc import WeatherService

# Initialize logger at module level
logger = logging.getLogger("sCore.Sync")

class SyncController:
    def __init__(self, auth_svc, db_svc):
        self.auth = auth_svc
        self.db = db_svc
        self.engine = ScoreEngine()

    def sync_activities(self, days_lookback: int) -> Dict[str, Any]:
        """
        Orchestra la sincronizzazione recuperando automaticamente i parametri necessari.
        """
        try:
             import streamlit as st
             if "strava_token" not in st.session_state:
                 return {"new": 0, "updated": 0, "skipped": 0, "error": "No Token"}
             
             token = st.session_state.strava_token["access_token"]
             ath = st.session_state.strava_token.get("athlete", {})
             athlete_id = ath.get("id")
             
             # Recupera parametri, priorità DB > Config
             profile = self.db.get_athlete_profile(athlete_id) or {}
             phys_params = {
                 "weight": profile.get("weight", Config.DEFAULT_WEIGHT),
                 "hr_max": profile.get("hr_max", Config.DEFAULT_HR_MAX),
                 "hr_rest": profile.get("hr_rest", Config.DEFAULT_HR_REST),
                 "age": profile.get("age", Config.DEFAULT_AGE),
                 "sex": profile.get("sex", "M"),
                 "ftp": profile.get("ftp", Config.DEFAULT_FTP)
             }
             
             # Recupera ID esistenti per skip
             existing_ids = self.db.get_run_ids_for_athlete(athlete_id)
             
             # --- 0. SYNC PROFILE (NEW) ---
             try:
                 strava_profile = self.auth.fetch_authenticated_athlete(token)
                 if strava_profile:
                     # Aggiorna il profilo nel DB con i dati freschi da Strava
                     payload = {
                         "id": athlete_id,
                         "firstname": strava_profile.get("firstname", ""),
                         "lastname": strava_profile.get("lastname", ""),
                         "weight": strava_profile.get("weight", Config.DEFAULT_WEIGHT),
                         "sex": strava_profile.get("sex", "M"),
                         "updated_at": datetime.now().isoformat()
                     }
                     
                     # Calcolo età da birthdate se disponibile
                     birthdate_str = strava_profile.get("birthdate")  # Format: YYYY-MM-DD
                     if birthdate_str:
                         try:
                             from datetime import datetime
                             birthdate = datetime.strptime(birthdate_str, "%Y-%m-%d")
                             today = datetime.now()
                             age = today.year - birthdate.year - ((today.month, today.day) < (birthdate.month, birthdate.day))
                             payload["age"] = age
                         except Exception as e:
                             print(f"Error calculating age from birthdate: {e}")
                     
                     # FTP da Strava (se disponibile)
                     strava_ftp = strava_profile.get("ftp")
                     if strava_ftp and strava_ftp > 0:
                         payload["ftp"] = strava_ftp
                         logger.info(f"FTP found in Strava profile: {strava_ftp}")
                     
                     # Manteniamo age, ftp, hr_max, hr_rest solo se NON sono in Strava
                     # (priorità a Strava, fallback a DB se già presenti)
                     existing = self.db.get_athlete_profile(athlete_id) or {}
                     
                     # HR Max e HR Rest non sono in Strava, usiamo DB o default
                     for key in ["hr_max", "hr_rest"]:
                         if key in existing:
                             payload[key] = existing[key]
                         else:
                             payload[key] = Config.DEFAULT_HR_MAX if key == "hr_max" else Config.DEFAULT_HR_REST
                     
                     # Se Strava non ha age o FTP, usa quelli del DB come fallback
                     if "age" not in payload and "age" in existing:
                         payload["age"] = existing["age"]
                     if "ftp" not in payload and "ftp" in existing:
                         payload["ftp"] = existing["ftp"]
                     
                     # --- FALLBACK FTP FROM ZONES ---
                     if not payload.get("ftp") or payload.get("ftp") == Config.DEFAULT_FTP:
                         try:
                             zones_data = self.auth.fetch_zones(token)
                             if zones_data and 'power' in zones_data:
                                 p_zones = zones_data['power'].get('zones', [])
                                 if len(p_zones) >= 4:
                                     # In Strava, Z4 max is usually FTP * 1.05
                                     z4_max = p_zones[3].get('max')
                                     if z4_max:
                                         inferred_ftp = int(z4_max / 1.05)
                                         payload["ftp"] = inferred_ftp
                                         logger.info(f"Inferred FTP from Strava zones: {inferred_ftp}")
                         except Exception as ze:
                             logger.warning(f"Failed to infer FTP from zones: {ze}")

                     self.db.save_athlete_profile(payload)
                     logger.info(f"Profile updated for athlete {athlete_id} from Strava")
                     
                     # Update local phys_params for the current sync run
                     for k, v in payload.items():
                         if k in phys_params: phys_params[k] = v
                         
             except Exception as e:
                 logger.error(f"Error syncing profile: {e}")

             # --- 0.1 SYNC ZONES ---
             try:
                 zones = self.auth.fetch_zones(token)
                 if zones:
                     self.db.update_athlete_zones(athlete_id, zones)
                     logger.info(f"Zones updated for athlete {athlete_id}")
             except Exception as e:
                 logger.error(f"Error syncing zones: {e}")

             # History Scores per gaming
             history = [r['SCORE'] for r in self.db.get_history(athlete_id) if 'SCORE' in r]
             
             # Esegui sync
             new_count, msg = self.run_sync(
                 token, athlete_id, phys_params, days_lookback, 
                 existing_ids, history
             )
             
             return {"new": new_count, "api_msg": msg}
             
        except Exception as e:
            print(f"Sync Error: {e}")
            return {"new": 0, "error": str(e)}

    def run_sync(self, token, athlete_id, physical_params, days_back, existing_ids, history_scores, progress_bar=None, last_import_timestamp=None):
        """
        Esegue la sync. Ritona (count_new, message).
        history_scores: lista di float degli score precedenti (per calcolo gaming)
        """
        weight = physical_params.get('weight', Config.DEFAULT_WEIGHT)
        # Default Params from config first
        hr_max = physical_params.get('hr_max', Config.DEFAULT_HR_MAX)
        hr_rest = physical_params.get('hr_rest', Config.DEFAULT_HR_REST)
        age = physical_params.get('age', Config.DEFAULT_AGE)
        sex = physical_params.get('sex', 'M')
        ftp = physical_params.get('ftp', Config.DEFAULT_FTP)
        
        # Override with DB Profile if available (Task: Recupera parametri da DB)
        profile = self.db.get_athlete_profile(athlete_id)
        if profile:
            if profile.get('hr_max'): hr_max = profile.get('hr_max')
            if profile.get('hr_rest'): hr_rest = profile.get('hr_rest')
            if profile.get('weight'): weight = profile.get('weight')
            if profile.get('ftp'): ftp = profile.get('ftp')
            if profile.get('sex'): sex = profile.get('sex')
            if profile.get('age'): age = profile.get('age')

        # --- 1. FETCH SEMPLIFICATO (SOLUZIONE DEFINITIVA) ---

        # --- 1. FETCH SEMPLIFICATO (SOLUZIONE DEFINITIVA) ---
        activities_list = self.auth.fetch_all_activities_simple(token)
        
        # Debug Temporaneo / Dev Console
        try:
             import streamlit as st
             st.session_state.last_activities = activities_list
             if activities_list:
                  st.session_state.last_strava_response = activities_list[:2]
             
             if progress_bar:
                 st.write(f"Strava activities fetched: {len(activities_list)}")
        except: pass
        
        if not activities_list:
             return -1, "Nessuna attività trovata"

        # FIX ORDER: Strava returns Newest-First. We need Oldest-First for Gaming History.
        activities_list.sort(key=lambda x: x['start_date_local'])

        count_new = 0
        total = len(activities_list)
        
        # Local copy of history
        current_history = list(history_scores)

        # FIX TYPE MISMATCH: Ensure all are strings
        existing_ids_str = set(str(eid) for eid in existing_ids)
        
        # Cutoff Date (Filtro post-fetch)
        # For initial sync (no existing runs), load everything. For updates, use cutoff.
        from datetime import timedelta
        is_initial_sync = len(existing_ids_str) == 0
        cutoff = None if is_initial_sync else datetime.now() - timedelta(days=days_back)
        
        if is_initial_sync:
            logger.info("🔄 Initial sync detected - loading ALL historical activities")
        else:
            logger.info(f"🔄 Update sync - checking activities from last {days_back} days")
        
        # --- SAFE SYNC LOGIC (DROP-IN) ---
        # --- SAFE SYNC LOGIC (DROP-IN) ---
        MAX_STREAMS = 50 # Increased cap for historical analysis
        RETRY = 3
        RETRY = 3
        stream_count = 0

        stream_count = 0

        for i, s in enumerate(activities_list):
            if progress_bar:
                progress_bar.progress((i + 1) / total)
            
            # --- 1. BASIC FILTERS ---
            # Solo Corsa (case-insensitive)
            activity_type = (s.get('type') or '').lower()
            if activity_type != 'run': 
                logger.info(f"Skipping activity {s.get('id')}: Not a Run (type={s.get('type')})")
                continue

            # Date Filter (skip only if cutoff is set)
            try:
                dt = datetime.strptime(s['start_date_local'], "%Y-%m-%dT%H:%M:%SZ")
                if cutoff is not None and dt < cutoff:
                    logger.info(f"Skipping activity {s.get('id')}: Before cutoff date")
                    continue
            except Exception as e:
                logger.warning(f"Skipping activity {s.get('id')}: Date parse error - {e}")
                continue

            # ID Check (deduplica)
            if str(s['id']) in existing_ids_str:
                logger.info(f"Skipping activity {s.get('id')}: Already exists in DB")
                continue
            
            # Verifica GPS (almeno distanza e tempo)
            if not s.get('distance') or s.get('distance', 0) < 100:  # min 100m
                logger.warning(f"Skipping activity {s.get('id')}: No GPS data (distance too low)")
                continue
            
            if not s.get('moving_time') or s.get('moving_time', 0) < 60:  # min 1 min
                logger.warning(f"Skipping activity {s.get('id')}: Too short (moving_time < 60s)")
                continue
            
            logger.info(f"Processing activity {s.get('id')} - {s.get('name', 'Untitled')}")
            
            # --- 2. FETCH STREAMS (con fallback) ---
            watts_stream = []
            hr_stream = []
            
            # Scarichiamo streams solo per le prime N attività (Anti-Ban)
            if stream_count < MAX_STREAMS:
                for r in range(RETRY):
                    try:
                         # Fetch streams con backoff
                         st_raw = self.auth.fetch_streams(token, s['id'])
                         if st_raw:
                             watts_stream = st_raw.get('watts', {}).get('data', [])
                             hr_stream = st_raw.get('heartrate', {}).get('data', [])
                             stream_count += 1
                             logger.info(f"Streams fetched for {s['id']}: {len(watts_stream)} watts, {len(hr_stream)} HR")
                             break
                    except Exception as e:
                         logger.warning(f"Stream fetch attempt {r+1} failed for {s['id']}: {e}")
                         time.sleep(2 ** (r + 1))
            else:
                logger.info(f"Stream limit reached ({MAX_STREAMS}), using summary data only for {s['id']}")
            
            # Fallback: se mancano streams, usa i dati summary di Strava
            avg_power = s.get('average_watts', 0) or 0
            avg_hr = s.get('average_heartrate', 0) or 0
            
            # Se NON ci sono dati summary e nemmeno streams, skippa
            if avg_power == 0 and avg_hr == 0 and not watts_stream and not hr_stream:
                logger.warning(f"Skipping {s['id']}: No power or HR data (summary or streams)")
                continue
            
            # --- 3. BUILD RUN OBJECT (ROBUST) ---
            # Meteo (Optional)
            t, h, is_real = 20.0, 50.0, False 
            
            # Safely extract LatLng
            latlng = s.get('start_latlng')
            if latlng and isinstance(latlng, list) and len(latlng) == 2:
                 try:
                    # Date YYYY-MM-DD logic
                    date_iso = dt.strftime("%Y-%m-%d")
                    t, h, is_real = WeatherService.get_weather(latlng[0], latlng[1], date_iso, dt.hour)
                    logger.info(f"Weather for {s['id']}: {t}°C, {h}% (real={is_real})")
                 except Exception as e: 
                    logger.warning(f"Weather fetch failed for {s['id']}: {e}")
                    pass

            # Create MeteoData object
            from engine.metrics import MeteoData
            meteo_data = MeteoData(temperature=t, humidity=h, is_real=is_real)

            m = RunMetrics(
                avg_power,
                avg_hr,
                s.get('distance', 0),
                s.get('moving_time', 0),
                s.get('total_elevation_gain', 0),
                weight, hr_max, hr_rest,
                meteo_data,  # Pass MeteoData object instead of t, h
                age, sex
            )

            # Drift & Score
            dec = self.engine.calculate_decoupling(watts_stream, hr_stream)
            m.decoupling = dec
            
            # --- v6 IMPLEMENTATION & BASELINE UPDATE ---
            # 1. Calcolo T_adj (Logic v5 per baseline)
            current_t_adj = self.engine.calculate_t_adj(m)
            dist_label = m.dist_label
            
            # 2. Aggiornamento Baseline (Se improvement)
            self.db.update_athlete_baseline(athlete_id, dist_label, current_t_adj)
            
            # 3. Calcolo Score v6 Darkritual (Competitive Efficiency Index)
            # Nominal Power (W/kg) = FTP / Weight. Fallback to 3.0 W/kg if weight is missing
            nominal_pwr_kg = (ftp / weight) if weight > 0 else 3.0
            
            # Target HR Eff. Assuming default 1.0 (Parity)
            # Recupero Baseline PRIMA dello score per passarlo alla funzione (Richiesta User)
            db_baseline_pre = self.db.get_athlete_baseline(athlete_id, dist_label)
            
            # DARKRITUAL: Competitive score with WR comparison
            score, details = self.engine.compute_score_v6_darkritual_wrapper(
                m, 
                nominal_power=nominal_pwr_kg, 
                target_hr_eff=1.0,
                athlete_level="intermediate",  # TODO: make dynamic from DB profile
                db_baseline_adj=db_baseline_pre
            )
            
            # UI Helpers & Gaming
            rnk, _ = self.engine.get_rank(score)
            quality = self.engine.run_quality(score)
            
            # Update History
            current_history.append(score)
            gaming = self.engine.gaming_feedback(current_history)

            # Reconstruct details for UI
            db_baseline = self.db.get_athlete_baseline(athlete_id, dist_label)
            
            run_obj = {
                "id": s['id'],
                "name": s.get('name', 'Untitled Run'),  # NEW: activity name from Strava
                "Data": dt.strftime("%Y-%m-%d"),
                "Dist (km)": round(m.distance_meters / 1000, 2),
                "Power": int(m.avg_power),
                "HR": int(m.avg_hr),
                "Decoupling": round(dec * 100, 1),
                "SCORE": round(score, 2),
                "WCF": round(details['wcf'], 2), 
                "WR_Pct": 0.0, # Deprecated in v5
                "Rank": rnk,
                "Quality": quality,
                "Meteo": f"{t}°C", 
                "SCORE_DETAIL": {
                    "W/kg": round(m.w_kg, 2),
                    "Nominal": round(details['nominal_pwr'], 2),
                    "Mech Eff": round(details['mech_eff'], 2),
                    "Metabolic Eff": round(details['metabolic_eff'], 2),
                    "WCF": round(details['wcf'], 2),
                    "Stability": round(details['stability'], 2),
                    "Target T_adj": round(db_baseline, 1) if db_baseline else "N/A"
                },
                "Device": s.get("device_name", "Unknown"),
                "raw_watts": watts_stream,
                "raw_hr": hr_stream,
                "Achievements": gaming["achievements"],
                "Trend": gaming["trend"],
                "Comparison": gaming["comparison"],
                "is_weather_real": is_real
            }

            if self.db.save_run(run_obj, athlete_id):
                count_new += 1
                logger.info(f"✅ Saved run {s['id']}: SCORE={score:.1f}, Rank={rnk}")
            else:
                logger.error(f"❌ Failed to save run {s['id']}")
            
            # Simpler rate limit sleep
            time.sleep(0.5)

        if count_new > 0:
            self.db.update_streak(athlete_id)
            
            # Update session state with fresh data after sync
            try:
                import streamlit as st
                # Refresh the data in session state immediately
                fresh_data = self.db.get_history(athlete_id)
                st.session_state.data = fresh_data
            except:
                pass
        
        return count_new, f"Sync terminata: {count_new} nuove attività (Streams utilizzati: {stream_count})"
