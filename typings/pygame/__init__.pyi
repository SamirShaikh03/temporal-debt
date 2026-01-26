# Type stubs for pygame - minimal definitions for type checking
from typing import Any, Tuple

# pygame constants
SRCALPHA: int
DOUBLEBUF: int
QUIT: int
KEYDOWN: int
MOUSEMOTION: int
MOUSEBUTTONDOWN: int

# Key constants
K_UP: int
K_DOWN: int
K_LEFT: int
K_RIGHT: int
K_w: int
K_a: int
K_s: int
K_d: int
K_SPACE: int
K_RETURN: int
K_ESCAPE: int
K_TAB: int
K_q: int
K_e: int
K_r: int

# Functions
def init() -> None: ...
def quit() -> None: ...

class Surface:
    def __init__(self, size: Tuple[int, int], flags: int = 0) -> None: ...
    def blit(self, source: Any, dest: Any, area: Any = None, special_flags: int = 0) -> Any: ...
    def fill(self, color: Any, rect: Any = None, special_flags: int = 0) -> Any: ...
    def get_rect(self, **kwargs: Any) -> Any: ...

class Rect:
    def __init__(self, left: int, top: int, width: int, height: int) -> None: ...
    x: int
    y: int
    width: int
    height: int
    left: int
    right: int
    top: int
    bottom: int
    centerx: int
    centery: int

class event:
    class Event:
        type: int
        key: int
    @staticmethod
    def get() -> list[Event]: ...

class draw:
    @staticmethod
    def rect(surface: Surface, color: Any, rect: Rect, width: int = 0) -> Rect: ...
    @staticmethod
    def circle(surface: Surface, color: Any, center: Tuple[int, int], radius: int, width: int = 0) -> Rect: ...
    @staticmethod
    def line(surface: Surface, color: Any, start_pos: Tuple[int, int], end_pos: Tuple[int, int], width: int = 1) -> Rect: ...
    @staticmethod
    def polygon(surface: Surface, color: Any, points: list[Tuple[float, float]], width: int = 0) -> Rect: ...

class display:
    @staticmethod
    def set_mode(size: Tuple[int, int], flags: int = 0, depth: int = 0) -> Surface: ...
    @staticmethod
    def flip() -> None: ...
    @staticmethod
    def set_caption(title: str) -> None: ...

class time:
    class Clock:
        def tick(self, framerate: int = 0) -> int: ...
        def get_fps() -> float: ...

class key:
    @staticmethod
    def get_pressed() -> Any: ...
