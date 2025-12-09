from abc import ABC, abstractmethod
import socket
import struct
import time
import pickle
import os

HOST = 'localhost'
PORT = 6000

COMMAND_CLEAR = 'clear'
COMMAND_SHOW_IMAGE = 'showimage'
COMMAND_GROW_IMAGE = 'growimage'
COMMAND_FLYOUT = 'flyout'
COMMAND_PULSE_IMAGE = 'pulseimage'
COMMAND_PLAY_VIDEOS = 'playvideos'
COMMAND_HORZ_SCROLL_IMAGES = 'horzscrollimages'
COMMAND_VERT_SCROLL_IMAGES = 'vertscrollimages'
COMMAND_BACKGROUND = 'background'
COMMAND_SET_STATE = 'setstate'
COMMAND_GET_STATE = 'getstate'
COMMAND_COMMAND_LIST = 'commandlist'
COMMAND_CLOSE = 'close'
COMMAND_NOOP = 'noop'

DISPLAY_ONLY_MARQUEE = -1
DISPLAY_DEBUG = -2

FIT_FILL = 'fill'
FIT_FIT = 'fit'
FIT_STRETCH = 'stretch'
FIT_CENTER = 'center'

def start_marquee(display_idx=DISPLAY_ONLY_MARQUEE):
    """
    Start the marquee process
    """

    # This checks if a marquee process is already running. This is
    # not really concurrency safe, i.e. if two processes call start_marquee
    # in rapid succession, this would not catch it-- TODO: Come up with a better approach
    if noop():
        return 0

    import subprocess
    import sys

    # Start the marquee process
    flags = subprocess.DETACHED_PROCESS if os.name == 'nt' else 0
    process = subprocess.Popen(
        [sys.executable, __file__, str(display_idx)],
        creationflags=flags,
        stdout=subprocess.PIPE)

    # Wait for the marquee process/window to be ready
    t0 = time.time()
    while True:
        if process.poll() != None:
            # If the marquee process crashed we return false
            return -1

        # Give up after a while if the marquee process isn't responding
        MAX_WAIT_TIME_SECONDS = 6
        elapsed = time.time() - t0
        if elapsed > MAX_WAIT_TIME_SECONDS:
            return -1

        # Check if the marquee process is ready to receive commands
        if noop():
            return 1
        else:
            time.sleep(0.1)


def horizontal_scroll_images_command(image_paths: list[str], speed: float, reverse: bool, margin: float, spacing: float, svg_aa_factor: float):
    return _make_command(COMMAND_HORZ_SCROLL_IMAGES, {
        'images': image_paths,
        'speed': speed,
        'reverse': reverse,
        'margin': margin,
        'spacing': spacing,
        'svgaafactor': svg_aa_factor})

def horizontal_scroll_images(image_paths: list[str], speed: float, reverse: bool, margin: float, spacing: float, svg_aa_factor: float):
    return _send_marquee_command(horizontal_scroll_images_command(image_paths, speed, reverse, margin, spacing, svg_aa_factor))


def vertical_scroll_images_command(image_paths: list[str]):
    return _make_command(COMMAND_VERT_SCROLL_IMAGES, {
        'images': image_paths})


def vertical_scroll_images(image_paths: list[str]):
    return _send_marquee_command(vertical_scroll_images_command(image_paths))


def grow_image_command(image_path: str, start_margin: float, end_margin: float, duration: float, fade: str):
    return _make_command(COMMAND_GROW_IMAGE, {
        'image': image_path,
        'startmargin': start_margin,
        'endmargin': end_margin,
        'duration': duration,
        'fade': fade})


def grow_image(image_path: str, margin_start: float, margin_end: float, duration: float, fade: str):
    return _send_marquee_command(grow_image_command(image_path, margin_start, margin_end, duration, fade))


def show_image_command(image_path: str, margin: float):
    return _make_command(COMMAND_SHOW_IMAGE, {
        'image': image_path,
        'margin': margin})


def show_image(image_path: str, margin: float):
    return _send_marquee_command(show_image_command(image_path, margin))


def flyout_command(image_path: str, alpha: float, height: float, margin: float, delay: float):
    return _make_command(COMMAND_FLYOUT, {
        'image': image_path,
        'alpha': alpha,
        'height': height,
        'margin': margin,
        'delay': delay})


