import unittest
import pandas as pd
from src.dashboard_logic import add_scores,best_window,category


class DashboardLogicTests(unittest.TestCase):
    def test_categories(self):
        self.assertEqual(category(60)[0],'Grün')
        self.assertEqual(category(40)[0],'Gelb')
        self.assertEqual(category(39.9)[0],'Rot')

    def test_best_window(self):
        day=pd.DataFrame({'time_utc':pd.date_range('2025-01-01',periods=6,freq='h',tz='UTC'),
                          'predicted_co2':[9,8,2,1,3,8],
                          'predicted_renewable':[20,30,70,80,75,20]})
        scored=add_scores(day)
        result=best_window(scored,2)
        self.assertEqual(result['start'],day.time_utc.iloc[2])
        self.assertAlmostEqual(result['average_co2'],1.5)


if __name__=='__main__':unittest.main()
