import importlib.util
import unittest
from collections import Counter
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

spec = importlib.util.spec_from_file_location('prepare_stage0', Path(__file__).resolve().parents[1] / 'scripts/prepare_stage0.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


class PreparationTests(unittest.TestCase):
    def test_dst_fall_two_distinct_hours(self):
        seen = Counter()
        first = p.local_to_utc('25.10.2015 02:00', seen)
        second = p.local_to_utc('25.10.2015 02:00', seen)
        self.assertEqual(second - first, timedelta(hours=1))

    def test_dst_nonexistent_rejected(self):
        with self.assertRaises(ValueError):
            p.local_to_utc('29.03.2015 02:00', Counter())

    def test_non_dst_duplicate_rejected(self):
        seen = Counter()
        p.local_to_utc('01.01.2015 00:00', seen)
        with self.assertRaises(ValueError):
            p.local_to_utc('01.01.2015 00:00', seen)

    def test_missing_is_not_zero(self):
        self.assertIsNone(p.number('-', german=True))
        self.assertEqual(p.number('1.234,56', german=True), 1234.56)

    def test_pumped_storage_only_denominator(self):
        row = {k: 0.0 for k in p.TECH.values()}
        row.update(solar=40, gas=40, pumped_storage=20)
        self.assertEqual(p.renewables(row), 40)
        row['other_renewables'] = None
        self.assertIsNone(p.renewables(row))

    def test_capacity_does_not_see_future_month(self):
        t = datetime(2025, 3, 2, 12, tzinfo=timezone.utc)
        self.assertEqual(p.capacity_reference(t), date(2025, 2, 1))
        for h in range(1, 73):
            self.assertLessEqual(p.capacity_reference(t), (t - timedelta(hours=h)).astimezone(p.BERLIN).date())

    def test_folds_keep_holdout_out(self):
        s = p.fold_spec()
        for fold in s['development_folds']:
            self.assertEqual(len(fold['train_years']), 3)
            self.assertLess(max(fold['train_years']), fold['validation_year'])
            self.assertLess(fold['validation_year'], s['final_test_year'])
        self.assertNotIn(2025, s['final_train_years'])

    def test_holiday_exception(self):
        self.assertIn(date(2017, 10, 31), p.holidays(2017))
        self.assertNotIn(date(2018, 10, 31), p.holidays(2018))

    def test_daylight_seasons(self):
        self.assertGreater(p.daylight(date(2024, 6, 21)), p.daylight(date(2024, 12, 21)))


if __name__ == '__main__':
    unittest.main()
