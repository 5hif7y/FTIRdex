#ifndef APP_STATE_H
#define APP_STATE_H

#include "gw.h"

// System and limit constants
#define MAX_CSV_ROWS 512
#define MAX_GROUPS 128
#define MAX_SAMPLES 8

// Inline group addition states
enum AddState {
    ADD_STATE_NONE = 0,
    ADD_STATE_NAME,
    ADD_STATE_MIN,
    ADD_STATE_MAX
};

// Data Structures
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
    int super_selected;
} Sample;

// App State Globals (External)
extern int is_processing;
extern int ww;
extern int wh;
extern struct GW_Window* app_win;

extern FuncGroup groups[MAX_GROUPS];
extern int ngroups;

extern Sample samples[MAX_SAMPLES];
extern int nsamples;
extern int current_sample_idx;

// Superposition images
extern GW_Image* super_img_trans;
extern GW_Image* super_img_super;
extern GW_Image* super_img_abs;
extern int super_images_loaded;

// Fonts
extern GW_Font* ui_font;
extern GW_Font* title_font;
extern int font_height;

// Splitter Layout
extern int splitter_x;
extern int is_dragging_splitter;

// Add Group Inline State
extern int add_state;
extern char add_name[64];
extern char add_min_str[32];
extern char add_max_str[32];

// Dropdown Options
extern const char* smooth_opts[];
extern int nsmooth_opts;
extern int sel_smooth;

extern const char* baseline_opts[];
extern int nbaseline_opts;
extern int sel_baseline;

extern const char* mode_opts[];
extern int nmode_opts;
extern int sel_mode;

extern int csv_horizontal_scroll;
extern int active_dropdown;

// Zoom configuration
extern int zoom_mode;
extern GW_Image* zoom_img;
extern float zoom_scale;

// Header layout coordinates
extern int x_smooth;
extern int x_baseline;
extern int x_mode;
extern int x_super;
extern int x_open;
extern int x_process;

// String formatting helpers
const char* get_smooth_display_name(int idx);
const char* get_baseline_display_name(int idx);
const char* get_mode_display_name(int idx);

// I/O & Processing logic functions
void copy_file(const char* src, const char* dst);
void save_groups_json(const char* filepath);
void parse_csv_report(const char* filepath, int s_idx);
void regenerate_superposition(void);
int run_python_pump_events(const char* argv[]);

#endif // APP_STATE_H
