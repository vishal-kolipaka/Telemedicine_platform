"""
claim_validator.py — Hard Programmatic Evidence & Provenance Gatekeeper

Enforces all 11 Phase 1.6 / Phase 2 validation checks before any recommendation
or plan claim is permitted to reach the user.

Checks:
  Layer 1 (Structural): Checks 1–3 (Chunk existence, retrieval membership, registry presence)
  Layer 2 (Role & Scope): Checks 4–6 (Source role permissions, condition scope, category match)
  Layer 3 (Numerical): Check 8 (Approved numerical anchors & exact quantity match)
  Layer 4 (Safety & Prohibitions): Checks 9–11 (Prohibited claim types, historical sources, taxon cures)
  Layer 5 (Semantic NLI): Check 7 (Constrained NLI entailment & support verification)
"""

from __future__ import annotations

import os
import json
import logging
from typing import Dict, Any, List, Optional, Tuple

from .nli_verifier import NLIVerifier

logger = logging.getLogger("Recommendations.ClaimValidator")


class ClaimValidator:
    """Rigorous layered claim validator."""

    def __init__(self, manifest_path: Optional[str] = None, chunks_path: Optional[str] = None):
        base_dir = os.path.join(os.getcwd(), "knowledge_base")
        if not os.path.exists(base_dir):
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "knowledge_base"))
        if manifest_path is None:
            manifest_path = os.path.join(base_dir, "source_manifest.json")
        if chunks_path is None:
            chunks_path = os.path.join(base_dir, "chunks.json")

        self.manifest_path = manifest_path
        self.chunks_path = chunks_path

        self.sources: Dict[str, Dict[str, Any]] = {}
        self.chunks: Dict[str, Dict[str, Any]] = {}
        self._load_knowledge_base()

    def _load_knowledge_base(self):
        if os.path.exists(self.manifest_path):
            with open(self.manifest_path, "r", encoding="utf-8") as f:
                manifest_list = json.load(f)
                self.sources = {s["source_id"]: s for s in manifest_list}

        if os.path.exists(self.chunks_path):
            with open(self.chunks_path, "r", encoding="utf-8") as f:
                chunks_list = json.load(f)
                self.chunks = {c["chunk_id"]: c for c in chunks_list}

    def validate_claim(
        self,
        claim: Dict[str, Any],
        retrieved_chunk_ids: List[str],
        current_condition: str,
    ) -> Dict[str, Any]:
        """Validates a single candidate claim against retrieved evidence and governance rules.

        Parameters
        ----------
        claim : dict
            Contains 'claim_id', 'claim_text', 'claim_type', 'category', 'supporting_chunk_ids'.
        retrieved_chunk_ids : list[str]
            List of chunk IDs retrieved in the current search/RAG session.
        current_condition : str
            Target condition (e.g. 'Type2_Diabetes', 'Prediabetes', 'NAFLD', etc.).

        Returns
        -------
        dict
            Validation outcome with 'is_valid', 'layer_passed', 'rejection_code', 'reason', 'nli_result'.
        """
        claim_id = claim.get("claim_id", "unknown_claim")
        claim_text = claim.get("claim_text", "").strip()
        claim_type = claim.get("claim_type", "recommendation")
        claim_category = claim.get("category", "")
        supporting_cids = claim.get("supporting_chunk_ids", [])

        # ── LAYER 1: STRUCTURAL PROVENANCE ────────────────────────────────────
        # Check 1: Supporting chunk IDs must exist
        if not supporting_cids:
            return {
                "claim_id": claim_id,
                "is_valid": False,
                "rejection_layer": "LAYER_1_STRUCTURAL",
                "rejection_code": "UNVERIFIED_CHUNK_CITATION",
                "reason": "Claim contains zero supporting chunk ID citations.",
                "nli_result": None
            }

        # Check 2: All cited chunks must belong to current retrieval session
        retrieved_set = set(retrieved_chunk_ids)
        for cid in supporting_cids:
            if cid not in retrieved_set:
                return {
                    "claim_id": claim_id,
                    "is_valid": False,
                    "rejection_layer": "LAYER_1_STRUCTURAL",
                    "rejection_code": "UNRETRIEVED_CHUNK_CITATION",
                    "reason": f"Cited chunk '{cid}' was not retrieved in the active recommendation session.",
                    "nli_result": None
                }

            # Check 3: Cited chunk must exist in knowledge base
            if cid not in self.chunks:
                return {
                    "claim_id": claim_id,
                    "is_valid": False,
                    "rejection_layer": "LAYER_1_STRUCTURAL",
                    "rejection_code": "UNREGISTERED_CHUNK_ID",
                    "reason": f"Cited chunk '{cid}' does not exist in the approved chunk store.",
                    "nli_result": None
                }

        # Evaluate cited chunks
        valid_supporting_chunks = []
        nli_evaluations = []

        for cid in supporting_cids:
            chunk = self.chunks[cid]
            source_id = chunk["source_id"]

            if source_id not in self.sources:
                return {
                    "claim_id": claim_id,
                    "is_valid": False,
                    "rejection_layer": "LAYER_1_STRUCTURAL",
                    "rejection_code": "UNREGISTERED_SOURCE_ID",
                    "reason": f"Source '{source_id}' is not in the approved source registry.",
                    "nli_result": None
                }
            source = self.sources[source_id]

            # ── LAYER 2: ROLE AND PERMISSION VALIDATION ─────────────────────────
            # Check 4: Source & chunk role permissions
            if claim_type == "recommendation":
                if not source.get("recommendation_generation_allowed", False):
                    return {
                        "claim_id": claim_id,
                        "is_valid": False,
                        "rejection_layer": "LAYER_2_ROLE_PERMISSIONS",
                        "rejection_code": "UNAUTHORIZED_SOURCE_ROLE",
                        "reason": f"Source '{source_id}' evidence role ({source.get('evidence_role')}) strictly prohibits recommendation generation.",
                        "nli_result": None
                    }
                if not chunk.get("recommendation_generation_allowed", False):
                    return {
                        "claim_id": claim_id,
                        "is_valid": False,
                        "rejection_layer": "LAYER_2_ROLE_PERMISSIONS",
                        "rejection_code": "UNAUTHORIZED_CHUNK_ROLE",
                        "reason": f"Chunk '{cid}' is designated diagnostic/explanatory only and cannot justify interventions.",
                        "nli_result": None
                    }

            # Check 5: Condition scope match
            allowed_conditions = chunk.get("allowed_condition_scopes", [])
            if current_condition not in allowed_conditions and "All_Cardiometabolic" not in allowed_conditions:
                return {
                    "claim_id": claim_id,
                    "is_valid": False,
                    "rejection_layer": "LAYER_2_ROLE_PERMISSIONS",
                    "rejection_code": "UNAUTHORIZED_CONDITION_SCOPE",
                    "reason": f"Chunk '{cid}' allowed conditions {allowed_conditions} do not cover '{current_condition}'.",
                    "nli_result": None
                }

            # Check 6: Category match
            allowed_categories = chunk.get("allowed_recommendation_categories", [])
            if claim_category and claim_category not in allowed_categories:
                return {
                    "claim_id": claim_id,
                    "is_valid": False,
                    "rejection_layer": "LAYER_2_ROLE_PERMISSIONS",
                    "rejection_code": "CATEGORY_MISMATCH",
                    "reason": f"Claim category '{claim_category}' is not supported by chunk categories {allowed_categories}.",
                    "nli_result": None
                }

            # ── LAYER 4: SAFETY & PROHIBITIONS ─────────────────────────────────
            # Check 9: Prohibited claim types in chunk metadata
            prohibited_types = chunk.get("prohibited_claim_types", [])
            for p_type in prohibited_types:
                if p_type in claim.get("detected_claim_types", []):
                    return {
                        "claim_id": claim_id,
                        "is_valid": False,
                        "rejection_layer": "LAYER_4_SAFETY_PROHIBITIONS",
                        "rejection_code": "PROHIBITED_CLAIM_VIOLATION",
                        "reason": f"Claim contains prohibited type '{p_type}' forbidden by chunk '{cid}'.",
                        "nli_result": None
                    }

            # Check 10: Historical source restriction
            if source.get("evidence_role") in ("HISTORICAL_CONTEXT_ONLY", "DIAGNOSTIC_EXPLANATORY_SOURCE") and claim_type == "recommendation":
                return {
                    "claim_id": claim_id,
                    "is_valid": False,
                    "rejection_layer": "LAYER_4_SAFETY_PROHIBITIONS",
                    "rejection_code": "HISTORICAL_SOURCE_VIOLATION",
                    "reason": f"Historical/diagnostic source '{source_id}' cannot justify personalized interventions.",
                    "nli_result": None
                }

            # ── LAYER 5: CONSTRAINED NLI SEMANTIC VERIFIER ─────────────────────
            # Check 7 & 8 & 11: NLI entailment, numbers, and taxon cure safety
            nli_res = NLIVerifier.verify_support(
                claim_text=claim_text,
                chunk_text=chunk["chunk_text"],
                chunk_metadata=chunk
            )
            nli_evaluations.append((cid, nli_res))

            if nli_res["validation_passed"] and nli_res["support_status"] == "SUPPORTED":
                valid_supporting_chunks.append((cid, nli_res))

        # Check if at least ONE supporting chunk passed NLI entailment
        if not valid_supporting_chunks:
            primary_failure = nli_evaluations[0][1] if nli_evaluations else {}
            failure_code = primary_failure.get("failure_code", "UNSUPPORTED_SEMANTIC_DRIFT")
            return {
                "claim_id": claim_id,
                "is_valid": False,
                "rejection_layer": "LAYER_5_SEMANTIC_NLI",
                "rejection_code": failure_code,
                "reason": primary_failure.get("reason", "Semantic verification failed against all cited evidence chunks."),
                "nli_result": primary_failure
            }

        # Claim successfully passed all 11 checks!
        winning_cid, winning_nli = valid_supporting_chunks[0]
        return {
            "claim_id": claim_id,
            "is_valid": True,
            "rejection_layer": None,
            "rejection_code": None,
            "reason": f"Claim verified by chunk '{winning_cid}' ({winning_nli['support_type']} support).",
            "verified_chunk_id": winning_cid,
            "support_type": winning_nli["support_type"],
            "matched_evidence": winning_nli["matched_evidence"],
            "nli_result": winning_nli
        }
