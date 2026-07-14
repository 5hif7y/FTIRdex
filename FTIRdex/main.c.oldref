#include "gw_internal.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
  #include <windows.h>
#else
  #include <unistd.h>
#endif

#include "iprocesses.h"

// implement more headers as a mean to refactor some repetitive code
//#include "itimer.h"
//#include "icolors.h"

static int is_processing = 0;
static int ww = 1100;
static int wh = 750;
static struct GW_Window* app_win = NULL;

static void draw_interface(struct GW_Window* win);

static const char* get_smooth_display_name(int idx) {
    if (idx == 0) return "RAW";
    if (idx == 1) return "Móvil (5)";
    if (idx == 2) return "S-Golay (11,2)";
    if (idx == 3) return "Mediana (5)";
    return "";
}

static const char* get_baseline_display_name(int idx) {
    if (idx == 0) return "RAW";
    if (idx == 1) return "Detrend";
    if (idx == 2) return "Lineal";
    if (idx == 3) return "Polinomial (2)";
    if (idx == 4) return "AsLS (1e5)";
    if (idx == 5) return "airPLS (1e5)";
    if (idx == 6) return "arPLS (1e5)";
    return "";
}

static const char* get_mode_display_name(int idx) {
    if (idx == 0) return "Líneas";
    if (idx == 1) return "Cajas";
    if (idx == 2) return "Desactivado";
    if (idx == 3) return "Líneas Comp.";
    return "";
}

static int run_python_pump_events(const char* argv[]) {
    iprocess_t proc;
    if (!iprocess_spawn(&proc, NULL, argv)) {
        return -1;
    }
    while (iprocess_poll(&proc)) {
        GW_Event ev;
        while (GW_PollEvent(&ev)) {
            if (ev.type == GW_EVENT_QUIT) {
                iprocess_terminate(&proc);
                iprocess_close(&proc);
                exit(0);
            }
            if (ev.type == GW_EVENT_WINDOW_RESIZE) {
                ww = ev.resize.width;
                wh = ev.resize.height;
                draw_interface(app_win);
            }
            if (ev.type == GW_EVENT_WINDOW_EXPOSE) {
                draw_interface(app_win);
            }
        }
#ifdef _WIN32
        Sleep(15);
#else
        usleep(15000);
#endif
    }
    int exit_code = proc.exit_code;
    iprocess_close(&proc);
    return exit_code;
}

typedef struct {
    char name[64];
    int min_val;
    int max_val;
    int enabled;
} FuncGroup;

typedef struct {
    char type[32];
    char wavenumber[32];
    char absorbance[32];
    char mapped_group[64];
} CSVRow;

#define MAX_CSV_ROWS 512

#define MAX_GROUPS 128
static FuncGroup groups[MAX_GROUPS];
static int ngroups = 0;

#define MAX_SAMPLES 8
typedef struct {
    char filepath[512];
    char filename[256];
    GW_Image* img_trans;
    GW_Image* img_super;
    GW_Image* img_abs;
    int images_loaded;
    CSVRow csv_rows[MAX_CSV_ROWS];
    int ncsv_rows;
    int csv_scroll_offset;
    int super_selected; // 1 if selected to be superimposed, 0 otherwise
} Sample;

static Sample samples[MAX_SAMPLES];
static int nsamples = 0;
static int current_sample_idx = 0;

// Superposition images
static GW_Image* super_img_trans = NULL;
static GW_Image* super_img_super = NULL;
static GW_Image* super_img_abs = NULL;
static int super_images_loaded = 0;

static GW_Font* ui_font = NULL;
static GW_Font* title_font = NULL;
static int font_height = 16;

static int splitter_x = 480;
static int is_dragging_splitter = 0;

// Add Group Inline State
enum AddState {
    ADD_STATE_NONE = 0,
    ADD_STATE_NAME,
    ADD_STATE_MIN,
    ADD_STATE_MAX
};
static int add_state = ADD_STATE_NONE;
static char add_name[64] = "";
static char add_min_str[32] = "";
static char add_max_str[32] = "";

// Dropdown Menus Config
static const char* smooth_opts[] = {
    "RAW",
    "Moving_Average(5)",
    "Savitzky_Golay(11, 2)",
    "Median_Filter(5)"
};
static int nsmooth_opts = 4;
static int sel_smooth = 0;

static const char* baseline_opts[] = {
    "RAW",
    "detrend",
    "linear_baseline",
    "polynomial_baseline(deg=2)",
    "asls(lam=1e5, p=0.001)",
    "airpls(lam=1e5)",
    "arpls(lam=1e5)"
};
static int nbaseline_opts = 7;
static int sel_baseline = 0;

static const char* mode_opts[] = {
    "lines",
    "boxes",
    "desactivado",
    "lineas-completas"
};
static int nmode_opts = 4;
static int sel_mode = 3; // Default to "lineas-completas"

static int csv_horizontal_scroll = 0;

static int active_dropdown = 0; // 0 = none, 1 = smoothing, 2 = baseline, 3 = mode

// Zoom mode states
static int zoom_mode = 0;
static GW_Image* zoom_img = NULL;
static float zoom_scale = 1.0f;


static void draw_text_utf8(GW_Window *win, GW_Font *font, int x, int y, const char *utf8, uint32_t color) {
    wchar_t wide[1024] = {0};
    GW_UTF8ToWide(utf8, wide, 1024);
    GW_DrawText(win, font, x, y, wide, color);
}

static void draw_text_button_centered(GW_Window* win, GW_Font* font, int bx, int by, int bw, int bh, const char* utf8, uint32_t color) {
    wchar_t wide[256] = {0};
    GW_UTF8ToWide(utf8, wide, 256);
    int tw = 0, th = 0;
    GW_MeasureText(font, wide, &tw, &th);
    int tx = bx + (bw - tw) / 2;
    int ty = by + (bh - th) / 2 + (int)(0.15f * th);
    GW_DrawText(win, font, tx, ty, wide, color);
}

