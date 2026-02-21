"""
Temporal Momentum System - Rewards restraint in time freezing.

The longer the player avoids freezing time, the more "momentum" they build.
This momentum reduces debt accrual rates when they do freeze, creating
a risk-reward system that encourages skillful, minimal freezing.

Design Philosophy:
- Reward players who use time freeze sparingly
- Create a visible incentive to improve play
- Momentum decays slowly but builds quickly with skill
- Maximum momentum provides significant debt reduction
"""

from typing import TYPE_CHECKING
import pygame
import math

from ..core.settings import Settings, COLORS
from ..core.events import EventManager, GameEvent, get_event_manager
from ..core.utils import Vector2, lerp, get_font

if TYPE_CHECKING:
    from ..systems.debt_manager import DebtManager


class MomentumSystem:
    """
    Manages temporal momentum - a reward system for not using time freeze.
    
    Features:
    - Momentum builds while not freezing (1 point per second)
    - Maximum momentum: 10 points
    - Each point reduces debt accrual by 5% (max 50% reduction)
    - Momentum drains slowly during freeze (2 points per second)
    - Visual meter shows current momentum level
    """
    
    # Configuration
    MAX_MOMENTUM = 10.0
    BUILD_RATE = 1.0  # Points per second while not frozen
    DRAIN_RATE = 2.0  # Points per second during freeze
    DEBT_REDUCTION_PER_POINT = 0.05  # 5% reduction per point
    MAX_DEBT_REDUCTION = 0.50  # Maximum 50% reduction
    
    # Momentum milestones
    MILESTONES = {
        3: "MOMENTUM BUILDING",
        6: "STRONG MOMENTUM",
        10: "PERFECT MOMENTUM"
    }
    
    def __init__(self, event_manager: EventManager = None):
        """
        Initialize the Momentum System.
        
        Args:
            event_manager: Event system for notifications
        """
        self._event_manager = event_manager or get_event_manager()
        
        # State
        self._momentum = 0.0
        self._is_frozen = False
        self._last_milestone = 0
        
        # Statistics
        self._peak_momentum = 0.0
        self._total_momentum_earned = 0.0
        self._times_max_reached = 0
        
        # Visual
        self._display_momentum = 0.0  # Smoothed for display
        self._glow_intensity = 0.0
        self._pulse_timer = 0.0
        
        # Subscribe to events
        self._subscribe_to_events()
    
    def _subscribe_to_events(self) -> None:
        """Subscribe to relevant game events."""
        self._event_manager.subscribe(GameEvent.TIME_FROZEN, self._on_time_frozen)
        self._event_manager.subscribe(GameEvent.TIME_UNFROZEN, self._on_time_unfrozen)
    
    def _on_time_frozen(self, _event_data) -> None:
        """Handle time freeze start."""
        self._is_frozen = True
    
    def _on_time_unfrozen(self, _event_data) -> None:
        """Handle time unfreeze."""
        self._is_frozen = False
    
    @property
    def momentum(self) -> float:
        """Current momentum value (0 to MAX_MOMENTUM)."""
        return self._momentum
    
    @property
    def momentum_percentage(self) -> float:
        """Current momentum as percentage (0.0 to 1.0)."""
        return self._momentum / self.MAX_MOMENTUM
    
    @property
    def debt_reduction_multiplier(self) -> float:
        """
        Get the debt reduction multiplier based on current momentum.
        
        Returns:
            Value between 1.0 (no reduction) and 0.5 (50% reduction)
        """
        reduction = min(
            self._momentum * self.DEBT_REDUCTION_PER_POINT,
            self.MAX_DEBT_REDUCTION
        )
        return 1.0 - reduction
    
    def update(self, dt: float) -> None:
        """
        Update momentum based on freeze state.
        
        Args:
            dt: Delta time in seconds
        """
        old_momentum = self._momentum
        
        if self._is_frozen:
            # Drain momentum during freeze
            self._momentum = max(0, self._momentum - self.DRAIN_RATE * dt)
        else:
            # Build momentum while not frozen
            self._momentum = min(self.MAX_MOMENTUM, self._momentum + self.BUILD_RATE * dt)
        
        # Track statistics
        if self._momentum > self._peak_momentum:
            self._peak_momentum = self._momentum
        
        if old_momentum < self._momentum:
            self._total_momentum_earned += (self._momentum - old_momentum)
        
        # Check for max momentum achievement
        if self._momentum >= self.MAX_MOMENTUM and old_momentum < self.MAX_MOMENTUM:
            self._times_max_reached += 1
            self._event_manager.emit(GameEvent.DEBT_CHANGED, {
                'momentum_max_reached': True
            })
        
        # Check milestones
        self._check_milestones()
        
        # Update visual smoothing
        self._display_momentum = lerp(self._display_momentum, self._momentum, dt * 8)
        self._pulse_timer += dt * 3
        
        # Update glow based on momentum level
        target_glow = self._momentum / self.MAX_MOMENTUM
        self._glow_intensity = lerp(self._glow_intensity, target_glow, dt * 4)
    
    def _check_milestones(self) -> None:
        """Check and announce milestone achievements."""
        current_milestone = 0
        for threshold in self.MILESTONES.keys():
            if self._momentum >= threshold:
                current_milestone = threshold
        
        if current_milestone > self._last_milestone:
            self._last_milestone = current_milestone
            # Could emit milestone event for UI feedback
    
    def get_milestone_name(self) -> str:
        """Get the name of current milestone, or empty string."""
        for threshold in sorted(self.MILESTONES.keys(), reverse=True):
            if self._momentum >= threshold:
                return self.MILESTONES[threshold]
        return ""
    
    def reset(self) -> None:
        """Reset momentum to zero (e.g., on death)."""
        self._momentum = 0.0
        self._last_milestone = 0
        self._display_momentum = 0.0
        self._glow_intensity = 0.0
    
    def render(self, screen: pygame.Surface, x: int, y: int) -> None:
        """
        Render the momentum meter.
        
        Args:
            screen: Surface to render to
            x: X position for meter
            y: Y position for meter
        """
        # Dimensions
        width = 200
        height = 16
        
        # Background
        bg_rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(screen, COLORS.DARK_GRAY, bg_rect)
        
        # Fill based on momentum
        fill_width = int(width * self.momentum_percentage)
        if fill_width > 0:
            # Color shifts from cyan to gold as momentum builds
            r = int(lerp(100, 255, self.momentum_percentage))
            g = int(lerp(200, 215, self.momentum_percentage))
            b = int(lerp(255, 0, self.momentum_percentage))
            fill_color = (r, g, b)
            
            fill_rect = pygame.Rect(x, y, fill_width, height)
            pygame.draw.rect(screen, fill_color, fill_rect)
            
            # Glow effect at high momentum
            if self._glow_intensity > 0.5:
                pulse = (math.sin(self._pulse_timer) + 1) / 2
                glow_alpha = int(50 * self._glow_intensity * pulse)
                glow_surf = pygame.Surface((fill_width + 10, height + 10), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (*fill_color, glow_alpha), 
                               (5, 5, fill_width, height))
                screen.blit(glow_surf, (x - 5, y - 5))
        
        # Border
        pygame.draw.rect(screen, COLORS.WHITE, bg_rect, 1)
        
        # Labels
        try:
            font = get_font('Arial', 12)
        except Exception:
            font = pygame.font.Font(None, 14)
        
        # Momentum text
        momentum_text = f"MOMENTUM: {self._display_momentum:.1f}"
        text_surf = font.render(momentum_text, True, COLORS.WHITE)
        screen.blit(text_surf, (x, y - 15))
        
        # Reduction indicator
        reduction = (1 - self.debt_reduction_multiplier) * 100
        if reduction > 0:
            reduction_text = f"-{reduction:.0f}% DEBT"
            reduction_color = (100, 255, 150)
            reduction_surf = font.render(reduction_text, True, reduction_color)
            screen.blit(reduction_surf, (x + width + 5, y))
        
        # Milestone name
        milestone = self.get_milestone_name()
        if milestone:
            milestone_surf = font.render(milestone, True, (255, 215, 0))
            screen.blit(milestone_surf, (x + width // 2 - milestone_surf.get_width() // 2, 
                                        y + height + 2))
    
    def get_stats(self) -> dict:
        """Get momentum statistics for end-of-level display."""
        return {
            'peak_momentum': self._peak_momentum,
            'total_earned': self._total_momentum_earned,
            'times_max_reached': self._times_max_reached,
            'current': self._momentum
        }