def flyout(image_path: str, alpha: float, height: float, margin: float, delay: float):
    return _send_marquee_command(flyout_command(image_path, alpha, height, margin, delay))


def pulse_image_command(image_path: str):
    return _make_command(COMMAND_PULSE_IMAGE, {
        'image': image_path})


def pulse_image(image_path: str):
    return _send_marquee_command(pulse_image_command(image_path))


def play_videos_command(video_paths: str, margin: float, alpha: float, fit: str):
    return _make_command(COMMAND_PLAY_VIDEOS, {
        'videos': video_paths,
        'margin': margin,
        'alpha': alpha,
        'fit': fit})


def play_videos(video_paths: str, margin: float, alpha: float, fit: str):
    return _send_marquee_command(play_videos_command(video_paths, margin, alpha, fit))


def set_background_color_command(r, g, b):
    return _make_command(COMMAND_BACKGROUND, {
        'color': (r, g, b)})


def set_background_color(r, g, b):
    return _send_marquee_command(set_background_color_command(r, g, b))


def command_list(commands: list[str]):
    return _send_marquee_command(_make_command(COMMAND_COMMAND_LIST, {
        'commands': commands }))


def noop():
    return _send_marquee_command(_make_command(COMMAND_NOOP))


def clear_command():
    return _make_command(COMMAND_CLEAR)


def clear():
    return _send_marquee_command(clear_command())


def close():
    return _send_marquee_command(_make_command(COMMAND_CLOSE))


def set_state_command(key, value):
    return _make_command(COMMAND_SET_STATE, {
        'key': key,
        'value': value})


def set_state(key, value):
    return _send_marquee_command(set_state_command(key, value))


def get_state(key):
    return _send_marquee_command_and_receive_response(_make_command(COMMAND_GET_STATE, {
        'key': key}))


def _make_command(command_name, arguments=None):
    return {
        'name': command_name,
        'arguments': arguments}


def _send_on_socket(sock, payload):
    """
    Serialize and send payload via socket
    """
    buffer = pickle.dumps(payload)
    buffer_size_bytes = struct.pack('<Q', len(buffer))
    sock.sendall(buffer_size_bytes)
    sock.sendall(buffer)


def _receive_on_socket(connection):
    """
    Receive and de-serialize payload via socket
    """
    def receive(connection, byte_count):
        result = b''
        while len(result) < byte_count:
            chunk = connection.recv(byte_count - len(result))
            if chunk:
                result += chunk
        return result
    buffer_size_bytes = receive(connection, 8)
    buffer_size = struct.unpack('<Q', buffer_size_bytes)[0]
    buffer = receive(connection, buffer_size)
    return pickle.loads(buffer)


def _send_marquee_command(command):
    """
    Send command to marquee process. Used by clients (including other
    processes) who wants to interact with the marquee screen
    """
    TIMEOUT = 0.5
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.settimeout(TIMEOUT)
            sock.connect((HOST, PORT))
            _send_on_socket(sock, command)
            return True
        except (ConnectionRefusedError, TimeoutError) as ex:
            return False


def _send_marquee_command_and_receive_response(command):
    """
    Similar to "_send_marquee_command", but this one receives a response too
    """
    TIMEOUT = 0.5
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        try:
            sock.settimeout(TIMEOUT)
            sock.connect((HOST, PORT))
            _send_on_socket(sock, command)
            return _receive_on_socket(sock)
        except (ConnectionRefusedError, TimeoutError) as ex:
            return None

#
# Below here, "server side" rendering logic
#

def _get_fit_rect(iw, ih, rw, rh, fit=FIT_FIT, margin=0):

    ih = float(ih)
    iw = float(iw)

    rh = float(rh)
    rw = float(rw)

    sx = (rw - 2 * margin) / iw
    sy = (rh - 2 * margin) / ih

    if fit == FIT_FILL:
        s = max(sx, sy)

    elif fit == FIT_FIT:
        s = min(sx, sy)

    elif fit == FIT_STRETCH:
        return sdl2.SDL_FRect(x=margin, y=margin, w=rw - 2 * margin, h=rh - 2 * margin)

    elif fit == FIT_CENTER:
        s = 1.0

    dw = iw * s
    dh = ih * s
    dx = (rw - dw) * 0.5
    dy = (rh - dh) * 0.5

    return sdl2.SDL_FRect(x=dx, y=dy, w=dw, h=dh)


