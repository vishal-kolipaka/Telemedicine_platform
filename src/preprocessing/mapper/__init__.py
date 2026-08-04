"""
Feature Mapper Module
=====================
Maps raw extracted content (Contract 1) to structured schema fields
(Contract 2) with unit conversion, validation, derived features,
conflict detection, and full provenance.

This module is the second stage of the Preprocessing Unit pipeline.
It matches — it never resolves conflicts or generates user-facing text.
"""

from src.preprocessing.mapper.exceptions import (
    MappingError,
    AmbiguousMatchError,
    UnitConversionError,
    InvalidUserValueError,
    SchemaMismatchError,
)
from src.preprocessing.mapper.config import MapperConfig
from src.preprocessing.mapper.models import Candidate, MappedFeature
from src.preprocessing.mapper.interfaces import (
    CandidateExtractor,
    MatchingEngine,
    Validator,
    DerivedFeatureCalculator,
)
from src.preprocessing.mapper.feature_mapper import FeatureMapper
from src.preprocessing.mapper.candidate_extractor import (
    DefaultCandidateExtractor,
)
from src.preprocessing.mapper.regex_matching_engine import (
    RegexMatchingEngine,
)
from src.preprocessing.mapper.llm_matching_engine import (
    LLMFallbackMatchingEngine,
)
from src.preprocessing.mapper.validators import (
    RangeValidator,
    UnitValidator,
    TypeValidator,
)
from src.preprocessing.mapper.derived_features import BMICalculator
from src.preprocessing.mapper.conflict_detector import detect_conflict

__all__ = [
    "FeatureMapper",
    "MapperConfig",
    "Candidate",
    "MappedFeature",
    "CandidateExtractor",
    "DefaultCandidateExtractor",
    "MatchingEngine",
    "RegexMatchingEngine",
    "LLMFallbackMatchingEngine",
    "Validator",
    "RangeValidator",
    "UnitValidator",
    "TypeValidator",
    "DerivedFeatureCalculator",
    "BMICalculator",
    "detect_conflict",
    "MappingError",
    "AmbiguousMatchError",
    "UnitConversionError",
    "InvalidUserValueError",
    "SchemaMismatchError",
]
