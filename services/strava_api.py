import requests
import time
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("sCore.Strava")

class StravaService:
    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://www.strava.com/api/v3"

    def get_auth_url(self, redirect_uri: str) -> str:
        scope = "activity:read_all,profile:read_all"
        return (f"https://www.strava.com/oauth/authorize?client_id={self.client_id}"
                f"&response_type=code&redirect_uri={redirect_uri}&approval_prompt=force&scope={scope}")

    def exchange_token(self, code: str) -> Optional[Dict[str, Any]]:
        url = "https://www.strava.com/oauth/token"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code"
        }
        return self._post_request(url, data)

    def fetch_activities(self, token: str, page: int = 1, per_page: int = 50) -> List[Dict[str, Any]]:
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{self.base_url}/athlete/activities"
        params = {"page": page, "per_page": per_page}
        return self._request_with_retry("GET", url, headers=headers, params=params) or []

    def fetch_authenticated_athlete(self, token: str) -> Optional[Dict[str, Any]]:
        """Recupera il profilo dettagliato dell'atleta loggato (include peso, ecc)"""
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{self.base_url}/athlete"
        return self._request_with_retry("GET", url, headers=headers)


    def fetch_all_activities_simple(self, token, per_page=50, max_pages=20):
        """
        Fetch robusto: prende TUTTE le attività disponibili tramite paginazione.
        Wrapper around fetch_activities to match existing interface expected by sync_controller.
        """
        all_activities = []
        for page in range(1, max_pages + 1):
            acts = self.fetch_activities(token, page, per_page)
            if not acts:
                break
            all_activities.extend(acts)
            if len(acts) < per_page:
                break
            time.sleep(0.5) 
        return all_activities

    def fetch_streams(self, token: str, activity_id: int) -> Optional[Dict[str, Any]]:
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{self.base_url}/activities/{activity_id}/streams"
        params = {"keys": "watts,heartrate,altitude,cadence,grade_smooth", "key_by_type": "true"}
        return self._request_with_retry("GET", url, headers=headers, params=params)

    def fetch_full_activity_data(self, token: str, activity_id: int) -> Dict[str, Any]:
        """
        Recupera il pacchetto completo: Dettagli, Best Efforts e tutti gli Stream.
        """
        headers = {"Authorization": f"Bearer {token}"}
        
        # 1. GET ACTIVITY DETAIL (Include Best Efforts e Mappa)
        detail_url = f"{self.base_url}/activities/{activity_id}"
        activity_detail = self._request_with_retry("GET", detail_url, headers=headers) or {}

        # 2. GET STREAMS (Dati al secondo)
        stream_keys = [
            "time", "watts", "heartrate", "altitude", "cadence", 
            "velocity_smooth", "grade_smooth", "latlng", "temp", "distance"
        ]
        streams_url = f"{self.base_url}/activities/{activity_id}/streams"
        params = {"keys": ",".join(stream_keys), "key_by_type": "true"}
        streams = self._request_with_retry("GET", streams_url, headers=headers, params=params) or {}

        # 3. Assemble Full Packet
        return {
            "summary": activity_detail,
            "streams": streams,
            "metadata": {
                "has_poly": bool(activity_detail.get('map', {}).get('polyline')),
                "has_efforts": len(activity_detail.get('best_efforts', [])) > 0,
                "device": activity_detail.get('device_name')
            }
        }

    def fetch_zones(self, token: str) -> Optional[Dict[str, Any]]:
        headers = {"Authorization": f"Bearer {token}"}
        url = f"{self.base_url}/athlete/zones"
        return self._request_with_retry("GET", url, headers=headers)

    def fetch_athlete_stats(self, token: str, athlete_id: int) -> Optional[Dict[str, Any]]:
        """
        Recupera le statistiche aggregate dell'atleta e i Best Efforts.
        Questa chiamata è costosa, da usare solo se refresh richiesto.
        """
        url = f"{self.base_url}/athletes/{athlete_id}/stats"
        headers = {"Authorization": f"Bearer {token}"}
        return self._request_with_retry("GET", url, headers=headers)

    def _request_with_retry(self, method: str, url: str, **kwargs) -> Optional[Any]:
        for i in range(3):
            try:
                res = requests.request(method, url, timeout=10, **kwargs)
                if res.status_code == 200:
                    return res.json()
                if res.status_code == 429:
                    time.sleep(5 * (i + 1))
                    continue
                break
            except Exception as e:
                logger.error(f"Strava API Error: {e}")
        return None

    def _post_request(self, url: str, data: Dict) -> Optional[Dict]:
        try:
            res = requests.post(url, data=data, timeout=10)
            return res.json() if res.status_code == 200 else None
        except Exception: return None
