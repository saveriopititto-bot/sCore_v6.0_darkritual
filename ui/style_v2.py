import streamlit as st
from config import Config

def load_custom_css():
    """
    Injects Tailwind CSS (via CDN) and custom style overrides.
    """
    st.markdown("""
        <!-- Tailwind CSS via CDN (Development Only - Use build step for Prod) -->
        <script src="https://cdn.tailwindcss.com"></script>
        
        <!-- Google Fonts -->
        <link href="https://fonts.googleapis.com/css2?family=Manrope:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
        <link href="https://fonts.googleapis.com/icon?family=Material+Icons+Round" rel="stylesheet">

        <style>
            /* Custom Scrollbar Hide */
            .no-scrollbar::-webkit-scrollbar {
                display: none;
            }
            .no-scrollbar {
                -ms-overflow-style: none;
                scrollbar-width: none;
            }

            /* Streamlit Overrides to match design */
            .stApp {
                background-color: #F9FAFB; /* Light Background */
                font-family: 'Manrope', sans-serif;
            }
            
            /* Dark Mode Support via Streamlit Theme detection or manual class */
            @media (prefers-color-scheme: dark) {
                .stApp {
                    background-color: #111827; /* Dark Background */
                    color: #f3f4f6;
                }
            }
            
            /* Glassmorphism Utilities */
            .glass-panel {
                background: rgba(255, 255, 255, 0.7);
                backdrop-filter: blur(10px);
                -webkit-backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.3);
            }
            
            /* Ring Gradients */
            .ring-gradient-green {
                background: conic-gradient(#5CB338 0% 100%, transparent 100%);
                border-radius: 50%;
            }
            .ring-gradient-red {
                background: conic-gradient(#FB4141 0% 100%, transparent 100%);
                border-radius: 50%;
            }
            .ring-gradient-yellow {
                background: conic-gradient(#ECE852 0% 100%, transparent 100%);
                border-radius: 50%;
            }
            .ring-gradient-orange-red {
                 background: conic-gradient(#FB4141 0% 75%, #FFC145 75% 100%);
                 border-radius: 50%;
            }

            /* Animations */
            @keyframes pulse-glow {
                0%, 100% { box-shadow: 0 0 15px rgba(92, 179, 56, 0.3); }
                50% { box-shadow: 0 0 25px rgba(92, 179, 56, 0.6); }
            }
            .animate-pulse-glow {
                animation: pulse-glow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
            }

            /* Hide Streamlit default header/footer */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            header {visibility: hidden;}
            
        </style>
        
        <script>
            // Initialize Tailwind Config
            tailwind.config = {
                darkMode: "class",
                theme: {
                    extend: {
                        colors: {
                            primary: "#FF6B6B",
                            secondary: "#5CB338",
                            accent: "#FFC145",
                            warning: "#FB4141",
                            info: "#5C5CFF",
                            "background-light": "#F9FAFB",
                            "background-dark": "#111827",
                            "surface-light": "#FFFFFF",
                            "surface-dark": "#1F2937",
                        },
                        fontFamily: {
                            display: ["Manrope", "sans-serif"],
                            body: ["Manrope", "sans-serif"],
                        },
                        boxShadow: {
                            'soft': '0 4px 20px -2px rgba(0, 0, 0, 0.05)',
                            'glow-green': '0 0 15px rgba(92, 179, 56, 0.3)',
                            'glow-red': '0 0 15px rgba(251, 65, 65, 0.3)',
                            'glow-yellow': '0 0 15px rgba(255, 193, 69, 0.3)',
                        }
                    },
                },
            };
        </script>
    """, unsafe_allow_html=True)

def apply_theme(theme_name=None):
    load_custom_css()
