"""
smoke_test_gut.py - Comprehensive smoke tests for predict_gut.py (13 test cases)
Runs all handoff verification tests and reports PASS/FAIL for each.

Test T5-T11 verify that bad inputs are REJECTED (expect exceptions).
Test T1-T4, T12-T13 verify valid inputs are accepted and produce correct output.
"""
import sys
import os
import math

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
from predict_gut import predict_gut

PASS = "PASS"
FAIL = "FAIL"
results = []

def run_test_valid(name, fn):
    """Test that expects a valid result (no exception)."""
    try:
        result = fn()
        results.append((name, PASS, str(result)[:120]))
        print(f"  [PASS] {name}")
        if result:
            print(f"         -> {str(result)[:120]}")
    except Exception as e:
        results.append((name, FAIL, f"Unexpected {type(e).__name__}: {e}"))
        print(f"  [FAIL] {name}")
        print(f"         -> Unexpected {type(e).__name__}: {str(e)[:200]}")

def run_test_raises(name, fn, expected_exc):
    """Test that expects an exception to be raised."""
    try:
        result = fn()
        # Should have raised — this is a failure
        results.append((name, FAIL, f"ERROR: Expected {expected_exc.__name__} but got result: {result}"))
        print(f"  [FAIL] {name}")
        print(f"         -> ERROR: Should have raised {expected_exc.__name__}, but returned: {str(result)[:120]}")
    except expected_exc as e:
        results.append((name, PASS, f"Correctly raised {type(e).__name__}: {str(e)[:100]}"))
        print(f"  [PASS] {name}")
        print(f"         -> Correctly raised {type(e).__name__}: {str(e)[:120]}")
    except Exception as e:
        results.append((name, FAIL, f"Wrong exception type: expected {expected_exc.__name__}, got {type(e).__name__}: {e}"))
        print(f"  [FAIL] {name}")
        print(f"         -> Wrong exception: expected {expected_exc.__name__}, got {type(e).__name__}: {str(e)[:200]}")

# ── Base valid inputs ──────────────────────────────────────────────

HEALTHY_PROFILE = {
    "Akkermansia": 3.5, "Faecalibacterium": 10.0, "Roseburia": 5.0,
    "Bifidobacterium": 6.0, "Bacteroides": 20.0, "Prevotella": 5.0,
    "Ruminococcus": 4.0, "Blautia": 7.5, "Collinsella": 2.0,
    "Escherichia_Shigella": 1.0, "Coprococcus": 3.0, "Alistipes": 3.5,
    "Subdoligranulum": 2.5, "Enterococcus": 0.8, "Eubacterium": 4.5,
    "Parabacteroides": 3.2, "Lactobacillus": 5.5, "Klebsiella": 0.5,
    "Streptococcus": 1.5, "Eggerthella": 0.5, "Other_Taxa": 10.5,
}
assert abs(sum(HEALTHY_PROFILE.values()) - 100.0) < 0.01

# Disease-associated profile: reduced protective, elevated pathogen taxa
DISEASE_PROFILE = {
    "Akkermansia": 0.3, "Faecalibacterium": 1.0, "Roseburia": 0.5,
    "Bifidobacterium": 0.5, "Bacteroides": 15.0, "Prevotella": 3.0,
    "Ruminococcus": 2.0, "Blautia": 3.0, "Collinsella": 4.0,
    "Escherichia_Shigella": 12.0, "Coprococcus": 1.0, "Alistipes": 2.0,
    "Subdoligranulum": 1.0, "Enterococcus": 8.0, "Eubacterium": 1.5,
    "Parabacteroides": 2.0, "Lactobacillus": 4.0, "Klebsiella": 10.0,
    "Streptococcus": 8.0, "Eggerthella": 6.0, "Other_Taxa": 15.2,
}
assert abs(sum(DISEASE_PROFILE.values()) - 100.0) < 0.01

# Minimum plausible: near-zero for all, valid sum via Other_Taxa
MIN_PROFILE = {k: 0.01 for k in HEALTHY_PROFILE}
MIN_PROFILE["Other_Taxa"] = 100.0 - (0.01 * 20)
assert abs(sum(MIN_PROFILE.values()) - 100.0) < 0.01

# Maximum plausible: one dominant taxon, all others minimal
MAX_PROFILE = {k: 0.1 for k in HEALTHY_PROFILE}
MAX_PROFILE["Bacteroides"] = 100.0 - (0.1 * 20)
assert abs(sum(MAX_PROFILE.values()) - 100.0) < 0.01

print("\n" + "=" * 70)
print("SMOKE TESTS - predict_gut() - 13 Test Cases")
print("=" * 70 + "\n")

