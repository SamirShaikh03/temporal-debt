"""
Advanced Interactables - New interactive objects for Temporal Debt 2.0

This module adds new interactable objects that enhance gameplay:
- Time Dilation Zones: Areas that modify debt accrual rates
- Temporal Fragments: Collectibles for debt relief
- Debt Transfer Pods: Store and release debt strategically

Design Philosophy:
- Each object creates unique strategic opportunities
- Clear visual feedback for all states
- Integrate seamlessly with existing mechanics
"""

from typing import Optional, List, TYPE_CHECKING
from dataclasses import dataclass
import pygame
import math

from .base_entity import BaseEntity
from ..core.settings import Settings, COLORS
from ..core.utils import Vector2
from ..core.events import GameEvent, get_event_manager
from ..systems.collision import CollisionLayer

if TYPE_CHECKING:
    from ..systems.debt_manager import DebtManager
    from ..entities.player import Player


class TimeDilationZone(BaseEntity):
    """
    An area that modifies debt accrual rates.
    
    Types:
    - 'safe': Blue zone, debt accrues at 0.75x rate
    - 'danger': Red zone, debt accrues at 2x rate (often contains shortcuts/rewards)
    
    Creates strategic routing decisions for players.
    """
    
    ZONE_TYPES = {
        'safe': {
            'multiplier': 0.75,
            'color': (50, 100, 200),
            'name': 'SAFE ZONE'
        },
        'danger': {
            'multiplier': 2.0,
            'color': (200, 50, 50),
            'name': 'DANGER ZONE'
        }
    }
    
    def __init__(self, position: Vector2, zone_type: str = 'safe',
                 width: int = 128, height: int = 128):
        """
        Initialize a dilation zone.
        
        Args:
            position: Position of zone
            zone_type: 'safe' or 'danger'
            width: Zone width in pixels
            height: Zone height in pixels
        """
        super().__init__(position, (width, height))
        
        self.zone_type = zone_type
        self._config = self.ZONE_TYPES.get(zone_type, self.ZONE_TYPES['safe'])
        
        # Visual state
        self._pulse_timer = 0.0
        self._active = False  # Whether player is inside
        
        # Collision
        self.collision_layer = CollisionLayer.TRIGGER
    
    @property
    def debt_multiplier(self) -> float:
        """Get the debt accrual multiplier for this zone."""
        return self._config['multiplier']
    
    def check_player_inside(self, player_rect: pygame.Rect) -> bool:
        """
        Check if player is inside this zone.
        
        Args:
            player_rect: Player's collision rect
            
        Returns:
            True if player is inside zone
        """
        self._active = self.get_rect().colliderect(player_rect)
        return self._active
    
    def update(self, dt: float) -> None:
        """Update zone visual state."""
        self._pulse_timer += dt * (3 if self._active else 1)
    
    def render(self, screen: pygame.Surface) -> None:
        """Render the dilation zone."""
        if not self.visible:
            return
        
        rect = self.get_rect()
        color = self._config['color']
        
        # Pulsing effect
        pulse = (math.sin(self._pulse_timer) + 1) / 2
        alpha = int(40 + 30 * pulse) if self._active else int(25 + 15 * pulse)
        
        # Create zone surface with alpha
        zone_surf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        zone_color = (*color, alpha)
        pygame.draw.rect(zone_surf, zone_color, (0, 0, rect.width, rect.height))
        
        # Border
        border_alpha = int(100 + 50 * pulse) if self._active else 60
        pygame.draw.rect(zone_surf, (*color, border_alpha), 
                        (0, 0, rect.width, rect.height), 3)
        
        # Draw zone
        screen.blit(zone_surf, rect.topleft)
        
        # Zone type indicator (small text)
        if self._active:
            from ..core.utils import get_font
            try:
                font = get_font('Arial', 14, bold=True)
                text = self._config['name']
                text_surf = font.render(text, True, color)
                text_rect = text_surf.get_rect(center=(rect.centerx, rect.top - 10))
                screen.blit(text_surf, text_rect)
            except Exception:
                pass


