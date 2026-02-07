import unittest
import numpy as np
from engine.metrics import MetricsCalculator, RunMetrics

class TestMetricsCalculator(unittest.TestCase):

    def test_calculate_decoupling_perfect_steady(self):
        # 200 points (enough for >120 check)
        # Power steady 200W, HR steady 140bpm
        power = [200.0] * 200
        hr = [140.0] * 200
        # cost1 = 140/200 = 0.7, cost2 = 0.7 => drift 0
        drift = MetricsCalculator.calculate_decoupling(power, hr)
        self.assertAlmostEqual(drift, 0.0)

    def test_calculate_decoupling_with_drift(self):
        # First half: 200W, 140bpm (Cost 0.7)
        # Second half: 200W, 154bpm (Cost 0.77)
        # Drift = (0.77 - 0.7)/0.7 = 0.1 (10%)
        power = [200.0] * 200
        hr = [140.0] * 100 + [154.0] * 100
        
        drift = MetricsCalculator.calculate_decoupling(power, hr)
        self.assertAlmostEqual(drift, 0.1, places=2)

    def test_calculate_decoupling_insufficient_data(self):
        power = [200.0] * 50 # < 120
        hr = [140.0] * 50
        drift = MetricsCalculator.calculate_decoupling(power, hr)
        self.assertEqual(drift, 0.0)

    def test_calculate_zones_coggan(self):
        # FTP 250
        # Limits: 0.55(137.5), 0.75(187.5), 0.90(225), 1.05(262.5), 1.20(300), 1.50(375)
        ftp = 250
        watts = [
            100, # < 137.5 -> Z1
            150, # < 187.5 -> Z2
            200, # < 225   -> Z3
            250, # < 262.5 -> Z4
            280, # < 300   -> Z5
            350, # < 375   -> Z6
            400  # >= 375  -> Z7
        ]
        zones = MetricsCalculator.calculate_zones(watts, ftp)
        
        # Each zone should have 1 hit, total 7. 1/7*100 = 14.3%
        expected = 14.3
        self.assertEqual(len(zones), 7)
        self.assertAlmostEqual(zones["Z1"], expected, places=1)
        self.assertAlmostEqual(zones["Z7"], expected, places=1)

    def test_calculate_hr_zones(self):
        zones_config = {
            "zones": [
                {"min": 0, "max": 100},   # Z1
                {"min": 101, "max": 150}, # Z2
                {"min": 151, "max": -1}   # Z3 (max -1 usually means max)
            ]
        }
        hr_stream = [50, 60, 120, 130, 160, 170]
        # Z1: 50, 60 (2)
        # Z2: 120, 130 (2)
        # Z3: 160, 170 (2)
        # Total 6. Each 33.3%
        
        zones = MetricsCalculator.calculate_hr_zones(hr_stream, zones_config)
        self.assertAlmostEqual(zones["Z1"], 33.3, places=1)
        self.assertAlmostEqual(zones["Z2"], 33.3, places=1)
        self.assertAlmostEqual(zones["Z3"], 33.3, places=1)

    def test_calculate_t_adj(self):
        # Standard conditions: 30yo M, 15°C
        m = RunMetrics(
            avg_power=200, avg_hr=150, distance=10000, moving_time=3600,
            elevation_gain=0, weight=70, hr_max=190, hr_rest=50,
            temp_c=15, humidity=50, age=30, sex="M"
        )
        # F_age(30)=1.0, F_sex(M)=1.0, F_env(15)=1.0 -> Denom=1.0
        t_adj = MetricsCalculator.calculate_t_adj(m)
        self.assertAlmostEqual(t_adj, 3600.0)

        # Hot Older Female
        # Age 60 -> F_age = 1 + 0.15*((30)/30)^2 = 1.15
        # Sex F -> 1.10
        # Temp 25 -> F_env = 1 + 0.01*(10) = 1.10
        # Denom = 1.15 * 1.10 * 1.10 = 1.3915
        m2 = RunMetrics(
            avg_power=200, avg_hr=150, distance=10000, moving_time=3600,
            elevation_gain=0, weight=70, hr_max=190, hr_rest=50,
            temp_c=25, humidity=50, age=60, sex="F"
        )
        t_adj_2 = MetricsCalculator.calculate_t_adj(m2)
        self.assertLess(t_adj_2, 3600.0) # Should be faster/less time adjusted

if __name__ == '__main__':
    unittest.main()