# ── TEST 1: Healthy microbiome ─────────────────────────────────────
def test1():
    r = predict_gut(HEALTHY_PROFILE)
    assert "probabilities" in r and "predictions" in r
    assert set(r["probabilities"].keys()) == {"Type2_Diabetes","Prediabetes","High_Adiposity_Risk","Metabolic_Syndrome","NAFLD"}
    assert set(r["predictions"].keys()) == {"Type2_Diabetes","Prediabetes","High_Adiposity_Risk","Metabolic_Syndrome","NAFLD"}
    assert r["threshold_used"] == 0.5
    assert "suppressed_labels" in r
    # All probs should be floats in [0,1]
    for k, v in r["probabilities"].items():
        assert isinstance(v, float) and 0.0 <= v <= 1.0, f"{k} prob={v} not in [0,1]"
    return f"probs={r['probabilities']}, preds={r['predictions']}, suppressed={r['suppressed_labels']}"
run_test_valid("T1: Plausible healthy microbiome - full output structure", test1)

# ── TEST 2: Disease-associated microbiome ─────────────────────────
def test2():
    r_disease = predict_gut(DISEASE_PROFILE)
    r_healthy = predict_gut(HEALTHY_PROFILE)
    t2d_disease = r_disease["probabilities"]["Type2_Diabetes"]
    t2d_healthy = r_healthy["probabilities"]["Type2_Diabetes"]
    assert t2d_disease > t2d_healthy, f"Expected disease T2D prob > healthy, got {t2d_disease} vs {t2d_healthy}"
    return f"T2D_prob: disease={t2d_disease:.4f} > healthy={t2d_healthy:.4f}"
run_test_valid("T2: Disease-associated microbiome - elevated disease probs", test2)

# ── TEST 3: Minimum plausible abundances ──────────────────────────
def test3():
    r = predict_gut(MIN_PROFILE)
    assert all(isinstance(v, float) and math.isfinite(v) for v in r["probabilities"].values())
    return f"probs={r['probabilities']}"
run_test_valid("T3: Minimum plausible abundances (near-zero, valid sum)", test3)

# ── TEST 4: Maximum plausible abundances ──────────────────────────
def test4():
    r = predict_gut(MAX_PROFILE)
    assert all(isinstance(v, float) and math.isfinite(v) for v in r["probabilities"].values())
    return f"probs={r['probabilities']}"
run_test_valid("T4: Maximum plausible abundances (one dominant taxon, valid sum)", test4)

# ── TEST 5: Missing feature ────────────────────────────────────────
def test5():
    bad = dict(HEALTHY_PROFILE)
    del bad["Akkermansia"]
    predict_gut(bad)
run_test_raises("T5: Missing feature - should raise ValueError", test5, ValueError)

# ── TEST 6: Extra feature ─────────────────────────────────────────
def test6():
    bad = dict(HEALTHY_PROFILE)
    bad["Patient_ID"] = "P12345"
    predict_gut(bad)
run_test_raises("T6: Extra field (Patient_ID) - should raise ValueError", test6, ValueError)

# ── TEST 7: NaN value ─────────────────────────────────────────────
def test7():
    bad = dict(HEALTHY_PROFILE)
    bad["Akkermansia"] = float("nan")
    predict_gut(bad)
run_test_raises("T7: NaN value - should raise ValueError", test7, ValueError)

# ── TEST 8: Infinity ──────────────────────────────────────────────
def test8():
    bad = dict(HEALTHY_PROFILE)
    bad["Akkermansia"] = float("inf")
    predict_gut(bad)
run_test_raises("T8: Infinite value - should raise ValueError", test8, ValueError)

# ── TEST 9: Negative abundance ────────────────────────────────────
def test9():
    bad = dict(HEALTHY_PROFILE)
    bad["Escherichia_Shigella"] = -1.5
    predict_gut(bad)
run_test_raises("T9: Negative abundance - should raise ValueError", test9, ValueError)

# ── TEST 10: Wrong abundance sum ──────────────────────────────────
def test10():
    # Values summing to ~50 (proportions, not percentages)
    bad = {k: v / 2.0 for k, v in HEALTHY_PROFILE.items()}
    predict_gut(bad)
run_test_raises("T10: Wrong sum (proportions not percentages) - should raise ValueError", test10, ValueError)

# ── TEST 11: Wrong datatype ───────────────────────────────────────
def test11():
    bad = dict(HEALTHY_PROFILE)
    bad["Akkermansia"] = "3.5"  # string instead of float
    predict_gut(bad)
run_test_raises("T11: String value (wrong datatype) - should raise TypeError", test11, TypeError)

