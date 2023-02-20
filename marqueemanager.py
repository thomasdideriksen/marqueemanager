
# Notes:
# 1. SDL_UpdateWindowSurface is the SW equvalient to SDL_RenderPresent for HW rendering
# 2. Consider: https://stackoverflow.com/questions/1597289/hide-console-in-c-system-function-win

URL = 'localhost'
PORT = 6000

OPCODE_CLEAR = 'clear'
OPCODE_IMAGE = 'image'
OPCODE_CLOSE = 'close'


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


class Animation(object):
    """
    Simple animation object
    """
    def __init__(self, begin, end, duration):
        self.begin = begin
        self.end = end
        self.duration = duration
        self.t0 = time.time()

    def evaluate(self):
        dt = time.time() - self.t0
        if dt < self.duration:
            ratio = dt / self.duration
            return self.begin + (self.end - self.begin) * ratio, False
        else:
            return self.end, True


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

    sdl2.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255)

    clear_renderer(renderer)

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


def clear_renderer(renderer):
    """
    Clear renderer
    """
    sdl2.SDL_RenderClear(renderer)
    sdl2.SDL_RenderPresent(renderer)


def show_image(renderer, image_path, fade_duration):
    """
    Fade in image
    """
    surface = sdl2.ext.image.load_img(image_path)

    sdl2.ext.renderer.set_texture_scale_quality('best')
    tex = sdl2.SDL_CreateTextureFromSurface(renderer, surface)

    rw, rh = get_renderer_dimensions(renderer)

    sw = float(surface.w)
    sh = float(surface.h)

    sx = rw / sw
    sy = rh / sh
    s = min(sx, sy)
    s = min(1.0, s)

    src_rect = sdl2.SDL_Rect(x=0, y=0, w=surface.w, h=surface.h)

    dw = int(surface.w * s)
    dh = int(surface.h * s)
    dx = int((rw - dw) * 0.5)
    dy = int((rh - dh) * 0.5)
    dst_rect = sdl2.SDL_Rect(x=dx, y=dy, w=dw, h=dh)

    fade_anim = Animation(0.0, 1.0, fade_duration)

    while True:

        value, complete = fade_anim.evaluate()

        sdl2.SDL_RenderClear(renderer)
        sdl2.SDL_SetTextureAlphaMod(tex, int(value * 255.0))
        sdl2.SDL_RenderCopy(renderer, tex, src_rect, dst_rect)
        sdl2.SDL_RenderPresent(renderer)

        if complete:
            break

    sdl2.SDL_DestroyTexture(tex)
    sdl2.SDL_FreeSurface(surface)


def process_marquee_command(command, renderer):
    """
    Process marquee command
    """
    print(f'Command: {command}')

    opcode = command[0]

    if opcode == OPCODE_CLEAR:
        clear_renderer(renderer)

    elif opcode == OPCODE_CLOSE:
        return False

    elif opcode == OPCODE_IMAGE:
        show_image(renderer, command[1], 0.5)

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

    # Enter main loop
    while True:

        # Process events
        events = sdl2.ext.get_events()
        if not process_events(events):
            send_marquee_command(OPCODE_CLOSE)

        # Process commands
        if not command_queue.empty():
            command = command_queue.get(block=False)
            if not process_marquee_command(command, renderer):
                break

    # Wait for command listener thread to finish
    command_listener_thread.join()

    # Close marquee window and cleanup
    close_marquee_window(window, renderer)


if __name__ == "__main__":
    import sdl2
    import sdl2.ext
    import time
    from ctypes import c_int, byref
    from threading import Thread
    from queue import Queue
    from multiprocessing.connection import Listener
    main()
