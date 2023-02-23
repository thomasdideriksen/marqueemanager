from abc import ABC, abstractmethod
import time

URL = 'localhost'
PORT = 6000
READY_MSG = 'marquee ready'

COMMAND_CLEAR = 'clear'
COMMAND_SHOW_IMAGE = 'image'
COMMAND_HORZ_SCROLL_IMAGES = 'horzscrollimages'
COMMAND_VERT_SCROLL_IMAGES = 'vertscrollimages'
COMMAND_BACKGROUND = 'background'
COMMAND_CLOSE = 'close'
COMMAND_NOOP = 'noop'


def start_marquee():
    """
    Start the marquee process
    """
    import subprocess

    if send_marquee_command(COMMAND_NOOP):
        # This checks if a marquee process is already running. We only
        # allow one marquee process to run at the time. This only works
        # because we're synchronizing using the 'READY_MSG' (see below)
        # which ensures that 'start_marquee' will not return before the
        # command listener is ready
        return False

    process = subprocess.Popen(
        ['python', __file__],
        creationflags=subprocess.DETACHED_PROCESS,
        stdout=subprocess.PIPE)

    while True:
        line = process.stdout.readline().decode('utf8').strip()
        if line == READY_MSG:
            break

    return True


def send_marquee_command(*command):
    """
    Send command to marquee process. Used by clients (including other
    processes) who wants to interact with the marquee screen
    """
    from multiprocessing.connection import Client
    try:
        address = (URL, PORT)
        with Client(address) as connection:
            connection.send(command)
        return True
    except ConnectionRefusedError:
        return False


class Animation(ABC):

    @abstractmethod
    def restart(self, start_time=None):
        pass

    @abstractmethod
    def evaluate(self, eval_time=None):
        pass


class ValueAnimation(Animation):
    """
    Animates a single numerical value
    """
    def __init__(self, begin, end, duration, start_time=None, ease=False, repeat=False):
        assert duration >= 0.0
        self.begin = begin
        self.end = end
        self.duration = duration
        self.ease = ease
        self.repeat = repeat
        self.restart(start_time)

    def restart(self, start_time=None):
        self.start_time = time.time() if start_time is None else start_time

    def evaluate(self, eval_time=None):
        eval_time = time.time() if eval_time is None else eval_time
        dt = eval_time - self.start_time
        if dt < 0:
            return self.begin, False
        if self.repeat and dt > self.duration:
            dt %= self.duration
        if dt < self.duration:
            r = dt / self.duration
            if self.ease:
                r = r - 1.0
                r = -(r * r * r * r - 1.0)
            return self.begin + (self.end - self.begin) * r, False
        else:
            return self.end, True


class ColorAnimation(Animation):

    def __init__(self, begin, end, duration, start_time=None, ease=False, repeat=False):
        assert isinstance(begin, tuple) and len(begin) == 3
        assert isinstance(end, tuple) and len(end) == 3
        self.r = ValueAnimation(begin[0], end[0], duration, start_time, ease, repeat)
        self.g = ValueAnimation(begin[1], end[1], duration, start_time, ease, repeat)
        self.b = ValueAnimation(begin[2], end[2], duration, start_time, ease, repeat)

    def restart(self, start_time=None):
        self.r.restart(start_time)
        self.g.restart(start_time)
        self.b.restart(start_time)

    def evaluate(self, eval_time=None):
        eval_time = time.time() if eval_time is None else eval_time
        r_val, r_done = self.r.evaluate(eval_time)
        g_val, g_done = self.g.evaluate(eval_time)
        b_val, b_done = self.b.evaluate(eval_time)
        return (r_val, g_val, b_val), all([r_done, g_done, b_done])


class Image(object):
    """
    Small wrapper class for images
    """
    def __init__(self, renderer, path):
        self.surface = sdl2.ext.image.load_img(path, as_argb=True)
        self.tex = sdl2.SDL_CreateTextureFromSurface(renderer, self.surface)
        sdl2.SDL_SetTextureBlendMode(self.tex, sdl2.SDL_BLENDMODE_BLEND)

    def cleanup(self):
        sdl2.SDL_DestroyTexture(self.tex)
        sdl2.SDL_FreeSurface(self.surface)

    @property
    def texture(self):
        return self.tex

    @property
    def rect(self):
        return sdl2.SDL_Rect(x=0, y=0, w=self.surface.w, h=self.surface.h)

    @property
    def width(self):
        return self.surface.w

    @property
    def height(self):
        return self.surface.h


class Effect(ABC):
    """
    Effect base class
    """
    @abstractmethod
    def render(self, renderer):
        pass

    @abstractmethod
    def stop(self):
        pass

    @abstractmethod
    def is_stopped(self):
        return False

    @abstractmethod
    def cleanup(self):
        pass


