"""
Tutorial System - Guides new players through game mechanics.

Provides step-by-step introduction to:
- Basic movement
- Time freezing
- Debt system
- Anchors
- Enemies

Design Philosophy:
- Non-intrusive but informative
- Learn by doing
- Visual cues over text
"""

import pygame
import math
from typing import Optional, List, Tuple
from enum import Enum, auto

from ..core.settings import Settings, COLORS


class TutorialStep(Enum):
    """Tutorial progression stages."""
    WELCOME = auto()
    MOVEMENT = auto()
    TIME_FREEZE = auto()
    DEBT_EXPLAIN = auto()
    ANCHORS = auto()
    ENEMIES = auto()
    COMPLETE = auto()


class TutorialOverlay:
    """
    Renders tutorial instructions as beautiful overlays.
    
    Features animated text, glowing highlights, and
    visual indicators for controls.
    """
    
    def __init__(self):
        pygame.font.init()
        
        # Fonts
        self.font_title = pygame.font.SysFont('Segoe UI', 48, bold=True)
        self.font_main = pygame.font.SysFont('Segoe UI', 28)
        self.font_hint = pygame.font.SysFont('Segoe UI', 22)
        self.font_key = pygame.font.SysFont('Consolas', 32, bold=True)
        
        # State
        self.current_step = TutorialStep.WELCOME
        self.step_timer = 0.0
        self.is_active = True
        self.fade_alpha = 255
        self.transitioning = False
        
        # Animation
        self._pulse_time = 0.0
        self._key_flash_time = 0.0
        
        # Track player actions
        self.has_moved = False
        self.has_frozen_time = False
        self.has_placed_anchor = False
        self.has_recalled = False
        
        # Tutorial data
        self.steps_data = {
            TutorialStep.WELCOME: {
                'title': 'TEMPORAL DEBT',
                'subtitle': 'A Game of Borrowed Time',
                'text': [
                    'Welcome, Temporal Borrower.',
                    'You have the power to freeze time...',
                    'But every second borrowed must be repaid.'
                ],
                'hint': 'Press any key to continue',
                'auto_advance': False,
                'duration': 0
            },
            TutorialStep.MOVEMENT: {
                'title': 'MOVEMENT',
                'subtitle': '',
                'text': ['Use the movement keys to navigate.'],
                'keys': [
                    ('W', 'Up'),
                    ('A', 'Left'),
                    ('S', 'Down'),
                    ('D', 'Right')
                ],
                'hint': 'Move around to continue',
                'auto_advance': False,
                'check': 'movement'
            },
            TutorialStep.TIME_FREEZE: {
                'title': 'TIME FREEZE',
                'subtitle': 'Your Greatest Power',
                'text': [
                    'Hold SPACE to freeze time.',
                    'The world stops - but you can still move!',
                    'Use it to dodge enemies and plan routes.'
                ],
                'keys': [('SPACE', 'Hold to Freeze')],
                'hint': 'Hold SPACE for 2 seconds',
                'auto_advance': False,
                'check': 'freeze'
            },
            TutorialStep.DEBT_EXPLAIN: {
                'title': 'TEMPORAL DEBT',
                'subtitle': 'The Cost of Power',
                'text': [
                    'Every second frozen adds DEBT.',
                    'When unfrozen, time accelerates to repay it.',
                    'High debt = faster, more dangerous world!',
                    '',
                    'Watch your debt meter at the top-left.'
                ],
                'hint': 'Press any key to continue',
                'auto_advance': False
            },
            TutorialStep.ANCHORS: {
                'title': 'TIME ANCHORS',
                'subtitle': 'Safety Points',
                'text': [
                    'Press Q to place a Time Anchor.',
                    'Press E to recall to your nearest anchor.',
                    'Warning: Recalling costs 2 seconds of debt!'
                ],
                'keys': [
                    ('Q', 'Place Anchor'),
                    ('E', 'Recall')
                ],
                'hint': 'Place an anchor with Q',
                'auto_advance': False,
                'check': 'anchor'
            },
            TutorialStep.ENEMIES: {
                'title': 'THREATS',
                'subtitle': 'Know Your Enemies',
                'text': [
                    '🔴 Patrol Drones - Follow set paths',
                    '🟣 Temporal Hunters - Move ONLY when time is frozen!',
                    '👤 Debt Shadows - Spawn at high debt levels',
                    '',
                    'Reach the green EXIT zone to complete each level.'
                ],
                'hint': 'Press any key to begin!',
                'auto_advance': False
            },
            TutorialStep.COMPLETE: {
                'title': 'READY',
                'subtitle': '',
                'text': ['Good luck, Borrower. Manage your debt wisely.'],
                'hint': '',
                'auto_advance': True,
                'duration': 2.0
            }
        }
    
    def update(self, dt: float, keys_pressed: dict = None) -> None:
        """Update tutorial state."""
        if not self.is_active:
            return
        
        self._pulse_time += dt
        self._key_flash_time += dt
        self.step_timer += dt
        
        # Check for step completion
        step_data = self.steps_data.get(self.current_step, {})
        
        if step_data.get('auto_advance') and self.step_timer >= step_data.get('duration', 2.0):
            self._advance_step()
        
        # Handle transitioning
        if self.transitioning:
            self.fade_alpha = max(0, self.fade_alpha - int(dt * 500))
            if self.fade_alpha <= 0:
                self.transitioning = False
                self.fade_alpha = 255
    
    def handle_input(self, event: pygame.event.Event) -> bool:
        """
        Handle input during tutorial.
        
        Returns True if tutorial consumed the input.
        """
        if not self.is_active or self.transitioning:
            return False
        
        step_data = self.steps_data.get(self.current_step, {})
        
        # Generic key advance for non-check steps
        if event.type == pygame.KEYDOWN:
            if 'check' not in step_data:
                self._advance_step()
                return True
        
        return False
    
    def notify_action(self, action: str) -> None:
        """Notify tutorial of player action."""
        if not self.is_active:
            return
        
        step_data = self.steps_data.get(self.current_step, {})
        check = step_data.get('check')
        
        if check == 'movement' and action == 'moved':
            self.has_moved = True
            self._advance_step()
        elif check == 'freeze' and action == 'frozen_2s':
            self.has_frozen_time = True
            self._advance_step()
        elif check == 'anchor' and action == 'anchor_placed':
            self.has_placed_anchor = True
            self._advance_step()
    
    def _advance_step(self) -> None:
        """Advance to next tutorial step."""
        self.transitioning = True
        self.step_timer = 0.0
        
        steps = list(TutorialStep)
        current_idx = steps.index(self.current_step)
        
        if current_idx < len(steps) - 1:
            self.current_step = steps[current_idx + 1]
        
        if self.current_step == TutorialStep.COMPLETE:
            # Will auto-hide after duration
            pass
    
    def skip(self) -> None:
        """Skip the tutorial entirely."""
        self.is_active = False
        self.current_step = TutorialStep.COMPLETE
    
    def is_complete(self) -> bool:
        """Check if tutorial is finished."""
        return self.current_step == TutorialStep.COMPLETE and self.step_timer > 2.0
    
    def render(self, screen: pygame.Surface) -> None:
        """Render tutorial overlay."""
        if not self.is_active:
            return
        
        step_data = self.steps_data.get(self.current_step, {})
        
        # Create overlay
        overlay = pygame.Surface((Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT), pygame.SRCALPHA)
        
        # Background gradient
        for y in range(Settings.SCREEN_HEIGHT):
            alpha = int(180 * (1 - abs(y - Settings.SCREEN_HEIGHT // 2) / (Settings.SCREEN_HEIGHT // 2) * 0.3))
            pygame.draw.line(overlay, (10, 15, 30, alpha), (0, y), (Settings.SCREEN_WIDTH, y))
        
        screen.blit(overlay, (0, 0))
        
        # Content box with improved dimensions and centering
        box_width = 750
        box_height = 450
        box_x = (Settings.SCREEN_WIDTH - box_width) // 2
        box_y = (Settings.SCREEN_HEIGHT - box_height) // 2 - 20  # Slightly higher for better balance
        
        # Animated border glow
        pulse = (math.sin(self._pulse_time * 2) + 1) / 2
        glow_color = (
            int(60 + 40 * pulse),
            int(100 + 50 * pulse),
            int(180 + 40 * pulse)
        )
        
        # Box background
        box_rect = pygame.Rect(box_x, box_y, box_width, box_height)
        pygame.draw.rect(screen, (15, 20, 35), box_rect, border_radius=15)
        pygame.draw.rect(screen, glow_color, box_rect, width=3, border_radius=15)
        
        # Inner glow
        inner_rect = box_rect.inflate(-10, -10)
        pygame.draw.rect(screen, (25, 35, 55), inner_rect, border_radius=12)
        
        # Title with improved spacing
        title = step_data.get('title', '')
        title_color = (
            int(150 + 80 * pulse),
            int(200 + 55 * pulse),
            255
        )
        title_surface = self.font_title.render(title, True, title_color)
        title_rect = title_surface.get_rect(centerx=Settings.SCREEN_WIDTH // 2, top=box_y + 30)
        screen.blit(title_surface, title_rect)
        
        # Subtitle with spacing anchored to title height
        subtitle = step_data.get('subtitle', '')
        if subtitle:
            sub_surface = self.font_hint.render(subtitle, True, (120, 140, 180))
            sub_rect = sub_surface.get_rect(centerx=Settings.SCREEN_WIDTH // 2,
                                            top=title_rect.bottom + 16)
            screen.blit(sub_surface, sub_rect)
            content_top = sub_rect.bottom + 26
        else:
            content_top = title_rect.bottom + 32
        
        # Decorative line sits below title/subtitle block
        line_y = content_top
        pygame.draw.line(screen, glow_color, 
                        (box_x + 50, line_y), (box_x + box_width - 50, line_y), 2)
        
        # Main text with improved line spacing
        text_lines = step_data.get('text', [])
        text_y = line_y + 32
        line_spacing = 42  # Increased for better readability
        for line in text_lines:
            if line:
                text_surface = self.font_main.render(line, True, (200, 210, 230))
                text_rect = text_surface.get_rect(centerx=Settings.SCREEN_WIDTH // 2, top=text_y)
                screen.blit(text_surface, text_rect)
            text_y += line_spacing
        
        # Key displays with improved spacing and alignment
        keys = step_data.get('keys', [])
        if keys:
            key_y = text_y + 30  # Better gap from text
            key_spacing = 130  # Increased horizontal spacing
            key_x_start = Settings.SCREEN_WIDTH // 2 - (len(keys) * key_spacing) // 2 + key_spacing // 2
            
            for i, (key, desc) in enumerate(keys):
                kx = key_x_start + i * key_spacing - 40  # Center the key boxes
                
                # Key box with flash effect
                flash = (math.sin(self._key_flash_time * 3 + i) + 1) / 2
                key_bg = (
                    int(40 + 30 * flash),
                    int(60 + 40 * flash),
                    int(100 + 50 * flash)
                )
                
                key_rect = pygame.Rect(kx, key_y, 85, 55)  # Slightly larger for better visibility
                pygame.draw.rect(screen, key_bg, key_rect, border_radius=8)
                pygame.draw.rect(screen, (150, 180, 220), key_rect, width=2, border_radius=8)
                
                # Key text
                key_surface = self.font_key.render(key, True, (255, 255, 255))
                key_text_rect = key_surface.get_rect(center=key_rect.center)
                screen.blit(key_surface, key_text_rect)
                
                # Description with better spacing
                desc_surface = self.font_hint.render(desc, True, (140, 160, 190))
                desc_rect = desc_surface.get_rect(centerx=key_rect.centerx, top=key_rect.bottom + 12)
                screen.blit(desc_surface, desc_rect)
        
        # Hint at bottom with improved positioning
        hint = step_data.get('hint', '')
        if hint:
            # Pulsing hint
            hint_alpha = int(150 + 105 * pulse)
            hint_surface = self.font_hint.render(hint, True, (hint_alpha, hint_alpha, hint_alpha))
            hint_rect = hint_surface.get_rect(centerx=Settings.SCREEN_WIDTH // 2, bottom=box_y + box_height - 30)
            screen.blit(hint_surface, hint_rect)
        
        # Skip option with better margin
        skip_surface = self.font_hint.render("Press ESC to skip tutorial", True, (80, 90, 110))
        screen.blit(skip_surface, (box_x + 25, box_y + box_height - 35))
        
        # Step indicator dots with improved spacing
        steps = [s for s in TutorialStep if s != TutorialStep.COMPLETE]
        dot_y = box_y + box_height + 30  # Better gap from box
        dot_spacing = 24  # Increased spacing between dots
        dot_x_start = Settings.SCREEN_WIDTH // 2 - (len(steps) * dot_spacing) // 2 + dot_spacing // 2
        
        for i, step in enumerate(steps):
            dx = dot_x_start + i * dot_spacing
            if step == self.current_step:
                pygame.draw.circle(screen, glow_color, (dx, dot_y), 7)  # Slightly larger
            else:
                pygame.draw.circle(screen, (60, 70, 90), (dx, dot_y), 5)


class ControlsDisplay:
    """
    On-screen controls display during gameplay.
    
    Shows current control bindings in a sleek, non-intrusive way.
    """
    
    def __init__(self):
        pygame.font.init()
        self.font_key = pygame.font.SysFont('Consolas', 16, bold=True)
        self.font_desc = pygame.font.SysFont('Segoe UI', 14)
        
        # Animation
        self._time = 0.0
        self.visible = True
        self.alpha = 200
        
        # Position (bottom-right corner with better margins)
        self.x = Settings.SCREEN_WIDTH - 190
        self.y = Settings.SCREEN_HEIGHT - 190
        
        # Controls to display
        self.controls = [
            ('WASD', 'Move'),
            ('SPACE', 'Freeze Time'),
            ('Q', 'Place Anchor'),
            ('E', 'Recall'),
            ('ESC', 'Pause')
        ]
    
    def update(self, dt: float) -> None:
        self._time += dt
    
    def toggle(self) -> None:
        self.visible = not self.visible
    
    def render(self, screen: pygame.Surface) -> None:
        if not self.visible:
            return
        
        # Background panel with improved dimensions
        panel_width = 175
        panel_height = 175
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        
        # Gradient background
        for y in range(panel_height):
            alpha = int(self.alpha * (0.3 + 0.7 * (y / panel_height)))
            pygame.draw.line(panel, (15, 20, 30, alpha), (0, y), (panel_width, y))
        
        # Border
        pygame.draw.rect(panel, (60, 80, 120), (0, 0, panel_width, panel_height), 
                        width=1, border_radius=8)
        
        # Title with better padding
        title = self.font_desc.render("CONTROLS", True, (100, 130, 180))
        panel.blit(title, (12, 10))
        
        # Separator with better margins
        pygame.draw.line(panel, (60, 80, 120), (12, 32), (panel_width - 12, 32))
        
        # Controls list with improved spacing
        y_offset = 42
        item_spacing = 26
        for key, desc in self.controls:
            # Key box with better size
            key_surf = self.font_key.render(key, True, (180, 200, 255))
            key_rect = pygame.Rect(12, y_offset, 58, 22)
            pygame.draw.rect(panel, (40, 50, 70), key_rect, border_radius=3)
            pygame.draw.rect(panel, (80, 100, 140), key_rect, width=1, border_radius=3)
            
            # Center key text
            key_text_rect = key_surf.get_rect(center=key_rect.center)
            panel.blit(key_surf, key_text_rect)
            
            # Description with better alignment
            desc_surf = self.font_desc.render(desc, True, (150, 160, 180))
            panel.blit(desc_surf, (75, y_offset + 3))
            
            y_offset += item_spacing
        
        screen.blit(panel, (self.x, self.y))


class GameTips:
    """Rotating tips displayed during loading or pause."""
    
    TIPS = [
        "💡 Freezing time accrues debt at 1.5x rate",
        "💡 Higher debt = faster enemies when unfrozen",
        "💡 Temporal Hunters ONLY move during freeze!",
        "💡 Green crystals absorb your debt",
        "💡 Place anchors before dangerous sections",
        "💡 Recalling to anchors costs 2s of debt",
        "💡 Watch your debt tier - it affects everything",
        "💡 Plan your route during freeze time",
        "💡 Debt Shadows spawn when debt exceeds 12s",
        "💡 The exit glows green - reach it to win!"
    ]
    
    def __init__(self):
        pygame.font.init()
        self.font = pygame.font.SysFont('Segoe UI', 20)
        self.current_tip = 0
        self._timer = 0.0
        self._change_interval = 5.0
    
    def update(self, dt: float) -> None:
        self._timer += dt
        if self._timer >= self._change_interval:
            self._timer = 0
            self.current_tip = (self.current_tip + 1) % len(self.TIPS)
    
    def get_current_tip(self) -> str:
        return self.TIPS[self.current_tip]
    
    def render(self, screen: pygame.Surface, y: int) -> None:
        tip = self.get_current_tip()
        tip_surface = self.font.render(tip, True, (140, 160, 200))
        tip_rect = tip_surface.get_rect(centerx=Settings.SCREEN_WIDTH // 2, top=y)
        screen.blit(tip_surface, tip_rect)
