#!/usr/bin/env python3

import utils

EVENT_NAME = 'quit'
print(EVENT_NAME)

mm = utils.get_marquee_manager()
mm.close()