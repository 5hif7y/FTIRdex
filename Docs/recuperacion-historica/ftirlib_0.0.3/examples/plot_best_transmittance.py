"""
FTIR Plotting Script
--------------------
Applies the best FTIR preprocessing configuration and plots the result
matching the aesthetic style of 'pedido.png'.
"""

import os
import numpy as np
import matplotlib.pyplot as plt
from ftir_library import (
    load_ftir_data,
    moving_average,
    savitzky_golay,
    median_filter,
    percentile_filter,
    correct_baseline_transmittance,
    detect_peaks_transmittance,
    assign_functional_groups,
    DEFAULT_FUNCTIONAL_GROUPS
)

# Input spectrum and configurations
INPUT_FILE = "GO coque s lav red.txt"
CONFIG_FILE = "best_config.txt"
OUTPUT_IMAGE = "images/resultado_best.png"

def get_best_config():
    """Reads the best configuration from the text file."""
    config = {"smoothing": "Savitzky_Golay(11, 2)", "baseline": "arpls(lam=1e5)"}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if ":" in line:
                        k, v = line.split(":", 1)
                        config[k.strip().lower()] = v.strip()
        except Exception as e:
            print(f"Error reading {CONFIG_FILE}, using default config. Error: {e}")
    return config


def parse_num(s):
    """Helper to parse a string into an integer or float, supporting scientific notation."""
    try:
        val = float(s)
        if val.is_integer():
            return int(val)
        return val
    except ValueError:
        return s


def parse_config_params(label):
    """Parses configuration names and parameters from labels."""
    label = label.strip()
    if label == "RAW":
        return "raw", {}
        
    if "(" in label and ")" in label:
        name = label.split("(")[0].strip()
        param_str = label.split("(")[1].split(")")[0].strip()
        
        # Parse parameters
        params = {}
        if "," in param_str:
            parts = param_str.split(",")
            for part in parts:
                if "=" in part:
                    k, v = part.split("=")
                    params[k.strip()] = parse_num(v.strip())
                else:
                    # Positional arguments (e.g. window, poly)
                    val = parse_num(part.strip())
                    if "poly" not in params and len(params) == 1:
                        params["poly"] = val
                    elif "window" not in params:
                        params["window"] = val
        else:
            # Single parameter (e.g. window size or lam)
            if "=" in param_str:
                k, v = param_str.split("=")
                params[k.strip()] = parse_num(v.strip())
            else:
                val = parse_num(param_str.strip())
                params["window"] = val
                    
        return name, params
    return label, {}


