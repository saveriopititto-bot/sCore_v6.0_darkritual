import unittest
import pandas as pd
import numpy as np
from engine.insights import InsightsEngine
from config import Config

class TestInsightsEngine(unittest.TestCase):
    def setUp(self):
        self.insights = InsightsEngine()

    def test_achievements_empty(self):
        ach = self.insights.achievements([])
        self.assertEqual(ach, [])

    def test_achievements_legendary(self):
        # Last score 96 -> Legendary
        ach = self.insights.achievements([80, 85, 96])
        self.assertIn("Legendary Run", ach)

    def test_achievements_consistency_beast(self):
        # 5 runs, avg > 80
        scores = [80, 80, 80, 80, 80]
        ach = self.insights.achievements(scores)
        self.assertIn("Consistency Beast (5 runs)", str(ach))

    def test_analyze_smart_quality_trend_stable(self):
        # Create a DF where short MA ~= Long MA
        # 30 days of 80 score
        dates = pd.date_range(end='2024-01-01', periods=40)
        df = pd.DataFrame({'Data': dates, 'SCORE': [80]*40})
        
        trend = self.insights.analyze_smart_quality_trend(df)
        self.assertEqual(trend["direction"], "flat")
        self.assertEqual(trend["message"], "Trend Stabile")

    def test_analyze_smart_quality_trend_improving(self):
        # Historical 80, Recent 90
        dates = pd.date_range(end='2024-01-01', periods=50)
        scores = [80]*40 + [90]*10
        df = pd.DataFrame({'Data': dates, 'SCORE': scores})
        
        trend = self.insights.analyze_smart_quality_trend(df)
        self.assertEqual(trend["direction"], "up")

    def test_calculate_consistency_score_perfect(self):
        # Perfect consistency: 4 weeks, 3 runs/week, same volume
        dates = []
        for i in range(28):
             dates.append(pd.Timestamp("2024-01-01") + pd.Timedelta(days=i))
             
        # Create data: Run every Mon, Wed, Fri
        rows = []
        for d in dates:
             if d.dayofweek in [0, 2, 4]:
                 rows.append({'date': d, 'moving_time_min': 60, 'distance_km': 10})
        
        df = pd.DataFrame(rows)
        res = self.insights.calculate_consistency_score(df)
        
        # Consistency factor should be high (near 1.0)
        # Score should be decent
        self.assertGreater(res["score"], 50)
        self.assertAlmostEqual(res["consistency_factor"], 1.0, places=1)

    def test_calculate_consistency_no_data(self):
        res = self.insights.calculate_consistency_score(pd.DataFrame())
        self.assertEqual(res["score"], 0.0)

if __name__ == '__main__':
    unittest.main()
