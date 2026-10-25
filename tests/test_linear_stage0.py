import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import numpy as np
from train_linear_stage0 import pipeline, finite


class LinearTests(unittest.TestCase):
    def test_preprocessing_training_only(self):
        features=['signal','hour_local','weekday','month']
        x=np.array([[1,0,0,1],[2,1,1,2],[3,2,2,3],[4,3,3,4]],dtype=float)
        p=pipeline(features).fit(x,np.array([1,2,3,4]))
        scaler=p['preprocess'].named_transformers_['numeric']
        before=scaler.mean_.copy()
        prediction=p.predict([[1000,23,6,12]])
        np.testing.assert_array_equal(before,scaler.mean_)
        self.assertEqual(before[0],2.5)
        self.assertTrue(np.isfinite(prediction).all())
        self.assertEqual(len(p['preprocess'].get_feature_names_out(features)),41)

    def test_reference_categories_zero(self):
        p=pipeline(['signal','hour_local','weekday','month'])
        p.fit([[1,0,0,1],[2,1,1,2]],[1,2])
        self.assertTrue((p['preprocess'].transform([[1,0,0,1]])[0,1:]==0).all())

    def test_invalid_lag(self):
        self.assertFalse(finite(''))
        self.assertFalse(finite('nan'))
        self.assertTrue(finite('0'))