class Animation(ABC):

    @abstractmethod
    def restart(self, start_time=None):
        pass

    @abstractmethod
    def total_duration(self):
        pass

    @abstractmethod
    def evaluate(self, eval_time=None):
        pass


class ValueAnimation(Animation):
    """
    Animates a single numerical value
    """
    def __init__(self, begin, end, duration=0, start_time=None, ease=False, repeat=False, linger_duration=0, start_delay=0):
        assert duration >= 0.0
        self.begin = begin
        self.end = end
        self.duration = duration
        self.start_delay = start_delay
        self.linger_duration = linger_duration
        self.ease = ease
        self.repeat = repeat
        self.restart(start_time)

    def restart(self, start_time=None):
        self.start_time = time.time() if start_time is None else start_time

    def total_duration(self):
        return self.start_delay + self.duration + self.linger_duration

    def evaluate(self, eval_time=None):
        eval_time = time.time() if eval_time is None else eval_time
        dt = eval_time - self.start_time

        if dt < 0:
            return self.begin, False

        total_duration = self.total_duration()
        if self.repeat and dt > total_duration:
            dt %= total_duration

        if dt < self.start_delay:
            return self.begin, False

        if dt < self.start_delay + self.duration:
            r = (dt - self.start_delay) / self.duration
            if self.ease:
                r = r - 1.0
                r = -(r * r * r * r - 1.0)
            return self.begin + (self.end - self.begin) * r, False

        return self.end, dt > total_duration


class AnimationSequence(Animation):

    def __init__(self, *animations, repeat=False):
        self.animations = animations
        self.idx = 0
        self.repeat = repeat

    def restart(self, start_time=None):
        self.idx = 0
        for anim in self.animations:
            anim.restart(start_time)

    def total_duration(self):
        sum = 0.0
        for anim in self.animations:
            sum += anim.total_duration()
        return sum

    def evaluate(self, eval_time=None):
        anim = self.animations[self.idx]
        val, done = anim.evaluate(eval_time)
        if done and (self.idx < len(self.animations) - 1 or self.repeat):
            old_anim = self.animations[self.idx]
            new_anim_start_time = old_anim.start_time + old_anim.total_duration()
            self.idx += 1
            self.idx %= len(self.animations)
            new_anim = self.animations[self.idx]
            new_anim.restart(new_anim_start_time)
            return val, False
        return val, done


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

    def total_duration(self):
        return max(
            self.r.total_duration(),
            self.g.total_duration(),
            self.b.total_duration())

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
    def __init__(self, renderer, path, height=0, width=0, svg_aa_factor=1):

        MAX_DIM = 8192
        if path.lower().endswith('.svg'):
            self.surface = sdl2.ext.image.load_svg(path, int(width * svg_aa_factor), int(height * svg_aa_factor), as_argb=True)
            # Don't exceed max allowed texture size
            if self.surface.w > MAX_DIM or self.surface.h > MAX_DIM:
                sx = MAX_DIM / float(self.surface.w)
                sy = MAX_DIM / float(self.surface.h)
                s = min(sx, sy)
                sdl2.SDL_FreeSurface(self.surface)
                self.surface = sdl2.ext.image.load_svg(path, int(width * s), int(height * s), as_argb=True)
        else:
            self.surface = sdl2.ext.image.load_img(path, as_argb=True)

        assert self.surface.w <= MAX_DIM
        assert self.surface.h <= MAX_DIM

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


