"""
Anchor System - Manages temporal anchors for save points.

Time Anchors allow players to mark positions and recall to them.
This creates tactical opportunities but comes at the cost of
instant debt accumulation.

Design Philosophy:
- Anchors are a powerful but costly tool
- Limited number forces strategic placement
- Decay timer prevents anchor hoarding
"""

from typing import List, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass
import pygame

from ..core.settings import Settings, COLORS
from ..core.events import EventManager, GameEvent, get_event_manager
from ..core.utils import Vector2

if TYPE_CHECKING:
    from ..systems.debt_manager import DebtManager


@dataclass
class TimeAnchor:
    """
    A temporal anchor point in the world.
    
    Anchors store a position and decay over time.
    Players can recall to anchors at the cost of debt.
    """
    position: Vector2
    creation_time: float  # When anchor was placed
    remaining_time: float  # Time until decay
    index: int  # Anchor slot (0-2)
    
    def update(self, dt: float) -> bool:
        """
        Update anchor decay timer.
        
        Args:
            dt: Time passed
            
        Returns:
            True if anchor has expired
        """
        self.remaining_time -= dt
        return self.remaining_time <= 0
    
    def get_decay_percentage(self) -> float:
        """Get remaining time as percentage (1.0 = fresh, 0.0 = about to expire)."""
        return self.remaining_time / Settings.ANCHOR_DECAY_TIME
    
    def to_dict(self) -> dict:
        """Serialize anchor to dictionary."""
        return {
            'position': (self.position.x, self.position.y),
            'remaining_time': self.remaining_time,
            'index': self.index
        }


