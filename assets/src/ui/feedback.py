"""
Screen Effects - Visual feedback and post-processing.

Screen effects communicate game state through visuals:
- Time freeze tint
- Debt tier overlays
- Screen shake
- Flash effects

Design Philosophy:
- Effects support gameplay understanding
- Never obscure critical information
- Intensity scales with game state
"""

import pygame
import random
import math
from typing import Tuple, Optional

from ..core.settings import Settings, COLORS
from ..core.utils import Vector2, lerp


class ScreenEffects:
    """
    Manages all screen-wide visual effects.
    
    Effects are layered and composited after main rendering.
    """
    
    def __init__(self):
        """Initialize screen effects."""
        # Screen shake
        self._shake_intensity = 0.0
        self._shake_offset = Vector2.zero()
        
        # Color tint
        self._tint_color = (0, 0, 0, 0)
        self._target_tint = (0, 0, 0, 0)
        
        # Flash effect
        self._flash_alpha = 0
        self._flash_color = COLORS.WHITE
        
        # Vignette
        self._vignette_intensity = 0.0
        
        # Time freeze overlay
        self._freeze_active = False
        self._freeze_alpha = 0
        
        # Cached surfaces
        self._vignette_surface: Optional[pygame.Surface] = None
        self._create_vignette_surface()
    
    def _create_vignette_surface(self) -> None:
        """Create the vignette overlay surface."""
        self._vignette_surface = pygame.Surface(
            (Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT),
            pygame.SRCALPHA
        )
        
        # Create radial gradient vignette
        center_x = Settings.SCREEN_WIDTH // 2
        center_y = Settings.SCREEN_HEIGHT // 2
        max_dist = math.sqrt(center_x ** 2 + center_y ** 2)
        
        for y in range(0, Settings.SCREEN_HEIGHT, 4):
            for x in range(0, Settings.SCREEN_WIDTH, 4):
                dist = math.sqrt((x - center_x) ** 2 + (y - center_y) ** 2)
                alpha = int(255 * (dist / max_dist) ** 2)
                pygame.draw.rect(self._vignette_surface, (0, 0, 0, alpha),
                               (x, y, 4, 4))
    
    def update(self, dt: float) -> None:
        """
        Update all effects.
        
        Args:
            dt: Delta time
        """
        # Decay shake
        self._shake_intensity *= Settings.SHAKE_DECAY
        if self._shake_intensity < 0.5:
            self._shake_intensity = 0
            self._shake_offset = Vector2.zero()
        else:
            self._shake_offset = Vector2(
                random.uniform(-1, 1) * self._shake_intensity,
                random.uniform(-1, 1) * self._shake_intensity
            )
        
        # Lerp tint
        self._tint_color = (
            int(lerp(self._tint_color[0], self._target_tint[0], dt * 3)),
            int(lerp(self._tint_color[1], self._target_tint[1], dt * 3)),
            int(lerp(self._tint_color[2], self._target_tint[2], dt * 3)),
            int(lerp(self._tint_color[3], self._target_tint[3], dt * 3))
        )
        
        # Decay flash
        self._flash_alpha = max(0, self._flash_alpha - int(dt * 500))
        
        # Freeze overlay
        if self._freeze_active:
            self._freeze_alpha = min(80, self._freeze_alpha + int(dt * 300))
        else:
            self._freeze_alpha = max(0, self._freeze_alpha - int(dt * 300))
    
    def trigger_shake(self, intensity: float = None) -> None:
        """
        Trigger screen shake.
        
        Args:
            intensity: Shake strength (uses default if None)
        """
        self._shake_intensity = intensity or Settings.SHAKE_INTENSITY_BASE
    
    def set_tint(self, color: Tuple[int, int, int], alpha: int = 50) -> None:
        """
        Set target screen tint color.
        
        Args:
            color: RGB color
            alpha: Tint transparency
        """
        self._target_tint = (*color, alpha)
    
    def clear_tint(self) -> None:
        """Remove screen tint."""
        self._target_tint = (0, 0, 0, 0)
    
    def flash(self, color: Tuple[int, int, int] = None, intensity: int = 200) -> None:
        """
        Trigger screen flash.
        
        Args:
            color: Flash color (white if None)
            intensity: Flash alpha
        """
        self._flash_color = color or COLORS.WHITE
        self._flash_alpha = intensity
    
    def set_freeze_active(self, active: bool) -> None:
        """Set time freeze overlay state."""
        self._freeze_active = active
    
    def set_vignette_intensity(self, intensity: float) -> None:
        """Set vignette darkness."""
        self._vignette_intensity = max(0, min(1, intensity))
    
    def set_debt_tier(self, tier: int) -> None:
        """
        Set effects based on debt tier.
        
        Args:
            tier: Current debt tier (0-5)
        """
        tint = Settings.DEBT_TIERS[tier]['tint']
        
        if tier >= 3:
            # High tiers get vignette and tint
            self.set_tint(tint, 30 + tier * 10)
            self.set_vignette_intensity(0.1 * tier)
            
            # Shake at critical levels
            if tier >= 4:
                if random.random() < 0.1:  # Occasional shake
                    self.trigger_shake(tier * 2)
        else:
            self.clear_tint()
            self.set_vignette_intensity(0)
    
    def get_shake_offset(self) -> Vector2:
        """Get current shake offset for camera."""
        return self._shake_offset
    
    def reset(self) -> None:
        """Reset all effects to initial state."""
        self._shake_intensity = 0.0
        self._shake_offset = Vector2.zero()
        self._tint_color = (0, 0, 0, 0)
        self._target_tint = (0, 0, 0, 0)
        self._flash_alpha = 0
        self._freeze_active = False
        self._freeze_alpha = 0
        self._vignette_intensity = 0.0

    def render(self, screen: pygame.Surface) -> None:
        """
        Render all effects on top of the game.
        
        Args:
            screen: Surface to render to
        """
        # Time freeze overlay
        if self._freeze_alpha > 0:
            freeze_surface = pygame.Surface(
                (Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT),
                pygame.SRCALPHA
            )
            freeze_surface.fill((*COLORS.FREEZE_TINT[:3], self._freeze_alpha))
            screen.blit(freeze_surface, (0, 0))
        
        # Debt tint
        if self._tint_color[3] > 0:
            tint_surface = pygame.Surface(
                (Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT),
                pygame.SRCALPHA
            )
            tint_surface.fill(self._tint_color)
            screen.blit(tint_surface, (0, 0))
        
        # Vignette
        if self._vignette_intensity > 0 and self._vignette_surface:
            vignette_copy = self._vignette_surface.copy()
            vignette_copy.set_alpha(int(255 * self._vignette_intensity))
            screen.blit(vignette_copy, (0, 0))
        
        # Flash
        if self._flash_alpha > 0:
            flash_surface = pygame.Surface(
                (Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT),
                pygame.SRCALPHA
            )
            flash_surface.fill((*self._flash_color, self._flash_alpha))
            screen.blit(flash_surface, (0, 0))


