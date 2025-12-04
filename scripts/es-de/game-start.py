#!/usr/bin/env python3

import os
import sys
import utils


mm = utils.get_marquee_manager()

if mm.start_marquee() >= 0:

    mm.clear()
    mm.set_background_color(0, 0, 0)

    rom_path = sys.argv[1]
    rom_system = sys.argv[3]
    rom_name = utils.rom_name_from_rom_path(rom_path)

    video_path = utils.get_video_path_for(rom_system, rom_name)
    if os.path.isfile(video_path):
        mm.play_video(video_path, margin=0, alpha=0.35, fit='fill')

    marquee_image_path = utils.get_marquee_image_path_for(rom_system, rom_name)
    if os.path.isfile(marquee_image_path):
        mm.pulse_image(marquee_image_path)

    info_img_path = os.path.join(utils.get_graphics_folder(), 'buttons_flattened.svg')
    mm.flyout(info_img_path, 0.6, 0.45, 8)