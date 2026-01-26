"""
Base Entity - Abstract base class for all game objects.

All entities in TEMPORAL DEBT inherit from this class.
It provides common functionality for position, rendering, collision,
and temporal echo prediction.

Design Philosophy:
- Entities are self-contained and update/render themselves
- Time-awareness is built into the base class
- Prediction interface enables the echo system
"""

from typing import List, Tuple, TYPE_CHECKING
from abc import ABC, abstractmethod
import pygame
import uuid

from ..core.settings import Settings, COLORS
from ..core.utils import Vector2
from ..systems.collision import CollisionLayer

if TYPE_CHECKING:
    from ..systems.collision import CollisionResult



class BaseEntity(ABC):
    """
    Abstract base class for all game entities.
    
    Features:
    - Unique identification
    - Position and velocity
    - Collision handling
    - Time-awareness (can be frozen)
    - Prediction for echo system
    
    Subclasses must implement:
    - update(dt): Update entity state
    - render(screen): Draw entity
    """
    
    def __init__(self, position: Vector2, size: Tuple[int, int] = (32, 32)):
        """
        Initialize a base entity.
        
        Args:
            position: Starting position (top-left corner)
            size: Entity dimensions (width, height)
        """
        # Unique identifier
        self.id = str(uuid.uuid4())[:8]
        
        # Transform
        self.position = position.copy()
        self.velocity = Vector2.zero()
        self.size = size
        
        # State
        self.active = True  # Whether entity updates and renders
        self.visible = True  # Whether entity renders (can be inactive but visible)
        
        # Time behavior
        self.affected_by_time = True  # Whether time freeze affects this entity
        
        # Collision
        self.collision_layer = CollisionLayer.NONE
        self.collision_mask = CollisionLayer.NONE
        
        # Visual
        self.color = COLORS.WHITE
        self.echo_color = COLORS.ECHO  # Color for temporal echoes
        
        # Cached rect
        self._rect = pygame.Rect(
            int(position.x), int(position.y),
            size[0], size[1]
        )
    
    @property
    def center(self) -> Vector2:
        """Get entity center position."""
        return Vector2(
            self.position.x + self.size[0] / 2,
            self.position.y + self.size[1] / 2
        )
    
    @center.setter
    def center(self, value: Vector2) -> None:
        """Set position based on center."""
        self.position.x = value.x - self.size[0] / 2
        self.position.y = value.y - self.size[1] / 2
    
    def get_rect(self) -> pygame.Rect:
        """
        Get collision rectangle.
        
        Returns:
            pygame.Rect at current position
        """
        self._rect.x = int(self.position.x)
        self._rect.y = int(self.position.y)
        return self._rect
    
    @abstractmethod
    def update(self, dt: float) -> None:
        """
        Update entity state.
        
        Args:
            dt: Delta time (may be 0 if frozen, >1 if accelerated)
        
        Subclasses must implement this to update position,
        animation, behavior, etc.
        """

    
    @abstractmethod
    def render(self, screen: pygame.Surface) -> None:
        """
        Render entity to screen.
        
        Args:
            screen: Surface to render to
        
        Subclasses must implement this to draw the entity.
        """

    
    def get_predicted_positions(self, duration: float, interval: float,
                                accuracy: float = 1.0) -> List[Tuple[Vector2, float]]:
        """
        Predict future positions for echo system.
        
        Args:
            duration: How far into future to predict (seconds)
            interval: Time between predictions
            accuracy: Prediction accuracy (1.0 = perfect)
        
        Returns:
            List of (position, timestamp) tuples
        
        Default implementation assumes linear movement.
        Override for complex behaviors.
        """
        predictions = []
        current_pos = self.position.copy()
        current_vel = self.velocity.copy()
        
        t = interval
        while t <= duration:
            # Simple linear prediction
            predicted_pos = current_pos + current_vel * t
            
            # Add noise based on accuracy
            if accuracy < 1.0:
                import random
                noise = 10 * (1 - accuracy)
                predicted_pos.x += random.uniform(-noise, noise)
                predicted_pos.y += random.uniform(-noise, noise)
            
            predictions.append((predicted_pos, t))
            t += interval
        
        return predictions
    
    def on_collision(self, other: 'BaseEntity', result: 'CollisionResult') -> None:
        """
        Called when this entity collides with another.
        
        Args:
            other: The other entity
            result: Collision information
        
        Override in subclasses for specific collision responses.
        """
        # Default: no collision response

    
    def set_position(self, x: float, y: float) -> None:
        """Set position from coordinates."""
        self.position.x = x
        self.position.y = y
    
    def move(self, delta: Vector2) -> None:
        """Move by a delta amount."""
        self.position = self.position + delta
    
    def destroy(self) -> None:
        """Mark entity for destruction."""
        self.active = False
        self.visible = False
    
    def render_debug(self, screen: pygame.Surface) -> None:
        """
        Render debug information.
        
        Args:
            screen: Surface to render to
        
        Called when debug mode is enabled.
        """
        if Settings.SHOW_COLLISION_BOXES:
            pygame.draw.rect(screen, (255, 0, 0), self.get_rect(), 1)
    
    def distance_to(self, other: 'BaseEntity') -> float:
        """Get distance to another entity (center to center)."""
        return self.center.distance_to(other.center)
    
    def direction_to(self, other: 'BaseEntity') -> Vector2:
        """Get normalized direction toward another entity."""
        diff = other.center - self.center
        return diff.normalized()
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self.id}, pos={self.position})"
