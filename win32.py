import ctypes
from ctypes import wintypes
from collections import defaultdict

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
psapi = ctypes.windll.psapi


def enumerate_hwnds(visible_only=True):
    """
    Get list of open HWNDS
    """
    hwnds = []
    def worker(hwnd, context):
        if (visible_only and user32.IsWindowVisible(hwnd)) or not visible_only:
            hwnds.append(hwnd)
        return True
    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    worker_callback = WNDENUMPROC(worker)
    if user32.EnumWindows(worker_callback, None) == 0:
        raise RuntimeError('EnumWindows failed')
    return hwnds


def get_window_title(hwnd):
    """
    Get window title from HWND
    """
    win_title_length = user32.GetWindowTextLengthW(hwnd) + 1
    win_title_buffer = ctypes.create_unicode_buffer(win_title_length)
    user32.GetWindowTextW(hwnd, win_title_buffer, win_title_length) # Note: Ignore return value
    win_title = win_title_buffer.value
    del win_title_buffer
    return win_title if win_title else None


def get_executable_path(hwnd):
    """
    Get path of executable for HWND
    """
     # Get process ID
    process_id = ctypes.c_ulong()
    if user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id)) == 0:
        raise RuntimeError('GetWindowThreadProcessId failed')
    pid = process_id.value

    # Get process handle
    result = None
    PROCESS_QUERY_INFORMATION = 0x0400
    PROCESS_VM_READ = 0x0010
    handle = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if handle:

        # Get process file path
        MAX_PATH = 260
        path_buffer = ctypes.create_unicode_buffer(MAX_PATH + 1)
        if psapi.GetProcessImageFileNameW(handle, path_buffer, MAX_PATH) == 0:
            raise RuntimeError('GetProcessImageFileNameW failed')
        result = path_buffer.value
        del path_buffer
        kernel32.CloseHandle(handle)

    return result


def set_foreground_window(hwnd):
    """
    Make the window foreground
    see: https://stackoverflow.com/questions/916259/win32-bring-a-window-to-top
    """
    SW_SHOW = 5
    SW_MINIMIZE = 6
    SW_RESTORE = 9
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
    user32.ShowWindow(hwnd, SW_MINIMIZE)
    user32.ShowWindow(hwnd, SW_RESTORE)
    user32.ShowWindow(hwnd, SW_SHOW)
    user32.BringWindowToTop(hwnd)
    user32.SetForegroundWindow(hwnd)
    user32.SwitchToThisWindow(hwnd, True)
    user32.SetFocus(hwnd)
    user32.SetActiveWindow(hwnd)


def get_foreground_window():
    return user32.GetForegroundWindow()
    
    
def is_minimized(hwnd):
    return user32.IsIconic(hwnd) != 0
