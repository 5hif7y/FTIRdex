import sys
import os
import argparse
import json
import numpy as np
import matplotlib.pyplot as plt
from ftir_library import preprocess_spectrum, load_data, transmittance_to_absorbance, FTIR
from ftir_library import detect_peaks_absorbance, detect_peaks_transmittance, assign_functional_groups

def annotate_plot(ax, groups_dict, space, mode, groups_db, y_min, y_max):
    if mode == 'none':
        return
        
    y_range = y_max - y_min if y_max > y_min else 1.0
    
    if mode == 'box':
        active_groups = sorted(groups_dict.keys())
        for g_name in active_groups:
            w_min, w_max = (None, None)
            if groups_db and g_name in groups_db:
                w_min, w_max = groups_db[g_name]
            else:
                from ftir_library.pipeline import DEFAULT_FUNCTIONAL_GROUPS
                if g_name in DEFAULT_FUNCTIONAL_GROUPS:
                    w_min, w_max = DEFAULT_FUNCTIONAL_GROUPS[g_name]
            
            if w_min is not None and w_max is not None:
                ax.axvspan(w_min, w_max, facecolor='red', alpha=0.06, edgecolor='red', linestyle='--', linewidth=0.8)
                if space == 'absorbance':
                    y_text = y_max + 0.12 * y_range
                    va = 'bottom'
                else:
                    y_text = y_min - 0.12 * y_range
                    va = 'top'
                ax.text((w_min + w_max) / 2, y_text, g_name, rotation=270, color='blue', ha='center', va=va, fontsize=10, fontweight='bold')
                
    elif mode in ('lines', 'full-lines'):
        subgroups_list = []
        for g_name, peaks in groups_dict.items():
            if not peaks:
                continue
            sorted_peaks = sorted(peaks, key=lambda p: p[0])
            current_subg = [sorted_peaks[0]]
            for p in sorted_peaks[1:]:
                if p[0] - current_subg[-1][0] <= 150:
                    current_subg.append(p)
                else:
                    center_w = sum(x[0] for x in current_subg) / len(current_subg)
                    subgroups_list.append((center_w, g_name, current_subg))
                    current_subg = [p]
            center_w = sum(x[0] for x in current_subg) / len(current_subg)
            subgroups_list.append((center_w, g_name, current_subg))
            
        subgroups_list.sort(key=lambda item: item[0], reverse=True)
        
        alternate = False
        text_offset = 0.10 * y_range if space == 'absorbance' else 0.12 * y_range
        
        for i, (center_w, g_name, peaks) in enumerate(subgroups_list):
            current_offset = text_offset
            if i > 0 and abs(center_w - subgroups_list[i-1][0]) < 160:
                if not alternate:
                    current_offset = text_offset + 0.15 * y_range
                    alternate = True
                else:
                    current_offset = text_offset
                    alternate = False
            else:
                alternate = False
                
            unique_peaks = []
            for p in peaks:
                if not any(abs(p[0] - up[0]) < 1.0 for up in unique_peaks):
                    unique_peaks.append(p)
            
            if len(unique_peaks) > 2:
                unique_peaks = [unique_peaks[0], unique_peaks[-1]]
                
            for pw, pval, label in unique_peaks:
                if mode == 'lines':
                    if space == 'absorbance':
                        y_line_end = pval + current_offset
                        ax.plot([pw, pw], [pval, y_line_end], color='red', linestyle='--', linewidth=1.0)
                    else:
                        y_line_end = pval - current_offset
                        ax.plot([pw, pw], [y_line_end, pval], color='red', linestyle='--', linewidth=1.0)
                elif mode == 'full-lines':
                    if space == 'absorbance':
                        y_line_end = y_max + current_offset
                        ax.plot([pw, pw], [y_min - 0.05 * y_range, y_line_end], color='red', linestyle='--', linewidth=1.0)
                    else:
                        y_line_end = y_min - current_offset
                        ax.plot([pw, pw], [y_line_end, y_max + 0.05 * y_range], color='red', linestyle='--', linewidth=1.0)
            
            if space == 'absorbance':
                y_text_pos = (y_max if mode == 'full-lines' else max(p[1] for p in unique_peaks)) + current_offset
                ax.text(center_w, y_text_pos + 0.02 * y_range, g_name, rotation=270, color='blue', ha='center', va='bottom', fontsize=10, fontweight='bold')
            else:
                y_text_pos = (y_min if mode == 'full-lines' else min(p[1] for p in unique_peaks)) - current_offset
                ax.text(center_w, y_text_pos - 0.02 * y_range, g_name, rotation=270, color='blue', ha='center', va='top', fontsize=10, fontweight='bold')

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--files', nargs='+', required=True)
    parser.add_argument('--labels', nargs='+', required=True)
    parser.add_argument('--smooth', default='RAW')
    parser.add_argument('--baseline', default='RAW')
    parser.add_argument('--mode', default='lineas-completas')
    parser.add_argument('--groups', default=None)
    args = parser.parse_args()

    files = args.files
    labels = args.labels
    smooth_algorithm = args.smooth
    baseline_algorithm = args.baseline
    
    mode = args.mode
    if mode == 'lineas-completas':
        mode = 'full-lines'
    elif mode == 'desactivado':
        mode = 'none'
    elif mode == 'boxes':
        mode = 'box'
        
    groups_db = None
    if args.groups and os.path.exists(args.groups):
        try:
            with open(args.groups, 'r', encoding='utf-8') as f:
                custom_groups = json.load(f)
            groups_db = {k: tuple(v) for k, v in custom_groups.items()}
        except Exception as e:
            print(f"Error loading custom groups: {e}")

    # Load and preprocess all spectra
    spectra = []
    for f, label in zip(files, labels):
        try:
            x, y_trans = load_data(f, FTIR)
            y_abs = transmittance_to_absorbance(y_trans)
            
            # Preprocess
            _, y_trans_corr = preprocess_spectrum(x, y_trans, smooth_algorithm, baseline_algorithm, space='transmittance')
            _, y_abs_corr = preprocess_spectrum(x, y_abs, smooth_algorithm, baseline_algorithm, space='absorbance')
            
            spectra.append({
                'label': label,
                'x': x,
                'y_trans': y_trans_corr,
                'y_abs': y_abs_corr
            })
        except Exception as e:
            print(f"Error loading {f}: {e}")

    if not spectra:
        sys.exit(1)

    # Detect peaks for each sample
    groups_trans = {}
    groups_abs = {}
    groups_norm = {}
    
    for spec in spectra:
        # Detect peaks
        indices_abs, peak_x_abs, peak_y_abs = detect_peaks_absorbance(spec['x'], spec['y_abs'], prominence=0.02, distance=15)
        matched_abs, _ = assign_functional_groups(peak_x_abs, groups_db=groups_db)
        
        indices_trans, peak_x_trans, peak_y_trans = detect_peaks_transmittance(spec['x'], spec['y_trans'], prominence=0.02, distance=15)
        matched_trans, _ = assign_functional_groups(peak_x_trans, groups_db=groups_db)
        
        y_norm = (spec['y_abs'] - np.min(spec['y_abs'])) / (np.max(spec['y_abs']) - np.min(spec['y_abs']))
        indices_norm, peak_x_norm, peak_y_norm = detect_peaks_absorbance(spec['x'], y_norm, prominence=0.02, distance=15)
        matched_norm, _ = assign_functional_groups(peak_x_norm, groups_db=groups_db)
        
        # Store peaks
        for g_name, peaks_list in matched_abs.items():
            if g_name not in groups_abs:
                groups_abs[g_name] = []
            for pw in peaks_list:
                idx = np.abs(spec['x'] - pw).argmin()
                groups_abs[g_name].append((spec['x'][idx], spec['y_abs'][idx], spec['label']))
                
        for g_name, peaks_list in matched_trans.items():
            if g_name not in groups_trans:
                groups_trans[g_name] = []
            for pw in peaks_list:
                idx = np.abs(spec['x'] - pw).argmin()
                groups_trans[g_name].append((spec['x'][idx], spec['y_trans'][idx], spec['label']))
                
        for g_name, peaks_list in matched_norm.items():
            if g_name not in groups_norm:
                groups_norm[g_name] = []
            for pw in peaks_list:
                idx = np.abs(spec['x'] - pw).argmin()
                groups_norm[g_name].append((spec['x'][idx], y_norm[idx], spec['label']))

    # Output filenames
    out_trans = "super_transmittance.png"
    out_abs = "super_absorbance.png"
    out_super = "super_superposition.png"

    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Inter", "Liberation Sans"]

    colors = ['black', 'red', 'blue', 'green', 'orange', 'purple', 'cyan', 'magenta']

    # 1. Superimposed Transmittance
    fig, ax = plt.subplots(figsize=(10, 7), dpi=300)
    for i, spec in enumerate(spectra):
        color = colors[i % len(colors)]
        ax.plot(spec['x'], spec['y_trans'], color=color, linewidth=1.2, label=spec['label'])
    
    # Invert x-axis
    x_all = np.concatenate([spec['x'] for spec in spectra])
    ax.set_xlim(max(x_all), min(x_all))
    ax.set_xlabel("Número de onda (cm$^{-1}$)", fontsize=13)
    ax.set_ylabel("Transmitancia (u.a.)", fontsize=13)
    ax.set_title("Superposición de Transmitancias", fontsize=12, fontweight='bold', pad=10)
    ax.legend(loc='best', frameon=True, edgecolor='black', fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.5)
    
    # Apply marking mode
    y_min_t = min(np.min(spec['y_trans']) for spec in spectra)
    y_max_t = max(np.max(spec['y_trans']) for spec in spectra)
    y_range_t = y_max_t - y_min_t if y_max_t > y_min_t else 1.0
    ax.set_ylim(y_min_t - 0.45 * y_range_t, y_max_t + 0.05 * y_range_t)
    annotate_plot(ax, groups_trans, 'transmittance', mode, groups_db, y_min_t, y_max_t)
    
    plt.tight_layout()
    plt.savefig(out_trans, bbox_inches='tight', dpi=300)
    plt.close()

    # 2. Superimposed Absorbance
    fig, ax = plt.subplots(figsize=(10, 7), dpi=300)
    for i, spec in enumerate(spectra):
        color = colors[i % len(colors)]
        ax.plot(spec['x'], spec['y_abs'], color=color, linewidth=1.2, label=spec['label'])
    ax.set_xlim(max(x_all), min(x_all))
    ax.set_xlabel("Número de onda (cm$^{-1}$)", fontsize=13)
    ax.set_ylabel("Absorbancia (u.a.)", fontsize=13)
    ax.set_title("Superposición de Absorbancias", fontsize=12, fontweight='bold', pad=10)
    ax.legend(loc='best', frameon=True, edgecolor='black', fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.5)
    
    y_min_a = min(np.min(spec['y_abs']) for spec in spectra)
    y_max_a = max(np.max(spec['y_abs']) for spec in spectra)
    y_range_a = y_max_a - y_min_a if y_max_a > y_min_a else 1.0
    ax.set_ylim(y_min_a - 0.05 * y_range_a, y_max_a + 0.45 * y_range_a)
    annotate_plot(ax, groups_abs, 'absorbance', mode, groups_db, y_min_a, y_max_a)
    
    plt.tight_layout()
    plt.savefig(out_abs, bbox_inches='tight', dpi=300)
    plt.close()

    # 3. Superimposed Normalized Superposition
    fig, ax = plt.subplots(figsize=(10, 7), dpi=300)
    for i, spec in enumerate(spectra):
        color = colors[i % len(colors)]
        y_norm = (spec['y_abs'] - np.min(spec['y_abs'])) / (np.max(spec['y_abs']) - np.min(spec['y_abs']))
        ax.plot(spec['x'], y_norm, color=color, linewidth=1.2, label=spec['label'])
    ax.set_xlim(max(x_all), min(x_all))
    ax.set_xlabel("Número de onda (cm$^{-1}$)", fontsize=13)
    ax.set_ylabel("Absorbancia Normalizada (u.a.)", fontsize=13)
    ax.set_title("Superposición de Absorbancias Normalizadas", fontsize=12, fontweight='bold', pad=10)
    ax.legend(loc='best', frameon=True, edgecolor='black', fontsize=10)
    ax.grid(True, linestyle='--', alpha=0.5)
    
    # Normalized superposition has fixed Y range [0.0, 1.0]
    ax.set_ylim(-0.05, 1.45)
    annotate_plot(ax, groups_norm, 'absorbance', mode, groups_db, 0.0, 1.0)
    
    plt.tight_layout()
    plt.savefig(out_super, bbox_inches='tight', dpi=300)
    plt.close()

    print("Superposition images generated successfully.")

if __name__ == "__main__":
    main()
