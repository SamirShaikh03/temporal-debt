"""
Custom event system for decoupled game communication.

Design Philosophy:
- Observer pattern for loose coupling between systems
- Named events for clarity and debugging
- Type hints for event data contracts
"""

from typing import Callable, Dict, List, Any
from dataclasses import dataclass
from enum import Enum, auto


class GameEvent(Enum):
    """
    All game events are enumerated here for type safety and discoverability.
    
    Naming Convention:
    - NOUN_VERB format (e.g., TIME_FROZEN, not FREEZE_TIME)
    - Past tense for completed actions
    - Present tense for state changes
    """
    
    # Time Events
    TIME_FROZEN = auto()
    TIME_UNFROZEN = auto()
    TIME_SCALE_CHANGED = auto()
    
    # Debt Events
    DEBT_CHANGED = auto()
    DEBT_TIER_CHANGED = auto()
    BANKRUPTCY_STARTED = auto()
    BANKRUPTCY_ENDED = auto()
    DEBT_ABSORBED = auto()
    
    # Anchor Events
    ANCHOR_PLACED = auto()
    ANCHOR_RECALLED = auto()
    ANCHOR_EXPIRED = auto()
    ANCHOR_LIMIT_REACHED = auto()
    
    # Player Events
    PLAYER_DIED = auto()
    PLAYER_RESPAWNED = auto()
    PLAYER_MOVED = auto()
    
    # Level Events
    LEVEL_STARTED = auto()
    LEVEL_COMPLETED = auto()
    CHECKPOINT_REACHED = auto()
    
    # Game State Events
    GAME_STARTED = auto()
    GAME_PAUSED = auto()
    GAME_RESUMED = auto()
    GAME_OVER = auto()
    GAME_WON = auto()
    
    # Entity Events
    ENTITY_SPAWNED = auto()
    ENTITY_DESTROYED = auto()
    COLLISION_OCCURRED = auto()
    
    # Interactable Events
    DOOR_OPENED = auto()
    DOOR_CLOSED = auto()
    SWITCH_ACTIVATED = auto()
    BOMB_TRIGGERED = auto()


@dataclass
class EventData:
    """
    Container for event-specific data.
    Each event type can have custom data attached.
    """
    event_type: GameEvent
    data: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.data is None:
            self.data = {}


class EventManager:
    """
    Central hub for game event distribution.
    
    Usage:
        event_manager = EventManager()
        
        # Subscribe to events
        event_manager.subscribe(GameEvent.TIME_FROZEN, self.on_time_frozen)
        
        # Emit events
        event_manager.emit(GameEvent.TIME_FROZEN, {"duration": 2.5})
    
    Design Decisions:
    - Single global instance pattern (but not enforced singleton)
    - Callbacks receive EventData object for flexibility
    - Subscriptions can be removed for cleanup
    """
    
    def __init__(self):
        """Initialize empty listener registry."""
        self._listeners: Dict[GameEvent, List[Callable]] = {}
        self._event_history: List[EventData] = []  # For debugging
        self._history_limit = 100
    
    def subscribe(self, event_type: GameEvent, callback: Callable[[EventData], None]) -> None:
        """
        Register a callback for a specific event type.
        
        Args:
            event_type: The event to listen for
            callback: Function to call when event is emitted
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        
        if callback not in self._listeners[event_type]:
            self._listeners[event_type].append(callback)
    
    def unsubscribe(self, event_type: GameEvent, callback: Callable) -> bool:
        """
        Remove a callback from an event's listener list.
        
        Returns:
            True if callback was removed, False if it wasn't registered
        """
        if event_type in self._listeners:
            if callback in self._listeners[event_type]:
                self._listeners[event_type].remove(callback)
                return True
        return False
    
    def emit(self, event_type: GameEvent, data: Dict[str, Any] = None) -> None:
        """
        Broadcast an event to all registered listeners.
        
        Args:
            event_type: The event being emitted
            data: Optional dictionary of event-specific data
        """
        event_data = EventData(event_type, data or {})
        
        # Store in history for debugging
        self._event_history.append(event_data)
        if len(self._event_history) > self._history_limit:
            self._event_history.pop(0)
        
        # Notify all listeners
        if event_type in self._listeners:
            for callback in self._listeners[event_type]:
                try:
                    callback(event_data)
                except Exception as e:
                    print(f"Error in event handler for {event_type.name}: {e}")
    
    def clear_listeners(self, event_type: GameEvent = None) -> None:
        """
        Remove all listeners for a specific event or all events.
        
        Args:
            event_type: Specific event to clear, or None for all
        """
        if event_type:
            self._listeners[event_type] = []
        else:
            self._listeners.clear()
    
    def get_history(self, limit: int = 10) -> List[EventData]:
        """
        Get recent event history for debugging.
        
        Args:
            limit: Maximum number of events to return
        
        Returns:
            List of recent EventData objects
        """
        return self._event_history[-limit:]
    
    def get_listener_count(self, event_type: GameEvent) -> int:
        """Get the number of listeners for an event type."""
        return len(self._listeners.get(event_type, []))


# Global event manager instance
# Can be imported and used throughout the game
_global_event_manager: EventManager = None


def get_event_manager() -> EventManager:
    """
    Get or create the global event manager.
    
    This provides a convenient way to access events from anywhere
    while still allowing dependency injection for testing.
    """
    global _global_event_manager
    if _global_event_manager is None:
        _global_event_manager = EventManager()
    return _global_event_manager


def reset_event_manager() -> None:
    """Reset the global event manager (useful for testing)."""
    global _global_event_manager
    _global_event_manager = EventManager()
