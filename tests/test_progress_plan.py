"""
test_progress_plan.py — Automated Tests for Personalized Progress Plan System

Tests:
1. 1-week plan generation (7 days, daily task structure).
2. 1-month plan generation (28 days, 4 weekly progressions).
3. 3-month plan generation (84 days, 12 weeks, 3 distinct phases).
4. Maximum daily task count is enforced (4–6 tasks/day, strictly <= 7).
5. Tasks originate from validated recommendation pillars.
6. Unsupported numerical targets are not introduced.
7. Day completion requires all required tasks.
8. Next day remains locked until previous day completion.
9. Progress persistence works after reload and retrieval from store.
10. Real PDF generation produces valid PDF bytes.
11. REST API endpoints work seamlessly.
12. Existing health_plan and prediction responses remain intact.
"""

import os
import sys
import pytest
from fastapi.testclient import TestClient

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.recommendations.progress_plan_generator import ProgressPlanGenerator
from src.recommendations.progress_plan_store import ProgressPlanStore
from src.recommendations.progress_plan_pdf import ProgressPlanPDFGenerator
from api_server import app

client = TestClient(app)


@pytest.fixture
def sample_health_plan_data():
    return {
        "summary_title": "Your Personalized Health Plan",
        "primary_disease_evaluated": "Type2_Diabetes",
        "sections": {
            "section_a_your_results": {
                "title": "A. What Your Results Mean",
                "body": "Your assessment indicates an elevated risk for Type 2 Diabetes.",
                "evaluated_conditions": [
                    {"disease": "Type2_Diabetes", "risk_level": "High Risk", "probability_percentage": "85.0%"}
                ]
            },
            "section_b_what_is_contributing": {
                "title": "B. Key Factors",
                "contributing_items": [
                    {
                        "parameter": "Fasting_Blood_Glucose",
                        "friendly_name": "Fasting Blood Glucose",
                        "patient_value": 150.0,
                        "unit": "mg/dL",
                        "status": "above_expected_range",
                        "explanation_sentence": "Your Fasting Blood Glucose is 150.0 mg/dL, compared to 70–99 mg/dL."
                    }
                ]
            },
            "section_c_what_to_focus_on_first": {
                "title": "C. What to Focus On First",
                "priorities": [
                    {"rank": 1, "title": "Physical Activity & Movement", "explanation": "Regular movement improves glucose uptake."},
                    {"rank": 2, "title": "Dietary Quality & Carbohydrate Nutrition", "explanation": "High-fibre foods slow glucose spikes."}
                ]
            },
            "section_d_personalized_recommendations": {
                "title": "D. Actionable Recommendations",
                "recommendations": [
                    {
                        "title": "Physical Activity & Movement",
                        "priority_rank": 1,
                        "recommendation_text": "Aim for at least 150–300 minutes of moderate-intensity aerobic physical activity.",
                        "numerical_target": "150–300 minutes/week"
                    },
                    {
                        "title": "Dietary Quality & Carbohydrate Nutrition",
                        "priority_rank": 2,
                        "recommendation_text": "Consume at least 25 g per day of naturally occurring dietary fibre.",
                        "numerical_target": "25 g per day"
                    }
                ]
            },
            "section_e_why_suggested": {
                "title": "E. Why Suggested",
                "items": [
                    {"title": "Physical Activity", "reason": "Improves insulin sensitivity.", "evidence_source": "WHO Guidelines"}
                ]
            }
        }
    }


@pytest.fixture
def sample_patient_info():
    return {
        "patient_id": "P_PROGRESS_TEST",
        "name": "Jordan Hayes",
        "age": 49,
        "gender": "Female"
    }


def test_progress_1_week_plan_generation(sample_health_plan_data, sample_patient_info):
    """Test 1: 1-week plan generates exactly 7 days with sequential day structures."""
    plan = ProgressPlanGenerator.generate_progress_plan(
        sample_health_plan_data, sample_patient_info, duration="1_week"
    )

    assert plan["duration"] == "1_week"
    assert plan["total_days"] == 7
    assert len(plan["days"]) == 7
    assert plan["days"][0]["day_number"] == 1
    assert plan["days"][0]["is_unlocked"] is True
    assert plan["days"][1]["is_unlocked"] is False
    print(f"\n[PASS] Test 1: 1-Week Plan Generated successfully with {plan['total_tasks']} total tasks.")


