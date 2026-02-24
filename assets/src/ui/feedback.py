"""
Screen Effects - Visual feedback and post-processing.

Neon Abyss theme — chromatic aberration at high debt, scan lines,
enhanced vignette, and tighter flash decay for snappy feel.
"""

import pygame
import random
import math
from typing import Tuple, Optional

from ..core.settings import Settings, COLORS
from ..core.utils import Vector2, lerp


class ScreenEffects:
    """
    Screen-wide visual effects with Neon Abyss theming.
    """
    
    def __init__(self):
        # Shake
        self._shake_intensity = 0.0
        self._shake_offset = Vector2.zero()
        
        # Color tint
        self._tint_color = (0, 0, 0, 0)
        self._target_tint = (0, 0, 0, 0)
        
        # Flash
        self._flash_alpha = 0
        self._flash_color = (255, 255, 255)
        
        # Vignette
        self._vignette_intensity = 0.0
        
        # Freeze
        self._freeze_active = False
        self._freeze_alpha = 0
        
        # Chromatic aberration (increases with debt tier)
        self._chromatic_offset = 0.0
        self._target_chromatic = 0.0
        
        # Scan lines toggle (active at tier >= 3)
        self._scanlines_active = False
        
        # Current debt tier for effect scaling
        self._current_tier = 0
        
        # Cached surfaces
        self._vignette_surface: Optional[pygame.Surface] = None
        self._scanline_surface: Optional[pygame.Surface] = None
        self._create_vignette_surface()
        self._create_scanline_surface()
    
    def _create_vignette_surface(self) -> None:
        self._vignette_surface = pygame.Surface(
            (Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT),
            pygame.SRCALPHA
        )
        cx = Settings.SCREEN_WIDTH // 2
        cy = Settings.SCREEN_HEIGHT // 2
        max_dist = math.sqrt(cx ** 2 + cy ** 2)
        
        step = 4
        for y in range(0, Settings.SCREEN_HEIGHT, step):
            for x in range(0, Settings.SCREEN_WIDTH, step):
                dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                alpha = int(255 * (dist / max_dist) ** 2.2)
                pygame.draw.rect(self._vignette_surface, (0, 0, 0, alpha),
                                (x, y, step, step))
    
    def _create_scanline_surface(self) -> None:
        self._scanline_surface = pygame.Surface(
            (Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT),
            pygame.SRCALPHA
        )
        for y in range(0, Settings.SCREEN_HEIGHT, 3):
            pygame.draw.line(self._scanline_surface, (0, 0, 0, 18),
                           (0, y), (Settings.SCREEN_WIDTH, y))
    
    def update(self, dt: float) -> None:
        # Shake decay
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
        
        # Flash decay (faster for snappy feel)
        self._flash_alpha = max(0, self._flash_alpha - int(dt * 600))
        
        # Freeze overlay
        if self._freeze_active:
            self._freeze_alpha = min(60, self._freeze_alpha + int(dt * 350))
        else:
            self._freeze_alpha = max(0, self._freeze_alpha - int(dt * 400))
        
        # Smooth chromatic aberration
        self._chromatic_offset = lerp(self._chromatic_offset, self._target_chromatic, dt * 4)
    
    def trigger_shake(self, intensity: float = None) -> None:
        self._shake_intensity = intensity or Settings.SHAKE_INTENSITY_BASE
    
    def set_tint(self, color: Tuple[int, int, int], alpha: int = 50) -> None:
        self._target_tint = (*color, alpha)
    
    def clear_tint(self) -> None:
        self._target_tint = (0, 0, 0, 0)
    
    def flash(self, color: Tuple[int, int, int] = None, intensity: int = 200) -> None:
        self._flash_color = color or (255, 255, 255)
        self._flash_alpha = min(255, max(0, intensity))
    
    def set_freeze_active(self, active: bool) -> None:
        self._freeze_active = active
    
    def set_vignette_intensity(self, intensity: float) -> None:
        self._vignette_intensity = max(0, min(1, intensity))
    
    def set_debt_tier(self, tier: int) -> None:
        self._current_tier = tier
        tint = Settings.DEBT_TIERS[tier]['tint']
        
        if tier >= 3:
            self.set_tint(tint, 20 + tier * 12)
            self.set_vignette_intensity(0.12 * tier)
            
            # Chromatic aberration scales with tier
            max_offset = getattr(Settings, 'CHROMATIC_OFFSET_MAX', 4)
            self._target_chromatic = max_offset * ((tier - 2) / 3)
            self._scanlines_active = True
            
            if tier >= 4 and random.random() < 0.12:
                self.trigger_shake(tier * 2.5)
        else:
            self.clear_tint()
            self.set_vignette_intensity(0)
            self._target_chromatic = 0
            self._scanlines_active = False
    
    def get_shake_offset(self) -> Vector2:
        return self._shake_offset
    
    def reset(self) -> None:
        self._shake_intensity = 0.0
        self._shake_offset = Vector2.zero()
        self._tint_color = (0, 0, 0, 0)
        self._target_tint = (0, 0, 0, 0)
        self._flash_alpha = 0
        self._freeze_active = False
        self._freeze_alpha = 0
        self._vignette_intensity = 0.0
        self._chromatic_offset = 0.0
        self._target_chromatic = 0.0
        self._scanlines_active = False
        self._current_tier = 0

    def render(self, screen: pygame.Surface) -> None:
        # Chromatic aberration (shift red/blue channels at high debt)
        if self._chromatic_offset >= 0.5:
            offset = int(self._chromatic_offset)
            if offset > 0:
                w, h = screen.get_size()
                red_layer = pygame.Surface((w, h), pygame.SRCALPHA)
                blue_layer = pygame.Surface((w, h), pygame.SRCALPHA)
                
                red_layer.fill((255, 0, 0, 12))
                blue_layer.fill((0, 0, 255, 10))
                
                screen.blit(red_layer, (-offset, 0))
                screen.blit(blue_layer, (offset, 0))
        
        # Time freeze tint
        if self._freeze_alpha > 0:
            freeze_tint = getattr(COLORS, 'FREEZE_TINT', (100, 200, 255))
            freeze_surface = pygame.Surface(
                (Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT),
                pygame.SRCALPHA
            )
            ft = freeze_tint[:3]
            freeze_surface.fill((ft[0], ft[1], ft[2], min(255, max(0, self._freeze_alpha))))
            screen.blit(freeze_surface, (0, 0))
        
        # Debt tint
        if self._tint_color[3] > 0:
            tint_surface = pygame.Surface(
                (Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT),
                pygame.SRCALPHA
            )
            tint_surface.fill(self._tint_color)
            screen.blit(tint_surface, (0, 0))
        
        # Scan lines (at high tier)
        if self._scanlines_active and self._scanline_surface:
            screen.blit(self._scanline_surface, (0, 0))
        
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
            fc = self._flash_color
            flash_surface.fill((fc[0], fc[1], fc[2], min(255, max(0, self._flash_alpha))))
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
            pygame.draw.circle(surf, (color[0], color[1], color[2], min(255, max(0, alpha))), (size, size), size)
            screen.blit(surf, (pos[0] - size, pos[1] - size))
    
    def clear(self) -> None:
        """Remove all particles."""
        self.particles.clear()
