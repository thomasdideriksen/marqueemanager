#!/usr/bin/env python3

import utils

EVENT_NAME = 'startup'
print(EVENT_NAME)

mm = utils.get_marquee_manager()

if mm.start_marquee() >= 0:
    mm.clear()
    mm.set_background_color(0, 0, 0)

utils.set_last_event(EVENT_NAME)