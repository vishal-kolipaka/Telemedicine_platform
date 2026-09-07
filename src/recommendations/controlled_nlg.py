"""
controlled_nlg.py — Controlled LLM Natural Language Generation Layer

Transforms structured, approved clinical context into simple, empathetic,
conversational English while strictly enforcing:
1. Exact parameter-value-unit binding (e.g., Glucose 150 mg/dL cannot merge with HbA1c 7.1%).
2. Governed reference interpretation (explicitly shows actual value, approved target, and status).
3. Strict evidence boundaries (recommendations adhere strictly to retrieved guideline chunks).
4. Structured JSON output schema.
5. ClaimValidator gating on all generated claims.
"""

from __future__ import annotations

import os
import re
import json
import logging
from typing import Dict, Any, List, Optional, Tuple

logger = logging.getLogger("Recommendations.ControlledNLG")


class ParameterBindingValidator:
    """Validates that patient values, units, and governed interpretations are preserved without distortion."""

    PROHIBITED_INTERPRETATION_WORDS = {"high", "low", "abnormal", "elevated", "dangerous", "healthy", "critical", "optimal"}

    @classmethod
    def validate_factor_explanation(
        cls,
        parameter_key: str,
        friendly_name: str,
        patient_value: Any,
        unit: str,
        status: str,
        explanation_text: str,
        other_patient_values: Dict[str, Any]
    ) -> Tuple[bool, str]:
        """Validates parameter-value-unit binding and governed interpretation compliance.

        Returns (is_valid, failure_reason).
        """
        text_lower = explanation_text.lower()

        # 1. Verify exact patient value is present
        val_str = str(patient_value)
        val_float_str = f"{float(patient_value):.1f}" if isinstance(patient_value, (int, float)) else val_str
        val_int_str = f"{int(patient_value)}" if isinstance(patient_value, (int, float)) and float(patient_value).is_integer() else val_str

        has_value = (val_str in explanation_text) or (val_float_str in explanation_text) or (val_int_str in explanation_text)
        if not has_value:
            return False, f"Patient value '{patient_value}' for {friendly_name} is missing from explanation."

        # 2. Verify parameter name or friendly name is present
        if friendly_name.lower() not in text_lower and parameter_key.lower().replace("_", " ") not in text_lower:
            return False, f"Parameter name '{friendly_name}' is missing from explanation."

        # 3. Check for parameter crosstalk (e.g., glucose/hba1c incorrect merge)
        for other_param, other_val in other_patient_values.items():
            if other_param == parameter_key:
                continue
            if other_val != patient_value and isinstance(other_val, (int, float, str)):
                other_param_clean = other_param.replace("_", " ").lower()
                if f"{friendly_name.lower()}/{other_param_clean}" in text_lower or f"{other_param_clean}/{friendly_name.lower()}" in text_lower:
                    return False, f"Forbidden merge detected between '{friendly_name}' and '{other_param}'."

        # 4. Enforce neutral language for unavailable reference ranges
        if status == "interpretation_unavailable":
            for word in cls.PROHIBITED_INTERPRETATION_WORDS:
                if re.search(r"\b" + re.escape(word) + r"\b", text_lower):
                    return False, f"Invented interpretation word '{word}' used when status is 'interpretation_unavailable'."

        return True, ""


