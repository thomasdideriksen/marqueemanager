import os
import sys
sys.path.append('c:\\arcade\\marqueemanager')
import marqueemanager as mm

mm.start_marquee()

mm.clear()
mm.set_background_color(0, 0, 0)

rom_path = sys.argv[1]
rom_system = sys.argv[3]
rom_name = os.path.splitext(os.path.basename(rom_path))[0]

video_path = f'.emulationstation\\downloaded_media\\{rom_system}\\videos\\{rom_name}.mp4'

if os.path.isfile(video_path):
    mm.play_video(video_path, margin=0, alpha=0.35, fit='fill')
    
marquee_image_path = f'.emulationstation\\downloaded_media\\{rom_system}\\marquees\\{rom_name}.png'

if os.path.isfile(marquee_image_path):
    mm.pulse_image(marquee_image_path)

mm.flyout('C:\\arcade\\marqueemanager\\graphics\\buttons_flattened.svg', 0.6, 0.45, 8);