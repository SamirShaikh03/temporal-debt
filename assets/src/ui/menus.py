"""
Menu Screens — Neon Abyss theme with psychological design.

Menus use deep dark backgrounds with vibrant neon accents.
Color psychology: cyan/teal = calm → magenta = unease → red = danger.

Design Philosophy:
- Immersive dark atmosphere from the first pixel
- Smooth animations telegraph interactivity
- Consistent neon accent language
"""

import pygame
import math
import random
from typing import Optional, Callable, List
from enum import Enum, auto

from ..core.settings import Settings, COLORS
from ..core.utils import get_font


class MenuState(Enum):
    NONE = auto()
    MAIN_MENU = auto()
    PAUSE = auto()
    GAME_OVER = auto()
    VICTORY = auto()


class Particle:
    """Neon particle for ambient menu effects."""
    def __init__(self, x: float, y: float, color: tuple = None):
        self.x = x
        self.y = y
        self.vx = random.uniform(-15, 15)
        self.vy = random.uniform(-35, -8)
        self.size = random.uniform(1.5, 4)
        self.alpha = random.randint(60, 180)
        self.lifetime = random.uniform(2.5, 6)
        self.age = 0
        self.color = color or (0, 200, 255)
    
    def update(self, dt: float) -> bool:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.age += dt
        self.alpha = int(180 * (1 - self.age / self.lifetime))
        return self.age < self.lifetime
    
    def render(self, screen: pygame.Surface, color: tuple = None):
        c = color or self.color
        if self.alpha > 0:
            sz = int(max(1, self.size * 2))
            surf = pygame.Surface((sz, sz), pygame.SRCALPHA)
            pygame.draw.circle(surf, (*c[:3], max(0, min(255, self.alpha))),
                             (sz // 2, sz // 2), max(1, sz // 2))
            screen.blit(surf, (int(self.x - sz // 2), int(self.y - sz // 2)))


class MenuItem:
    """A single menu button with neon hover effects."""
    
    def __init__(self, text: str, action: Callable, y_position: int):
        self.text = text
        self.action = action
        self.y = y_position
        self.selected = False
        
        self.width = 360
        self.height = 56
        self.x = (Settings.SCREEN_WIDTH - self.width) // 2
        
        self._hover_anim = 0.0
        self._glow_phase = random.uniform(0, math.pi * 2)
    
    def get_rect(self) -> pygame.Rect:
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def update(self, dt: float):
        if self.selected:
            self._hover_anim = min(1.0, self._hover_anim + dt * 6)
        else:
            self._hover_anim = max(0.0, self._hover_anim - dt * 4)
        self._glow_phase += dt * 2.5
    
    def render(self, screen: pygame.Surface, font: pygame.font.Font) -> None:
        rect = self.get_rect()
        glow = (math.sin(self._glow_phase) + 1) / 2
        
        if self.selected:
            # Neon glow border
            glow_rect = rect.inflate(6 + int(4 * glow), 6 + int(4 * glow))
            glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            accent = getattr(COLORS, 'MENU_ACCENT', (0, 200, 255))
            pygame.draw.rect(glow_surf, (*accent, int(40 + 30 * glow)),
                           (0, 0, glow_rect.width, glow_rect.height), border_radius=10)
            screen.blit(glow_surf, glow_rect.topleft)
            
            # Filled bg with accent tint
            bg_color = (
                int(15 + 25 * glow),
                int(35 + 40 * glow),
                int(60 + 50 * glow)
            )
            pygame.draw.rect(screen, bg_color, rect, border_radius=8)
            pygame.draw.rect(screen, accent, rect, width=2, border_radius=8)
            text_color = COLORS.WHITE
        else:
            # Muted background
            pygame.draw.rect(screen, (18, 22, 35), rect, border_radius=8)
            pygame.draw.rect(screen, (40, 48, 65), rect, width=1, border_radius=8)
            text_color = getattr(COLORS, 'MENU_TEXT_DIM', (100, 110, 130))
        
        # Text with subtle shadow
        if self.selected:
            shadow = font.render(self.text, True, (5, 10, 20))
            screen.blit(shadow, (rect.centerx - shadow.get_width() // 2 + 2,
                                rect.centery - shadow.get_height() // 2 + 2))
        
        text_surface = font.render(self.text, True, text_color)
        text_rect = text_surface.get_rect(center=rect.center)
        screen.blit(text_surface, text_rect)


class BaseMenu:
    """Base class for all menu screens — neon abyss theme."""
    
    def __init__(self):
        pygame.font.init()
        self.font_title = get_font('Segoe UI', 72, bold=True)
        self.font_large = get_font('Segoe UI', 30)
        self.font_medium = get_font('Segoe UI', 24)
        self.font_small = get_font('Segoe UI', 18)
        
        self.items: List[MenuItem] = []
        self.selected_index = 0
        
        self.particles: List[Particle] = []
        self._particle_timer = 0
    
    def update(self, dt: float):
        self._particle_timer += dt
        if self._particle_timer > 0.08:
            self._particle_timer = 0
            # Spawn particles with neon colors
            color_choices = [
                getattr(COLORS, 'MENU_ACCENT', (0, 200, 255)),
                getattr(COLORS, 'MENU_ACCENT2', (220, 50, 255)),
                (0, 180, 180),
            ]
            self.particles.append(Particle(
                random.uniform(0, Settings.SCREEN_WIDTH),
                Settings.SCREEN_HEIGHT + 10,
                color=random.choice(color_choices)
            ))
        
        self.particles = [p for p in self.particles if p.update(dt)]
        
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
    
    def _render_background(self, screen: pygame.Surface, color: tuple = None):
        bg = color or getattr(COLORS, 'MENU_BG', (8, 10, 20))
        screen.fill(bg)
        
        # Subtle grid
        grid_color = getattr(COLORS, 'MENU_GRID', (18, 22, 40))
        for x in range(0, Settings.SCREEN_WIDTH, 64):
            pygame.draw.line(screen, grid_color, (x, 0), (x, Settings.SCREEN_HEIGHT))
        for y in range(0, Settings.SCREEN_HEIGHT, 64):
            pygame.draw.line(screen, grid_color, (0, y), (Settings.SCREEN_WIDTH, y))
        
        # Particles
        for p in self.particles:
            p.render(screen)
    
    def render(self, screen: pygame.Surface) -> None:
        pass


class MainMenu(BaseMenu):
    """Main menu — immersive neon abyss intro."""
    
    def __init__(self):
        super().__init__()
        
        start_y = 400
        spacing = 75
        
        self.items = [
            MenuItem("START GAME", lambda: "start", start_y),
            MenuItem("CONTROLS", lambda: "controls", start_y + spacing),
            MenuItem("QUIT", lambda: "quit", start_y + spacing * 2),
        ]
        self.items[0].selected = True
        
        self._title_time = 0.0
        self._subtitle_alpha = 0
        
    def update(self, dt: float) -> None:
        super().update(dt)
        self._title_time += dt
        self._subtitle_alpha = min(255, self._subtitle_alpha + int(dt * 150))
    
    def render(self, screen: pygame.Surface) -> None:
        self._render_background(screen)
        
        t = self._title_time
        accent = getattr(COLORS, 'MENU_ACCENT', (0, 200, 255))
        accent2 = getattr(COLORS, 'MENU_ACCENT2', (220, 50, 255))
        
        # Animated vignette overlay
        vig = pygame.Surface((Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        pulse = (math.sin(t * 0.8) + 1) / 2
        vig_alpha = int(30 + 20 * pulse)
        cx, cy = Settings.SCREEN_WIDTH // 2, Settings.SCREEN_HEIGHT // 2
        for ring in range(3):
            radius = 300 + ring * 150
            pygame.draw.circle(vig, (*accent[:3], max(0, vig_alpha - ring * 10)),
                             (cx, cy), radius, 2)
        screen.blit(vig, (0, 0))
        
        # Title glow
        glow = (math.sin(t * 2) + 1) / 2
        title_color = (
            int(lerp_val(accent[0], accent2[0], glow)),
            int(lerp_val(accent[1], accent2[1], glow)),
            int(lerp_val(accent[2], accent2[2], glow))
        )
        
        title_text = "TEMPORAL DEBT"
        
        # Chromatic aberration on title — red/blue offset
        red_surf = self.font_title.render(title_text, True, (255, 40, 80))
        blue_surf = self.font_title.render(title_text, True, (40, 80, 255))
        main_surf = self.font_title.render(title_text, True, title_color)
        
        title_x = Settings.SCREEN_WIDTH // 2 - main_surf.get_width() // 2
        title_y = 75
        
        # Offset layers
        offset = int(2 + 1 * glow)
        red_alpha = pygame.Surface(red_surf.get_size(), pygame.SRCALPHA)
        red_alpha.blit(red_surf, (0, 0))
        red_alpha.set_alpha(80)
        blue_alpha = pygame.Surface(blue_surf.get_size(), pygame.SRCALPHA)
        blue_alpha.blit(blue_surf, (0, 0))
        blue_alpha.set_alpha(80)
        
        screen.blit(red_alpha, (title_x - offset, title_y))
        screen.blit(blue_alpha, (title_x + offset, title_y))
        screen.blit(main_surf, (title_x, title_y))
        
        # Subtitle — psychological hook
        subtitle = "Time is a loan you cannot afford."
        if self._subtitle_alpha > 0:
            sub_alpha = min(255, self._subtitle_alpha)
            sub_surf = self.font_medium.render(subtitle, True,
                                               (150, 160, 180))
            sub_surf.set_alpha(sub_alpha)
            sub_rect = sub_surf.get_rect(centerx=Settings.SCREEN_WIDTH // 2, top=165)
            screen.blit(sub_surf, sub_rect)
        
        # Decorative neon line
        line_y = 205
        line_w = 450
        line_start = Settings.SCREEN_WIDTH // 2 - line_w // 2
        line_end = Settings.SCREEN_WIDTH // 2 + line_w // 2
        pygame.draw.line(screen, accent, (line_start, line_y), (line_end, line_y), 2)
        # Glow dot at center
        pygame.draw.circle(screen, accent, (Settings.SCREEN_WIDTH // 2, line_y), 4)
        
        # Feature highlights with neon bullets
        features = [
            ("FREEZE TIME", "Every second borrowed accrues deadly DEBT"),
            ("DEBT TIERS", "Higher debt = faster, deadlier world"),
            ("DANGER ZONES", "Touch them and enemies will punish you"),
        ]
        
        fy = 230
        for i, (key, desc) in enumerate(features):
            # Neon bullet
            bullet_color = accent if i % 2 == 0 else accent2
            pygame.draw.circle(screen, bullet_color,
                             (Settings.SCREEN_WIDTH // 2 - 250, fy + 10), 4)
            key_surf = self.font_small.render(key, True, bullet_color)
            screen.blit(key_surf, (Settings.SCREEN_WIDTH // 2 - 238, fy))
            desc_surf = self.font_small.render(f"  —  {desc}", True, (100, 110, 140))
            screen.blit(desc_surf, (Settings.SCREEN_WIDTH // 2 - 238 + key_surf.get_width(), fy))
            fy += 35
        
        # Menu items
        for item in self.items:
            item.render(screen, self.font_large)
        
        # Bottom hint
        hint = "WASD to navigate  ·  ENTER to select"
        hint_surf = self.font_small.render(hint, True, (60, 65, 80))
        screen.blit(hint_surf, (20, Settings.SCREEN_HEIGHT - 28))
        
        version = "v3.0"
        ver_surf = self.font_small.render(version, True, (50, 55, 70))
        screen.blit(ver_surf, (Settings.SCREEN_WIDTH - 60, Settings.SCREEN_HEIGHT - 28))


def lerp_val(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


class PauseMenu(BaseMenu):
    """Pause menu overlay with dark neon aesthetic."""
    
    def __init__(self):
        super().__init__()
        
        center_y = Settings.SCREEN_HEIGHT // 2 + 10
        spacing = 72
        
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
        overlay = pygame.Surface((Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((6, 8, 16, 210))
        screen.blit(overlay, (0, 0))
        
        accent = getattr(COLORS, 'MENU_ACCENT', (0, 200, 255))
        glow = (math.sin(self._anim_time * 3) + 1) / 2
        title_color = (
            int(accent[0] * (0.6 + 0.4 * glow)),
            int(accent[1] * (0.6 + 0.4 * glow)),
            int(accent[2] * (0.6 + 0.4 * glow))
        )
        
        title_surface = self.font_title.render("PAUSED", True, title_color)
        title_rect = title_surface.get_rect(centerx=Settings.SCREEN_WIDTH // 2, top=120)
        screen.blit(title_surface, title_rect)
        
        line_y = 205
        pygame.draw.line(screen, accent,
                        (Settings.SCREEN_WIDTH // 2 - 150, line_y),
                        (Settings.SCREEN_WIDTH // 2 + 150, line_y), 2)
        
        for item in self.items:
            item.render(screen, self.font_large)
        
        hint = "Press ESC to resume"
        hint_surface = self.font_small.render(hint, True, (80, 85, 100))
        hint_rect = hint_surface.get_rect(centerx=Settings.SCREEN_WIDTH // 2,
                                         bottom=Settings.SCREEN_HEIGHT - 30)
        screen.blit(hint_surface, hint_rect)


class GameOverScreen(BaseMenu):
    """Game over screen — dramatic neon-red glitch aesthetic."""
    
    def __init__(self):
        super().__init__()
        
        center_y = Settings.SCREEN_HEIGHT // 2 + 70
        spacing = 75
        
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
        # Deep red-magenta overlay
        overlay = pygame.Surface((Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        pulse = (math.sin(self._anim_time * 2) + 1) / 2
        overlay.fill((int(40 + 30 * pulse), 5, int(15 + 10 * pulse), 225))
        screen.blit(overlay, (0, 0))
        
        # Scan lines effect
        scan = pygame.Surface((Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        for y in range(0, Settings.SCREEN_HEIGHT, 3):
            pygame.draw.line(scan, (0, 0, 0, 30), (0, y), (Settings.SCREEN_WIDTH, y))
        screen.blit(scan, (0, 0))
        
        # Glitchy title
        title_text = "GAME OVER"
        
        # Chromatic aberration — offset increases with pulse
        offset = int(3 + 4 * pulse)
        if random.random() < 0.08:
            offset += random.randint(-8, 8)
        
        red_surf = self.font_title.render(title_text, True, (255, 30, 60))
        blue_surf = self.font_title.render(title_text, True, (60, 30, 255))
        main_surf = self.font_title.render(title_text, True, (255, 180, 180))
        
        tx = Settings.SCREEN_WIDTH // 2 - main_surf.get_width() // 2
        ty = 100
        
        red_a = pygame.Surface(red_surf.get_size(), pygame.SRCALPHA)
        red_a.blit(red_surf, (0, 0))
        red_a.set_alpha(100)
        blue_a = pygame.Surface(blue_surf.get_size(), pygame.SRCALPHA)
        blue_a.blit(blue_surf, (0, 0))
        blue_a.set_alpha(80)
        
        screen.blit(red_a, (tx - offset, ty))
        screen.blit(blue_a, (tx + offset, ty))
        screen.blit(main_surf, (tx, ty))
        
        # Death message
        msg_surf = self.font_medium.render(self.death_message, True, (255, 120, 120))
        msg_rect = msg_surf.get_rect(centerx=Settings.SCREEN_WIDTH // 2, top=195)
        screen.blit(msg_surf, msg_rect)
        
        # Warning
        warning = "TEMPORAL COLLAPSE"
        warn_surf = self.font_small.render(warning, True, (180, 50, 60))
        warn_rect = warn_surf.get_rect(centerx=Settings.SCREEN_WIDTH // 2, top=240)
        screen.blit(warn_surf, warn_rect)
        
        for item in self.items:
            item.render(screen, self.font_large)


class VictoryScreen(BaseMenu):
    """Victory screen — neon-cyan celebration with particle fireworks."""
    
    def __init__(self):
        super().__init__()
        
        center_y = Settings.SCREEN_HEIGHT // 2 + 110
        spacing = 75
        
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
        
        # Spawn multi-colored celebration particles
        celebration_colors = [
            getattr(COLORS, 'MENU_ACCENT', (0, 200, 255)),
            getattr(COLORS, 'MENU_ACCENT2', (220, 50, 255)),
            (0, 255, 180),
            (255, 220, 50),
        ]
        for _ in range(40):
            p = Particle(
                random.uniform(80, Settings.SCREEN_WIDTH - 80),
                Settings.SCREEN_HEIGHT + 50,
                color=random.choice(celebration_colors),
            )
            self._celebration_particles.append(p)
    
    def update(self, dt: float):
        super().update(dt)
        self._anim_time += dt
        
        self._celebration_particles = [p for p in self._celebration_particles if p.update(dt)]
        
        if random.random() < 0.15:
            celebration_colors = [
                getattr(COLORS, 'MENU_ACCENT', (0, 200, 255)),
                getattr(COLORS, 'MENU_ACCENT2', (220, 50, 255)),
                (0, 255, 180),
            ]
            self._celebration_particles.append(Particle(
                random.uniform(80, Settings.SCREEN_WIDTH - 80),
                Settings.SCREEN_HEIGHT + 50,
                color=random.choice(celebration_colors),
            ))
    
    def render(self, screen: pygame.Surface) -> None:
        # Deep teal overlay
        overlay = pygame.Surface((Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((6, 25, 30, 215))
        screen.blit(overlay, (0, 0))
        
        # Celebration particles
        for p in self._celebration_particles:
            p.render(screen)
        
        # Title with pulsing glow
        glow = (math.sin(self._anim_time * 3) + 1) / 2
        title_text = "GAME COMPLETE!" if self.is_final_level else "LEVEL COMPLETE!"
        accent = getattr(COLORS, 'MENU_ACCENT', (0, 200, 255))
        title_color = (
            int(accent[0] * 0.5 + accent[0] * 0.5 * glow),
            int(min(255, accent[1] + 40 * glow)),
            int(min(255, accent[2] + 30 * glow)),
        )
        
        title_surface = self.font_title.render(title_text, True, title_color)
        title_rect = title_surface.get_rect(centerx=Settings.SCREEN_WIDTH // 2, top=70)
        screen.blit(title_surface, title_rect)
        
        # Level name
        name_surface = self.font_large.render(self.level_name, True, (200, 240, 255))
        name_rect = name_surface.get_rect(centerx=Settings.SCREEN_WIDTH // 2, top=155)
        screen.blit(name_surface, name_rect)
        
        # Stats box
        stats_box = pygame.Rect(Settings.SCREEN_WIDTH // 2 - 230, 200, 460, 120)
        pygame.draw.rect(screen, (12, 30, 40), stats_box, border_radius=12)
        pygame.draw.rect(screen, accent, stats_box, width=2, border_radius=12)
        
        # Inner glow line at top of stats box
        glow_rect = pygame.Rect(stats_box.x + 2, stats_box.y + 2, stats_box.width - 4, 2)
        glow_surf = pygame.Surface((glow_rect.width, 2), pygame.SRCALPHA)
        glow_surf.fill((*accent, 120))
        screen.blit(glow_surf, glow_rect.topleft)
        
        time_text = f"Completion Time: {self.completion_time:.1f}s"
        time_surface = self.font_medium.render(time_text, True, (180, 230, 255))
        time_rect = time_surface.get_rect(centerx=Settings.SCREEN_WIDTH // 2, top=225)
        screen.blit(time_surface, time_rect)
        
        debt_color = (255, 180, 80) if self.total_debt > 5 else (100, 255, 200)
        debt_text = f"Total Debt Incurred: {self.total_debt:.1f}s"
        debt_surface = self.font_medium.render(debt_text, True, debt_color)
        debt_rect = debt_surface.get_rect(centerx=Settings.SCREEN_WIDTH // 2, top=270)
        screen.blit(debt_surface, debt_rect)
        
        for item in self.items:
            item.render(screen, self.font_large)


class ControlsScreen(BaseMenu):
    """Full-screen controls — neon-styled keybinding reference."""
    
    def __init__(self):
        super().__init__()
        
        self.items = [
            MenuItem("BACK", lambda: "back", Settings.SCREEN_HEIGHT - 100),
        ]
        self.items[0].selected = True
        
        self._anim_time = 0.0
        
        self.controls = [
            ('WASD / Arrows', 'Move your character'),
            ('SPACE (hold)', 'Freeze time — accumulates debt!'),
            ('Q', 'Place a Time Anchor checkpoint'),
            ('E', 'Recall to nearest anchor (costs debt)'),
            ('C', 'Spawn Chrono-Clone (replays your path)'),
            ('R', 'Time Rewind (limited uses)'),
            ('B', 'Fragment Burst (5 fragments = slow-mo)'),
            ('F (hold)', 'Interact with Debt Transfer Pods'),
            ('ESC', 'Pause the game'),
        ]
        
        self.tips = [
            "Higher debt = faster, more dangerous world",
            "Temporal Hunters only move when time is frozen!",
            "Stay moving to build Momentum (reduces debt rate)",
            "Chrono-Clones distract enemies and trigger plates",
            "Avoid Debt Leeches — they drain your time silently",
        ]
    
    def handle_input(self, event: pygame.event.Event) -> Optional[str]:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return "back"
        return super().handle_input(event)
    
    def update(self, dt: float):
        super().update(dt)
        self._anim_time += dt
    
    def render(self, screen: pygame.Surface) -> None:
        self._render_background(screen)
        
        accent = getattr(COLORS, 'MENU_ACCENT', (0, 200, 255))
        accent2 = getattr(COLORS, 'MENU_ACCENT2', (220, 50, 255))
        
        # Title
        glow = (math.sin(self._anim_time * 2) + 1) / 2
        title_color = (
            int(accent[0] * 0.6 + accent[0] * 0.4 * glow),
            int(min(255, accent[1] + 30 * glow)),
            int(min(255, accent[2] + 20 * glow)),
        )
        title_surface = self.font_title.render("CONTROLS", True, title_color)
        title_rect = title_surface.get_rect(centerx=Settings.SCREEN_WIDTH // 2, top=45)
        screen.blit(title_surface, title_rect)
        
        # Accent line under title
        line_y = 125
        line_hw = 200
        cx = Settings.SCREEN_WIDTH // 2
        for i in range(3):
            a = max(0, 180 - i * 60)
            col = (*accent[:3], a) if len(accent) >= 3 else (0, 200, 255, a)
            line_surf = pygame.Surface((line_hw * 2 + i * 40, 1), pygame.SRCALPHA)
            line_surf.fill(col)
            screen.blit(line_surf, (cx - line_hw - i * 20, line_y + i))
        
        # Controls section
        y_offset = 155
        
        for key, desc in self.controls:
            # Key badge
            key_surf = self.font_medium.render(key, True, accent)
            badge_w = max(160, key_surf.get_width() + 24)
            key_rect = pygame.Rect(cx - 290, y_offset - 4, badge_w, 34)
            pygame.draw.rect(screen, (18, 22, 40), key_rect, border_radius=6)
            pygame.draw.rect(screen, (*accent[:3], 120) if len(accent) >= 3 else (0, 200, 255, 120),
                           key_rect, width=1, border_radius=6)
            
            key_text_rect = key_surf.get_rect(center=key_rect.center)
            screen.blit(key_surf, key_text_rect)
            
            # Description
            desc_surface = self.font_medium.render(desc, True, (160, 170, 190))
            screen.blit(desc_surface, (cx - 105, y_offset + 2))
            
            y_offset += 45
        
        # Tips section
        tips_y = y_offset + 20
        tips_title = self.font_large.render("TIPS", True, accent2)
        tips_rect = tips_title.get_rect(centerx=cx, top=tips_y)
        screen.blit(tips_title, tips_rect)
        
        # Accent line under tips
        line_surf2 = pygame.Surface((140, 1), pygame.SRCALPHA)
        line_surf2.fill((*accent2[:3], 100) if len(accent2) >= 3 else (220, 50, 255, 100))
        screen.blit(line_surf2, (cx - 70, tips_y + 38))
        
        tips_y += 50
        for tip in self.tips:
            bullet = "> " + tip
            tip_surface = self.font_small.render(bullet, True, (120, 130, 160))
            tip_rect = tip_surface.get_rect(centerx=cx, top=tips_y)
            screen.blit(tip_surface, tip_rect)
            tips_y += 28
        
        for item in self.items:
            item.render(screen, self.font_large)
        
        hint = "Press ESC or click BACK to return"
        hint_surface = self.font_small.render(hint, True, (60, 65, 80))
        hint_rect = hint_surface.get_rect(centerx=cx, bottom=Settings.SCREEN_HEIGHT - 20)
        screen.blit(hint_surface, hint_rect)
