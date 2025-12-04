#!/usr/bin/env python3

import sys
import utils


mm = utils.get_marquee_manager()

if mm.start_marquee() >= 0:

    #mm.clear()
    #mm.set_background_color(random.random(), random.random(), random.random())
    print(sys.argv)
