import sys
from time import sleep
sys.path.append('c:\\arcade\\marqueemanager')
import win32

sleep(6)

while True:

    print('Foreground helper running')

    try:
        hwnd_retroarch = None
        hwnd_emustation = None

        hwnds = win32.enumerate_hwnds()
        for hwnd in hwnds:
            path = win32.get_executable_path(hwnd)
            if path is None:
                continue
            path = path.lower()
            if 'retroarch.exe' in path:
                hwnd_retroarch = hwnd
            if 'emulationstation.exe' in path:
                hwnd_emustation = hwnd

        hwnd_front = win32.get_foreground_window()
        if hwnd_emustation is not None and hwnd_emustation != hwnd_front and hwnd_retroarch is None and not win32.is_minimized(hwnd_emustation):
            print('Set emulationstation.exe to foreground')
            win32.set_foreground_window(hwnd_emustation)
            sys.exit()
    
    except Exception as ex:
        print(f'Exception: {ex}')

    sleep(4)

