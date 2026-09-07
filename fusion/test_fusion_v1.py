"""
test_fusion_v1.py — Complete Unit Test Suite for Fusion V1 Implementation

Executes all 11 mandatory unit tests:
  - Test 1: T2D Passthrough
  - Test 2: Prediabetes Passthrough
  - Test 3: Prediabetes Post-Decision Suppression
  - Test 4: High Adiposity Passthrough
  - Test 5: MetSyn Fusion (Clin+Gut -> LR -> Platt -> 0.20 threshold)
  - Test 6: MetSyn Monotonicity
  - Test 7: NAFLD Fusion (Clin+Gut LR)
  - Test 8: NAFLD Monotonicity
  - Test 9: Wearable Exclusion (Mandatory)
  - Test 10: Probability Boundedness & Validity
  - Test 11: Patient_ID Alignment Safety
"""

import os
import unittest
import numpy as np
import pandas as pd
from fusion.predict_fusion import FusionV1Predictor, predict_fusion_v1, sigmoid


class TestFusionV1(unittest.TestCase):
    def setUp(self):
        models_dir = r"c:\Users\HP PC\Desktop\telemedicine platform\fusion_phase2\models\fusion_candidates"
        self.predictor = FusionV1Predictor(models_dir=models_dir)

    def _create_sample_df(self, n=5):
        df = pd.DataFrame({"Patient_ID": [f"P_{i:03d}" for i in range(n)]})
        modalities = ["Clinical", "Gut", "Wearable"]
        diseases = ["Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk", "Metabolic_Syndrome", "NAFLD"]
        
        for mod in modalities:
            for dis in diseases:
                df[f"P_{mod}_{dis}"] = np.random.uniform(0.1, 0.9, size=n)
        return df

    def test_01_t2d_passthrough(self):
        """Test 1 — T2D Passthrough: Changing Gut/Wearable does not change T2D fused prob."""
        df1 = self._create_sample_df(3)
        res1 = self.predictor.predict(master_df=df1)
        
        # Mutate Gut and Wearable
        df2 = df1.copy()
        df2["P_Gut_Type2_Diabetes"] = 0.99
        df2["P_Wearable_Type2_Diabetes"] = 0.01
        res2 = self.predictor.predict(master_df=df2)
        
        np.testing.assert_array_almost_equal(res1["P_Fused_Type2_Diabetes"].values, res2["P_Fused_Type2_Diabetes"].values)
        np.testing.assert_array_equal(res1["P_Fused_Type2_Diabetes"].values, df1["P_Clinical_Type2_Diabetes"].values)

    def test_02_prediabetes_passthrough(self):
        """Test 2 — Prediabetes Passthrough: Raw Prediabetes fused prob equals Clinical Prediabetes prob."""
        df = self._create_sample_df(3)
        res = self.predictor.predict(master_df=df)
        np.testing.assert_array_almost_equal(res["P_Fused_Prediabetes"].values, df["P_Clinical_Prediabetes"].values)

    def test_03_prediabetes_suppression(self):
        """Test 3 — Prediabetes Suppression: When T2D pred = 1, Prediabetes pred = 0, but fused prob remains unchanged."""
        df = self._create_sample_df(2)
        # Force Patient 0 to have T2D=1 and Prediabetes=1
        df.loc[0, "P_Clinical_Type2_Diabetes"] = 0.85
        df.loc[0, "P_Clinical_Prediabetes"] = 0.75

        res = self.predictor.predict(master_df=df)
        
        self.assertEqual(res.loc[0, "Pred_Type2_Diabetes"], 1)
        self.assertEqual(res.loc[0, "Pred_Prediabetes_Raw"], 1)
        self.assertEqual(res.loc[0, "Pred_Prediabetes"], 0)  # Suppressed!
        self.assertEqual(res.loc[0, "Prediabetes_Suppressed"], 1)
        self.assertAlmostEqual(res.loc[0, "P_Fused_Prediabetes"], 0.75)  # Raw probability un-mutated!

    def test_04_high_adiposity_passthrough(self):
        """Test 4 — High Adiposity Passthrough: Changing Gut/Wearable does not change HAR fused prob."""
        df1 = self._create_sample_df(3)
        res1 = self.predictor.predict(master_df=df1)
        
        df2 = df1.copy()
        df2["P_Gut_High_Adiposity_Risk"] = 0.05
        df2["P_Wearable_High_Adiposity_Risk"] = 0.95
        res2 = self.predictor.predict(master_df=df2)
        
        np.testing.assert_array_almost_equal(res1["P_Fused_High_Adiposity_Risk"].values, res2["P_Fused_High_Adiposity_Risk"].values)

    def test_05_metsyn_fusion_math(self):
        """Test 5 — MetSyn Fusion: Verify exact Clin+Gut -> LR -> Platt -> 0.20 threshold."""
        df = self._create_sample_df(1)
        p_c = 0.60
        p_g = 0.70
        df.loc[0, "P_Clinical_Metabolic_Syndrome"] = p_c
        df.loc[0, "P_Gut_Metabolic_Syndrome"] = p_g
        
        res = self.predictor.predict(master_df=df)
        
        # Expected Math
        logit_raw = -4.3697124012 + 2.5798532189 * p_c + 1.9638807682 * p_g
        p_raw = sigmoid(logit_raw)
        logit_platt = 1.5006 + 1.8243 * logit_raw
        p_cal = sigmoid(logit_platt)
        pred = int(p_cal >= 0.20)
        
        self.assertAlmostEqual(res.loc[0, "P_Raw_LR_Metabolic_Syndrome"], p_raw, places=4)
        self.assertAlmostEqual(res.loc[0, "P_Fused_Metabolic_Syndrome"], p_cal, places=4)
        self.assertEqual(res.loc[0, "Pred_Metabolic_Syndrome"], pred)

    def test_06_metsyn_monotonicity(self):
        """Test 6 — MetSyn Monotonicity: Increasing Clin or Gut never decreases fused MetSyn prob."""
        df1 = self._create_sample_df(1)
        df1.loc[0, "P_Clinical_Metabolic_Syndrome"] = 0.40
        df1.loc[0, "P_Gut_Metabolic_Syndrome"] = 0.40
        res1 = self.predictor.predict(master_df=df1)
        
        df2 = df1.copy()
        df2.loc[0, "P_Clinical_Metabolic_Syndrome"] = 0.70  # Increased Clinical
        res2 = self.predictor.predict(master_df=df2)
        
        df3 = df1.copy()
        df3.loc[0, "P_Gut_Metabolic_Syndrome"] = 0.70  # Increased Gut
        res3 = self.predictor.predict(master_df=df3)
        
        self.assertGreater(res2.loc[0, "P_Fused_Metabolic_Syndrome"], res1.loc[0, "P_Fused_Metabolic_Syndrome"])
        self.assertGreater(res3.loc[0, "P_Fused_Metabolic_Syndrome"], res1.loc[0, "P_Fused_Metabolic_Syndrome"])

    def test_07_nafld_fusion_math(self):
        """Test 7 — NAFLD Fusion: Verify exact Clin+Gut LR equation."""
        df = self._create_sample_df(1)
        p_c = 0.55
        p_g = 0.65
        df.loc[0, "P_Clinical_NAFLD"] = p_c
        df.loc[0, "P_Gut_NAFLD"] = p_g
        
        res = self.predictor.predict(master_df=df)
        
        logit = -4.7670735247 + 3.7924128668 * p_c + 2.8339984355 * p_g
        p_fused = sigmoid(logit)
        pred = int(p_fused >= 0.50)
        
        self.assertAlmostEqual(res.loc[0, "P_Fused_NAFLD"], p_fused, places=4)
        self.assertEqual(res.loc[0, "Pred_NAFLD"], pred)

    def test_08_nafld_monotonicity(self):
        """Test 8 — NAFLD Monotonicity: Increasing Clin or Gut never decreases fused NAFLD prob."""
        df1 = self._create_sample_df(1)
        df1.loc[0, "P_Clinical_NAFLD"] = 0.30
        df1.loc[0, "P_Gut_NAFLD"] = 0.30
        res1 = self.predictor.predict(master_df=df1)
        
        df2 = df1.copy()
        df2.loc[0, "P_Clinical_NAFLD"] = 0.80
        res2 = self.predictor.predict(master_df=df2)
        
        self.assertGreater(res2.loc[0, "P_Fused_NAFLD"], res1.loc[0, "P_Fused_NAFLD"])

    def test_09_wearable_exclusion_mandatory(self):
        """Test 9 — Wearable Exclusion: Changing Wearable prob MUST NOT change any fused disease prob."""
        df1 = self._create_sample_df(5)
        res1 = self.predictor.predict(master_df=df1)
        
        # Mutate all Wearable probabilities completely
        df2 = df1.copy()
        for dis in ["Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk", "Metabolic_Syndrome", "NAFLD"]:
            df2[f"P_Wearable_{dis}"] = np.random.uniform(0.0, 1.0, size=5)
            
        res2 = self.predictor.predict(master_df=df2)
        
        for dis in ["Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk", "Metabolic_Syndrome", "NAFLD"]:
            np.testing.assert_array_almost_equal(
                res1[f"P_Fused_{dis}"].values,
                res2[f"P_Fused_{dis}"].values,
                err_msg=f"Wearable probability mutation leaked into fused head {dis}!"
            )

    def test_10_probability_validity(self):
        """Test 10 — Probability Validity: All fused probabilities must sit within [0, 1]."""
        df = self._create_sample_df(20)
        res = self.predictor.predict(master_df=df)
        
        fused_cols = [f"P_Fused_{d}" for d in ["Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk", "Metabolic_Syndrome", "NAFLD"]]
        for col in fused_cols:
            vals = res[col].values
            self.assertTrue(np.all(vals >= 0.0), f"Negative probability found in {col}")
            self.assertTrue(np.all(vals <= 1.0), f"Probability > 1 found in {col}")

    def test_11_patient_alignment_safety(self):
        """Test 11 — Patient Alignment Safety: Uses Patient_ID matching, not row position."""
        clin_df = pd.DataFrame({"Patient_ID": ["P_001", "P_002"], "P_Clinical_Metabolic_Syndrome": [0.8, 0.2]})
        gut_df = pd.DataFrame({"Patient_ID": ["P_002", "P_001"], "P_Gut_Metabolic_Syndrome": [0.1, 0.9]})  # Reversed order!
        
        res = self.predictor.predict(clinical_df=clin_df, gut_df=gut_df)
        
        # P_001 should match Clin=0.8, Gut=0.9
        p1_res = res[res["Patient_ID"] == "P_001"].iloc[0]
        self.assertEqual(p1_res["P_Clinical_Metabolic_Syndrome"], 0.8)
        self.assertEqual(p1_res["P_Gut_Metabolic_Syndrome"], 0.9)


if __name__ == "__main__":
    unittest.main()
