// Hidden bootstrap: bounded UI acknowledgement, local diagnostics, one retry.
#include <windows.h>
#include <wchar.h>
#include <stdio.h>

#define PATH_CAP 32768
#define STARTUP_TIMEOUT_MS 25000
static wchar_t root[PATH_CAP], temporary[PATH_CAP], logfile[PATH_CAP];

static void record(int attempt, const wchar_t *stage, DWORD code, const wchar_t *detail) {
    SYSTEMTIME now;
    GetSystemTime(&now);
    wchar_t message[4096];
    int count = swprintf(message, 4096,
        L"%04u-%02u-%02uT%02u:%02u:%02u.%03uZ pid=%lu attempt=%d %ls code=%lu %.*ls\r\n",
        now.wYear, now.wMonth, now.wDay, now.wHour, now.wMinute, now.wSecond, now.wMilliseconds,
        GetCurrentProcessId(), attempt, stage, code, 2048, detail ? detail : L"");
    if (count <= 0) return;
    char bytes[16384];
    int length = WideCharToMultiByte(CP_UTF8, 0, message, count, bytes, sizeof bytes, NULL, NULL);
    if (!length) return;
    HANDLE file = CreateFileW(logfile, FILE_APPEND_DATA, FILE_SHARE_READ | FILE_SHARE_WRITE,
                              NULL, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    if (file != INVALID_HANDLE_VALUE) {
        DWORD written;
        WriteFile(file, bytes, (DWORD)length, &written, NULL);
        CloseHandle(file);
    }
}

static int attempt_start(int attempt, const wchar_t *powershell, const wchar_t *script) {
    LARGE_INTEGER nonce;
    QueryPerformanceCounter(&nonce);
    wchar_t event_name[160], output_path[PATH_CAP], command[PATH_CAP];
    swprintf(event_name, 160, L"Local\\OWMCLauncherReady-%lu-%llu-%d",
             GetCurrentProcessId(), (unsigned long long)nonce.QuadPart, attempt);
    HANDLE ready = CreateEventW(NULL, TRUE, FALSE, event_name);
    if (!ready) { record(attempt, L"event-failed", GetLastError(), event_name); return 0; }
    int length = swprintf(command, PATH_CAP,
        L"\"%ls\" -NoProfile -NonInteractive -ExecutionPolicy Bypass -WindowStyle Hidden -File \"%ls\" -ReadyEvent \"%ls\"",
        powershell, script, event_name);
    if (length <= 0 || length >= PATH_CAP - 1) {
        record(attempt, L"command-too-long", ERROR_FILENAME_EXCED_RANGE, script);
        CloseHandle(ready); return 0;
    }
    SECURITY_ATTRIBUTES attributes = {sizeof(SECURITY_ATTRIBUTES), NULL, TRUE};
    swprintf(output_path, PATH_CAP, L"%ls\\launcher-powershell-%lu-%llu-%d.log", temporary,
             GetCurrentProcessId(), (unsigned long long)nonce.QuadPart, attempt);
    HANDLE output = CreateFileW(output_path, FILE_APPEND_DATA, FILE_SHARE_READ | FILE_SHARE_WRITE,
                                &attributes, OPEN_ALWAYS, FILE_ATTRIBUTE_NORMAL, NULL);
    HANDLE input = CreateFileW(L"NUL", GENERIC_READ, FILE_SHARE_READ | FILE_SHARE_WRITE,
                               &attributes, OPEN_EXISTING, FILE_ATTRIBUTE_NORMAL, NULL);
    STARTUPINFOW startup = {0};
    startup.cb = sizeof startup;
    startup.dwFlags = STARTF_USESHOWWINDOW;
    startup.wShowWindow = SW_HIDE;
    BOOL inherit = output != INVALID_HANDLE_VALUE && input != INVALID_HANDLE_VALUE;
    if (inherit) {
        startup.dwFlags |= STARTF_USESTDHANDLES;
        startup.hStdInput = input;
        startup.hStdOutput = output;
        startup.hStdError = output;
    }
    PROCESS_INFORMATION process = {0};
    record(attempt, L"starting-powershell", 0, script);
    BOOL started = CreateProcessW(powershell, command, NULL, NULL, inherit, CREATE_NO_WINDOW,
                                  NULL, root, &startup, &process);
    DWORD create_error = started ? 0 : GetLastError();
    if (output != INVALID_HANDLE_VALUE) CloseHandle(output);
    if (input != INVALID_HANDLE_VALUE) CloseHandle(input);
    if (!started) {
        record(attempt, L"create-process-failed", create_error, powershell);
        CloseHandle(ready); return 0;
    }
    wchar_t child[160];
    swprintf(child, 160, L"powershell-pid=%lu", process.dwProcessId);
    record(attempt, L"waiting-ui-ready", 0, child);
    HANDLE waits[2] = {ready, process.hProcess};
    DWORD waited = WaitForMultipleObjects(2, waits, FALSE, STARTUP_TIMEOUT_MS);
    DWORD wait_error = waited == WAIT_FAILED ? GetLastError() : 0;
    BOOL confirmed = WaitForSingleObject(ready, 0) == WAIT_OBJECT_0;
    DWORD exit_code = STILL_ACTIVE;
    GetExitCodeProcess(process.hProcess, &exit_code);
    if (confirmed) {
        record(attempt, L"ui-ready", 0, child);
        if (WaitForSingleObject(process.hProcess, 1500) == WAIT_TIMEOUT) {
            record(attempt, L"bootstrap-exit-timeout", ERROR_TIMEOUT, child);
            TerminateProcess(process.hProcess, ERROR_TIMEOUT);
            WaitForSingleObject(process.hProcess, 1000);
        }
    } else {
        record(attempt, waited == WAIT_TIMEOUT ? L"startup-timeout" : L"no-ui-acknowledgement",
               waited == WAIT_FAILED ? wait_error : exit_code, output_path);
        if (exit_code == STILL_ACTIVE) {
            // Only this attempt's bootstrap process; never its UI/game children.
            TerminateProcess(process.hProcess, ERROR_TIMEOUT);
            WaitForSingleObject(process.hProcess, 1000);
        }
    }
    CloseHandle(process.hThread);
    CloseHandle(process.hProcess);
    CloseHandle(ready);
    return confirmed ? 1 : 0;
}

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE previous, PWSTR arguments, int show) {
    (void)instance; (void)previous; (void)arguments; (void)show;
    DWORD length = GetModuleFileNameW(NULL, root, PATH_CAP);
    if (!length || length >= PATH_CAP) return 1;
    wchar_t *slash = wcsrchr(root, L'\\');
    if (!slash) return 1;
    *slash = 0;
    if (swprintf(temporary, PATH_CAP, L"%ls\\data", root) < 0) return 1;
    CreateDirectoryW(temporary, NULL);
    if (swprintf(temporary, PATH_CAP, L"%ls\\data\\tmp", root) < 0) return 1;
    CreateDirectoryW(temporary, NULL);
    if (swprintf(logfile, PATH_CAP, L"%ls\\launcher-exe.log", temporary) < 0) return 1;
    wchar_t desktop[256] = L"unknown";
    DWORD bytes;
    GetUserObjectInformationW(GetThreadDesktop(GetCurrentThreadId()), UOI_NAME,
                              desktop, sizeof desktop, &bytes);
    record(0, L"begin-desktop", 0, desktop);
    wchar_t script[PATH_CAP], powershell[PATH_CAP];
    if (swprintf(script, PATH_CAP, L"%ls\\tools\\open_project_launcher.ps1", root) < 0) return 1;
    length = GetSystemDirectoryW(powershell, PATH_CAP);
    const wchar_t *suffix = L"\\WindowsPowerShell\\v1.0\\powershell.exe";
    if (!length || length + wcslen(suffix) >= PATH_CAP) {
        record(0, L"system-directory-failed", GetLastError(), L""); return 1;
    }
    wcscat(powershell, suffix);
    for (int attempt = 1; attempt <= 2; ++attempt) {
        if (GetFileAttributesW(script) == INVALID_FILE_ATTRIBUTES) {
            record(attempt, L"script-missing", GetLastError(), script);
        } else if (attempt_start(attempt, powershell, script)) {
            return 0;
        }
        if (attempt == 1) record(attempt, L"retrying-once", 0, L"");
    }
    record(2, L"failed-final", 1, L"启动器未就绪，请查看同目录的启动日志。");
    return 1; // No dialogs, including invisible UI / mutex recovery failures.
}
