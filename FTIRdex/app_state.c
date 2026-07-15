#include "app_state.h"
#include "gui_render.h"
#include "iprocesses.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef _WIN32
  #include <windows.h>
#else
  #include <unistd.h>
#endif

// Define Global State Variables
int is_processing = 0;
int ww = 1100;
int wh = 750;
struct GW_Window* app_win = NULL;

FuncGroup groups[MAX_GROUPS];
int ngroups = 0;

Sample samples[MAX_SAMPLES];
int nsamples = 0;
int current_sample_idx = 0;

GW_Image* super_img_trans = NULL;
GW_Image* super_img_super = NULL;
GW_Image* super_img_abs = NULL;
int super_images_loaded = 0;

GW_Font* ui_font = NULL;
GW_Font* title_font = NULL;
int font_height = 16;

int splitter_x = 480;
int is_dragging_splitter = 0;

int add_state = ADD_STATE_NONE;
char add_name[64] = "";
char add_min_str[32] = "";
char add_max_str[32] = "";

const char* smooth_opts[] = {
    "RAW",
    "Moving_Average(5)",
    "Savitzky_Golay(11, 2)",
    "Median_Filter(5)"
};
int nsmooth_opts = 4;
int sel_smooth = 0;

const char* baseline_opts[] = {
    "RAW",
    "detrend",
    "linear_baseline",
    "polynomial_baseline(deg=2)",
    "asls(lam=1e5, p=0.001)",
    "airpls(lam=1e5)",
    "arpls(lam=1e5)"
};
int nbaseline_opts = 7;
int sel_baseline = 0;

const char* mode_opts[] = {
    "lines",
    "boxes",
    "desactivado",
    "lineas-completas"
};
int nmode_opts = 4;
int sel_mode = 3; // Default to "lineas-completas"

int csv_horizontal_scroll = 0;
int active_dropdown = 0;

int zoom_mode = 0;
GW_Image* zoom_img = NULL;
float zoom_scale = 1.0f;

int x_smooth = 0;
int x_baseline = 0;
int x_mode = 0;
int x_super = 0;
int x_open = 0;
int x_process = 0;

const char* get_smooth_display_name(int idx) {
    if (idx == 0) return "RAW";
    if (idx == 1) return "Móvil (5)";
    if (idx == 2) return "S-Golay (11,2)";
    if (idx == 3) return "Mediana (5)";
    return "";
}

const char* get_baseline_display_name(int idx) {
    if (idx == 0) return "RAW";
    if (idx == 1) return "Detrend";
    if (idx == 2) return "Lineal";
    if (idx == 3) return "Polinomial (2)";
    if (idx == 4) return "AsLS (1e5)";
    if (idx == 5) return "airPLS (1e5)";
    if (idx == 6) return "arPLS (1e5)";
    return "";
}

const char* get_mode_display_name(int idx) {
    if (idx == 0) return "Líneas";
    if (idx == 1) return "Cajas";
    if (idx == 2) return "Desactivado";
    if (idx == 3) return "Líneas Comp.";
    return "";
}