class ParticleSystem:
    """
    Simple particle system for visual effects.
    
    Used for:
    - Time freeze dust
    - Debt absorption sparkles
    - Death effects
    """
    
    def __init__(self, max_particles: int = 100):
        """Initialize particle system."""
        self.max_particles = max_particles
        self.particles: list = []
    
    def emit(self, position: Vector2, count: int = 10,
             color: Tuple[int, int, int] = COLORS.WHITE,
             speed: float = 50, lifetime: float = 1.0,
             size: int = 4) -> None:
        """
        Emit particles at a position.
        
        Args:
            position: Emission center
            count: Number of particles
            color: Particle color
            speed: Initial velocity magnitude
            lifetime: How long particles live
            size: Particle size
        """
        for _ in range(count):
            if len(self.particles) >= self.max_particles:
                break
            
            angle = random.uniform(0, math.pi * 2)
            velocity = Vector2.from_angle(angle, random.uniform(speed * 0.5, speed))
            
            self.particles.append({
                'position': position.copy(),
                'velocity': velocity,
                'color': color,
                'lifetime': lifetime,
                'max_lifetime': lifetime,
                'size': size
            })
    
    def update(self, dt: float) -> None:
        """Update all particles."""
        for particle in self.particles[:]:
            particle['lifetime'] -= dt
            if particle['lifetime'] <= 0:
                self.particles.remove(particle)
                continue
            
            # Move particle
            particle['position'] = (particle['position'] + 
                                   particle['velocity'] * dt)
            
            # Apply friction
            particle['velocity'] = particle['velocity'] * 0.98
    
    def render(self, screen: pygame.Surface) -> None:
        """Render all particles."""
        for particle in self.particles:
            alpha = int(255 * (particle['lifetime'] / particle['max_lifetime']))
            size = particle['size']
            
            # Draw particle
            pos = particle['position'].int_tuple
            color = particle['color']
            
            # Create surface with alpha
            surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*color, alpha), (size, size), size)
            screen.blit(surf, (pos[0] - size, pos[1] - size))
    
    def clear(self) -> None:
        """Remove all particles."""
        self.particles.clear()
