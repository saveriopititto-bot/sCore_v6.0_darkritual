import requests
import logging
from typing import Tuple, Optional

logger = logging.getLogger("sCore.Meteo")

class WeatherService:
    @staticmethod
    def get_weather(lat: float, lon: float, date_str: str, hour: int) -> Tuple[float, float, bool]:
        """Recupera dati meteo storici o forecast da Open-Meteo."""
        urls = [
            "https://archive-api.open-meteo.com/v1/archive",
            "https://api.open-meteo.com/v1/forecast"
        ]
        
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": date_str,
            "end_date": date_str,
            "hourly": "temperature_2m,relative_humidity_2m"
        }

        for url in urls:
            try:
                res = requests.get(url, params=params, timeout=5)
                if res.status_code == 200:
                    data = res.json()
                    if "hourly" in data:
                        idx = min(hour, 23)
                        temp = data["hourly"]["temperature_2m"][idx]
                        hum = data["hourly"]["relative_humidity_2m"][idx]
                        if temp is not None:
                            return float(temp), float(hum), True
            except Exception as e:
                logger.error(f"Errore su {url}: {e}")
                continue

        return 20.0, 50.0, False  # Fallback Standard
