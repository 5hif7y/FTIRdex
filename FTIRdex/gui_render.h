#ifndef GUI_RENDER_H
#define GUI_RENDER_H

#include "gw.h"

// Core UI Rendering API
void draw_interface(GW_Window* win);

// Helpers
void draw_text_utf8(GW_Window* win, GW_Font* font, int x, int y, const char* utf8, uint32_t color);
void draw_text_button_centered(GW_Window* win, GW_Font* font, int bx, int by, int bw, int bh, const char* utf8, uint32_t color);
void draw_text_truncated(GW_Window* win, GW_Font* font, int x, int y, const char* text, int max_w, uint32_t color);
void draw_image_fit(GW_Window* win, GW_Image* img, int dx, int dy, int dw, int dh);
void compute_header_layout(int ww);

#endif // GUI_RENDER_H
