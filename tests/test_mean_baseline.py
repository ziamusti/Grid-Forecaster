import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from train_mean_baseline import key, metrics, fit
from datetime import datetime, timedelta, timezone


class MeanBaselineTests(unittest.TestCase):
    def test_metrics(self):
        m = metrics([1, 3], [2, 2])
        self.assertEqual(m, dict(n=2, mae=1, rmse=1, r2=0))

    def test_constant_r2(self):
        self.assertIsNone(metrics([2, 2], [1, 1])['r2'])

    def test_dst(self):
        self.assertEqual(key('2024-10-27T00:00:00Z'), key('2024-10-27T01:00:00Z'))
        self.assertEqual(key('2024-03-31T01:00:00Z'), (6, 3))

    def test_training_means_and_exclusion(self):
        rows = []
        for i in range(336):
            t = datetime(2023, 1, 2, tzinfo=timezone.utc)+timedelta(hours=i)
            rows.append(dict(target_time_utc=t.isoformat(), target_co2_gco2eq_kwh=str(2 if i<168 else 4), eligible_co2_nonestimated='1'))
        rows.append(dict(rows[0], target_co2_gco2eq_kwh='99999', eligible_co2_nonestimated='0'))
        model = fit(rows, 'target_co2_gco2eq_kwh')
        self.assertEqual(len(model), 168)
        self.assertTrue(all(v == (3, 2) for v in model.values()))
        rows[0]['target_co2_gco2eq_kwh'] = '999'
        self.assertTrue(all(v == (3, 2) for v in model.values()))

    def test_missing_group_rejected(self):
        with self.assertRaises(ValueError):
            fit([], 'target_co2_gco2eq_kwh')
