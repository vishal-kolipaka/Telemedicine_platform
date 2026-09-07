"""
personalization_engine.py — Deterministic Personalization & Priority Engine

Evaluates structured patient context, disease risks, biomarker gaps, wearable telemetry,
and microbiome diversity to select the Top 2–3 personalized priority pillars.

Features:
- 100% deterministic and explainable priority scoring.
- Connects patient-specific context directly to priority selection.
- Selects only the most relevant pillars (prevents recommendation dumps).
- Strictly enforces microbiome general dietary boundary.
"""

from __future__ import annotations

from typing import Dict, Any, List, Tuple


class PersonalizationEngine:
    """Deterministic priority and recommendation pillar selection engine."""

    # Governed pillar categories in knowledge_base
    PILLARS = {
        "physical_activity": {
            "name": "Physical Activity & Movement",
            "category": "physical_activity",
            "condition_focus": ["Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk", "Metabolic_Syndrome", "NAFLD"]
        },
        "weight_management": {
            "name": "Weight & Caloric Management",
            "category": "weight_management",
            "condition_focus": ["High_Adiposity_Risk", "Prediabetes", "Type2_Diabetes", "Metabolic_Syndrome", "NAFLD"]
        },
        "dietary_nutrition": {
            "name": "Dietary Quality & Carbohydrate Nutrition",
            "category": "dietary_nutrition",
            "condition_focus": ["Type2_Diabetes", "Prediabetes", "Metabolic_Syndrome", "NAFLD", "High_Adiposity_Risk"]
        },
        "sedentary_reduction": {
            "name": "Sedentary Time Interruption",
            "category": "physical_activity",
            "condition_focus": ["Type2_Diabetes", "Prediabetes", "High_Adiposity_Risk", "Metabolic_Syndrome"]
        },
        "microbiome_support_diet": {
            "name": "Dietary Plant Diversity & Prebiotic Fiber",
            "category": "dietary_nutrition",
            "condition_focus": ["Type2_Diabetes", "Prediabetes", "Metabolic_Syndrome", "NAFLD"]
        }
    }

    @staticmethod
    def select_priorities(patient_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Deterministically evaluates patient context and ranks top 2–3 priorities.

        Parameters
        ----------
        patient_context : dict
            Output from PatientContextBuilder.build_context().

        Returns
        -------
        list[dict]
            Ordered list of top priorities (max 3), each containing:
            'rank', 'pillar_key', 'category', 'title', 'reason', 'search_query', 'target_condition'.
        """
        contributing = patient_context.get("contributing_factors", [])
        disease_results = patient_context.get("disease_results", [])
        raw_features = patient_context.get("raw_patient_features", {})

        # Identify positive or highest risk disease
        positive_diseases = [d for d in disease_results if d.get("prediction") == 1]
        primary_disease = positive_diseases[0]["disease"] if positive_diseases else (
            disease_results[0]["disease"] if disease_results else "Type2_Diabetes"
        )

        # Calculate evidence-driven priority scores
        pillar_scores: Dict[str, float] = {k: 0.0 for k in PersonalizationEngine.PILLARS}
        pillar_reasons: Dict[str, List[str]] = {k: [] for k in PersonalizationEngine.PILLARS}
        pillar_queries: Dict[str, str] = {k: "" for k in PersonalizationEngine.PILLARS}

        # ── 1. Evaluate Clinical Biomarker Drivers ─────────────────────────────
        for factor in contributing:
            param = factor.get("parameter", "")
            status = factor.get("status", "")
            val = factor.get("patient_value")
            unit = factor.get("unit", "")
            imp = factor.get("importance_score", 0.0)

            if param in ("Fasting_Blood_Glucose", "HbA1c") and status == "above_expected_range":
                pillar_scores["physical_activity"] += 3.0 + imp * 5
                pillar_scores["dietary_nutrition"] += 3.5 + imp * 5
                pillar_reasons["physical_activity"].append(
                    f"Your fasting glucose/HbA1c ({val} {unit}) is above the expected range, and regular aerobic activity helps muscles absorb glucose independently of insulin."
                )
                pillar_reasons["dietary_nutrition"].append(
                    f"Your glycemic markers ({val} {unit}) indicate that focusing on high-fiber whole foods and reducing refined carbohydrates will support glycemic regulation."
                )

            elif param in ("BMI", "Waist_Circumference", "Weight") and status == "above_expected_range":
                pillar_scores["weight_management"] += 4.0 + imp * 5
                pillar_scores["dietary_nutrition"] += 2.5 + imp * 3
                pillar_reasons["weight_management"].append(
                    f"Your BMI ({val} {unit}) is a key contributing factor, and achieving a gradual 5% to 7% weight reduction substantially improves insulin sensitivity and metabolic health."
                )

            elif param in ("Triglycerides", "HDL", "LDL") and status in ("above_expected_range", "below_expected_range"):
                pillar_scores["dietary_nutrition"] += 2.5 + imp * 3
                pillar_scores["physical_activity"] += 2.0 + imp * 2
                pillar_reasons["dietary_nutrition"].append(
                    f"Your lipid profile ({param} {val} {unit}) will benefit from replacing saturated fats with healthy unsaturated plant oils and increasing dietary fiber."
                )

            elif param in ("ALT", "AST") and status == "above_expected_range":
                pillar_scores["dietary_nutrition"] += 3.5 + imp * 4
                pillar_scores["weight_management"] += 3.0 + imp * 3
                pillar_reasons["dietary_nutrition"].append(
                    f"Your liver enzymes ({param} {val} {unit}) suggest metabolic stress on the liver, where adopting a Mediterranean dietary pattern has proven hepatic protective benefits."
                )

        # ── 2. Evaluate Wearable Telemetry Gaps ────────────────────────────────
        daily_steps = raw_features.get("Daily_Steps")
        if daily_steps is not None and isinstance(daily_steps, (int, float)) and daily_steps < 7500:
            pillar_scores["physical_activity"] += 3.5
            pillar_reasons["physical_activity"].append(
                f"Your daily step count ({int(daily_steps)} steps/day) is below recommended activity levels, making daily walking an accessible and high-impact starting point."
            )

        sed_min = raw_features.get("Sedentary_Minutes")
        if sed_min is not None and isinstance(sed_min, (int, float)) and sed_min > 480:
            pillar_scores["sedentary_reduction"] += 3.0
            pillar_reasons["sedentary_reduction"].append(
                f"Your logged daily sitting time ({int(sed_min)} minutes) is elevated; interrupting sedentary periods with light movement produces measurable metabolic benefits."
            )

        mod_act = raw_features.get("Moderate_Activity_Minutes")
        if mod_act is not None and isinstance(mod_act, (int, float)) and mod_act < 150:
            pillar_scores["physical_activity"] += 4.0
            pillar_reasons["physical_activity"].append(
                f"Your weekly moderate physical activity ({int(mod_act)} minutes) is lower than the recommended 150-minute weekly target."
            )

        # ── 3. Evaluate Gut Microbiome Context (Non-Taxon Fiber Focus) ────────
        # Check if gut features are present in contributing factors
        gut_factors = [f for f in contributing if f.get("parameter", "").startswith("k__") or "gut" in f.get("parameter", "").lower()]
        if gut_factors:
            pillar_scores["microbiome_support_diet"] += 2.5
            pillar_reasons["microbiome_support_diet"].append(
                "Your gut microbiome profile indicates that increasing overall dietary plant diversity and natural prebiotic fiber can support intestinal microbial metabolic health."
            )

        # ── 4. Formulate Evidence Search Queries ──────────────────────────────
        pillar_queries["physical_activity"] = "moderate intensity aerobic physical activity 150 minutes per week brisk walking"
        pillar_queries["weight_management"] = "5% to 7% weight loss reduce daily calories by 500 to 750 kcal energy deficit"
        pillar_queries["dietary_nutrition"] = "dietary fiber at least 25 g per day whole grains vegetables pulses Mediterranean diet"
        pillar_queries["sedentary_reduction"] = "limit sedentary time replace sedentary sitting with light physical activity"
        pillar_queries["microbiome_support_diet"] = "naturally occurring dietary fibre whole grains pulses prebiotic diversity"

        # ── 5. Rank and Select Top 2–3 Pillars (No Overwhelming Dump) ──────────
        ranked_pillars = sorted(pillar_scores.items(), key=lambda x: x[1], reverse=True)

        selected_priorities = []
        rank = 1
        for p_key, score in ranked_pillars:
            if score <= 0.0:
                continue

            meta = PersonalizationEngine.PILLARS[p_key]
            # Construct a clear, empathetic reason
            reasons = pillar_reasons[p_key]
            consolidated_reason = " ".join(reasons) if reasons else (
                f"Supporting regular {meta['name'].lower()} provides direct cardiovascular and metabolic risk reduction for your profile."
            )

            selected_priorities.append({
                "rank": rank,
                "pillar_key": p_key,
                "category": meta["category"],
                "title": meta["name"],
                "priority_score": round(score, 2),
                "reason": consolidated_reason,
                "search_query": pillar_queries[p_key],
                "target_condition": primary_disease
            })
            rank += 1

            if len(selected_priorities) >= 3:
                break

        # Fallback if all scores were zero (ensure at least physical activity & diet)
        if not selected_priorities:
            selected_priorities = [
                {
                    "rank": 1,
                    "pillar_key": "physical_activity",
                    "category": "physical_activity",
                    "title": "Physical Activity & Movement",
                    "priority_score": 1.0,
                    "reason": "Regular moderate physical activity is a foundational pillar for maintaining healthy glucose regulation and cardiovascular fitness.",
                    "search_query": pillar_queries["physical_activity"],
                    "target_condition": primary_disease
                },
                {
                    "rank": 2,
                    "pillar_key": "dietary_nutrition",
                    "category": "dietary_nutrition",
                    "title": "Dietary Quality & Nutrition",
                    "priority_score": 1.0,
                    "reason": "Consuming a balanced, fiber-rich dietary pattern supports metabolic homeostasis.",
                    "search_query": pillar_queries["dietary_nutrition"],
                    "target_condition": primary_disease
                }
            ]

        return selected_priorities
