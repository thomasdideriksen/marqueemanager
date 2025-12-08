#!/usr/bin/env python3

import sys
import utils
import random
import os

EVENT_NAME = 'system-select'
print(EVENT_NAME)

if len(sys.argv) > 1:

    mm = utils.get_marquee_manager()

    if mm.start_marquee() >= 0:

        last_event = utils.get_last_event()

        # Only update the UI if we transition to system-select from something different
        if last_event != EVENT_NAME:

            mm.clear()
            mm.set_background_color(0.25, 0.25, 0.25),

            VIDEO_COUNT = 32
            video_paths = []
            for _ in range(VIDEO_COUNT):
                video_paths.append(utils.get_random_video_path())

            mm.play_videos(video_paths, 0, 0.45, 'fill'),

            logo_images = utils.get_logo_paths()
            random.shuffle(logo_images)
            mm.horizontal_scroll_images(logo_images, 180, True, 120, 80)

            info_img_path = os.path.join(utils.get_graphics_folder(), 'buttons_main_flattened.svg')
            mm.flyout(info_img_path, 0.6, 0.45, 8, 3)

utils.set_last_event(EVENT_NAME)