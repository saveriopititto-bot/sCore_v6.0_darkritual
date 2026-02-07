import numpy as np
import logging
from typing import Tuple, Dict, Any, Optional
from config import Config
from .metrics import RunMetrics

logger = logging.getLogger("sCore.Engine.Scoring")

class ScoringSystem:
    """Gestisce il calcolo dello SCORE e delle classifiche."""
    def __init__(self) -> None:
        self.version = Config.ENGINE_VERSION


    
    # SCORE 4.1 - Dark Ritual Algorithm

    def compute_score_v6_darkritual(self, metrics: RunMetrics, 
                                    nominal_power: float, 
                                    target_hr_eff: float,
                                    athlete_level: str = "intermediate") -> Tuple[float, Dict[str, Any]]:
        """
        SCORE 4.1 - Robust Competitive Efficiency Index
        
        Formula: SCORE = exp(ln W_eff - ln HRR_eff + ln WCF + ln P_eff - α*√(D/T))
        where P = T_ref / T_act
        
        Args:
            metrics: RunMetrics object with activity data
            nominal_power: Target power (W/kg) for athlete
            target_hr_eff: Target HR efficiency
            athlete_level: "elite"|"sub_elite"|"advanced"|"intermediate"|"amateur"
        """
        import json
        import math
        from pathlib import Path
        
        # === 1. LOAD WORLD RECORDS ===
        wr_path = Path(__file__).parent.parent / "assets" / "bestwr.json"
        with open(wr_path, 'r') as f:
            wr_data = json.load(f)
        
        # === 2. FIND CLOSEST WORLD RECORD ===
        dist_m = metrics.distance_meters
        # New distance mapping for assets/bestwr.json (which uses '5k', '10k', 'hm', 'm')
        dist_map = {
            5000: "5k",
            10000: "10k",
            21097: "hm",
            42195: "m"
        }
        closest_dist = min(dist_map.keys(), key=lambda x: abs(x - dist_m))
        wr_key = dist_map[closest_dist]
        
        # T_WR is the base record (men_elite used as baseline before factors)
        T_WR = wr_data["records"][wr_key]["men_elite"]
        
        # === 3. CALCULATE DYNAMIC REFERENCE TIME ===
        # F_age: minimum at 30 years, quadratic growth
        k_a = 0.15
        F_age = 1 + k_a * ((metrics.age - 30) / 30) ** 2
        
        # F_sex: gender gap from world records
        F_sex = 1.0 if metrics.sex.upper() == "M" else 1.10
        
        # F_level: athletic level factor
        level_factors = {
            "elite": 1.00,
            "sub_elite": 1.05,
            "advanced": 1.12,
            "intermediate": 1.20,
            "amateur": 1.35
        }
        F_level = level_factors.get(athlete_level.lower(), 1.20)
        
        # F_env: environmental penalty (temperature only, humidity in WCF)
        F_env = 1 + 0.01 * max(0, metrics.temp_c - 15)
        
        # T_ref calculation (F_surface removed as requested)
        T_ref = T_WR * F_age * F_sex * F_level * F_env
        T_act = metrics.duration_sec
        
        # === 4. EFFICIENCY COMPONENTS ===
        # 4a. Mechanical Efficiency (W_eff)
        if nominal_power <= 0:
            nominal_power = 1.0
        power_ratio = metrics.w_kg / nominal_power
        W_eff = max(0.01, power_ratio)  # Prevent log(0)
        
        # 4b. Heart Rate Reserve Efficiency
        hr_reserve = metrics.hr_max - metrics.hr_rest
        if hr_reserve <= 0:
            hr_reserve = 60  # Safe default
        hrr = (metrics.hr_avg - metrics.hr_rest) / hr_reserve
        
        if target_hr_eff <= 0:
            target_hr_eff = 0.75
        HRR_eff = max(0.01, hrr / target_hr_eff)
        
        # 4c. Weather Correction Factor
        temp_penalty = max(0, 0.012 * (metrics.temp_c - 20))
        hum_penalty = max(0, 0.005 * (metrics.humidity - 60))
        WCF = 1 + temp_penalty + hum_penalty
        
        # 4d. Performance Efficiency
        P_eff = max(0.01, T_ref / T_act)  # Prevent log(0 or neg)
        
        # 4e. Aerobic Stability Penalty
        alpha = 0.15  # Stability coefficient
        D = metrics.decoupling  # Decoupling percentage
        T = max(1, T_act / 60)  # Time in minutes
        stability_penalty = alpha * math.sqrt(D / T)
        
        # === 5. FINAL SCORE CALCULATION (LOG-LINEAR FORM) ===
        try:
            log_score = (
                math.log(W_eff)
                - math.log(HRR_eff)
                + math.log(WCF)
                + math.log(P_eff)
                - stability_penalty
            )
            raw_score = math.exp(log_score)
            
            # Normalize to 0-100 scale with saturation
            score = 100 * (1 - math.exp(-1.8 * raw_score))
            score = np.clip(score, 0, 100)
            
        except (ValueError, OverflowError) as e:
            logger.error(f"SCORE 4.1 calculation error: {e}")
            score = 0.0
            raw_score = 0.0
        
        # === 6. DETAILED BREAKDOWN ===
        details = {
            "algo": "score_4.1_darkritual",
            "version": "4.1",
            # Reference Time Components
            "T_WR": round(T_WR, 1),
            "T_ref": round(T_ref, 1),
            "T_act": round(T_act, 1),
            "closest_wr_dist": wr_key,
            # Factors
            "F_age": round(F_age, 3),
            "F_sex": F_sex,
            "F_level": F_level,
            "F_env": round(F_env, 3),
            # Efficiencies (native keys)
            "W_eff": round(W_eff, 3),
            "HRR_eff": round(HRR_eff, 3),
            "WCF": round(WCF, 3),
            "P_eff": round(P_eff, 3),
            "stability_penalty": round(stability_penalty, 3),
            # Final
            "raw_score": round(raw_score, 3),
            "normalized_score": round(score, 1),
            
            # === COMPATIBILITY LAYER FOR sync_controller.py ===
            # These keys ensure backward compatibility with UI expectations
            "nominal_pwr": nominal_power,           # Expected by SCORE_DETAIL
            "mech_eff": round(W_eff, 3),           # Alias for W_eff
            "metabolic_eff": round(HRR_eff, 3),    # Alias for HRR_eff
            "wcf": round(WCF, 3),                  # Lowercase alias
            "stability": max(0, 1 - round(stability_penalty, 3))  # Invert penalty to positive metric
        }
        
        return score, details

    @staticmethod
    def get_rank(score: float) -> Tuple[str, str]:
        t = Config.Thresholds
        c = Config.Theme
        if score >= 100: return "ELITE 🏆", "text-purple-600"
        if score >= t.EPIC: return "PRO 🥇", "text-blue-600"
        if score >= t.GREAT: return "ADVANCED 🥈", "text-green-600"
        if score >= t.SOLID: return "INTERMEDIATE 🥉", "text-yellow-600"
        return "ROOKIE 🎗️", "text-gray-600"

    @staticmethod
    def run_quality(score: float) -> Dict[str, str]:
        """Returns Label and Color for UI"""
        if score is None or score <= 0:
            return {"label": "🚫 N/D", "color": Config.Theme.SCORE_WASTED} 
        
        t = Config.Thresholds
        c = Config.Theme
        
        if score >= t.EPIC: return {"label": "🏆 Epic Run", "color": c.SCORE_EPIC}      
        if score >= t.GREAT: return {"label": "💎 Great Run", "color": c.SCORE_GREAT}     
        if score >= t.SOLID: return {"label": "⚡ Solid Run", "color": c.SCORE_SOLID}     
        return {"label": "🐌 Weak Run", "color": c.SCORE_WEAK}
