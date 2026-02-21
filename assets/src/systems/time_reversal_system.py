"""
Time Reversal System - Limited ability to rewind game state.

Time Reversal is a powerful "super" ability that allows players to
rewind the last few seconds of gameplay. Unlike anchors (which teleport),
this actually reverses the game state including enemy positions.

Design Philosophy:
- High-cost, high-reward safety net
- Limited uses create meaningful decisions
- Visual spectacle for important moments
- Recharges at checkpoints, encouraging progress
"""

from typing import List, Dict, Any, Optional, TYPE_CHECKING
from dataclasses import dataclass
from collections import deque
import pygame
import math

from ..core.settings import Settings, COLORS
from ..core.events import EventManager, GameEvent, get_event_manager
from ..core.utils import Vector2, lerp, get_font

if TYPE_CHECKING:
    from ..systems.debt_manager import DebtManager


@dataclass
class GameStateSnapshot:
    """
    A snapshot of game state at a point in time.
    
    Contains all information needed to restore the game
    to a previous moment.
    """
    timestamp: float
    player_position: Vector2
    player_velocity: Vector2
    entity_states: Dict[str, Dict[str, Any]]  # Entity ID -> state dict
    debt_amount: float
    debt_tier: int


class TimeReversalSystem:
    """
    Manages time reversal - a powerful rewind ability.
    
    Features:
    - Records game state snapshots every 0.1 seconds
    - Stores last 5 seconds of game state
    - Press R to rewind (costs 8 seconds of instant debt)
    - Limited uses per life (recharges at checkpoints)
    - Dramatic visual effect during rewind
    """
    
    # Configuration
    RECORDING_DURATION = 5.0  # Seconds of state to record
    RECORDING_INTERVAL = 0.1  # Seconds between snapshots
    REWIND_DURATION = 3.0  # How far back to rewind
    DEBT_COST = 8.0  # Instant debt cost for using rewind
    USES_PER_LIFE = 1  # Uses before needing checkpoint recharge
    REWIND_VISUAL_DURATION = 1.0  # Duration of rewind visual effect
    
    MAX_SNAPSHOTS = int(RECORDING_DURATION / RECORDING_INTERVAL)
    
    def __init__(self, event_manager: EventManager = None):
        """
        Initialize the Time Reversal System.
        
        Args:
            event_manager: Event system for notifications
        """
        self._event_manager = event_manager or get_event_manager()
        
        # State recording
        self._snapshots: deque[GameStateSnapshot] = deque(maxlen=self.MAX_SNAPSHOTS)
        self._record_timer = 0.0
        self._recording_time = 0.0
        
        # References
        self._debt_manager: Optional['DebtManager'] = None
        
        # Usage tracking
        self._uses_remaining = self.USES_PER_LIFE
        self._total_uses = 0
        
        # Rewind state
        self._is_rewinding = False
        self._rewind_timer = 0.0
        self._rewind_visual_alpha = 0.0
        self._target_snapshot: Optional[GameStateSnapshot] = None
        
        # Visual effects
        self._effect_particles: List[Dict] = []
    
    def set_debt_manager(self, debt_manager: 'DebtManager') -> None:
        """Set debt manager reference."""
        self._debt_manager = debt_manager
    
    @property
    def can_rewind(self) -> bool:
        """Whether rewind is currently available."""
        return (self._uses_remaining > 0 and 
                len(self._snapshots) >= 10 and
                not self._is_rewinding)
    
    @property
    def uses_remaining(self) -> int:
        """Number of rewind uses remaining."""
        return self._uses_remaining
    
    @property
    def is_rewinding(self) -> bool:
        """Whether currently in rewind visual state."""
        return self._is_rewinding
    
    def record_state(self, player_pos: Vector2, player_vel: Vector2,
                    entities: List[Any], debt: float, tier: int, dt: float) -> None:
        """
        Record current game state for potential rewind.
        
        Args:
            player_pos: Current player position
            player_vel: Current player velocity
            entities: List of game entities with state info
            debt: Current debt amount
            tier: Current debt tier
            dt: Delta time
        """
        if self._is_rewinding:
            return
        
        self._record_timer += dt
        self._recording_time += dt
        
        if self._record_timer >= self.RECORDING_INTERVAL:
            self._record_timer = 0.0
            
            # Build entity state dict
            entity_states = {}
            for entity in entities:
                if hasattr(entity, 'id') and hasattr(entity, 'position'):
                    entity_states[entity.id] = {
                        'position': entity.position.copy() if hasattr(entity.position, 'copy') else Vector2(entity.position.x, entity.position.y),
                        'velocity': getattr(entity, 'velocity', Vector2.zero()),
                        'active': getattr(entity, 'active', True)
                    }
            
            snapshot = GameStateSnapshot(
                timestamp=self._recording_time,
                player_position=player_pos.copy(),
                player_velocity=player_vel.copy(),
                entity_states=entity_states,
                debt_amount=debt,
                debt_tier=tier
            )
            
            self._snapshots.append(snapshot)
    
    def initiate_rewind(self) -> Optional[GameStateSnapshot]:
        """
        Begin time reversal.
        
        Returns:
            The target snapshot to restore to, or None if rewind unavailable
        """
        if not self.can_rewind:
            return None
        
        # Find snapshot from REWIND_DURATION seconds ago
        target_time = self._recording_time - self.REWIND_DURATION
        target_snapshot = None
        
        for snapshot in self._snapshots:
            if snapshot.timestamp <= target_time:
                target_snapshot = snapshot
            else:
                break
        
        # If no old enough snapshot, use oldest
        if target_snapshot is None and self._snapshots:
            target_snapshot = self._snapshots[0]
        
        if target_snapshot is None:
            return None
        
        # Apply debt cost
        if self._debt_manager:
            self._debt_manager.accrue_debt(self.DEBT_COST)
        
        # Start rewind effect
        self._is_rewinding = True
        self._rewind_timer = 0.0
        self._rewind_visual_alpha = 1.0
        self._target_snapshot = target_snapshot
        self._uses_remaining -= 1
        self._total_uses += 1
        
        # Spawn visual particles
        self._spawn_rewind_particles()
        
        # Emit event
        self._event_manager.emit(GameEvent.DEBT_CHANGED, {
            'time_reversal': True,
            'debt_cost': self.DEBT_COST
        })
        
        return target_snapshot
    
    def _spawn_rewind_particles(self) -> None:
        """Spawn dramatic particles for rewind effect."""
        import random
        
        for _ in range(50):
            self._effect_particles.append({
                'x': random.uniform(0, Settings.SCREEN_WIDTH),
                'y': random.uniform(0, Settings.SCREEN_HEIGHT),
                'target_x': Settings.SCREEN_WIDTH / 2,
                'target_y': Settings.SCREEN_HEIGHT / 2,
                'life': 1.0,
                'size': random.uniform(3, 10),
                'speed': random.uniform(200, 400)
            })
    
    def update(self, dt: float) -> None:
        """
        Update the reversal system.
        
        Args:
            dt: Delta time
        """
        if self._is_rewinding:
            self._rewind_timer += dt
            
            # Fade out effect
            self._rewind_visual_alpha = lerp(
                self._rewind_visual_alpha,
                0.0,
                dt * 2
            )
            
            if self._rewind_timer >= self.REWIND_VISUAL_DURATION:
                self._is_rewinding = False
                self._target_snapshot = None
        
        # Update particles
        for particle in self._effect_particles[:]:
            # Move toward center
            dx = particle['target_x'] - particle['x']
            dy = particle['target_y'] - particle['y']
            dist = math.sqrt(dx * dx + dy * dy)
            
            if dist > 1:
                particle['x'] += (dx / dist) * particle['speed'] * dt
                particle['y'] += (dy / dist) * particle['speed'] * dt
            
            particle['life'] -= dt * 1.5
            
            if particle['life'] <= 0:
                self._effect_particles.remove(particle)
    
    def render(self, screen: pygame.Surface) -> None:
        """Render reversal visual effects and UI."""
        # Render rewind effect
        if self._is_rewinding or self._rewind_visual_alpha > 0.1:
            self._render_rewind_effect(screen)
        
        # Render particles
        self._render_particles(screen)
        
        # Render indicator
        self._render_indicator(screen)
    
    def _render_rewind_effect(self, screen: pygame.Surface) -> None:
        """Render the rewind visual overlay."""
        alpha = int(150 * self._rewind_visual_alpha)
        
        # Purple overlay
        overlay = pygame.Surface((Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((100, 50, 150, alpha))
        screen.blit(overlay, (0, 0))
        
        # Concentric rings expanding from center
        center_x = Settings.SCREEN_WIDTH // 2
        center_y = Settings.SCREEN_HEIGHT // 2
        
        num_rings = 5
        for i in range(num_rings):
            ring_progress = (self._rewind_timer * 2 + i * 0.2) % 1.0
            radius = int(ring_progress * max(Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT))
            ring_alpha = int(100 * (1 - ring_progress) * self._rewind_visual_alpha)
            
            ring_surf = pygame.Surface((radius * 2 + 10, radius * 2 + 10), pygame.SRCALPHA)
            pygame.draw.circle(ring_surf, (200, 150, 255, ring_alpha),
                             (radius + 5, radius + 5), radius, 3)
            screen.blit(ring_surf, (center_x - radius - 5, center_y - radius - 5))
        
        # "REWINDING" text
        if self._rewind_visual_alpha > 0.5:
            try:
                font = get_font('Arial', 48, bold=True)
            except Exception:
                font = pygame.font.Font(None, 52)
            
            text = "REWINDING"
            text_surf = font.render(text, True, (255, 200, 255))
            text_alpha = int(255 * self._rewind_visual_alpha)
            text_surf.set_alpha(text_alpha)
            
            text_rect = text_surf.get_rect(center=(center_x, center_y))
            screen.blit(text_surf, text_rect)
    
    def _render_particles(self, screen: pygame.Surface) -> None:
        """Render rewind effect particles."""
        for particle in self._effect_particles:
            alpha = int(255 * particle['life'])
            size = int(particle['size'] * particle['life'])
            if size < 1:
                continue
            
            particle_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(particle_surf, (200, 150, 255, alpha), (size, size), size)
            screen.blit(particle_surf, (int(particle['x']) - size, int(particle['y']) - size))
    
    def _render_indicator(self, screen: pygame.Surface) -> None:
        """Render the rewind ability indicator."""
        x = Settings.SCREEN_WIDTH - 120
        y = 180
        
        try:
            font = get_font('Arial', 12)
        except Exception:
            font = pygame.font.Font(None, 14)
        
        # Status
        if self._is_rewinding:
            text = "REWINDING..."
            color = (200, 150, 255)
        elif self._uses_remaining > 0:
            text = f"REWIND READY [R] x{self._uses_remaining}"
            color = (200, 150, 255)
        else:
            text = "REWIND DEPLETED"
            color = (100, 100, 100)
        
        text_surf = font.render(text, True, color)
        screen.blit(text_surf, (x, y))
        
        # Visual indicator
        indicator_y = y + 15
        for i in range(self.USES_PER_LIFE):
            indicator_x = x + i * 20
            if i < self._uses_remaining:
                pygame.draw.circle(screen, (200, 150, 255), (indicator_x + 6, indicator_y + 6), 6)
            else:
                pygame.draw.circle(screen, (60, 60, 80), (indicator_x + 6, indicator_y + 6), 6)
                pygame.draw.circle(screen, (100, 100, 100), (indicator_x + 6, indicator_y + 6), 6, 1)
    
    def recharge_at_checkpoint(self) -> None:
        """Recharge uses when reaching a checkpoint."""
        if self._uses_remaining < self.USES_PER_LIFE:
            self._uses_remaining = self.USES_PER_LIFE
            self._event_manager.emit(GameEvent.CHECKPOINT_REACHED, {
                'rewind_recharged': True
            })
    
    def reset(self) -> None:
        """Reset the system (e.g., on death)."""
        self._snapshots.clear()
        self._record_timer = 0.0
        self._recording_time = 0.0
        self._uses_remaining = self.USES_PER_LIFE
        self._is_rewinding = False
        self._target_snapshot = None
        self._effect_particles.clear()
    
    def get_stats(self) -> dict:
        """Get reversal statistics."""
        return {
            'total_uses': self._total_uses,
            'uses_remaining': self._uses_remaining
        }