class FlyoutEffect(Effect):
    """
    Effect for displaying an image
    """
    def __init__(self, renderer, image_path, alpha, height_pct, margin, start_delay):
        _, h = _get_renderer_dimensions(renderer)
        self.alpha = alpha
        self.height_pct = height_pct
        self.margin = margin
        self.image = Image(renderer, image_path, height=int(h * height_pct))
        self.fade_anim = ValueAnimation(0.0, 1.0, 2.0, ease=True)
        self.translate_anim = ValueAnimation(0.0, 1.0, 4.0, ease=True, start_delay=start_delay)
        self.stopping = False
        self.stopped = False

    def stop(self):
        if not self.stopping:
            self.stopping = True
            current_fade_value, _ = self.fade_anim.evaluate()
            self.fade_anim = ValueAnimation(current_fade_value, 0.0, 1.0, ease=True)
            current_translate_value, _ = self.translate_anim.evaluate()
            self.translate_anim = ValueAnimation(current_translate_value, 0.0, 1.0, ease=True)

    def is_stopped(self):
        return self.stopped

    def render(self, renderer):
        rw, rh = _get_renderer_dimensions(renderer)

        fade_value, fade_animation_done = self.fade_anim.evaluate()
        translate_value, translate_animation_done = self.translate_anim.evaluate()

        sw = float(self.image.width)
        sh = float(self.image.height)

        sx = rw / sw
        sy = rh / sh
        s = min(sx, sy) * self.height_pct

        dw = sw * s
        dh = sh * s
        dy = (rh - dh) - self.margin
        dx = -dw + (dw + self.margin) * translate_value

        dst_rect = sdl2.SDL_FRect(x=dx, y=dy, w=dw, h=dh)

        sdl2.SDL_SetTextureAlphaMod(self.image.texture, int(fade_value * 255.0 * self.alpha))
        sdl2.SDL_RenderCopyF(renderer, self.image.texture, self.image.rect, dst_rect)

        if self.stopping and fade_animation_done and translate_animation_done:
            self.stopped = True

    def cleanup(self):
        self.image.cleanup()


class GrowImageEffect(Effect):
    """
    Effect for growing an image
    """
    def __init__(self, renderer, image_path, start_margin, end_margin, duration, fade):
        self.margin_anim = ValueAnimation(start_margin, end_margin, duration, ease=True)

        start_fade = 1.0
        end_fade = 1.0
        if fade == 'fadein':
            start_fade = 0.0
            end_fade = 1.0
        elif fade == 'fadeout':
            start_fade = 1.0
            end_fade = 0.0

        self.fade_anim = ValueAnimation(start_fade, end_fade, duration, ease=True)
        _, h = _get_renderer_dimensions(renderer)
        self.image = Image(renderer, image_path, height=h)
        self.stopping = False
        self.stopped = False

    def stop(self):
        if not self.stopping:
            self.stopping = True
            current_value, _ = self.fade_anim.evaluate()
            self.fade_anim = ValueAnimation(current_value, 1.0, 0.0, ease=True)

    def is_stopped(self):
        return self.stopped

    def render(self, renderer):
        rw, rh = _get_renderer_dimensions(renderer)

        sw = float(self.image.width)
        sh = float(self.image.height)

        margin, _ = self.margin_anim.evaluate()
        fade, fade_anim_done = self.fade_anim.evaluate()

        dst_rect = _get_fit_rect(sw, sh, rw, rh, margin=margin)

        sdl2.SDL_SetTextureAlphaMod(self.image.texture, int(fade * 255.0))
        sdl2.SDL_RenderCopyF(renderer, self.image.texture, self.image.rect, dst_rect)

        if self.stopping and fade_anim_done:
            self.stopped = True

    def cleanup(self):
        self.image.cleanup()


class ShowImageEffect(Effect):
    """
    Effect for displaying an image
    """
    def __init__(self, renderer, image_path, margin):
        _, h = _get_renderer_dimensions(renderer)
        self.margin = margin
        self.image = Image(renderer, image_path, height=h)
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
        rw, rh = _get_renderer_dimensions(renderer)

        sw = float(self.image.width)
        sh = float(self.image.height)

        dst_rect = _get_fit_rect(sw, sh, rw, rh, margin=self.margin)

        value, fade_animation_done = self.fade_anim.evaluate()

        sdl2.SDL_SetTextureAlphaMod(self.image.texture, int(value * 255.0))
        sdl2.SDL_RenderCopyF(renderer, self.image.texture, self.image.rect, dst_rect)

        if self.stopping and fade_animation_done:
            self.stopped = True

    def cleanup(self):
        self.image.cleanup()