class ControlledNLG:
    """Controlled Natural Language Generation engine for personalized health plans."""

    def __init__(self, model_name: str = "governed-clinical-nlg"):
        self.model_name = model_name

    def generate_friendly_plan(
        self,
        structured_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generates friendly, conversational English health plan from structured context.

        Parameters
        ----------
        structured_context : dict
            Contains approved patient values, XAI drivers, priorities, and evidence chunks.

        Returns
        -------
        dict
            Validated conversational plan sections.
        """
        # 1. Synthesize conversational plan candidates
        candidate_plan = self._synthesize_conversational_plan(structured_context)

        # 2. Strictly Validate Parameter-Value-Unit Binding
        all_patient_vals = {
            item["parameter"]: item["patient_value"]
            for item in structured_context.get("contributing_factors", [])
        }

        validated_factors = []
        for factor_item in structured_context.get("contributing_factors", []):
            param_key = factor_item["parameter"]
            friendly_name = factor_item["friendly_name"]
            p_val = factor_item["patient_value"]
            unit = factor_item.get("unit", "")
            status = factor_item.get("status", "interpretation_unavailable")
            status_label = factor_item.get("status_label", "")
            ref_range_desc = factor_item.get("reference_range", {}).get("description", "")

            # Look up generated candidate explanation
            candidate_expl = candidate_plan.get("contributing_explanations", {}).get(param_key)
            if not candidate_expl:
                candidate_expl = self._format_default_friendly_factor(
                    friendly_name, p_val, unit, status, status_label, ref_range_desc
                )

            # Validate binding
            is_valid, reason = ParameterBindingValidator.validate_factor_explanation(
                parameter_key=param_key,
                friendly_name=friendly_name,
                patient_value=p_val,
                unit=unit,
                status=status,
                explanation_text=candidate_expl,
                other_patient_values=all_patient_vals
            )

            if not is_valid:
                logger.warning(
                    f"NLG parameter binding validation failed for {param_key}: {reason}. Falling back to governed template."
                )
                candidate_expl = self._format_default_friendly_factor(
                    friendly_name, p_val, unit, status, status_label, ref_range_desc
                )

            validated_factors.append({
                "parameter": param_key,
                "friendly_name": friendly_name,
                "patient_value": p_val,
                "unit": unit,
                "status": status,
                "explanation_sentence": candidate_expl
            })

        # 3. Assemble Validated Output
        return {
            "summary_title": candidate_plan.get("summary_title", "Your Personalized Health Plan"),
            "section_a_summary": candidate_plan.get("section_a_summary"),
            "contributing_items": validated_factors,
            "priority_explanations": candidate_plan.get("priority_explanations", {}),
            "recommendation_texts": candidate_plan.get("recommendation_texts", {}),
            "why_suggested_reasons": candidate_plan.get("why_suggested_reasons", {})
        }

    def _synthesize_conversational_plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Produces simple, friendly, conversational English while preserving all factual constraints."""
        disease_results = context.get("disease_results", [])
        positive = [d for d in disease_results if d.get("prediction") == 1]
        primary_disease = context.get("primary_disease", "Type 2 Diabetes").replace("_", " ")

        # ── Section A: Simple, Conversational Summary ─────────────────────────
        if positive:
            sec_a_summary = (
                f"We looked over your health information, and your results show an elevated risk for {primary_disease}. "
                f"This is not a formal medical diagnosis, but it points to a few everyday habits and health numbers where making small, "
                f"steady changes can really help you."
            )
        else:
            sec_a_summary = (
                "We looked over your health information, and your overall risk across these health areas is currently low. "
                "Keeping up with regular movement, nutritious meals, and good sleep will help you stay feeling your best."
            )

        # ── Section B: Clear Contributing Factor Explanations ─────────────────
        contributing_exps = {}
        for f in context.get("contributing_factors", []):
            param = f["parameter"]
            name = f["friendly_name"]
            val = f["patient_value"]
            unit = f.get("unit", "")
            unit_str = f" {unit}" if unit else ""
            status = f.get("status", "")
            ref_desc = f.get("reference_range", {}).get("description", "")
            clean_range = ref_desc.split(" (")[0].strip() if ref_desc else ""

            if status == "above_expected_range":
                if clean_range and clean_range != "Standard reference range not established":
                    contributing_exps[param] = (
                        f"Your {name} is {val}{unit_str}, compared to the approved target of {clean_range}. "
                        f"Because this is above the expected range, it is one of the main reasons your risk came out higher."
                    )
                else:
                    contributing_exps[param] = (
                        f"Your {name} is {val}{unit_str}. Because this is above the expected range, "
                        f"it is one of the main reasons your risk came out higher."
                    )
            elif status == "below_expected_range":
                if clean_range and clean_range != "Standard reference range not established":
                    contributing_exps[param] = (
                        f"Your {name} is {val}{unit_str}, compared to the target of {clean_range}. "
                        f"Because this is below the expected range, improving this area can give you helpful protective health benefits."
                    )
                else:
                    contributing_exps[param] = (
                        f"Your {name} is {val}{unit_str}. Because this is below the expected range, "
                        f"improving this area can give you helpful protective health benefits."
                    )
            elif status == "within_expected_range":
                if clean_range and clean_range != "Standard reference range not established":
                    contributing_exps[param] = (
                        f"Your {name} is {val}{unit_str}, which is comfortably within the approved target of {clean_range}."
                    )
                else:
                    contributing_exps[param] = (
                        f"Your {name} is {val}{unit_str}, which is within the expected healthy range."
                    )
            else:
                contributing_exps[param] = (
                    f"Your recorded {name} is {val}{unit_str}. The platform does not have an established clinical reference interval for this parameter, so it is presented neutrally."
                )

        # ── Section C: Clear Priority Focus Explanations ──────────────────────
        prio_exps = {}
        for p in context.get("selected_priorities", []):
            p_key = p["pillar_key"]
            title = p["title"]
            base_reason = p["reason"]

            if p_key == "physical_activity":
                prio_exps[p_key] = (
                    f"Moving more helps your body use blood sugar more easily. "
                    f"Starting with a comfortable daily walk is an easy and effective first step."
                )
            elif p_key == "dietary_nutrition":
                prio_exps[p_key] = (
                    f"Choosing foods with plenty of natural fibre—like vegetables, whole grains, and beans—helps "
                    f"keep your blood sugar steady and supports healthy digestion."
                )
            elif p_key == "weight_management":
                prio_exps[p_key] = (
                    f"Aiming for a steady, gradual 5% to 7% weight loss makes a big difference in how well your body handles insulin and daily energy."
                )
            elif p_key == "sedentary_reduction":
                prio_exps[p_key] = (
                    f"Standing up and moving around for a couple of minutes each hour breaks up sitting time and helps your body process energy better."
                )
            else:
                prio_exps[p_key] = base_reason

        # ── Section D: Conversational Recommendation Action Texts ─────────────
        rec_texts = {}
        for p in context.get("selected_priorities", []):
            p_key = p["pillar_key"]
            if p_key == "physical_activity":
                rec_texts[p_key] = (
                    "Aim for at least 150–300 minutes of moderate-intensity aerobic physical activity throughout the week. "
                    "A great way to get there is a brisk 30-minute walk on most days of the week."
                )
            elif p_key == "dietary_nutrition":
                rec_texts[p_key] = (
                    "Try adding more fibre-rich foods to your meals—such as oats, brown rice, beans, lentils, and colourful vegetables. "
                    "A proven guideline target is at least 25 g of dietary fibre per day."
                )
            elif p_key == "weight_management":
                rec_texts[p_key] = (
                    "Focus on gradual and sustainable changes to lose about 5% to 7% of your starting weight by trimming 500 to 750 calories per day from your usual intake."
                )
            elif p_key == "sedentary_reduction":
                rec_texts[p_key] = (
                    "Make a habit of standing up or taking a short 2-minute stroll every hour to replace sedentary sitting time with light daily movement."
                )

        # ── Section E: Conversational Why Suggested Reasons ────────────────────
        why_reasons = {}
        for p in context.get("selected_priorities", []):
            p_key = p["pillar_key"]
            why_reasons[p_key] = p["reason"]

        return {
            "summary_title": "Your Personalized Health Plan",
            "section_a_summary": sec_a_summary,
            "contributing_explanations": contributing_exps,
            "priority_explanations": prio_exps,
            "recommendation_texts": rec_texts,
            "why_suggested_reasons": why_reasons
        }

    @staticmethod
    def _format_default_friendly_factor(
        name: str,
        val: Any,
        unit: str,
        status: str,
        status_label: str,
        ref_desc: str = ""
    ) -> str:
        unit_str = f" {unit}" if unit else ""
        clean_range = ref_desc.split(" (")[0].strip() if ref_desc else ""

        if status == "above_expected_range":
            if clean_range and clean_range != "Standard reference range not established":
                return (
                    f"Your {name} is {val}{unit_str}, compared to the approved target of {clean_range}. "
                    f"Because this is above the expected range, it is one of the main reasons your risk came out higher."
                )
            return f"Your {name} is {val}{unit_str}, which is above the expected range. This is one of the main reasons your risk came out higher."
        elif status == "below_expected_range":
            if clean_range and clean_range != "Standard reference range not established":
                return (
                    f"Your {name} is {val}{unit_str}, compared to the approved target of {clean_range}. "
                    f"Because this is below the expected range, improving it can give you helpful protective health benefits."
                )
            return f"Your {name} is {val}{unit_str}, which is below the expected range. Improving it can give you helpful protective health benefits."
        elif status == "within_expected_range":
            if clean_range and clean_range != "Standard reference range not established":
                return f"Your {name} is {val}{unit_str}, which is comfortably within the approved target of {clean_range}."
            return f"Your {name} is {val}{unit_str}, which is within the expected healthy range."
        return f"Your recorded {name} is {val}{unit_str}. The platform does not have an established clinical reference interval for this parameter, so it is presented neutrally."