class TemporalFragment(BaseEntity):
    """
    A collectible that provides debt relief and can be charged for slow-motion.
    
    When collected:
    - Instantly reduces debt by 1.5 seconds
    - Adds to fragment counter (100% = slow-motion burst)
    
    Creates exploration incentive and secondary objectives.
    """
    
    DEBT_REDUCTION = 1.5  # Seconds of debt removed
    FRAGMENT_VALUE = 0.20  # Each fragment adds 20% toward slow-motion
    
    def __init__(self, position: Vector2, fragment_id: int = 0):
        """
        Initialize a temporal fragment.
        
        Args:
            position: Fragment position
            fragment_id: Unique ID for tracking collection
        """
        super().__init__(position, (24, 24))
        
        self.fragment_id = fragment_id
        self.collected = False
        
        # Visual state
        self._glow_timer = 0.0
        self._bob_offset = 0.0
        self._rotation = 0.0
        
        # Collision
        self.collision_layer = CollisionLayer.TRIGGER
    
    def collect(self, debt_manager: 'DebtManager' = None) -> dict:
        """
        Collect this fragment.
        
        Args:
            debt_manager: Reference to apply debt reduction
            
        Returns:
            Dict with collection results
        """
        if self.collected:
            return {'success': False}
        
        self.collected = True
        self.visible = False
        
        # Apply debt reduction
        actual_reduction = 0.0
        if debt_manager:
            actual_reduction = debt_manager.absorb_debt(self.DEBT_REDUCTION)
        
        return {
            'success': True,
            'debt_reduced': actual_reduction,
            'fragment_value': self.FRAGMENT_VALUE,
            'fragment_id': self.fragment_id
        }
    
    def update(self, dt: float) -> None:
        """Update fragment animation."""
        if self.collected:
            return
        
        self._glow_timer += dt * 4
        self._bob_offset = math.sin(self._glow_timer * 0.5) * 5
        self._rotation += dt * 90  # Degrees per second
    
    def render(self, screen: pygame.Surface) -> None:
        """Render the temporal fragment."""
        if not self.visible or self.collected:
            return
        
        center = self.center
        render_y = center.y + self._bob_offset
        
        # Glow effect
        pulse = (math.sin(self._glow_timer) + 1) / 2
        glow_size = int(20 + 8 * pulse)
        glow_alpha = int(60 + 40 * pulse)
        
        glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (200, 220, 255, glow_alpha), 
                          (glow_size, glow_size), glow_size)
        screen.blit(glow_surf, (center.x - glow_size, render_y - glow_size))
        
        # Core fragment (diamond shape)
        fragment_size = 12
        points = [
            (center.x, render_y - fragment_size),
            (center.x + fragment_size, render_y),
            (center.x, render_y + fragment_size),
            (center.x - fragment_size, render_y)
        ]
        
        # Rotate points
        angle_rad = math.radians(self._rotation)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        rotated_points = []
        for px, py in points:
            dx = px - center.x
            dy = py - render_y
            new_x = center.x + dx * cos_a - dy * sin_a
            new_y = render_y + dx * sin_a + dy * cos_a
            rotated_points.append((new_x, new_y))
        
        # Draw fragment
        pygame.draw.polygon(screen, (200, 220, 255), rotated_points)
        pygame.draw.polygon(screen, (255, 255, 255), rotated_points, 2)


