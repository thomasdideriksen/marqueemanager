import sys
import os
import random
import glob

MM_ROOT = '/home/thomas/Arcade/marqueemanager'
ES_ROOT = '/home/thomas/ES-DE'
LAST_EVENT_KEY = '_last_event'
DOWNLOADED_MEDIA = 'downloaded_media'

sys.path.append(MM_ROOT)
import marqueemanager as mm


def set_last_event(event):
    mm.set_state(LAST_EVENT_KEY, event)


def get_last_event():
    return mm.get_state(LAST_EVENT_KEY)


def get_marquee_manager():
    return mm


def get_logos_folder():
    return os.path.join(MM_ROOT, 'logos')


def get_graphics_folder():
    return os.path.join(MM_ROOT, 'graphics')


def rom_name_from_rom_path(rom_path):
    return os.path.splitext(os.path.basename(rom_path))[0]


def _clean_path(p):
    return p.replace('\\', '')


def get_video_path_for(rom_system, rom_name):
    video_folder = get_video_folder_for(rom_system)
    result = os.path.join(video_folder, f'{rom_name}.mp4')
    return _clean_path(result)


def get_marquee_image_path_for(rom_system, rom_name):
    result = os.path.join(ES_ROOT, DOWNLOADED_MEDIA, rom_system, 'marquees', f'{rom_name}.png')
    return _clean_path(result)


def get_systems():
    folder = os.path.join(ES_ROOT, DOWNLOADED_MEDIA)
    return os.listdir(folder)


def get_video_folder_for(system):
    return os.path.join(ES_ROOT, DOWNLOADED_MEDIA, system, 'videos')


def get_random_video_path(system=None):
    if system is None:
        systems = get_systems()
        system = random.choice(systems)
    video_folder = get_video_folder_for(system)
    videos = glob.glob('*.mp4', root_dir=video_folder)
    result = os.path.join(video_folder, random.choice(videos))
    return _clean_path(result)


def get_logo_paths():
    images = []
    logos_folder = get_logos_folder()
    for f in os.listdir(logos_folder):
        if f.lower().endswith('.svg'):
            images.append(os.path.join(logos_folder, f))
    return images
