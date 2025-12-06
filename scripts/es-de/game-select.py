#!/usr/bin/env python3

import sys
import utils
import os

EVENT_NAME = 'game-select'
print(EVENT_NAME)

if len(sys.argv) > 1:

    mm = utils.get_marquee_manager()

    if mm.start_marquee() >= 0:

        rom_path = sys.argv[1]
        game_name = sys.argv[2]
        sys_name = sys.argv[3]
        sys_full_name = sys.argv[4]
        rom_name = utils.rom_name_from_rom_path(rom_path)

        marquee_image_path = utils.get_marquee_image_path_for(sys_name, rom_name)
        video_path = utils.get_video_path_for(sys_name, rom_name)

        mm.clear_queue()
        mm.clear()
        mm.set_background_color(0, 0, 0)

        mm.play_video(video_path, 0, 0.35, 'fill')
        mm.show_image(marquee_image_path, 48)

        info_img_path = os.path.join(utils.get_graphics_folder(), 'buttons_main_flattened.svg')
        mm.flyout(info_img_path, 0.6, 0.45, 8, 1.5)

utils.set_last_event(EVENT_NAME)