class DebtTransferPod(BaseEntity):
    """
    A container that can store and release debt.
    
    Mechanics:
    - Walk into pod while holding interaction key to deposit debt
    - Pod stores up to 5 seconds of debt
    - Interact again to release as area effect
    - Released debt affects nearby enemies (slows them) or opens special doors
    
    Creates puzzle opportunities and risk/reward decisions.
    """
    
    MAX_STORED_DEBT = 5.0
    DEPOSIT_RATE = 2.0  # Debt per second when depositing
    RELEASE_RADIUS = 150.0
    RELEASE_EFFECT_DURATION = 3.0
    
    def __init__(self, position: Vector2, pod_id: int = 0):
        """
        Initialize a debt transfer pod.
        
        Args:
            position: Pod position
            pod_id: Unique identifier
        """
        super().__init__(position, (48, 48))
        
        self.pod_id = pod_id
        self.stored_debt = 0.0
        
        # State
        self._is_depositing = False
        self._is_releasing = False
        self._release_timer = 0.0
        self._release_progress = 0.0
        
        # Visual
        self._pulse_timer = 0.0
        self._glow_intensity = 0.0
        
        # Collision
        self.collision_layer = CollisionLayer.INTERACTABLE
    
    @property
    def is_charged(self) -> bool:
        """Whether pod has stored debt."""
        return self.stored_debt > 0.5
    
    @property
    def is_full(self) -> bool:
        """Whether pod is at maximum capacity."""
        return self.stored_debt >= self.MAX_STORED_DEBT
    
    @property
    def charge_percentage(self) -> float:
        """Current charge as percentage."""
        return self.stored_debt / self.MAX_STORED_DEBT
    
    def deposit_debt(self, debt_manager: 'DebtManager', dt: float) -> float:
        """
        Deposit player debt into the pod.
        
        Args:
            debt_manager: Source of debt
            dt: Delta time
            
        Returns:
            Amount of debt actually deposited
        """
        if self.is_full or self._is_releasing:
            return 0.0
        
        self._is_depositing = True
        
        # Calculate how much to deposit
        space_remaining = self.MAX_STORED_DEBT - self.stored_debt
        amount_to_deposit = min(self.DEPOSIT_RATE * dt, space_remaining)
        
        # Actually transfer debt
        actual_deposit = debt_manager.absorb_debt(amount_to_deposit)
        self.stored_debt += actual_deposit
        
        return actual_deposit
    
    def stop_deposit(self) -> None:
        """Stop depositing debt."""
        self._is_depositing = False
    
    def release_debt(self) -> bool:
        """
        Release stored debt as area effect.
        
        Returns:
            True if release initiated
        """
        if not self.is_charged or self._is_releasing:
            return False
        
        self._is_releasing = True
        self._release_timer = 0.0
        self._release_progress = 0.0
        
        return True
    
    def get_release_effect_area(self) -> Optional[pygame.Rect]:
        """Get the area affected by release, if releasing."""
        if not self._is_releasing:
            return None
        
        radius = int(self.RELEASE_RADIUS * self._release_progress)
        center = self.center
        return pygame.Rect(
            center.x - radius,
            center.y - radius,
            radius * 2,
            radius * 2
        )
    
    def get_effect_strength(self) -> float:
        """Get current effect strength (0.0 to 1.0)."""
        if not self._is_releasing:
            return 0.0
        return (self.stored_debt / self.MAX_STORED_DEBT) * (1.0 - self._release_progress)
    
    def update(self, dt: float) -> None:
        """Update pod state."""
        self._pulse_timer += dt * 3
        
        # Update glow based on stored debt
        target_glow = self.stored_debt / self.MAX_STORED_DEBT
        from ..core.utils import lerp
        self._glow_intensity = lerp(self._glow_intensity, target_glow, dt * 3)
        
        # Update release effect
        if self._is_releasing:
            self._release_timer += dt
            self._release_progress = self._release_timer / self.RELEASE_EFFECT_DURATION
            
            if self._release_progress >= 1.0:
                self._is_releasing = False
                self.stored_debt = 0.0
                self._release_progress = 0.0
        
        if not self._is_depositing and not self._is_releasing:
            self._is_depositing = False
    
    def render(self, screen: pygame.Surface) -> None:
        """Render the debt transfer pod."""
        if not self.visible:
            return
        
        rect = self.get_rect()
        center = self.center
        
        # Base pod shape
        if self._is_releasing:
            base_color = (255, 100, 50)  # Orange when releasing
        elif self._is_depositing:
            base_color = (100, 200, 100)  # Green when depositing
        else:
            base_color = (100, 150, 200)  # Blue normally
        
        # Draw pod base
        pygame.draw.rect(screen, base_color, rect)
        pygame.draw.rect(screen, COLORS.WHITE, rect, 2)
        
        # Charge indicator (fill level)
        if self.stored_debt > 0:
            fill_height = int(rect.height * self.charge_percentage)
            fill_rect = pygame.Rect(
                rect.x + 4,
                rect.bottom - fill_height - 4,
                rect.width - 8,
                fill_height
            )
            fill_color = (255, 200, 100)
            pygame.draw.rect(screen, fill_color, fill_rect)
        
        # Glow effect when charged
        if self._glow_intensity > 0.1:
            pulse = (math.sin(self._pulse_timer) + 1) / 2
            glow_size = int(30 * self._glow_intensity * (0.8 + 0.2 * pulse))
            glow_alpha = int(50 * self._glow_intensity)
            
            glow_surf = pygame.Surface((glow_size * 2, glow_size * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255, 200, 100, glow_alpha),
                             (glow_size, glow_size), glow_size)
            screen.blit(glow_surf, (center.x - glow_size, center.y - glow_size))
        
        # Release effect
        if self._is_releasing:
            self._render_release_effect(screen)
        
        # Label
        from ..core.utils import get_font
        try:
            font = get_font('Arial', 10)
            if self.is_full:
                text = "FULL"
            elif self.stored_debt > 0:
                text = f"{self.stored_debt:.1f}s"
            else:
                text = "EMPTY"
            text_surf = font.render(text, True, COLORS.WHITE)
            text_rect = text_surf.get_rect(center=(center.x, rect.bottom + 10))
            screen.blit(text_surf, text_rect)
        except Exception:
            pass
    
    def _render_release_effect(self, screen: pygame.Surface) -> None:
        """Render the release wave effect."""
        center = self.center
        max_radius = int(self.RELEASE_RADIUS * self._release_progress)
        
        # Multiple rings expanding outward
        for i in range(3):
            ring_progress = (self._release_progress - i * 0.1)
            if ring_progress <= 0:
                continue
            
            radius = int(self.RELEASE_RADIUS * ring_progress)
            alpha = int(100 * (1 - ring_progress) * (1 - i * 0.3))
            
            if alpha > 0 and radius > 0:
                ring_surf = pygame.Surface((radius * 2 + 10, radius * 2 + 10), pygame.SRCALPHA)
                pygame.draw.circle(ring_surf, (255, 150, 50, alpha),
                                 (radius + 5, radius + 5), radius, 4)
                screen.blit(ring_surf, (center.x - radius - 5, center.y - radius - 5))