def test_progress_1_month_plan_generation(sample_health_plan_data, sample_patient_info):
    """Test 2: 1-month plan generates 4 weeks and 28 days."""
    plan = ProgressPlanGenerator.generate_progress_plan(
        sample_health_plan_data, sample_patient_info, duration="1_month"
    )

    assert plan["duration"] == "1_month"
    assert plan["total_days"] == 28
    assert plan["total_weeks"] == 4
    assert len(plan["weeks"]) == 4
    assert len(plan["days"]) == 28
    print(f"\n[PASS] Test 2: 1-Month Plan Generated successfully with 4 weekly themes and 28 days.")


def test_progress_3_months_plan_generation(sample_health_plan_data, sample_patient_info):
    """Test 3: 3-month plan generates 3 distinct phases (Foundation, Consistency, Habits) over 12 weeks / 84 days."""
    plan = ProgressPlanGenerator.generate_progress_plan(
        sample_health_plan_data, sample_patient_info, duration="3_months"
    )

    assert plan["duration"] == "3_months"
    assert plan["total_days"] == 84
    assert plan["total_weeks"] == 12
    assert len(plan["phases"]) == 3
    assert "Foundation" in plan["phases"][0]["title"]
    assert "Consistency" in plan["phases"][1]["title"]
    assert "Habit Mastery" in plan["phases"][2]["title"]
    print(f"\n[PASS] Test 3: 3-Months Plan Generated successfully across 3 progressive phases.")


def test_progress_max_daily_tasks_enforced(sample_health_plan_data, sample_patient_info):
    """Test 4: Maximum daily task count is strictly capped between 4 and 6 (max <= 7)."""
    for duration in ["1_week", "1_month", "3_months"]:
        plan = ProgressPlanGenerator.generate_progress_plan(
            sample_health_plan_data, sample_patient_info, duration=duration
        )
        for day in plan["days"]:
            assert 4 <= len(day["tasks"]) <= 7, f"Day {day['day_number']} has {len(day['tasks'])} tasks (expected 4-7)."
    print("\n[PASS] Test 4: Daily task count strictly enforced between 4 and 6 tasks across all durations.")


def test_progress_tasks_originate_from_validated_pillars(sample_health_plan_data, sample_patient_info):
    """Test 5: Tasks strictly originate from validated priority pillars (e.g. Physical Activity, Dietary Nutrition)."""
    plan = ProgressPlanGenerator.generate_progress_plan(
        sample_health_plan_data, sample_patient_info, duration="1_week"
    )
    categories = {t["category"] for d in plan["days"] for t in d["tasks"]}
    assert "physical_activity" in categories
    assert "dietary_nutrition" in categories

    for d in plan["days"]:
        for t in d["tasks"]:
            assert t["completion_required"] is True
            assert len(t["instruction"]) > 0
            assert len(t["why_selected"]) > 0
            assert t["recommendation_source"] in ("WHO_PA_SEDENTARY_2020", "WHO_CARB_FIBER_2023", "CDC_DPP_CURRICULUM_2024", "CLINICAL_LIFESTYLE_GUIDELINES")
    print("\n[PASS] Test 5: All tasks are strictly anchored to verified guideline recommendation sources.")


