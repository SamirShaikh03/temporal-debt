"""
HUD - Heads-Up Display for in-game information.

The HUD communicates critical game state to the player:
- Current debt level and tier
- Time freeze status
- Anchor status
- Level information

Design Philosophy:
- Clarity over beauty
- Progressive disclosure (more info at higher stakes)
- Non-intrusive until needed
"""

import pygame
import math


from ..core.settings import Settings, COLORS
from ..core.utils import lerp, get_font


class HUD:
    """
    In-game heads-up display.
    
    Renders all UI elements during gameplay:
    - Debt meter with tier indication
    - Time freeze indicator
    - Anchor status
    - Level info
    """
    
    def __init__(self):
        """Initialize the HUD."""
        # Fonts
        pygame.font.init()
        self.font_large = get_font('Arial', 32, bold=True)
        self.font_medium = get_font('Arial', 24)
        self.font_small = get_font('Arial', 18)
        
        # State references (set externally)
        self._debt_manager = None
        self._time_engine = None
        self._anchor_system = None
        self._level_manager = None
        
        # Animation state
        self._debt_display = 0.0  # Smoothed debt for display
        self._freeze_flash = 0.0
        self._warning_pulse = 0.0
        
        # Layout
        self.margin = 20
        self.bar_height = 30
        self.bar_width = 300
        
        # V2.0 Data
        self._v2_data = {
            'momentum': 0,
            'max_momentum': 10,
            'resonance_progress': 0,
            'resonance_state': 'idle',
            'clone_cooldown': 0,
            'clone_recording': False,
            'reversal_available': False,
            'reversal_uses': 0,
            'fragments_collected': 0,
            'fragment_energy': 0,
            'burst_ready': False,
            'burst_active': False,
        }
        
        # V2 Animation state
        self._momentum_display = 0.0
        self._fragment_pulse = 0.0
    
    def set_systems(self, debt_manager, time_engine, anchor_system, level_manager):
        """Set system references."""
        self._debt_manager = debt_manager
        self._time_engine = time_engine
        self._anchor_system = anchor_system
        self._level_manager = level_manager
    
    def set_v2_data(self, data: dict) -> None:
        """Set V2.0 system data for display."""
        self._v2_data.update(data)
    
    def update(self, dt: float) -> None:
        """Update HUD animations."""
        # Smooth debt display
        if self._debt_manager:
            target_debt = self._debt_manager.current_debt
            self._debt_display = lerp(self._debt_display, target_debt, dt * 5)
        
        # Freeze flash animation
        if self._time_engine and self._time_engine.is_frozen():
            self._freeze_flash += dt * 3
        else:
            self._freeze_flash = 0.0
        
        # Warning pulse for high debt
        if self._debt_manager and self._debt_manager.current_tier >= 3:
            self._warning_pulse += dt * 5
        
        # V2.0 Animation updates
        target_momentum = self._v2_data.get('momentum', 0)
        self._momentum_display = lerp(self._momentum_display, target_momentum, dt * 3)
        
        # Fragment pulse when burst ready
        if self._v2_data.get('burst_ready', False):
            self._fragment_pulse += dt * 4
        else:
            self._fragment_pulse = 0.0
    
    def render(self, screen: pygame.Surface) -> None:
        """
        Render the HUD.
        
        Args:
            screen: Surface to render to
        """
        # Debt meter (top left)
        self._render_debt_meter(screen)
        
        # Time freeze indicator (top center)
        self._render_freeze_indicator(screen)
        
        # Anchor status (top right)
        self._render_anchor_status(screen)
        
        # Level info (bottom left)
        self._render_level_info(screen)
        
        # V2.0 HUD elements
        self._render_momentum_meter(screen)
        self._render_fragment_energy(screen)
        self._render_ability_cooldowns(screen)
        
        # FPS counter (if enabled)
        if Settings.SHOW_FPS:
            self._render_fps(screen)
    
    def _render_debt_meter(self, screen: pygame.Surface) -> None:
        """Render the debt meter."""
        x = self.margin
        y = self.margin
        
        # Background
        bg_rect = pygame.Rect(x, y, self.bar_width, self.bar_height)
        pygame.draw.rect(screen, COLORS.DEBT_BAR_BG, bg_rect)
        
        # Get debt percentage
        if self._debt_manager:
            debt_pct = min(1.0, self._debt_display / Settings.BANKRUPTCY_THRESHOLD)
            tier = self._debt_manager.current_tier
        else:
            debt_pct = 0
            tier = 0
        
        # Fill color based on tier
        tier_colors = [
            COLORS.TIER_CLEAR,
            COLORS.TIER_MILD,
            COLORS.TIER_MODERATE,
            COLORS.TIER_SEVERE,
            COLORS.TIER_CRITICAL,
            COLORS.TIER_BANKRUPTCY
        ]
        fill_color = tier_colors[min(tier, len(tier_colors) - 1)]
        
        # Add pulse for warning tiers
        if tier >= 3:
            pulse = (math.sin(self._warning_pulse) + 1) / 2
            fill_color = (
                min(255, fill_color[0] + int(30 * pulse)),
                fill_color[1],
                fill_color[2]
            )
        
        # Fill bar
        fill_width = int(self.bar_width * debt_pct)
        if fill_width > 0:
            fill_rect = pygame.Rect(x, y, fill_width, self.bar_height)
            pygame.draw.rect(screen, fill_color, fill_rect)
        
        # Border
        pygame.draw.rect(screen, COLORS.WHITE, bg_rect, 2)
        
        # Tier markers
        for threshold in [3, 6, 10, 15]:
            marker_x = x + int(self.bar_width * (threshold / Settings.BANKRUPTCY_THRESHOLD))
            pygame.draw.line(screen, COLORS.WHITE, 
                           (marker_x, y), (marker_x, y + self.bar_height), 1)
        
        # Debt text
        if self._debt_manager:
            debt_text = f"DEBT: {self._debt_display:.1f}s"
            tier_name = Settings.DEBT_TIERS[tier]['name'].upper()
            
            text_surface = self.font_small.render(debt_text, True, COLORS.WHITE)
            screen.blit(text_surface, (x + 5, y + 5))
            
            tier_surface = self.font_small.render(tier_name, True, fill_color)
            screen.blit(tier_surface, (x + self.bar_width - tier_surface.get_width() - 5, y + 5))
    
    def _render_freeze_indicator(self, screen: pygame.Surface) -> None:
        """Render time freeze indicator."""
        if not self._time_engine:
            return
        
        center_x = Settings.SCREEN_WIDTH // 2
        y = self.margin
        
        if self._time_engine.is_frozen():
            # Flashing FROZEN text
            flash = int(self._freeze_flash) % 2 == 0
            color = COLORS.WHITE if flash else COLORS.PLAYER_FROZEN
            
            text = "TIME FROZEN"
            text_surface = self.font_large.render(text, True, color)
            text_rect = text_surface.get_rect(centerx=center_x, top=y)
            
            # Background
            bg_rect = text_rect.inflate(20, 10)
            pygame.draw.rect(screen, (*COLORS.FREEZE_TINT[:3], 150), bg_rect)
            pygame.draw.rect(screen, COLORS.WHITE, bg_rect, 2)
            
            screen.blit(text_surface, text_rect)
            
            # Freeze duration
            duration_text = f"+{self._time_engine.freeze_duration:.1f}s"
            duration_surface = self.font_small.render(duration_text, True, COLORS.WHITE)
            duration_rect = duration_surface.get_rect(centerx=center_x, top=text_rect.bottom + 5)
            screen.blit(duration_surface, duration_rect)
        else:
            # Show world speed if accelerated
            if self._time_engine.time_scale > 1.0:
                speed_text = f"TIME: {self._time_engine.time_scale:.1f}x"
                text_surface = self.font_medium.render(speed_text, True, COLORS.TIER_SEVERE)
                text_rect = text_surface.get_rect(centerx=center_x, top=y)
                screen.blit(text_surface, text_rect)
    
    def _render_anchor_status(self, screen: pygame.Surface) -> None:
        """Render anchor status."""
        if not self._anchor_system:
            return
        
        x = Settings.SCREEN_WIDTH - self.margin - 120
        y = self.margin
        
        # Anchor slots
        for i in range(self._anchor_system.max_anchors):
            slot_x = x + i * 40
            slot_rect = pygame.Rect(slot_x, y, 30, 30)
            
            anchor = self._anchor_system.anchors[i]
            
            if anchor:
                # Active anchor
                decay_pct = anchor.get_decay_percentage()
                color = COLORS.ANCHOR
                
                # Fill based on remaining time
                fill_height = int(30 * decay_pct)
                fill_rect = pygame.Rect(slot_x, y + 30 - fill_height, 30, fill_height)
                pygame.draw.rect(screen, color, fill_rect)
            
            # Slot border
            pygame.draw.rect(screen, COLORS.WHITE, slot_rect, 2)
            
            # Slot number
            num_surface = self.font_small.render(str(i + 1), True, COLORS.WHITE)
            num_rect = num_surface.get_rect(center=(slot_x + 15, y + 15))
            screen.blit(num_surface, num_rect)
        
        # Instructions
        instr_text = "Q: Place  E: Recall"
        instr_surface = self.font_small.render(instr_text, True, COLORS.GRAY)
        screen.blit(instr_surface, (x, y + 35))
    
    def _render_level_info(self, screen: pygame.Surface) -> None:
        """Render level information."""
        if not self._level_manager:
            return
        
        info = self._level_manager.get_level_info()
        if not info:
            return
        
        x = self.margin
        y = Settings.SCREEN_HEIGHT - self.margin - 70
        
        # Level name with nice styling
        level_num = info.get('index', 1)
        level_name = info.get('name', 'Unknown')
        
        # Background panel for level info
        panel_width = 350
        panel_height = 60
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel, (15, 20, 35, 180), (0, 0, panel_width, panel_height), border_radius=8)
        pygame.draw.rect(panel, (60, 80, 120), (0, 0, panel_width, panel_height), width=1, border_radius=8)
        screen.blit(panel, (x, y))
        
        # Level name
        name_text = f"LEVEL {level_num}: {level_name}"
        name_surface = self.font_medium.render(name_text, True, (180, 200, 255))
        screen.blit(name_surface, (x + 10, y + 8))
        
        # Time
        time_val = info.get('time', 0)
        time_text = f"⏱ {time_val:.1f}s"
        time_surface = self.font_small.render(time_text, True, (150, 170, 200))
        screen.blit(time_surface, (x + 10, y + 36))
        
        # Level hint (if available)
        hint = info.get('hint', '')
        if hint and time_val < 5.0:  # Only show hint at level start
            hint_alpha = int(255 * max(0, 1 - time_val / 5.0))
            hint_surface = self.font_small.render(hint, True, (hint_alpha, hint_alpha, int(hint_alpha * 0.8)))
            hint_rect = hint_surface.get_rect(centerx=Settings.SCREEN_WIDTH // 2, bottom=Settings.SCREEN_HEIGHT - 40)
            screen.blit(hint_surface, hint_rect)
    
    def _render_fps(self, screen: pygame.Surface) -> None:
        """Render FPS counter."""
        # Would need clock reference for actual FPS
        fps_text = "60 FPS"  # Placeholder
        fps_surface = self.font_small.render(fps_text, True, COLORS.GRAY)
        screen.blit(fps_surface, 
                   (Settings.SCREEN_WIDTH - fps_surface.get_width() - self.margin,
                    Settings.SCREEN_HEIGHT - fps_surface.get_height() - self.margin))
    
    def render_controls(self, screen: pygame.Surface) -> None:
        """Render control hints."""
        x = self.margin
        y = Settings.SCREEN_HEIGHT - 100
        
        controls = [
            "WASD - Move",
            "SPACE (hold) - Freeze Time",
            "Q - Place Anchor",
            "E - Recall to Anchor",
            "ESC - Pause"
        ]
        
        for i, text in enumerate(controls):
            surface = self.font_small.render(text, True, COLORS.GRAY)
            screen.blit(surface, (x, y + i * 20))
    
    # ============================================
    # V2.0 HUD RENDERING
    # ============================================
    
    def _render_momentum_meter(self, screen: pygame.Surface) -> None:
        """Render temporal momentum meter (bottom right, above ability cooldowns)."""
        # Position below anchor status, right side
        x = Settings.SCREEN_WIDTH - self.margin - 160
        y = self.margin + 80
        
        # Momentum bar dimensions
        bar_width = 140
        bar_height = 16
        
        # Background
        bg_rect = pygame.Rect(x, y, bar_width, bar_height)
        pygame.draw.rect(screen, (30, 35, 50), bg_rect, border_radius=3)
        
        # Fill based on momentum
        max_momentum = self._v2_data.get('max_momentum', 10)
        fill_pct = self._momentum_display / max_momentum if max_momentum > 0 else 0
        fill_width = int(bar_width * min(1.0, fill_pct))
        
        if fill_width > 0:
            # Gradient from cyan to gold as momentum builds
            r = int(lerp(80, 255, fill_pct))
            g = int(lerp(200, 215, fill_pct))
            b = int(lerp(255, 80, fill_pct))
            fill_color = (r, g, b)
            
            fill_rect = pygame.Rect(x, y, fill_width, bar_height)
            pygame.draw.rect(screen, fill_color, fill_rect, border_radius=3)
        
        # Border
        pygame.draw.rect(screen, (100, 120, 160), bg_rect, 1, border_radius=3)
        
        # Label
        label = "MOMENTUM"
        label_surface = self.font_small.render(label, True, (150, 170, 200))
        screen.blit(label_surface, (x, y - 18))
        
        # Value text
        value_text = f"{self._momentum_display:.1f}x"
        value_surface = self.font_small.render(value_text, True, (200, 220, 255))
        value_rect = value_surface.get_rect(right=x + bar_width, top=y - 18)
        screen.blit(value_surface, value_rect)
    
    def _render_fragment_energy(self, screen: pygame.Surface) -> None:
        """Render temporal fragment energy display."""
        # Position on right side, below momentum
        x = Settings.SCREEN_WIDTH - self.margin - 160
        y = self.margin + 130
        
        fragments = self._v2_data.get('fragments_collected', 0)
        _energy = self._v2_data.get('fragment_energy', 0)  # Reserved for future use
        burst_ready = self._v2_data.get('burst_ready', False)
        burst_active = self._v2_data.get('burst_active', False)
        
        # Display fragment orbs (max 5)
        orb_radius = 10
        orb_spacing = 28
        
        for i in range(5):
            orb_x = x + i * orb_spacing + orb_radius
            orb_y = y + orb_radius
            
            # Draw orb
            if i < fragments:
                # Collected fragment - glowing
                color = (200, 220, 255)
                if burst_ready:
                    # Pulse when ready
                    pulse = (math.sin(self._fragment_pulse) + 1) / 2
                    glow = int(50 * pulse)
                    pygame.draw.circle(screen, (150 + glow, 180 + glow, 255), 
                                      (orb_x, orb_y), orb_radius + 3)
                pygame.draw.circle(screen, color, (orb_x, orb_y), orb_radius)
            else:
                # Empty slot
                pygame.draw.circle(screen, (40, 50, 70), (orb_x, orb_y), orb_radius)
                pygame.draw.circle(screen, (80, 100, 130), (orb_x, orb_y), orb_radius, 1)
        
        # Label
        if burst_active:
            label = "BURST ACTIVE!"
            label_color = (255, 220, 100)
        elif burst_ready:
            label = "PRESS B - BURST"
            label_color = (200, 255, 200)
        else:
            label = "FRAGMENTS"
            label_color = (150, 170, 200)
        
        label_surface = self.font_small.render(label, True, label_color)
        screen.blit(label_surface, (x, y - 18))
    
    def _render_ability_cooldowns(self, screen: pygame.Surface) -> None:
        """Render V2 ability cooldown indicators."""
        # Position in bottom right corner
        x = Settings.SCREEN_WIDTH - self.margin - 180
        y = Settings.SCREEN_HEIGHT - self.margin - 80
        
        # Panel background
        panel_width = 160
        panel_height = 70
        panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
        pygame.draw.rect(panel, (15, 20, 35, 180), (0, 0, panel_width, panel_height), border_radius=6)
        pygame.draw.rect(panel, (60, 80, 120), (0, 0, panel_width, panel_height), width=1, border_radius=6)
        screen.blit(panel, (x, y))
        
        # Clone ability (C key)
        clone_cooldown = self._v2_data.get('clone_cooldown', 0)
        clone_recording = self._v2_data.get('clone_recording', False)
        
        if clone_recording:
            clone_text = "[C] RECORDING..."
            clone_color = (255, 150, 100)
        elif clone_cooldown > 0:
            clone_text = f"[C] Clone: {clone_cooldown:.1f}s"
            clone_color = (120, 120, 140)
        else:
            clone_text = "[C] Clone Ready"
            clone_color = (120, 255, 180)
        
        clone_surface = self.font_small.render(clone_text, True, clone_color)
        screen.blit(clone_surface, (x + 8, y + 8))
        
        # Rewind ability (R key)
        reversal_available = self._v2_data.get('reversal_available', False)
        reversal_uses = self._v2_data.get('reversal_uses', 0)
        
        if reversal_available:
            rewind_text = f"[R] Rewind ({reversal_uses})"
            rewind_color = (200, 180, 255)
        else:
            rewind_text = "[R] Rewind: USED"
            rewind_color = (80, 80, 100)
        
        rewind_surface = self.font_small.render(rewind_text, True, rewind_color)
        screen.blit(rewind_surface, (x + 8, y + 28))
        
        # Resonance state
        resonance_state = self._v2_data.get('resonance_state', 'idle')
        resonance_progress = self._v2_data.get('resonance_progress', 0)
        
        if resonance_state == 'warning':
            res_text = "⚡ WAVE INCOMING"
            res_color = (255, 200, 100)
        elif resonance_state == 'active':
            res_text = "⚡ WAVE ACTIVE!"
            res_color = (255, 100, 100)
        else:
            res_text = f"⚡ Wave: {int(resonance_progress * 100)}%"
            res_color = (100, 120, 160)
        
        res_surface = self.font_small.render(res_text, True, res_color)
        screen.blit(res_surface, (x + 8, y + 48))
