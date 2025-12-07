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
        info_img_path = os.path.join(utils.get_graphics_folder(), 'buttons_main_flattened.svg')

        mm.command_list([
            mm.clear_command(),
            mm.set_background_color_command(0.25, 0.25, 0.25),
            mm.play_video_command(video_path, 0, 0.45, 'fill'),
            mm.show_image_command(marquee_image_path, 32),
            mm.flyout_command(info_img_path, 0.6, 0.45, 8, 1.5),
        ])

utils.set_last_event(EVENT_NAME)