class VideoPlaybackEffect(Effect):
    """
    Effect for video playback
    """
    def __init__(self, renderer, video_paths, margin, alpha, fit):

        self.video_paths = video_paths
        self.margin = margin
        self.alpha = alpha
        self.fit = fit

        self.fade_anim = ValueAnimation(0.0, 1.0, 1.0, ease=True)

        self.last_frame = None
        self.next_frame_idx = 0
        self.video_idx = 0
        self.loaded_video_path = None

        self.video = None
        self.tex = None

        self.stopping = False
        self.stopped = False

    def stop(self):
        if not self.stopping:
            self.stopping = True
            current_value, _ = self.fade_anim.evaluate()
            self.fade_anim = ValueAnimation(current_value, 0.0, 1.0, ease=True)

    def is_stopped(self):
        return self.stopped

    def _load_video(self, renderer, video_path):

        if not os.path.isfile(video_path):
            return None, None

        # Load new video
        video = cv2.VideoCapture(video_path)
        w = video.get(cv2.CAP_PROP_FRAME_WIDTH)
        h = video.get(cv2.CAP_PROP_FRAME_HEIGHT)

        # Create texture
        tex = sdl2.SDL_CreateTexture(
            renderer,
            sdl2.SDL_PIXELFORMAT_ABGR32,
            sdl2.SDL_TEXTUREACCESS_STREAMING,
            int(w), int(h))
        sdl2.SDL_SetTextureBlendMode(tex, sdl2.SDL_BLENDMODE_BLEND)

        return video, tex

    def _get_frame(self):

        # Compute desired frame index
        dt = time.time() - self.t0
        desired_frame_idx = int(round(dt * self.fps))

        if desired_frame_idx < self.next_frame_idx:
            # We're ahead, just re-use the last frame until we're caught up
            return self.last_frame

        else:
            # We're behind, we need to read some throw-away frames to catch up
            catchup_frames = desired_frame_idx - self.next_frame_idx
            for i in range(catchup_frames):
                ret, _ = self.video.read()
                self.next_frame_idx += 1

            # This is the frame we will use
            ret, frame = self.video.read()
            self.next_frame_idx += 1
            return frame

    def _copy_frame_to_tex(self, frame, tex):
        """
        Copy numpy (ndarray) to SDL texture
        """
        # Get video frame dimensions
        w = frame.shape[1]
        h = frame.shape[0]

        # Copy pixels from the decoded video 'frame' to the texture
        tex_pixels_ptr = c_void_p()
        tex_pixels_pitch = c_int()
        sdl2.SDL_LockTexture(tex, None, byref(tex_pixels_ptr), byref(tex_pixels_pitch))
        tex_pixels = cast(tex_pixels_ptr, POINTER(c_ubyte * (tex_pixels_pitch.value * h))).contents
        bytes_per_pixel = int(tex_pixels_pitch.value / w)
        tex_pixels_ndarray = np.ndarray((h, w, bytes_per_pixel), np.uint8, buffer=tex_pixels)

        # TODO:
        # Figure out why '/home/thomas/ES-DE/downloaded_media/snes/videos/Spot Goes to Hollywood (USA) (Proto).mp4' is broken when
        # using 3-channel textures. Using 4-channel textures seems to fix it, but requires some extra work as seen below.
        np.copyto(tex_pixels_ndarray[:,:,1:4], frame)
        tex_pixels_ndarray[:, :, 0] = int(255)

        sdl2.SDL_UnlockTexture(tex)

    def render(self, renderer):

        # When 'last_frame' is undefined, it indicates that either 1) no video has
        # been loaded yet OR 2) a video played to completion - in either case we have
        # to prepare the next video
        if self.last_frame is None:

            # Get video path
            video_path = self.video_paths[self.video_idx]
            assert video_path is not None
            self.video_idx += 1
            self.video_idx %= len(self.video_paths)

            if video_path != self.loaded_video_path:
                # This is a new video, load it
                self.cleanup()
                self.video, self.tex = self._load_video(renderer, video_path)
                if self.video is None or self.tex is None:
                    if len(self.video_paths) == 1:
                        # Failed to load the only video in the list, terminating effect
                        self.stopped = True
                    return
                self.loaded_video_path = video_path

            # Reset state
            self.fps = self.video.get(cv2.CAP_PROP_FPS)
            self.video.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.t0 = time.time()
            self.next_frame_idx = 0
            self.fade_anim = ValueAnimation(0.0, 1.0, 1.0, ease=True)

        # Decode frame for current time
        self.last_frame = self._get_frame()
        if self.last_frame is None:
            return

        # Copy frame to texture
        self._copy_frame_to_tex(self.last_frame, self.tex)

        # Set texture alpha value
        value, fade_animation_done = self.fade_anim.evaluate()
        sdl2.SDL_SetTextureAlphaMod(self.tex, int(value * self.alpha * 255.0))

        # Get video frame dimensions
        w = self.last_frame.shape[1]
        h = self.last_frame.shape[0]

        # Render
        src_rect = sdl2.SDL_Rect(0, 0, w, h)
        rw, rh = _get_renderer_dimensions(renderer)
        dst_rect = _get_fit_rect(w, h, rw, rh, fit=self.fit, margin=self.margin)
        sdl2.SDL_RenderCopyF(
            renderer,
            self.tex,
            src_rect,
            dst_rect)

        # Handle effect termination
        if self.stopping and fade_animation_done:
            self.stopped = True

    def cleanup(self):
        if self.video is not None:
            #self.video.close()
            self.video.release()
            self.video = None

        if self.tex is not None:
            sdl2.SDL_DestroyTexture(self.tex)
            self.tex = None


