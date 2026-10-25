import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
import numpy as np
from threadpoolctl import threadpool_limits
from train_hist_stage0 import estimator


class HistTests(unittest.TestCase):
    def test_fixed_settings(self):
        m=estimator()
        self.assertFalse(m.early_stopping)
        self.assertEqual(m.max_iter,100)
        self.assertEqual(m.random_state,42)

    def test_deterministic_and_finite(self):
        x=np.arange(240,dtype=float).reshape(120,2)
        y=np.sin(x[:,0]/50)
        with threadpool_limits(limits=1):
            a=estimator().fit(x,y)
            b=estimator().fit(x,y)
            np.testing.assert_array_equal(a.predict(x),b.predict(x))
        self.assertEqual(a.n_iter_,100)
        self.assertFalse(a.do_early_stopping_)
