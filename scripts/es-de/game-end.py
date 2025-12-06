#!/usr/bin/env python3

import utils

EVENT_NAME = 'game-end'
print(EVENT_NAME)

# mm = utils.get_marquee_manager()
# if mm.start_marquee() >= 0:
#     mm.clear()

utils.set_last_event(EVENT_NAME)