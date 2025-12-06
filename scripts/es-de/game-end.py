#!/usr/bin/env python3

import utils

EVENT_NAME = 'game-end'
print(EVENT_NAME)

# Note: Nothing to do here (for now), since the "game-select" event handles game termination

utils.set_last_event(EVENT_NAME)