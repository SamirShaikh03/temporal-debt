"""
Menu Screens - Main menu, pause, game over, and victory screens.

Menus provide navigation and state transitions outside gameplay.

Design Philosophy:
- Clean, readable interfaces
- Clear visual hierarchy
- Consistent styling with immersive effects
"""

import pygame
import math
import random
from typing import Optional, Callable, List
from enum import Enum, auto

from ..core.settings import Settings, COLORS


class MenuState(Enum):
    """Current menu selection state."""
    NONE = auto()
    MAIN_MENU = auto()
    PAUSE = auto()
    GAME_OVER = auto()
    VICTORY = auto()


class Particle:
    """Simple particle for menu background effects."""
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.vx = random.uniform(-20, 20)
        self.vy = random.uniform(-30, -10)
        self.size = random.uniform(2, 5)
        self.alpha = random.randint(50, 150)
        self.lifetime = random.uniform(2, 5)
        self.age = 0
    
    def update(self, dt: float) -> bool:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.age += dt
        self.alpha = int(150 * (1 - self.age / self.lifetime))
        return self.age < self.lifetime
    
    def render(self, screen: pygame.Surface, color: tuple):
        if self.alpha > 0:
            surf = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*color[:3], self.alpha), 
                             (int(self.size), int(self.size)), int(self.size))
            screen.blit(surf, (int(self.x - self.size), int(self.y - self.size)))


