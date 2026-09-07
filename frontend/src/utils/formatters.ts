/**
 * Reusable formatting utilities for clinical risk percentages and display values.
 */

/**
 * Formats a risk percentage (0 to 100) with precise, non-misleading representation.
 * - Never rounds a probability below 100% up to 100%.
 * - Never rounds a positive probability down to 0.0%.
 * - Formats standard numbers with clean single-decimal precision.
 *
 * @param val - The percentage value (e.g., 99.9935, 87.7, 0.0, 100.0)
 * @returns Formatted string with '%' suffix (e.g., "99.9935%", "87.7%", "100%")
 */
export const formatRiskPercentage = (val: number | null | undefined): string => {
  if (val === null || val === undefined || isNaN(val)) {
    return '—';
  }

  // Exactly 100%
  if (val >= 100) {
    return '100%';
  }

  // Exactly 0%
  if (val <= 0) {
    return '0.0%';
  }

  // Very high risk close to 100%: preserve meaningful precision, NEVER round up to 100.0%
  if (val >= 99.9) {
    const rawFixed = val.toFixed(4);
    const trimmed = rawFixed.replace(/\.?0+$/, '');
    if (trimmed === '100' || trimmed === '100.0') {
      return '99.99%';
    }
    return `${trimmed}%`;
  }

  // Very low risk close to 0%: preserve precision, NEVER round down to 0.0%
  if (val < 0.1) {
    const rawFixed = val.toFixed(4);
    const trimmed = rawFixed.replace(/\.?0+$/, '');
    if (trimmed === '0' || trimmed === '0.0') {
      return '0.01%';
    }
    return `${trimmed}%`;
  }

  // Standard range (0.1% to 99.8%): standard 1-decimal display
  return `${val.toFixed(1)}%`;
};
