import importlib.util
import unittest
from datetime import datetime, timedelta
from pathlib import Path

spec = importlib.util.spec_from_file_location('sunshine', Path(__file__).resolve().parents[1] / 'scripts/add_sunshine_stage0.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class SunshineTests(unittest.TestCase):
    def data(self):
        return dict(utc_offset_seconds=0, hourly_units={'sunshine_duration': 's'},
                    hourly={'time': [(datetime(2015, 1, 1)+timedelta(hours=i)).isoformat(timespec='minutes') for i in range(24)],
                            'sunshine_duration': [0.0]*24})

    def test_zero_is_valid(self):
        self.assertEqual(len(m.validate(self.data(), '2015-01-01', '2015-01-01')), 24)

    def test_missing_rejected(self):
        d = self.data(); d['hourly']['sunshine_duration'][5] = None
        with self.assertRaises(AssertionError): m.validate(d, '2015-01-01', '2015-01-01')

    def test_out_of_range_rejected(self):
        d = self.data(); d['hourly']['sunshine_duration'][5] = 3601
        with self.assertRaises(AssertionError): m.validate(d, '2015-01-01', '2015-01-01')

    def test_duplicate_timestamp_rejected(self):
        d = self.data(); d['hourly']['time'][5] = d['hourly']['time'][4]
        with self.assertRaises(AssertionError): m.validate(d, '2015-01-01', '2015-01-01')

    def test_wrong_units_rejected(self):
        d = self.data(); d['hourly_units']['sunshine_duration'] = 'h'
        with self.assertRaises(AssertionError): m.validate(d, '2015-01-01', '2015-01-01')
