"""
Echo System - Renders temporal echoes showing predicted entity paths.

When time is frozen, entities display "echoes" showing where they
will be in the future. This allows strategic planning and creates
a unique visual language for the game.

Design Philosophy:
- Echoes are predictions, not recordings
- Higher debt = less accurate predictions (uncertainty)
- Echoes fade with distance into future
"""

from typing import List, Dict, Tuple, TYPE_CHECKING
from dataclasses import dataclass
import pygame

from ..core.settings import Settings, COLORS
from ..core.utils import Vector2

if TYPE_CHECKING:
    from ..entities.base_entity import BaseEntity


@dataclass
class EchoFrame:
    """
    A single frame in an echo trail.
    
    Represents one predicted future position of an entity.
    """
    position: Vector2
    timestamp: float  # Seconds into future
    alpha: int  # Transparency (0-255)
    rotation: float = 0  # Optional rotation
    
    def get_alpha_surface(self, base_surface: pygame.Surface) -> pygame.Surface:
        """Create a copy of surface with this frame's alpha."""
        surface = base_surface.copy()
        surface.set_alpha(self.alpha)
        return surface


class EntityEcho:
    """
    Echo trail for a single entity.
    
    Contains multiple EchoFrames representing the entity's
    predicted path through time.
    """
    
    def __init__(self, entity_id: str, color: Tuple[int, int, int]):
        """
        Initialize an entity echo.
        
        Args:
            entity_id: Unique identifier for the entity
            color: Base color for echo rendering
        """
        self.entity_id = entity_id
        self.color = color
        self.frames: List[EchoFrame] = []
        self.size = (32, 32)  # Default size, updated from entity
    
    def update_prediction(self, positions: List[Tuple[Vector2, float]], 
                         base_alpha: int = Settings.ECHO_BASE_ALPHA) -> None:
        """
        Update the echo frames with new predictions.
        
        Args:
            positions: List of (position, timestamp) tuples
            base_alpha: Starting alpha value
        """
        self.frames.clear()
        
        alpha = base_alpha
        for pos, timestamp in positions:
            self.frames.append(EchoFrame(
                position=pos.copy(),
                timestamp=timestamp,
                alpha=int(alpha)
            ))
            alpha *= Settings.ECHO_FADE_RATE
    
    def render(self, screen: pygame.Surface, offset: Vector2 = None) -> None:
        """
        Render the echo trail.
        
        Args:
            screen: Surface to render to
            offset: Optional camera offset
        """
        offset = offset or Vector2.zero()
        
        for frame in self.frames:
            # Create echo surface
            echo_surface = pygame.Surface(self.size, pygame.SRCALPHA)
            
            # Draw echo shape (simple rectangle with alpha)
            echo_color = (*self.color, frame.alpha)
            pygame.draw.rect(echo_surface, echo_color, 
                           (0, 0, self.size[0], self.size[1]))
            
            # Draw at predicted position
            pos = frame.position + offset
            screen.blit(echo_surface, pos.int_tuple)


