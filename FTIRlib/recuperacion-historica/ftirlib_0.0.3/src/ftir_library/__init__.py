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

from .pipeline import (
    parse_num,
    parse_config_params,
    apply_smoothing,
    apply_baseline,
    preprocess_spectrum,
    run_grid_search,
    plot_best_configuration,
    plot_gallery_3x1,
    plot_superposition,
    generate_numerical_report,
    run_raman_grid_search,
    plot_raman_pca,
    PipelineResult,
    load_data,
    generate_report,
    run_analysis,
    plot_best,
    plot_gallery,
    get_approved_count,
    get_approvednumber,
    FTIR,
    SERS
)

from .raman import (
    remove_cosmic_rays,
    normalize_spectra,
    NearestCentroidClassifier,
    KernelRidgeClassifier
)

__version__ = "0.0.3"



