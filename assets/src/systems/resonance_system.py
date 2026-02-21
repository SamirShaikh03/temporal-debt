"""
Resonance System - Periodic time waves that create risk/reward gameplay.

Resonance events are waves that periodically sweep through levels,
creating a rhythmic element to gameplay. Players must adapt their
freeze timing to avoid penalties and gain bonuses.

Design Philosophy:
- Add dynamic timing element to levels
- Create moments of high tension
- Reward awareness and planning
- Penalize careless freeze spam
"""

from typing import List, Optional, TYPE_CHECKING
from enum import Enum, auto
import pygame
import math

from ..core.settings import Settings, COLORS
from ..core.events import EventManager, GameEvent, get_event_manager
from ..core.utils import Vector2, lerp, get_font

if TYPE_CHECKING:
    from ..systems.time_engine import TimeEngine
    from ..systems.debt_manager import DebtManager


class ResonancePhase(Enum):
    """Phases of a resonance event."""
    CALM = auto()      # No wave active
    WARNING = auto()   # Wave approaching (visual warning)
    ACTIVE = auto()    # Wave passing through
    AFTERMATH = auto() # Brief cooldown after wave


class ResonanceSystem:
    """
    Manages temporal resonance waves that sweep through levels.
    
    Waves occur every 15-20 seconds and create a brief moment
    where being frozen is penalized and moving is rewarded:
    
    - Frozen during wave: +3 seconds instant debt
    - Moving during wave: -0.5 seconds debt relief
    - Standing still: No effect
    
    Visual: A golden wave sweeps across the screen with particle effects.
    """
    
    # Configuration
    MIN_WAVE_INTERVAL = 15.0  # Minimum seconds between waves
    MAX_WAVE_INTERVAL = 20.0  # Maximum seconds between waves
    WARNING_DURATION = 2.0  # Seconds of warning before wave
    WAVE_DURATION = 1.5  # Duration of active wave
    AFTERMATH_DURATION = 1.0  # Cooldown after wave
    
    FROZEN_PENALTY = 3.0  # Debt added if frozen during wave
    MOVING_BONUS = 0.5  # Debt removed if moving during wave
    
    def __init__(self, event_manager: EventManager = None):
        """
        Initialize the Resonance System.
        
        Args:
            event_manager: Event system for notifications
        """
        self._event_manager = event_manager or get_event_manager()
        
        # State
        self._phase = ResonancePhase.CALM
        self._timer = 0.0
        self._next_wave_time = self._calculate_next_wave_time()
        
        # References (set externally)
        self._time_engine = None
        self._debt_manager = None
        
        # Visual state
        self._wave_position = 0.0  # 0.0 to 1.0 (left to right)
        self._visual_intensity = 0.0
        self._particles: List[dict] = []
        
        # Statistics
        self._waves_survived = 0
        self._waves_penalized = 0
        self._total_bonus_earned = 0.0
        
        # Enabled flag
        self.enabled = True
    
    def set_systems(self, time_engine: 'TimeEngine', debt_manager: 'DebtManager') -> None:
        """Set system references."""
        self._time_engine = time_engine
        self._debt_manager = debt_manager
    
    def _calculate_next_wave_time(self) -> float:
        """Calculate random time until next wave."""
        import random
        return random.uniform(self.MIN_WAVE_INTERVAL, self.MAX_WAVE_INTERVAL)
    
    @property
    def phase(self) -> ResonancePhase:
        """Current phase of resonance cycle."""
        return self._phase
    
    @property
    def is_wave_active(self) -> bool:
        """Whether a wave is currently passing through."""
        return self._phase == ResonancePhase.ACTIVE
    
    @property
    def time_until_wave(self) -> float:
        """Seconds until next wave, or 0 if wave is active."""
        if self._phase == ResonancePhase.CALM:
            return max(0, self._next_wave_time - self._timer)
        return 0.0
    
    @property
    def wave_progress(self) -> float:
        """Progress through current wave cycle (0.0 to 1.0)."""
        if self._phase == ResonancePhase.CALM:
            # Progress towards next wave
            return min(1.0, self._timer / self._next_wave_time)
        elif self._phase == ResonancePhase.WARNING:
            # Warning phase progress
            return min(1.0, self._timer / self.WARNING_DURATION)
        elif self._phase == ResonancePhase.ACTIVE:
            # Active wave progress
            return self._wave_position
        else:  # AFTERMATH
            return 1.0
    
    @property
    def state(self) -> ResonancePhase:
        """Alias for phase property for compatibility."""
        return self._phase
    
    def update(self, dt: float, player_moving: bool = False) -> None:
        """
        Update resonance system.
        
        Args:
            dt: Delta time
            player_moving: Whether the player is currently moving
        """
        if not self.enabled:
            return
        
        self._timer += dt
        
        if self._phase == ResonancePhase.CALM:
            # Wait for next wave
            if self._timer >= self._next_wave_time:
                self._start_warning()
        
        elif self._phase == ResonancePhase.WARNING:
            # Visual warning building up
            self._visual_intensity = lerp(self._visual_intensity, 1.0, dt * 3)
            if self._timer >= self.WARNING_DURATION:
                self._start_wave()
        
        elif self._phase == ResonancePhase.ACTIVE:
            # Wave passing through
            self._wave_position = self._timer / self.WAVE_DURATION
            self._update_wave_effects(player_moving)
            self._spawn_wave_particles()
            
            if self._timer >= self.WAVE_DURATION:
                self._end_wave()
        
        elif self._phase == ResonancePhase.AFTERMATH:
            # Cooldown
            self._visual_intensity = lerp(self._visual_intensity, 0.0, dt * 2)
            if self._timer >= self.AFTERMATH_DURATION:
                self._reset_cycle()
        
        # Update particles
        self._update_particles(dt)
    
    def _start_warning(self) -> None:
        """Begin the warning phase."""
        self._phase = ResonancePhase.WARNING
        self._timer = 0.0
        self._visual_intensity = 0.0
        
        # Emit warning event
        self._event_manager.emit(GameEvent.DEBT_CHANGED, {
            'resonance_warning': True
        })
    
    def _start_wave(self) -> None:
        """Begin the active wave phase."""
        self._phase = ResonancePhase.ACTIVE
        self._timer = 0.0
        self._wave_position = 0.0
    
    def _update_wave_effects(self, player_moving: bool) -> None:
        """Apply wave effects based on player state."""
        if not self._time_engine or not self._debt_manager:
            return
        
        if self._time_engine.is_frozen():
            # Penalize freezing during wave
            # Only apply penalty once at wave start
            if self._timer < 0.1:
                self._debt_manager.accrue_debt(self.FROZEN_PENALTY)
                self._waves_penalized += 1
                self._event_manager.emit(GameEvent.DEBT_CHANGED, {
                    'resonance_penalty': self.FROZEN_PENALTY
                })
        elif player_moving:
            # Reward movement during wave
            # Apply bonus gradually over wave duration
            bonus_per_frame = (self.MOVING_BONUS / self.WAVE_DURATION) * 0.016
            actual_bonus = self._debt_manager.absorb_debt(bonus_per_frame)
            self._total_bonus_earned += actual_bonus
    
    def _end_wave(self) -> None:
        """End the active wave."""
        self._phase = ResonancePhase.AFTERMATH
        self._timer = 0.0
        self._waves_survived += 1
    
    def _reset_cycle(self) -> None:
        """Reset to calm state for next wave."""
        self._phase = ResonancePhase.CALM
        self._timer = 0.0
        self._next_wave_time = self._calculate_next_wave_time()
        self._visual_intensity = 0.0
        self._wave_position = 0.0
    
    def _spawn_wave_particles(self) -> None:
        """Spawn particles for wave visual effect."""
        import random
        
        if len(self._particles) > 100:
            return
        
        # Spawn particles along wave front
        wave_x = self._wave_position * Settings.SCREEN_WIDTH
        for _ in range(3):
            self._particles.append({
                'x': wave_x + random.uniform(-20, 20),
                'y': random.uniform(0, Settings.SCREEN_HEIGHT),
                'vx': random.uniform(-50, 50),
                'vy': random.uniform(-100, -50),
                'life': 1.0,
                'size': random.uniform(3, 8)
            })
    
    def _update_particles(self, dt: float) -> None:
        """Update particle positions and lifetimes."""
        for particle in self._particles[:]:
            particle['x'] += particle['vx'] * dt
            particle['y'] += particle['vy'] * dt
            particle['life'] -= dt * 2
            
            if particle['life'] <= 0:
                self._particles.remove(particle)
    
    def render(self, screen: pygame.Surface) -> None:
        """Render resonance visual effects."""
        if not self.enabled:
            return
        
        if self._phase == ResonancePhase.WARNING:
            self._render_warning(screen)
        elif self._phase == ResonancePhase.ACTIVE:
            self._render_wave(screen)
        
        # Render particles
        self._render_particles(screen)
        
        # Render indicator
        self._render_indicator(screen)
    
    def _render_warning(self, screen: pygame.Surface) -> None:
        """Render warning visual."""
        # Pulsing border
        alpha = int(100 * self._visual_intensity)
        pulse = (math.sin(self._timer * 8) + 1) / 2
        alpha = int(alpha * (0.5 + 0.5 * pulse))
        
        border_surf = pygame.Surface((Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        
        # Golden border pulse
        border_color = (255, 200, 50, alpha)
        pygame.draw.rect(border_surf, border_color, 
                        (0, 0, Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT), 8)
        
        screen.blit(border_surf, (0, 0))
        
        # Warning text
        try:
            font = get_font('Arial', 28, bold=True)
        except Exception:
            font = pygame.font.Font(None, 32)
        
        text = "RESONANCE INCOMING"
        text_alpha = int(255 * self._visual_intensity * (0.5 + 0.5 * pulse))
        text_surf = font.render(text, True, (255, 200, 50))
        text_surf.set_alpha(text_alpha)
        
        text_rect = text_surf.get_rect(center=(Settings.SCREEN_WIDTH // 2, 50))
        screen.blit(text_surf, text_rect)
    
    def _render_wave(self, screen: pygame.Surface) -> None:
        """Render active wave effect."""
        wave_x = int(self._wave_position * Settings.SCREEN_WIDTH)
        
        # Wave line with glow
        wave_surf = pygame.Surface((Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        
        # Multiple layers for glow effect
        for offset in range(30, 0, -5):
            alpha = int(30 * (1 - offset / 30))
            pygame.draw.line(wave_surf, (255, 200, 50, alpha),
                           (wave_x - offset, 0), (wave_x - offset, Settings.SCREEN_HEIGHT), 3)
            pygame.draw.line(wave_surf, (255, 200, 50, alpha),
                           (wave_x + offset, 0), (wave_x + offset, Settings.SCREEN_HEIGHT), 3)
        
        # Core wave line
        pygame.draw.line(wave_surf, (255, 220, 100, 200),
                        (wave_x, 0), (wave_x, Settings.SCREEN_HEIGHT), 6)
        
        screen.blit(wave_surf, (0, 0))
    
    def _render_particles(self, screen: pygame.Surface) -> None:
        """Render wave particles."""
        for particle in self._particles:
            alpha = int(255 * particle['life'])
            size = int(particle['size'] * particle['life'])
            if size < 1:
                continue
            
            particle_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(particle_surf, (255, 200, 50, alpha), (size, size), size)
            screen.blit(particle_surf, (int(particle['x']) - size, int(particle['y']) - size))
    
    def _render_indicator(self, screen: pygame.Surface) -> None:
        """Render resonance timer indicator."""
        if self._phase != ResonancePhase.CALM:
            return
        
        # Small indicator showing time until next wave
        x = Settings.SCREEN_WIDTH - 120
        y = 100
        
        try:
            font = get_font('Arial', 12)
        except Exception:
            font = pygame.font.Font(None, 14)
        
        time_left = self._next_wave_time - self._timer
        text = f"RESONANCE: {time_left:.0f}s"
        text_surf = font.render(text, True, (150, 150, 150))
        screen.blit(text_surf, (x, y))
        
        # Small progress bar
        bar_width = 100
        bar_height = 4
        progress = self._timer / self._next_wave_time
        
        pygame.draw.rect(screen, COLORS.DARK_GRAY, (x, y + 15, bar_width, bar_height))
        pygame.draw.rect(screen, (255, 200, 50), (x, y + 15, int(bar_width * progress), bar_height))
    
    def reset(self) -> None:
        """Reset the system (e.g., on level change)."""
        self._phase = ResonancePhase.CALM
        self._timer = 0.0
        self._next_wave_time = self._calculate_next_wave_time()
        self._visual_intensity = 0.0
        self._wave_position = 0.0
        self._particles.clear()
    
    def get_stats(self) -> dict:
        """Get resonance statistics."""
        return {
            'waves_survived': self._waves_survived,
            'waves_penalized': self._waves_penalized,
            'total_bonus_earned': self._total_bonus_earned
        }