static void copy_file(const char* src, const char* dst) {
    FILE* fsrc = fopen(src, "rb");
    if (!fsrc) return;
    FILE* fdst = fopen(dst, "wb");
    if (!fdst) {
        fclose(fsrc);
        return;
    }
    char buf[4096];
    size_t n;
    while ((n = fread(buf, 1, sizeof(buf), fsrc)) > 0) {
        fwrite(buf, 1, n, fdst);
    }
    fclose(fsrc);
    fclose(fdst);
}

static void save_groups_json(const char* filepath) {
    FILE* f = fopen(filepath, "w");
    if (!f) return;
    fprintf(f, "{\n");
    int first = 1;
    for (int i = 0; i < ngroups; i++) {
        if (groups[i].enabled) {
            if (!first) fprintf(f, ",\n");
            fprintf(f, "  \"%s\": [%d, %d]", groups[i].name, groups[i].min_val, groups[i].max_val);
            first = 0;
        }
    }
    fprintf(f, "\n}\n");
    fclose(f);
}

static void parse_csv_report(const char* filepath, int s_idx) {
    if (s_idx < 0 || s_idx >= nsamples) return;
    FILE* f = fopen(filepath, "r");
    if (!f) return;

    samples[s_idx].ncsv_rows = 0;
    samples[s_idx].csv_scroll_offset = 0;

    char line[512];
    // Skip header line
    if (fgets(line, sizeof(line), f)) {
        // Parsed headers
    }

    while (fgets(line, sizeof(line), f) && samples[s_idx].ncsv_rows < MAX_CSV_ROWS) {
        char* token;
        int r = samples[s_idx].ncsv_rows;

        // Type
        token = strtok(line, ",");
        if (token) {
            strncpy(samples[s_idx].csv_rows[r].type, token, sizeof(samples[s_idx].csv_rows[r].type) - 1);
            samples[s_idx].csv_rows[r].type[sizeof(samples[s_idx].csv_rows[r].type) - 1] = '\0';
        }
        
        // Wavenumber
        token = strtok(NULL, ",");
        if (token) {
            strncpy(samples[s_idx].csv_rows[r].wavenumber, token, sizeof(samples[s_idx].csv_rows[r].wavenumber) - 1);
            samples[s_idx].csv_rows[r].wavenumber[sizeof(samples[s_idx].csv_rows[r].wavenumber) - 1] = '\0';
        }
        
        // Absorbance
        token = strtok(NULL, ",");
        if (token) {
            strncpy(samples[s_idx].csv_rows[r].absorbance, token, sizeof(samples[s_idx].csv_rows[r].absorbance) - 1);
            samples[s_idx].csv_rows[r].absorbance[sizeof(samples[s_idx].csv_rows[r].absorbance) - 1] = '\0';
        }

        // Mapped Group
        token = strtok(NULL, ",");
        if (token) {
            // strip newlines
            int len = strlen(token);
            while (len > 0 && (token[len-1] == '\r' || token[len-1] == '\n')) {
                token[len-1] = '\0';
                len--;
            }
            strncpy(samples[s_idx].csv_rows[r].mapped_group, token, sizeof(samples[s_idx].csv_rows[r].mapped_group) - 1);
            samples[s_idx].csv_rows[r].mapped_group[sizeof(samples[s_idx].csv_rows[r].mapped_group) - 1] = '\0';
        }

        samples[s_idx].ncsv_rows++;
    }

    fclose(f);
}

static void draw_text_truncated(GW_Window* win, GW_Font* font, int x, int y, const char* text, int max_w, uint32_t color) {
    wchar_t wide[512];
    GW_UTF8ToWide(text, wide, 512);
    int tw = 0, th = 0;
    GW_MeasureText(font, wide, &tw, &th);
    if (tw <= max_w) {
        GW_DrawText(win, font, x, y, wide, color);
    } else {
        int len = wcslen(wide);
        while (len > 0 && tw > max_w - 20) {
            wide[--len] = L'\0';
            GW_MeasureText(font, wide, &tw, &th);
        }
        wcscat(wide, L"...");
        GW_DrawText(win, font, x, y, wide, color);
    }
}