class PulseImageEffect(Effect):
    """
    Effect for pulsing an image
    """
    def __init__(self, renderer, image_path):
        _, h = _get_renderer_dimensions(renderer)
        self.image = Image(renderer, image_path, height=h)
        self.fade_anim = ValueAnimation(0.0, 1.0, 1.5, ease=True)

        grow = ValueAnimation(1, 1.25, 0.25, ease=True)
        shrink = ValueAnimation(1.25, 1.0, 2.0, ease=True, linger_duration=0.1)
        self.pulse_anim = AnimationSequence(grow, shrink, repeat=True)

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
        rw, rh = _get_renderer_dimensions(renderer)

        sw = float(self.image.width)
        sh = float(self.image.height)

        MARGIN = 8

        sx = (rw - 2 * MARGIN) / sw
        sy = (rh - 2 * MARGIN) / sh
        s = min(sx, sy)

        pulse_scale, _ = self.pulse_anim.evaluate()
        s *= pulse_scale

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
    def __init__(self, renderer, image_paths, pixels_per_second=400, reverse=False, margin=8, spacing=64, svg_aa_factor=1):

        rw, rh = _get_renderer_dimensions(renderer)

        self.margin = margin
        self.spacing = spacing

        self.images = [Image(renderer, path, height=rh, svg_aa_factor=svg_aa_factor) for path in image_paths]
        self.animations = []
        self.rects = []
        self.full_width = 0.0

        for image in self.images:

            s = (rh - (self.margin * 2)) / float(image.height)

            w = float(image.width) * s
            h = float(image.height) * s
            y = (rh - h) * 0.5

            rect = sdl2.SDL_FRect(x=0, y=y, w=w, h=h)
            self.rects.append(rect)

            self.full_width += rect.w + self.spacing

        pos0 = -self.full_width
        pos1 = (math.ceil(rw / self.full_width) + 1) * self.full_width
        if reverse:
            pos0, pos1 = pos1, pos0
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

        rw, rh = _get_renderer_dimensions(renderer)

        scroll_val, _ = self.scroll_anim.evaluate()
        alpha_val, alpha_anim_done = self.alpha_anim.evaluate()

        repeat_behind = math.ceil(scroll_val / self.full_width)
        pos = scroll_val - (repeat_behind * self.full_width)

        done = False
        while not done:
            for idx, _ in enumerate(self.images):
                self.draw_image(renderer, idx, alpha_val, pos)
                rect = self.rects[idx]
                pos += rect.w + self.spacing
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
    def __init__(self, renderer, image_paths):

        self.TOP_BOTTOM_MARGIN = 8
        self.PIXELS_PER_SECOND = 100

        rw, rh = _get_renderer_dimensions(renderer)
        self.images = [Image(renderer, path, height=rh) for path in image_paths]
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
        anim1 = ValueAnimation(pos0, pos1, abs(pos1 - pos0) / self.PIXELS_PER_SECOND, ease=True, linger_duration=1)

        pos0 = self.TOP_BOTTOM_MARGIN
        pos1 = -self.rects[self.current_image_idx].h
        anim2 = ValueAnimation(pos0, pos1, abs(pos1 - pos0) / self.PIXELS_PER_SECOND, ease=True)

        self.scroll_anim = AnimationSequence(anim1, anim2)

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

        rw, rh = _get_renderer_dimensions(renderer)

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


