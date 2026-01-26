"""Core game modules."""
from .settings import Settings
from .events import EventManager, GameEvent, get_event_manager, reset_event_manager
from .utils import Vector2, clamp, lerp
from .game import Game, GameState
