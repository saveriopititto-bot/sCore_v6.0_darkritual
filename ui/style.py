import streamlit as st
import os
from config import Config

def load_css_file(filename="style.css"):
    with open(os.path.join(os.path.dirname(__file__), filename)) as f:
        return f.read()

def apply_theme(theme_mode="light"):
    """
    Injects CSS for Glassmorphic Design System.
    Uses centralized Config.Theme colors.
    """
    t = Config.Theme
    
    if theme_mode == "dark":
        params = {
            "bg": t.BG_DARK,
            "card": t.CARD_DARK,
            "text": t.TEXT_DARK,
            "border": t.GLASS_BORDER_DARK,
            "primary": t.PRIMARY
        }
    else:
        params = {
            "bg": t.BG_LIGHT,
            "card": t.CARD_LIGHT,
            "text": t.TEXT_LIGHT,
            "border": t.GLASS_BORDER_LIGHT,
            "primary": t.PRIMARY
        }

    # Load and Format CSS
    css_template = load_css_file()
    
    # Use replace instead of format to avoid issues with CSS curly braces
    css = css_template.replace("{bg}", params["bg"])
    css = css.replace("{card}", params["card"])
    css = css.replace("{text}", params["text"])
    css = css.replace("{border}", params["border"])
    css = css.replace("{primary}", params["primary"])
    
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
