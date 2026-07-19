"""
FTIR Absorbance Grid Search & Plotting Pipeline
-----------------------------------------------
Uses the ftir_library package to:
1. Load transmittance data and convert to absorbance.
2. Run combinatorial grid searches of 180 combinations for both rGO and GO.
3. Save grid search results as CSV.
4. Plot the optimal configuration with functional group annotations.
5. Plot galleries of top configurations as multiple 3x1 images.
"""

from ftir_library import (
    load_ftir_data,
    transmittance_to_absorbance,
    run_grid_search,
    plot_best_configuration,
    plot_gallery_3x1
)

# Input files in local examples directory
RGO_FILE = "GO coque s lav red.txt"
GO_FILE = "GO coque s lav ox.txt"

# Prominence and distance parameters in absorbance space
PROMINENCE = 0.02
DISTANCE = 15


def main():
    # 1. Process rGO
    print("\n==========================================")
    print("PROCESSING SAMPLE: rGO")
    print("==========================================")
    
    x_rgo, y_rgo_trans = load_ftir_data(RGO_FILE)
    y_rgo_abs = transmittance_to_absorbance(y_rgo_trans)
    
    best_rgo, results_rgo = run_grid_search(
        x_rgo, y_rgo_abs,
        output_csv="absorbance_pipeline_results_rGO.csv",
        best_config_txt="best_config_absorbance_rGO.txt",
        space="absorbance",
        prominence=PROMINENCE,
        distance=DISTANCE
    )
    
    plot_best_configuration(
        x_rgo, y_rgo_abs, best_rgo, "images/absorbance_result_best_rGO.png",
        space="absorbance", prominence=PROMINENCE, distance=DISTANCE
    )
    
    plot_gallery_3x1(
        x_rgo, y_rgo_abs, results_rgo, "images/absorbance_result_gallery_rGO",
        space="absorbance", prominence=PROMINENCE, distance=DISTANCE
    )
    
    # 2. Process GO
    print("\n==========================================")
    print("PROCESSING SAMPLE: GO")
    print("==========================================")
    
    x_go, y_go_trans = load_ftir_data(GO_FILE)
    y_go_abs = transmittance_to_absorbance(y_go_trans)
    
    best_go, results_go = run_grid_search(
        x_go, y_go_abs,
        output_csv="absorbance_pipeline_results_GO.csv",
        best_config_txt="best_config_absorbance_GO.txt",
        space="absorbance",
        prominence=PROMINENCE,
        distance=DISTANCE
    )
    
    plot_best_configuration(
        x_go, y_go_abs, best_go, "images/absorbance_result_best_GO.png",
        space="absorbance", prominence=PROMINENCE, distance=DISTANCE
    )
    
    plot_gallery_3x1(
        x_go, y_go_abs, results_go, "images/absorbance_result_gallery_GO",
        space="absorbance", prominence=PROMINENCE, distance=DISTANCE
    )


if __name__ == "__main__":
    main()
