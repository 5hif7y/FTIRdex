import sys
import os
import json
import argparse
import numpy as np
import matplotlib.pyplot as plt

# Add local library path to sys.path so we don't depend on PYTHONPATH environment variable
local_lib_path = os.path.join(os.path.dirname(__file__), "..", "FTIRlib")
if os.path.exists(local_lib_path):
    sys.path.insert(0, local_lib_path)

# Import from installed ftir_library
from ftir_library import (
    load_data,
    transmittance_to_absorbance,
    plot_config,
    generate_numerical_report,
    preprocess_spectrum,
    detect_peaks_absorbance,
    detect_peaks_transmittance,
    assign_functional_groups,
    FTIR
)

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
    parser = argparse.ArgumentParser(description="Consolidated FTIR Spectral Processing Tool")
    parser.add_argument('--files', nargs='*', default=[], help="Paths to raw spectra files to process individually")
    parser.add_argument('--labels', nargs='*', default=[], help="Labels corresponding to files")
    parser.add_argument('--indices', type=int, nargs='*', default=[], help="Indices mapping to files for naming outputs")
    
    parser.add_argument('--superimpose-files', nargs='*', default=[], help="Paths to files to superimpose")
    parser.add_argument('--superimpose-labels', nargs='*', default=[], help="Labels for superimposed files")
    
    parser.add_argument('--groups', required=True, help="Path to groups JSON configuration")
    parser.add_argument('--smooth', default='RAW', help="Smoothing algorithm option")
    parser.add_argument('--baseline', default='RAW', help="Baseline algorithm option")
    parser.add_argument('--mode', default='lines', help="Peak marker mode")
    parser.add_argument('--out-dir', default='.', help="Directory to save generated plots and reports")
    
    args = parser.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    # Map Spanish mode names
    mode_lower = args.mode.strip().lower()
    if mode_lower in ("cajas", "boxes", "box"):
        mode = "box"
    elif mode_lower in ("lineas", "lines"):
        mode = "lines"
    elif mode_lower == "desactivado":
        mode = "none"
    elif mode_lower == "lineas-completas":
        mode = "full-lines"
    else:
        mode = args.mode

    if not os.path.exists(args.groups):
        print(f"Error: Functional groups JSON file '{args.groups}' not found.")
        sys.exit(1)

    # Load custom functional groups
    try:
        with open(args.groups, 'r', encoding='utf-8') as f:
            custom_groups = json.load(f)
        groups_db = {k: tuple(v) for k, v in custom_groups.items()}
    except Exception as e:
        print(f"Error parsing functional groups JSON: {e}")
        sys.exit(1)

    # 1. Process individual files
    if args.files:
        for filepath, label, s_idx in zip(args.files, args.labels, args.indices):
            if not os.path.exists(filepath):
                print(f"Warning: Input file '{filepath}' not found, skipping.")
                continue

            print(f"Processing spectrum {label} (Index {s_idx})...")
            try:
                x, y_trans = load_data(filepath, FTIR)
            except Exception as e:
                print(f"Error loading FTIR data for {filepath}: {e}")
                continue

            y_abs = transmittance_to_absorbance(y_trans)

            out_trans = os.path.join(args.out_dir, f"transmittance_{s_idx}.png")
            out_abs = os.path.join(args.out_dir, f"absorbance_{s_idx}.png")
            out_super = os.path.join(args.out_dir, f"superposition_{s_idx}.png")
            out_csv = os.path.join(args.out_dir, f"reporte_picos_valleys_{s_idx}.csv")

            # Generate transmittance plot
            plot_config(
                x, y_trans, args.smooth, args.baseline,
                output_image=out_trans,
                space="transmittance",
                groups_db=groups_db,
                prominence=0.5,
                distance=15,
                mode=mode
            )

            # Generate absorbance plot
            plot_config(
                x, y_abs, args.smooth, args.baseline,
                output_image=out_abs,
                space="absorbance",
                groups_db=groups_db,
                prominence=0.01,
                distance=15,
                mode=mode
            )

            # Generate normalized superposition plot for this sample
            try:
                _, y_trans_corr = preprocess_spectrum(x, y_trans, args.smooth, args.baseline, space='transmittance')
                _, y_abs_corr = preprocess_spectrum(x, y_abs, args.smooth, args.baseline, space='absorbance')

                y_trans_norm = (y_trans_corr - np.min(y_trans_corr)) / (np.max(y_trans_corr) - np.min(y_trans_corr))
                y_abs_norm = (y_abs_corr - np.min(y_abs_corr)) / (np.max(y_abs_corr) - np.min(y_abs_corr))

                plt.figure(figsize=(10, 7), dpi=120)
                plt.rcParams["font.family"] = "sans-serif"
                plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Inter", "Liberation Sans"]

                plt.plot(x, y_trans_norm, color='blue', linewidth=1.2, label='Transmitancia (Normalizada)')
                plt.plot(x, y_abs_norm, color='red', linewidth=1.2, label='Absorbancia (Normalizada)')

                plt.xlim(max(x), min(x))
                plt.xlabel("Número de onda (cm$^{-1}$)", fontsize=13)
                plt.ylabel("Intensidad Normalizada (u.a.)", fontsize=13)
                plt.title(f"Superposición (Smooth: {args.smooth}, Baseline: {args.baseline})", fontsize=12, fontweight='bold', pad=10)
                plt.legend(loc='best', frameon=True, edgecolor='black', fontsize=11)
                plt.grid(True, linestyle='--', alpha=0.5)
                plt.tick_params(axis='both', which='major', labelsize=11)

                if mode != 'none':
                    indices, peak_x, peak_y = detect_peaks_absorbance(x, y_abs_corr, prominence=0.01, distance=15)
                    matched_groups, _ = assign_functional_groups(peak_x, groups_db=groups_db)
                    
                    sorted_peaks = []
                    group_order = ["O-H", "C-H", "CO2", "C=O", "C=C", "C-O", "C-O-C"]
                    for k in groups_db.keys():
                        if k not in group_order:
                            group_order.append(k)
                            
                    for group_name in group_order:
                        if group_name not in matched_groups:
                            w_min, w_max = groups_db[group_name]
                            mask = (x >= w_min) & (x <= w_max)
                            if np.any(mask):
                                ext_idx = np.argmax(y_abs_corr[mask])
                                peak_w = x[mask][ext_idx]
                                peak_val = y_abs_corr[mask][ext_idx]
                                if peak_val > 0.01:
                                    matched_groups[group_name] = [peak_w]
                                    
                        if group_name in matched_groups:
                            peak_w = matched_groups[group_name][0]
                            idx = np.abs(x - peak_w).argmin()
                            sorted_peaks.append((x[idx], y_abs_norm[idx], group_name))
                    
                    sorted_peaks.sort(key=lambda item: item[0], reverse=True)
                    plt.ylim(-0.05, 1.45)
                    
                    if mode == 'box':
                        for group_name in group_order:
                            if group_name in matched_groups:
                                w_min, w_max = groups_db[group_name]
                                plt.axvspan(w_min, w_max, facecolor='red', alpha=0.06, edgecolor='red', linestyle='--', linewidth=0.8)
                                plt.text((w_min + w_max) / 2, 1.05, group_name, rotation=270, color='blue', ha='center', va='bottom', fontsize=10, fontweight='bold')
                    elif mode == 'full-lines':
                        alternate = False
                        for i, (peak_w, peak_val, group_name) in enumerate(sorted_peaks):
                            current_offset = 0.10
                            if i > 0 and abs(peak_w - sorted_peaks[i-1][0]) < 160:
                                if not alternate:
                                    current_offset = 0.25
                                    alternate = True
                                else:
                                    current_offset = 0.10
                                    alternate = False
                            else:
                                alternate = False
                            y_text = 1.0 + current_offset
                            plt.plot([peak_w, peak_w], [-0.05, y_text], color='red', linestyle='--', linewidth=1.0)
                            plt.text(peak_w, y_text + 0.02, group_name, rotation=270, color='blue', ha='center', va='bottom', fontsize=10, fontweight='bold')
                    else: # lines mode
                        alternate = False
                        for i, (peak_w, peak_val, group_name) in enumerate(sorted_peaks):
                            current_offset = 0.10
                            if i > 0 and abs(peak_w - sorted_peaks[i-1][0]) < 160:
                                if not alternate:
                                    current_offset = 0.25
                                    alternate = True
                                else:
                                    current_offset = 0.10
                                    alternate = False
                            else:
                                alternate = False
                            y_text = peak_val + current_offset
                            plt.plot([peak_w, peak_w], [peak_val, y_text], color='red', linestyle='--', linewidth=1.0)
                            plt.text(peak_w, y_text + 0.02, group_name, rotation=270, color='blue', ha='center', va='bottom', fontsize=10, fontweight='bold')

                plt.tight_layout()
                plt.savefig(out_super, bbox_inches='tight', dpi=120)
                plt.close()
            except Exception as e:
                print(f"Error plotting superposition for {label}: {e}")

            # Generate peaks/valleys report CSV
            try:
                _, y_abs_corr = preprocess_spectrum(x, y_abs, args.smooth, args.baseline, space='absorbance')
                generate_numerical_report(
                    x, y_abs_corr,
                    sample_name=os.path.basename(filepath),
                    output_csv=out_csv,
                    prominence_peaks=0.01,
                    prominence_valleys=0.01,
                    distance=15,
                    groups_db=groups_db
                )
            except Exception as e:
                print(f"Error generating CSV report for {label}: {e}")

    # 2. Process superposition of multiple files
    if args.superimpose_files:
        print("Generating consolidated superposition plots...")
        spectra = []
        for f, label in zip(args.superimpose_files, args.superimpose_labels):
            try:
                x, y_trans = load_data(f, FTIR)
                y_abs = transmittance_to_absorbance(y_trans)
                
                _, y_trans_corr = preprocess_spectrum(x, y_trans, args.smooth, args.baseline, space='transmittance')
                _, y_abs_corr = preprocess_spectrum(x, y_abs, args.smooth, args.baseline, space='absorbance')
                
                spectra.append({
                    'label': label,
                    'x': x,
                    'y_trans': y_trans_corr,
                    'y_abs': y_abs_corr
                })
            except Exception as e:
                print(f"Error loading superposition target {f}: {e}")

        if spectra:
            groups_trans = {}
            groups_abs = {}
            groups_norm = {}
            
            for spec in spectra:
                indices_abs, peak_x_abs, peak_y_abs = detect_peaks_absorbance(spec['x'], spec['y_abs'], prominence=0.02, distance=15)
                matched_abs, _ = assign_functional_groups(peak_x_abs, groups_db=groups_db)
                
                indices_trans, peak_x_trans, peak_y_trans = detect_peaks_transmittance(spec['x'], spec['y_trans'], prominence=0.02, distance=15)
                matched_trans, _ = assign_functional_groups(peak_x_trans, groups_db=groups_db)
                
                y_norm = (spec['y_abs'] - np.min(spec['y_abs'])) / (np.max(spec['y_abs']) - np.min(spec['y_abs']))
                indices_norm, peak_x_norm, peak_y_norm = detect_peaks_absorbance(spec['x'], y_norm, prominence=0.02, distance=15)
                matched_norm, _ = assign_functional_groups(peak_x_norm, groups_db=groups_db)
                
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

            out_trans = os.path.join(args.out_dir, "super_transmittance.png")
            out_abs = os.path.join(args.out_dir, "super_absorbance.png")
            out_super = os.path.join(args.out_dir, "super_superposition.png")

            plt.rcParams["font.family"] = "sans-serif"
            plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Inter", "Liberation Sans"]
            colors = ['black', 'red', 'blue', 'green', 'orange', 'purple', 'cyan', 'magenta']

            # Superimposed Transmittance
            fig, ax = plt.subplots(figsize=(10, 7), dpi=120)
            for i, spec in enumerate(spectra):
                color = colors[i % len(colors)]
                ax.plot(spec['x'], spec['y_trans'], color=color, linewidth=1.2, label=spec['label'])
            
            x_all = np.concatenate([spec['x'] for spec in spectra])
            ax.set_xlim(max(x_all), min(x_all))
            ax.set_xlabel("Número de onda (cm$^{-1}$)", fontsize=13)
            ax.set_ylabel("Transmitancia (u.a.)", fontsize=13)
            ax.set_title("Superposición de Transmitancias", fontsize=12, fontweight='bold', pad=10)
            ax.legend(loc='best', frameon=True, edgecolor='black', fontsize=10)
            ax.grid(True, linestyle='--', alpha=0.5)
            
            y_min_t = min(np.min(spec['y_trans']) for spec in spectra)
            y_max_t = max(np.max(spec['y_trans']) for spec in spectra)
            y_range_t = y_max_t - y_min_t if y_max_t > y_min_t else 1.0
            ax.set_ylim(y_min_t - 0.45 * y_range_t, y_max_t + 0.05 * y_range_t)
            annotate_plot(ax, groups_trans, 'transmittance', mode, groups_db, y_min_t, y_max_t)
            
            plt.tight_layout()
            plt.savefig(out_trans, bbox_inches='tight', dpi=120)
            plt.close()

            # Superimposed Absorbance
            fig, ax = plt.subplots(figsize=(10, 7), dpi=120)
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
            plt.savefig(out_abs, bbox_inches='tight', dpi=120)
            plt.close()

            # Superimposed Normalized
            fig, ax = plt.subplots(figsize=(10, 7), dpi=120)
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
            
            ax.set_ylim(-0.05, 1.45)
            annotate_plot(ax, groups_norm, 'absorbance', mode, groups_db, 0.0, 1.0)
            
            plt.tight_layout()
            plt.savefig(out_super, bbox_inches='tight', dpi=120)
            plt.close()

            print("Consolidated superposition images generated successfully.")

    print("FTIR analysis pipeline finished successfully.")

if __name__ == "__main__":
    main()
