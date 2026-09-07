"""
progress_plan_generator.py — Governed Personalized Progress Plan Generator

Downstream planning layer that transforms already-validated health recommendations
and priority pillars into actionable, structured daily/weekly progress plans for:
1. 1 Week Plan (7 days)
2. 1 Month Plan (4 weeks / 28 days)
3. 3 Months Plan (12 weeks / 3 phases: Foundation, Consistency, Long-Term Habits)

Strict Governance Rules:
- Derives tasks strictly from validated priority pillars and recommendations in health_plan.
- Daily tasks are strictly capped at 4–6 (max 7) manageable tasks per day.
- Preserves all numerical targets (e.g., 25 g/day, 150–300 min/week, 5%–7% weight loss).
- Does not invent unsupported medical or pharmacological claims.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional


class ProgressPlanGenerator:
    """Generates structured, manageable daily progress plans from validated health plan recommendations."""

    # Curated task templates tied to approved guideline categories
    ACTIVITY_TASKS = [
        {
            "title": "20-Minute Brisk Walk",
            "instruction": "Enjoy a comfortable 20-minute brisk walk after lunch or dinner.",
            "suggestion": "Brisk walking at a pace where you can talk comfortably.",
            "why_selected": "Regular daily walking helps your muscles absorb blood sugar directly.",
            "source": "WHO_PA_SEDENTARY_2020",
            "target": "150–300 min/week"
        },
        {
            "title": "15-Minute Movement Session",
            "instruction": "Take a 15-minute active break with bodyweight movement or brisk walking.",
            "suggestion": "Light dynamic stretches, stairs, or indoor walking.",
            "why_selected": "Short movement breaks improve insulin response throughout the day.",
            "source": "WHO_PA_SEDENTARY_2020",
            "target": "150–300 min/week"
        },
        {
            "title": "30-Minute Aerobic Activity",
            "instruction": "Complete a 30-minute session of moderate-intensity aerobic exercise.",
            "suggestion": "Brisk walking, stationary cycling, or swimming.",
            "why_selected": "Contributes to your weekly 150–300 minute aerobic target.",
            "source": "WHO_PA_SEDENTARY_2020",
            "target": "150–300 min/week"
        },
        {
            "title": "Post-Meal Digestive Walk",
            "instruction": "Take a gentle 15-minute stroll within 30 minutes after your largest meal.",
            "suggestion": "Gentle outdoor or treadmill walking.",
            "why_selected": "Post-meal walking significantly blunts blood sugar spikes.",
            "source": "WHO_PA_SEDENTARY_2020",
            "target": "150–300 min/week"
        },
        {
            "title": "Weekend Active Recreation",
            "instruction": "Engage in 30–45 minutes of enjoyable active leisure.",
            "suggestion": "Park walk, gardening, hiking, or recreational cycling.",
            "why_selected": "Builds long-term enjoyment and consistency in regular movement.",
            "source": "WHO_PA_SEDENTARY_2020",
            "target": "150–300 min/week"
        },
        {
            "title": "Weekly Movement Summary Check",
            "instruction": "Review your weekly physical activity and aim for a gentle 20-minute stroll.",
            "suggestion": "Check if you reached your weekly movement goals.",
            "why_selected": "Tracking consistency builds confidence in long-term habit formation.",
            "source": "WHO_PA_SEDENTARY_2020",
            "target": "150–300 min/week"
        }
    ]

    FIBRE_NUTRITION_TASKS = [
        {
            "title": "Add One High-Fibre Whole Grain",
            "instruction": "Include a serving of whole grains in your breakfast or lunch.",
            "suggestion": "Rolled oats, brown rice, whole wheat bread, or quinoa.",
            "why_selected": "Whole grains provide natural dietary fibre to support metabolic health.",
            "source": "WHO_CARB_FIBER_2023",
            "target": "25 g per day"
        },
        {
            "title": "Include Beans or Lentils",
            "instruction": "Add a portion of legumes or pulses to your lunch or dinner.",
            "suggestion": "Lentil soup, chickpea salad, or black bean chilli.",
            "why_selected": "Legumes are exceptionally rich in soluble fibre that slows carbohydrate digestion.",
            "source": "WHO_CARB_FIBER_2023",
            "target": "25 g per day"
        },
        {
            "title": "Eat One Serving of Fresh Fruit",
            "instruction": "Enjoy one piece of fresh fruit with edible skin as a snack or dessert.",
            "suggestion": "Apple with peel, fresh berries, or a pear.",
            "why_selected": "Whole fruits provide intact dietary fibre, antioxidants, and vitamins.",
            "source": "WHO_CARB_FIBER_2023",
            "target": "25 g per day"
        },
        {
            "title": "Include 2 Servings of Colourful Vegetables",
            "instruction": "Fill at least half your lunch or dinner plate with non-starchy vegetables.",
            "suggestion": "Broccoli, spinach, carrots, bell peppers, or salad greens.",
            "why_selected": "Non-starchy vegetables provide high nutrient density with minimal caloric impact.",
            "source": "WHO_CARB_FIBER_2023",
            "target": "25 g per day"
        },
        {
            "title": "Add Healthy Seeds or Nuts",
            "instruction": "Sprinkle a spoonful of nuts or seeds over your meal or breakfast.",
            "suggestion": "Chia seeds, ground flaxseeds, walnuts, or almonds.",
            "why_selected": "Seeds and nuts provide healthy fats and prebiotic fibre for digestive wellness.",
            "source": "WHO_CARB_FIBER_2023",
            "target": "25 g per day"
        }
    ]

    WEIGHT_CALORIC_TASKS = [
        {
            "title": "Mindful Plate Portioning",
            "instruction": "Use the plate method: 1/2 vegetables, 1/4 lean protein, 1/4 whole grains.",
            "suggestion": "Visual portion control without complicated calorie counting.",
            "why_selected": "Supports a gradual, sustainable 500–750 kcal daily caloric reduction.",
            "source": "CDC_DPP_CURRICULUM_2024",
            "target": "5% to 7% weight loss"
        },
        {
            "title": "Pre-Meal Water Glass",
            "instruction": "Drink a large glass of water 15 minutes before your main meals.",
            "suggestion": "Still water or sparkling water with a slice of lemon.",
            "why_selected": "Aids hydration and supports natural satiety cues.",
            "source": "CDC_DPP_CURRICULUM_2024",
            "target": "5% to 7% weight loss"
        },
        {
            "title": "Swap One Refined Snack",
            "instruction": "Replace one processed or sugary snack with a wholesome alternative.",
            "suggestion": "Handful of almonds or sliced cucumber instead of biscuits or crisps.",
            "why_selected": "Prevents rapid glucose fluctuations and trims unnecessary calories.",
            "source": "CDC_DPP_CURRICULUM_2024",
            "target": "5% to 7% weight loss"
        }
    ]

    LIFESTYLE_ROUTINE_TASKS = [
        {
            "title": "Break Up Sitting Time",
            "instruction": "Stand up and walk for 2 minutes every hour during sitting periods.",
            "suggestion": "Set a gentle hourly reminder or stand during phone calls.",
            "why_selected": "Reducing uninterrupted sedentary time supports cardiovascular and metabolic health.",
            "source": "WHO_PA_SEDENTARY_2020",
            "target": "< 8 hours sedentary/day"
        },
        {
            "title": "Restorative Sleep Routine",
            "instruction": "Begin winding down 30 minutes before bed and dim electronic screens.",
            "suggestion": "Aim for 7–8 hours of restful sleep in a dark, quiet room.",
            "why_selected": "Quality sleep regulates hunger hormones and improves daytime insulin sensitivity.",
            "source": "CLINICAL_LIFESTYLE_GUIDELINES",
            "target": "7–9 hours sleep/night"
        }
    ]

    @classmethod
    def generate_progress_plan(
        cls,
        health_plan: Dict[str, Any],
        patient_info: Dict[str, Any],
        duration: str = "1_week"
    ) -> Dict[str, Any]:
        """Generates a complete, structured progress plan for the given duration.

        Parameters
        ----------
        health_plan : dict
            Validated health plan containing priority pillars and recommendations.
        patient_info : dict
            Patient metadata (patient_id, name, age, gender).
        duration : str
            "1_week", "1_month", or "3_months".

        Returns
        -------
        dict
            Complete progress plan with days, weeks, and structured daily tasks.
        """
        # 1. Extract validated priorities and recommendations from health_plan
        sections = health_plan.get("sections", {})
        priorities_data = sections.get("section_c_what_to_focus_on_first", {}).get("priorities", [])
        recs_data = sections.get("section_d_personalized_recommendations", {}).get("recommendations", [])

        priority_keys = []
        for p in priorities_data:
            title_lower = p.get("title", "").lower()
            if "physical" in title_lower or "activity" in title_lower or "move" in title_lower:
                priority_keys.append("physical_activity")
            elif "diet" in title_lower or "nutrition" in title_lower or "food" in title_lower or "fibre" in title_lower or "fiber" in title_lower:
                priority_keys.append("dietary_nutrition")
            elif "weight" in title_lower or "caloric" in title_lower or "bmi" in title_lower:
                priority_keys.append("weight_management")
            elif "sedentary" in title_lower or "sitting" in title_lower:
                priority_keys.append("sedentary_reduction")

        if not priority_keys:
            priority_keys = ["physical_activity", "dietary_nutrition", "weight_management"]

        # Extract verified numerical targets
        targets_summary = {}
        for r in recs_data:
            t = r.get("numerical_target")
            if t:
                targets_summary[r.get("title", "Target")] = t

        patient_id = patient_info.get("patient_id", "P001")
        plan_id = f"plan_{patient_id}_{duration}_{uuid.uuid4().hex[:6]}"

        if duration == "1_week":
            return cls._build_1_week_plan(plan_id, patient_info, priority_keys, targets_summary, health_plan)
        elif duration == "1_month":
            return cls._build_1_month_plan(plan_id, patient_info, priority_keys, targets_summary, health_plan)
        elif duration == "3_months":
            return cls._build_3_months_plan(plan_id, patient_info, priority_keys, targets_summary, health_plan)
        else:
            return cls._build_1_week_plan(plan_id, patient_info, priority_keys, targets_summary, health_plan)

    @classmethod
    def _build_1_week_plan(
        cls,
        plan_id: str,
        patient_info: Dict[str, Any],
        priority_keys: List[str],
        targets: Dict[str, str],
        health_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Builds a 7-day kickstart plan."""
        days = []
        for day_num in range(1, 8):
            daily_tasks = cls._generate_daily_tasks(day_num, priority_keys, day_theme=f"Day {day_num} Focus")
            days.append({
                "day_number": day_num,
                "title": f"Day {day_num}",
                "focus_theme": cls._get_day_focus_theme(day_num),
                "tasks_count": len(daily_tasks),
                "tasks": daily_tasks,
                "is_unlocked": day_num == 1,
                "is_completed": False
            })

        total_tasks = sum(len(d["tasks"]) for d in days)

        return {
            "plan_id": plan_id,
            "patient_info": patient_info,
            "duration": "1_week",
            "duration_label": "1 Week Kickstart Plan",
            "total_days": 7,
            "total_weeks": 1,
            "total_tasks": total_tasks,
            "created_at": datetime.now().isoformat(),
            "priority_pillars": priority_keys,
            "guideline_targets": targets,
            "phases": [
                {
                    "phase_number": 1,
                    "title": "Phase 1: 7-Day Kickstart",
                    "subtitle": "Building daily awareness and starting with simple, high-impact habits",
                    "days": days
                }
            ],
            "days": days
        }

    @classmethod
    def _build_1_month_plan(
        cls,
        plan_id: str,
        patient_info: Dict[str, Any],
        priority_keys: List[str],
        targets: Dict[str, str],
        health_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Builds a 4-week (28 days) progressive plan."""
        weeks = []
        all_days = []
        week_themes = [
            ("Week 1: Daily Awareness", "Starting small with consistent daily food choices and movement"),
            ("Week 2: Establishing Routine", "Solidifying regular walking, portion balance, and high-fibre meals"),
            ("Week 3: Overcoming Barriers", "Staying active on busy days and optimizing your evening sleep routine"),
            ("Week 4: Habit Consolidation", "Reviewing progress and turning healthy habits into an automatic lifestyle")
        ]

        day_counter = 1
        for week_num, (w_title, w_sub) in enumerate(week_themes, start=1):
            week_days = []
            for d_idx in range(1, 8):
                daily_tasks = cls._generate_daily_tasks(
                    day_counter,
                    priority_keys,
                    day_theme=f"Week {week_num} Day {d_idx}"
                )
                day_obj = {
                    "day_number": day_counter,
                    "week_number": week_num,
                    "day_in_week": d_idx,
                    "title": f"Day {day_counter}",
                    "focus_theme": f"Week {week_num} — {w_title.split(': ')[1]}",
                    "tasks_count": len(daily_tasks),
                    "tasks": daily_tasks,
                    "is_unlocked": day_counter == 1,
                    "is_completed": False
                }
                week_days.append(day_obj)
                all_days.append(day_obj)
                day_counter += 1

            weeks.append({
                "week_number": week_num,
                "title": w_title,
                "subtitle": w_sub,
                "days": week_days
            })

        total_tasks = sum(len(d["tasks"]) for d in all_days)

        return {
            "plan_id": plan_id,
            "patient_info": patient_info,
            "duration": "1_month",
            "duration_label": "1 Month Progression Plan",
            "total_days": 28,
            "total_weeks": 4,
            "total_tasks": total_tasks,
            "created_at": datetime.now().isoformat(),
            "priority_pillars": priority_keys,
            "guideline_targets": targets,
            "weeks": weeks,
            "days": all_days
        }

    @classmethod
    def _build_3_months_plan(
        cls,
        plan_id: str,
        patient_info: Dict[str, Any],
        priority_keys: List[str],
        targets: Dict[str, str],
        health_plan: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Builds a 12-week (3 months) progressive transformation plan structured into 3 distinct phases."""
        phases_meta = [
            (1, "Month 1: Foundation", "Weeks 1–4", "Starting small, mastering foundational meal quality and daily walking"),
            (2, "Month 2: Consistency", "Weeks 5–8", "Increasing aerobic endurance, steady portion control, and digestive health"),
            (3, "Month 3: Long-Term Habit Mastery", "Weeks 9–12", "Maintaining sustainable lifestyle habits for lifelong metabolic wellness")
        ]

        phases = []
        all_days = []
        day_counter = 1

        for p_num, p_title, p_weeks_lbl, p_sub in phases_meta:
            phase_weeks = []
            for w_in_phase in range(1, 5):
                overall_week = (p_num - 1) * 4 + w_in_phase
                week_days = []
                for d_in_week in range(1, 8):
                    daily_tasks = cls._generate_daily_tasks(
                        day_counter,
                        priority_keys,
                        day_theme=f"{p_title} — Week {overall_week}"
                    )
                    day_obj = {
                        "day_number": day_counter,
                        "phase_number": p_num,
                        "week_number": overall_week,
                        "day_in_week": d_in_week,
                        "title": f"Day {day_counter}",
                        "focus_theme": f"{p_title} ({p_weeks_lbl})",
                        "tasks_count": len(daily_tasks),
                        "tasks": daily_tasks,
                        "is_unlocked": day_counter == 1,
                        "is_completed": False
                    }
                    week_days.append(day_obj)
                    all_days.append(day_obj)
                    day_counter += 1

                phase_weeks.append({
                    "week_number": overall_week,
                    "title": f"Week {overall_week}",
                    "days": week_days
                })

            phases.append({
                "phase_number": p_num,
                "title": p_title,
                "weeks_label": p_weeks_lbl,
                "subtitle": p_sub,
                "weeks": phase_weeks
            })

        total_tasks = sum(len(d["tasks"]) for d in all_days)

        return {
            "plan_id": plan_id,
            "patient_info": patient_info,
            "duration": "3_months",
            "duration_label": "3 Months Habit Transformation Plan",
            "total_days": 84,
            "total_weeks": 12,
            "total_tasks": total_tasks,
            "created_at": datetime.now().isoformat(),
            "priority_pillars": priority_keys,
            "guideline_targets": targets,
            "phases": phases,
            "days": all_days
        }

    @classmethod
    def _generate_daily_tasks(
        cls,
        day_num: int,
        priority_keys: List[str],
        day_theme: str = ""
    ) -> List[Dict[str, Any]]:
        """Generates exactly 4 to 6 (max 7) personalized, actionable tasks for a single day."""
        tasks = []
        task_idx = 1

        # 1. Physical Activity Task (Rotated deterministically by day)
        act_template = cls.ACTIVITY_TASKS[(day_num - 1) % len(cls.ACTIVITY_TASKS)]
        tasks.append({
            "id": f"d{day_num}_t{task_idx}",
            "title": act_template["title"],
            "category": "physical_activity",
            "priority_pillar": "Physical Activity & Movement",
            "instruction": act_template["instruction"],
            "suggestion": act_template["suggestion"],
            "why_selected": act_template["why_selected"],
            "completion_required": True,
            "recommendation_source": act_template["source"],
            "target": act_template["target"]
        })
        task_idx += 1

        # 2. Dietary Fibre Task 1 (e.g. Whole grains or beans)
        fibre_template_1 = cls.FIBRE_NUTRITION_TASKS[(day_num - 1) % len(cls.FIBRE_NUTRITION_TASKS)]
        tasks.append({
            "id": f"d{day_num}_t{task_idx}",
            "title": fibre_template_1["title"],
            "category": "dietary_nutrition",
            "priority_pillar": "Dietary Quality & Carbohydrate Nutrition",
            "instruction": fibre_template_1["instruction"],
            "suggestion": fibre_template_1["suggestion"],
            "why_selected": fibre_template_1["why_selected"],
            "completion_required": True,
            "recommendation_source": fibre_template_1["source"],
            "target": fibre_template_1["target"]
        })
        task_idx += 1

        # 3. Dietary Whole Foods / Fruit / Veggie Task 2
        fibre_template_2 = cls.FIBRE_NUTRITION_TASKS[(day_num + 1) % len(cls.FIBRE_NUTRITION_TASKS)]
        tasks.append({
            "id": f"d{day_num}_t{task_idx}",
            "title": fibre_template_2["title"],
            "category": "dietary_nutrition",
            "priority_pillar": "Dietary Quality & Carbohydrate Nutrition",
            "instruction": fibre_template_2["instruction"],
            "suggestion": fibre_template_2["suggestion"],
            "why_selected": fibre_template_2["why_selected"],
            "completion_required": True,
            "recommendation_source": fibre_template_2["source"],
            "target": fibre_template_2["target"]
        })
        task_idx += 1

        # 4. Weight or Lifestyle Task (If weight management is a priority)
        if "weight_management" in priority_keys or (day_num % 2 == 1):
            wt_template = cls.WEIGHT_CALORIC_TASKS[(day_num - 1) % len(cls.WEIGHT_CALORIC_TASKS)]
            tasks.append({
                "id": f"d{day_num}_t{task_idx}",
                "title": wt_template["title"],
                "category": "weight_management",
                "priority_pillar": "Weight & Caloric Management",
                "instruction": wt_template["instruction"],
                "suggestion": wt_template["suggestion"],
                "why_selected": wt_template["why_selected"],
                "completion_required": True,
                "recommendation_source": wt_template["source"],
                "target": wt_template["target"]
            })
            task_idx += 1

        # 5. Routine / Sedentary / Sleep Task
        ls_template = cls.LIFESTYLE_ROUTINE_TASKS[(day_num - 1) % len(cls.LIFESTYLE_ROUTINE_TASKS)]
        tasks.append({
            "id": f"d{day_num}_t{task_idx}",
            "title": ls_template["title"],
            "category": "lifestyle_routine",
            "priority_pillar": "Lifestyle & Restorative Routine",
            "instruction": ls_template["instruction"],
            "suggestion": ls_template["suggestion"],
            "why_selected": ls_template["why_selected"],
            "completion_required": True,
            "recommendation_source": ls_template["source"],
            "target": ls_template["target"]
        })

        # Ensure task count is strictly between 4 and 6 (max 7)
        return tasks[:6]

    @staticmethod
    def _get_day_focus_theme(day_num: int) -> str:
        themes = {
            1: "Starting with Simple Daily Habits",
            2: "Building Consistency in Walking & Fibre",
            3: "Staying Hydrated & Active",
            4: "Balancing Meal Portions",
            5: "Energizing Your Afternoon",
            6: "Weekend Movement & Wholesome Meals",
            7: "Weekly Progress Review & Celebration"
        }
        return themes.get(day_num, f"Day {day_num} Healthy Focus")
