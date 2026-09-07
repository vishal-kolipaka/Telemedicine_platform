"""Fusion V2 — independent multimodal fusion layer.

Public API
----------
fuse_predictions(router_output, patient_id) -> dict
"""

from .fusion import fuse_predictions, DISEASES
from .meta_stacker import MetaStacker
from .pathway_registry import PathwayRegistry, PATHWAY_DISPLAY_NAMES

__all__ = [
    "fuse_predictions",
    "DISEASES",
    "MetaStacker",
    "PathwayRegistry",
    "PATHWAY_DISPLAY_NAMES",
]