int run_python_pump_events(const char* argv[]) {
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

void copy_file(const char* src, const char* dst) {
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

void save_groups_json(const char* filepath) {
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

void parse_csv_report(const char* filepath, int s_idx) {
    if (s_idx < 0 || s_idx >= nsamples) return;
    FILE* f = fopen(filepath, "r");
    if (!f) return;

    samples[s_idx].ncsv_rows = 0;
    samples[s_idx].csv_scroll_offset = 0;

    char line[512];
    if (fgets(line, sizeof(line), f)) {
        // Parsed headers
    }

    while (fgets(line, sizeof(line), f) && samples[s_idx].ncsv_rows < MAX_CSV_ROWS) {
        char* token;
        int r = samples[s_idx].ncsv_rows;

        token = strtok(line, ",");
        if (token) {
            strncpy(samples[s_idx].csv_rows[r].type, token, sizeof(samples[s_idx].csv_rows[r].type) - 1);
            samples[s_idx].csv_rows[r].type[sizeof(samples[s_idx].csv_rows[r].type) - 1] = '\0';
        }
        
        token = strtok(NULL, ",");
        if (token) {
            strncpy(samples[s_idx].csv_rows[r].wavenumber, token, sizeof(samples[s_idx].csv_rows[r].wavenumber) - 1);
            samples[s_idx].csv_rows[r].wavenumber[sizeof(samples[s_idx].csv_rows[r].wavenumber) - 1] = '\0';
        }
        
        token = strtok(NULL, ",");
        if (token) {
            strncpy(samples[s_idx].csv_rows[r].absorbance, token, sizeof(samples[s_idx].csv_rows[r].absorbance) - 1);
            samples[s_idx].csv_rows[r].absorbance[sizeof(samples[s_idx].csv_rows[r].absorbance) - 1] = '\0';
        }

        token = strtok(NULL, ",");
        if (token) {
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

void regenerate_superposition() {
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

static void ensure_dir_exists(const char* filepath) {
    char path[512];
    strncpy(path, filepath, sizeof(path) - 1);
    path[sizeof(path) - 1] = '\0';
    
    char* slash = strchr(path, '/');
    while (slash) {
        *slash = '\0';
#ifdef _WIN32
        CreateDirectoryA(path, NULL);
#endif
        *slash = '/';
        slash = strchr(slash + 1, '/');
    }
    
    slash = strchr(path, '\\');
    while (slash) {
        *slash = '\0';
#ifdef _WIN32
        CreateDirectoryA(path, NULL);
#endif
        *slash = '\\';
        slash = strchr(slash + 1, '\\');
    }
}

void init_default_project_zip() {
    char temp_dir[256];
#ifdef _WIN32
    GetTempPathA(sizeof(temp_dir), temp_dir);
#else
    const char* t = getenv("TMPDIR");
    if (!t) t = "/tmp/";
    strncpy(temp_dir, t, sizeof(temp_dir));
#endif
    
    snprintf(project_zip_path, sizeof(project_zip_path), "%sFTIRdex-temp.zip", temp_dir);
    snprintf(project_vfs_mount_dir, sizeof(project_vfs_mount_dir), "%sFTIRdex-mount", temp_dir);
    
    if (project_vfs) {
        zipvfs_close(project_vfs);
        project_vfs = NULL;
    }
    
    remove(project_zip_path);
    
    project_vfs = zipvfs_open(project_zip_path, 'a');
    zipvfs_mount(project_vfs, project_vfs_mount_dir);

    char plots_dir[512], raw_dir[512];
    snprintf(plots_dir, sizeof(plots_dir), "%s/processed_plots/dummy.txt", project_vfs_mount_dir);
    ensure_dir_exists(plots_dir);
    snprintf(raw_dir, sizeof(raw_dir), "%s/raw_samples/dummy.txt", project_vfs_mount_dir);
    ensure_dir_exists(raw_dir);
}

void load_project_zip(const char* filepath) {
    if (project_vfs) {
        zipvfs_close(project_vfs);
        project_vfs = NULL;
    }
    
    strncpy(project_zip_path, filepath, sizeof(project_zip_path) - 1);
    project_zip_path[sizeof(project_zip_path) - 1] = '\0';

    for (int i = 0; i < nsamples; i++) {
        if (samples[i].img_trans) GW_FreeImage(samples[i].img_trans);
        if (samples[i].img_super) GW_FreeImage(samples[i].img_super);
        if (samples[i].img_abs) GW_FreeImage(samples[i].img_abs);
    }
    nsamples = 0;
    current_sample_idx = 0;
    if (super_img_trans) { GW_FreeImage(super_img_trans); super_img_trans = NULL; }
    if (super_img_super) { GW_FreeImage(super_img_super); super_img_super = NULL; }
    if (super_img_abs)   { GW_FreeImage(super_img_abs);   super_img_abs = NULL; }
    super_images_loaded = 0;

    project_vfs = zipvfs_open(project_zip_path, 'a');
    zipvfs_mount(project_vfs, project_vfs_mount_dir);

    char plots_dir[512], raw_dir[512];
    snprintf(plots_dir, sizeof(plots_dir), "%s/processed_plots/dummy.txt", project_vfs_mount_dir);
    ensure_dir_exists(plots_dir);
    snprintf(raw_dir, sizeof(raw_dir), "%s/raw_samples/dummy.txt", project_vfs_mount_dir);
    ensure_dir_exists(raw_dir);
    
    char** names = NULL;
    size_t count = 0;
    if (zipvfs_list(project_vfs, "raw_samples", &names, &count) == 0) {
        for (size_t i = 0; i < count; i++) {
            if (nsamples < MAX_SAMPLES) {
                Sample* s = &samples[nsamples];
                strncpy(s->filename, names[i], sizeof(s->filename) - 1);
                s->filename[sizeof(s->filename) - 1] = '\0';
                
                snprintf(s->filepath, sizeof(s->filepath), "%s/raw_samples/%s", project_vfs_mount_dir, names[i]);
                s->img_trans = NULL;
                s->img_super = NULL;
                s->img_abs = NULL;
                s->images_loaded = 0;
                s->ncsv_rows = 0;
                s->csv_scroll_offset = 0;
                s->super_selected = 1;
                nsamples++;
            }
            free(names[i]);
        }
        free(names);
    }
    
    extract_and_load_processed_files();
}

void create_new_project_zip(const char* filepath) {
    if (project_vfs) {
        zipvfs_close(project_vfs);
        project_vfs = NULL;
    }
    
    if (strcmp(project_zip_path, filepath) != 0) {
        copy_file(project_zip_path, filepath);
    }
    
    strncpy(project_zip_path, filepath, sizeof(project_zip_path) - 1);
    project_zip_path[sizeof(project_zip_path) - 1] = '\0';
    
    project_vfs = zipvfs_open(project_zip_path, 'a');
    zipvfs_mount(project_vfs, project_vfs_mount_dir);
}

void add_sample_to_project(const char* filepath, const char* filename) {
    if (nsamples >= MAX_SAMPLES) return;

    char dest_path[512];
    snprintf(dest_path, sizeof(dest_path), "%s/raw_samples/%s", project_vfs_mount_dir, filename);
    
    ensure_dir_exists(dest_path);
    copy_file(filepath, dest_path);

    Sample* s = &samples[nsamples];
    strncpy(s->filepath, dest_path, sizeof(s->filepath) - 1);
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
}

void extract_and_load_processed_files() {
    for (int s_idx = 0; s_idx < nsamples; s_idx++) {
        if (samples[s_idx].img_trans) { GW_FreeImage(samples[s_idx].img_trans); samples[s_idx].img_trans = NULL; }
        if (samples[s_idx].img_super) { GW_FreeImage(samples[s_idx].img_super); samples[s_idx].img_super = NULL; }
        if (samples[s_idx].img_abs)   { GW_FreeImage(samples[s_idx].img_abs);   samples[s_idx].img_abs = NULL; }
        samples[s_idx].images_loaded = 0;

        char t_path[512], s_path[512], a_path[512], r_path[512];
        snprintf(t_path, sizeof(t_path), "%s/processed_plots/transmittance_%d.png", project_vfs_mount_dir, s_idx);
        snprintf(s_path, sizeof(s_path), "%s/processed_plots/superposition_%d.png", project_vfs_mount_dir, s_idx);
        snprintf(a_path, sizeof(a_path), "%s/processed_plots/absorbance_%d.png", project_vfs_mount_dir, s_idx);
        snprintf(r_path, sizeof(r_path), "%s/processed_plots/reporte_picos_valleys_%d.csv", project_vfs_mount_dir, s_idx);

        FILE* f = fopen(t_path, "rb");
        if (f) {
            fclose(f);
            samples[s_idx].img_trans = GW_LoadImage(t_path);
        }
        f = fopen(s_path, "rb");
        if (f) {
            fclose(f);
            samples[s_idx].img_super = GW_LoadImage(s_path);
        }
        f = fopen(a_path, "rb");
        if (f) {
            fclose(f);
            samples[s_idx].img_abs = GW_LoadImage(a_path);
        }
        if (samples[s_idx].img_trans && samples[s_idx].img_super && samples[s_idx].img_abs) {
            samples[s_idx].images_loaded = 1;
        }

        f = fopen(r_path, "r");
        if (f) {
            fclose(f);
            parse_csv_report(r_path, s_idx);
        }
    }

    if (super_img_trans) { GW_FreeImage(super_img_trans); super_img_trans = NULL; }
    if (super_img_super) { GW_FreeImage(super_img_super); super_img_super = NULL; }
    if (super_img_abs)   { GW_FreeImage(super_img_abs);   super_img_abs = NULL; }
    super_images_loaded = 0;

    char st_path[512], ss_path[512], sa_path[512];
    snprintf(st_path, sizeof(st_path), "%s/processed_plots/super_transmittance.png", project_vfs_mount_dir);
    snprintf(ss_path, sizeof(ss_path), "%s/processed_plots/super_superposition.png", project_vfs_mount_dir);
    snprintf(sa_path, sizeof(sa_path), "%s/processed_plots/super_absorbance.png", project_vfs_mount_dir);

    FILE* f = fopen(st_path, "rb");
    if (f) {
        fclose(f);
        super_img_trans = GW_LoadImage(st_path);
    }
    f = fopen(ss_path, "rb");
    if (f) {
        fclose(f);
        super_img_super = GW_LoadImage(ss_path);
    }
    f = fopen(sa_path, "rb");
    if (f) {
        fclose(f);
        super_img_abs = GW_LoadImage(sa_path);
    }
    if (super_img_trans && super_img_super && super_img_abs) {
        super_images_loaded = 1;
    }
}

