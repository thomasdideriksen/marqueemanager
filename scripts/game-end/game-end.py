import os
import sys
sys.path.append('c:\\arcade\\marqueemanager')
import marqueemanager as mm

if mm.start_marquee() >= 0:
    
    if False:
        mm.set_background_color(1, 1, 1)
        mm.horizontal_scroll_images(['c:\\arcade\\marqueemanager\\logos\\other\\arcade_kanji_black.svg'], 300, False, 80, 64)
        sys.exit()

    images = []
    mm.clear()
    mm.set_background_color(1, 1, 1)

    mm.play_video('c:\\arcade\\EmulationStation-DE\\.emulationstation\\scripts\\mvc.mp4', margin=0, alpha=0.4, fit='fill')

    for f in os.listdir('c:\\arcade\\marqueemanager\\logos\\'):
        if f.lower().endswith('.svg'):
            images.append('c:\\arcade\\marqueemanager\\logos\\' + f)
    mm.horizontal_scroll_images(images, 180, True, 80, 110)

    mm.flyout('C:\\arcade\\marqueemanager\\graphics\\buttons_main_flattened.svg', 0.6, 0.45, 8);