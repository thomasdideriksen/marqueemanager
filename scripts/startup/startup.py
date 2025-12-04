#!/usr/bin/env python3

import os
import sys
import time

ROOT = '/home/thomas/Arcade/marqueemanager'
sys.path.append(ROOT)
import marqueemanager as mm

if mm.start_marquee() >= 0:

    mm.clear()
    mm.set_background_color(1, 1, 1)
    mm.play_video("/home/thomas/Arcade/video.mp4", margin=0, alpha=0.4, fit='fill')

    images = []
    for f in os.listdir(f'{ROOT}/logos/'):
        if f.lower().endswith('.svg'):
            images.append(f'{ROOT}/logos/' + f)
    mm.horizontal_scroll_images(images, 180, True, 80, 110)

    mm.flyout(f'{ROOT}/graphics/buttons_main_flattened.svg', 0.6, 0.45, 8)
