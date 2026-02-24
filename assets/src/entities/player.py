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
import math

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
        
        # Trail system for smooth movement visual
        self._trail: List[Vector2] = []
        self._trail_timer = 0.0
        self._trail_max = 8
        
        # References
        self._event_manager = event_manager or get_event_manager()
        
        # Input buffer for responsive controls
        self._input_buffer: Dict[str, float] = {}
        self._buffer_duration = 0.1
        
        # Danger zone state
        self._in_danger_zone = False
        self._danger_slow_active = False
    
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
        """Update animation timers and trail."""
        self._anim_timer += dt
        
        # Trail recording
        self._trail_timer += dt
        if self._trail_timer >= 0.03 and self.velocity.magnitude() > 10:
            self._trail_timer = 0.0
            self._trail.append(self.center.copy())
            if len(self._trail) > self._trail_max:
                self._trail.pop(0)
        
        # Pulse when frozen
        if self.is_time_frozen:
            self._pulse_amount = (self._anim_timer * 4) % 1.0
        else:
            self._pulse_amount = 0
    
    def render(self, screen: pygame.Surface) -> None:
        """
        Render the player with neon glow and trail effects.
        
        Args:
            screen: Surface to render to
        """
        if not self.visible:
            return
        
        if self.is_dead:
            return
        
        # Draw trail first (behind player)
        if len(self._trail) > 1:
            for i, pos in enumerate(self._trail):
                t = i / len(self._trail)
                alpha = int(60 * t)
                sz = int(self.size[0] * 0.3 * t)
                if sz > 0 and alpha > 0:
                    trail_surf = pygame.Surface((sz * 2, sz * 2), pygame.SRCALPHA)
                    trail_color = (*self.color[:3], alpha)
                    pygame.draw.circle(trail_surf, trail_color, (sz, sz), sz)
                    screen.blit(trail_surf, (int(pos.x - sz), int(pos.y - sz)))
        
        # Determine color based on state
        if self.is_invulnerable:
            if int(self._anim_timer * 10) % 2 == 0:
                color = COLORS.WHITE
            else:
                color = self.color
        elif self.is_time_frozen:
            pulse = abs(self._pulse_amount - 0.5) * 2
            color = (
                min(255, int(COLORS.PLAYER_FROZEN[0] + 50 * pulse)),
                min(255, int(COLORS.PLAYER_FROZEN[1] + 30 * pulse)),
                int(COLORS.PLAYER_FROZEN[2])
            )
        elif self._in_danger_zone:
            # Red tinted in danger zone
            flash = (math.sin(self._anim_timer * 8) + 1) / 2
            color = (
                min(255, self.color[0] + int(80 * flash)),
                max(0, self.color[1] - int(60 * flash)),
                max(0, self.color[2] - int(60 * flash))
            )
        else:
            color = self.color
        
        rect = self.get_rect()
        center = self.center
        
        # Outer glow
        glow_size = self.size[0] + 12
        glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        glow_alpha = 35 if not self.is_time_frozen else 60
        pygame.draw.circle(glow_surf, (*color, glow_alpha),
                          (glow_size // 2, glow_size // 2), glow_size // 2)
        screen.blit(glow_surf, (int(center.x - glow_size // 2),
                                int(center.y - glow_size // 2)))
        
        # Draw player body — rounded rect
        pygame.draw.rect(screen, color, rect, border_radius=6)
        
        # Draw facing indicator — glowing line
        indicator_end = center + self.facing * (self.size[0] * 0.7)
        pygame.draw.line(screen, COLORS.WHITE,
                        center.int_tuple, indicator_end.int_tuple, 3)
        
        # Inner highlight
        inner = rect.inflate(-8, -8)
        highlight_color = (
            min(255, color[0] + 40),
            min(255, color[1] + 40),
            min(255, color[2] + 40)
        )
        pygame.draw.rect(screen, highlight_color, inner, 2, border_radius=3)
        
        # Outline
        outline_color = COLORS.WHITE if not self._in_danger_zone else (255, 100, 100)
        pygame.draw.rect(screen, outline_color, rect, 2, border_radius=6)
    
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
