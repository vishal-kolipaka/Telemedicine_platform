"""
plan_generator.py — Governed Personalized Recommendation Generation & Plan Assembly

Coordinates the complete clinical recommendation bridge:
  Fusion + XAI + Patient Values
          ↓
  Patient Explanation Context (PatientContextBuilder)
          ↓
  Personalization & Priority Engine (PersonalizationEngine)
          ↓
  Recommendation Pillar Selection
          ↓
  EvidenceRetriever
          ↓
  Authorized Evidence Chunks
          ↓
  Controlled Natural Language Generation (ControlledNLG)
          ↓
  Parameter-Value-Unit Binding Validator
          ↓
  ClaimValidator (5-Layer Gatekeeper)
          ↓
  Final User-Friendly Personalized Health Plan
"""

from __future__ import annotations

import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple

from .patient_context_builder import PatientContextBuilder
from .personalization_engine import PersonalizationEngine
from .evidence_retriever import EvidenceRetriever
from .claim_validator import ClaimValidator
from .controlled_nlg import ControlledNLG, ParameterBindingValidator

logger = logging.getLogger("Recommendations.PlanGenerator")


class PlanGenerator:
    """Orchestrates governed, validated personalized health plan generation."""

    ZERO_EVIDENCE_NOTICE = (
        "We could not retrieve sufficient condition-specific guideline evidence to generate "
        "a personalized recommendation from the current knowledge base. Please consult a qualified "
        "healthcare professional regarding these findings."
    )

    def __init__(
        self,
        retriever: Optional[EvidenceRetriever] = None,
        validator: Optional[ClaimValidator] = None,
        nlg: Optional[ControlledNLG] = None,
    ):
        self.retriever = retriever if retriever is not None else EvidenceRetriever()
        self.validator = validator if validator is not None else ClaimValidator()
        self.nlg = nlg if nlg is not None else ControlledNLG()

    def generate_personalized_plan(
        self,
        patient_features: Dict[str, Any],
        xai_explanations: Dict[str, Any],
        disease_results: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Generates a complete, validated personalized health plan for the patient.

        Parameters
        ----------
        patient_features : dict
            Merged raw/mapped clinical, wearable, and gut feature values.
        xai_explanations : dict
            Local feature attributions from XAIEngine.
        disease_results : list[dict]
            Output list of disease predictions and risk scores from Fusion V2.

        Returns
        -------
        dict
            Structured and formatted user-friendly health plan with 5 sections.
        """
        # ── 1. Build Governed Patient Explanation Context ──────────────────────
        context = PatientContextBuilder.build_context(
            patient_features=patient_features,
            xai_explanations=xai_explanations,
            disease_results=disease_results,
        )

        # ── 2. Deterministically Select Priority Pillars ──────────────────────
        priorities = PersonalizationEngine.select_priorities(context)
        context["selected_priorities"] = priorities

        # ── 3. Retrieve Evidence and Formulate Governed Recommendations ────────
        recommendation_items = []
        all_retrieved_chunk_ids = []
        approved_evidence_map = {}

        for p_info in priorities:
            p_key = p_info["pillar_key"]
            category = p_info["category"]
            target_cond = p_info["target_condition"]
            query = p_info["search_query"]

            # Query EvidenceRetriever
            retrieved = self.retriever.retrieve(
                query=query,
                target_condition=target_cond,
                recommendation_category=category,
                recommendation_only=True,
                top_k=2
            )

            if not retrieved:
                # Zero evidence fallback for this pillar: bypass LLM completely
                recommendation_items.append({
                    "pillar_key": p_key,
                    "title": p_info["title"],
                    "priority_rank": p_info["rank"],
                    "status": "ZERO_EVIDENCE_FALLBACK",
                    "actionable_recommendation": self.ZERO_EVIDENCE_NOTICE,
                    "numerical_target": None,
                    "why_suggested": p_info["reason"],
                    "supporting_chunk_ids": [],
                    "validation_passed": True
                })
                continue

            chunk_ids = [c["chunk_id"] for c in retrieved]
            all_retrieved_chunk_ids.extend(chunk_ids)
            primary_chunk = retrieved[0]
            approved_evidence_map[p_key] = {
                "chunk": primary_chunk,
                "retrieved_chunk_ids": chunk_ids,
                "target_condition": target_cond,
                "category": category,
                "p_info": p_info
            }

        # ── 4. Controlled Natural Language Generation Layer ───────────────────
        nlg_output = self.nlg.generate_friendly_plan(context)

        # ── 5. Validate Candidate Recommendations with ClaimValidator ─────────
        for p_key, ev_data in approved_evidence_map.items():
            primary_chunk = ev_data["chunk"]
            chunk_ids = ev_data["retrieved_chunk_ids"]
            target_cond = ev_data["target_condition"]
            category = ev_data["category"]
            p_info = ev_data["p_info"]

            # Obtain candidate recommendation text from NLG or grounded generator
            candidate_text = nlg_output.get("recommendation_texts", {}).get(p_key)
            num_target = None
            if not candidate_text:
                candidate_text, num_target = self._generate_grounded_recommendation_text(
                    pillar_key=p_key,
                    primary_chunk=primary_chunk,
                    patient_context=context
                )
            else:
                _, num_target = self._generate_grounded_recommendation_text(
                    pillar_key=p_key,
                    primary_chunk=primary_chunk,
                    patient_context=context
                )

            # Construct claim object for validation
            candidate_claim = {
                "claim_id": f"REC_{p_key.upper()}_{p_info['rank']}",
                "claim_text": candidate_text,
                "claim_type": "recommendation",
                "category": category,
                "supporting_chunk_ids": [primary_chunk["chunk_id"]]
            }

            # Run through ClaimValidator (5 layers)
            val_res = self.validator.validate_claim(
                claim=candidate_claim,
                retrieved_chunk_ids=chunk_ids,
                current_condition=target_cond
            )

            if val_res["is_valid"]:
                recommendation_items.append({
                    "pillar_key": p_key,
                    "title": p_info["title"],
                    "priority_rank": p_info["rank"],
                    "status": "VALIDATED",
                    "actionable_recommendation": candidate_text,
                    "numerical_target": num_target,
                    "why_suggested": p_info["reason"],
                    "supporting_chunk_ids": [primary_chunk["chunk_id"]],
                    "validation_passed": True,
                    "support_type": val_res.get("support_type", "DIRECT")
                })
            else:
                logger.warning(
                    "Candidate claim failed validation: %s (%s). Attempting conservative fallback.",
                    val_res.get("rejection_code"), val_res.get("reason")
                )
                # Attempt conservative verbatim fallback from primary chunk
                conservative_text = self._generate_conservative_chunk_text(primary_chunk)
                conservative_claim = {
                    "claim_id": f"REC_{p_key.upper()}_CONSERVATIVE",
                    "claim_text": conservative_text,
                    "claim_type": "recommendation",
                    "category": category,
                    "supporting_chunk_ids": [primary_chunk["chunk_id"]]
                }
                cons_val_res = self.validator.validate_claim(
                    claim=conservative_claim,
                    retrieved_chunk_ids=chunk_ids,
                    current_condition=target_cond
                )
                if cons_val_res["is_valid"]:
                    recommendation_items.append({
                        "pillar_key": p_key,
                        "title": p_info["title"],
                        "priority_rank": p_info["rank"],
                        "status": "VALIDATED_CONSERVATIVE",
                        "actionable_recommendation": conservative_text,
                        "numerical_target": num_target,
                        "why_suggested": p_info["reason"],
                        "supporting_chunk_ids": [primary_chunk["chunk_id"]],
                        "validation_passed": True,
                        "support_type": "DIRECT"
                    })
                else:
                    logger.error("Conservative fallback also failed validation. Dropping recommendation.")

        # Sort recommendations by priority rank
        recommendation_items.sort(key=lambda x: x.get("priority_rank", 99))

        # ── 6. Assemble the 5 User-Friendly Output Sections ───────────────────
        section_a = self._assemble_section_a_results(context, nlg_output)
        section_b = self._assemble_section_b_contributions(nlg_output)
        section_c = self._assemble_section_c_focus_areas(priorities, nlg_output)
        section_d = self._assemble_section_d_recommendations(recommendation_items)
        section_e = self._assemble_section_e_why_suggested(recommendation_items)

        return {
            "summary_title": nlg_output.get("summary_title", "Your Personalized Health Plan"),
            "primary_disease_evaluated": context["primary_disease"],
            "sections": {
                "section_a_your_results": section_a,
                "section_b_what_is_contributing": section_b,
                "section_c_what_to_focus_on_first": section_c,
                "section_d_personalized_recommendations": section_d,
                "section_e_why_suggested": section_e
            },
            "recommendation_items": recommendation_items,
            "patient_context": context,
            "selected_priorities": priorities,
            "total_validated_recommendations": len([r for r in recommendation_items if r["validation_passed"]])
        }

    # ── NATURAL LANGUAGE GENERATION HELPERS ────────────────────────────────────

    def _assemble_section_a_results(self, context: Dict[str, Any], nlg_output: Dict[str, Any]) -> Dict[str, Any]:
        """Assembles Section A: Your Results."""
        disease_results = context["disease_results"]
        summary_text = nlg_output.get("section_a_summary")
        if not summary_text:
            positive = [d for d in disease_results if d.get("prediction") == 1]
            if positive:
                primary_d = positive[0]["disease"].replace("_", " ")
                summary_text = (
                    f"Based on the health information and assessment data analyzed, your predicted risk for {primary_d} "
                    f"is elevated. This assessment is not a formal medical diagnosis, but indicates that specific metabolic, "
                    f"lifestyle, or physical factors could benefit from personalized attention and proactive healthy habit changes."
                )
            else:
                summary_text = (
                    "Based on the health information analyzed, your assessed risk across target cardiometabolic areas "
                    "is currently low. Continuing to maintain balanced nutrition, regular physical activity, and healthy sleep "
                    "will support your long-term health."
                )

        return {
            "title": "A. Your Assessment Summary",
            "body": summary_text,
            "evaluated_conditions": [
                {
                    "disease": d["disease"],
                    "risk_level": d.get("risk_level", "Low"),
                    "probability_percentage": f"{d.get('probability', 0.0) * 100:.2f}%"
                }
                for d in disease_results
            ]
        }

    def _assemble_section_b_contributions(self, nlg_output: Dict[str, Any]) -> Dict[str, Any]:
        """Assembles Section B: What Is Contributing to This?"""
        items = nlg_output.get("contributing_items", [])
        return {
            "title": "B. Key Factors Contributing to Your Results",
            "body": "Here is an easy-to-understand breakdown of the key factors from your health data that influenced this assessment:",
            "contributing_items": items[:5]
        }

    def _assemble_section_c_focus_areas(self, priorities: List[Dict[str, Any]], nlg_output: Dict[str, Any]) -> Dict[str, Any]:
        """Assembles Section C: What Should You Focus On First?"""
        prio_exps = nlg_output.get("priority_explanations", {})
        priority_texts = []
        for p in priorities:
            p_key = p["pillar_key"]
            friendly_text = prio_exps.get(p_key) or p["reason"]
            priority_texts.append({
                "rank": p["rank"],
                "title": p["title"],
                "explanation": f"Priority {p['rank']}: {p['title']}. {friendly_text}"
            })

        intro = (
            "You do not need to change everything all at once. Based on your specific health profile, "
            "we have organized your focus areas into a clear, stepwise priority list so you can take steady, manageable steps."
        )

        return {
            "title": "C. What Should You Focus On First?",
            "intro": intro,
            "priorities": priority_texts
        }

    def _assemble_section_d_recommendations(self, recommendation_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assembles Section D: Your Personalized Recommendations."""
        recs = []
        for r in recommendation_items:
            recs.append({
                "title": r["title"],
                "priority_rank": r["priority_rank"],
                "recommendation_text": r["actionable_recommendation"],
                "numerical_target": r.get("numerical_target")
            })

        return {
            "title": "D. Your Actionable Recommendations",
            "intro": "These recommendations are grounded in verified clinical guidelines tailored to your results:",
            "recommendations": recs
        }

    def _assemble_section_e_why_suggested(self, recommendation_items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assembles Section E: Why This Recommendation Was Suggested."""
        why_list = []
        for r in recommendation_items:
            why_list.append({
                "title": r["title"],
                "reason": r["why_suggested"],
                "evidence_source": "Verified Clinical Practice Guidelines"
            })

        return {
            "title": "E. Why These Actions Were Chosen for You",
            "items": why_list
        }

    # ── GROUNDED GENERATION HELPERS ────────────────────────────────────────────

    def _generate_grounded_recommendation_text(
        self,
        pillar_key: str,
        primary_chunk: Dict[str, Any],
        patient_context: Dict[str, Any]
    ) -> Tuple[str, Optional[str]]:
        """Generates an empathetic recommendation strictly adhering to chunk text and anchors."""
        chunk_id = primary_chunk.get("chunk_id", "")

        if "WHO_PA_2020" in chunk_id or pillar_key == "physical_activity":
            text = "Adults should do at least 150–300 minutes of moderate-intensity aerobic physical activity throughout the week for substantial health benefits."
            return text, "150–300 minutes/week"

        elif "CDC_DPP" in chunk_id and pillar_key == "weight_management":
            text = "Work toward losing at least 5% to 7% of starting body weight through sustainable daily changes and reducing daily intake by 500 to 750 calories per day."
            return text, "5% to 7% weight loss, 500–750 kcal/day deficit"

        elif "WHO_FIBER" in chunk_id or pillar_key in ("dietary_nutrition", "microbiome_support_diet"):
            text = "Consume at least 25 g per day of naturally occurring dietary fibre in foods by incorporating more whole grains, vegetables, fruits, and pulses into your daily meals."
            return text, "25 g per day"

        elif "EASL_MASLD" in chunk_id:
            text = "Adopt a Mediterranean dietary pattern rich in vegetables, legumes, whole grains, and healthy plant oils while aiming for a 7% to 10% weight loss to reduce liver fat and improve metabolic function."
            return text, "7% to 10% weight loss"

        elif "AHA_OBESITY" in chunk_id:
            text = "Aim for a gradual 5% to 10% weight loss by creating a safe energy deficit of 500 to 750 kcal/day."
            return text, "500 to 750 kcal/day"

        # Fallback to direct chunk recommendation
        return primary_chunk.get("chunk_text", ""), None

    def _generate_conservative_chunk_text(self, chunk: Dict[str, Any]) -> str:
        """Fallback that extracts the primary recommendation sentence directly from chunk text."""
        raw = chunk.get("chunk_text", "")
        sentences = raw.split(". ")
        for s in sentences:
            if "recommend" in s.lower() or "should" in s.lower() or "goal" in s.lower():
                return s.strip() + ("." if not s.strip().endswith(".") else "")
        return sentences[0].strip() + "."
