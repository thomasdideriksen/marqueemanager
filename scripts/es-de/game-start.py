#!/usr/bin/env python3

import os
import sys
import utils

EVENT_NAME = 'game-start'
print(EVENT_NAME)

mm = utils.get_marquee_manager()

if mm.start_marquee() >= 0:

    mm.clear()
    mm.set_background_color(0.25, 0.25, 0.25),

    rom_path = sys.argv[1]
    rom_system = sys.argv[3]
    rom_name = utils.rom_name_from_rom_path(rom_path)

    video_path = utils.get_video_path_for(rom_system, rom_name)
    mm.play_videos([video_path], 0, 0.45, 'fill', 0)

    marquee_image_path = utils.get_marquee_image_path_for(rom_system, rom_name)

    mm.grow_image(marquee_image_path, 32, -128, 2, 'fadeout')
    mm.grow_image(marquee_image_path, 0, 16, 2.5, 'fadein')

    #mm.show_image(marquee_image_path, 32),
    #mm.pulse_image(marquee_image_path)

    info_img_path = os.path.join(utils.get_graphics_folder(), 'buttons_flattened.svg')
    mm.flyout(info_img_path, 0.6, 0.45, 8, 0)

utils.set_last_event(EVENT_NAME)