class FragmentManager:
    """
    Manages temporal fragments and slow-motion burst ability.
    
    Tracks collected fragments and enables slow-motion burst
    when enough fragments are collected.
    """
    
    FRAGMENTS_FOR_BURST = 5  # Fragments needed for slow-motion
    BURST_DURATION = 2.0  # Seconds of slow-motion
    BURST_TIME_SCALE = 0.3  # World speed during burst
    
    def __init__(self):
        """Initialize the fragment manager."""
        self._collected_fragments: List[int] = []
        self._fragment_energy = 0.0  # 0.0 to 1.0
        
        # Slow-motion state
        self._burst_active = False
        self._burst_timer = 0.0
        
        # Statistics
        self._total_collected = 0
        self._bursts_used = 0
    
    @property
    def can_burst(self) -> bool:
        """Whether slow-motion burst is available."""
        return self._fragment_energy >= 1.0 and not self._burst_active
    
    @property
    def is_burst_active(self) -> bool:
        """Whether slow-motion burst is currently active."""
        return self._burst_active
    
    @property
    def is_burst_ready(self) -> bool:
        """Alias for can_burst for HUD compatibility."""
        return self.can_burst
    
    @property
    def burst_time_scale(self) -> float:
        """Get the time scale during burst, or 1.0 if not active."""
        return self.BURST_TIME_SCALE if self._burst_active else 1.0
    
    @property
    def energy_percentage(self) -> float:
        """Current energy as percentage."""
        return self._fragment_energy
    
    @property
    def fragments_collected(self) -> int:
        """Number of fragments collected."""
        return len(self._collected_fragments)
    
    @property
    def fragment_energy(self) -> float:
        """Current fragment energy (0.0 to 1.0)."""
        return self._fragment_energy
    
    def add_fragment(self, fragment_id: int, fragment_value: float) -> None:
        """
        Add a collected fragment.
        
        Args:
            fragment_id: ID of collected fragment
            fragment_value: Energy value of fragment
        """
        if fragment_id not in self._collected_fragments:
            self._collected_fragments.append(fragment_id)
            self._fragment_energy = min(1.0, self._fragment_energy + fragment_value)
            self._total_collected += 1
    
    def activate_burst(self) -> bool:
        """
        Activate slow-motion burst.
        
        Returns:
            True if burst was activated
        """
        if not self.can_burst:
            return False
        
        self._burst_active = True
        self._burst_timer = 0.0
        self._fragment_energy = 0.0
        self._bursts_used += 1
        
        return True
    
    def update(self, dt: float) -> None:
        """Update burst state."""
        if self._burst_active:
            self._burst_timer += dt
            if self._burst_timer >= self.BURST_DURATION:
                self._burst_active = False
    
    def render_ui(self, screen: pygame.Surface, x: int, y: int) -> None:
        """Render fragment collection UI."""
        from ..core.utils import get_font
        
        # Background bar
        bar_width = 100
        bar_height = 12
        
        pygame.draw.rect(screen, COLORS.DARK_GRAY, (x, y, bar_width, bar_height))
        
        # Fill based on energy
        fill_width = int(bar_width * self._fragment_energy)
        if fill_width > 0:
            fill_color = (200, 220, 255) if not self._burst_active else (255, 255, 200)
            pygame.draw.rect(screen, fill_color, (x, y, fill_width, bar_height))
        
        # Border
        pygame.draw.rect(screen, COLORS.WHITE, (x, y, bar_width, bar_height), 1)
        
        # Label
        try:
            font = get_font('Arial', 11)
            if self._burst_active:
                remaining = self.BURST_DURATION - self._burst_timer
                text = f"SLOW-MO: {remaining:.1f}s"
                color = (255, 255, 200)
            elif self.can_burst:
                text = "BURST READY [B]"
                color = (200, 220, 255)
            else:
                text = f"FRAGMENTS: {int(self._fragment_energy * 100)}%"
                color = COLORS.WHITE
            
            text_surf = font.render(text, True, color)
            screen.blit(text_surf, (x, y - 14))
        except Exception:
            pass
    
    def reset(self) -> None:
        """Reset fragment state (keeps collection history)."""
        self._fragment_energy = 0.0
        self._burst_active = False
        self._burst_timer = 0.0
    
    def get_stats(self) -> dict:
        """Get fragment statistics."""
        return {
            'total_collected': self._total_collected,
            'bursts_used': self._bursts_used,
            'unique_fragments': len(self._collected_fragments)
        }
