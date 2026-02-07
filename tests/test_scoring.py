import unittest
import numpy as np
from config import Config
from engine.scoring import ScoringSystem
from engine.metrics import RunMetrics

class TestScoringSystem(unittest.TestCase):
    def setUp(self):
        self.scoring = ScoringSystem()

    def test_compute_score_v6_pure_perfect(self):
        # Perfect Run:
        # Pwr/Nominal = 1.0 -> W_eff = ln(2) = 0.693
        # HRR/Target = 1.0 -> HR_eff = ln(2) = 0.693
        # W_eff / HR_eff = 1.0
        # WCF = 1.0 (20C, 60%)
        # Stability = 1.0 (Decoupling 0)
        # Raw = 1.0
        # Score = 100 * (1 - exp(-1.8 * 1.0)) = 100 * (1 - 0.165) = 83.5
        
        m = RunMetrics(200, 140, 10000, 3600, 0, 70, 190, 50, 20, 60)
        nominal_pwr = 200/70 # 2.85
        
        score, details = self.scoring.compute_score_v6_pure(m, nominal_pwr, 1.0)
        
        self.assertTrue(80 < score < 85)
        self.assertEqual(details['wcf'], 1.0)
        self.assertEqual(details['stability'], 1.0)

    def test_compute_score_v6_pure_elite(self):
        # Elite Run (More Power than nominal, less HR than target)
        m = RunMetrics(300, 140, 10000, 3600, 0, 70, 190, 50, 20, 60)
        nominal_pwr = 200/70 
        # Pwr ratio > 1 -> Higher W_eff
        # HR ratio = 1 -> Same HR_eff
        # Raw > 1
        
        score, details = self.scoring.compute_score_v6_pure(m, nominal_pwr, 1.0)
        self.assertGreater(score, 85)

    def test_get_rank(self):
        rank, color = self.scoring.get_rank(95)
        self.assertIn("ELITE", rank)
        
        rank, color = self.scoring.get_rank(30)
        self.assertIn("ROOKIE", rank)

    def test_run_quality(self):
        q = self.scoring.run_quality(95)
        self.assertIn("Legendary", q["label"])
        self.assertEqual(q["color"], Config.Theme.SCORE_LEGENDARY)
        
        q = self.scoring.run_quality(5)
        self.assertIn("Wasted", q["label"])

if __name__ == '__main__':
    unittest.main()
