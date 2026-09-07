"""
pathway_registry.py — Registry and Loader for the Adaptive 7-Pathway Models
"""

from __future__ import annotations

import os
import json
from typing import Dict, Any, List, Optional

MANIFEST_PATH = os.path.join(
    os.path.dirname(__file__), "models", "pathway_manifest.json"
)

# Standardized pathway keys mapped from active modalities
MODALITY_SET_TO_PATHWAY: Dict[frozenset[str], str] = {
    frozenset(["clinical"]): "C",
    frozenset(["wearable"]): "W",
    frozenset(["gut"]): "G",
    frozenset(["clinical", "wearable"]): "C_W",
    frozenset(["clinical", "gut"]): "C_G",
    frozenset(["wearable", "gut"]): "W_G",
    frozenset(["clinical", "wearable", "gut"]): "C_W_G",
}

PATHWAY_DISPLAY_NAMES: Dict[str, str] = {
    "C": "Clinical Only Stacker",
    "W": "Wearable Only Stacker",
    "G": "Gut Only Stacker",
    "C_W": "Clinical + Wearable Stacker",
    "C_G": "Clinical + Gut Stacker",
    "W_G": "Wearable + Gut Stacker",
    "C_W_G": "Clinical + Wearable + Gut Stacker",
    "insufficient": "Insufficient Modalities",
}


class PathwayRegistry:
    """Loads and caches the 35-model pathway manifest."""

    _manifest: Optional[Dict[str, Any]] = None

    @classmethod
    def get_manifest(cls) -> Dict[str, Any]:
        if cls._manifest is None:
            if not os.path.exists(MANIFEST_PATH):
                raise FileNotFoundError(
                    f"Pathway manifest not found at: {MANIFEST_PATH}. "
                    "Run 'python -m src.fusion_v2.train_pathways' to generate it."
                )
            with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
                cls._manifest = json.load(f)
        return cls._manifest

    @classmethod
    def get_model_entry(cls, pathway_key: str, disease: str) -> Dict[str, Any]:
        manifest = cls.get_manifest()
        models = manifest.get("models", {})
        if pathway_key not in models:
            raise KeyError(f"Unknown pathway: {pathway_key}")
        diseases = models[pathway_key].get("diseases", {})
        if disease not in diseases:
            raise KeyError(f"Unknown disease '{disease}' in pathway '{pathway_key}'")
        return diseases[disease]

    @classmethod
    def resolve_pathway_key(cls, active_modalities: List[str]) -> str:
        """Resolves active modalities (e.g. ['clinical', 'gut']) to a standard pathway key."""
        active_set = frozenset(m.lower().strip() for m in active_modalities)
        return MODALITY_SET_TO_PATHWAY.get(active_set, "insufficient")
