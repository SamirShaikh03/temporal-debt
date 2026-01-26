"""
Interactable Entities - Objects the player can interact with.

Interactables create puzzle depth through debt manipulation:
- Debt Sinks: Absorb debt (limited uses)
- Debt Mirrors: Reflect debt as projectiles
- Debt Bombs: Explode with time acceleration
- Timed Doors: Require timing to pass through

Design Philosophy:
- Each interactable offers strategic options
- Limited uses force resource management
- Visual feedback shows state clearly
"""

from typing import Optional, TYPE_CHECKING
import pygame
import math

from .base_entity import BaseEntity
from ..core.settings import Settings, COLORS
from ..core.utils import Vector2
from ..core.events import GameEvent, get_event_manager
from ..systems.collision import CollisionLayer

if TYPE_CHECKING:
    from ..systems.debt_manager import DebtManager



class DebtSink(BaseEntity):
    """
    A crystal that absorbs temporal debt.
    
    Debt Sinks provide relief from high debt situations.
    Limited uses mean players must choose when to use them.
    
    Strategic Value:
    - Save for emergencies
    - Use before risky sections
    - Consider debt tier when deciding
    """
    
    def __init__(self, position: Vector2, uses: int = 1,
                 absorption_amount: float = None):
        """
        Initialize a debt sink.
        
        Args:
            position: Position in world
            uses: Number of times it can be used
            absorption_amount: Debt absorbed per use
        """
        super().__init__(position, (48, 48))
        
        # Configuration
        self.absorption_amount = absorption_amount or Settings.DEBT_SINK_AMOUNT
        self.uses_remaining = uses
        self.max_uses = uses
        
        # State
        self.is_depleted = False
        self.is_activating = False
        self.activation_timer = 0.0
        self.activation_duration = 0.5
        
        # Visual
        self.color = COLORS.DEBT_SINK
        self._pulse_timer = 0.0
        
        # Collision
        self.collision_layer = CollisionLayer.TRIGGER
        self.collision_mask = CollisionLayer.PLAYER
        
        # Reference to debt manager (set externally)
        self._debt_manager = None
    
    def set_debt_manager(self, debt_manager: 'DebtManager') -> None:
        """Set debt manager reference."""
        self._debt_manager = debt_manager
    
    def activate(self) -> float:
        """
        Activate the debt sink.
        
        Returns:
            Amount of debt absorbed
        """
        if self.is_depleted or self.uses_remaining <= 0:
            return 0
        
        if self._debt_manager is None:
            return 0
        
        # Absorb debt
        absorbed = self._debt_manager.absorb_debt(self.absorption_amount)
        
        # Update state
        self.uses_remaining -= 1
        self.is_activating = True
        self.activation_timer = 0.0
        
        if self.uses_remaining <= 0:
            self.is_depleted = True
        
        return absorbed
    
    def update(self, dt: float) -> None:
        """Update sink state."""
        if self.is_activating:
            self.activation_timer += dt
            if self.activation_timer >= self.activation_duration:
                self.is_activating = False
        
        # Pulse animation
        if not self.is_depleted:
            self._pulse_timer += dt * 2
    
    def render(self, screen: pygame.Surface) -> None:
        """Render the debt sink."""
        if not self.visible:
            return
        
        rect = self.get_rect()
        center = self.center
        
        if self.is_depleted:
            # Draw depleted crystal
            color = COLORS.DARK_GRAY
            pygame.draw.polygon(screen, color, [
                (center.x, rect.top),
                (rect.right, center.y),
                (center.x, rect.bottom),
                (rect.left, center.y)
            ])
        else:
            # Draw active crystal with pulse
            pulse = (math.sin(self._pulse_timer) + 1) / 2
            glow_size = 10 * pulse
            
            # Glow effect
            glow_surf = pygame.Surface((self.size[0] + 40, self.size[1] + 40), pygame.SRCALPHA)
            glow_color = (*self.color, int(50 + 50 * pulse))
            pygame.draw.circle(glow_surf, glow_color,
                             (self.size[0] // 2 + 20, self.size[1] // 2 + 20),
                             int(30 + glow_size))
            screen.blit(glow_surf, (rect.x - 20, rect.y - 20))
            
            # Crystal shape
            color = self.color if not self.is_activating else COLORS.WHITE
            pygame.draw.polygon(screen, color, [
                (center.x, rect.top),
                (rect.right, center.y),
                (center.x, rect.bottom),
                (rect.left, center.y)
            ])
            
            # Uses indicator
            for i in range(self.uses_remaining):
                dot_x = center.x - (self.max_uses - 1) * 5 + i * 10
                pygame.draw.circle(screen, COLORS.WHITE, (int(dot_x), int(rect.bottom + 8)), 3)


class DebtMirror(BaseEntity):
    """
    A mirror that can reflect temporal debt.
    
    Debt Mirrors add puzzle complexity by allowing
    debt to be redirected. They can:
    - Absorb incoming debt
    - Emit debt projectiles
    - Create chain reactions
    """
    
    def __init__(self, position: Vector2, facing_direction: Vector2):
        """
        Initialize a debt mirror.
        
        Args:
            position: Position in world
            facing_direction: Direction mirror faces
        """
        super().__init__(position, (16, 64))
        
        # Configuration
        self.facing_direction = facing_direction.normalized()
        
        # State
        self.stored_debt = 0.0
        self.max_stored_debt = 5.0
        self.is_charged = False
        
        # Visual
        self.color = COLORS.DEBT_MIRROR
        self._charge_glow = 0.0
        
        # Collision
        self.collision_layer = CollisionLayer.INTERACTABLE
    
    def absorb_debt(self, amount: float) -> float:
        """
        Absorb debt into the mirror.
        
        Args:
            amount: Debt to absorb
            
        Returns:
            Amount actually absorbed
        """
        space_remaining = self.max_stored_debt - self.stored_debt
        absorbed = min(amount, space_remaining)
        self.stored_debt += absorbed
        
        if self.stored_debt >= self.max_stored_debt * 0.5:
            self.is_charged = True
        
        return absorbed
    
    def emit_debt(self) -> Optional[Vector2]:
        """
        Emit stored debt as a projectile direction.
        
        Returns:
            Direction of emitted debt, or None if not charged
        """
        if not self.is_charged:
            return None
        
        self.stored_debt = 0.0
        self.is_charged = False
        
        return self.facing_direction.copy()
    
    def update(self, dt: float) -> None:
        """Update mirror state."""
        if self.is_charged:
            self._charge_glow = min(1.0, self._charge_glow + dt * 2)
        else:
            self._charge_glow = max(0.0, self._charge_glow - dt * 2)
    
    def render(self, screen: pygame.Surface) -> None:
        """Render the debt mirror."""
        if not self.visible:
            return
        
        rect = self.get_rect()
        center = self.center
        
        # Draw mirror surface
        color = self.color
        if self.is_charged:
            # Add glow when charged
            glow_intensity = int(50 * self._charge_glow)
            color = (
                min(255, self.color[0] + glow_intensity),
                min(255, self.color[1] + glow_intensity),
                self.color[2]
            )
        
        pygame.draw.rect(screen, color, rect)
        
        # Draw facing indicator
        arrow_start = center
        arrow_end = center + self.facing_direction * 30
        pygame.draw.line(screen, COLORS.WHITE,
                        arrow_start.int_tuple, arrow_end.int_tuple, 2)
        
        # Draw charge level
        if self.stored_debt > 0:
            charge_height = int(rect.height * (self.stored_debt / self.max_stored_debt))
            charge_rect = pygame.Rect(
                rect.x, rect.bottom - charge_height,
                rect.width, charge_height
            )
            pygame.draw.rect(screen, COLORS.DEBT_BAR_FILL, charge_rect)


class DebtBomb(BaseEntity):
    """
    An explosive that detonates with temporal energy.
    
    When triggered, creates a zone of time acceleration.
    Entities in the zone experience sped-up time,
    including the player.
    """
    
    def __init__(self, position: Vector2, trigger_type: str = 'proximity',
                 payload: float = None, radius: float = None):
        """
        Initialize a debt bomb.
        
        Args:
            position: Position in world
            trigger_type: 'proximity' or 'interaction'
            payload: Amount of debt in explosion
            radius: Explosion radius
        """
        super().__init__(position, (40, 40))
        
        # Configuration
        self.trigger_type = trigger_type
        self.payload = payload or Settings.DEBT_BOMB_PAYLOAD
        self.radius = radius or Settings.DEBT_BOMB_RADIUS
        self.trigger_distance = 60.0
        
        # State
        self.is_triggered = False
        self.is_exploding = False
        self.explosion_timer = 0.0
        self.explosion_duration = 2.0
        self.fuse_timer = 0.0
        self.fuse_duration = 1.0
        
        # Visual
        self.color = COLORS.DEBT_BOMB
        self._tick_timer = 0.0
        
        # Collision
        self.collision_layer = CollisionLayer.INTERACTABLE
    
    def trigger(self) -> None:
        """Start the bomb's fuse."""
        if self.is_triggered:
            return
        
        self.is_triggered = True
        self.fuse_timer = 0.0
        
        get_event_manager().emit(GameEvent.BOMB_TRIGGERED, {
            'position': (self.position.x, self.position.y)
        })
    
    def update(self, dt: float, player_position: Vector2 = None) -> Optional[dict]:
        """
        Update bomb state.
        
        Args:
            dt: Delta time
            player_position: Player position for proximity check
            
        Returns:
            Explosion data if exploded this frame, else None
        """
        # Proximity trigger
        if self.trigger_type == 'proximity' and player_position and not self.is_triggered:
            distance = self.center.distance_to(player_position)
            if distance < self.trigger_distance:
                self.trigger()
        
        # Fuse countdown
        if self.is_triggered and not self.is_exploding:
            self.fuse_timer += dt
            self._tick_timer += dt * 10
            
            if self.fuse_timer >= self.fuse_duration:
                self.is_exploding = True
                return self._create_explosion_data()
        
        # Explosion duration
        if self.is_exploding:
            self.explosion_timer += dt
            if self.explosion_timer >= self.explosion_duration:
                self.destroy()
        
        return None
    
    def _create_explosion_data(self) -> dict:
        """Create explosion effect data."""
        return {
            'center': self.center.copy(),
            'radius': self.radius,
            'payload': self.payload,
            'duration': self.explosion_duration
        }
    
    def render(self, screen: pygame.Surface) -> None:
        """Render the debt bomb."""
        if not self.visible:
            return
        
        rect = self.get_rect()
        center = self.center
        
        if self.is_exploding:
            # Draw explosion effect
            progress = self.explosion_timer / self.explosion_duration
            current_radius = self.radius * (1 - progress * 0.3)
            alpha = int(150 * (1 - progress))
            
            explosion_surf = pygame.Surface((int(self.radius * 2 + 20), 
                                            int(self.radius * 2 + 20)), pygame.SRCALPHA)
            pygame.draw.circle(explosion_surf, (*self.color, alpha),
                             (int(self.radius + 10), int(self.radius + 10)),
                             int(current_radius))
            screen.blit(explosion_surf, 
                       (int(center.x - self.radius - 10), 
                        int(center.y - self.radius - 10)))
        else:
            # Draw bomb
            if self.is_triggered:
                # Flash when triggered
                flash = int(self._tick_timer) % 2 == 0
                color = COLORS.WHITE if flash else self.color
            else:
                color = self.color
            
            pygame.draw.circle(screen, color, center.int_tuple, self.size[0] // 2)
            
            # Draw fuse
            if self.is_triggered:
                fuse_length = 15 * (1 - self.fuse_timer / self.fuse_duration)
                pygame.draw.line(screen, COLORS.WHITE,
                               (center.x, rect.top),
                               (center.x, rect.top - fuse_length), 2)


class TimedDoor(BaseEntity):
    """
    A door that opens temporarily when triggered.
    
    Timed doors create timing puzzles - the player must
    trigger the door and reach it before it closes.
    Time freezing is key to solving these puzzles.
    """
    
    def __init__(self, position: Vector2, size: tuple = (64, 64),
                 open_duration: float = None):
        """
        Initialize a timed door.
        
        Args:
            position: Position in world
            size: Door dimensions
            open_duration: How long door stays open
        """
        super().__init__(position, size)
        
        # Configuration
        self.open_duration = open_duration or Settings.DOOR_OPEN_DURATION
        
        # State
        self.is_open = False
        self.timer = 0.0
        
        # Visual
        self.closed_color = COLORS.DOOR_CLOSED
        self.open_color = COLORS.DOOR_OPEN
        
        # Collision - blocks when closed
        self.collision_layer = CollisionLayer.WALL
        self.collision_mask = CollisionLayer.PLAYER
    
    def open(self) -> None:
        """Open the door."""
        if self.is_open:
            return
        
        self.is_open = True
        self.timer = self.open_duration
        self.collision_layer = CollisionLayer.NONE
        
        get_event_manager().emit(GameEvent.DOOR_OPENED, {
            'position': (self.position.x, self.position.y)
        })
    
    def close(self) -> None:
        """Close the door."""
        if not self.is_open:
            return
        
        self.is_open = False
        self.timer = 0.0
        self.collision_layer = CollisionLayer.WALL
        
        get_event_manager().emit(GameEvent.DOOR_CLOSED, {
            'position': (self.position.x, self.position.y)
        })
    
    def toggle(self) -> None:
        """Toggle door state."""
        if self.is_open:
            self.close()
        else:
            self.open()
    
    def update(self, dt: float) -> None:
        """Update door timer."""
        if self.is_open:
            self.timer -= dt
            if self.timer <= 0:
                self.close()
    
    def render(self, screen: pygame.Surface) -> None:
        """Render the door."""
        if not self.visible:
            return
        
        rect = self.get_rect()
        
        if self.is_open:
            color = self.open_color
            # Draw partially open door
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, COLORS.WHITE, rect, 2)
            
            # Timer indicator
            timer_width = int(rect.width * (self.timer / self.open_duration))
            timer_rect = pygame.Rect(rect.x, rect.bottom + 2, timer_width, 4)
            pygame.draw.rect(screen, COLORS.WHITE, timer_rect)
        else:
            color = self.closed_color
            pygame.draw.rect(screen, color, rect)
            pygame.draw.rect(screen, COLORS.WHITE, rect, 2)


class ExitZone(BaseEntity):
    """
    Level exit trigger zone.
    
    When the player enters this zone, the level is completed.
    """
    
    def __init__(self, position: Vector2, size: tuple = (64, 64)):
        """Initialize exit zone."""
        super().__init__(position, size)
        
        self.color = COLORS.EXIT_ZONE
        self._pulse_timer = 0.0
        
        self.collision_layer = CollisionLayer.TRIGGER
        self.collision_mask = CollisionLayer.PLAYER
        
        self.triggered = False
    
    def update(self, dt: float) -> None:
        """Update exit animation."""
        self._pulse_timer += dt * 3
    
    def render(self, screen: pygame.Surface) -> None:
        """Render exit zone."""
        if not self.visible:
            return
        
        rect = self.get_rect()
        
        # Pulsing glow
        pulse = (math.sin(self._pulse_timer) + 1) / 2
        glow_alpha = int(30 + 50 * pulse)
        
        glow_surf = pygame.Surface((self.size[0] + 20, self.size[1] + 20), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (*self.color, glow_alpha),
                        (0, 0, self.size[0] + 20, self.size[1] + 20))
        screen.blit(glow_surf, (rect.x - 10, rect.y - 10))
        
        # Main zone
        pygame.draw.rect(screen, self.color, rect)
        pygame.draw.rect(screen, COLORS.WHITE, rect, 2)
        
        # Exit text would go here with font rendering


class Checkpoint(BaseEntity):
    """
    Checkpoint that saves player progress.
    
    When touched, becomes the new respawn point.
    """
    
    def __init__(self, position: Vector2):
        """Initialize checkpoint."""
        super().__init__(position, (32, 64))
        
        self.color = COLORS.CHECKPOINT
        self.is_activated = False
        self._glow_timer = 0.0
        
        self.collision_layer = CollisionLayer.TRIGGER
        self.collision_mask = CollisionLayer.PLAYER
    
    def activate(self) -> None:
        """Activate this checkpoint."""
        self.is_activated = True
    
    def update(self, dt: float) -> None:
        """Update checkpoint animation."""
        if self.is_activated:
            self._glow_timer += dt * 2
    
    def render(self, screen: pygame.Surface) -> None:
        """Render checkpoint."""
        if not self.visible:
            return
        
        rect = self.get_rect()
        
        # Glow when activated
        if self.is_activated:
            pulse = (math.sin(self._glow_timer) + 1) / 2
            glow_alpha = int(50 + 30 * pulse)
            
            glow_surf = pygame.Surface((self.size[0] + 20, self.size[1] + 20), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*self.color, glow_alpha),
                           (0, 0, self.size[0] + 20, self.size[1] + 20))
            screen.blit(glow_surf, (rect.x - 10, rect.y - 10))
            
            color = self.color
        else:
            color = COLORS.GRAY
        
        # Draw flag pole
        pole_rect = pygame.Rect(rect.x + rect.width // 2 - 2, rect.y, 4, rect.height)
        pygame.draw.rect(screen, COLORS.WHITE, pole_rect)
        
        # Draw flag
        flag_points = [
            (pole_rect.right, rect.y),
            (pole_rect.right + 20, rect.y + 15),
            (pole_rect.right, rect.y + 30)
        ]
        pygame.draw.polygon(screen, color, flag_points)