class AnchorSystem:
    """
    Manages time anchors for tactical repositioning.
    
    Features:
    - Up to 3 simultaneous anchors
    - Anchors decay after 30 seconds
    - Recalling costs 2 seconds of instant debt
    - Visual feedback for anchor states
    
    Strategic Depth:
    Players must decide when to place anchors, which to keep,
    and whether the debt cost of recall is worth it.
    """
    
    def __init__(self, debt_manager: 'DebtManager' = None,
                 event_manager: EventManager = None):
        """
        Initialize the Anchor System.
        
        Args:
            debt_manager: Reference for applying recall debt
            event_manager: Event system for notifications
        """
        self.anchors: List[Optional[TimeAnchor]] = [None, None, None]
        self.max_anchors = Settings.MAX_ANCHORS
        self.decay_time = Settings.ANCHOR_DECAY_TIME
        self.recall_debt_cost = Settings.ANCHOR_RECALL_DEBT
        
        self._debt_manager = debt_manager
        self._event_manager = event_manager or get_event_manager()
        
        # Visual rendering
        self._pulse_timer = 0.0
        self._pulse_frequency = 2.0  # Pulses per second
    
    def set_debt_manager(self, debt_manager: 'DebtManager') -> None:
        """Set debt manager reference after initialization."""
        self._debt_manager = debt_manager
    
    def place_anchor(self, position: Vector2) -> Optional[TimeAnchor]:
        """
        Place a new time anchor at the given position.
        
        Args:
            position: World position for anchor
            
        Returns:
            The created anchor, or None if placement failed
        """
        # Find first empty slot
        empty_slot = None
        for i, anchor in enumerate(self.anchors):
            if anchor is None:
                empty_slot = i
                break
        
        if empty_slot is None:
            # All slots full - notify player
            self._event_manager.emit(GameEvent.ANCHOR_LIMIT_REACHED, {
                'max_anchors': self.max_anchors
            })
            # Remove oldest anchor to make room
            oldest_index = self._find_oldest_anchor()
            if oldest_index is not None:
                self.remove_anchor(oldest_index)
                empty_slot = oldest_index
            else:
                return None
        
        # Create new anchor
        anchor = TimeAnchor(
            position=position.copy(),
            creation_time=0,  # Will be set properly in game loop
            remaining_time=self.decay_time,
            index=empty_slot
        )
        
        self.anchors[empty_slot] = anchor
        
        # Emit event
        self._event_manager.emit(GameEvent.ANCHOR_PLACED, {
            'position': (position.x, position.y),
            'index': empty_slot,
            'total_anchors': self.get_anchor_count()
        })
        
        return anchor
    
    def recall_to_anchor(self, index: int) -> Optional[Vector2]:
        """
        Recall to a specific anchor.
        
        Args:
            index: Anchor slot index (0-2)
            
        Returns:
            Position to teleport to, or None if anchor doesn't exist
        """
        if index < 0 or index >= self.max_anchors:
            return None
        
        anchor = self.anchors[index]
        if anchor is None:
            return None
        
        # Get position before removing
        position = anchor.position.copy()
        
        # Apply debt cost
        if self._debt_manager:
            self._debt_manager.accrue_debt(self.recall_debt_cost)
        
        # Remove the used anchor
        self.anchors[index] = None
        
        # Emit event
        self._event_manager.emit(GameEvent.ANCHOR_RECALLED, {
            'position': (position.x, position.y),
            'index': index,
            'debt_cost': self.recall_debt_cost
        })
        
        return position
    
    def recall_to_nearest(self, current_position: Vector2) -> Optional[Vector2]:
        """
        Recall to the nearest anchor.
        
        Args:
            current_position: Player's current position
            
        Returns:
            Position to teleport to, or None if no anchors exist
        """
        nearest_index = None
        nearest_distance = float('inf')
        
        for i, anchor in enumerate(self.anchors):
            if anchor is not None:
                dist = current_position.distance_squared_to(anchor.position)
                if dist < nearest_distance:
                    nearest_distance = dist
                    nearest_index = i
        
        if nearest_index is not None:
            return self.recall_to_anchor(nearest_index)
        return None
    
    def remove_anchor(self, index: int) -> bool:
        """
        Remove an anchor without recalling.
        
        Args:
            index: Anchor slot index
            
        Returns:
            True if anchor was removed
        """
        if index < 0 or index >= self.max_anchors:
            return False
        
        if self.anchors[index] is not None:
            self.anchors[index] = None
            self._event_manager.emit(GameEvent.ANCHOR_EXPIRED, {
                'index': index
            })
            return True
        return False
    
    def _find_oldest_anchor(self) -> Optional[int]:
        """Find the anchor with least remaining time."""
        oldest_index = None
        min_time = float('inf')
        
        for i, anchor in enumerate(self.anchors):
            if anchor is not None and anchor.remaining_time < min_time:
                min_time = anchor.remaining_time
                oldest_index = i
        
        return oldest_index
    
    def update(self, dt: float) -> None:
        """
        Update all anchors.
        
        Args:
            dt: Time passed (real time, not game time)
        """
        # Update pulse animation
        self._pulse_timer += dt * self._pulse_frequency
        if self._pulse_timer > 1.0:
            self._pulse_timer -= 1.0
        
        # Update anchor decay
        for i, anchor in enumerate(self.anchors):
            if anchor is not None:
                if anchor.update(dt):
                    # Anchor expired
                    self.anchors[i] = None
                    self._event_manager.emit(GameEvent.ANCHOR_EXPIRED, {
                        'index': i
                    })
    
    def render(self, screen: pygame.Surface, camera_offset: Vector2 = None) -> None:
        """
        Render all active anchors.
        
        Args:
            screen: Surface to render to
            camera_offset: Optional camera offset
        """
        offset = camera_offset or Vector2.zero()
        
        for anchor in self.anchors:
            if anchor is None:
                continue
            
            # Calculate render position
            pos = anchor.position + offset
            
            # Get decay percentage for visual feedback
            decay = anchor.get_decay_percentage()
            
            # Calculate pulse
            pulse = abs(self._pulse_timer - 0.5) * 2  # 0 to 1 pulse
            
            # Base radius varies with decay
            base_radius = 20 + (10 * decay)
            pulse_radius = base_radius + (5 * pulse)
            
            # Alpha based on decay
            alpha = int(150 + 105 * decay)
            
            # Draw outer pulse ring
            self._draw_anchor_ring(screen, pos, pulse_radius, alpha // 2)
            
            # Draw inner solid circle
            self._draw_anchor_core(screen, pos, base_radius * 0.6, alpha)
            
            # Draw anchor index
            self._draw_anchor_label(screen, pos, anchor.index, alpha)
    
    def _draw_anchor_ring(self, screen: pygame.Surface, pos: Vector2,
                         radius: float, alpha: int) -> None:
        """Draw an anchor ring."""
        ring_surface = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(ring_surface, (*COLORS.ANCHOR, alpha),
                          (int(radius) + 2, int(radius) + 2), int(radius), 3)
        screen.blit(ring_surface, (int(pos.x - radius - 2), int(pos.y - radius - 2)))
    
    def _draw_anchor_core(self, screen: pygame.Surface, pos: Vector2,
                         radius: float, alpha: int) -> None:
        """Draw the anchor core."""
        core_surface = pygame.Surface((radius * 2 + 2, radius * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(core_surface, (*COLORS.ANCHOR, alpha),
                          (int(radius) + 1, int(radius) + 1), int(radius))
        screen.blit(core_surface, (int(pos.x - radius - 1), int(pos.y - radius - 1)))
    
    def _draw_anchor_label(self, screen: pygame.Surface, pos: Vector2,
                          index: int, alpha: int) -> None:
        """Draw anchor index label."""
        # Font rendering not implemented yet (requires font system)

    
    def get_anchor_positions(self) -> List[Tuple[int, Vector2]]:
        """Get list of (index, position) for all active anchors."""
        return [(i, a.position) for i, a in enumerate(self.anchors) if a is not None]
    
    def get_anchor_count(self) -> int:
        """Get number of active anchors."""
        return sum(1 for a in self.anchors if a is not None)
    
    def has_anchors(self) -> bool:
        """Check if any anchors are placed."""
        return any(a is not None for a in self.anchors)
    
    def clear_all(self) -> None:
        """Remove all anchors (on level change)."""
        for i in range(self.max_anchors):
            self.anchors[i] = None
    
    def get_stats(self) -> dict:
        """Get anchor system statistics."""
        return {
            'anchor_count': self.get_anchor_count(),
            'max_anchors': self.max_anchors,
            'anchors': [a.to_dict() if a else None for a in self.anchors]
        }
