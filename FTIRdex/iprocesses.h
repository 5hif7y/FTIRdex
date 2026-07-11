#ifndef IPROCESSES_H
#define IPROCESSES_H

#include <string.h>
#include <stdlib.h>
#include <stdio.h>

#ifdef _WIN32
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
typedef HANDLE process_handle_t;
#else
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#include <signal.h>
typedef pid_t process_handle_t;
#endif

// Struct representing a spawned process
typedef struct {
    process_handle_t handle;
    int is_running;
    int exit_code;
} iprocess_t;

#ifdef _WIN32
static void iprocess_escape_arg(const char* arg, char* out, int max_len) {
    int len = (int)strlen(arg);
    int needs_quotes = 0;
    for (int i = 0; i < len; i++) {
        if (arg[i] == ' ' || arg[i] == '\t' || arg[i] == '\n' || arg[i] == '\v' || arg[i] == '\"' || arg[i] == '&' || arg[i] == '|') {
            needs_quotes = 1;
            break;
        }
    }
    if (!needs_quotes && len > 0) {
        strncpy(out, arg, max_len - 1);
        out[max_len - 1] = '\0';
        return;
    }
    int p = 0;
    if (p < max_len - 1) out[p++] = '\"';
    for (int i = 0; i < len; i++) {
        int backslashes = 0;
        while (i < len && arg[i] == '\\') {
            backslashes++;
            i++;
        }
        if (i == len) {
            for (int k = 0; k < backslashes * 2; k++) {
                if (p < max_len - 1) out[p++] = '\\';
            }
            break;
        } else if (arg[i] == '\"') {
            for (int k = 0; k < backslashes * 2 + 1; k++) {
                if (p < max_len - 1) out[p++] = '\\';
            }
            if (p < max_len - 1) out[p++] = '\"';
        } else {
            for (int k = 0; k < backslashes; k++) {
                if (p < max_len - 1) out[p++] = '\\';
            }
            if (p < max_len - 1) out[p++] = arg[i];
        }
    }
    if (p < max_len - 1) out[p++] = '\"';
    out[p] = '\0';
}
#endif

// Spawns a process. argv is a NULL-terminated list of strings.
// executable can be NULL (in which case argv[0] is searched or used as the command name).
static int iprocess_spawn(iprocess_t* proc, const char* executable, const char* argv[]) {
#ifdef _WIN32
    char cmd_line[32768] = "";
    int p = 0;
    for (int i = 0; argv[i] != NULL; i++) {
        char escaped[8192] = "";
        iprocess_escape_arg(argv[i], escaped, sizeof(escaped));
        int esc_len = (int)strlen(escaped);
        if (p > 0 && p < (int)sizeof(cmd_line) - 2) {
            cmd_line[p++] = ' ';
            cmd_line[p] = '\0';
        }
        if (p + esc_len < (int)sizeof(cmd_line) - 1) {
            strcpy(cmd_line + p, escaped);
            p += esc_len;
        }
    }

    wchar_t wcmd_line[32768];
    MultiByteToWideChar(CP_UTF8, 0, cmd_line, -1, wcmd_line, 32768);

    wchar_t* wexecutable = NULL;
    wchar_t wexec_buf[4096];
    if (executable != NULL) {
        MultiByteToWideChar(CP_UTF8, 0, executable, -1, wexec_buf, 4096);
        wexecutable = wexec_buf;
    }

    STARTUPINFOW si;
    PROCESS_INFORMATION pi;
    memset(&si, 0, sizeof(si));
    si.cb = sizeof(si);
    memset(&pi, 0, sizeof(pi));

    BOOL success = CreateProcessW(
        wexecutable,
        wcmd_line,
        NULL,
        NULL,
        FALSE,
        CREATE_NO_WINDOW,
        NULL,
        NULL,
        &si,
        &pi
    );

    if (!success) {
        proc->handle = NULL;
        proc->is_running = 0;
        proc->exit_code = -1;
        return 0;
    }

    CloseHandle(pi.hThread);
    proc->handle = pi.hProcess;
    proc->is_running = 1;
    proc->exit_code = 0;
    return 1;
#else
    pid_t pid = fork();
    if (pid < 0) {
        proc->handle = -1;
        proc->is_running = 0;
        proc->exit_code = -1;
        return 0;
    }
    if (pid == 0) {
        execvp(executable ? executable : argv[0], (char* const*)argv);
        exit(127);
    }
    proc->handle = pid;
    proc->is_running = 1;
    proc->exit_code = 0;
    return 1;
#endif
}

// Polls the status of the process. Returns 1 if still running, 0 if exited.
static int iprocess_poll(iprocess_t* proc) {
#ifdef _WIN32
    if (!proc->is_running || proc->handle == NULL) {
        return 0;
    }
    DWORD exit_code = 0;
    if (GetExitCodeProcess(proc->handle, &exit_code)) {
        if (exit_code == STILL_ACTIVE) {
            return 1;
        } else {
            proc->exit_code = (int)exit_code;
            proc->is_running = 0;
            return 0;
        }
    }
    return 0;
#else
    if (!proc->is_running || proc->handle <= 0) {
        return 0;
    }
    int status = 0;
    pid_t res = waitpid(proc->handle, &status, WNOHANG);
    if (res == 0) {
        return 1; // Still running
    } else if (res > 0) {
        proc->is_running = 0;
        if (WIFEXITED(status)) {
            proc->exit_code = WEXITSTATUS(status);
        } else if (WIFSIGNALED(status)) {
            proc->exit_code = -WTERMSIG(status);
        } else {
            proc->exit_code = -1;
        }
        return 0;
    } else {
        proc->is_running = 0;
        proc->exit_code = -1;
        return 0;
    }
#endif
}

// Forcefully terminates the process.
static void iprocess_terminate(iprocess_t* proc) {
#ifdef _WIN32
    if (proc->handle != NULL) {
        TerminateProcess(proc->handle, 1);
        proc->is_running = 0;
    }
#else
    if (proc->handle > 0) {
        kill(proc->handle, SIGKILL);
        proc->is_running = 0;
    }
#endif
}

// Closes any OS handles associated with the process.
static void iprocess_close(iprocess_t* proc) {
#ifdef _WIN32
    if (proc->handle != NULL) {
        CloseHandle(proc->handle);
        proc->handle = NULL;
    }
#else
    // No descriptor resources to close in Unix for pid
#endif
}

#endif // IPROCESSES_H