class MenuItem:
    """A single menu item/button with hover effects."""
    
    def __init__(self, text: str, action: Callable, y_position: int):
        self.text = text
        self.action = action
        self.y = y_position
        self.selected = False
        
        # Visual properties with better dimensions
        self.width = 340
        self.height = 60
        self.x = (Settings.SCREEN_WIDTH - self.width) // 2
        
        # Animation
        self._hover_anim = 0.0
        self._glow_phase = random.uniform(0, math.pi * 2)
    
    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def update(self, dt: float):
        if self.selected:
            self._hover_anim = min(1.0, self._hover_anim + dt * 5)
        else:
            self._hover_anim = max(0.0, self._hover_anim - dt * 5)
        self._glow_phase += dt * 2
    
    def render(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        rect = self.get_rect()
        
        # Calculate glow
        glow = (math.sin(self._glow_phase) + 1) / 2
        
        # Background with animation
        if self.selected:
            # Animated gradient effect
            base_color = (
                int(60 + 40 * glow),
                int(100 + 50 * glow),
                int(180 + 40 * glow)
            )
            pygame.draw.rect(screen, base_color, rect, border_radius=8)
            
            # Glow border
            glow_rect = rect.inflate(4 + int(4 * glow), 4 + int(4 * glow))
            pygame.draw.rect(screen, (100, 180, 255, 100), glow_rect, 
                           width=2, border_radius=10)
            text_color = COLORS.WHITE
        else:
            # Normal state
            pygame.draw.rect(screen, (40, 45, 55), rect, border_radius=8)
            pygame.draw.rect(screen, (60, 65, 75), rect, width=2, border_radius=8)
            text_color = (180, 185, 195)
        
        # Border
        pygame.draw.rect(screen, (100, 105, 115) if not self.selected else (150, 200, 255),
                        rect, width=2, border_radius=8)
        
        # Text with subtle shadow
        if self.selected:
            shadow = font.render(self.text, True, (20, 30, 50))
            screen.blit(shadow, (rect.centerx - shadow.get_width() // 2 + 2, 
                                rect.centery - shadow.get_height() // 2 + 2))
        
        text_surface = font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=rect.center)
        screen.blit(text_surface, text_rect)


class BaseMenu:
    """Base class for all menu screens."""
    
    def __init__(self):
        pygame.font.init()
        self.font_title = pygame.font.SysFont('Segoe UI', 72, bold=True)
        self.font_large = pygame.font.SysFont('Segoe UI', 32)
        self.font_medium = pygame.font.SysFont('Segoe UI', 26)
        self.font_small = pygame.font.SysFont('Segoe UI', 20)
        
        self.items: List[MenuItem] = []
        self.selected_index = 0
        
        # Background particles
        self.particles: List[Particle] = []
        self._particle_timer = 0
    
    def update(self, dt: float):
        # Update particles
        self._particle_timer += dt
        if self._particle_timer > 0.1:
            self._particle_timer = 0
            self.particles.append(Particle(
                random.uniform(0, Settings.SCREEN_WIDTH),
                Settings.SCREEN_HEIGHT + 10
            ))
        
        self.particles = [p for p in self.particles if p.update(dt)]
        
        # Update menu items
        for item in self.items:
            item.update(dt)
    
    def handle_input(self, event: pygame.event.Event) -> Optional[str]:
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self._move_selection(-1)
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self._move_selection(1)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self._activate_selection()
        
        elif event.type == pygame.MOUSEMOTION:
            self._handle_mouse_hover(event.pos)
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                return self._handle_mouse_click(event.pos)
        
        return None
    
    def _move_selection(self, direction: int) -> None:
        if not self.items:
            return
        self.items[self.selected_index].selected = False
        self.selected_index = (self.selected_index + direction) % len(self.items)
        self.items[self.selected_index].selected = True
    
    def _activate_selection(self) -> Optional[str]:
        if self.items and 0 <= self.selected_index < len(self.items):
            item = self.items[self.selected_index]
            if item.action:
                return item.action()
        return None
    
    def _handle_mouse_hover(self, pos: tuple) -> None:
        for i, item in enumerate(self.items):
            if item.get_rect().collidepoint(pos):
                self.items[self.selected_index].selected = False
                self.selected_index = i
                item.selected = True
                break
    
    def _handle_mouse_click(self, pos: tuple) -> Optional[str]:
        for item in self.items:
            if item.get_rect().collidepoint(pos) and item.action:
                return item.action()
        return None
    
    def _render_background(self, screen: pygame.Surface, color: tuple = (15, 18, 28)):
        screen.fill(color)
        
        # Render grid pattern
        grid_color = (25, 28, 38)
        for x in range(0, Settings.SCREEN_WIDTH, 64):
            pygame.draw.line(screen, grid_color, (x, 0), (x, Settings.SCREEN_HEIGHT))
        for y in range(0, Settings.SCREEN_HEIGHT, 64):
            pygame.draw.line(screen, grid_color, (0, y), (Settings.SCREEN_WIDTH, y))
        
        # Render particles
        for p in self.particles:
            p.render(screen, (80, 120, 200))
    
    def render(self, screen: pygame.Surface) -> None:
        pass


class MainMenu(BaseMenu):
    """Main menu screen with immersive visuals."""
    
    def __init__(self):
        super().__init__()
        
        start_y = 390
        spacing = 80  # Better vertical spacing between items
        
        self.items = [
            MenuItem("START GAME", lambda: "start", start_y),
            MenuItem("CONTROLS", lambda: "controls", start_y + spacing),
            MenuItem("QUIT", lambda: "quit", start_y + spacing * 2),
        ]
        self.items[0].selected = True
        
        # Animation state
        self._title_time = 0.0
        self._subtitle_alpha = 0
        
    def update(self, dt: float) -> None:
        super().update(dt)
        self._title_time += dt
        self._subtitle_alpha = min(255, self._subtitle_alpha + int(dt * 200))
    
    def render(self, screen: pygame.Surface) -> None:
        self._render_background(screen)
        
        # Animated title
        time = self._title_time
        
        # Title glow effect
        glow = (math.sin(time * 2) + 1) / 2
        title_color = (
            int(80 + 100 * glow),
            int(150 + 80 * glow),
            255
        )
        
        # Render title with layered glow
        title_text = "TEMPORAL DEBT"
        
        # Glow layers
        for i in range(3, 0, -1):
            glow_surface = self.font_title.render(title_text, True, 
                                                  (40, 80, 150, 50 // i))
            glow_rect = glow_surface.get_rect(centerx=Settings.SCREEN_WIDTH // 2 + i, 
                                             top=90 + i)
            screen.blit(glow_surface, glow_rect)
        
        # Main title with better positioning
        title_surface = self.font_title.render(title_text, True, title_color)
        title_rect = title_surface.get_rect(centerx=Settings.SCREEN_WIDTH // 2, top=80)
        screen.blit(title_surface, title_rect)
        
        # Subtitle with improved spacing
        subtitle = "Time is a loan you cannot afford."
        if self._subtitle_alpha > 0:
            sub_surface = self.font_medium.render(subtitle, True, 
                                                  (150, 155, 170, self._subtitle_alpha))
            sub_rect = sub_surface.get_rect(centerx=Settings.SCREEN_WIDTH // 2, top=170)
            screen.blit(sub_surface, sub_rect)
        
        # Decorative line with better margin
        line_y = 215
        line_width = 420  # Slightly wider for better balance
        pygame.draw.line(screen, (60, 100, 180), 
                        (Settings.SCREEN_WIDTH // 2 - line_width // 2, line_y),
                        (Settings.SCREEN_WIDTH // 2 + line_width // 2, line_y), 2)
        
        # Feature highlights with improved spacing
        features = [
            "FREEZE TIME - But every second borrowed accrues debt",
            "DEBT TIERS - Higher debt = faster, more dangerous world",
            "TIME ANCHORS - Place checkpoints, recall at a cost"
        ]
        
        feature_spacing = 32  # Better line spacing for readability
        for i, feature in enumerate(features):
            color = (100, 120, 150) if i % 2 == 0 else (90, 110, 140)
            feat_surface = self.font_small.render(feature, True, color)
            feat_rect = feat_surface.get_rect(centerx=Settings.SCREEN_WIDTH // 2, 
                                             top=250 + i * feature_spacing)
            screen.blit(feat_surface, feat_rect)
        
        # Menu items
        for item in self.items:
            item.render(screen, self.font_large)
        
        # Controls hint
        hint = "Use WASD to navigate, ENTER to select"
        hint_surface = self.font_small.render(hint, True, (80, 85, 95))
        screen.blit(hint_surface, (20, Settings.SCREEN_HEIGHT - 30))
        
        # Version
        version = "v1.0.0"
        ver_surface = self.font_small.render(version, True, (60, 65, 75))
        screen.blit(ver_surface, (Settings.SCREEN_WIDTH - 70, Settings.SCREEN_HEIGHT - 30))


class PauseMenu(BaseMenu):
    """Pause menu overlay with blur effect."""
    
    def __init__(self):
        super().__init__()
        
        center_y = Settings.SCREEN_HEIGHT // 2 + 10  # Slightly lower for better balance
        spacing = 75  # Better spacing between menu items
        
        self.items = [
            MenuItem("RESUME", lambda: "resume", center_y - spacing),
            MenuItem("RESTART LEVEL", lambda: "restart", center_y),
            MenuItem("MAIN MENU", lambda: "main_menu", center_y + spacing),
        ]
        self.items[0].selected = True
        self._anim_time = 0.0
    
    def update(self, dt: float):
        super().update(dt)
        self._anim_time += dt
    
    def render(self, screen: pygame.Surface) -> None:
        # Dark overlay with gradient
        overlay = pygame.Surface((Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 15, 25, 200))
        screen.blit(overlay, (0, 0))
        
        # Title with glow
        glow = (math.sin(self._anim_time * 3) + 1) / 2
        title_color = (
            int(150 + 50 * glow),
            int(180 + 50 * glow),
            255
        )
        
        title_surface = self.font_title.render("PAUSED", True, title_color)
        title_rect = title_surface.get_rect(centerx=Settings.SCREEN_WIDTH // 2, top=120)
        screen.blit(title_surface, title_rect)
        
        # Decorative line with better spacing
        line_y = 205
        pygame.draw.line(screen, (60, 80, 120),
                        (Settings.SCREEN_WIDTH // 2 - 150, line_y),
                        (Settings.SCREEN_WIDTH // 2 + 150, line_y), 2)
        
        # Menu items
        for item in self.items:
            item.render(screen, self.font_large)
        
        # Hint
        hint = "Press ESC to resume"
        hint_surface = self.font_small.render(hint, True, (100, 105, 120))
        hint_rect = hint_surface.get_rect(centerx=Settings.SCREEN_WIDTH // 2, 
                                         bottom=Settings.SCREEN_HEIGHT - 30)
        screen.blit(hint_surface, hint_rect)


class GameOverScreen(BaseMenu):
    """Game over screen with dramatic visuals."""
    
    def __init__(self):
        super().__init__()
        
        center_y = Settings.SCREEN_HEIGHT // 2 + 70  # Better vertical positioning
        spacing = 75  # Consistent spacing with other menus
        
        self.items = [
            MenuItem("TRY AGAIN", lambda: "restart", center_y),
            MenuItem("MAIN MENU", lambda: "main_menu", center_y + spacing),
        ]
        self.items[0].selected = True
        
        self.death_message = "TIME BANKRUPTCY"
        self._anim_time = 0.0
    
    def set_death_message(self, message: str) -> None:
        self.death_message = message
    
    def update(self, dt: float):
        super().update(dt)
        self._anim_time += dt
    
    def render(self, screen: pygame.Surface) -> None:
        # Red-tinted overlay
        overlay = pygame.Surface((Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        
        # Gradient red background
        pulse = (math.sin(self._anim_time * 2) + 1) / 2
        overlay.fill((int(60 + 30 * pulse), 10, 15, 220))
        screen.blit(overlay, (0, 0))
        
        # Vignette effect
        for i in range(5):
            vign_rect = pygame.Rect(i * 20, i * 20, 
                                   Settings.SCREEN_WIDTH - i * 40,
                                   Settings.SCREEN_HEIGHT - i * 40)
            pygame.draw.rect(overlay, (40, 0, 0, 40 - i * 8), vign_rect, width=20)
        screen.blit(overlay, (0, 0))
        
        # Glitchy title effect
        title_text = "GAME OVER"
        
        # Glitch offset
        if random.random() < 0.1:
            offset = random.randint(-5, 5)
        else:
            offset = 0
        
        # Red channel offset (chromatic aberration)
        red_surface = self.font_title.render(title_text, True, (255, 50, 50))
        screen.blit(red_surface, (Settings.SCREEN_WIDTH // 2 - red_surface.get_width() // 2 - 3 + offset, 117))
        
        # Main title with better positioning
        title_surface = self.font_title.render(title_text, True, (255, 200, 200))
        title_rect = title_surface.get_rect(centerx=Settings.SCREEN_WIDTH // 2, top=110)
        screen.blit(title_surface, title_rect)
        
        # Death message with improved spacing
        msg_surface = self.font_medium.render(self.death_message, True, (255, 150, 150))
        msg_rect = msg_surface.get_rect(centerx=Settings.SCREEN_WIDTH // 2, top=205)
        screen.blit(msg_surface, msg_rect)
        
        # Warning symbol with better margin
        warning = "⚠ TEMPORAL COLLAPSE ⚠"
        warn_surface = self.font_small.render(warning, True, (180, 80, 80))
        warn_rect = warn_surface.get_rect(centerx=Settings.SCREEN_WIDTH // 2, top=250)
        screen.blit(warn_surface, warn_rect)
        
        # Menu items
        for item in self.items:
            item.render(screen, self.font_large)


class VictoryScreen(BaseMenu):
    """Victory/level complete screen with celebration effects."""
    
    def __init__(self):
        super().__init__()
        
        center_y = Settings.SCREEN_HEIGHT // 2 + 110  # Better positioning
        spacing = 75  # Consistent spacing
        
        self.items = [
            MenuItem("NEXT LEVEL", lambda: "next_level", center_y),
            MenuItem("MAIN MENU", lambda: "main_menu", center_y + spacing),
        ]
        self.items[0].selected = True
        
        self.level_name = ""
        self.completion_time = 0.0
        self.total_debt = 0.0
        self.is_final_level = False
        self._anim_time = 0.0
        
        # Celebration particles
        self._celebration_particles: List[Particle] = []
    
    def set_stats(self, level_name: str, time: float, debt: float, is_final: bool = False):
        self.level_name = level_name
        self.completion_time = time
        self.total_debt = debt
        self.is_final_level = is_final
        
        if is_final:
            self.items[0] = MenuItem("PLAY AGAIN", lambda: "restart_game", 
                                    Settings.SCREEN_HEIGHT // 2 + 100)
            self.items[0].selected = True
        
        # Spawn celebration particles
        for _ in range(30):
            self._celebration_particles.append(Particle(
                random.uniform(100, Settings.SCREEN_WIDTH - 100),
                Settings.SCREEN_HEIGHT + 50
            ))
    
    def update(self, dt: float):
        super().update(dt)
        self._anim_time += dt
        
        # Update celebration particles
        self._celebration_particles = [p for p in self._celebration_particles if p.update(dt)]
        
        # Spawn more particles occasionally
        if random.random() < 0.1:
            self._celebration_particles.append(Particle(
                random.uniform(100, Settings.SCREEN_WIDTH - 100),
                Settings.SCREEN_HEIGHT + 50
            ))
    
    def render(self, screen: pygame.Surface) -> None:
        # Green-tinted overlay
        overlay = pygame.Surface((Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((10, 40, 20, 210))
        screen.blit(overlay, (0, 0))
        
        # Celebration particles
        for p in self._celebration_particles:
            p.render(screen, (100, 255, 150))
        
        # Title with glow
        glow = (math.sin(self._anim_time * 3) + 1) / 2
        title_text = "GAME COMPLETE!" if self.is_final_level else "LEVEL COMPLETE!"
        title_color = (
            int(100 + 50 * glow),
            int(255),
            int(150 + 50 * glow)
        )
        
        title_surface = self.font_title.render(title_text, True, title_color)
        title_rect = title_surface.get_rect(centerx=Settings.SCREEN_WIDTH // 2, top=70)
        screen.blit(title_surface, title_rect)
        
        # Level name with better spacing
        name_surface = self.font_large.render(self.level_name, True, (220, 255, 220))
        name_rect = name_surface.get_rect(centerx=Settings.SCREEN_WIDTH // 2, top=155)
        screen.blit(name_surface, name_rect)
        
        # Stats box with improved dimensions and positioning
        stats_box = pygame.Rect(Settings.SCREEN_WIDTH // 2 - 220, 205, 440, 110)
        pygame.draw.rect(screen, (20, 60, 30), stats_box, border_radius=10)
        pygame.draw.rect(screen, (80, 180, 100), stats_box, width=2, border_radius=10)
        
        # Time stat with better padding
        time_text = f"Completion Time: {self.completion_time:.1f}s"
        time_surface = self.font_medium.render(time_text, True, (200, 255, 200))
        time_rect = time_surface.get_rect(centerx=Settings.SCREEN_WIDTH // 2, top=228)
        screen.blit(time_surface, time_rect)
        
        # Debt stat with improved spacing
        debt_color = (255, 200, 100) if self.total_debt > 5 else (150, 255, 150)
        debt_text = f"Total Debt Incurred: {self.total_debt:.1f}s"
        debt_surface = self.font_medium.render(debt_text, True, debt_color)
        debt_rect = debt_surface.get_rect(centerx=Settings.SCREEN_WIDTH // 2, top=268)
        screen.blit(debt_surface, debt_rect)
        
        # Menu items
        for item in self.items:
            item.render(screen, self.font_large)