class EchoSystem:
    """
    Manages temporal echoes for all entities.
    
    The Echo System:
    1. Tracks which entities should have echoes
    2. Calculates predicted future positions
    3. Renders echo trails when time is frozen
    
    Accuracy System:
    Higher debt levels reduce echo accuracy, visualizing
    the "uncertainty" of predicting a chaotic future.
    """
    
    def __init__(self):
        """Initialize the Echo System."""
        self.echoes: Dict[str, EntityEcho] = {}
        self.active = False
        
        # Prediction parameters
        self.prediction_duration = Settings.ECHO_PREDICTION_DURATION
        self.echo_interval = Settings.ECHO_INTERVAL
        
        # Accuracy modifier (reduced at high debt)
        self.accuracy = 1.0
    
    def activate(self) -> None:
        """Activate echo rendering (when time freezes)."""
        self.active = True
    
    def deactivate(self) -> None:
        """Deactivate echo rendering (when time unfreezes)."""
        self.active = False
        # Keep echoes cached for quick re-activation
    
    def register_entity(self, entity_id: str, color: Tuple[int, int, int],
                       size: Tuple[int, int] = (32, 32)) -> None:
        """
        Register an entity to receive echoes.
        
        Args:
            entity_id: Unique entity identifier
            color: Base color for echoes
            size: Size of echo shapes
        """
        echo = EntityEcho(entity_id, color)
        echo.size = size
        self.echoes[entity_id] = echo
    
    def unregister_entity(self, entity_id: str) -> None:
        """Remove an entity from echo tracking."""
        if entity_id in self.echoes:
            del self.echoes[entity_id]
    
    def update(self, entities: List['BaseEntity'], debt_level: float = 0) -> None:
        """
        Update echo predictions for all registered entities.
        
        Args:
            entities: List of entities to predict
            debt_level: Current debt for accuracy calculation
        """
        if not self.active:
            return
        
        # Calculate accuracy based on debt
        # At 15+ seconds debt, accuracy drops significantly
        self.accuracy = max(0.5, 1.0 - (debt_level / 30))
        
        for entity in entities:
            if not hasattr(entity, 'id') or not hasattr(entity, 'get_predicted_positions'):
                continue
            
            if entity.id not in self.echoes:
                # Auto-register unknown entities
                color = getattr(entity, 'echo_color', COLORS.ECHO)
                size = getattr(entity, 'size', (32, 32))
                self.register_entity(entity.id, color, size)
            
            # Get predicted positions from entity
            predictions = entity.get_predicted_positions(
                self.prediction_duration,
                self.echo_interval,
                self.accuracy
            )
            
            # Update echo
            self.echoes[entity.id].update_prediction(predictions)
    
    def render(self, screen: pygame.Surface, offset: Vector2 = None) -> None:
        """
        Render all active echoes.
        
        Args:
            screen: Surface to render to
            offset: Optional camera offset
        """
        if not self.active:
            return
        
        for echo in self.echoes.values():
            echo.render(screen, offset)
    
    def clear(self) -> None:
        """Clear all echoes."""
        self.echoes.clear()
    
    def set_accuracy(self, accuracy: float) -> None:
        """
        Set prediction accuracy.
        
        Args:
            accuracy: 0.0 to 1.0 (1.0 = perfect prediction)
        """
        self.accuracy = max(0.0, min(1.0, accuracy))


class EchoRenderer:
    """
    Static utility class for rendering individual echo effects.
    
    Used for special echo visualizations beyond simple trails.
    """
    
    @staticmethod
    def render_pulse(screen: pygame.Surface, center: Vector2, 
                    radius: float, color: Tuple[int, int, int],
                    alpha: int = 100) -> None:
        """
        Render a pulsing echo circle.
        
        Args:
            screen: Surface to render to
            center: Center position
            radius: Circle radius
            color: Circle color
            alpha: Transparency
        """
        pulse_surface = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(pulse_surface, (*color, alpha),
                          (int(radius), int(radius)), int(radius), 2)
        screen.blit(pulse_surface, 
                   (int(center.x - radius), int(center.y - radius)))
    
    @staticmethod
    def render_trail_line(screen: pygame.Surface, 
                         points: List[Vector2],
                         color: Tuple[int, int, int],
                         start_alpha: int = 200) -> None:
        """
        Render a fading line trail.
        
        Args:
            screen: Surface to render to
            points: List of positions
            color: Line color
            start_alpha: Starting transparency
        """
        if len(points) < 2:
            return
        
        alpha = start_alpha
        for i in range(len(points) - 1):
            # Create line surface
            p1 = points[i]
            p2 = points[i + 1]
            
            # Draw line segment with current alpha
            pygame.draw.line(screen, (*color, int(alpha)),
                           p1.int_tuple, p2.int_tuple, 2)
            
            alpha *= Settings.ECHO_FADE_RATE
