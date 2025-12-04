#!/usr/bin/env python3

import sys
import random
import os

ROOT = '/home/thomas/Arcade/marqueemanager'
sys.path.append(ROOT)
import marqueemanager as mm

if mm.start_marquee() >= 0:

    if len(sys.argv) > 1:

        rom_path = sys.argv[1]
        game_name = sys.argv[2]
        sys_name = sys.argv[3]
        sys_full_name = sys.argv[4]
        rom_name = os.path.splitext(os.path.basename(rom_path))[0]

        marquee_image_path = f'/home/thomas/ES-DE/downloaded_media/{sys_name}/marquees/{rom_name}.png'
        marquee_image_path = marquee_image_path.replace('\\', '')

        mm.clear()
        mm.set_background_color(random.random(), random.random(), random.random())

        mm.horizontal_scroll_images([marquee_image_path], 100.2, False, 0, 0)
