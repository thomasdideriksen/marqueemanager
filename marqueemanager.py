from abc import ABC, abstractmethod

URL = 'localhost'
PORT = 6000
READY_MSG = 'marquee ready'

OPCODE_CLEAR = 'clear'
OPCODE_IMAGE = 'image'
OPCODE_CLOSE = 'close'


def start_marquee():
    """
    Start the marquee process
    """
    import subprocess

    process = subprocess.Popen(
        ['pythonw', __file__],
        creationflags=subprocess.DETACHED_PROCESS,
        stdout=subprocess.PIPE)

    while True:
        line = process.stdout.readline().decode('utf8').strip()
        if line == READY_MSG:
            break


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


class ValueAnimation(object):
    """
    Animates a single numerical value
    """
    def __init__(self, begin, end, duration, ease=False):
        self.begin = begin
        self.end = end
        self.duration = duration
        self.ease = ease
        self.t0 = time.time()

    def evaluate(self):
        dt = time.time() - self.t0
        if dt < self.duration:
            r = dt / self.duration
            if self.ease:
                r = r - 1.0
                r = -(r * r * r * r - 1.0)
            return self.begin + (self.end - self.begin) * r, False
        else:
            return self.end, True


class VisualEffect(ABC):
    """
    Visual effect base class
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


class DisplayImageVisualEffect(VisualEffect):
    """
    Visual effect for displaying an image
    """

    def __init__(self, renderer, image_path):
        self.surface = sdl2.ext.image.load_img(image_path)
        self.texture = sdl2.SDL_CreateTextureFromSurface(renderer, self.surface)
        self.fade_anim = ValueAnimation(0.0, 1.0, 1.5, ease=True)
        self.texture_src_rect = sdl2.SDL_Rect(x=0, y=0, w=self.surface.w, h=self.surface.h)
        self.stopping = False
        self.stopped = False
        self.translate_anim = ValueAnimation(0.0, 200.0, 3.0)

    def stop(self):
        if not self.stopping:
            self.stopping = True
            current_value, _ = self.fade_anim.evaluate()
            self.fade_anim = ValueAnimation(current_value, 0.0, 1.0, ease=True)

    def is_stopped(self):
        return self.stopped

    def render(self, renderer):
        rw, rh = get_renderer_dimensions(renderer)

        sw = float(self.surface.w)
        sh = float(self.surface.h)

        sx = rw / sw
        sy = rh / sh
        s = min(sx, sy)
        s = min(1.0, s)

        translate_x, translate_anim_done = self.translate_anim.evaluate()
        if translate_anim_done:
            self.translate_anim = ValueAnimation(translate_x, translate_x - 200, 3, ease=True)
        translate_x = 0


        dw = sw * s
        dh = sh * s
        dx = (rw - dw) * 0.5 + translate_x
        dy = (rh - dh) * 0.5
        dst_rect = sdl2.SDL_FRect(x=dx, y=dy, w=dw, h=dh)

        value, fade_animation_done = self.fade_anim.evaluate()

        sdl2.SDL_SetTextureAlphaMod(self.texture, int(value * 255.0))
        sdl2.SDL_RenderCopyF(renderer, self.texture, self.texture_src_rect, dst_rect)

        if self.stopping and fade_animation_done:
            self.stopped = True

    def cleanup(self):
        sdl2.SDL_DestroyTexture(self.texture)
        sdl2.SDL_FreeSurface(self.surface)


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
    print(f'Command: {command}')

    opcode = command[0]

    if opcode == OPCODE_CLEAR:
        render_manager.stop_all_visual_effects()

    elif opcode == OPCODE_CLOSE:
        return False

    elif opcode == OPCODE_IMAGE:
        effect = DisplayImageVisualEffect(render_manager.renderer, command[1])
        render_manager.add_visual_effect(effect)

    else:
        print(f'Invalid command opcode: {opcode}')

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
                    if command[0] == OPCODE_CLOSE:
                        break
            except TimeoutError:
                continue


class RenderManager(object):

    def __init__(self, renderer):
        self.visual_effects = []
        self.renderer = renderer

    def add_visual_effect(self, effect):
        self.visual_effects.append(effect)

    def stop_all_visual_effects(self):
        for effect in self.visual_effects:
            effect.stop()

    def cleanup(self):
        for effect in self.visual_effects:
            effect.cleanup()

    def render(self):

        sdl2.SDL_RenderClear(self.renderer)

        effects_to_remove = []
        for effect in self.visual_effects:
            effect.render(self.renderer)
            if effect.is_stopped():
                effect.cleanup()
                effects_to_remove.append(effect)

        for effect in effects_to_remove:
            self.visual_effects.remove(effect)

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
        name='ipc listener thread',
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
            send_marquee_command(OPCODE_CLOSE)

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
    import time
    from ctypes import c_int, byref
    from threading import Thread
    from queue import Queue
    from multiprocessing.connection import Listener
    main()