def _get_marquee_display_bounds(display_idx=DISPLAY_ONLY_MARQUEE):
    """
    Get the bounds of the marquee display
    """
    # Gather all display bounds
    display_count = sdl2.SDL_GetNumVideoDisplays()
    all_display_bounds = []
    for idx in range(display_count):
        bounds = sdl2.SDL_Rect()
        sdl2.SDL_GetDisplayBounds(idx, bounds)
        all_display_bounds.append(bounds)

    if display_idx == DISPLAY_ONLY_MARQUEE:

        # Only display if there are more than one display, pick the one with the smallest height
        assert display_count > 1
        auto_idx = 0
        for idx, bounds in enumerate(all_display_bounds):
            if bounds.h < all_display_bounds[auto_idx].h:
                auto_idx = idx
        return all_display_bounds[auto_idx]

    elif display_idx == DISPLAY_DEBUG:

        # Debug mode, create narrow display on subset of the main display
        bounds = all_display_bounds[0]
        bounds.h = int(bounds.h / 3.0)
        return bounds

    else:

        # Select explicitly defined display
        display_idx = max(0, min(display_count - 1, display_idx))
        return all_display_bounds[display_idx]


def _open_marquee_window(display_idx=DISPLAY_ONLY_MARQUEE):
    """
    Open marquee window (used on startup)
    """
    sdl2.SDL_Init(sdl2.SDL_INIT_VIDEO)

    bounds = _get_marquee_display_bounds(display_idx)

    window = sdl2.video.SDL_CreateWindow(
        b'Marquee',
        bounds.x, bounds.y,
        bounds.w, bounds.h,
        sdl2.SDL_WINDOW_BORDERLESS | sdl2.SDL_WINDOW_VULKAN)

    #sdl2.SDL_SetWindowAlwaysOnTop(window, True) # This may grab focus in some cases (I think)
    sdl2.SDL_ShowCursor(sdl2.SDL_DISABLE)

    renderer = sdl2.SDL_CreateRenderer(
        window, -1,
        sdl2.render.SDL_RENDERER_ACCELERATED | sdl2.SDL_RENDERER_PRESENTVSYNC)

    sdl2.SDL_SetHint(sdl2.SDL_HINT_RENDER_SCALE_QUALITY, b'best')
    sdl2.SDL_SetRenderDrawColor(renderer, 0, 0, 0, 255)
    sdl2.SDL_RenderClear(renderer)
    sdl2.SDL_RenderPresent(renderer)

    return window, renderer


def _close_marquee_window(window, renderer):
    """
    Close marquee window (used on shutdown)
    """
    sdl2.SDL_DestroyWindow(window)
    sdl2.SDL_DestroyRenderer(renderer)
    sdl2.SDL_Quit()


def _get_renderer_dimensions(renderer):
    """
    Get renderer dimensions
    """
    w = c_int(0)
    h = c_int(0)
    sdl2.SDL_GetRendererOutputSize(renderer, byref(w), byref(h))
    return w.value, h.value


def _process_marquee_command(command, render_manager):

    name = command['name']
    args = command['arguments']

    if name == COMMAND_SHOW_IMAGE:
        image_path = Path(args['image'])
        if image_path.is_file():
            effect = ShowImageEffect(render_manager.renderer, args['image'], args['margin'])
            render_manager.add_effect(effect)

    elif name == COMMAND_GROW_IMAGE:
        image_path = Path(args['image'])
        if image_path.is_file():
            effect = GrowImageEffect(render_manager.renderer, args['image'], args['startmargin'], args['endmargin'], args['duration'], args['fade'])
            render_manager.add_effect(effect)

    elif name == COMMAND_FLYOUT:
        image_path = Path(args['image'])
        if image_path.is_file():
            effect = FlyoutEffect(render_manager.renderer, args['image'], args['alpha'], args['height'], args['margin'], args['delay'])
            render_manager.add_effect(effect)

    elif name == COMMAND_PULSE_IMAGE:
        image_path = Path(args['image'])
        if image_path.is_file():
            effect = PulseImageEffect(render_manager.renderer, args['image'])
            render_manager.add_effect(effect)

    elif name == COMMAND_HORZ_SCROLL_IMAGES:
        if all([Path(image_path).is_file() for image_path in args['images']]):
            effect = HorizontalScrollImagesEffect(
                render_manager.renderer,
                args['images'],
                args['speed'],
                args['reverse'],
                args['margin'],
                args['spacing'],
                args['svgaafactor'])
            render_manager.add_effect(effect)

    elif name == COMMAND_VERT_SCROLL_IMAGES:
        if all([Path(image_path).is_file() for image_path in args['images']]):
            effect = VerticalScrollImagesEffect(
                render_manager.renderer,
                args['images'])
            render_manager.add_effect(effect)

    elif name == COMMAND_BACKGROUND:
        color = list(args['color'])
        render_manager.set_background_color(*color)

    elif name == COMMAND_PLAY_VIDEOS:
        effect = VideoPlaybackEffect(render_manager.renderer, args['videos'], args['margin'], args['alpha'], args['fit'])
        render_manager.add_effect(effect)

    elif name == COMMAND_CLEAR:
        render_manager.stop_all_effects()

    elif name == COMMAND_NOOP:
        pass

    elif name == COMMAND_COMMAND_LIST:
        for child_command in args['commands']:
            _process_marquee_command(child_command, render_manager)

    elif name == COMMAND_CLOSE:
        return False

    return True


