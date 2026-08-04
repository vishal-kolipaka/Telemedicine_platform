"""
Exception hierarchy for the Feature Mapper module.

Only SchemaMismatchError should ever propagate unhandled — all others
are caught internally by the orchestrator and converted into structured
output (missing_fields, flagged_for_reconfirm, etc.).
"""


class MappingError(Exception):
    """Base class for all Feature Mapper errors."""


class AmbiguousMatchError(MappingError):
    """Raised when multiple plausible candidates exist for a single
    schema field and no disambiguation is possible."""


class UnitConversionError(MappingError):
    """Raised when a detected unit cannot be converted to the schema's
    canonical unit (no conversion rule exists)."""


class InvalidUserValueError(MappingError):
    """Raised when a user-provided value fails validation (type,
    range, or unit check)."""


class SchemaMismatchError(MappingError):
    """Raised when the feature_schema.json structure is invalid or
    missing required keys. This is the only MappingError subclass
    that should propagate unhandled — it indicates a broken schema,
    not a data-quality issue."""
