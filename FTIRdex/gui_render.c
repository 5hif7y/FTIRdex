#include "gui_render.h"
#include "app_state.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

uint32_t get_theme_color(uint32_t color) {
    if (!theme_light) {
        // Adjust dark theme colors for high aesthetics and deuteranopia/protanopia daltonism support
        if (color == 0xFF00FF00) return 0xFF00F5A0; // Bright green -> Mint/emerald green (highly visible for red-green colorblindness)
        if (color == 0xFFFF0000) return 0xFFFF5C5C; // Bright red -> High-contrast Coral/Vermillion
        return color;
    }
    
    uint8_t a = (color >> 24) & 0xFF;
    uint8_t r = (color >> 16) & 0xFF;
    uint8_t g = (color >> 8) & 0xFF;
    uint8_t b = color & 0xFF;
    
    // Specially selected pre-defined colors for Light Mode (Sleek Slate/Light Theme & Colorblind Accessibility):
    if (color == 0xFF1E1E1E) return 0xFFF8F9FA; // Main background -> Very soft clean off-white
    if (color == 0xFF2D2D30) return 0xFFE9ECEF; // Header bar -> Elegant light gray
    if (color == 0xFF121212) return 0xFFFFFFFF; // Zoom background -> Pure White
    if (color == 0xFF0078D7) return 0xFF005A9E; // Selection/Active -> Premium dark blue
    if (color == 0xFF252526) return 0xFFDEE2E6; // Hover/List selected -> Light gray
    if (color == 0xFF3E3E42) return 0xFFCED4DA; // Borders -> Neutral light gray
    if (color == 0xFF555555) return 0xFFADB5BD; // Inner borders -> Neutral medium gray
    if (color == 0xFF2B2B2B) return 0xFFE9ECEF;
    
    // Text and Indicator colors in Light Mode (High Contrast & Colorblind Friendly)
    if (color == 0xFFFFFFFF) return 0xFF212529; // White text -> Dark slate black
    if (color == 0xFFCCCCCC) return 0xFF495057; // Light gray text -> Slate gray text
    if (color == 0xFF888888) return 0xFF6C757D; // Dark gray text -> Medium slate gray
    if (color == 0xFF00FF00) return 0xFF087F5B; // Bright green -> Deep teal green (distinguishable from red for protanopes)
    if (color == 0xFFFF0000) return 0xFFC92A2A; // Bright red -> Deep crimson/vermillion
    if (color == 0xFF00FFFF) return 0xFF0B7285; // Bright cyan -> Dark turquoise
    
    // Fallback: Algorithmic inversion
    return (a << 24) | ((255 - r) << 16) | ((255 - g) << 8) | (255 - b);
}

static void GW_Clear_themed(GW_Window* win, uint32_t color) {
    (GW_Clear)(win, get_theme_color(color));
}
#define GW_Clear GW_Clear_themed

static void GW_FillRect_themed(GW_Window* win, int x, int y, int w, int h, uint32_t color) {
    (GW_FillRect)(win, x, y, w, h, get_theme_color(color));
}
#define GW_FillRect GW_FillRect_themed

static void GW_DrawRect_themed(GW_Window* win, int x, int y, int w, int h, uint32_t color) {
    (GW_DrawRect)(win, x, y, w, h, get_theme_color(color));
}
#define GW_DrawRect GW_DrawRect_themed

static void GW_DrawLine_themed(GW_Window* win, int x1, int y1, int x2, int y2, uint32_t color) {
    (GW_DrawLine)(win, x1, y1, x2, y2, get_theme_color(color));
}
#define GW_DrawLine GW_DrawLine_themed

static void GW_DrawPixel_themed(GW_Window* win, int x, int y, uint32_t color) {
    (GW_DrawPixel)(win, x, y, get_theme_color(color));
}
#define GW_DrawPixel GW_DrawPixel_themed

