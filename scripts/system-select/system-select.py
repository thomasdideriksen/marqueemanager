#!/usr/bin/env python3

import sys
import random

ROOT = '/home/thomas/Arcade/marqueemanager'
sys.path.append(ROOT)
import marqueemanager as mm

if False and mm.start_marquee() >= 0:

    mm.clear()
    mm.set_background_color(random.random(), random.random(), random.random())
    print(sys.argv)