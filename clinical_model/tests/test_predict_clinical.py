import sys
import os
import unittest
import numpy as np

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))

from predict_clinical import predict_clinical, _load_clinical_models

class TestPredictClinical(unittest.TestCase):

    def setUp(self):
        self.healthy_patient = {
            "Age": 45,
            "Gender": 1,
            "Height": 175.0,
            "Weight": 70.0,
            "BMI": 22.86,
            "Waist_Circumference": 80.0,
            "Systolic_BP": 120.0,
            "Diastolic_BP": 80.0,
            "Fasting_Blood_Glucose": 90.0,
            "HbA1c": 5.2,
            "Triglycerides": 120.0,
            "HDL": 55.0,
            "LDL": 100.0,
            "ALT": 20.0,
            "AST": 22.0,
            "Family_History_Diabetes": 0,
            "Family_History_Hypertension": 0,
            "Family_History_CVD": 0
        }

        self.diabetic_patient = self.healthy_patient.copy()
        self.diabetic_patient.update({
            "Fasting_Blood_Glucose": 210.0,
            "HbA1c": 9.5,
            "Family_History_Diabetes": 1
        })

        # Boundary patient P18636 where raw predictions for BOTH Type2_Diabetes and Prediabetes are >= 0.5
        self.suppression_boundary_patient = {
            'Age': 56, 'Gender': 1, 'Height': 174.6, 'Weight': 57.2, 'BMI': 18.75,
            'Waist_Circumference': 63.0, 'Systolic_BP': 129.7, 'Diastolic_BP': 81.0,
            'Fasting_Blood_Glucose': 126.1, 'HbA1c': 6.35, 'Triglycerides': 105.1,
            'HDL': 52.1, 'LDL': 126.7, 'ALT': 43.3, 'AST': 39.2,
            'Family_History_Diabetes': 0, 'Family_History_Hypertension': 0, 'Family_History_CVD': 0
        }

    def test_healthy_patient(self):
        res = predict_clinical(self.healthy_patient)
        self.assertIn("probabilities", res)
        self.assertIn("predictions", res)
        self.assertEqual(res["threshold_used"], 0.5)
        self.assertIsInstance(res["suppressed_labels"], list)

        # Expected low probability for Type2_Diabetes on healthy patient
        self.assertLess(res["probabilities"]["Type2_Diabetes"], 0.5)
        self.assertEqual(res["predictions"]["Type2_Diabetes"], 0)

    def test_diabetic_patient_and_suppression(self):
        # 1. Severe diabetic patient
        res = predict_clinical(self.diabetic_patient)
        self.assertGreater(res["probabilities"]["Type2_Diabetes"], 0.8)
        self.assertEqual(res["predictions"]["Type2_Diabetes"], 1)
        self.assertEqual(res["predictions"]["Prediabetes"], 0)

        # 2. Boundary diabetic patient where both raw predictions >= 0.5
        res_supp = predict_clinical(self.suppression_boundary_patient)
        self.assertGreaterEqual(res_supp["probabilities"]["Type2_Diabetes"], 0.5)
        self.assertGreaterEqual(res_supp["probabilities"]["Prediabetes"], 0.5)

        # Confirm suppression rule applied: prediction for Prediabetes forced to 0
        self.assertEqual(res_supp["predictions"]["Type2_Diabetes"], 1)
        self.assertEqual(res_supp["predictions"]["Prediabetes"], 0)
        self.assertIn("Prediabetes", res_supp["suppressed_labels"])

        # Confirm raw probability for Prediabetes is preserved untouched
        self.assertGreaterEqual(res_supp["probabilities"]["Prediabetes"], 0.5)

    def test_missing_field_rejection(self):
        invalid = self.healthy_patient.copy()
        del invalid["HbA1c"]
        with self.assertRaises(ValueError) as ctx:
            predict_clinical(invalid)
        self.assertIn("Missing required clinical feature", str(ctx.exception))

    def test_extra_field_rejection(self):
        invalid = self.healthy_patient.copy()
        invalid["Extra_Column"] = 123
        with self.assertRaises(ValueError) as ctx:
            predict_clinical(invalid)
        self.assertIn("Unexpected extra feature", str(ctx.exception))

    def test_nan_field_rejection(self):
        invalid = self.healthy_patient.copy()
        invalid["BMI"] = float("nan")
        with self.assertRaises(ValueError) as ctx:
            predict_clinical(invalid)
        self.assertIn("cannot be None or NaN", str(ctx.exception))

    def test_out_of_range_field_rejection(self):
        invalid_age = self.healthy_patient.copy()
        invalid_age["Age"] = 800
        with self.assertRaises(ValueError) as ctx:
            predict_clinical(invalid_age)
        self.assertIn("outside valid physiological range", str(ctx.exception))

        invalid_bmi = self.healthy_patient.copy()
        invalid_bmi["BMI"] = 150.0
        with self.assertRaises(ValueError) as ctx:
            predict_clinical(invalid_bmi)
        self.assertIn("outside valid physiological range", str(ctx.exception))

    def test_five_independent_models(self):
        models, metadata = _load_clinical_models()
        self.assertEqual(len(models), 5)
        self.assertEqual(len(metadata), 5)
        for label in ["Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk", "Metabolic_Syndrome", "NAFLD"]:
            self.assertIn(label, models)
            self.assertEqual(metadata[label]["model_type"], "xgboost")

if __name__ == "__main__":
    unittest.main()
