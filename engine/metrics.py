import numpy as np
from typing import List, Dict
import logging
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger("sCore.MeteoData")

@dataclass
class MeteoData:
    temperature: float = 20.0
    humidity: float = 50.0
    is_real: bool = False

    @classmethod
    def fetch_for_activity(cls, activity_data: dict):
        """
        Factory Method: Crea un oggetto MeteoData partendo dai dati grezzi dell'attività.
        Si occupa lui di chiamare il servizio esterno se i dati sono disponibili.
        """
        # 1. Estrazione dati geospaziali
        latlng = activity_data.get('start_latlng')
        date_str = activity_data.get('start_date_local')
        
        # 2. Se mancano i dati, restituisce un oggetto "Default" (vuoto)
        if not latlng or not date_str:
            return cls()  # Chiama il costruttore coi default (20°, 50%, False)

        # 3. Tentativo di Fetch
        try:
            # Import locale per evitare cicli: L'Engine usa il Service solo qui
            from services.meteo_svc import WeatherService
            
            dt_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
            
            # Chiamata al servizio
            t, h, is_real = WeatherService.get_weather(
                lat=latlng[0], 
                lon=latlng[1], 
                date_str=dt_obj.strftime("%Y-%m-%d"), 
                hour=dt_obj.hour
            )
            
            # Restituisce l'oggetto popolato
            return cls(temperature=t, humidity=h, is_real=is_real)
            
        except Exception as e:
            logger.warning(f"Meteo fetch failed: {e}")
            return cls()  # Fallback sicuro in caso di errore

logger = logging.getLogger("sCore.Engine.Metrics")

class RunMetrics:
    def __init__(self, avg_power: float, avg_hr: float, distance: float, moving_time: int, 
                 elevation_gain: float, weight: float, hr_max: int, hr_rest: int, 
                 meteo: MeteoData, age: int = 30, sex: str = "M"):
        self.avg_power = avg_power
        self.avg_hr = avg_hr
        self.distance_meters = distance
        self.moving_time = moving_time
        self.elevation_gain = elevation_gain
        self.weight = weight if weight > 0 else 70.0 
        self.hr_max = hr_max
        self.hr_rest = hr_rest
        self.meteo = meteo
        self.temperature = meteo.temperature
        self.humidity = meteo.humidity
        self.age = age
        self.sex = sex
        self.decoupling = 0.0

    @property
    def hr_avg(self): return self.avg_hr
    @property
    def temp_c(self): return self.temperature
    @property
    def duration_sec(self): return self.moving_time
    @property
    def w_kg(self): return self.avg_power / self.weight if self.weight > 0 else 0
    @property
    def dist_label(self):
        d = self.distance_meters
        if d < 8000: return "5k"
        elif d < 16000: return "10k"
        elif d < 30000: return "hm"
        return "m"
    @property
    def ascent(self): return self.elevation_gain
    @property
    def distance_m(self): return self.distance_meters

@dataclass
class FullActivityRecord:
    id: int
    name: str
    date: str
    moving_time: int
    distance: float
    total_elevation_gain: float
    average_watts: float
    average_heartrate: float
    calories: float
    device_name: str
    has_heartrate: bool
    # Complex fields
    best_efforts: List[Dict] = field(default_factory=list)
    streams: Dict[str, List] = field(default_factory=dict)
    # Metadata
    is_weather_real: bool = False
    temperature: float = 20.0
    humidity: float = 50.0

@dataclass
class AthleteBests:
    distance_type: str
    best_time_seconds: int
    activity_id: int
    achieved_at: str

