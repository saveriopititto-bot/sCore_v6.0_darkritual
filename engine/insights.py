import numpy as np
import pandas as pd
import math
from typing import List, Dict, Any
from config import Config

class InsightsEngine:
    
    @staticmethod
    def achievements(scores_last_runs: List[float]) -> List[str]:
        ach = []
        if not scores_last_runs: return ach
        last = scores_last_runs[-1]
        t = Config.Thresholds

        if last >= 95: ach.append("🔥")
        elif last >= t.EPIC: ach.append("🏆")
        elif last >= t.GREAT: ach.append("💎")

        if len(scores_last_runs) >= 5:
            avg5 = np.mean(scores_last_runs[-5:])
            if avg5 >= t.EPIC: ach.append("📈 Consistency Beast (5 runs)")

        if len(scores_last_runs) >= 10:
            avg10 = np.mean(scores_last_runs[-10:])
            if avg10 >= 75: ach.append("🧱 Iron Engine (10 runs)")

        if len(scores_last_runs) >= 3:
            if scores_last_runs[-1] > scores_last_runs[-2] > scores_last_runs[-3]:
                ach.append("🚀 On Fire (3 improving runs)")

        if len(scores_last_runs) >= 4:
            if scores_last_runs[-4] < 50 and last >= t.GREAT:
                ach.append("💪 Comeback")

        return ach

    @staticmethod
    def analyze_smart_quality_trend(df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty or 'SCORE' not in df.columns:
            return {"direction": "flat", "symbol": "=", "message": "Insufficient Data", "delta": 0.0}

        data = df.copy().sort_values("Data")
        
        if 'SCORE_MA_7' not in data.columns:
            data["SCORE_MA_7"] = data["SCORE"].rolling(7, min_periods=1).mean()
        if 'SCORE_MA_28' not in data.columns:
            data["SCORE_MA_28"] = data["SCORE"].rolling(28, min_periods=1).mean()

        recent_history = data['SCORE'].tail(30)
        smart_threshold = 2.0
        if len(recent_history) >= 5:
            volatility = recent_history.std()
            smart_threshold = max(1.0, (0.0 if pd.isna(volatility) else volatility) * 0.5)

        last_row = data.iloc[-1]
        ma_short = last_row['SCORE_MA_7']
        ma_long = last_row['SCORE_MA_28']
        delta = ma_short - ma_long

        if abs(delta) <= smart_threshold:
            return {"direction": "flat", "symbol": "=", "message": "Trend Stabile", "delta": delta}
        elif delta > smart_threshold:
            return {"direction": "up", "symbol": "+", "message": "Trend Positivo", "delta": delta}
        else:
            return {"direction": "down", "symbol": "-", "message": "Trend Negativo", "delta": delta}

    @staticmethod
    def calculate_consistency_score(activities_df: pd.DataFrame) -> Dict[str, Any]:
        if activities_df.empty: return {"score": 0.0}
        
        df = activities_df.copy()
        
        # Normalize columns
        # Normalize columns
        col_map = {'Data': 'date', 'Dist (km)': 'distance_km', 'Moving Time': 'moving_time_min'}
        
        # Avoid creating duplicates if target column already exists
        rename_map = {}
        for k, v in col_map.items():
            if k in df.columns:
                if v in df.columns:
                    # Target exists, just drop the source to avoid ambiguity/duplication
                    # Or keep source but don't rename (we rely on target existing)
                    # Let's trust the 'already existing' one if it was calculated freshly
                    pass 
                else:
                    rename_map[k] = v
        
        if rename_map:
            df = df.rename(columns=rename_map)
        
        if 'moving_time_min' in df.columns and df['moving_time_min'].mean() > 600: 
             # Heuristic: if values are huge, likely seconds, convert to min
             df['moving_time_min'] = df['moving_time_min'] / 60.0

        if 'date' not in df.columns: return {"score": 0.0}
        
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date')

        weekly_stats = df.set_index('date').resample('W-MON').agg({
            'moving_time_min': ['count', 'sum']
        }).fillna(0)
        weekly_stats.columns = ['count', 'min_sum']

        if len(weekly_stats) < 1: return {"score": 0.0}

        current = weekly_stats.iloc[-1]
        N_curr = current['count']
        
        # Simple weighted target logic
        history = weekly_stats.iloc[:-1].tail(3)
        target_count = N_curr if len(history) == 0 else history['count'].mean() # Simplified for brevity

        delta = abs(N_curr - target_count)
        sigma = max(1.0, target_count * 0.5)
        consistency_factor = math.exp(- (delta**2) / (2 * sigma**2))

        raw_score = (N_curr * 20) * consistency_factor
        
        # Normalization
        K = 5.0
        log_val = math.log(1 + raw_score)
        final_score = 100 * (log_val / (log_val + K))

        return {"score": round(final_score, 1)}
