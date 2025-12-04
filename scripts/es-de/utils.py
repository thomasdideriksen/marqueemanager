import sys
import os


MM_ROOT = '/home/thomas/Arcade/marqueemanager'
ES_ROOT = '/home/thomas/ES-DE'

sys.path.append(MM_ROOT)
import marqueemanager as mm


def get_marquee_manager():
    return mm


def get_logos_folder():
    return os.path.join(MM_ROOT, 'logos')


def get_graphics_folder():
    return os.path.join(MM_ROOT, 'graphics')


def rom_name_from_rom_path(rom_path):
    return os.path.splitext(os.path.basename(rom_path))[0]


def get_video_path_for(rom_system, rom_name):
    result = os.path.join(ES_ROOT, 'downloaded_media', rom_system, 'videos', f'{rom_name}.mp4')
    return result.replace('\\', '')


def get_marquee_image_path_for(rom_system, rom_name):
    result = os.path.join(ES_ROOT, 'downloaded_media', rom_system, 'marquees', f'{rom_name}.png')
    return result.replace('\\', '')


def get_logo_paths():
    images = []
    logos_folder = get_logos_folder()
    for f in os.listdir(logos_folder):
        if f.lower().endswith('.svg'):
            images.append(os.path.join(logos_folder, f))
    return images
