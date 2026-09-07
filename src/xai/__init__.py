"""
src.xai package — Explainable AI layer for Level-0 models and Fusion V2.
"""

from .xai_engine import XAIEngine
from .tree_explainer import explain_domain_disease
from .fusion_explainer import explain_provenance, build_supporting_wearable_evidence
from .feature_formatter import get_feature_meta, format_feature_value

__all__ = [
    "XAIEngine",
    "explain_domain_disease",
    "explain_provenance",
    "build_supporting_wearable_evidence",
    "get_feature_meta",
    "format_feature_value",
]
