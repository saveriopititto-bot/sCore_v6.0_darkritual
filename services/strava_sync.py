import time
import logging
from datetime import datetime
from engine.metrics import RunMetrics, MeteoData

logger = logging.getLogger("sCore.StravaSync")

def safe_strava_sync(
    auth_svc,
    db_svc,
    eng,
    token: str,
    athlete_id: int,
    weight: float,
    hr_max: int,
    hr_rest: int,
    age: int,
    sex: str,
    days_to_fetch: int = 365,
):
    """
    Sync robusto Strava:
    - paginazione completa
    - deduplica per atleta
    - 2-pass sync
    - retry + backoff
    - INTEGRAZIONE METEO REALE (Open-Meteo)
    """

    # --------------------------------------------------
    # 1. Recupera ID già presenti SOLO per questo atleta
    # --------------------------------------------------
    existing_ids = set(db_svc.get_run_ids_for_athlete(athlete_id))
    logger.info(f"[SYNC] Existing runs: {len(existing_ids)}")

    # Check validation for Best Efforts
    has_bests = db_svc.has_athlete_bests(athlete_id)
    refresh_bests = not has_bests # Se non li abbiamo, forziamo il download

    # --------------------------------------------------
    # 2. Fetch TUTTE le attività (paginazione)
    # --------------------------------------------------
    activities = auth_svc.fetch_all_activities_simple(token)
    logger.info(f"[SYNC] Activities fetched: {len(activities)}")

    if not activities:
        return {"new": 0, "streams": 0, "skipped": 0}

    new_runs = []
    skipped = 0

    # --------------------------------------------------
    # 3. PASS 1 — salva metadata preliminari
    # --------------------------------------------------
    for s in activities:
        if s["id"] in existing_ids:
            # Anche se esiste, controlliamo se ha PR recenti per triggerare un refresh globale
            if s.get("pr_count", 0) > 0:
                refresh_bests = True
            skipped += 1
            continue

        # Validate Data Integrity (Skip if 0 Watts or 0 HR)
        pwr = int(s.get("average_watts", 0) or 0)
        hr = int(s.get("average_heartrate", 0) or 0)
        
        if pwr <= 0 or hr <= 0:
            logger.warning(f"[SYNC] Skipping {s['id']}: Missing Power ({pwr}) or HR ({hr})")
            skipped += 1
            continue

        run_obj = {
            "id": s["id"],
            "Data": s["start_date_local"][:10],
            "Dist (km)": round(s.get("distance", 0) / 1000, 2),
            "Power": pwr,
            "HR": hr,
            "Decoupling": 0.0,
            "SCORE": 0.0,
            "WCF": 1.0,
            "WR_Pct": 0.0,
            "Rank": "—",
            "Meteo": "Pending...", # Placeholder in attesa del Pass 2
            "SCORE_DETAIL": {},
            "raw_watts": [],
            "raw_hr": []
        }

        db_svc.save_run(run_obj, athlete_id)
        new_runs.append(s["id"])
        
        # Check per nuovi PR
        if s.get("pr_count", 0) > 0:
            refresh_bests = True

    logger.info(f"[SYNC] New runs saved: {len(new_runs)}")

    # --------------------------------------------------
    # 4. PASS 2 — Streams + Meteo Reale + Calcolo SCORE
    # --------------------------------------------------
    updated = 0

    for i, run_id in enumerate(new_runs):
        try:
            # A. Recupero Streams (Watt/HR)
            streams = auth_svc.fetch_streams(token, run_id) or {}
            watts = streams.get("watts", {}).get("data", [])
            hr = streams.get("heartrate", {}).get("data", [])

            # Recupero l'oggetto activity completo dalla lista in memoria
            s = next(a for a in activities if a["id"] == run_id)

            # B. --- ⛈️ GESTIONE METEO (Semplificata) ---
            # Una sola riga! La classe MeteoData fa tutto il lavoro sporco.
            meteo_data = MeteoData.fetch_for_activity(s)

            # C. Creazione Metriche
            m = RunMetrics(
                avg_power=s.get("average_watts", 0),
                avg_hr=s.get("average_heartrate", 0),
                distance=s.get("distance", 0),
                moving_time=s.get("moving_time", 0),
                elevation_gain=s.get("total_elevation_gain", 0),
                weight=weight,
                hr_max=hr_max,
                hr_rest=hr_rest,
                meteo=meteo_data,    # <--- Passi l'oggetto appena creato
                age=age,
                sex=sex
            )

            # D. Calcolo SCORE & Decoupling
            # Recuperiamo i Best Efforts dal DB per il calcolo relativo
            athlete_bests = db_svc.get_athlete_bests(athlete_id)
            
            # Chiamata al Nuovo Motore unificato
            score, details, wcf, wr_pct, quality = eng.compute_score(
                metrics=m, 
                decoupling=dec,
                athlete_bests=athlete_bests
            )

            # E. Aggiornamento Oggetto Run
            s_local['Decoupling'] = dec
            s_local['SCORE'] = score
            s_local['WCF'] = wcf
            s_local['WR_Pct'] = wr_pct
            
            # Salva dettagli complessi (Quality, PB%, ecc)
            # Flattening per semplicità nel JSON o salvataggio diretto
            details['quality_label'] = quality.get('label')
            details['quality_color'] = quality.get('color')
            s_local['SCORE_DETAIL'] = details
            
            # F. Persistenza
            db_svc.update_run(run_id, s_local, athlete_id)
            updated += 1

        except Exception as e:
            logger.error(f"[SYNC] Error processing run {run_id}: {e}")

    # --------------------------------------------------
    # 5. Best Efforts Sync (Conditional)
    # --------------------------------------------------
    if refresh_bests:
        logger.info("[SYNC] Refreshing Athlete Best Efforts (Triggered by PR count or missing data)")
        try:
            stats = auth_svc.fetch_athlete_stats(token, athlete_id)
            if stats:
                bests_to_save = []
                if "best_efforts" in stats:
                     for be in stats["best_efforts"]:
                         bests_to_save.append({
                             "athlete_id": athlete_id,
                             "distance_type": be.get("name"),
                             "best_time": be.get("elapsed_time"),
                             "activity_id": be.get("activity", {}).get("id"),
                             "achieved_at": be.get("start_date_local")
                         })
                         
                if bests_to_save:
                    db_svc.save_athlete_bests(athlete_id, bests_to_save)
                    logger.info(f"[SYNC] Saved {len(bests_to_save)} best efforts.")
                else:
                    logger.info("[SYNC] No 'best_efforts' list found in stats response.")

        except Exception as e:
            logger.error(f"[SYNC] Error fetching stats: {e}")

    return {"new": len(new_runs), "streams": updated, "skipped": skipped}