static void regenerate_superposition() {
    if (super_img_trans) { GW_FreeImage(super_img_trans); super_img_trans = NULL; }
    if (super_img_super) { GW_FreeImage(super_img_super); super_img_super = NULL; }
    if (super_img_abs)   { GW_FreeImage(super_img_abs);   super_img_abs = NULL; }
    super_images_loaded = 0;

    save_groups_json("temp_groups.json");

    const char* argv[64];
    int argc = 0;
    argv[argc++] = "python";
    argv[argc++] = "process_ftir.py";
    argv[argc++] = "--superimpose-files";
    
    int count = 0;
    for (int i = 0; i < nsamples; i++) {
        if (samples[i].super_selected) {
            argv[argc++] = samples[i].filepath;
            count++;
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

    if (count > 0) {
        is_processing = 1;
        int res = run_python_pump_events(argv);
        is_processing = 0;
        if (res == 0) {
            super_img_trans = GW_LoadImage("super_transmittance.png");
            super_img_super = GW_LoadImage("super_superposition.png");
            super_img_abs   = GW_LoadImage("super_absorbance.png");
            if (super_img_trans && super_img_super && super_img_abs) {
                super_images_loaded = 1;
            }
        }
    }

    remove("temp_groups.json");
}

static int x_smooth = 0;
static int x_baseline = 0;
static int x_mode = 0;
static int x_super = 0;
static int x_open = 0;
static int x_process = 0;

static void compute_header_layout(int ww) {
    int right_margin = 15;
    int gap = 10;
    x_process  = ww - right_margin - 145;
    x_open     = x_process - gap - 140;
    x_super    = x_open - gap - 140;
    x_mode     = x_super - gap - 140;
    x_baseline = x_mode - gap - 140;
    x_smooth   = x_baseline - gap - 140;
}

static void draw_image_fit(GW_Window* win, GW_Image* img, int dx, int dy, int dw, int dh) {
    if (!img) return;
    float img_aspect = (float)img->w / (float)img->h;
    float rect_aspect = (float)dw / (float)dh;
    int draw_w = dw;
    int draw_h = dh;
    int draw_x = dx;
    int draw_y = dy;

    if (img_aspect > rect_aspect) {
        draw_h = (int)(dw / img_aspect);
        draw_y = dy + (dh - draw_h) / 2;
    } else {
        draw_w = (int)(dh * img_aspect);
        draw_x = dx + (dw - draw_w) / 2;
    }
    GW_DrawImage(win, img, draw_x, draw_y, draw_w, draw_h, 0, 0, img->w, img->h, 0, 0);
}

static void draw_interface(GW_Window* win) {
    if (zoom_mode == 1 && zoom_img) {
        GW_Clear(win, 0xFF121212);
        
        const char* mode_str = "";
        const char* name_str = "";
        
        if (zoom_img == super_img_trans) { mode_str = "Transmitancia"; name_str = "Superposición"; }
        else if (zoom_img == super_img_super) { mode_str = "Intensidad normalizada"; name_str = "Superposición"; }
        else if (zoom_img == super_img_abs) { mode_str = "Absorbancia"; name_str = "Superposición"; }
        else {
            for (int i = 0; i < nsamples; i++) {
                if (zoom_img == samples[i].img_trans) {
                    mode_str = "Transmitancia";
                    name_str = samples[i].filename;
                    break;
                } else if (zoom_img == samples[i].img_super) {
                    mode_str = "Intensidad normalizada";
                    name_str = samples[i].filename;
                    break;
                } else if (zoom_img == samples[i].img_abs) {
                    mode_str = "Absorbancia";
                    name_str = samples[i].filename;
                    break;
                }
            }
        }
        
        char header_text[512];
        snprintf(header_text, sizeof(header_text), "Visor de imagen %s - %s - (Click izquierdo para salir. Click derecho para guardar).", mode_str, name_str);
        
        GW_Font* zf = GW_LoadFont("Segoe UI", 12.0f);
        if (!zf) zf = GW_LoadFont("Consolas", 12.0f);
        int zh = 16;
        int zw_tmp = 0;
        wchar_t wtmp_z[4] = L"Ap";
        GW_MeasureText(zf, wtmp_z, &zw_tmp, &zh);
        draw_text_button_centered(win, zf, 0, 50, ww, zh + 10, header_text, 0xFF0078D7);
        GW_FreeFont(zf);

        float img_aspect = (float)zoom_img->w / (float)zoom_img->h;
        float win_aspect = (float)ww / (float)wh;
        int base_w = ww - 40;
        int base_h = wh - 120;
        if (img_aspect > win_aspect) {
            base_h = (int)(base_w / img_aspect);
        } else {
            base_w = (int)(base_h * img_aspect);
        }
        int draw_w = (int)(base_w * zoom_scale);
        int draw_h = (int)(base_h * zoom_scale);
        int draw_x = (ww - draw_w) / 2;
        int draw_y = (wh - draw_h) / 2;
        
        GW_DrawImage(win, zoom_img, draw_x, draw_y, draw_w, draw_h, 0, 0, zoom_img->w, zoom_img->h, 0, 0);
        draw_text_button_centered(win, ui_font, 0, wh - 50, ww, 30, "Teclas +/- o Rueda del mouse para Zoom.", 0xFFCCCCCC);
        GW_Present(win);
        return;
    }

    if (zoom_mode == 2) {
        GW_Clear(win, 0xFF121212);
        GW_Font* zf = GW_LoadFont("Segoe UI", 12.0f * zoom_scale);
        if (!zf) zf = GW_LoadFont("Consolas", 12.0f * zoom_scale);
        int zh = 16;
        int zw_tmp = 0;
        wchar_t wtmp_z[4] = L"Ap";
        GW_MeasureText(zf, wtmp_z, &zw_tmp, &zh);
        draw_text_button_centered(win, zf, 0, 50, ww, zh + 10, "Bases de Datos de Grupos Funcionales (Click izquierdo fuera para salir)", 0xFF0078D7);
        
        int box_size = (int)(16 * zoom_scale);
        int item_spacing = (int)(32 * zoom_scale);
        int panel_w = (int)(500 * zoom_scale);
        int sx = (ww - panel_w) / 2;
        int sy = 120;
        
        for (int i = 0; i < ngroups; i++) {
            if (sy + item_spacing > wh - 80) break;
            
            // Checkbox
            GW_FillRect(win, sx, sy, box_size, box_size, 0xFF3E3E42);
            if (groups[i].enabled) {
                GW_FillRect(win, sx + (int)(3 * zoom_scale), sy + (int)(3 * zoom_scale), box_size - (int)(6 * zoom_scale), box_size - (int)(6 * zoom_scale), 0xFF00FF00);
            }
            
            // Label
            char text[128];
            snprintf(text, sizeof(text), "%s [%d - %d] cm-1", groups[i].name, groups[i].min_val, groups[i].max_val);
            wchar_t wtext[128];
            GW_UTF8ToWide(text, wtext, 128);
            GW_DrawText(win, zf, sx + box_size + (int)(15 * zoom_scale), sy - (int)(2 * zoom_scale), wtext, groups[i].enabled ? 0xFFFFFFFF : 0xFF888888);
            
            // Delete button
            int rx = sx + panel_w - (int)(30 * zoom_scale);
            GW_FillRect(win, rx, sy, box_size, box_size, 0xFF7A2020);
            draw_text_button_centered(win, zf, rx, sy, box_size, box_size, "x", 0xFFFFFFFF);
            
            sy += item_spacing;
        }
        
        // Add Button / Typing state in zoom mode
        if (add_state == ADD_STATE_NONE) {
            if (sy + (int)(30 * zoom_scale) <= wh - 80) {
                GW_FillRect(win, sx, sy, panel_w, (int)(26 * zoom_scale), 0xFF0078D7);
                wchar_t w_add[64];
                GW_UTF8ToWide("+ Agregar Banda Funcional", w_add, 64);
                int tw_add = 0, th_add = 0;
                GW_MeasureText(zf, w_add, &tw_add, &th_add);
                GW_DrawText(win, zf, sx + (panel_w - tw_add) / 2, sy + ((int)(26 * zoom_scale) - th_add) / 2, w_add, 0xFFFFFFFF);
            }
        } else {
            char prompt_msg[256] = "";
            if (add_state == ADD_STATE_NAME) {
                snprintf(prompt_msg, sizeof(prompt_msg), "Nombre del Grupo: %s|", add_name);
            } else if (add_state == ADD_STATE_MIN) {
                snprintf(prompt_msg, sizeof(prompt_msg), "Min (cm-1): %s|", add_min_str);
            } else if (add_state == ADD_STATE_MAX) {
                snprintf(prompt_msg, sizeof(prompt_msg), "Max (cm-1): %s|", add_max_str);
            }
            wchar_t w_prompt[256];
            GW_UTF8ToWide(prompt_msg, w_prompt, 256);
            GW_DrawText(win, zf, sx, sy - (int)(2 * zoom_scale), w_prompt, 0xFFFFFF00);
        }
        
        draw_text_button_centered(win, ui_font, 0, wh - 50, ww, 30, "Teclas +/- o Rueda del mouse para Zoom. Click izquierdo fuera del panel para salir.", 0xFFCCCCCC);
        GW_FreeFont(zf);
        GW_Present(win);
        return;
    }

    if (zoom_mode == 3) {
        GW_Clear(win, 0xFF121212);
        GW_Font* zf = GW_LoadFont("Segoe UI", 12.0f * zoom_scale);
        if (!zf) zf = GW_LoadFont("Consolas", 12.0f * zoom_scale);
        int zh = 16;
        int zw_tmp = 0;
        wchar_t wtmp_z[4] = L"Ap";
        GW_MeasureText(zf, wtmp_z, &zw_tmp, &zh);
        draw_text_button_centered(win, zf, 0, 50, ww, zh + 10, "Visor CSV - Peaks & Valleys Report (Click izquierdo para salir. Click derecho para guardar).", 0xFF0078D7);
        int col_width = (int)(160 * zoom_scale);
        int row_height = (int)(28 * zoom_scale);
        int table_w = col_width * 4;
        
        // Clamp horizontal scroll
        int max_h_scroll = table_w - ww + 40;
        if (max_h_scroll < 0) max_h_scroll = 0;
        if (csv_horizontal_scroll < 0) csv_horizontal_scroll = 0;
        if (csv_horizontal_scroll > max_h_scroll) csv_horizontal_scroll = max_h_scroll;

        int tx = (ww - table_w) / 2 - csv_horizontal_scroll;
        int ty = 120;
        
        GW_FillRect(win, tx, ty, table_w, row_height, 0xFF2D2D30);
        wchar_t w_t1[32], w_t2[32], w_t3[32], w_t4[32];
        GW_UTF8ToWide("Tipo", w_t1, 32);
        GW_UTF8ToWide("Onda (cm-1)", w_t2, 32);
        GW_UTF8ToWide("Absorbancia", w_t3, 32);
        GW_UTF8ToWide("Grupo Mapeado", w_t4, 32);
        GW_DrawText(win, zf, tx + (int)(10 * zoom_scale), ty + (row_height - zh) / 2, w_t1, 0xFFCCCCCC);
        GW_DrawText(win, zf, tx + col_width + (int)(10 * zoom_scale), ty + (row_height - zh) / 2, w_t2, 0xFFCCCCCC);
        GW_DrawText(win, zf, tx + col_width * 2 + (int)(10 * zoom_scale), ty + (row_height - zh) / 2, w_t3, 0xFFCCCCCC);
        GW_DrawText(win, zf, tx + col_width * 3 + (int)(10 * zoom_scale), ty + (row_height - zh) / 2, w_t4, 0xFFCCCCCC);
        
        int r_scroll = (nsamples > 0) ? samples[current_sample_idx].csv_scroll_offset : 0;
        int r_count = (nsamples > 0) ? samples[current_sample_idx].ncsv_rows : 0;
        int sy = ty + row_height + 5;
        for (int i = r_scroll; i < r_count; i++) {
            if (sy + row_height > wh - 80) break;
            if (i % 2 == 0) {
                GW_FillRect(win, tx, sy, table_w, row_height, 0xFF252526);
            }
            uint32_t text_col = strcmp(samples[current_sample_idx].csv_rows[i].type, "Peak") == 0 ? 0xFF00FF00 : 0xFFFFA500;
            wchar_t w_r1[64], w_r2[64], w_r3[64], w_r4[64];
            GW_UTF8ToWide(samples[current_sample_idx].csv_rows[i].type, w_r1, 64);
            GW_UTF8ToWide(samples[current_sample_idx].csv_rows[i].wavenumber, w_r2, 64);
            GW_UTF8ToWide(samples[current_sample_idx].csv_rows[i].absorbance, w_r3, 64);
            GW_UTF8ToWide(samples[current_sample_idx].csv_rows[i].mapped_group, w_r4, 64);
            GW_DrawText(win, zf, tx + (int)(10 * zoom_scale), sy + (row_height - zh) / 2, w_r1, text_col);
            GW_DrawText(win, zf, tx + col_width + (int)(10 * zoom_scale), sy + (row_height - zh) / 2, w_r2, 0xFFFFFFFF);
            GW_DrawText(win, zf, tx + col_width * 2 + (int)(10 * zoom_scale), sy + (row_height - zh) / 2, w_r3, 0xFFFFFFFF);
            GW_DrawText(win, zf, tx + col_width * 3 + (int)(10 * zoom_scale), sy + (row_height - zh) / 2, w_r4, 0xFFFFFFFF);
            sy += row_height;
        }
        draw_text_button_centered(win, ui_font, 0, wh - 65, ww, 20, "Teclas +/- o Rueda del mouse para Zoom. Flecha izquierda/derecha para rotar de tabla de muestra.", 0xFFCCCCCC);
        draw_text_button_centered(win, ui_font, 0, wh - 45, ww, 20, "Flecha abajo/arriba para navegar la tabla verticalmente.", 0xFFCCCCCC);
        GW_FreeFont(zf);
        GW_Present(win);
        return;
    }

    GW_Clear(win, 0xFF1E1E1E);

    // 1. Compute dynamic layout
    compute_header_layout(ww);

    // 1. Header Bar
    GW_FillRect(win, 0, 0, ww, 42, 0xFF2D2D30);

    // File path info (placed at the left of the header, dynamically truncated to not overlap buttons)
    int max_label_width = x_smooth - 25;
    if (max_label_width < 100) max_label_width = 100;
    if (nsamples > 0) {
        char info[256];
        snprintf(info, sizeof(info), "Muestra %d/%d: %s", current_sample_idx + 1, nsamples, samples[current_sample_idx].filename);
        draw_text_button_centered(win, title_font ? title_font : ui_font, 15, 8, max_label_width, 26, info, 0xFF00FF00);
    } else {
        draw_text_button_centered(win, title_font ? title_font : ui_font, 15, 8, max_label_width, 26, "Sin muestras cargadas", 0xFFFF0000);
    }

    // Dropdown 1: Smoothing
    char smooth_lbl[128];
    snprintf(smooth_lbl, sizeof(smooth_lbl), "Suavizar: %s", get_smooth_display_name(sel_smooth));
    GW_FillRect(win, x_smooth, 8, 140, 26, 0xFF2D2D30);
    GW_DrawRect(win, x_smooth, 8, 140, 26, 0xFF3E3E42);
    draw_text_button_centered(win, ui_font, x_smooth, 8, 140, 26, smooth_lbl, 0xFFFFFFFF);

    // Dropdown 2: Baseline
    char base_lbl[128];
    snprintf(base_lbl, sizeof(base_lbl), "L. Base: %s", get_baseline_display_name(sel_baseline));
    GW_FillRect(win, x_baseline, 8, 140, 26, 0xFF2D2D30);
    GW_DrawRect(win, x_baseline, 8, 140, 26, 0xFF3E3E42);
    draw_text_button_centered(win, ui_font, x_baseline, 8, 140, 26, base_lbl, 0xFFFFFFFF);

    // Dropdown 3: Group Marking Mode (lines / boxes)
    char mode_lbl[128];
    snprintf(mode_lbl, sizeof(mode_lbl), "Ver: %s", get_mode_display_name(sel_mode));
    GW_FillRect(win, x_mode, 8, 140, 26, 0xFF2D2D30);
    GW_DrawRect(win, x_mode, 8, 140, 26, 0xFF3E3E42);
    draw_text_button_centered(win, ui_font, x_mode, 8, 140, 26, mode_lbl, 0xFFFFFFFF);

    // Dropdown 4: Superposition samples selector (New)
    GW_FillRect(win, x_super, 8, 140, 26, 0xFF2D2D30);
    GW_DrawRect(win, x_super, 8, 140, 26, 0xFF3E3E42);
    draw_text_button_centered(win, ui_font, x_super, 8, 140, 26, "Superponer", 0xFFFFFFFF);

    // File Selector Button in header
    if (is_processing) {
        GW_FillRect(win, x_open, 8, 140, 26, 0xFF888888);
        draw_text_button_centered(win, ui_font, x_open, 8, 140, 26, "Abrir FTIR .txt", 0xFFCCCCCC);
    } else {
        GW_FillRect(win, x_open, 8, 140, 26, 0xFF0078D7);
        draw_text_button_centered(win, ui_font, x_open, 8, 140, 26, "Abrir FTIR .txt", 0xFFFFFFFF);
    }

    // Process Button in header
    if (is_processing) {
        GW_FillRect(win, x_process, 8, 145, 26, 0xFF888888);
        draw_text_button_centered(win, ui_font, x_process, 8, 145, 26, "Procesando...", 0xFFFFFFFF);
    } else {
        GW_FillRect(win, x_process, 8, 145, 26, 0xFF107C41);
        draw_text_button_centered(win, ui_font, x_process, 8, 145, 26, "Procesar Espectro", 0xFFFFFFFF);
    }

    // 2. Left Panel (Width: splitter_x)
    int left_w = splitter_x;
    int panel_h = wh - 42;

    // A. Title: "Grupos Funcionales a Detectar"
    GW_DrawRect(win, 10, 52, left_w - 20, 26, 0xFF3E3E42);
    draw_text_button_centered(win, title_font ? title_font : ui_font, 10, 52, left_w - 20, 26, "Bases de Datos de Grupos Funcionales (cm-1)", 0xFF0078D7);

    // Render checkable groups list
    int y = 80;
    for (int i = 0; i < ngroups; i++) {
        if (y + 25 > 290) break; // Capped list height

        // Draw checkbox
        GW_FillRect(win, 15, y, 14, 14, 0xFF3E3E42);
        if (groups[i].enabled) {
            GW_FillRect(win, 18, y + 3, 8, 8, 0xFF00FF00);
        }

        // Draw name and range
        char text[128];
        snprintf(text, sizeof(text), "%s [%d - %d]", groups[i].name, groups[i].min_val, groups[i].max_val);
        draw_text_utf8(win, ui_font, 40, y - 1, text, groups[i].enabled ? 0xFFFFFFFF : 0xFF888888);

        // Draw delete button [x]
        GW_FillRect(win, left_w - 35, y, 16, 14, 0xFF2D2D30);
        draw_text_button_centered(win, ui_font, left_w - 35, y, 16, 14, "x", 0xFFFF0000);

        y += 25;
    }

    // Add inline Group Widget
    y = 295;
    if (add_state == ADD_STATE_NONE) {
        GW_FillRect(win, 15, y, left_w - 30, 26, 0xFF3E3E42);
        draw_text_button_centered(win, ui_font, 15, y, left_w - 30, 26, "+ Agregar Banda Funcional", 0xFFFFFFFF);
    } else {
        GW_FillRect(win, 15, y, left_w - 30, 26, 0xFF2D2D30);
        char prompt_msg[128] = "";
        if (add_state == ADD_STATE_NAME) {
            snprintf(prompt_msg, sizeof(prompt_msg), "Nombre: %s|", add_name);
        } else if (add_state == ADD_STATE_MIN) {
            snprintf(prompt_msg, sizeof(prompt_msg), "Min (cm-1): %s|", add_min_str);
        } else if (add_state == ADD_STATE_MAX) {
            snprintf(prompt_msg, sizeof(prompt_msg), "Max (cm-1): %s|", add_max_str);
        }
        draw_text_utf8(win, ui_font, 20, y + 5, prompt_msg, 0xFFFFFF00);
    }

    // B. Title: "Visor CSV - Reporte de Picos"
    char csv_title[256];
    if (nsamples > 0) {
        snprintf(csv_title, sizeof(csv_title), "Visor CSV - Muestra %d/%d", current_sample_idx + 1, nsamples);
    } else {
        snprintf(csv_title, sizeof(csv_title), "Visor CSV - Sin muestras");
    }
    GW_DrawRect(win, 10, 340, left_w - 270, 26, 0xFF3E3E42);
    draw_text_button_centered(win, title_font ? title_font : ui_font, 10, 340, left_w - 270, 26, csv_title, 0xFF0078D7);

    // Four Scroll / Navigate buttons (aligned to left_w - 15, height 26)
    GW_FillRect(win, left_w - 250, 340, 55, 26, 0xFF3E3E42);
    draw_text_button_centered(win, ui_font, left_w - 250, 340, 55, 26, "Ant", 0xFFFFFFFF);

    GW_FillRect(win, left_w - 190, 340, 55, 26, 0xFF3E3E42);
    draw_text_button_centered(win, ui_font, left_w - 190, 340, 55, 26, "Sig", 0xFFFFFFFF);

    GW_FillRect(win, left_w - 130, 340, 55, 26, 0xFF3E3E42);
    draw_text_button_centered(win, ui_font, left_w - 130, 340, 55, 26, "Subir", 0xFFFFFFFF);

    GW_FillRect(win, left_w - 70, 340, 55, 26, 0xFF3E3E42);
    draw_text_button_centered(win, ui_font, left_w - 70, 340, 55, 26, "Bajar", 0xFFFFFFFF);

    // Table Header
    int table_y = 370;
    GW_FillRect(win, 15, table_y, left_w - 30, 22, 0xFF2D2D30);
    draw_text_utf8(win, ui_font, 20, table_y + 3, "Tipo", 0xFFCCCCCC);
    draw_text_utf8(win, ui_font, 90, table_y + 3, "Onda (cm-1)", 0xFFCCCCCC);
    draw_text_utf8(win, ui_font, 200, table_y + 3, "Absorbancia", 0xFFCCCCCC);
    draw_text_utf8(win, ui_font, 310, table_y + 3, "Grupo", 0xFFCCCCCC);

    // Draw CSV rows
    int r_scroll = (nsamples > 0) ? samples[current_sample_idx].csv_scroll_offset : 0;
    int r_count = (nsamples > 0) ? samples[current_sample_idx].ncsv_rows : 0;

    y = table_y + 25;
    for (int i = r_scroll; i < r_count; i++) {
        if (y + 22 > wh - 20) break;

        // Alternate background color
        if (i % 2 == 0) {
            GW_FillRect(win, 15, y, left_w - 30, 20, 0xFF252526);
        }

        uint32_t text_col = strcmp(samples[current_sample_idx].csv_rows[i].type, "Peak") == 0 ? 0xFF00FF00 : 0xFFFFA500;
        draw_text_utf8(win, ui_font, 20, y + 2, samples[current_sample_idx].csv_rows[i].type, text_col);
        draw_text_utf8(win, ui_font, 90, y + 2, samples[current_sample_idx].csv_rows[i].wavenumber, 0xFFFFFFFF);
        draw_text_utf8(win, ui_font, 200, y + 2, samples[current_sample_idx].csv_rows[i].absorbance, 0xFFFFFFFF);
        draw_text_utf8(win, ui_font, 310, y + 2, samples[current_sample_idx].csv_rows[i].mapped_group, 0xFFFFFFFF);

        y += 22;
    }

    // 3. Splitter Bar (Width: 5px)
    GW_FillRect(win, splitter_x, 42, 5, wh - 42, 0xFF3E3E42);

    // 4. Right Panel (Width: ww - splitter_x - 5)
    int right_x = splitter_x + 5;
    int right_w = ww - right_x;
    
    int total_cols = nsamples + (super_images_loaded ? 1 : 0);
    if (total_cols > 0) {
        int col_w = right_w / total_cols;
        int mid_idx = nsamples / 2; // Superposition column index in the middle
        int slot_h = (wh - 60) / 3;

        for (int c = 0; c < total_cols; c++) {
            int cx = right_x + c * col_w;
            
            // Separator vertical line
            if (c > 0) {
                GW_DrawLine(win, cx, 42, cx, wh, 0xFF3E3E42);
            }

            if (super_images_loaded && c == mid_idx) {
                // Draw superposition column
                draw_text_utf8(win, ui_font, cx + 10, 42 + 2, "Superposición", 0xFF00FFFF);
                
                if (super_img_trans) draw_image_fit(win, super_img_trans, cx + 5, 42 + 18 + 5, col_w - 10, slot_h - 10);
                if (super_img_super) draw_image_fit(win, super_img_super, cx + 5, 42 + 18 + slot_h + 5, col_w - 10, slot_h - 10);
                if (super_img_abs)   draw_image_fit(win, super_img_abs, cx + 5, 42 + 18 + 2 * slot_h + 5, col_w - 10, slot_h - 10);
            } else {
                // Draw individual sample column
                int s_idx = (super_images_loaded && c > mid_idx) ? (c - 1) : c;
                
                // Truncate name to fit column width
                draw_text_truncated(win, ui_font, cx + 10, 42 + 2, samples[s_idx].filename, col_w - 20, 0xFF00FF00);
                
                if (samples[s_idx].images_loaded) {
                    if (samples[s_idx].img_trans) draw_image_fit(win, samples[s_idx].img_trans, cx + 5, 42 + 18 + 5, col_w - 10, slot_h - 10);
                    if (samples[s_idx].img_super) draw_image_fit(win, samples[s_idx].img_super, cx + 5, 42 + 18 + slot_h + 5, col_w - 10, slot_h - 10);
                    if (samples[s_idx].img_abs)   draw_image_fit(win, samples[s_idx].img_abs, cx + 5, 42 + 18 + 2 * slot_h + 5, col_w - 10, slot_h - 10);
                } else {
                    draw_text_utf8(win, ui_font, cx + 10, wh / 2 - 10, "Sin procesar", 0xFF888888);
                }
            }
        }
    } else {
        // Placeholder text
        draw_text_utf8(win, ui_font, right_x + 30, wh / 2 - 10, "No hay muestras cargadas. Abra archivos .txt y presione 'Procesar Espectro'.", 0xFF888888);
    }

    // 5. Draw dropdown list overlays if active
    if (active_dropdown == 1) {
        for (int i = 0; i < nsmooth_opts; i++) {
            int oy = 34 + i * 24;
            GW_FillRect(win, x_smooth, oy, 140, 24, 0xFF252526);
            GW_DrawRect(win, x_smooth, oy, 140, 24, 0xFF3E3E42);
            draw_text_button_centered(win, ui_font, x_smooth, oy, 140, 24, get_smooth_display_name(i), i == sel_smooth ? 0xFF00FF00 : 0xFFFFFFFF);
        }
    } else if (active_dropdown == 2) {
        for (int i = 0; i < nbaseline_opts; i++) {
            int oy = 34 + i * 24;
            GW_FillRect(win, x_baseline, oy, 140, 24, 0xFF252526);
            GW_DrawRect(win, x_baseline, oy, 140, 24, 0xFF3E3E42);
            draw_text_button_centered(win, ui_font, x_baseline, oy, 140, 24, get_baseline_display_name(i), i == sel_baseline ? 0xFF00FF00 : 0xFFFFFFFF);
        }
    } else if (active_dropdown == 3) {
        for (int i = 0; i < nmode_opts; i++) {
            int oy = 34 + i * 24;
            GW_FillRect(win, x_mode, oy, 140, 24, 0xFF252526);
            GW_DrawRect(win, x_mode, oy, 140, 24, 0xFF3E3E42);
            draw_text_button_centered(win, ui_font, x_mode, oy, 140, 24, get_mode_display_name(i), i == sel_mode ? 0xFF00FF00 : 0xFFFFFFFF);
        }
    } else if (active_dropdown == 4) {
        for (int i = 0; i < nsamples; i++) {
            int oy = 34 + i * 24;
            GW_FillRect(win, x_super, oy, 140, 24, 0xFF252526);
            GW_DrawRect(win, x_super, oy, 140, 24, 0xFF3E3E42);
            
            // Draw checkbox
            GW_FillRect(win, x_super + 10, oy + 5, 14, 14, 0xFF3E3E42);
            if (samples[i].super_selected) {
                GW_FillRect(win, x_super + 13, oy + 8, 8, 8, 0xFF00FF00);
            }
            
            // Truncate name inside dropdown item
            draw_text_truncated(win, ui_font, x_super + 30, oy + 4, samples[i].filename, 100, samples[i].super_selected ? 0xFFFFFFFF : 0xFF888888);
        }
    }

    GW_Present(win);
}

int main(int argc, char* argv[]) {
    // 1. Initialize Default Functional Groups Database
    groups[ngroups++] = (FuncGroup){"O-H", 3000, 3600, 1};
    groups[ngroups++] = (FuncGroup){"C-H", 2800, 3000, 1};
    groups[ngroups++] = (FuncGroup){"CO2", 2200, 2400, 1};
    groups[ngroups++] = (FuncGroup){"C=O", 1650, 1750, 1};
    groups[ngroups++] = (FuncGroup){"C=C", 1500, 1650, 1};
    groups[ngroups++] = (FuncGroup){"C-O", 1000, 1300, 1};
    groups[ngroups++] = (FuncGroup){"C-O-C", 800, 1000, 1};

    // 2. Initialize GUI
    app_win = GW_CreateWindow("FTIRdex - Analisis de Espectros", ww, wh);
    if (!app_win) {
        fprintf(stderr, "FTIRdex: Failed to create window\n");
        return 1;
    }

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

            if (zoom_mode) {
                if (btn == 1) { // Left click
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
                            
                            // Checkbox
                            if (mx >= sx && mx <= sx + box_size && my >= sy && my <= sy + box_size) {
                                groups[i].enabled = !groups[i].enabled;
                                if (super_images_loaded) regenerate_superposition();
                                draw_interface(app_win);
                                clicked_item = 1;
                                break;
                            }
                            
                            // Delete
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
                            continue; // Do not exit zoom mode
                        }
                    }
                    
                    // Exit Zoom Mode
                    zoom_mode = 0;
                    zoom_img = NULL;
                    csv_horizontal_scroll = 0;
                    draw_interface(app_win);
                } else if (btn == 3) { // Right click inside zoom mode (Saves file)
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

            // Right-click image saving option
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

            // Right-click CSV saving option
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

            if (btn == 1) { // Left clicks
                // Dropdown overlays processing
                if (active_dropdown == 1) {
                    if (mx >= x_smooth && mx <= x_smooth + 140 && my >= 34 && my < 34 + nsmooth_opts * 24) {
                        int idx = (my - 34) / 24;
                        sel_smooth = idx;
                        active_dropdown = 0;
                        draw_interface(app_win);
                        continue;
                    } else {
                        active_dropdown = 0;
                        draw_interface(app_win);
                    }
                } else if (active_dropdown == 2) {
                    if (mx >= x_baseline && mx <= x_baseline + 140 && my >= 34 && my < 34 + nbaseline_opts * 24) {
                        int idx = (my - 34) / 24;
                        sel_baseline = idx;
                        active_dropdown = 0;
                        draw_interface(app_win);
                        continue;
                    } else {
                        active_dropdown = 0;
                        draw_interface(app_win);
                    }
                } else if (active_dropdown == 3) {
                    if (mx >= x_mode && mx <= x_mode + 140 && my >= 34 && my < 34 + nmode_opts * 24) {
                        int idx = (my - 34) / 24;
                        sel_mode = idx;
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

                // Dropdown activation triggers
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

                // Zoom functional groups list trigger
                if (mx >= 15 && mx < splitter_x - 15 && my >= 50 && my < 80) {
                    zoom_mode = 2;
                    zoom_scale = 1.0f;
                    draw_interface(app_win);
                    continue;
                }

                // Zoom CSV table trigger (stops before navigation buttons)
                if (mx >= 15 && mx < splitter_x - 260 && my >= 340 && my < 370) {
                    zoom_mode = 3;
                    zoom_scale = 1.0f;
                    draw_interface(app_win);
                    continue;
                }

                // Splitter drag start
                if (mx >= splitter_x - 3 && mx <= splitter_x + 8 && my >= 42) {
                    is_dragging_splitter = 1;
                }

                // File Dialog trigger (.txt only)
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

                // Process pipeline trigger
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

                // Zoom mode click entry (images)
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
                                if (zoom_img) { zoom_mode = 1; zoom_scale = 1.0f; }
                            } else {
                                int s_idx = (super_images_loaded && c > mid_idx) ? (c - 1) : c;
                                if (samples[s_idx].images_loaded) {
                                    if (slot == 1) zoom_img = samples[s_idx].img_trans;
                                    else if (slot == 2) zoom_img = samples[s_idx].img_super;
                                    else if (slot == 3) zoom_img = samples[s_idx].img_abs;
                                    if (zoom_img) { zoom_mode = 1; zoom_scale = 1.0f; }
                                }
                            }
                            if (zoom_mode) {
                                draw_interface(app_win);
                                continue;
                            }
                        }
                    }
                }

                // Checkbox and delete triggers in group list
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

                // Inline add group widget click
                if (add_state == ADD_STATE_NONE && mx >= 15 && mx <= left_w - 15 && my >= 295 && my <= 321) {
                    add_state = ADD_STATE_NAME;
                    add_name[0] = '\0';
                    add_min_str[0] = '\0';
                    add_max_str[0] = '\0';
                    draw_interface(app_win);
                }

                // CSV scrolling & navigation click
                // Ant button: left_w - 250 to left_w - 195
                if (mx >= left_w - 250 && mx <= left_w - 195 && my >= 340 && my <= 366) {
                    if (current_sample_idx > 0) {
                        current_sample_idx--;
                        draw_interface(app_win);
                    }
                }
                // Sig button: left_w - 190 to left_w - 135
                if (mx >= left_w - 190 && mx <= left_w - 135 && my >= 340 && my <= 366) {
                    if (current_sample_idx < nsamples - 1) {
                        current_sample_idx++;
                        draw_interface(app_win);
                    }
                }
                // Subir button: left_w - 130 to left_w - 75
                if (mx >= left_w - 130 && mx <= left_w - 75 && my >= 340 && my <= 366) {
                    if (nsamples > 0 && samples[current_sample_idx].csv_scroll_offset > 0) {
                        samples[current_sample_idx].csv_scroll_offset--;
                        draw_interface(app_win);
                    }
                }
                // Bajar button: left_w - 70 to left_w - 15
                if (mx >= left_w - 70 && mx <= left_w - 15 && my >= 340 && my <= 366) {
                    if (nsamples > 0 && samples[current_sample_idx].csv_scroll_offset < samples[current_sample_idx].ncsv_rows - 10) {
                        samples[current_sample_idx].csv_scroll_offset++;
                        draw_interface(app_win);
                    }
                }
            }
        }

        // Handle inline keyboard typing for new bands and zoom controls
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

    // Clean up
    for (int i = 0; i < nsamples; i++) {
        if (samples[i].img_trans) GW_FreeImage(samples[i].img_trans);
        if (samples[i].img_super) GW_FreeImage(samples[i].img_super);
        if (samples[i].img_abs) GW_FreeImage(samples[i].img_abs);
    }
    if (super_img_trans) GW_FreeImage(super_img_trans);
    if (super_img_super) GW_FreeImage(super_img_super);
    if (super_img_abs) GW_FreeImage(super_img_abs);

    // Clean up files
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
