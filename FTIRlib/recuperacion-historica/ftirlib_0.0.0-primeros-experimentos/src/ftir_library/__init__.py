"""
FTIR Analysis Package Interface
"""

from .core import (
    load_ftir_data,
    moving_average,
    savitzky_golay,
    median_filter,
    percentile_filter,
    baseline_detrend,
    baseline_linear,
    baseline_polynomial,
    baseline_asls,
    baseline_airpls,
    baseline_arpls,
    correct_baseline_transmittance,
    correct_baseline_absorbance,
    transmittance_to_absorbance,
    detect_peaks_transmittance,
    detect_peaks_absorbance,
    assign_functional_groups,
    calculate_pipeline_score,
    DEFAULT_FUNCTIONAL_GROUPS
)
