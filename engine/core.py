import logging
import pandas as pd
from typing import List, Dict, Any, Optional
from config import Config

# Components
from .metrics import RunMetrics, MetricsCalculator
from .scoring import ScoringSystem
from .insights import InsightsEngine

logger = logging.getLogger("sCore.Engine")

class ScoreEngine:
    """
    Facade for the Modularized Score Engine v6.
    Integrazione Best Efforts: calcola la performance relativa ai record personali.
    """
    def __init__(self):
        self.version = Config.ENGINE_VERSION
        self.metrics = MetricsCalculator()
        self.scoring = ScoringSystem()
        self.insights = InsightsEngine()

    # --- DELEGATED TO METRICS CALCULATOR ---
    def calculate_decoupling(self, power: List[float], hr: List[float], window: int = 300) -> float:
        return self.metrics.calculate_decoupling(power, hr)
    
    def calculate_zones(self, watts: List[float], ftp: int) -> Dict[str, float]:
        return self.metrics.calculate_zones(watts, ftp)
        
    def calculate_hr_zones(self, hr_stream: List[float], zones_config: Dict) -> Dict[str, float]:
        return self.metrics.calculate_hr_zones(hr_stream, zones_config)

    def calculate_t_adj(self, metrics: RunMetrics) -> float:
        return self.metrics.calculate_t_adj(metrics)

    # --- DELEGATED TO SCORING SYSTEM ---
    # compute_score_v6_pure REMOVED - See score_v6_pure_BACKUP.txt
    
    def compute_score_v6_darkritual_wrapper(self, metrics: RunMetrics, nominal_power: float, target_hr_eff: float, athlete_level: str = "intermediate", db_baseline_adj: Optional[float] = None) -> Tuple[float, Dict[str, Any]]:
        """Wrapper for darkritual algorithm with athlete level parameter"""
        return self.scoring.compute_score_v6_darkritual(metrics, nominal_power, target_hr_eff, athlete_level)
        
    def get_rank(self, score: float) -> Tuple[str, str]:
        return self.scoring.get_rank(score)
        
    def run_quality(self, score: float) -> Dict[str, str]:
        return self.scoring.run_quality(score)

    def compute_score(self, metrics: RunMetrics, decoupling: float, athlete_bests: List[Dict] = None) -> Tuple[float, Dict[str, Any], float, float, Dict[str, str]]:
        """
        Orchestra il calcolo dello SCORE e dei benchmark personali.
        
        :param athlete_bests: Lista di dict dal DB (es. [{"distance_type": "5k", "best_time": 1200, ...}])
        """
        metrics.decoupling = decoupling 
        
        # 1. Calcolo Base Score (SCORE 4.1 'Dark Ritual')
        # Parametri aggiuntivi per la nuova formula
        nominal_power = Config.W_REF
        target_hr_eff = 1.0
        athlete_level = "intermediate" # Default fallback, should be passed or configurable
        
        score, details = self.scoring.compute_score_v6_darkritual(
            metrics, 
            nominal_power, 
            target_hr_eff,
            athlete_level
        )
        
        wcf = details.get('wcf', 1.0)
        
        # 2. Calcolo WR % (Benchmark Mondiale Statico)
        wr_pct = 0.0
        if metrics.weight > 0 and metrics.avg_power > 0:
            w_kg = metrics.avg_power / metrics.weight
            wr_pct = (w_kg / Config.WR_WKG) * 100
        
        # 3. NUOVO: Calcolo Personal Best % (Benchmark Relativo)
        # Se abbiamo i record personali, calcoliamo quanto questa attività si avvicina al picco dell'atleta
        pb_pct = 0.0
        if athlete_bests and metrics.duration_sec > 0:
            # Cerchiamo il Best Effort più vicino alla distanza attuale (es. 5k, 10k)
            # Nota: logicamente potresti voler confrontare i Watt/kg o il Tempo. 
            # Qui implementiamo la logica di 'vicinanza al tempo record' se la distanza è simile.
            current_dist = metrics.distance_meters
            relevant_pb = self._find_relevant_best(current_dist, athlete_bests)
            
            if relevant_pb and relevant_pb['best_time'] > 0:
                # Esempio: Rapporto tra tempo record e tempo attuale (normalizzato)
                # Se l'atleta corre alla stessa velocità del suo PB, pb_pct = 100%
                pb_pct = (relevant_pb['best_time'] / metrics.duration_sec) * 100

        quality = self.scoring.run_quality(score)
        
        # Aggiungiamo i dati dei Best Effort ai dettagli per la UI
        details['pb_pct'] = pb_pct
        
        return score, details, wcf, wr_pct, quality

    def _find_relevant_best(self, distance: float, bests: List[Dict]) -> Optional[Dict]:
        """Helper per trovare il record personale più pertinente alla distanza attuale"""
        # Tolleranza del 10% sulla distanza per considerare un record comparabile
        for b in bests:
            # Esempio: se distanza è ~5000m e abbiamo un record '5k'
            d_type = b.get('distance_type', '').lower()
            if "5k" in d_type and 4500 <= distance <= 5500: return b
            if "10k" in d_type and 9000 <= distance <= 11000: return b
            if ("half" in d_type or "hm" in d_type) and 20000 <= distance <= 22000: return b
        return None

    # --- DELEGATED TO INSIGHTS ENGINE ---
    def achievements(self, scores_history):
        return self.insights.achievements(scores_history)
        
    def analyze_smart_quality_trend(self, df):
        return self.insights.analyze_smart_quality_trend(df)
        
    def calculate_consistency_score(self, df):
        return self.insights.calculate_consistency_score(df)

    def calculate_trend_metrics(self, df):
        if df.empty or 'SCORE' not in df.columns: return df
        result = df.copy().sort_values("Data")
        result["SCORE_MA_7"] = result["SCORE"].rolling(7, min_periods=1).mean()
        result["SCORE_MA_28"] = result["SCORE"].rolling(28, min_periods=1).mean()
        return result

    # --- COMPOSED METHODS ---
    def gaming_feedback(self, scores_history: List[float], activities_df: pd.DataFrame = None) -> Dict[str, Any]:
        """Composed method aggregating insights"""
        if not scores_history: return {}

        quality = self.run_quality(scores_history[-1])
        achievs = self.achievements(scores_history)
        
        if activities_df is not None and not activities_df.empty and 'SCORE' in activities_df.columns:
            trend_df = activities_df
        else:
            dates = pd.date_range(end=pd.Timestamp.now(), periods=len(scores_history), freq='D')
            trend_df = pd.DataFrame({'Data': dates, 'SCORE': scores_history})
            
        trend = self.analyze_smart_quality_trend(trend_df)
        
        consistency = {}
        if activities_df is not None:
             consistency = self.calculate_consistency_score(activities_df)

        return {
            "quality": quality,
            "achievements": achievs,
            "trend": trend,
            "comparison": consistency
        }