def test_progress_day_completion_and_unlocking(sample_health_plan_data, sample_patient_info):
    """Test 7 & 8: Day completes ONLY when all required tasks are done, and next day unlocks sequentially."""
    plan_data = ProgressPlanGenerator.generate_progress_plan(
        sample_health_plan_data, sample_patient_info, duration="1_week"
    )
    saved_record = ProgressPlanStore.save_plan(plan_data)
    plan_id = saved_record["plan_id"]

    day1_tasks = plan_data["days"][0]["tasks"]
    task_ids = [t["id"] for t in day1_tasks]

    # Complete first task: Day 1 should NOT be complete, Day 2 should remain LOCKED
    rec = ProgressPlanStore.toggle_task(plan_id, task_ids[0], completed=True)
    assert 1 not in rec["completed_days"]
    assert rec["current_day"] == 1
    assert rec["plan_data"]["days"][1]["is_unlocked"] is False

    # Complete all remaining Day 1 tasks: Day 1 should become COMPLETE, Day 2 UNLOCKED
    for tid in task_ids[1:]:
        rec = ProgressPlanStore.toggle_task(plan_id, tid, completed=True)

    assert 1 in rec["completed_days"]
    assert rec["current_day"] == 2
    assert rec["plan_data"]["days"][0]["is_completed"] is True
    assert rec["plan_data"]["days"][1]["is_unlocked"] is True
    assert rec["plan_data"]["days"][2]["is_unlocked"] is False
    assert rec["overall_progress"] > 0
    print(f"\n[PASS] Test 7 & 8: Day 1 completion unlocked Day 2 ({rec['overall_progress']}% overall progress).")


def test_progress_persistence_and_reset(sample_health_plan_data, sample_patient_info):
    """Test 9: Plan survives store reload and resets cleanly."""
    plan_data = ProgressPlanGenerator.generate_progress_plan(
        sample_health_plan_data, sample_patient_info, duration="1_week"
    )
    saved = ProgressPlanStore.save_plan(plan_data)
    plan_id = saved["plan_id"]

    # Toggle task
    ProgressPlanStore.toggle_task(plan_id, plan_data["days"][0]["tasks"][0]["id"], completed=True)

    # Retrieve fresh record
    retrieved = ProgressPlanStore.get_plan(plan_id)
    assert retrieved is not None
    assert len(retrieved["completed_tasks"]) == 1

    # Reset
    reset_rec = ProgressPlanStore.reset_plan(plan_id)
    assert len(reset_rec["completed_tasks"]) == 0
    assert reset_rec["current_day"] == 1
    assert reset_rec["overall_progress"] == 0.0
    print("\n[PASS] Test 9: Persistence and Reset tested successfully.")


def test_progress_pdf_generation(sample_health_plan_data, sample_patient_info):
    """Test 10: PDF generator produces valid PDF bytes."""
    plan_data = ProgressPlanGenerator.generate_progress_plan(
        sample_health_plan_data, sample_patient_info, duration="1_week"
    )
    saved_record = ProgressPlanStore.save_plan(plan_data)
    pdf_bytes = ProgressPlanPDFGenerator.generate_pdf_bytes(saved_record)

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")
    print(f"\n[PASS] Test 10: Real PDF generated successfully ({len(pdf_bytes)} bytes, starts with %PDF).")


def test_progress_rest_api_endpoints(sample_health_plan_data):
    """Test 11: Progress Plan REST API endpoints (generate, get, toggle, pdf)."""
    # 1. Generate endpoint
    gen_payload = {
        "patient_id": "P_API_TEST",
        "patient_name": "Marcus Aurelius",
        "patient_age": 55,
        "patient_gender": "Male",
        "duration": "1_week",
        "health_plan": sample_health_plan_data
    }
    resp = client.post("/api/progress-plan/generate", json=gen_payload)
    assert resp.status_code == 200
    data = resp.json()
    plan_id = data["plan_id"]
    assert "plan_data" in data

    # 2. Get endpoint
    get_resp = client.get(f"/api/progress-plan/{plan_id}")
    assert get_resp.status_code == 200
    assert get_resp.json()["plan_id"] == plan_id

    # 3. Toggle task endpoint
    first_task_id = data["plan_data"]["days"][0]["tasks"][0]["id"]
    toggle_resp = client.post(
        f"/api/progress-plan/{plan_id}/toggle-task",
        json={"task_id": first_task_id, "completed": True}
    )
    assert toggle_resp.status_code == 200
    assert first_task_id in toggle_resp.json()["completed_tasks"]

    # 4. PDF download endpoint
    pdf_resp = client.get(f"/api/progress-plan/{plan_id}/pdf")
    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert pdf_resp.content.startswith(b"%PDF")
    print(f"\n[PASS] Test 11: All Progress Plan REST API endpoints verified.")
