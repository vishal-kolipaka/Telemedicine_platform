import json
import math
import numpy as np
from src.fusion_v2.pathway_registry import PathwayRegistry
from src.fusion_v2.meta_stacker import MetaStacker
from src.fusion_v2.fusion import fuse_predictions

def sigmoid(x):
    return 1.0 / (1.0 + math.exp(-x))

print("="*80)
print("AUDIT TASK 3: MANUAL END-TO-END MATHEMATICAL RECOMPUTATIONS")
print("="*80)

# CASE 1: Pathway C (5D input), Disease: Type2_Diabetes
# Level-0 inputs from 01_Clinical_Only.pdf:
# Clinical T2D prob = 0.934
print("\n--- CASE 1: Pathway 'C' (5D Level-0 space) -> Type 2 Diabetes ---")
p_clin = 0.9340
print(f"Step A: Level-0 Input: Clinical T2D prob = {p_clin:.4f}")
print(f"Step B: Fusion vector: z = [{p_clin:.4f}]")

# Model parameters
m_c = PathwayRegistry.get_model_entry("C", "Type2_Diabetes")
coef_c = m_c["coefficients"]["clinical"]
b_c = m_c["intercept"]
A_c = m_c["platt_scaling"]["A"]
B_c = m_c["platt_scaling"]["B"]
thresh_c = m_c["threshold"]

raw_logit_c = math.log(p_clin / (1.0 - p_clin))
print(f"Step C: Raw logit: log({p_clin:.4f} / (1 - {p_clin:.4f})) = {raw_logit_c:.6f}")
p_raw_c = sigmoid(raw_logit_c)
print(f"Step D: Raw sigmoid: sigmoid({raw_logit_c:.6f}) = {p_raw_c:.6f}")

cal_logit_c = A_c * raw_logit_c + B_c
p_cal_c = sigmoid(cal_logit_c)
print(f"Step E: Platt calibration: sigmoid({A_c:.6f} * {raw_logit_c:.6f} + {B_c:.6f}) = sigmoid({cal_logit_c:.6f}) = {p_cal_c:.6f} ({p_cal_c*100:.2f}%)")

decision_c = p_cal_c >= thresh_c
print(f"Step F: Threshold: {p_cal_c:.4f} >= {thresh_c:.2f} -> Decision = {decision_c}")

# Compare with MetaStacker
pred_stacker_c = MetaStacker.predict_disease("C", "Type2_Diabetes", {"clinical": p_clin})
print(f"Pipeline output: risk_score = {pred_stacker_c['risk_score']}, decision = {pred_stacker_c['decision']}, threshold = {pred_stacker_c['threshold_used']}")
print(f"Match difference: {abs(p_cal_c - pred_stacker_c['risk_score']):.8f}")


# CASE 2: Pathway C_G (10D Level-0 space), Disease: Metabolic_Syndrome
# Level-0 inputs from 04_Clinical_Gut.pdf:
# Clinical MetSyn = 0.7570, Gut MetSyn = 0.8910
print("\n--- CASE 2: Pathway 'C_G' (10D Level-0 space) -> Metabolic Syndrome ---")
p_clin_ms = 0.7570
p_gut_ms = 0.8910
print(f"Step A: Level-0 Inputs: Clinical MetSyn = {p_clin_ms:.4f}, Gut MetSyn = {p_gut_ms:.4f}")
print(f"Step B: Fusion vector: z = [P_c={p_clin_ms:.4f}, P_g={p_gut_ms:.4f}]")

m_cg = PathwayRegistry.get_model_entry("C_G", "Metabolic_Syndrome")
w_clin = m_cg["coefficients"]["clinical"]
w_gut = m_cg["coefficients"]["gut"]
b_cg = m_cg["intercept"]
A_cg = m_cg["platt_scaling"]["A"]
B_cg = m_cg["platt_scaling"]["B"]
thresh_cg = m_cg["threshold"]

raw_logit_cg = b_cg + w_clin * p_clin_ms + w_gut * p_gut_ms
print(f"Step C: Multi-modality Linear Combination:")
print(f"        w_clin * P_c = {w_clin:.6f} * {p_clin_ms:.4f} = {w_clin * p_clin_ms:.6f}")
print(f"        w_gut * P_g  = {w_gut:.6f} * {p_gut_ms:.4f}  = {w_gut * p_gut_ms:.6f}")
print(f"        intercept    = {b_cg:.6f}")
print(f"        raw_logit    = {raw_logit_cg:.6f}")

p_raw_cg = sigmoid(raw_logit_cg)
print(f"Step D: Raw sigmoid: sigmoid({raw_logit_cg:.6f}) = {p_raw_cg:.6f}")