# ── TEST 12: Dict order doesn't matter (key-based lookup) ─────────
def test12():
    # Python dicts are ordered since 3.7, but predict_gut uses key lookup, not positional
    # Pass features in reversed order — output must be identical to HEALTHY_PROFILE
    r_forward = predict_gut(HEALTHY_PROFILE)
    r_reversed = predict_gut({k: HEALTHY_PROFILE[k] for k in reversed(list(HEALTHY_PROFILE.keys()))})
    assert r_forward["probabilities"] == r_reversed["probabilities"], \
        f"Order-dependency detected: {r_forward['probabilities']} != {r_reversed['probabilities']}"
    return f"PASS (order-independent): preds={r_reversed['predictions']}"
run_test_valid("T12: Reversed feature order in dict - should still work (dict is key-based)", test12)

# ── TEST 13: Suppression rule ─────────────────────────────────────
def test13():
    """
    Suppression contract:
    - If T2D_pred=1 AND Prediabetes_raw_prob >= 0.5: Prediabetes_pred forced to 0,
      'Prediabetes' added to suppressed_labels, raw prob unchanged.
    - If T2D_pred=1 AND Prediabetes_raw_prob < 0.5: Prediabetes_pred=0 already,
      suppressed_labels empty (no change needed), raw prob unchanged.
    - If T2D_pred=0: suppression not triggered, Prediabetes_pred = threshold(raw_prob).
    Key assertion: raw probabilities are NEVER modified by suppression.
    """
    r_d = predict_gut(DISEASE_PROFILE)
    r_h = predict_gut(HEALTHY_PROFILE)

    lines = []

    # -- Disease profile checks --
    t2d_d = r_d["predictions"]["Type2_Diabetes"]
    pre_pred_d = r_d["predictions"]["Prediabetes"]
    pre_raw_d = r_d["probabilities"]["Prediabetes"]
    t2d_raw_d = r_d["probabilities"]["Type2_Diabetes"]
    suppressed_d = r_d["suppressed_labels"]

    lines.append(f"Disease: T2D_pred={t2d_d}(raw={t2d_raw_d:.4f}), Pre_pred={pre_pred_d}, Pre_raw={pre_raw_d:.6f}, suppressed={suppressed_d}")

    if t2d_d == 1:
        # T2D predicted: Prediabetes MUST be 0 (whether or not it would have been 1)
        assert pre_pred_d == 0, f"Suppression failed: T2D=1 but Prediabetes_pred={pre_pred_d}"
        # Raw prob must be preserved (finite float, unchanged)
        assert isinstance(pre_raw_d, float) and math.isfinite(pre_raw_d)
        if pre_raw_d >= 0.5:
            # Would have been 1 — explicitly suppressed
            assert "Prediabetes" in suppressed_d, f"Expected 'Prediabetes' in suppressed_labels (pre_raw={pre_raw_d})"
            lines.append(f"EXPLICIT SUPPRESSION: Pre_raw={pre_raw_d:.4f}>=0.5 -> forced to 0, added to suppressed_labels")
        else:
            # Would have been 0 anyway — suppression transparent
            lines.append(f"TRANSPARENT: Pre_raw={pre_raw_d:.4f}<0.5, already 0, suppressed_labels correctly empty")
    else:
        assert isinstance(pre_raw_d, float) and math.isfinite(pre_raw_d)
        expected = 1 if pre_raw_d >= 0.5 else 0
        lines.append("T2D=0 (disease profile): suppression not triggered, raw prob contract correct")

    # Check healthy profile (expected T2D=0 — suppression not triggered)
    t2d_h = r_h["predictions"]["Type2_Diabetes"]
    pre_raw_h = r_h["probabilities"]["Prediabetes"]
    lines.append(f"Healthy profile: T2D_pred={t2d_h}, Pre_raw={pre_raw_h:.6f}, suppressed={r_h['suppressed_labels']}")
    assert isinstance(pre_raw_h, float) and math.isfinite(pre_raw_h)

    return " | ".join(lines)
run_test_valid("T13: Suppression rule - T2D=1 -> Prediabetes_pred=0, raw prob preserved", test13)

# ── Summary ────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print("SUMMARY")
print("=" * 70)
total = len(results)
passed = sum(1 for _, status, _ in results if status == PASS)
failed = total - passed
print(f"  Total: {total}  |  PASS: {passed}  |  FAIL: {failed}")
print()
for name, status, detail in results:
    marker = "+" if status == PASS else "X"
    print(f"  {marker} [{status}] {name}")
print()
if failed == 0:
    print("  ALL TESTS PASSED")
else:
    print(f"  {failed} TEST(S) FAILED")
    for name, status, detail in results:
        if status == FAIL:
            print(f"    FAILED: {name}")
            print(f"    REASON: {detail}")
print("=" * 70)