static void GW_DrawText_themed(GW_Window* win, GW_Font* font, int x, int y, const wchar_t* text, uint32_t color) {
    (GW_DrawText)(win, font, x, y, text, get_theme_color(color));
}
#define GW_DrawText GW_DrawText_themed

void draw_text_utf8(GW_Window *win, GW_Font *font, int x, int y, const char *utf8, uint32_t color) {
    wchar_t wide[1024] = {0};
    GW_UTF8ToWide(utf8, wide, 1024);
    GW_DrawText(win, font, x, y, wide, color);
}

void draw_text_button_centered(GW_Window* win, GW_Font* font, int bx, int by, int bw, int bh, const char* utf8, uint32_t color) {
    wchar_t wide[256] = {0};
    GW_UTF8ToWide(utf8, wide, 256);
    int tw = 0, th = 0;
    GW_MeasureText(font, wide, &tw, &th);
    int tx = bx + (bw - tw) / 2;
    int ty = by + (bh - th) / 2 + (int)(0.15f * th);
    GW_DrawText(win, font, tx, ty, wide, color);
}

void draw_text_truncated(GW_Window* win, GW_Font* font, int x, int y, const char* text, int max_w, uint32_t color) {
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

void compute_header_layout(int ww) {
    int right_margin = 15;
    int gap = 10;
    x_process  = ww - right_margin - 145;
    x_open     = x_process - gap - 140;
    x_super    = x_open - gap - 140;
    x_mode     = x_super - gap - 140;
    x_baseline = x_mode - gap - 140;
    x_smooth   = x_baseline - gap - 140;
}

void draw_image_fit(GW_Window* win, GW_Image* img, int dx, int dy, int dw, int dh) {
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

// Private rendering sub-modules
static void draw_zoom_image(GW_Window* win) {
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
}

static void draw_zoom_groups(GW_Window* win) {
    GW_Clear(win, 0xFF121212);
    GW_Font* zf = GW_LoadFont("Segoe UI", 12.0f * zoom_scale);
    if (!zf) zf = GW_LoadFont("Consolas", 12.0f * zoom_scale);
    int zh = 16;
    int zw_tmp = 0;
    wchar_t wtmp_z[4] = L"Ap";
    GW_MeasureText(zf, wtmp_z, &zw_tmp, &zh);
    draw_text_button_centered(win, zf, 0, 50, ww, zh + 10, "Tabla de Datos de Grupos Funcionales (Click izquierdo fuera para salir)", 0xFF0078D7);
    
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
}

static void draw_zoom_csv(GW_Window* win) {
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
}

static void draw_zoom_menu(GW_Window* win) {
    GW_Clear(win, 0xFF121212);
    
    GW_Font* zf = GW_LoadFont("Segoe UI", 12.0f * zoom_scale);
    if (!zf) zf = GW_LoadFont("Consolas", 12.0f * zoom_scale);
    int zh = 16;
    int zw_tmp = 0;
    wchar_t wtmp_z[4] = L"Ap";
    GW_MeasureText(zf, wtmp_z, &zw_tmp, &zh);
    
    draw_text_button_centered(win, zf, 0, 50, ww, zh + 10, "Menú de Opciones (Click izquierdo fuera para salir)", 0xFF0078D7);

    int item_h = (int)(40 * zoom_scale);
    int item_w = (int)(250 * zoom_scale);
    int item_spacing = (int)(50 * zoom_scale);
    
    int sx = (ww / 2) - item_w - (int)(20 * zoom_scale);
    if (menu_active_subview == 0) {
        sx = (ww - item_w) / 2;
    }
    int sy = 150;

    const char* menu_opts[] = {
        "Nuevo Proyecto (.ftirzip)",
        "Abrir Proyecto (.ftirzip)",
        "Guardar Proyecto (.ftirzip)",
        "Colores de Interfaz",
        "Sobre este software",
        "Salir"
    };

    for (int i = 0; i < 6; i++) {
        GW_FillRect(win, sx, sy, item_w, item_h, 0xFF2D2D30);
        GW_DrawRect(win, sx, sy, item_w, item_h, 0xFF3E3E42);
        draw_text_button_centered(win, zf, sx, sy, item_w, item_h, menu_opts[i], 0xFFFFFFFF);
        sy += item_spacing;
    }

    if (menu_active_subview == 1) { // Sobre este software
        int rx = (ww / 2) + (int)(20 * zoom_scale);
        int ry = 150;
        int rw = (int)(320 * zoom_scale);
        int rh = (int)(240 * zoom_scale);
        
        GW_FillRect(win, rx, ry, rw, rh, 0xFF1E1E1E);
        GW_DrawRect(win, rx, ry, rw, rh, 0xFF3E3E42);

        GW_Font* title_f = GW_LoadFont("Segoe UI Semibold", 13.5f * zoom_scale);
        if (!title_f) title_f = zf;
        
        draw_text_button_centered(win, title_f, rx, ry + (int)(10 * zoom_scale), rw, (int)(30 * zoom_scale), "Sobre FTIRdex", 0xFF00FF00);
        
        int ty = ry + (int)(60 * zoom_scale);
        int dy = (int)(24 * zoom_scale);
        
        draw_text_utf8(win, zf, rx + (int)(20 * zoom_scale), ty, "Inicio de Dev: Lunes 01/06/2026", 0xFFFFFFFF);
        
        char comp_str[128];
        snprintf(comp_str, sizeof(comp_str), "Compilación: %s %s", __DATE__, __TIME__);
        draw_text_utf8(win, zf, rx + (int)(20 * zoom_scale), ty + dy, comp_str, 0xFFFFFFFF);
        
        draw_text_utf8(win, zf, rx + (int)(20 * zoom_scale), ty + 2 * dy, "Dueño: Ing. Mendoza Nicolás", 0xFFFFFFFF);
        draw_text_utf8(win, zf, rx + (int)(20 * zoom_scale), ty + 3 * dy, "DEV: Alemán Matías (5hif7y)", 0xFFFFFFFF);
        draw_text_utf8(win, zf, rx + (int)(20 * zoom_scale), ty + 4 * dy, "Versión: 0.0.5", 0xFF00FFFF);

        if (title_f != zf) GW_FreeFont(title_f);
    } else if (menu_active_subview == 2) { // Colores de Interfaz (Stub)
        int rx = (ww / 2) + (int)(20 * zoom_scale);
        int ry = 150;
        int rw = (int)(320 * zoom_scale);
        int rh = (int)(240 * zoom_scale);
        
        GW_FillRect(win, rx, ry, rw, rh, 0xFF1E1E1E);
        GW_DrawRect(win, rx, ry, rw, rh, 0xFF3E3E42);

        GW_Font* title_f = GW_LoadFont("Segoe UI Semibold", 13.5f * zoom_scale);
        if (!title_f) title_f = zf;

        draw_text_button_centered(win, title_f, rx, ry + (int)(10 * zoom_scale), rw, (int)(30 * zoom_scale), "Colores de Interfaz", 0xFF00FF00);
        
        int ty = ry + (int)(60 * zoom_scale);
        int dy = (int)(24 * zoom_scale);
        draw_text_utf8(win, zf, rx + (int)(20 * zoom_scale), ty, "Configuración de Colores (.ini)", 0xFFFFFFFF);
        draw_text_utf8(win, zf, rx + (int)(20 * zoom_scale), ty + dy, "(Próximamente disponible)", 0xFF888888);
        draw_text_utf8(win, zf, rx + (int)(20 * zoom_scale), ty + 2 * dy, "Paleta Actual: Dark-Tech-Modern", 0xFF00FFFF);

        if (title_f != zf) GW_FreeFont(title_f);
    }

    draw_text_button_centered(win, ui_font, 0, wh - 50, ww, 30, "Teclas +/- o Rueda del mouse para Zoom. Click izquierdo fuera para cerrar el menú.", 0xFFCCCCCC);
    GW_FreeFont(zf);
    GW_Present(win);
}

static void draw_dropdowns(GW_Window* win) {
    if (active_dropdown == 1) {
        for (int i = 0; i < nsmooth_opts; i++) {
            int oy = 34 + i * 24;
            GW_FillRect(win, x_smooth, oy, 140, 24, 0xFF252526);
            GW_DrawRect(win, x_smooth, oy, 140, 24, 0xFF3E3E42);
            draw_text_button_centered(win, ui_font, x_smooth, oy, 140, 24, get_smooth_display_name(i), (i == sel_smooth) ? 0xFF00FF00 : 0xFFFFFFFF);
        }
    } else if (active_dropdown == 2) {
        for (int i = 0; i < nbaseline_opts; i++) {
            int oy = 34 + i * 24;
            GW_FillRect(win, x_baseline, oy, 140, 24, 0xFF252526);
            GW_DrawRect(win, x_baseline, oy, 140, 24, 0xFF3E3E42);
            draw_text_button_centered(win, ui_font, x_baseline, oy, 140, 24, get_baseline_display_name(i), (i == sel_baseline) ? 0xFF00FF00 : 0xFFFFFFFF);
        }
    } else if (active_dropdown == 3) {
        for (int i = 0; i < nmode_opts; i++) {
            int oy = 34 + i * 24;
            GW_FillRect(win, x_mode, oy, 140, 24, 0xFF252526);
            GW_DrawRect(win, x_mode, oy, 140, 24, 0xFF3E3E42);
            draw_text_button_centered(win, ui_font, x_mode, oy, 140, 24, get_mode_display_name(i), (i == sel_mode) ? 0xFF00FF00 : 0xFFFFFFFF);
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
}

void draw_interface(GW_Window* win) {
    if (zoom_mode == 1 && zoom_img) {
        draw_zoom_image(win);
        return;
    }
    if (zoom_mode == 2) {
        draw_zoom_groups(win);
        return;
    }
    if (zoom_mode == 3) {
        draw_zoom_csv(win);
        return;
    }
    if (zoom_mode == 4) {
        draw_zoom_menu(win);
        return;
    }

    GW_Clear(win, 0xFF1E1E1E);

    // 1. Compute dynamic layout
    compute_header_layout(ww);

    // 1. Header Bar
    GW_FillRect(win, 0, 0, ww, 42, 0xFF2D2D30);

    // Menu Button (vertical ellipsis)
    GW_FillRect(win, 12, 8, 26, 26, 0xFF3E3E42);
    GW_DrawRect(win, 12, 8, 26, 26, 0xFF555555);
    // Draw three 2x2 dots stacked vertically manually (bypassing font rendering limits)
    GW_FillRect(win, 24, 14, 2, 2, 0xFFFFFFFF);
    GW_FillRect(win, 24, 20, 2, 2, 0xFFFFFFFF);
    GW_FillRect(win, 24, 26, 2, 2, 0xFFFFFFFF);

    // Theme Toggle Button
    GW_FillRect(win, 44, 8, 26, 26, 0xFF3E3E42);
    GW_DrawRect(win, 44, 8, 26, 26, 0xFF555555);
    if (!theme_light) {
        // Draw crescent moon vectorially (Yellow U+263D moon)
        int mcx = 57, mcy = 21;
        for (int dy = -6; dy <= 6; dy++) {
            for (int dx = -6; dx <= 6; dx++) {
                if (dx*dx + dy*dy <= 36) {
                    int mx = dx - 3;
                    int my = dy;
                    if (mx*mx + my*my > 36) {
                        (GW_DrawPixel)(win, mcx + dx, mcy + dy, 0xFFFFFF00);
                    }
                }
            }
        }
    } else {
        // Draw sun vectorially (Orange-yellow U+2600 sun)
        int scx = 57, scy = 21;
        for (int dy = -4; dy <= 4; dy++) {
            for (int dx = -4; dx <= 4; dx++) {
                if (dx*dx + dy*dy <= 16) {
                    (GW_DrawPixel)(win, scx + dx, scy + dy, 0xFFFFA500);
                }
            }
        }
        for (int i = -7; i <= 7; i++) {
            if (abs(i) >= 5) {
                (GW_DrawPixel)(win, scx + i, scy, 0xFFFFA500);
                (GW_DrawPixel)(win, scx, scy + i, 0xFFFFA500);
                (GW_DrawPixel)(win, scx + i * 7 / 10, scy + i * 7 / 10, 0xFFFFA500);
                (GW_DrawPixel)(win, scx + i * 7 / 10, scy - i * 7 / 10, 0xFFFFA500);
            }
        }
    }

    // File path info (placed at the left of the header, dynamically truncated to not overlap buttons)
    int max_label_width = x_smooth - 86;
    if (max_label_width < 100) max_label_width = 100;
    if (nsamples > 0) {
        char info[256];
        snprintf(info, sizeof(info), "Muestra %d/%d: %s", current_sample_idx + 1, nsamples, samples[current_sample_idx].filename);
        draw_text_button_centered(win, title_font ? title_font : ui_font, 76, 8, max_label_width, 26, info, 0xFF00FF00);
    } else {
        draw_text_button_centered(win, title_font ? title_font : ui_font, 76, 8, max_label_width, 26, "Sin muestras cargadas", 0xFFFF0000);
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

    // Dropdown 4: Superposition samples selector
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
    int groups_bottom_y = (int)(wh * 0.42f);
    if (groups_bottom_y < 250) groups_bottom_y = 250;
    if (groups_bottom_y > wh - 250) groups_bottom_y = wh - 250;

    // A. Title: "Grupos Funcionales a Detectar"
    GW_DrawRect(win, 10, 52, left_w - 20, 26, 0xFF3E3E42);
    draw_text_button_centered(win, title_font ? title_font : ui_font, 10, 52, left_w - 20, 26, "Tabla de Datos de Grupos Funcionales (cm-1)", 0xFF0078D7);

    // Render checkable groups list as a table
    int gt_table_w = left_w - 30;
    int gt_col0_w = (int)(gt_table_w * 0.18f);
    int gt_col1_w = (int)(gt_table_w * 0.36f);
    int gt_col2_w = (int)(gt_table_w * 0.31f);
    int gt_col3_w = gt_table_w - gt_col0_w - gt_col1_w - gt_col2_w;

    int gt_x0 = 15 + (gt_col0_w - 14) / 2; // Center checkbox/header icon
    int gt_x1 = 15 + gt_col0_w + 5;
    int gt_x2 = 15 + gt_col0_w + gt_col1_w + 5;
    int gt_x3 = 15 + gt_col0_w + gt_col1_w + gt_col2_w + (gt_col3_w - 16) / 2; // Center delete button

    // Table Header
    int gtable_y = 80;
    GW_FillRect(win, 15, gtable_y, gt_table_w, 22, 0xFF2D2D30);
    draw_text_button_centered(win, ui_font, 15, gtable_y, gt_col0_w, 22, "Activo", 0xFFCCCCCC);
    draw_text_utf8(win, ui_font, gt_x1, gtable_y + 3, "Grupo Funcional", 0xFFCCCCCC);
    draw_text_utf8(win, ui_font, gt_x2, gtable_y + 3, "Banda", 0xFFCCCCCC);
    draw_text_button_centered(win, ui_font, 15 + gt_col0_w + gt_col1_w + gt_col2_w, gtable_y, gt_col3_w, 22, "Eliminar", 0xFFCCCCCC);

    int y = gtable_y + 25;
    for (int i = 0; i < ngroups; i++) {
        if (y + 22 > groups_bottom_y - 30) break;

        // Alternating row background
        if (i % 2 == 0) {
            GW_FillRect(win, 15, y, gt_table_w, 20, 0xFF252526);
        }

        // Draw checkbox
        int cb_x = 15 + (gt_col0_w - 14) / 2;
        int cb_y = y + 3;
        GW_FillRect(win, cb_x, cb_y, 14, 14, 0xFF3E3E42);
        if (groups[i].enabled) {
            GW_FillRect(win, cb_x + 3, cb_y + 3, 8, 8, 0xFF00FF00);
        }

        // Format range text [min - max]
        char range_str[64];
        snprintf(range_str, sizeof(range_str), "[%d - %d]", groups[i].min_val, groups[i].max_val);

        // Draw name truncated to prevent overlapping the range
        draw_text_truncated(win, ui_font, gt_x1, y + 2, groups[i].name, gt_col1_w - 10, groups[i].enabled ? 0xFFFFFFFF : 0xFF888888);
        
        // Draw range text
        draw_text_truncated(win, ui_font, gt_x2, y + 2, range_str, gt_col2_w - 10, groups[i].enabled ? 0xFFCCCCCC : 0xFF666666);

        // Draw delete button [x]
        int db_x = 15 + gt_col0_w + gt_col1_w + gt_col2_w + (gt_col3_w - 16) / 2;
        int db_y = y + 3;
        GW_FillRect(win, db_x, db_y, 16, 14, 0xFF2D2D30);
        draw_text_button_centered(win, ui_font, db_x, db_y, 16, 14, "x", 0xFFFF0000);

        y += 22;
    }

    // Add inline Group Widget
    y = groups_bottom_y - 28;
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
    GW_DrawRect(win, 10, groups_bottom_y + 10, left_w - 270, 26, 0xFF3E3E42);
    draw_text_button_centered(win, title_font ? title_font : ui_font, 10, groups_bottom_y + 10, left_w - 270, 26, csv_title, 0xFF0078D7);

    // Four Scroll / Navigate buttons
    GW_FillRect(win, left_w - 250, groups_bottom_y + 10, 55, 26, 0xFF3E3E42);
    draw_text_button_centered(win, ui_font, left_w - 250, groups_bottom_y + 10, 55, 26, "Ant", 0xFFFFFFFF);

    GW_FillRect(win, left_w - 190, groups_bottom_y + 10, 55, 26, 0xFF3E3E42);
    draw_text_button_centered(win, ui_font, left_w - 190, groups_bottom_y + 10, 55, 26, "Sig", 0xFFFFFFFF);

    GW_FillRect(win, left_w - 130, groups_bottom_y + 10, 55, 26, 0xFF3E3E42);
    draw_text_button_centered(win, ui_font, left_w - 130, groups_bottom_y + 10, 55, 26, "Subir", 0xFFFFFFFF);

    GW_FillRect(win, left_w - 70, groups_bottom_y + 10, 55, 26, 0xFF3E3E42);
    draw_text_button_centered(win, ui_font, left_w - 70, groups_bottom_y + 10, 55, 26, "Bajar", 0xFFFFFFFF);

    // CSV Table dimensions
    int table_w = left_w - 30;
    int col0_w = (int)(table_w * 0.18f);
    int col1_w = (int)(table_w * 0.28f);
    int col2_w = (int)(table_w * 0.26f);
    int col3_w = table_w - col0_w - col1_w - col2_w;

    int x0 = 15 + 5;
    int x1 = 15 + col0_w + 5;
    int x2 = 15 + col0_w + col1_w + 5;
    int x3 = 15 + col0_w + col1_w + col2_w + 5;

    // Table Header
    int table_y = groups_bottom_y + 40;
    GW_FillRect(win, 15, table_y, table_w, 22, 0xFF2D2D30);
    draw_text_utf8(win, ui_font, x0, table_y + 3, "Tipo", 0xFFCCCCCC);
    draw_text_utf8(win, ui_font, x1, table_y + 3, "Onda (cm-1)", 0xFFCCCCCC);
    draw_text_utf8(win, ui_font, x2, table_y + 3, "Absorbancia", 0xFFCCCCCC);
    draw_text_utf8(win, ui_font, x3, table_y + 3, "Grupo", 0xFFCCCCCC);

    // Draw CSV rows
    int r_scroll = (nsamples > 0) ? samples[current_sample_idx].csv_scroll_offset : 0;
    int r_count = (nsamples > 0) ? samples[current_sample_idx].ncsv_rows : 0;

    y = table_y + 25;
    for (int i = r_scroll; i < r_count; i++) {
        if (y + 22 > wh - 20) break;

        if (i % 2 == 0) {
            GW_FillRect(win, 15, y, table_w, 20, 0xFF252526);
        }

        uint32_t text_col = strcmp(samples[current_sample_idx].csv_rows[i].type, "Peak") == 0 ? 0xFF00FF00 : 0xFFFFA500;
        draw_text_utf8(win, ui_font, x0, y + 2, samples[current_sample_idx].csv_rows[i].type, text_col);
        draw_text_utf8(win, ui_font, x1, y + 2, samples[current_sample_idx].csv_rows[i].wavenumber, 0xFFFFFFFF);
        draw_text_utf8(win, ui_font, x2, y + 2, samples[current_sample_idx].csv_rows[i].absorbance, 0xFFFFFFFF);
        draw_text_truncated(win, ui_font, x3, y + 2, samples[current_sample_idx].csv_rows[i].mapped_group, col3_w - 10, 0xFFFFFFFF);

        y += 22;
    }

    // 3. Splitter Bar (Width: 5px)
    GW_FillRect(win, splitter_x, 42, 5, wh - 42, 0xFF3E3E42);

    // 4. Right Panel (Width: ww - splitter_x - 5)
    int right_x = splitter_x + 5;
    int right_w = ww - right_x;
    int total_cols = nsamples + ((super_images_loaded && nsamples > 1) ? 1 : 0);
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

            if (super_images_loaded && nsamples > 1 && c == mid_idx) {
                // Draw superposition column
                draw_text_utf8(win, ui_font, cx + 10, 42 + 2, "Superposición", 0xFF00FFFF);
                
                if (super_img_trans) draw_image_fit(win, super_img_trans, cx + 5, 42 + 18 + 5, col_w - 10, slot_h - 10);
                if (super_img_super) draw_image_fit(win, super_img_super, cx + 5, 42 + 18 + slot_h + 5, col_w - 10, slot_h - 10);
                if (super_img_abs)   draw_image_fit(win, super_img_abs, cx + 5, 42 + 18 + 2 * slot_h + 5, col_w - 10, slot_h - 10);
            } else {
                // Draw individual sample column
                int s_idx = (super_images_loaded && nsamples > 1 && c > mid_idx) ? (c - 1) : c;
                
                // Truncate name to fit column width
                draw_text_truncated(win, ui_font, cx + 10, 42 + 2, samples[s_idx].filename, col_w - 20, 0xFF00FF00);
                
                if (samples[s_idx].images_loaded) {
                    if (samples[s_idx].img_trans) draw_image_fit(win, samples[s_idx].img_trans, cx + 5, 42 + 18 + 5, col_w - 10, slot_h - 10);
                    if (samples[s_idx].img_super) draw_image_fit(win, samples[s_idx].img_super, cx + 5, 42 + 18 + slot_h + 5, col_w - 10, slot_h - 10);
                    if (samples[s_idx].img_abs)   draw_image_fit(win, samples[s_idx].img_abs, cx + 5, 42 + 18 + 2 * slot_h + 5, col_w - 10, slot_h - 10);
                }
            }
        }
    }

    // Render Overlay Dropdown Menus (if active)
    draw_dropdowns(win);

    GW_Present(win);
}
