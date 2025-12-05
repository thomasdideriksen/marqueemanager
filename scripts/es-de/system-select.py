#!/usr/bin/env python3

import sys
import utils

SYSTEM_SELECT_EVENT = 'system-select'

if len(sys.argv) > 1:

    mm = utils.get_marquee_manager()

    if mm.start_marquee() >= 0:

        last_event = utils.get_last_event()

        if last_event != SYSTEM_SELECT_EVENT:

            print('Do something!')
            # TODO

utils.set_last_event(SYSTEM_SELECT_EVENT)