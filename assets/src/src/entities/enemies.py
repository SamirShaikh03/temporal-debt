"""
Enemy Entities - Various threats the player must avoid.

Enemies create the puzzle pressure:
- Patrol Drones: Predictable patterns, dangerous when rushed
- Temporal Hunters: Only move during freeze, punish overuse
- Debt Shadows: Spawn at high debt, chase relentlessly

Design Philosophy:
- Each enemy type counters a different strategy
- No "spam freeze to win" - hunters prevent this
- Debt shadows make high debt tangibly dangerous
"""

from typing import List, Tuple, Optional, TYPE_CHECKING
import pygame
import math

from .base_entity import BaseEntity
from ..core.settings import Settings, COLORS
from ..core.utils import Vector2
from ..systems.collision import CollisionLayer

if TYPE_CHECKING:
    from ..entities.player import Player



class PatrolDrone(BaseEntity):
    """
    A drone that patrols between waypoints.
    
    Patrol drones are the basic enemy type. They follow
    predictable patterns, making them avoidable with
    good timing and planning.
    
    Types:
    - linear: Back and forth between two points
    - circular: Orbit around a center point
    - seeker: Move toward player when in line of sight
    """
    
    def __init__(self, position: Vector2, patrol_points: List[Vector2],
                 drone_type: str = 'linear', speed: float = None):
        """
        Initialize a patrol drone.
        
        Args:
            position: Starting position
            patrol_points: List of waypoints to patrol between
            drone_type: 'linear', 'circular', or 'seeker'
            speed: Movement speed (uses default if None)
        """
        super().__init__(position, (40, 40))
        
        # Patrol configuration
        self.patrol_points = patrol_points
        self.drone_type = drone_type
        self.speed = speed or Settings.DRONE_SPEED
        
        # Patrol state
        self.current_target_index = 0
        self.patrol_direction = 1  # 1 = forward, -1 = backward
        
        # For circular patrol
        self.orbit_center = position.copy()
        self.orbit_radius = 100.0
        self.orbit_angle = 0.0
        self.orbit_speed = 1.0  # Radians per second
        
        # For seeker
        self.target: Optional['Player'] = None
        self.detection_range = Settings.SEEKER_RANGE
        self.can_see_player = False
        
        # Visual
        self.color = COLORS.DRONE
        self.echo_color = COLORS.DRONE
        
        # Collision
        self.collision_layer = CollisionLayer.ENEMY
        self.collision_mask = CollisionLayer.PLAYER
        
        # Animation
        self._rotation = 0.0
    
    def update(self, dt: float) -> None:
        """
        Update drone position based on type.
        
        Args:
            dt: Delta time (affected by time scale)
        """
        if dt == 0:  # Frozen in time
            return
        
        if self.drone_type == 'linear':
            self._update_linear(dt)
        elif self.drone_type == 'circular':
            self._update_circular(dt)
        elif self.drone_type == 'seeker':
            self._update_seeker(dt)
        
        # Update rotation for visual effect
        self._rotation += dt * 2
    
    def _update_linear(self, dt: float) -> None:
        """Update linear patrol movement."""
        if not self.patrol_points:
            return
        
        target = self.patrol_points[self.current_target_index]
        direction = (target - self.center)
        distance = direction.magnitude()
        
        if distance < 5:  # Reached waypoint
            # Move to next waypoint
            self.current_target_index += self.patrol_direction
            
            # Bounce at ends
            if self.current_target_index >= len(self.patrol_points):
                self.current_target_index = len(self.patrol_points) - 2
                self.patrol_direction = -1
            elif self.current_target_index < 0:
                self.current_target_index = 1
                self.patrol_direction = 1
        else:
            # Move toward target
            direction = direction.normalized()
            self.velocity = direction * self.speed
            self.position = self.position + self.velocity * dt
    
    def _update_circular(self, dt: float) -> None:
        """Update circular patrol movement."""
        self.orbit_angle += self.orbit_speed * dt
        
        # Calculate position on circle
        self.position.x = self.orbit_center.x + math.cos(self.orbit_angle) * self.orbit_radius - self.size[0] / 2
        self.position.y = self.orbit_center.y + math.sin(self.orbit_angle) * self.orbit_radius - self.size[1] / 2
        
        # Calculate velocity for predictions
        next_angle = self.orbit_angle + 0.1
        next_x = self.orbit_center.x + math.cos(next_angle) * self.orbit_radius
        next_y = self.orbit_center.y + math.sin(next_angle) * self.orbit_radius
        
        self.velocity = Vector2(
            (next_x - self.center.x) * 10,
            (next_y - self.center.y) * 10
        )
    
    def _update_seeker(self, dt: float) -> None:
        """Update seeker behavior."""
        if self.target is None:
            return
        
        # Check if player is in range and visible
        distance = self.center.distance_to(self.target.center)
        self.can_see_player = distance <= self.detection_range
        
        if self.can_see_player:
            # Move toward player
            direction = (self.target.center - self.center).normalized()
            self.velocity = direction * Settings.SEEKER_SPEED
            self.position = self.position + self.velocity * dt
        else:
            # Return to patrol
            self._update_linear(dt)
    
    def set_target(self, target: 'Player') -> None:
        """Set the seeker's target."""
        self.target = target
    
    def get_predicted_positions(self, duration: float, interval: float,
                                accuracy: float = 1.0) -> List[Tuple[Vector2, float]]:
        """Predict future positions based on patrol type."""
        predictions = []
        
        if self.drone_type == 'circular':
            # Predict circular motion
            t = interval
            while t <= duration:
                future_angle = self.orbit_angle + self.orbit_speed * t
                predicted_x = self.orbit_center.x + math.cos(future_angle) * self.orbit_radius - self.size[0] / 2
                predicted_y = self.orbit_center.y + math.sin(future_angle) * self.orbit_radius - self.size[1] / 2
                predictions.append((Vector2(predicted_x, predicted_y), t))
                t += interval
        elif self.drone_type == 'linear':
            # Simulate patrol
            sim_pos = self.position.copy()
            sim_target_idx = self.current_target_index
            sim_direction = self.patrol_direction
            
            t = interval
            while t <= duration and self.patrol_points:
                # Simulate movement
                target = self.patrol_points[sim_target_idx]
                move_dir = (target - (sim_pos + Vector2(self.size[0]/2, self.size[1]/2)))
                dist = move_dir.magnitude()
                
                move_amount = self.speed * interval
                if dist < move_amount:
                    sim_target_idx += sim_direction
                    if sim_target_idx >= len(self.patrol_points):
                        sim_target_idx = len(self.patrol_points) - 2
                        sim_direction = -1
                    elif sim_target_idx < 0:
                        sim_target_idx = 1
                        sim_direction = 1
                else:
                    sim_pos = sim_pos + move_dir.normalized() * move_amount
                
                predictions.append((sim_pos.copy(), t))
                t += interval
        else:
            # Default linear prediction for seekers
            return super().get_predicted_positions(duration, interval, accuracy)
        
        return predictions
    
    def render(self, screen: pygame.Surface) -> None:
        """Render the patrol drone."""
        if not self.visible:
            return
        
        rect = self.get_rect()
        center = self.center
        
        # Draw main body
        pygame.draw.rect(screen, self.color, rect)
        
        # Draw rotating indicator
        indicator_length = self.size[0] * 0.4
        end_x = center.x + math.cos(self._rotation) * indicator_length
        end_y = center.y + math.sin(self._rotation) * indicator_length
        pygame.draw.line(screen, COLORS.WHITE,
                        center.int_tuple, (int(end_x), int(end_y)), 2)
        
        # Draw seeker range (if seeker and debug)
        if self.drone_type == 'seeker' and Settings.DEBUG_MODE:
            pygame.draw.circle(screen, (255, 0, 0), center.int_tuple,
                             int(self.detection_range), 1)
        
        # Draw outline
        pygame.draw.rect(screen, COLORS.WHITE, rect, 2)


