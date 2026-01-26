"""
Player Entity - The Temporal Borrower.

The player is the only entity that can move during frozen time.
They navigate levels, avoid enemies, and manage temporal debt
to reach the exit.

Design Philosophy:
- Responsive controls even under time pressure
- Clear visual feedback for all states
- Simple movement, complex strategy
"""

from typing import List, Dict, Any, TYPE_CHECKING
import pygame

from .base_entity import BaseEntity
from ..core.settings import Settings, COLORS
from ..core.utils import Vector2, clamp
from ..core.events import EventManager, GameEvent, get_event_manager
from ..systems.collision import CollisionLayer

if TYPE_CHECKING:
    from ..systems.collision import CollisionResult



class Player(BaseEntity):
    """
    The player character - a Temporal Borrower.
    
    Features:
    - 8-directional movement
    - Immune to time freeze (can always move)
    - Dies on enemy contact
    - Respawns at checkpoints
    - Visual states for frozen/normal/invulnerable
    """
    
    def __init__(self, position: Vector2, event_manager: EventManager = None):
        """
        Initialize the player.
        
        Args:
            position: Starting position
            event_manager: Event system for player events
        """
        super().__init__(position, Settings.PLAYER_SIZE)
        
        # Movement
        self.speed = Settings.PLAYER_SPEED
        self.input_vector = Vector2.zero()
        self.facing = Vector2(1, 0)  # Direction player is facing
        
        # State
        self.is_dead = False
        self.can_move = True
        self.is_invulnerable = False
        self.invuln_timer = 0.0
        
        # Position tracking
        self.spawn_position = position.copy()
        self.last_checkpoint = position.copy()
        
        # Time state
        self.affected_by_time = False  # Player ignores time freeze
        self.is_time_frozen = False  # Track if world is frozen
        
        # Visual
        self.color = COLORS.PLAYER
        self.echo_color = COLORS.PLAYER
        
        # Collision
        self.collision_layer = CollisionLayer.PLAYER
        self.collision_mask = CollisionLayer.ENEMY | CollisionLayer.HAZARD | CollisionLayer.TRIGGER
        
        # Animation
        self._anim_timer = 0.0
        self._pulse_amount = 0.0
        
        # References
        self._event_manager = event_manager or get_event_manager()
        
        # Input buffer for responsive controls
        self._input_buffer: Dict[str, float] = {}
        self._buffer_duration = 0.1
    
    def handle_input(self, keys: pygame.key.ScancodeWrapper) -> None:
        """
        Process player input.
        
        Args:
            keys: Current keyboard state
        """
        if not self.can_move or self.is_dead:
            self.input_vector = Vector2.zero()
            return
        
        # Reset input
        self.input_vector = Vector2.zero()
        
        # Collect directional input
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.input_vector.y -= 1
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.input_vector.y += 1
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.input_vector.x -= 1
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.input_vector.x += 1
        
        # Normalize diagonal movement
        if self.input_vector.magnitude() > 0:
            self.input_vector = self.input_vector.normalized()
            self.facing = self.input_vector.copy()
    
    def update(self, dt: float) -> None:
        """
        Update player state.
        
        Args:
            dt: Delta time (real time for player, ignores time freeze)
        """
        if self.is_dead:
            return
        
        # Update invulnerability
        if self.is_invulnerable:
            self.invuln_timer -= dt
            if self.invuln_timer <= 0:
                self.is_invulnerable = False
        
        # Calculate movement
        if self.can_move:
            self.velocity = self.input_vector * self.speed
            movement = self.velocity * dt
            
            # Apply movement (collision handled externally)
            self.position = self.position + movement
            
            # Clamp to screen bounds
            self.position.x = clamp(self.position.x, 0, 
                                   Settings.SCREEN_WIDTH - self.size[0])
            self.position.y = clamp(self.position.y, 0, 
                                   Settings.SCREEN_HEIGHT - self.size[1])
        
        # Update animation
        self._update_animation(dt)
    
    def update_with_collision(self, dt: float, walls: List[pygame.Rect]) -> None:
        """
        Update player with wall collision handling.
        
        Args:
            dt: Delta time
            walls: List of wall rectangles
        """
        if self.is_dead:
            return
        
        # Update invulnerability
        if self.is_invulnerable:
            self.invuln_timer -= dt
            if self.invuln_timer <= 0:
                self.is_invulnerable = False
        
        # Calculate desired movement
        if self.can_move and self.input_vector.magnitude() > 0:
            self.velocity = self.input_vector * self.speed
            
            # Try movement on each axis separately for sliding
            # X axis
            new_x = self.position.x + self.velocity.x * dt
            test_rect = pygame.Rect(int(new_x), int(self.position.y), 
                                   self.size[0], self.size[1])
            
            can_move_x = True
            for wall in walls:
                if test_rect.colliderect(wall):
                    can_move_x = False
                    break
            
            if can_move_x:
                self.position.x = new_x
            
            # Y axis
            new_y = self.position.y + self.velocity.y * dt
            test_rect = pygame.Rect(int(self.position.x), int(new_y),
                                   self.size[0], self.size[1])
            
            can_move_y = True
            for wall in walls:
                if test_rect.colliderect(wall):
                    can_move_y = False
                    break
            
            if can_move_y:
                self.position.y = new_y
            
            # Clamp to screen
            self.position.x = clamp(self.position.x, 0,
                                   Settings.SCREEN_WIDTH - self.size[0])
            self.position.y = clamp(self.position.y, 0,
                                   Settings.SCREEN_HEIGHT - self.size[1])
        else:
            self.velocity = Vector2.zero()
        
        # Update animation
        self._update_animation(dt)
    
    def _update_animation(self, dt: float) -> None:
        """Update animation timers."""
        self._anim_timer += dt
        
        # Pulse when frozen
        if self.is_time_frozen:
            self._pulse_amount = (self._anim_timer * 4) % 1.0
        else:
            self._pulse_amount = 0
    
    def render(self, screen: pygame.Surface) -> None:
        """
        Render the player.
        
        Args:
            screen: Surface to render to
        """
        if not self.visible:
            return
        
        if self.is_dead:
            return
        
        # Determine color based on state
        if self.is_invulnerable:
            # Flash during invulnerability
            if int(self._anim_timer * 10) % 2 == 0:
                color = COLORS.WHITE
            else:
                color = self.color
        elif self.is_time_frozen:
            # Glowing effect during freeze
            pulse = abs(self._pulse_amount - 0.5) * 2
            color = (
                int(COLORS.PLAYER_FROZEN[0] + 50 * pulse),
                int(COLORS.PLAYER_FROZEN[1] + 30 * pulse),
                int(COLORS.PLAYER_FROZEN[2])
            )
        else:
            color = self.color
        
        # Draw player body
        rect = self.get_rect()
        pygame.draw.rect(screen, color, rect)
        
        # Draw facing indicator
        center = self.center
        indicator_end = center + self.facing * (self.size[0] * 0.6)
        pygame.draw.line(screen, COLORS.WHITE,
                        center.int_tuple, indicator_end.int_tuple, 3)
        
        # Draw outline
        pygame.draw.rect(screen, COLORS.WHITE, rect, 2)
    
    def die(self) -> None:
        """Handle player death."""
        if self.is_invulnerable or self.is_dead:
            return
        
        if Settings.GOD_MODE:
            return
        
        self.is_dead = True
        self.can_move = False
        self.velocity = Vector2.zero()
        
        self._event_manager.emit(GameEvent.PLAYER_DIED, {
            'position': (self.position.x, self.position.y)
        })
    
    def respawn(self, position: Vector2 = None) -> None:
        """
        Respawn the player.
        
        Args:
            position: Position to respawn at (uses last checkpoint if None)
        """
        respawn_pos = position if position else self.last_checkpoint
        
        self.position = respawn_pos.copy()
        self.velocity = Vector2.zero()
        self.is_dead = False
        self.can_move = True
        self.is_invulnerable = True
        self.invuln_timer = Settings.RESPAWN_INVULN_TIME
        
        self._event_manager.emit(GameEvent.PLAYER_RESPAWNED, {
            'position': (self.position.x, self.position.y)
        })
    
    def set_checkpoint(self, position: Vector2) -> None:
        """
        Update last checkpoint position.
        
        Args:
            position: New checkpoint position
        """
        self.last_checkpoint = position.copy()
    
    def set_time_frozen(self, frozen: bool) -> None:
        """Update frozen state for visual feedback."""
        self.is_time_frozen = frozen
    
    def on_collision(self, other: 'BaseEntity', result: 'CollisionResult') -> None:
        """Handle collision with other entities."""
        # Death on enemy/hazard collision
        if other.collision_layer & (CollisionLayer.ENEMY | CollisionLayer.HAZARD):
            self.die()
    
    def get_state(self) -> Dict[str, Any]:
        """Get current player state for saving/debugging."""
        return {
            'position': (self.position.x, self.position.y),
            'velocity': (self.velocity.x, self.velocity.y),
            'is_dead': self.is_dead,
            'is_invulnerable': self.is_invulnerable,
            'checkpoint': (self.last_checkpoint.x, self.last_checkpoint.y)
        }
