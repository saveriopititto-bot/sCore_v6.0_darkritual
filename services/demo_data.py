import random
from datetime import datetime, timedelta
from config import Config
from engine.core import ScoreEngine
from engine.metrics import RunMetrics

def generate_demo_data():
    """
    Genera dati demo realistici per mostrare la dashboard senza account Strava.
    Include 30 corse negli ultimi 90 giorni con metriche variabili.
    USA ALGORITMO REALE ScoreEngine v6 per calcolare i punteggi.
    """
    demo_runs = []
    engine = ScoreEngine()
    
    # Parametri atleta demo
    weight = 70.0
    hr_max = 185
    hr_rest = 50
    age = 30
    sex = "M"
    ftp = 250  # Demo FTP
    
    # Genera 30 corse negli ultimi 90 giorni
    for i in range(30):
        days_ago = 90 - (i * 3)  # Una corsa ogni 3 giorni
        date = datetime.now() - timedelta(days=days_ago)
        
        # Variazione naturale delle metriche
        distance_km = round(random.uniform(5.0, 21.0), 2)
        distance_m = distance_km * 1000
        
        # Power e HR con variazione realistica
        avg_power = int(random.uniform(200, 280))
        avg_hr = int(random.uniform(145, 172))
        
        # Meteo simulato
        temp = random.randint(15, 28)
        humidity = random.randint(40, 70)
        
        # Durata realistica (4:30 - 6:00 min/km)
        pace_sec_per_km = random.uniform(270, 360)
        duration_sec = int(distance_km * pace_sec_per_km)
        
        # Genera stream dati realistici
        raw_watts = [int(avg_power + random.uniform(-35, 35)) for _ in range(duration_sec)]
        raw_hr = [int(avg_hr + random.uniform(-12, 12)) for _ in range(duration_sec)]
        
        # Calcola decoupling reale
        decoupling = engine.calculate_decoupling(raw_watts, raw_hr)
        
        # Crea oggetto Meteo
        from engine.metrics import MeteoData
        meteo_data = MeteoData(temperature=temp, humidity=humidity)
        
        # Crea RunMetrics con dati realistici
        metrics = RunMetrics(
            avg_power=avg_power,
            avg_hr=avg_hr,
            distance=distance_m,
            moving_time=duration_sec,
            elevation_gain=int(random.uniform(50, 200)),
            weight=weight,
            hr_max=hr_max,
            hr_rest=hr_rest,
            meteo=meteo_data,
            age=age,
            sex=sex
        )
        metrics.decoupling = decoupling
        
        # CALCOLA SCORE V6 DARKRITUAL (Competitive Efficiency Index)
        nominal_pwr_kg = ftp / weight
        score, details = engine.compute_score_v6_darkritual_wrapper(
            metrics, 
            nominal_power=nominal_pwr_kg,
            target_hr_eff=1.0,
            athlete_level="intermediate",
            db_baseline_adj=None
        )
        
        # Rank e Quality basati su SCORE REALE
        rank, _ = engine.get_rank(score)
        quality = engine.run_quality(score)
        
        run = {
            "id": 9000000 + i,
            "Data": date.strftime("%Y-%m-%d"),
            "Moving Time": duration_sec,
            "Dist (km)": distance_km,
            "Power": avg_power,
            "HR": avg_hr,
            "Decoupling": round(decoupling * 100, 1),
            "SCORE": round(score, 1),
            "WCF": round(details.get('wcf', 1.0), 2),
            "WR_Pct": 0.0,  # Deprecated
            "Rank": rank,
            "Quality": quality,
            "Meteo": f"{temp}°C",
            "ai_feedback": None,
            "SCORE_DETAIL": {
                "W/kg": round(metrics.w_kg, 2),
                "Nominal": round(details.get('nominal_pwr', 0), 2),
                "Mech Eff": round(details.get('mech_eff', 0), 2),
                "Metabolic Eff": round(details.get('metabolic_eff', 0), 2),
                "WCF": round(details.get('wcf', 1.0), 2),
                "Stability": round(details.get('stability', 0), 2),
                "Target T_adj": "N/A"
            },
            "raw_watts": raw_watts,
            "raw_hr": raw_hr,
            "Achievements": ["🎯 Personal Best 5K"] if i == 5 else [],
            "Trend": {
                "direction": "up" if score > 70 else "flat",
                "message": "Ottima forma!" if score > 75 else "Stabile"
            },
            "Comparison": {
                "score": round(score, 1),
                "percentile": int((score / 100) * 90)  # Approssimazione
            }
        }
        
        demo_runs.append(run)
    
    # Calcola medie mobili (come nel sync reale)
    import pandas as pd
    df = pd.DataFrame(demo_runs)
    df['Data'] = pd.to_datetime(df['Data'])
    df = df.sort_values('Data')
    
    # Aggiungi SCORE_MA_7 per trend
    df['SCORE_MA_7'] = df['SCORE'].rolling(window=7, min_periods=1).mean()
    
    # Converti back a dict list
    demo_runs = df.to_dict('records')
    
    # Ordina dal più recente
    demo_runs.sort(key=lambda x: x['Data'], reverse=True)
    
    return demo_runs

def get_demo_athlete():
    """
    Restituisce un profilo atleta demo.
    """
    return {
        "athlete": {
            "id": 99999999,
            "firstname": "Demo",
            "lastname": "Runner",
            "profile": "avatar_demo.png",
            "city": "Rome",
            "country": "Italy",
            "sex": "M",
            "weight": 70.0
        },
        "access_token": "demo_token_fake"
    }