class DisplayImageEffect(Effect):
    """
    Effect for displaying an image
    """
    def __init__(self, renderer, image_path):
        self.image = Image(renderer, image_path)
        self.fade_anim = ValueAnimation(0.0, 1.0, 1.5, ease=True)
        self.stopping = False
        self.stopped = False

    def stop(self):
        if not self.stopping:
            self.stopping = True
            current_value, _ = self.fade_anim.evaluate()
            self.fade_anim = ValueAnimation(current_value, 0.0, 1.0, ease=True)

    def is_stopped(self):
        return self.stopped

    def render(self, renderer):
        rw, rh = get_renderer_dimensions(renderer)

        sw = float(self.image.width)
        sh = float(self.image.height)

        sx = rw / sw
        sy = rh / sh
        s = min(sx, sy, 1.0)

        dw = sw * s
        dh = sh * s
        dx = (rw - dw) * 0.5
        dy = (rh - dh) * 0.5

        dst_rect = sdl2.SDL_FRect(x=dx, y=dy, w=dw, h=dh)

        value, fade_animation_done = self.fade_anim.evaluate()

        sdl2.SDL_SetTextureAlphaMod(self.image.texture, int(value * 255.0))
        sdl2.SDL_RenderCopyF(renderer, self.image.texture, self.image.rect, dst_rect)

        if self.stopping and fade_animation_done:
            self.stopped = True

    def cleanup(self):
        self.image.cleanup()


class HorizontalScrollImagesEffect(Effect):
    """
    Horizontal image scrolling effect
    """
    def __init__(self, renderer, image_paths, pixels_per_second=400):

        self.TOP_BOTTOM_MARGIN = 8
        self.IMAGE_IMAGE_MARGIN = 32

        rw, rh = get_renderer_dimensions(renderer)
        self.images = [Image(renderer, path) for path in image_paths]
        self.animations = []
        self.rects = []
        self.full_width = 0.0

        for image in self.images:

            sx = rw / float(image.width)
            sy = (rh - (self.TOP_BOTTOM_MARGIN * 2)) / float(image.height)
            s = min(sx, sy)

            w = float(image.width) * s
            h = float(image.height) * s
            y = (rh - h) * 0.5

            rect = sdl2.SDL_FRect(x=0, y=y, w=w, h=h)
            self.rects.append(rect)

            self.full_width += rect.w + self.IMAGE_IMAGE_MARGIN

        pos0 = -self.full_width
        pos1 = (math.ceil(rw / self.full_width) + 1) * self.full_width
        self.scroll_anim = ValueAnimation(pos0, pos1, abs(pos1 - pos0) / pixels_per_second, repeat=True)

        self.alpha_anim = ValueAnimation(0.0, 1.0, 1.0, ease=True)
        self.stopping = False
        self.stopped = False

    def stop(self):
        if not self.stopping:
            self.stopping = True
            current_value, _ = self.alpha_anim.evaluate()
            self.alpha_anim = ValueAnimation(current_value, 0.0, 1.0, ease=True)

    def is_stopped(self):
        return self.stopped

    def draw_image(self, renderer, idx, alpha, scroll):
        image = self.images[idx]
        rect = self.rects[idx]
        rect.x = scroll
        sdl2.SDL_SetTextureAlphaMod(image.texture, int(alpha * 255.0))
        sdl2.SDL_RenderCopyF(renderer, image.texture, image.rect, rect)

    def render(self, renderer):

        rw, rh = get_renderer_dimensions(renderer)

        scroll_val, _ = self.scroll_anim.evaluate()
        alpha_val, alpha_anim_done = self.alpha_anim.evaluate()

        repeat_behind = math.ceil(scroll_val / self.full_width)
        pos = scroll_val - (repeat_behind * self.full_width)

        done = False
        while not done:
            for idx, _ in enumerate(self.images):
                self.draw_image(renderer, idx, alpha_val, pos)
                rect = self.rects[idx]
                pos += rect.w + self.IMAGE_IMAGE_MARGIN
                done = pos > rw
                if done:
                    break

        if self.stopping and alpha_anim_done:
            self.stopped = True

    def cleanup(self):
        for image in self.images:
            image.cleanup()


