import ctypes
import time
import sdl2
import sys
from collections import defaultdict
import wmi
import os
import signal
import subprocess

sdl2.SDL_Init(sdl2.SDL_INIT_JOYSTICK)

e = sdl2.SDL_Event()
devices = []

timestamps = defaultdict(int)
counters = defaultdict(int)

while True:
    time.sleep(0.01)
    if sdl2.SDL_PollEvent(ctypes.byref(e)) == 1:
       
        if e.type == sdl2.SDL_JOYDEVICEADDED:
            print(f'Joystick #{e.jdevice.which}')
            devices.append(sdl2.SDL_JoystickOpen(e.jdevice.which))
            
        #elif e.type == sdl2.SDL_JOYBUTTONUP:
        #print(f'[{device_id}] {e.jbutton.button}: Up')
        
        #elif e.type == sdl2.SDL_JOYAXISMOTION:
        #print(f'[{device_id}] {e.jaxis.axis}: {e.jaxis.value}')

        elif e.type == sdl2.SDL_JOYBUTTONDOWN:
        
            b = e.jbutton
            key = f'{b.which}::{b.button}'
            
            dt = b.timestamp - timestamps[key]
            timestamps[key] = b.timestamp
            
            if (dt < 300):
                counters[key] += 1
            else:
                counters[key] = 1
    
    if counters['0::8'] >= 3 and counters['1::8'] >= 3:
        counters['0::8'] = counters['1::8'] = 0
        
        print('Got joystick input')
        os.system('shutdown /r /t 0')
        sys.exit()
        
        if False:
            f = wmi.WMI()
            processes = f.Win32_Process(['ExecutablePath', 'ProcessId'])
            
            restart_path = None
            RETROARCH_EXE = 'retroarch.exe'
            EMUSTATION_EXE = 'emulationstation.exe'

            for process in processes:
                
                exe = process.ExecutablePath
                pid = process.ProcessId
                
                if exe is None:
                    continue
                
                exe = exe.lower()
                if RETROARCH_EXE in exe or EMUSTATION_EXE in exe:
                    print(f'Killing "{exe}" (PID: {pid})')
                    os.kill(pid, signal.SIGTERM)
                    if EMUSTATION_EXE in exe:
                        restart_path = exe
                    
            if restart_path is not None:
                print(f'Restarting: "{restart_path}"')
                subprocess.Popen(restart_path)
            
            print('Done')