class MetricsCalculator:
    @staticmethod
    def calculate_decoupling(power_stream: List[float], hr_stream: List[float]) -> float:
        """Drift Fisiologico (PW:HR)"""
        if not power_stream or not hr_stream: return 0.0
        
        power = np.array(power_stream)
        hr = np.array(hr_stream)

        if len(power) < 120 or len(hr) < 120: return 0.0

        n = len(power)
        split = int(n * 0.5)

        p1, h1 = np.mean(power[:split]), np.mean(hr[:split])
        p2, h2 = np.mean(power[split:]), np.mean(hr[split:])

        if p1 <= 0 or p2 <= 0 or h1 <= 0 or h2 <= 0: return 0.0

        cost1 = h1 / p1
        cost2 = h2 / p2
        drift = (cost2 - cost1) / cost1
        
        return float(max(0.0, drift))

    @staticmethod
    def calculate_efficiency_factor(watts: List[float], hr: List[float]) -> Dict[str, Any]:
        """
        Calcola l'Efficiency Factor (EF) come rapporto Potenza/HR.
        """
        # 1. Creazione DataFrame per allineare i dati
        if not watts or not hr or len(watts) != len(hr):
            return {"ef": 0.0, "interpretation": "N/A", "avg_power_clean": 0.0, "avg_hr_clean": 0}

        # Use numpy for faster filtering if possible, but pandas is robust
        # We need pandas here or re-implement filtering logic. 
        # Since MetricsCalculator imports numpy, let's use numpy or keep pandas if already imported.
        # engine/metrics.py does NOT import pandas currently. 
        # Check imports: import numpy as np.
        # So I should implementation using numpy to avoid adding pandas dependency to metrics.py if it's not there.
        # Wait, core.py imports pandas. metrics.py does NOT.
        # I should use numpy for filtering.
        
        w_arr = np.array(watts)
        h_arr = np.array(hr)
        
        # Valid mask: watts > 10 AND hr > 40
        mask = (w_arr > 10) & (h_arr > 40)
        
        valid_w = w_arr[mask]
        valid_h = h_arr[mask]
        
        if len(valid_w) == 0:
             return {"ef": 0.0, "interpretation": "Insufficient Data", "avg_power_clean": 0.0, "avg_hr_clean": 0}
             
        avg_power = np.mean(valid_w)
        avg_hr = np.mean(valid_h)
        
        if avg_hr == 0: return {"ef": 0.0, "interpretation": "Error"} # div by zero protection

        ef = avg_power / avg_hr
        
        # INTERPRETAZIONE
        rating = ""
        if ef < 1.1: rating = "Low Aerobic Base"
        elif 1.1 <= ef < 1.3: rating = "Good (Amateur)"
        elif 1.3 <= ef < 1.5: rating = "Very Good (Competitive)"
        elif ef >= 1.5: rating = "Elite / Pro"

        return {
            "ef": round(float(ef), 2),
            "interpretation": rating,
            "avg_power_clean": round(float(avg_power), 1),
            "avg_hr_clean": int(avg_hr)
        }


    @staticmethod
    def calculate_zones(watts_stream: List[int], ftp: int) -> Dict[str, float]:
        """Coggan Zones Distribution"""
        if not watts_stream or not ftp: return {}
        zones = [0]*7
        limits = [0.55, 0.75, 0.90, 1.05, 1.20, 1.50] 
        for w in watts_stream:
            if w < ftp * limits[0]: zones[0]+=1
            elif w < ftp * limits[1]: zones[1]+=1
            elif w < ftp * limits[2]: zones[2]+=1
            elif w < ftp * limits[3]: zones[3]+=1
            elif w < ftp * limits[4]: zones[4]+=1
            elif w < ftp * limits[5]: zones[5]+=1
            else: zones[6]+=1
        total = len(watts_stream)
        return {f"Z{i+1}": round(c/total*100, 1) for i, c in enumerate(zones)}

    @staticmethod
    def calculate_hr_zones(hr_stream: List[int], zones_config: Dict) -> Dict[str, float]:
        """Time in HR Zones"""
        if not hr_stream or not zones_config or 'zones' not in zones_config: return {}
        zones_def = zones_config['zones']
        counts = [0] * len(zones_def)
        limits = [(z.get('min', 0), z.get('max', 250)) for z in zones_def]
        
        for h in hr_stream:
            for i, (mn, mx) in enumerate(limits):
                if mx == -1: mx = 300
                if mn <= h <= mx:
                     counts[i] += 1
                     break
        total = len(hr_stream)
        return {f"Z{i+1}": round(c/total*100, 1) if total > 0 else 0 for i, c in enumerate(counts)}

    @staticmethod
    def calculate_t_adj(m: RunMetrics) -> float:
        """Helper to calculate Adjusted Time (depurated)"""
        if not m: return 0.0
        f_age = 1 + 0.15 * ((m.age - 30) / 30) ** 2
        f_sex = 1.0 if m.sex == "M" else 1.10
        f_env = 1 + 0.01 * max(0, m.temp_c - 15)
        # Avoid division by zero
        denom = f_age * f_sex * f_env
        if denom <= 0: return m.duration_sec
        return m.duration_sec / denom
