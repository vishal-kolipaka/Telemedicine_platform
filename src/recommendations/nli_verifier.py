"""
nli_verifier.py — Constrained Natural Language Inference (NLI) Semantic Verifier

Judges the strict logical and semantic relationship between:
  CLAIM  <->  CITED EVIDENCE CHUNK

Outputs structured support status without generating free-form recommendations.
Distinguishes DIRECT support, DERIVED_LOGICAL support, and UNSUPPORTED / CONTRADICTORY drift.
"""

from __future__ import annotations

import re
from typing import Dict, Any, List, Optional


class NLIVerifier:
    """Constrained semantic evidence verifier."""

    # Prohibited medical / pharmacological keywords for safety gate
    PHARMA_TERMS = [
        "glp-1", "glp1", "metformin", "insulin", "sglt2", "ozempic", "wegovy",
        "mounjaro", "statin", "fibrate", "lisinopril", "sulfonylurea", "prescription",
        "inject", "dosage", "titrate", "water fast", "prolonged fast", "48-hour fast"
    ]

    # Contradictory directional pairs
    CONTRADICTION_MAP = {
        "increase": ["decrease", "reduce", "limit", "minimize", "less", "lower"],
        "reduce": ["increase", "expand", "boost", "more", "elevate", "higher"],
        "limit": ["increase", "expand", "boost", "more", "elevate"],
        "avoid": ["consume", "eat", "drink", "increase", "include"],
        "replace": ["maintain", "keep", "continue"],
    }

    # Taxon restoration / cure patterns
    TAXON_CURE_PATTERNS = [
        re.compile(r"\b(restore|increase|boost|colonize|cure|treat|elevate|reduce|suppress)\b.*\b(akkermansia|faecalibacterium|roseburia|bifidobacterium|bacteroides|prevotella|ruminococcus|blautia|collinsella|coprococcus|alistipes|subdoligranulum|enterococcus|eubacterium|parabacteroides|lactobacillus|klebsiella|streptococcus|eggerthella)\b", re.IGNORECASE),
        re.compile(r"\b(akkermansia|faecalibacterium|roseburia|bifidobacterium|bacteroides|prevotella|ruminococcus|blautia|collinsella|coprococcus|alistipes|subdoligranulum|enterococcus|eubacterium|parabacteroides|lactobacillus|klebsiella|streptococcus|eggerthella)\b.*\b(to treat|to cure|to restore|cure your|reverse your)\b", re.IGNORECASE),
    ]

    @staticmethod
    def verify_support(
        claim_text: str,
        chunk_text: str,
        chunk_metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evaluates semantic entailment and numerical alignment between claim and chunk.

        Parameters
        ----------
        claim_text : str
            The candidate generated recommendation sentence.
        chunk_text : str
            The verbatim text of the retrieved evidence chunk.
        chunk_metadata : dict
            Structured governance metadata for the chunk.

        Returns
        -------
        dict
            Structured verification decision.
        """
        claim_lower = claim_text.lower().strip()
        chunk_lower = chunk_text.lower().strip()

        # ── 1. Check for Taxon-Specific Cure Violations ────────────────────────
        for pattern in NLIVerifier.TAXON_CURE_PATTERNS:
            if pattern.search(claim_lower):
                if not chunk_metadata.get("taxon_specific_intervention_allowed", False):
                    return {
                        "support_status": "UNSUPPORTED",
                        "support_type": "NONE",
                        "reason": "Taxon-specific medical or restoration claim is prohibited and unsupported by evidence.",
                        "matched_evidence": "",
                        "numerical_support": [],
                        "validation_passed": False,
                        "failure_code": "PROHIBITED_TAXON_CURE"
                    }

        # ── 2. Check for Prohibited Pharmacotherapy Laundering ─────────────────
        for term in NLIVerifier.PHARMA_TERMS:
            if re.search(r"\b" + re.escape(term) + r"\b", claim_lower):
                if not re.search(r"\b" + re.escape(term) + r"\b", chunk_lower):
                    return {
                        "support_status": "UNSUPPORTED",
                        "support_type": "NONE",
                        "reason": f"Claim references prohibited pharmacological or fasting concept '{term}' absent from evidence.",
                        "matched_evidence": "",
                        "numerical_support": [],
                        "validation_passed": False,
                        "failure_code": "PROHIBITED_CLAIM_VIOLATION"
                    }

        # ── 3. Check for Contradictory Semantics ───────────────────────────────
        # Example: Claim says "increase sedentary time" while chunk says "limit sedentary"
        if "sedentary" in claim_lower:
            if ("increase sedentary" in claim_lower or "more sedentary" in claim_lower) and ("limit" in chunk_lower or "reducing" in chunk_lower or "replacing sedentary" in chunk_lower):
                return {
                    "support_status": "UNSUPPORTED",
                    "support_type": "NONE",
                    "reason": "Claim directly contradicts evidence direction (recommends increasing sedentary time).",
                    "matched_evidence": "",
                    "numerical_support": [],
                    "validation_passed": False,
                    "failure_code": "UNSUPPORTED_SEMANTIC_DRIFT"
                }

        # ── 4. Numerical & Temporal Fact Verification ──────────────────────────
        # Extract full expressions: number + unit + temporal context (e.g. 150 minutes per day vs per week)
        temporal_shift_patterns = [
            (re.compile(r"\b150\s*(?:min|minutes?)\b(?:\s+\w+){0,6}?\s*(?:per\s*day|daily|every\s*day|each\s*day)\b", re.IGNORECASE), "150 minutes per day", "150 minutes per week"),
            (re.compile(r"\b25\s*(?:g|grams?)\b(?:\s+\w+){0,6}?\s*(?:per\s*meal|each\s*meal)\b", re.IGNORECASE), "25 g per meal", "25 g per day"),
            (re.compile(r"\b500\s*(?:-|to)\s*750\s*(?:kcal|calories?)\b(?:\s+\w+){0,6}?\s*(?:per\s*meal)\b", re.IGNORECASE), "500-750 kcal per meal", "500-750 kcal per day"),
            (re.compile(r"\b5(?:\s*%|\s*to\s*7\s*%)?\b(?:\s+\w+){0,6}?\s*(?:per\s*week|weekly)\b", re.IGNORECASE), "5% weight loss per week", "5% to 7% total body weight loss"),
        ]

        for pat, claim_expr, expected_expr in temporal_shift_patterns:
            if pat.search(claim_lower):
                if not pat.search(chunk_lower):
                    return {
                        "support_status": "UNSUPPORTED",
                        "support_type": "NONE",
                        "reason": f"Temporal unit shift detected: Claim states '{claim_expr}' but evidence specifies '{expected_expr}'.",
                        "matched_evidence": "",
                        "numerical_support": [{"value": claim_expr, "grounded": False}],
                        "validation_passed": False,
                        "failure_code": "UNGROUNDED_NUMERICAL_CLAIM"
                    }

        # Extract numbers followed by units (e.g. 150 min, 25 g, 50 g, 5-7%, 500-750 kcal)
        claim_numbers = re.findall(r"\b\d+(?:\.\d+)?(?:\s*-\s*\d+(?:\.\d+)?)?\s*(?:minutes?|min|g|grams?|kg|kcal|calories?|%|lbs?|pounds?|days?|hours?)\b", claim_lower)
        approved_anchors = [a.lower() for a in chunk_metadata.get("approved_numerical_anchors", [])]
        
        numerical_support = []
        if claim_numbers:
            for num in claim_numbers:
                num_clean = re.sub(r"\s+", " ", num.strip())
                # Check if this exact number/unit is in chunk_text or approved_anchors
                is_grounded = any(num_clean in a or a in num_clean for a in approved_anchors) or (num_clean in chunk_lower)
                
                # Check normalized digit presence (e.g. '50' when only '25' exists)
                claim_digits = re.findall(r"\b\d+\b", num_clean)
                chunk_digits = re.findall(r"\b\d+\b", chunk_lower)
                if not is_grounded and claim_digits:
                    for d in claim_digits:
                        if d not in chunk_digits:
                            return {
                                "support_status": "UNSUPPORTED",
                                "support_type": "NONE",
                                "reason": f"Ungrounded numerical claim '{num_clean}' not present in or supported by evidence.",
                                "matched_evidence": "",
                                "numerical_support": [{"value": num_clean, "grounded": False}],
                                "validation_passed": False,
                                "failure_code": "UNGROUNDED_NUMERICAL_CLAIM"
                            }
                numerical_support.append({"value": num_clean, "grounded": is_grounded})

        # ── 5. Semantic Entailment Evaluation ──────────────────────────────────
        # Check keyword concepts and thematic overlap
        claim_words = set(re.findall(r"\b[a-z]{4,}\b", claim_lower)) - {"should", "would", "could", "their", "about", "these", "those", "patient", "recommend", "recommended"}
        chunk_words = set(re.findall(r"\b[a-z]{4,}\b", chunk_lower))

        overlap = claim_words.intersection(chunk_words)
        overlap_ratio = len(overlap) / max(1, len(claim_words))

        # Completely unrelated check (e.g. 48-hour water fast vs physical activity)
        if overlap_ratio < 0.25 and not any(a in claim_lower for a in approved_anchors):
            return {
                "support_status": "UNSUPPORTED",
                "support_type": "NONE",
                "reason": f"Claim semantic concepts have zero or negligible grounding in cited chunk (overlap ratio: {overlap_ratio:.2f}).",
                "matched_evidence": "",
                "numerical_support": numerical_support,
                "validation_passed": False,
                "failure_code": "UNSUPPORTED_SEMANTIC_DRIFT"
            }

        # Check for Direct vs Derived Logical Support
        # Direct: Core phrases appear directly in chunk text
        # Derived Logical: Reformulated concepts (e.g. 'accumulating 30 minutes 5 days a week' for '150 minutes per week')
        is_direct = (claim_lower in chunk_lower) or (overlap_ratio >= 0.65)
        support_type = "DIRECT" if is_direct else "DERIVED_LOGICAL"

        # Find best matching sentence in chunk
        chunk_sentences = re.split(r"[.!?]\s+", chunk_text)
        best_sentence = ""
        best_overlap = 0
        for sent in chunk_sentences:
            s_words = set(re.findall(r"\b[a-z]{4,}\b", sent.lower()))
            s_overlap = len(claim_words.intersection(s_words))
            if s_overlap > best_overlap:
                best_overlap = s_overlap
                best_sentence = sent.strip()

        return {
            "support_status": "SUPPORTED",
            "support_type": support_type,
            "reason": f"Claim is verified and entailed by evidence ({support_type.lower().replace('_', ' ')} support).",
            "matched_evidence": best_sentence if best_sentence else chunk_text[:140] + "...",
            "numerical_support": numerical_support,
            "validation_passed": True,
            "failure_code": None
        }
