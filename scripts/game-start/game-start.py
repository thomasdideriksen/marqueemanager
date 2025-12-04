#!/usr/bin/env python3

import os
import sys

ROOT = '/home/thomas/Arcade/marqueemanager'
sys.path.append(ROOT)
import marqueemanager as mm

if mm.start_marquee() >= 0:

    mm.clear()
    mm.set_background_color(0, 0, 0)

    rom_path = sys.argv[1]
    rom_system = sys.argv[3]
    rom_name = os.path.splitext(os.path.basename(rom_path))[0]

    video_path = f'/home/thomas/ES-DE/downloaded_media/{rom_system}/videos/{rom_name}.mp4'
    video_path = video_path.replace('\\', '')

    if os.path.isfile(video_path):
        mm.play_video(video_path, margin=0, alpha=0.35, fit='fill')

    marquee_image_path = f'/home/thomas/ES-DE/downloaded_media/{rom_system}/marquees/{rom_name}.png'
    marquee_image_path = marquee_image_path.replace('\\', '')

    if os.path.isfile(marquee_image_path):
        mm.pulse_image(marquee_image_path)

    mm.flyout(f'{ROOT}/graphics/buttons_flattened.svg', 0.6, 0.45, 8)