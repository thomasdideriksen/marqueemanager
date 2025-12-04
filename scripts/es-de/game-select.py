#!/usr/bin/env python3

import sys
import utils


mm = utils.get_marquee_manager()

if mm.start_marquee() >= 0:

    if len(sys.argv) > 1:

        rom_path = sys.argv[1]
        game_name = sys.argv[2]
        sys_name = sys.argv[3]
        sys_full_name = sys.argv[4]
        rom_name = utils.rom_name_from_rom_path(rom_path)

        marquee_image_path = utils.get_marquee_image_path_for(sys_name, rom_name)

        mm.clear()
        mm.set_background_color(0, 0, 0)
        mm.show_image(marquee_image_path)