class VerticalScrollImagesEffect(Effect):
    """
    Vertical image scrolling effect
    """
    def __init__(self, renderer, image_paths, pixels_per_second=400):

        self.TOP_BOTTOM_MARGIN = 8
        self.PIXELS_PER_SECOND = 100

        rw, rh = get_renderer_dimensions(renderer)
        self.images = [Image(renderer, path) for path in image_paths]
        self.animations = []
        self.rects = []
        self.current_image_idx = 0

        for image in self.images:

            sx = rw / float(image.width)
            sy = (rh - (self.TOP_BOTTOM_MARGIN * 2)) / float(image.height)
            s = min(sx, sy)

            w = float(image.width) * s
            h = float(image.height) * s
            x = (rw - w) * 0.5

            rect = sdl2.SDL_FRect(x=x, y=0, w=w, h=h)
            self.rects.append(rect)

        pos0 = rh
        pos1 = self.TOP_BOTTOM_MARGIN
        self.scroll_anim = ValueAnimation(pos0, pos1, abs(pos1 - pos0) / self.PIXELS_PER_SECOND, ease=True)

        self.alpha_anim = ValueAnimation(0.0, 1.0, 1.0, ease=True)
        self.stopping = False
        self.stopped = False

    def stop(self):
        if not self.stopping:
            self.stopping = True
            current_value, _ = self.alpha_anim.evaluate()
            self.alpha_anim = ValueAnimation(current_value, 0.0, 1.0, ease=True)

    def is_stopped(self):
        return self.stopped

    def draw_image(self, renderer, idx, alpha, scroll):
        image = self.images[idx]
        rect = self.rects[idx]
        rect.y = scroll
        sdl2.SDL_SetTextureAlphaMod(image.texture, int(alpha * 255.0))
        sdl2.SDL_RenderCopyF(renderer, image.texture, image.rect, rect)

    def render(self, renderer):

        rw, rh = get_renderer_dimensions(renderer)

        scroll_val, scroll_anim_done = self.scroll_anim.evaluate()
        alpha_val, alpha_anim_done = self.alpha_anim.evaluate()

        image = self.images[self.current_image_idx]
        rect = self.rects[self.current_image_idx]

        self.draw_image(renderer, self.current_image_idx, alpha_val, scroll_val)

        if scroll_anim_done:
            self.current_image_idx += 1
            self.current_image_idx %= len(self.images)
            self.scroll_anim.restart()


        if self.stopping and alpha_anim_done:
            self.stopped = True

    def cleanup(self):
        for image in self.images:
            image.cleanup()


def get_marquee_display_bounds():
    """
    Get the bounds of the marquee display
    """
    display_count = sdl2.SDL_GetNumVideoDisplays()

    # TODO: Bail out if we only have one display...

    marquee_bounds = None
    for display_idx in range(display_count):

        bounds = sdl2.SDL_Rect()
        sdl2.SDL_GetDisplayBounds(display_idx, bounds)

        if marquee_bounds is None:
            marquee_bounds = (bounds.x, bounds.y, bounds.w, int(bounds.h / 8)) # TODO: Remove this hack
        elif bounds.h < marquee_bounds[3]:
            marquee_bounds = (bounds.x, bounds.y, bounds.w, bounds.h)

    return marquee_bounds


def open_marquee_window():
    """
    Open marquee window (used on startup)
    """
    sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO)

    x, y, width, height = get_marquee_display_bounds()

    window = sdl2.video.SDL_CreateWindow(
        b'Marquee',
        x, y,
        width, height,
        sdl2.SDL_WINDOW_BORDERLESS | sdl2.SDL_WINDOW_VULKAN)

    sdl2.SDL_SetWindowAlwaysOnTop(window, True)
    sdl2.SDL_ShowCursor(sdl2.SDL_DISABLE)

    renderer = sdl2.SDL_CreateRenderer(
        window, -1,
        sdl2.render.SDL_RENDERER_ACCELERATED | sdl2.SDL_RENDERER_PRESENTVSYNC)

    sdl2.SDL_SetHint(sdl2.SDL_HINT_RENDER_SCALE_QUALITY, b'best')
    sdl2.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255)
    sdl2.SDL_RenderClear(renderer)
    sdl2.SDL_RenderPresent(renderer)

    return window, renderer


def close_marquee_window(window, renderer):
    """
    Close marquee window (used on shutdown)
    """
    sdl2.SDL_DestroyWindow(window)
    sdl2.SDL_DestroyRenderer(renderer)
    sdl2.SDL_Quit()


def get_renderer_dimensions(renderer):
    """
    Get renderer dimensions
    """
    w = c_int(0)
    h = c_int(0)
    sdl2.SDL_GetRendererOutputSize(renderer, byref(w), byref(h))
    return w.value, h.value


