import pandas as pd
from typing import Dict, Any, List
from engine.core import ScoreEngine
from engine.metrics import MetricsCalculator

class DashboardLogic:
    """
    Logic layer for the Dashboard view.
    Handles data transformation and preparation before visualization.
    """
    def __init__(self, engine: ScoreEngine):
        self.engine = engine

    def prepare_trend_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculates moving averages and sorts data.
        """
        if df.empty: return df
        df = self.engine.calculate_trend_metrics(df)
        return df.sort_values("Data", ascending=False)

    def calculate_delta(self, df: pd.DataFrame) -> float:
        """
        Calculates the delta between current and previous run's MA7.
        """
        if len(df) < 2: return 0.0
        # Ensure we are accessing the first and second row after sorting
        return df.iloc[0]['SCORE_MA_7'] - df.iloc[1]['SCORE_MA_7']

    def prepare_consistency_score(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Prepares the DataFrame for consistency score calculation by mapping columns
        and calculating moving time if missing.
        Delegates calculation to the engine.
        """
        if df.empty: return {}
        
        cons_df = df.copy()
        
        # Mapping Data columns
        if 'Data' in cons_df.columns: 
            cons_df['date'] = cons_df['Data']
        
        # Mapping Distance
        if 'Dist (km)' in cons_df.columns: 
            cons_df['distance_km'] = cons_df['Dist (km)']
        
        # Calculate Moving Time Logic
        cons_df['moving_time_min'] = cons_df.apply(
            lambda x: len(x.get('raw_watts') or [])/60 if x.get('raw_watts') else (x.get('Dist (km)', 0) * 5), 
            axis=1
        )

        return self.engine.calculate_consistency_score(cons_df)

    def get_zones(self, run_data: pd.Series, ftp: int) -> Dict[str, float]:
        """Calculates power zones distribution."""
        return self.engine.calculate_zones(run_data.get('raw_watts', []), ftp)

    def get_efficiency_factor(self, run_data: pd.Series) -> Dict[str, Any]:
        """Calculates efficiency factor (EF)."""
        return MetricsCalculator.calculate_efficiency_factor(run_data.get('raw_watts', []), run_data.get('raw_hr', []))

    def get_run_quality(self, score: float) -> Dict[str, Any]:
        """Determines run quality label/color based on score."""
        return self.engine.run_quality(score)