def _process_events(events):
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


def _run_command_listener(command_queue):
    """
    Run the command listener
    """

    # Client state store
    state = {}

    # Create socket
    TIMEOUT = 0.5
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((HOST, PORT))
        sock.settimeout(TIMEOUT)
        sock.listen(1)

        # Main receive loop
        while True:
            try:
                connection, _ = sock.accept()
                command = _receive_on_socket(connection)

                name = command['name']
                args = command['arguments']

                if name == COMMAND_SET_STATE:
                    state[args['key']] = args['value']

                elif name == COMMAND_GET_STATE:
                    _send_on_socket(connection, state.get(args['key']))

                else:
                    command_queue.put(command)
                    if name == COMMAND_CLOSE:
                        break

            except TimeoutError:
                continue


class RenderManager(object):

    def __init__(self, renderer, max_effects_count):
        self.effects = []
        self.renderer = renderer
        self.color_anim = ColorAnimation((0, 0, 0), (0, 0, 0), 0)
        self.max_effects_count = max_effects_count

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
        for idx, effect in enumerate(self.effects):
            effect.render(self.renderer)

            # Note: Prune oldest effects if we exceed the max allowed limit
            prune_effect = len(self.effects) > self.max_effects_count and idx < len(self.effects) - self.max_effects_count

            if effect.is_stopped() or prune_effect:
                effect.cleanup()
                effects_to_remove.append(effect)

        for effect in effects_to_remove:
            self.effects.remove(effect)

        sdl2.SDL_RenderPresent(self.renderer)


def _dequeue_command(queue):
    """
    Dequeue command; if the queue is empty return None
    """
    try:
        return queue.get(block=False)
    except Empty:
        return None


def _main():
    """
    Main entry point
    """
    # Create marquee window
    display_idx = int(sys.argv[1]) if len(sys.argv) > 1 else DISPLAY_ONLY_MARQUEE
    window, renderer = _open_marquee_window(display_idx)

    # Create a command queue that we share between threads
    command_queue = Queue()

    # Start the command listener thread
    command_listener_thread = Thread(
        target=_run_command_listener,
        name='Marquee command listener thread',
        args=(command_queue,),
        daemon=True)
    command_listener_thread.start()

    # Create render manager
    MAX_EFFECT_COUNT = 10
    render_manager = RenderManager(renderer, MAX_EFFECT_COUNT)

    # Enter main loop
    while True:

        # Process events
        events = sdl2.ext.get_events()
        if not _process_events(events):
            close()

        # Get command
        command = _dequeue_command(command_queue)

        # Process command
        if command is not None:
            try:
                if not _process_marquee_command(command, render_manager):
                    break
            except SDLError:
                # Hacky, but some media files fail to load and this is the easiest
                # place to handle/ignore that
                pass

        # Render
        render_manager.render()

    # Cleanup render resources
    render_manager.cleanup()

    # Wait for command listener thread to finish
    command_listener_thread.join()

    # Close marquee window and cleanup
    _close_marquee_window(window, renderer)


if __name__ == "__main__":
    import sys
    import sdl2
    import sdl2.ext
    from sdl2.ext.err import SDLError
    from ctypes import c_int, c_ubyte, c_void_p, byref, cast, POINTER, pythonapi, py_object
    from threading import Thread, Event
    from queue import Queue, Empty
    from multiprocessing.connection import Listener
    from pathlib import Path
    import math
    import numpy as np
    import cv2
    _main()
