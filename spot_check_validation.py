import math
from src.fusion_v2.fusion import fuse_predictions, DISEASES

def make_router_output(dis_target, val_target):
    probs = {d: 0.5 for d in DISEASES}
    probs[dis_target] = val_target
    return {
        "clinical": {
            "status": "success",
            "probabilities": probs,
            "predictions": {d: 0 for d in DISEASES}
        },
        "gut": {"status": "not_run"},
        "wearable": {"status": "not_run"}
    }

print("="*80)
print("INDEPENDENT RUNTIME SPOT-CHECK FOR STRICT PROBABILITY VALIDATION")
print("="*80)

test_cases = [
    # (Label, Input Value, Expected Exception Type)
    ("NaN float", float("nan"), ValueError),
    ("+Infinity float", float("inf"), ValueError),
    ("-Infinity float", float("-inf"), ValueError),
    ("Below 0.0 (-0.1)", -0.1, ValueError),
    ("Above 1.0 (1.1)", 1.1, ValueError),
    ("Boolean True", True, ValueError),
    ("Boolean False", False, ValueError),
    ("String 'not_a_number'", "not_a_number", ValueError),
    ("None inside dict", None, ValueError),
    ("List inside dict", [0.5], ValueError),
    ("Dict inside dict", {"nested": 0.5}, ValueError),
]

print(f"\n{'Test Case':25s} | {'Input Value':18s} | {'Expected':15s} | {'Actual Raised':15s} | {'Correct?':8s} | {'Exception Message'}")
print("-" * 110)

all_passed = True

for label, val, exp_exc in test_cases:
    router_out = make_router_output("Type2_Diabetes", val)
    actual_exc = None
    msg = ""
    try:
        fuse_predictions(router_out)
    except Exception as e:
        actual_exc = type(e)
        msg = str(e)
    
    is_correct = (actual_exc == exp_exc)
    if not is_correct:
        all_passed = False
    
    val_str = str(val) if not isinstance(val, float) or not math.isnan(val) else "float('nan')"
    print(f"{label:25s} | {val_str:18s} | {exp_exc.__name__:15s} | {actual_exc.__name__ if actual_exc else 'None':15s} | {str(is_correct):8s} | {msg}")

# Structural tests
structural_cases = [
    ("Non-dict string", "string_payload", TypeError),
    ("None router_output", None, TypeError),
    ("List router_output", [{"clinical": {}}], TypeError),
    ("Missing probs dict", {"clinical": {"status": "success"}}, ValueError),
    ("Missing disease key", {"clinical": {"status": "success", "probabilities": {"Type2_Diabetes": 0.5}}}, ValueError),
]

print("\n--- Structural Router Output Rejections ---")
print(f"{'Test Case':25s} | {'Input Type':18s} | {'Expected':15s} | {'Actual Raised':15s} | {'Correct?':8s} | {'Exception Message'}")
print("-" * 110)

for label, payload, exp_exc in structural_cases:
    actual_exc = None
    msg = ""
    try:
        fuse_predictions(payload)
    except Exception as e:
        actual_exc = type(e)
        msg = str(e)
    
    is_correct = (actual_exc == exp_exc)
    if not is_correct:
        all_passed = False
    
    print(f"{label:25s} | {type(payload).__name__:18s} | {exp_exc.__name__:15s} | {actual_exc.__name__ if actual_exc else 'None':15s} | {str(is_correct):8s} | {msg}")

# Boundary acceptance tests
boundary_cases = [
    ("Lower Boundary 0.0", 0.0),
    ("Upper Boundary 1.0", 1.0),
    ("Valid Midpoint 0.5", 0.5),
    ("Valid Float 0.8266", 0.8266),
]

print("\n--- Valid Boundary & Probability Acceptance Tests ---")
print(f"{'Test Case':25s} | {'Input Value':18s} | {'Accepted?':15s} | {'Output Score':15s} | {'Correct?'}")
print("-" * 80)

for label, val in boundary_cases:
    router_out = make_router_output("Type2_Diabetes", val)
    passed = False
    score = None
    try:
        res = fuse_predictions(router_out)
        score = res["diseases"]["Type2_Diabetes"]["risk_score"]
        passed = (score is not None and isinstance(score, float))
    except Exception as e:
        passed = False
        score = str(e)
    
    if not passed:
        all_passed = False
    
    print(f"{label:25s} | {str(val):18s} | {str(passed):15s} | {str(score):15s} | {str(passed)}")

print("\n" + "="*80)
print(f"OVERALL SPOT-CHECK VERDICT: {'ALL TESTS PASSED WITH 100% PRECISION' if all_passed else 'FAILURES DETECTED'}")
print("="*80)
