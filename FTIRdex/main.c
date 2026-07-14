#include "app_state.h"
#include "gui_render.h"
#include "gw_internal.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

#ifdef _WIN32
  #include <windows.h>
#endif

int main(int argc, char* argv[]) {
    // 1. Initialize Default Functional Groups Database
    groups[ngroups++] = (FuncGroup){"O-H", 3000, 3600, 1};
    groups[ngroups++] = (FuncGroup){"C-H", 2800, 3000, 1};
    groups[ngroups++] = (FuncGroup){"CO2", 2200, 2400, 1};
    groups[ngroups++] = (FuncGroup){"C=O", 1650, 1750, 1};
    groups[ngroups++] = (FuncGroup){"C=C", 1500, 1650, 1};
    groups[ngroups++] = (FuncGroup){"C-O", 1000, 1300, 1};
    groups[ngroups++] = (FuncGroup){"C-O-C", 800, 1000, 1};

    // 2. Initialize GUI Window
    app_win = GW_CreateWindow("FTIRdex - Análisis de espectros", ww, wh);
    if (!app_win) {
        fprintf(stderr, "FTIRdex: Failed to create LibGW window\n");
        return 1;
    }

    // 3. Load UI Fonts
    ui_font = GW_LoadFont("Segoe UI", 12.0f);
    if (!ui_font) {
        ui_font = GW_LoadFont("Consolas", 12.0f);
    }
    title_font = GW_LoadFont("Segoe UI Semibold", 13.5f);
    if (!title_font) {
        title_font = GW_LoadFont("Segoe UI", 13.5f);
    }
    if (!title_font) {
        title_font = GW_LoadFont("Consolas", 13.5f);
    }

    // Set font height measurement
    int temp_w = 0;
    wchar_t wtemp[4] = L"Ap";
    GW_MeasureText(ui_font, wtemp, &temp_w, &font_height);

    // 4. Set Application Custom Icon (Win32 Specific)
#ifdef _WIN32
    {
        HWND hwnd = (HWND)app_win->hwnd;
        HICON hIcon = (HICON)LoadImageW(GetModuleHandleW(NULL), MAKEINTRESOURCEW(1), IMAGE_ICON, 32, 32, LR_DEFAULTCOLOR);
        HICON hIconSm = (HICON)LoadImageW(GetModuleHandleW(NULL), MAKEINTRESOURCEW(1), IMAGE_ICON, 16, 16, LR_DEFAULTCOLOR);
        if (hIcon) {
            SendMessageW(hwnd, WM_SETICON, ICON_BIG, (LPARAM)hIcon);
        } else {
            char err_msg[256];
            snprintf(err_msg, sizeof(err_msg), "LoadImageW (Big) failed. Error: %lu", GetLastError());
            MessageBoxA(hwnd, err_msg, "FTIRdex Resource Debug", MB_OK | MB_ICONWARNING);
        }
        if (hIconSm) {
            SendMessageW(hwnd, WM_SETICON, ICON_SMALL, (LPARAM)hIconSm);
        }
    }
#endif

    GW_ShowWindow(app_win, 1);
    draw_interface(app_win);

    // 5. Main Event Loop
    GW_Event ev;
    while (GW_WaitEvent(&ev)) {
        if (ev.type == GW_EVENT_QUIT) {
            break;
        }

        if (ev.type == GW_EVENT_WINDOW_RESIZE) {
            ww = ev.resize.width;
            wh = ev.resize.height;
            draw_interface(app_win);
        }

        if (ev.type == GW_EVENT_MOUSE_MOTION) {
            if (is_dragging_splitter) {
                splitter_x = ev.mouse_motion.x;
                if (splitter_x < 250) splitter_x = 250;
                if (splitter_x > ww - 300) splitter_x = ww - 300;
                draw_interface(app_win);
            }
        }

        if (ev.type == GW_EVENT_MOUSE_BUTTON_UP) {
            if (ev.mouse_button.button == 1) {
                is_dragging_splitter = 0;
            }
        }

        if (ev.type == GW_EVENT_MOUSE_BUTTON_DOWN) {
            if (is_processing) continue;
            int mx = ev.mouse_button.x;
            int my = ev.mouse_button.y;
            int btn = ev.mouse_button.button;

            // Mode A: Interactive clicks while zoom_mode is active
            if (zoom_mode) {
                if (btn == 1) { // Left click: Click interactive slots or exit zoom mode
                    if (zoom_mode == 2) {
                        GW_Font* zf = GW_LoadFont("Segoe UI", 12.0f * zoom_scale);
                        if (!zf) zf = GW_LoadFont("Consolas", 12.0f * zoom_scale);
                        int box_size = (int)(16 * zoom_scale);
                        int item_spacing = (int)(32 * zoom_scale);
                        int panel_w = (int)(500 * zoom_scale);
                        int sx = (ww - panel_w) / 2;
                        int sy = 120;
                        int clicked_item = 0;
                        
                        for (int i = 0; i < ngroups; i++) {
                            if (sy + item_spacing > wh - 80) break;
                            
                            // Checkbox toggle
                            if (mx >= sx && mx <= sx + box_size && my >= sy && my <= sy + box_size) {
                                groups[i].enabled = !groups[i].enabled;
                                if (super_images_loaded) regenerate_superposition();
                                draw_interface(app_win);
                                clicked_item = 1;
                                break;
                            }
                            
                            // Delete group button
                            int rx = sx + panel_w - (int)(30 * zoom_scale);
                            if (mx >= rx && mx <= rx + box_size && my >= sy && my <= sy + box_size) {
                                for (int j = i; j < ngroups - 1; j++) {
                                    groups[j] = groups[j + 1];
                                }
                                ngroups--;
                                if (super_images_loaded) regenerate_superposition();
                                draw_interface(app_win);
                                clicked_item = 1;
                                break;
                            }
                            sy += item_spacing;
                        }
                        
                        // Inline group addition input field toggles
                        if (!clicked_item) {
                            if (add_state == ADD_STATE_NONE) {
                                if (sy + (int)(30 * zoom_scale) <= wh - 80) {
                                    if (mx >= sx && mx <= sx + panel_w && my >= sy && my <= sy + (int)(26 * zoom_scale)) {
                                        add_state = ADD_STATE_NAME;
                                        add_name[0] = '\0';
                                        add_min_str[0] = '\0';
                                        add_max_str[0] = '\0';
                                        draw_interface(app_win);
                                        clicked_item = 1;
                                    }
                                }
                            } else {
                                if (mx >= sx && mx <= sx + panel_w && my >= sy && my <= sy + (int)(30 * zoom_scale)) {
                                    clicked_item = 1;
                                }
                            }
                        }
                        
                        GW_FreeFont(zf);
                        if (clicked_item) {
                            continue; // Prevent exiting zoom_mode
                        }
                    }
                    
                    // Exit zoom mode
                    zoom_mode = 0;
                    zoom_img = NULL;
                    csv_horizontal_scroll = 0;
                    draw_interface(app_win);
                } else if (btn == 3) { // Right click: Save files from zoom views
                    if (zoom_mode == 3 && nsamples > 0 && samples[current_sample_idx].ncsv_rows > 0) {
                        char* path = GW_ShowSaveFileDialog(app_win, "Guardar reporte como CSV", "Archivos CSV (*.csv)\0*.csv\0");
                        if (path) {
                            char final_path[512];
                            strncpy(final_path, path, sizeof(final_path) - 1);
                            final_path[sizeof(final_path) - 1] = '\0';
                            
                            int len = strlen(final_path);
                            if (len < 4 || _stricmp(final_path + len - 4, ".csv") != 0) {
                                strncat(final_path, ".csv", sizeof(final_path) - len - 1);
                            }
                            
                            char src_csv[256];
                            snprintf(src_csv, sizeof(src_csv), "reporte_picos_valleys_%d.csv", current_sample_idx);
                            copy_file(src_csv, final_path);
                            free(path);
                            GW_ShowMessageBox(app_win, "Reporte Guardado", L"El reporte de picos y valles se ha exportado correctamente.", NULL, 0);
                        }
                    } else if (zoom_mode == 1 && zoom_img) {
                        char* path = GW_ShowSaveFileDialog(app_win, "Guardar imagen como PNG", "Archivos PNG (*.png)\0*.png\0");
                        if (path) {
                            char final_path[512];
                            strncpy(final_path, path, sizeof(final_path) - 1);
                            final_path[sizeof(final_path) - 1] = '\0';
                            
                            int len = strlen(final_path);
                            if (len < 4 || _stricmp(final_path + len - 4, ".png") != 0) {
                                strncat(final_path, ".png", sizeof(final_path) - len - 1);
                            }
                            
                            const char* src_file = NULL;
                            char temp_path[512] = "";
                            
                            if (zoom_img == super_img_trans) src_file = "super_transmittance.png";
                            else if (zoom_img == super_img_super) src_file = "super_superposition.png";
                            else if (zoom_img == super_img_abs) src_file = "super_absorbance.png";
                            else {
                                for (int i = 0; i < nsamples; i++) {
                                    if (zoom_img == samples[i].img_trans) {
                                        snprintf(temp_path, sizeof(temp_path), "transmittance_%d.png", i);
                                        src_file = temp_path;
                                        break;
                                    } else if (zoom_img == samples[i].img_super) {
                                        snprintf(temp_path, sizeof(temp_path), "superposition_%d.png", i);
                                        src_file = temp_path;
                                        break;
                                    } else if (zoom_img == samples[i].img_abs) {
                                        snprintf(temp_path, sizeof(temp_path), "absorbance_%d.png", i);
                                        src_file = temp_path;
                                        break;
                                    }
                                }
                            }
                            
                            if (src_file && src_file[0] != '\0') {
                                copy_file(src_file, final_path);
                                GW_ShowMessageBox(app_win, "Imagen Guardada", L"La imagen se ha exportado correctamente.", NULL, 0);
                            }
                            free(path);
                        }
                    }
                }
                continue;
            }

            // Mode B: Right-click image saving option on right column graphs
            if (btn == 3 && nsamples > 0) {
                int right_x = splitter_x + 5;
                int right_w = ww - right_x;
                int total_cols = nsamples + (super_images_loaded ? 1 : 0);
                if (total_cols > 0 && mx >= right_x && mx <= ww) {
                    int col_w = right_w / total_cols;
                    int c = (mx - right_x) / col_w;
                    if (c >= 0 && c < total_cols) {
                        int slot_h = (wh - 60) / 3;
                        int mid_idx = nsamples / 2;
                        
                        const char* src_file = NULL;
                        char temp_path[512] = "";
                        
                        int slot = -1;
                        if (my >= 42 + 18 + 5 && my < 42 + 18 + slot_h - 5) slot = 1;
                        else if (my >= 42 + 18 + slot_h + 5 && my < 42 + 18 + 2 * slot_h - 5) slot = 2;
                        else if (my >= 42 + 18 + 2 * slot_h + 5 && my < wh - 5) slot = 3;
                        
                        if (slot != -1) {
                            if (super_images_loaded && c == mid_idx) {
                                if (slot == 1) src_file = "super_transmittance.png";
                                else if (slot == 2) src_file = "super_superposition.png";
                                else if (slot == 3) src_file = "super_absorbance.png";
                            } else {
                                int s_idx = (super_images_loaded && c > mid_idx) ? (c - 1) : c;
                                if (samples[s_idx].images_loaded) {
                                    if (slot == 1) snprintf(temp_path, sizeof(temp_path), "transmittance_%d.png", s_idx);
                                    else if (slot == 2) snprintf(temp_path, sizeof(temp_path), "superposition_%d.png", s_idx);
                                    else if (slot == 3) snprintf(temp_path, sizeof(temp_path), "absorbance_%d.png", s_idx);
                                    src_file = temp_path;
                                }
                            }
                        }
                        
                        if (src_file && src_file[0] != '\0') {
                            char* path = GW_ShowSaveFileDialog(app_win, "Guardar imagen como PNG", "Archivos PNG (*.png)\0*.png\0");
                            if (path) {
                                char final_path[512];
                                strncpy(final_path, path, sizeof(final_path) - 1);
                                final_path[sizeof(final_path) - 1] = '\0';
                                
                                int len = strlen(final_path);
                                if (len < 4 || _stricmp(final_path + len - 4, ".png") != 0) {
                                    strncat(final_path, ".png", sizeof(final_path) - len - 1);
                                }
                                
                                copy_file(src_file, final_path);
                                free(path);
                                GW_ShowMessageBox(app_win, "Imagen Guardada", L"La imagen se ha exportado correctamente.", NULL, 0);
                            }
                        }
                    }
                }
            }

            // Mode C: Right-click CSV saving option inside CSV frame bounds
            if (btn == 3 && nsamples > 0 && samples[current_sample_idx].ncsv_rows > 0) {
                if (mx >= 15 && mx < splitter_x - 15 && my >= 345 && my < wh - 20) {
                    char* path = GW_ShowSaveFileDialog(app_win, "Guardar reporte como CSV", "Archivos CSV (*.csv)\0*.csv\0");
                    if (path) {
                        char final_path[512];
                        strncpy(final_path, path, sizeof(final_path) - 1);
                        final_path[sizeof(final_path) - 1] = '\0';
                        
                        int len = strlen(final_path);
                        if (len < 4 || _stricmp(final_path + len - 4, ".csv") != 0) {
                            strncat(final_path, ".csv", sizeof(final_path) - len - 1);
                        }
                        
                        char src_csv[256];
                        snprintf(src_csv, sizeof(src_csv), "reporte_picos_valleys_%d.csv", current_sample_idx);
                        copy_file(src_csv, final_path);
                        free(path);
                        GW_ShowMessageBox(app_win, "Reporte Guardado", L"El reporte de picos y valles se ha exportado correctamente.", NULL, 0);
                    }
                }
            }

            // Mode D: Left clicks (Buttons, Dropdowns, Toggles)
            if (btn == 1) {
                // Overlay dropdown menu option clicks
                if (active_dropdown == 1) {
                    if (mx >= x_smooth && mx <= x_smooth + 140 && my >= 34 && my < 34 + nsmooth_opts * 24) {
                        sel_smooth = (my - 34) / 24;
                        active_dropdown = 0;
                        draw_interface(app_win);
                        continue;
                    } else {
                        active_dropdown = 0;
                        draw_interface(app_win);
                    }
                } else if (active_dropdown == 2) {
                    if (mx >= x_baseline && mx <= x_baseline + 140 && my >= 34 && my < 34 + nbaseline_opts * 24) {
                        sel_baseline = (my - 34) / 24;
                        active_dropdown = 0;
                        draw_interface(app_win);
                        continue;
                    } else {
                        active_dropdown = 0;
                        draw_interface(app_win);
                    }
                } else if (active_dropdown == 3) {
                    if (mx >= x_mode && mx <= x_mode + 140 && my >= 34 && my < 34 + nmode_opts * 24) {
                        sel_mode = (my - 34) / 24;
                        active_dropdown = 0;
                        if (super_images_loaded) regenerate_superposition();
                        draw_interface(app_win);
                        continue;
                    } else {
                        active_dropdown = 0;
                        draw_interface(app_win);
                    }
                } else if (active_dropdown == 4) {
                    if (mx >= x_super && mx <= x_super + 140 && my >= 34 && my < 34 + nsamples * 24) {
                        int idx = (my - 34) / 24;
                        if (idx >= 0 && idx < nsamples) {
                            samples[idx].super_selected = !samples[idx].super_selected;
                            regenerate_superposition();
                        }
                        draw_interface(app_win);
                        continue;
                    } else {
                        active_dropdown = 0;
                        draw_interface(app_win);
                    }
                }

                // Dropdown header activation triggers
                if (mx >= x_smooth && mx <= x_smooth + 140 && my >= 8 && my <= 34) {
                    active_dropdown = (active_dropdown == 1) ? 0 : 1;
                    draw_interface(app_win);
                    continue;
                }
                if (mx >= x_baseline && mx <= x_baseline + 140 && my >= 8 && my <= 34) {
                    active_dropdown = (active_dropdown == 2) ? 0 : 2;
                    draw_interface(app_win);
                    continue;
                }
                if (mx >= x_mode && mx <= x_mode + 140 && my >= 8 && my <= 34) {
                    active_dropdown = (active_dropdown == 3) ? 0 : 3;
                    draw_interface(app_win);
                    continue;
                }
                if (mx >= x_super && mx <= x_super + 140 && my >= 8 && my <= 34) {
                    active_dropdown = (active_dropdown == 4) ? 0 : 4;
                    draw_interface(app_win);
                    continue;
                }

                // Zoom functional groups list header trigger
                if (mx >= 15 && mx < splitter_x - 15 && my >= 50 && my < 80) {
                    zoom_mode = 2;
                    zoom_scale = 1.0f;
                    draw_interface(app_win);
                    continue;
                }

                // Zoom CSV table header trigger
                if (mx >= 15 && mx < splitter_x - 260 && my >= 340 && my < 370) {
                    zoom_mode = 3;
                    zoom_scale = 1.0f;
                    draw_interface(app_win);
                    continue;
                }

                // Splitter bar drag start trigger
                if (mx >= splitter_x - 3 && mx <= splitter_x + 8 && my >= 42) {
                    is_dragging_splitter = 1;
                }

                // Header Action: Open FTIR .txt File Dialog
                if (mx >= x_open && mx <= x_open + 140 && my >= 8 && my <= 34) {
                    if (nsamples >= MAX_SAMPLES) {
                        GW_ShowMessageBox(app_win, "Limite alcanzado", L"No se pueden cargar mas de 8 muestras simultaneamente.", NULL, 0);
                        continue;
                    }
                    char* file = GW_ShowOpenFileDialog(app_win, "Abrir muestra FTIR (.txt)", "Archivos FTIR (*.txt)\0*.txt\0");
                    if (file) {
                        const char* filename = strrchr(file, '\\');
                        if (!filename) filename = strrchr(file, '/');
                        if (!filename) filename = file;
                        else filename++;

                        Sample* s = &samples[nsamples];
                        strncpy(s->filepath, file, sizeof(s->filepath) - 1);
                        s->filepath[sizeof(s->filepath) - 1] = '\0';
                        strncpy(s->filename, filename, sizeof(s->filename) - 1);
                        s->filename[sizeof(s->filename) - 1] = '\0';
                        
                        s->img_trans = NULL;
                        s->img_super = NULL;
                        s->img_abs = NULL;
                        s->images_loaded = 0;
                        s->ncsv_rows = 0;
                        s->csv_scroll_offset = 0;
                        s->super_selected = 1;
                        
                        current_sample_idx = nsamples;
                        nsamples++;
                        free(file);
                        draw_interface(app_win);
                    }
                }

                // Header Action: Run Spectrum Python Processing pipeline
                if (mx >= x_process && mx <= x_process + 145 && my >= 8 && my <= 34) {
                    if (nsamples == 0) {
                        GW_ShowMessageBox(app_win, "Error", L"Por favor cargue al menos una muestra FTIR (.txt) primero.", NULL, 0);
                        continue;
                    }

                    GW_FillRect(app_win, x_process, 8, 145, 26, 0xFF888888);
                    draw_text_button_centered(app_win, ui_font, x_process, 8, 145, 26, "Procesando...", 0xFFFFFFFF);
                    GW_Present(app_win);

                    save_groups_json("temp_groups.json");

                    const char* argv[128];
                    int argc = 0;
                    argv[argc++] = "python";
                    argv[argc++] = "process_ftir.py";
                    
                    argv[argc++] = "--files";
                    for (int i = 0; i < nsamples; i++) {
                        argv[argc++] = samples[i].filepath;
                    }
                    argv[argc++] = "--labels";
                    for (int i = 0; i < nsamples; i++) {
                        argv[argc++] = samples[i].filename;
                    }
                    
                    char idx_strs[MAX_SAMPLES][16];
                    argv[argc++] = "--indices";
                    for (int i = 0; i < nsamples; i++) {
                        snprintf(idx_strs[i], sizeof(idx_strs[i]), "%d", i);
                        argv[argc++] = idx_strs[i];
                    }
                    
                    int super_count = 0;
                    argv[argc++] = "--superimpose-files";
                    for (int i = 0; i < nsamples; i++) {
                        if (samples[i].super_selected) {
                            argv[argc++] = samples[i].filepath;
                            super_count++;
                        }
                    }
                    argv[argc++] = "--superimpose-labels";
                    for (int i = 0; i < nsamples; i++) {
                        if (samples[i].super_selected) {
                            argv[argc++] = samples[i].filename;
                        }
                    }
                    
                    argv[argc++] = "--smooth";
                    argv[argc++] = smooth_opts[sel_smooth];
                    argv[argc++] = "--baseline";
                    argv[argc++] = baseline_opts[sel_baseline];
                    argv[argc++] = "--mode";
                    argv[argc++] = mode_opts[sel_mode];
                    argv[argc++] = "--groups";
                    argv[argc++] = "temp_groups.json";
                    argv[argc++] = NULL;

                    is_processing = 1;
                    int result = run_python_pump_events(argv);
                    is_processing = 0;
                    
                    if (result == 0) {
                        for (int s_idx = 0; s_idx < nsamples; s_idx++) {
                            if (samples[s_idx].img_trans) { GW_FreeImage(samples[s_idx].img_trans); samples[s_idx].img_trans = NULL; }
                            if (samples[s_idx].img_super) { GW_FreeImage(samples[s_idx].img_super); samples[s_idx].img_super = NULL; }
                            if (samples[s_idx].img_abs)   { GW_FreeImage(samples[s_idx].img_abs);   samples[s_idx].img_abs = NULL; }

                            char t_img[256], s_img[256], a_img[256], r_csv[256];
                            snprintf(t_img, sizeof(t_img), "transmittance_%d.png", s_idx);
                            snprintf(s_img, sizeof(s_img), "superposition_%d.png", s_idx);
                            snprintf(a_img, sizeof(a_img), "absorbance_%d.png", s_idx);
                            snprintf(r_csv, sizeof(r_csv), "reporte_picos_valleys_%d.csv", s_idx);

                            samples[s_idx].img_trans = GW_LoadImage(t_img);
                            samples[s_idx].img_super = GW_LoadImage(s_img);
                            samples[s_idx].img_abs   = GW_LoadImage(a_img);
                            samples[s_idx].images_loaded = 1;

                            parse_csv_report(r_csv, s_idx);
                        }

                        if (super_count > 0) {
                            if (super_img_trans) { GW_FreeImage(super_img_trans); super_img_trans = NULL; }
                            if (super_img_super) { GW_FreeImage(super_img_super); super_img_super = NULL; }
                            if (super_img_abs)   { GW_FreeImage(super_img_abs);   super_img_abs = NULL; }

                            super_img_trans = GW_LoadImage("super_transmittance.png");
                            super_img_super = GW_LoadImage("super_superposition.png");
                            super_img_abs   = GW_LoadImage("super_absorbance.png");
                            if (super_img_trans && super_img_super && super_img_abs) {
                                super_images_loaded = 1;
                            }
                        }
                    }

                    remove("temp_groups.json");
                    draw_interface(app_win);
                }

                // Left Panel Action: Checkbox & delete clicks in groups list
                int left_w = splitter_x;
                int list_y = 80;
                for (int i = 0; i < ngroups; i++) {
                    if (list_y + 25 > 290) break;

                    if (mx >= 15 && mx <= 29 && my >= list_y && my <= list_y + 14) {
                        groups[i].enabled = !groups[i].enabled;
                        if (super_images_loaded) regenerate_superposition();
                        draw_interface(app_win);
                        break;
                    }

                    if (mx >= left_w - 35 && mx <= left_w - 19 && my >= list_y && my <= list_y + 14) {
                        for (int j = i; j < ngroups - 1; j++) {
                            groups[j] = groups[j + 1];
                        }
                        ngroups--;
                        if (super_images_loaded) regenerate_superposition();
                        draw_interface(app_win);
                        break;
                    }
                    list_y += 25;
                }

                // Left Panel Action: Inline Add Group Button trigger
                if (add_state == ADD_STATE_NONE && mx >= 15 && mx <= left_w - 15 && my >= 295 && my <= 321) {
                    add_state = ADD_STATE_NAME;
                    add_name[0] = '\0';
                    add_min_str[0] = '\0';
                    add_max_str[0] = '\0';
                    draw_interface(app_win);
                }

                // Left Panel Action: CSV Table navigation buttons
                // Ant button
                if (mx >= left_w - 250 && mx <= left_w - 195 && my >= 340 && my <= 366) {
                    if (current_sample_idx > 0) {
                        current_sample_idx--;
                        draw_interface(app_win);
                    }
                }
                // Sig button
                if (mx >= left_w - 190 && mx <= left_w - 135 && my >= 340 && my <= 366) {
                    if (current_sample_idx < nsamples - 1) {
                        current_sample_idx++;
                        draw_interface(app_win);
                    }
                }
                // Subir button
                if (mx >= left_w - 130 && mx <= left_w - 75 && my >= 340 && my <= 366) {
                    if (nsamples > 0 && samples[current_sample_idx].csv_scroll_offset > 0) {
                        samples[current_sample_idx].csv_scroll_offset--;
                        draw_interface(app_win);
                    }
                }
                // Bajar button
                if (mx >= left_w - 70 && mx <= left_w - 15 && my >= 340 && my <= 366) {
                    if (nsamples > 0 && samples[current_sample_idx].csv_scroll_offset < samples[current_sample_idx].ncsv_rows - 10) {
                        samples[current_sample_idx].csv_scroll_offset++;
                        draw_interface(app_win);
                    }
                }

                // Right Panel Action: Double-click to zoom an image slot
                int right_x = splitter_x + 5;
                int right_w = ww - right_x;
                int total_cols = nsamples + (super_images_loaded ? 1 : 0);
                if (total_cols > 0 && mx >= right_x && mx <= ww) {
                    int col_w = right_w / total_cols;
                    int c = (mx - right_x) / col_w;
                    if (c >= 0 && c < total_cols) {
                        int slot_h = (wh - 60) / 3;
                        int mid_idx = nsamples / 2;
                        
                        int slot = -1;
                        if (my >= 42 + 18 + 5 && my < 42 + 18 + slot_h - 5) slot = 1;
                        else if (my >= 42 + 18 + slot_h + 5 && my < 42 + 18 + 2 * slot_h - 5) slot = 2;
                        else if (my >= 42 + 18 + 2 * slot_h + 5 && my < wh - 5) slot = 3;
                        
                        if (slot != -1) {
                            if (super_images_loaded && c == mid_idx) {
                                if (slot == 1) zoom_img = super_img_trans;
                                else if (slot == 2) zoom_img = super_img_super;
                                else if (slot == 3) zoom_img = super_img_abs;
                                if (zoom_img) { zoom_mode = 1; zoom_scale = 1.0f / 1.1f; }
                            } else {
                                int s_idx = (super_images_loaded && c > mid_idx) ? (c - 1) : c;
                                if (samples[s_idx].images_loaded) {
                                    if (slot == 1) zoom_img = samples[s_idx].img_trans;
                                    else if (slot == 2) zoom_img = samples[s_idx].img_super;
                                    else if (slot == 3) zoom_img = samples[s_idx].img_abs;
                                    if (zoom_img) { zoom_mode = 1; zoom_scale = 1.0f / 1.1f; }
                                }
                            }
                            if (zoom_mode) {
                                draw_interface(app_win);
                                continue;
                            }
                        }
                    }
                }
            }
        }

        // 6. Handle inline keyboard typing for new bands and zoom controls
        if (ev.type == GW_EVENT_KEY_DOWN) {
            if (is_processing) continue;
            int key = ev.key.keycode;
            if (zoom_mode && !(zoom_mode == 2 && add_state != ADD_STATE_NONE)) {
                if (zoom_mode == 3 && (key == GW_KEY_UP || key == GW_KEY_DOWN || key == GW_KEY_LEFT || key == GW_KEY_RIGHT)) {
                    if (key == GW_KEY_UP) {
                        if (nsamples > 0 && samples[current_sample_idx].csv_scroll_offset > 0) samples[current_sample_idx].csv_scroll_offset--;
                    } else if (key == GW_KEY_DOWN) {
                        if (nsamples > 0 && samples[current_sample_idx].csv_scroll_offset < samples[current_sample_idx].ncsv_rows - 10) samples[current_sample_idx].csv_scroll_offset++;
                    } else if (key == GW_KEY_LEFT) {
                        if (current_sample_idx > 0) current_sample_idx--;
                    } else if (key == GW_KEY_RIGHT) {
                        if (current_sample_idx < nsamples - 1) current_sample_idx++;
                    }
                    draw_interface(app_win);
                } else {
                    if (key == '+' || key == '=' || key == GW_KEY_UP) {
                        zoom_scale *= 1.1f;
                        draw_interface(app_win);
                    } else if (key == '-' || key == '_' || key == GW_KEY_DOWN) {
                        zoom_scale /= 1.1f;
                        if (zoom_scale < 0.1f) zoom_scale = 0.1f;
                        draw_interface(app_win);
                    }
                }
            } else if (add_state != ADD_STATE_NONE) {
                if (key == GW_KEY_ESCAPE) {
                    add_state = ADD_STATE_NONE;
                    draw_interface(app_win);
                } else if (key == GW_KEY_ENTER) {
                    if (add_state == ADD_STATE_NAME) {
                        if (strlen(add_name) > 0) {
                            add_state = ADD_STATE_MIN;
                        }
                    } else if (add_state == ADD_STATE_MIN) {
                        if (strlen(add_min_str) > 0) {
                            add_state = ADD_STATE_MAX;
                        }
                    } else if (add_state == ADD_STATE_MAX) {
                        if (strlen(add_max_str) > 0 && ngroups < MAX_GROUPS) {
                            FuncGroup new_g;
                            strncpy(new_g.name, add_name, sizeof(new_g.name) - 1);
                            new_g.name[sizeof(new_g.name) - 1] = '\0';
                            new_g.min_val = atoi(add_min_str);
                            new_g.max_val = atoi(add_max_str);
                            new_g.enabled = 1;
                            
                            groups[ngroups++] = new_g;
                            add_state = ADD_STATE_NONE;
                            if (super_images_loaded) regenerate_superposition();
                        }
                    }
                    draw_interface(app_win);
                } else if (key == GW_KEY_BACKSPACE) {
                    if (add_state == ADD_STATE_NAME) {
                        int len = strlen(add_name);
                        if (len > 0) add_name[len - 1] = '\0';
                    } else if (add_state == ADD_STATE_MIN) {
                        int len = strlen(add_min_str);
                        if (len > 0) add_min_str[len - 1] = '\0';
                    } else if (add_state == ADD_STATE_MAX) {
                        int len = strlen(add_max_str);
                        if (len > 0) add_max_str[len - 1] = '\0';
                    }
                    draw_interface(app_win);
                }
            }
        }

        if (ev.type == GW_EVENT_TEXT_INPUT) {
            if (add_state != ADD_STATE_NONE) {
                char ch = (char)ev.text.character;
                if (add_state == ADD_STATE_NAME) {
                    int len = strlen(add_name);
                    if (len < 60 && isprint((unsigned char)ch) && ch != ',') {
                        add_name[len] = ch;
                        add_name[len+1] = '\0';
                    }
                } else if (add_state == ADD_STATE_MIN) {
                    int len = strlen(add_min_str);
                    if (len < 10 && isdigit((unsigned char)ch)) {
                        add_min_str[len] = ch;
                        add_min_str[len+1] = '\0';
                    }
                } else if (add_state == ADD_STATE_MAX) {
                    int len = strlen(add_max_str);
                    if (len < 10 && isdigit((unsigned char)ch)) {
                        add_max_str[len] = ch;
                        add_max_str[len+1] = '\0';
                    }
                }
                draw_interface(app_win);
            }
        }
    }

    // 7. Cleanup Resources
    for (int i = 0; i < nsamples; i++) {
        if (samples[i].img_trans) GW_FreeImage(samples[i].img_trans);
        if (samples[i].img_super) GW_FreeImage(samples[i].img_super);
        if (samples[i].img_abs) GW_FreeImage(samples[i].img_abs);
    }
    if (super_img_trans) GW_FreeImage(super_img_trans);
    if (super_img_super) GW_FreeImage(super_img_super);
    if (super_img_abs) GW_FreeImage(super_img_abs);

    for (int i = 0; i < MAX_SAMPLES; i++) {
        char t[64], s[64], a[64], c[64];
        snprintf(t, sizeof(t), "transmittance_%d.png", i);
        snprintf(s, sizeof(s), "superposition_%d.png", i);
        snprintf(a, sizeof(a), "absorbance_%d.png", i);
        snprintf(c, sizeof(c), "reporte_picos_valleys_%d.csv", i);
        remove(t);
        remove(s);
        remove(a);
        remove(c);
    }
    remove("super_transmittance.png");
    remove("super_superposition.png");
    remove("super_absorbance.png");

    GW_DestroyWindow(app_win);
    GW_FreeFont(ui_font);
    if (title_font) GW_FreeFont(title_font);

    return 0;
}

#ifdef _WIN32
int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    return main(__argc, __argv);
}
#endif
