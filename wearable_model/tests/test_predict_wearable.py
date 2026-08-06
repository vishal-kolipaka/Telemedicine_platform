import sys
import os
import unittest
import numpy as np

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from predict_wearable import predict_wearable, _load_wearable_models

class TestPredictWearable(unittest.TestCase):

    def setUp(self):
        self.healthy_patient = {
            "Average_Daily_Steps": 10000.0,
            "Active_Minutes": 45.0,
            "Sedentary_Time_Minutes": 480.0,
            "Resting_Heart_Rate": 65.0,
            "Heart_Rate_Variability_RMSSD": 55.0,
            "Sleep_Duration_Hours": 7.5,
            "Sleep_Efficiency_Score": 88.0,
            "Autonomic_Stress_Score": 25.0,
            "Activity_Energy_Expenditure": 450.0,
            "Exercise_Frequency_Days": 4.0,
            "CGM_Average_Glucose": 95.0,
            "CGM_Glucose_CV": 18.0,
            "CGM_Time_In_Range": 95.0,
            "CGM_Time_Above_Range": 3.0,
            "CGM_Time_Below_Range": 2.0
        }

        self.cgm_diabetic_patient = self.healthy_patient.copy()
        self.cgm_diabetic_patient.update({
            "CGM_Average_Glucose": 210.0,
            "CGM_Glucose_CV": 42.0,
            "CGM_Time_In_Range": 35.0,
            "CGM_Time_Above_Range": 62.0,
            "CGM_Time_Below_Range": 3.0
        })

        self.sedentary_patient = self.healthy_patient.copy()
        self.sedentary_patient.update({
            "Sedentary_Time_Minutes": 1100.0,
            "Active_Minutes": 10.0,
            "Average_Daily_Steps": 2500.0,
            "Autonomic_Stress_Score": 75.0,
            "Resting_Heart_Rate": 82.0
        })

        # Min and Max plausible edge patients
        self.min_plausible_patient = {
            "Average_Daily_Steps": 0.0, "Active_Minutes": 0.0, "Sedentary_Time_Minutes": 0.0,
            "Resting_Heart_Rate": 30.0, "Heart_Rate_Variability_RMSSD": 0.0, "Sleep_Duration_Hours": 0.0,
            "Sleep_Efficiency_Score": 0.0, "Autonomic_Stress_Score": 0.0, "Activity_Energy_Expenditure": 0.0,
            "Exercise_Frequency_Days": 0.0, "CGM_Average_Glucose": 40.0, "CGM_Glucose_CV": 0.0,
            "CGM_Time_In_Range": 0.0, "CGM_Time_Above_Range": 0.0, "CGM_Time_Below_Range": 0.0
        }

        self.max_plausible_patient = {
            "Average_Daily_Steps": 50000.0, "Active_Minutes": 1000.0, "Sedentary_Time_Minutes": 1440.0,
            "Resting_Heart_Rate": 200.0, "Heart_Rate_Variability_RMSSD": 250.0, "Sleep_Duration_Hours": 24.0,
            "Sleep_Efficiency_Score": 100.0, "Autonomic_Stress_Score": 100.0, "Activity_Energy_Expenditure": 8000.0,
            "Exercise_Frequency_Days": 7.0, "CGM_Average_Glucose": 450.0, "CGM_Glucose_CV": 120.0,
            "CGM_Time_In_Range": 100.0, "CGM_Time_Above_Range": 100.0, "CGM_Time_Below_Range": 100.0
        }

    def test_healthy_patient(self):
        res = predict_wearable(self.healthy_patient)
        self.assertIn("probabilities", res)
        self.assertIn("predictions", res)
        self.assertEqual(res["threshold_used"], 0.5)

        # Healthy patient low T2D risk
        self.assertLess(res["probabilities"]["Type2_Diabetes"], 0.5)
        self.assertEqual(res["predictions"]["Type2_Diabetes"], 0)

    def test_high_cgm_diabetic_patient(self):
        res = predict_wearable(self.cgm_diabetic_patient)

        # High CGM patient high T2D risk
        self.assertGreater(res["probabilities"]["Type2_Diabetes"], 0.8)
        self.assertEqual(res["predictions"]["Type2_Diabetes"], 1)

        # Prediabetes prediction forced to 0 via suppression rule
        self.assertEqual(res["predictions"]["Prediabetes"], 0)

        # Raw probability for Prediabetes untouched
        self.assertGreater(res["probabilities"]["Prediabetes"], 0.0)

    def test_sedentary_adiposity_risk(self):
        res = predict_wearable(self.sedentary_patient)
        self.assertIn("High_Adiposity_Risk", res["probabilities"])
        self.assertGreater(res["probabilities"]["High_Adiposity_Risk"], 0.3)

    def test_plausible_min_max_finite_outputs(self):
        res_min = predict_wearable(self.min_plausible_patient)
        res_max = predict_wearable(self.max_plausible_patient)

        for label in ["Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk", "Metabolic_Syndrome", "NAFLD"]:
            self.assertFalse(np.isnan(res_min["probabilities"][label]))
            self.assertFalse(np.isnan(res_max["probabilities"][label]))
            self.assertTrue(np.isfinite(res_min["probabilities"][label]))
            self.assertTrue(np.isfinite(res_max["probabilities"][label]))

    def test_missing_field_rejection(self):
        invalid = self.healthy_patient.copy()
        del invalid["CGM_Average_Glucose"]
        with self.assertRaises(ValueError) as ctx:
            predict_wearable(invalid)
        self.assertIn("Missing required wearable feature", str(ctx.exception))

    def test_extra_field_rejection(self):
        invalid = self.healthy_patient.copy()
        invalid["Extra_Sensor_Feature"] = 99.0
        with self.assertRaises(ValueError) as ctx:
            predict_wearable(invalid)
        self.assertIn("Unexpected extra feature", str(ctx.exception))

    def test_nan_field_rejection(self):
        invalid = self.healthy_patient.copy()
        invalid["CGM_Time_In_Range"] = float("nan")
        with self.assertRaises(ValueError) as ctx:
            predict_wearable(invalid)
        self.assertIn("cannot be None or NaN", str(ctx.exception))

    def test_impossible_value_rejections(self):
        # Negative sedentary time
        invalid_sed = self.healthy_patient.copy()
        invalid_sed["Sedentary_Time_Minutes"] = -50.0
        with self.assertRaises(ValueError) as ctx:
            predict_wearable(invalid_sed)
        self.assertIn("outside valid plausible range", str(ctx.exception))

        # Extreme glucose = 900
        invalid_gluc = self.healthy_patient.copy()
        invalid_gluc["CGM_Average_Glucose"] = 900.0
        with self.assertRaises(ValueError) as ctx:
            predict_wearable(invalid_gluc)
        self.assertIn("outside valid plausible range", str(ctx.exception))

        # Heart rate = 5
        invalid_hr = self.healthy_patient.copy()
        invalid_hr["Resting_Heart_Rate"] = 5.0
        with self.assertRaises(ValueError) as ctx:
            predict_wearable(invalid_hr)
        self.assertIn("outside valid plausible range", str(ctx.exception))

    def test_five_independent_models(self):
        models, metadata = _load_wearable_models()
        self.assertEqual(len(models), 5)
        self.assertEqual(len(metadata), 5)
        for label in ["Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk", "Metabolic_Syndrome", "NAFLD"]:
            self.assertIn(label, models)
            self.assertEqual(metadata[label]["model_version"], "wearable_v3")
            self.assertEqual(metadata[label]["feature_count"], 15)

if __name__ == "__main__":
    unittest.main()