cal_logit_cg = A_cg * raw_logit_cg + B_cg
p_cal_cg = sigmoid(cal_logit_cg)
print(f"Step E: Platt calibration: sigmoid({A_cg:.6f} * {raw_logit_cg:.6f} + {B_cg:.6f}) = sigmoid({cal_logit_cg:.6f}) = {p_cal_cg:.6f} ({p_cal_cg*100:.2f}%)")

decision_cg = p_cal_cg >= thresh_cg
print(f"Step F: Threshold: {p_cal_cg:.4f} >= {thresh_cg:.2f} -> Decision = {decision_cg}")

# Compare with MetaStacker
pred_stacker_cg = MetaStacker.predict_disease("C_G", "Metabolic_Syndrome", {"clinical": p_clin_ms, "gut": p_gut_ms})
print(f"Pipeline output: risk_score = {pred_stacker_cg['risk_score']}, decision = {pred_stacker_cg['decision']}, threshold = {pred_stacker_cg['threshold_used']}")
print(f"Match difference: {abs(p_cal_cg - pred_stacker_cg['risk_score']):.8f}")


# CASE 3: Pathway C_W_G (15D Level-0 space), Disease: NAFLD
# Level-0 inputs from 07_Clinical_Gut_Wearable_Full.pdf:
# Clinical NAFLD = 0.8980, Wearable NAFLD = 0.6060, Gut NAFLD = 0.9540
print("\n--- CASE 3: Pathway 'C_W_G' (15D Level-0 space) -> NAFLD ---")
p_clin_nf = 0.8980
p_wear_nf = 0.6060
p_gut_nf = 0.9540
print(f"Step A: Level-0 Inputs: Clinical={p_clin_nf:.4f}, Wearable={p_wear_nf:.4f}, Gut={p_gut_nf:.4f}")
print(f"Step B: Fusion vector: z = [P_c={p_clin_nf:.4f}, P_w={p_wear_nf:.4f}, P_g={p_gut_nf:.4f}]")

m_cwg = PathwayRegistry.get_model_entry("C_W_G", "NAFLD")
w_clin_cwg = m_cwg["coefficients"]["clinical"]
w_wear_cwg = m_cwg["coefficients"]["wearable"]
w_gut_cwg = m_cwg["coefficients"]["gut"]
b_cwg = m_cwg["intercept"]
A_cwg = m_cwg["platt_scaling"]["A"]
B_cwg = m_cwg["platt_scaling"]["B"]
thresh_cwg = m_cwg["threshold"]

raw_logit_cwg = b_cwg + w_clin_cwg * p_clin_nf + w_wear_cwg * p_wear_nf + w_gut_cwg * p_gut_nf
print(f"Step C: Multi-modality Linear Combination:")
print(f"        w_clin * P_c = {w_clin_cwg:.6f} * {p_clin_nf:.4f} = {w_clin_cwg * p_clin_nf:.6f}")
print(f"        w_wear * P_w = {w_wear_cwg:.6f} * {p_wear_nf:.4f} = {w_wear_cwg * p_wear_nf:.6f}")
print(f"        w_gut * P_g  = {w_gut_cwg:.6f} * {p_gut_nf:.4f}  = {w_gut_cwg * p_gut_nf:.6f}")
print(f"        intercept    = {b_cwg:.6f}")
print(f"        raw_logit    = {raw_logit_cwg:.6f}")

p_raw_cwg = sigmoid(raw_logit_cwg)
print(f"Step D: Raw sigmoid: sigmoid({raw_logit_cwg:.6f}) = {p_raw_cwg:.6f}")

cal_logit_cwg = A_cwg * raw_logit_cwg + B_cwg
p_cal_cwg = sigmoid(cal_logit_cwg)
print(f"Step E: Platt calibration: sigmoid({A_cwg:.6f} * {raw_logit_cwg:.6f} + {B_cwg:.6f}) = sigmoid({cal_logit_cwg:.6f}) = {p_cal_cwg:.6f} ({p_cal_cwg*100:.2f}%)")

decision_cwg = p_cal_cwg >= thresh_cwg
print(f"Step F: Threshold: {p_cal_cwg:.4f} >= {thresh_cwg:.2f} -> Decision = {decision_cwg}")

# Compare with MetaStacker
pred_stacker_cwg = MetaStacker.predict_disease("C_W_G", "NAFLD", {"clinical": p_clin_nf, "wearable": p_wear_nf, "gut": p_gut_nf})
print(f"Pipeline output: risk_score = {pred_stacker_cwg['risk_score']}, decision = {pred_stacker_cwg['decision']}, threshold = {pred_stacker_cwg['threshold_used']}")
print(f"Match difference: {abs(p_cal_cwg - pred_stacker_cwg['risk_score']):.8f}")
