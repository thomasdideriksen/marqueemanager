#!/usr/bin/env python3

import os
import utils


mm = utils.get_marquee_manager()

if mm.start_marquee() >= 0:

    mm.clear()
    mm.set_background_color(1, 1, 1)
    mm.play_video("/home/thomas/Arcade/video.mp4", margin=0, alpha=0.4, fit='fill')

    images = utils.get_logo_paths()
    mm.horizontal_scroll_images(images, 180, True, 80, 110)

    info_img_path = os.path.join(utils.get_graphics_folder(), 'buttons_main_flattened.svg')
    mm.flyout(info_img_path, 0.6, 0.45, 8)

    utils.set_last_event('startup')