class TemporalHunter(BaseEntity):
    """
    An enemy that only moves when time is frozen.
    
    Temporal Hunters create a risk/reward tension:
    - Freezing time activates them
    - They approach the player during freeze
    - They stop when time resumes
    
    This prevents "spam freeze" strategies and adds
    tactical depth to time manipulation.
    """
    
    def __init__(self, position: Vector2, speed: float = None):
        """
        Initialize a temporal hunter.
        
        Args:
            position: Starting position
            speed: Movement speed during freeze
        """
        super().__init__(position, (48, 48))
        
        # Movement
        self.speed = speed or Settings.HUNTER_SPEED
        self.target: Optional['Player'] = None
        
        # State
        self.is_active = False  # Only active during time freeze
        self.home_position = position.copy()  # Returns here when inactive
        
        # Visual
        self.color = COLORS.HUNTER
        self.echo_color = COLORS.HUNTER
        self._eye_offset = 0.0
        
        # Collision
        self.collision_layer = CollisionLayer.ENEMY
        self.collision_mask = CollisionLayer.PLAYER
        
        # This entity moves during time freeze
        self.affected_by_time = False
    
    def update(self, dt: float, time_frozen: bool = False) -> None:
        """
        Update hunter state.
        
        Args:
            dt: Delta time
            time_frozen: Whether time is currently frozen
        """
        self.is_active = time_frozen
        
        if time_frozen and self.target:
            # Move toward player during freeze
            direction = (self.target.center - self.center).normalized()
            self.velocity = direction * self.speed
            self.position = self.position + self.velocity * dt
            
            # Eye tracks player
            self._eye_offset = math.atan2(
                self.target.center.y - self.center.y,
                self.target.center.x - self.center.x
            )
        else:
            # Slowly return home when not frozen
            if self.position.distance_to(self.home_position) > 5:
                direction = (self.home_position - self.position).normalized()
                self.velocity = direction * (self.speed * 0.3)
                self.position = self.position + self.velocity * dt
            else:
                self.velocity = Vector2.zero()
    
    def set_target(self, target: 'Player') -> None:
        """Set the hunt target."""
        self.target = target
    
    def render(self, screen: pygame.Surface) -> None:
        """Render the temporal hunter."""
        if not self.visible:
            return
        
        rect = self.get_rect()
        center = self.center
        
        # Determine color based on active state
        if self.is_active:
            color = self.color
            # Add glow effect when active
            glow_rect = pygame.Rect(
                rect.x - 3, rect.y - 3,
                rect.width + 6, rect.height + 6
            )
            glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*self.color, 100), 
                           (0, 0, glow_rect.width, glow_rect.height))
            screen.blit(glow_surf, glow_rect.topleft)
        else:
            # Dim when inactive
            color = (
                self.color[0] // 2,
                self.color[1] // 2,
                self.color[2] // 2
            )
        
        # Draw body
        pygame.draw.rect(screen, color, rect)
        
        # Draw "eye"
        eye_radius = 8
        eye_x = center.x + math.cos(self._eye_offset) * 10
        eye_y = center.y + math.sin(self._eye_offset) * 10
        pygame.draw.circle(screen, COLORS.WHITE, (int(eye_x), int(eye_y)), eye_radius)
        pygame.draw.circle(screen, COLORS.BLACK, (int(eye_x), int(eye_y)), eye_radius // 2)
        
        # Draw outline
        outline_color = COLORS.WHITE if self.is_active else COLORS.GRAY
        pygame.draw.rect(screen, outline_color, rect, 2)


class DebtShadow(BaseEntity):
    """
    A manifestation of temporal debt that chases the player.
    
    Debt Shadows spawn when debt exceeds a threshold and
    dissolve when debt returns to zero. They make high
    debt tangibly dangerous beyond just faster enemies.
    
    This creates a "death spiral" pressure when debt
    accumulates - exactly the experience we want.
    """
    
    def __init__(self, position: Vector2, target: 'Player'):
        """
        Initialize a debt shadow.
        
        Args:
            position: Spawn position
            target: Player to chase
        """
        super().__init__(position, (60, 60))
        
        # Movement
        self.speed = Settings.SHADOW_SPEED
        self.target = target
        
        # State
        self.spawn_threshold = Settings.SHADOW_SPAWN_DEBT
        self.is_dissolving = False
        self.dissolve_timer = 0.0
        self.dissolve_duration = 1.0
        
        # Visual
        self.color = COLORS.SHADOW
        self.alpha = 200
        self._wobble_timer = 0.0
        
        # Collision
        self.collision_layer = CollisionLayer.HAZARD
        self.collision_mask = CollisionLayer.PLAYER
        
        # Shadows move during time freeze too (unstoppable debt!)
        self.affected_by_time = False
    
    def update(self, dt: float, current_debt: float = 0) -> None:
        """
        Update shadow state.
        
        Args:
            dt: Delta time
            current_debt: Current debt level
        """
        # Check for dissolve condition
        if current_debt < self.spawn_threshold * 0.5 and not self.is_dissolving:
            self.dissolve()
        
        if self.is_dissolving:
            self.dissolve_timer += dt
            self.alpha = int(200 * (1 - self.dissolve_timer / self.dissolve_duration))
            if self.dissolve_timer >= self.dissolve_duration:
                self.destroy()
            return
        
        # Chase player
        if self.target and not self.target.is_dead:
            direction = (self.target.center - self.center).normalized()
            
            # Speed increases with debt
            debt_factor = 1 + (current_debt / 20)
            actual_speed = self.speed * debt_factor
            
            self.velocity = direction * actual_speed
            self.position = self.position + self.velocity * dt
        
        # Wobble animation
        self._wobble_timer += dt * 3
    
    def dissolve(self) -> None:
        """Start dissolving animation."""
        self.is_dissolving = True
        self.dissolve_timer = 0.0
    
    def render(self, screen: pygame.Surface) -> None:
        """Render the debt shadow."""
        if not self.visible:
            return
        
        rect = self.get_rect()
        center = self.center
        
        # Create surface with alpha
        shadow_surf = pygame.Surface((self.size[0] + 20, self.size[1] + 20), pygame.SRCALPHA)
        
        # Wobble effect
        wobble = math.sin(self._wobble_timer) * 3
        
        # Draw multiple layers for ethereal effect
        for i in range(3):
            offset = i * 3 + wobble
            layer_alpha = self.alpha // (i + 1)
            layer_rect = pygame.Rect(
                10 - offset, 10 - offset,
                self.size[0] + offset * 2, self.size[1] + offset * 2
            )
            pygame.draw.rect(shadow_surf, (*self.color, layer_alpha), layer_rect)
        
        screen.blit(shadow_surf, (int(rect.x - 10), int(rect.y - 10)))
        
        # Draw menacing eyes
        if not self.is_dissolving:
            eye_y = center.y - 5
            pygame.draw.circle(screen, (200, 0, 50), 
                             (int(center.x - 10), int(eye_y)), 5)
            pygame.draw.circle(screen, (200, 0, 50),
                             (int(center.x + 10), int(eye_y)), 5)