def process_marquee_command(command, render_manager):
    """
    Process marquee command
    """

    if command[0] == COMMAND_CLOSE:
        return False

    elif command[0] == COMMAND_NOOP:
        pass

    elif command[0] == COMMAND_CLEAR:
        render_manager.stop_all_effects()

    elif command[0] == COMMAND_SHOW_IMAGE:
        image_path = Path(command[1])
        if image_path.is_file():
            effect = DisplayImageEffect(render_manager.renderer, command[1])
            render_manager.add_effect(effect)

    elif command[0] == COMMAND_HORZ_SCROLL_IMAGES:
        image_paths = command[2:]
        if all([Path(image_path).is_file() for image_path in image_paths]):
            effect = HorizontalScrollImagesEffect(render_manager.renderer, image_paths, pixels_per_second=command[1])
            render_manager.add_effect(effect)

    elif command[0] == COMMAND_VERT_SCROLL_IMAGES:
        image_paths = command[1:]
        if all([Path(image_path).is_file() for image_path in image_paths]):
            effect = VerticalScrollImagesEffect(render_manager.renderer, image_paths)
            render_manager.add_effect(effect)

    elif command[0] == COMMAND_BACKGROUND:
        if len(command) == 2:
            r = g = b = command[1]
        else:
            r = command[1]
            g = command[2]
            b = command[3]
        render_manager.set_background_color(r, g, b)

    return True


def process_events(events):
    """
    Return true if termination was requested
    """
    for e in events:
        if e.type == sdl2.SDL_QUIT:
            return False
        if e.type == sdl2.SDL_KEYDOWN:
            if e.key.keysym.sym == sdl2.SDLK_q:
                return False
    return True


def run_command_listener(command_queue):
    """
    Run the command listener
    """
    address = (URL, PORT)
    with Listener(address) as listener:
        listener._listener._socket.settimeout(0.5)  # Hacky
        while True:
            try:
                with listener.accept() as connection:
                    command = connection.recv()
                    command_queue.put(command)
                    if command[0] == COMMAND_CLOSE:
                        break
            except TimeoutError:
                continue


class RenderManager(object):

    def __init__(self, renderer):
        self.effects = []
        self.renderer = renderer
        self.color_anim = ColorAnimation((0, 0, 0), (0, 0, 0), 0)

    def add_effect(self, effect):
        self.effects.append(effect)

    def stop_all_effects(self):
        for effect in self.effects:
            effect.stop()

    def cleanup(self):
        for effect in self.effects:
            effect.cleanup()

    def set_background_color(self, r, g, b):
        def clamp(v):
            return max(0.0, min(1.0, v))
        color0, _ = self.color_anim.evaluate()
        color1 = (clamp(r), clamp(g), clamp(b))
        self.color_anim = ColorAnimation(color0, color1, 1.0, ease=True)

    def render(self):
        color, _ = self.color_anim.evaluate()
        sdl2.SDL_SetRenderDrawColor(
            self.renderer,
            int(color[0] * 255),
            int(color[1] * 255),
            int(color[2] * 255),
            255)
        sdl2.SDL_RenderClear(self.renderer)

        effects_to_remove = []
        for effect in self.effects:
            effect.render(self.renderer)
            if effect.is_stopped():
                effect.cleanup()
                effects_to_remove.append(effect)

        for effect in effects_to_remove:
            self.effects.remove(effect)

        sdl2.SDL_RenderPresent(self.renderer)


def main():
    """
    Main entry point
    """
    # Create marquee window
    window, renderer = open_marquee_window()

    # Create a command queue that we share between threads
    command_queue = Queue()

    # Start the command listener thread
    command_listener_thread = Thread(
        target=run_command_listener,
        name='Marquee command listener thread',
        args=(command_queue,),
        daemon=True)
    command_listener_thread.start()

    # Create render manager
    render_manager = RenderManager(renderer)

    # A parent process may listen for this (i.e. via a pipe) to
    # know when the marquee window has been created
    sys.stdout.write(f'{READY_MSG}\r\n')
    sys.stdout.flush()

    # Enter main loop
    while True:

        # Process events
        events = sdl2.ext.get_events()
        if not process_events(events):
            send_marquee_command(COMMAND_CLOSE)

        # Process commands
        if not command_queue.empty():
            command = command_queue.get(block=False)
            if not process_marquee_command(command, render_manager):
                break

        # Render
        render_manager.render()

    # Cleanup render resources
    render_manager.cleanup()

    # Wait for command listener thread to finish
    command_listener_thread.join()

    # Close marquee window and cleanup
    close_marquee_window(window, renderer)


if __name__ == "__main__":
    import sys
    import sdl2
    import sdl2.ext
    from ctypes import c_int, byref
    from threading import Thread
    from queue import Queue
    from multiprocessing.connection import Listener
    from pathlib import Path
    import math
    main()
