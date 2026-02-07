import streamlit as st
from dataclasses import dataclass, field
from typing import Optional, List, Any, Dict
from datetime import date, datetime, timedelta

@dataclass
class AppState:
    """
    Centralized State Manager for the Streamlit Application.
    Uses st.session_state as the backing store to ensure persistence across reruns.
    """
    
    # Define keys and default values
    _defaults = {
        "theme": "light",
        "dev_mode": False,
        "strava_token": None,
        "data": [],
        "demo_mode": False,
        "show_demo_page": False,
        "initial_sync_done": False,
        "filter_start_date": datetime.now().date() - timedelta(days=90),
        "authenticated": False
    }

    def __post_init__(self):
        # Initialize session state with defaults if not present
        for key, value in self._defaults.items():
            if key not in st.session_state:
                st.session_state[key] = value

    @property
    def theme(self) -> str:
        return st.session_state.theme

    @theme.setter
    def theme(self, value: str):
        st.session_state.theme = value

    @property
    def dev_mode(self) -> bool:
        return st.session_state.dev_mode
    
    @dev_mode.setter
    def dev_mode(self, value: bool):
        st.session_state.dev_mode = value

    @property
    def strava_token(self) -> Optional[Dict[str, Any]]:
        return st.session_state.strava_token

    @strava_token.setter
    def strava_token(self, value: Optional[Dict[str, Any]]):
        st.session_state.strava_token = value

    @property
    def data(self) -> List[Dict[str, Any]]:
        return st.session_state.data

    @data.setter
    def data(self, value: List[Dict[str, Any]]):
        st.session_state.data = value

    @property
    def demo_mode(self) -> bool:
        return st.session_state.demo_mode

    @demo_mode.setter
    def demo_mode(self, value: bool):
        st.session_state.demo_mode = value

    @property
    def show_demo_page(self) -> bool:
        return st.session_state.show_demo_page

    @show_demo_page.setter
    def show_demo_page(self, value: bool):
        st.session_state.show_demo_page = value

    @property
    def initial_sync_done(self) -> bool:
        return st.session_state.get("initial_sync_done", False)

    @initial_sync_done.setter
    def initial_sync_done(self, value: bool):
        st.session_state.initial_sync_done = value

    @property
    def filter_start_date(self) -> date:
        return st.session_state.get("filter_start_date", self._defaults["filter_start_date"])

    @filter_start_date.setter
    def filter_start_date(self, value: date):
        st.session_state.filter_start_date = value

    @property
    def authenticated(self) -> bool:
        return st.session_state.get("authenticated", False)

    @authenticated.setter
    def authenticated(self, value: bool):
        st.session_state.authenticated = value

    @staticmethod
    def get_instance() -> 'AppState':
        """Singleton accessor for AppState."""
        if "app_state" not in st.session_state:
            st.session_state.app_state = AppState()
        return st.session_state.app_state

# Helper to get state easily
def get_state() -> AppState:
    return AppState.get_instance()