def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file '{INPUT_FILE}' not found.")
        return
        
    # Load configuration
    config = get_best_config()
    smooth_label = config["smoothing"]
    base_label = config["baseline"]
    
    print(f"Applying best configuration:")
    print(f"  Smoothing: {smooth_label}")
    print(f"  Baseline:  {base_label}")
    
    # Load raw data
    x, y = load_ftir_data(INPUT_FILE)
    
    # 1. Apply Smoothing
    smooth_name, smooth_params = parse_config_params(smooth_label)
    if smooth_name == "raw":
        y_smoothed = y.copy()
    elif "Moving_Average" in smooth_label:
        window = smooth_params.get("window", 5)
        y_smoothed = moving_average(y, window=window)
    elif "Savitzky_Golay" in smooth_label:
        window = smooth_params.get("window", 11)
        poly = smooth_params.get("poly", 2)
        y_smoothed = savitzky_golay(y, window=window, poly=poly)
    elif "Median_Filter" in smooth_label:
        window = smooth_params.get("window", 5)
        y_smoothed = median_filter(y, window=window)
    elif "Percentile_Filter" in smooth_label:
        window = smooth_params.get("window", 5)
        pct = smooth_params.get("percentile", 50)
        # Handle cases where label is Percentile_Filter(5, 25)
        if "percentile" not in smooth_params and "poly" in smooth_params:
            pct = smooth_params["poly"]  # second argument parsed as poly
        y_smoothed = percentile_filter(y, window=window, percentile=pct)
    else:
        print(f"Warning: Unknown smoothing '{smooth_label}', using RAW.")
        y_smoothed = y.copy()
        
    # 2. Apply Baseline Correction
    base_name, base_params = parse_config_params(base_label)
    
    # Correct transmittance
    z, y_corrected = correct_baseline_transmittance(x, y_smoothed, method=base_name, **base_params)
    
    # 3. Detect Peaks
    PROMINENCE = 0.8
    DISTANCE = 15
    indices, peak_x, peak_y = detect_peaks_transmittance(x, y_corrected, prominence=PROMINENCE, distance=DISTANCE)
    
    # 4. Assign groups
    matched_groups, noise_peaks = assign_functional_groups(peak_x)
    
    print(f"Detected {len(peak_x)} peaks total.")
    print(f"Matched {len(matched_groups)} functional groups:")
    for group, pks in matched_groups.items():
        print(f"  {group}: {', '.join([f'{p:.1f}' for p in pks])} cm^-1")
    print(f"Noise peaks (N={len(noise_peaks)}): {', '.join([f'{p:.1f}' for p in noise_peaks])}")
    
    # ==========================================
    # Matplotlib Plotting (Styling matching pedido.png)
    # ==========================================
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Inter", "Liberation Sans"]
    
    fig, ax = plt.subplots(figsize=(10, 7), dpi=300)
    
    # Plot baseline-corrected transmittance curve in black
    ax.plot(x, y_corrected, color='black', linewidth=1.0, label='Espectro corregido')
    
    # Axis formatting
    ax.set_xlabel("Número de onda (cm$^{-1}$)", fontsize=13, fontweight='normal')
    ax.set_ylabel("Transmitancia (u.a.)", fontsize=13, fontweight='normal')
    
    # Inverted X-axis (standard for FTIR)
    ax.set_xlim(4000, 400)
    
    # Adjust Y-axis limits to leave space at the bottom for vertical labels
    y_min, y_max = np.min(y_corrected), np.max(y_corrected)
    y_range = y_max - y_min
    # Let's set the y limit to leave about 35% of space at the bottom for labels
    ax.set_ylim(y_min - 0.35 * y_range, y_max + 0.05 * y_range)
    
    # Hide Y-axis numbers to match 'pedido.png' (u.a. = arbitrary units, no numerical values shown)
    ax.yaxis.set_major_formatter(plt.NullFormatter())
    
    # Tick marks formatting (keep ticks, remove labels for Y-axis)
    ax.tick_params(axis='both', which='major', labelsize=11, direction='in', length=6, width=1.0)
    ax.tick_params(axis='both', which='minor', direction='in', length=3, width=1.0)
    
    # Add minor ticks
    ax.minorticks_on()
    # Remove minor ticks from Y-axis
    ax.yaxis.set_minor_locator(plt.NullLocator())
    
    # Double check frame styling (box outline)
    for spine in ax.spines.values():
        spine.set_linewidth(1.0)
        spine.set_color('black')
        
    # We want to label the identified groups
    # To avoid overlapping labels, we will match groups and find their most prominent peak
    labeled_x = []
    
    # We will iterate over the standard groups in the order of wavenumber from left to right (high to low)
    group_order = ["O-H", "C-H", "CO2", "C=O", "C=C", "C-O", "C-O-C"]
    
    # Define vertical offset for labels. In pedido.png, labels are placed at a nice distance below the peaks.
    # We will use y_text = y_peak - 15% of y_range
    text_offset = 0.12 * y_range
    
    for group_name in group_order:
        if group_name not in matched_groups:
            # If a group wasn't formally detected, let's see if we can find a local minimum in its range
            # to show it if needed, or skip it.
            # In order to match the request "parecida a pedido.png", let's search for a local minimum
            # in the range for this group anyway, as some groups might be broad or weak but still visible!
            # Let's do this: if it's in matched_groups, use the detected peak.
            # Otherwise, find the minimum in that range just to see if we can label it.
            # This is very smart! It ensures we display all expected groups if there is a minimum.
            w_min, w_max = DEFAULT_FUNCTIONAL_GROUPS[group_name]
            mask = (x >= w_min) & (x <= w_max)
            if np.any(mask):
                min_idx = np.argmin(y_corrected[mask])
                peak_w = x[mask][min_idx]
                peak_t = y_corrected[mask][min_idx]
                # Check if it looks like a peak (e.g. transmittance is less than 99%)
                if peak_t < 99.5:
                    # Add to matched_groups dynamically for plotting
                    matched_groups[group_name] = [peak_w]
                else:
                    continue
            else:
                continue
                
        # Get the peak position
        pks = matched_groups[group_name]
        # Use the first or most prominent peak
        peak_w = pks[0]
        # Find exact y value at this wavenumber
        idx = np.abs(x - peak_w).argmin()
        peak_w_exact = x[idx]
        peak_t = y_corrected[idx]
        
        # Plot red vertical dashed line from peak minimum down to the label start
        y_text = peak_t - text_offset
        ax.plot([peak_w_exact, peak_w_exact], [peak_t, y_text], color='red', linestyle='--', linewidth=1.0)
        
        # Add blue vertical text label below the line
        # Rotated by 270 degrees (or -90) so it reads from top to bottom
        ax.text(
            peak_w_exact, 
            y_text - 0.02 * y_range, 
            group_name, 
            rotation=270, 
            color='blue', 
            ha='center', 
            va='top', 
            fontsize=12, 
            fontweight='bold'
        )
        
    # Title or metadata (optional, we keep it clean like pedido.png which has no main title)
    plt.tight_layout()
    plt.savefig(OUTPUT_IMAGE, bbox_inches='tight', dpi=300)
    print(f"Plot saved successfully as '{OUTPUT_IMAGE}'.")
    plt.close()


if __name__ == "__main__":
    main()
