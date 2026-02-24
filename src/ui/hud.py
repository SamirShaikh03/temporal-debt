"""
HUD - Heads-Up Display for in-game information.

Neon Abyss aesthetic — dark translucent panels with accent glow borders,
color-graded debt meter, and pulsing warning indicators.
"""

import pygame
import math


from ..core.settings import Settings, COLORS
from ..core.utils import lerp, get_font


class HUD:
    """
    In-game heads-up display (Neon Abyss theme).
    """
    
    def __init__(self):
        pygame.font.init()
        self.font_large = get_font('Arial', 32, bold=True)
        self.font_medium = get_font('Arial', 24)
        self.font_small = get_font('Arial', 18)
        self.font_tiny = get_font('Arial', 14)
        
        # System references
        self._debt_manager = None
        self._time_engine = None
        self._anchor_system = None
        self._level_manager = None
        
        # Animation state
        self._debt_display = 0.0
        self._freeze_flash = 0.0
        self._warning_pulse = 0.0
        self._hud_time = 0.0
        
        # Layout
        self.margin = 16
        self.bar_height = 22
        self.bar_width = 280
        
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
        
        self._momentum_display = 0.0
        self._fragment_pulse = 0.0
    
    def set_systems(self, debt_manager, time_engine, anchor_system, level_manager):
        self._debt_manager = debt_manager
        self._time_engine = time_engine
        self._anchor_system = anchor_system
        self._level_manager = level_manager
    
    def set_v2_data(self, data: dict) -> None:
        self._v2_data.update(data)
    
    def update(self, dt: float) -> None:
        self._hud_time += dt
        
        if self._debt_manager:
            target_debt = self._debt_manager.current_debt
            self._debt_display = lerp(self._debt_display, target_debt, dt * 5)
        
        if self._time_engine and self._time_engine.is_frozen():
            self._freeze_flash += dt * 4
        else:
            self._freeze_flash = max(0, self._freeze_flash - dt * 6)
        
        if self._debt_manager and self._debt_manager.current_tier >= 3:
            self._warning_pulse += dt * 6
        else:
            self._warning_pulse = 0.0
        
        target_momentum = self._v2_data.get('momentum', 0)
        self._momentum_display = lerp(self._momentum_display, target_momentum, dt * 3)
        
        if self._v2_data.get('burst_ready', False):
            self._fragment_pulse += dt * 4
        else:
            self._fragment_pulse = 0.0
    
    def render(self, screen: pygame.Surface) -> None:
        self._render_debt_meter(screen)
        self._render_freeze_indicator(screen)
        self._render_anchor_status(screen)
        self._render_level_info(screen)
        self._render_momentum_meter(screen)
        self._render_fragment_energy(screen)
        self._render_ability_cooldowns(screen)
        
        if Settings.SHOW_FPS:
            self._render_fps(screen)
    
    # -- helper --
    def _panel(self, screen, x, y, w, h, border_color=None, alpha=170):
        """Draw a dark translucent panel with an optional accent border."""
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        hud_bg = getattr(COLORS, 'HUD_BACKGROUND', (10, 14, 28))
        pygame.draw.rect(s, (hud_bg[0], hud_bg[1], hud_bg[2], alpha), (0, 0, w, h), border_radius=8)
        screen.blit(s, (x, y))
        bc = border_color or getattr(COLORS, 'HUD_BORDER', (40, 60, 100))
        pygame.draw.rect(screen, bc, (x, y, w, h), width=1, border_radius=8)
    
    def _render_debt_meter(self, screen: pygame.Surface) -> None:
        x = self.margin
        y = self.margin
        
        # Panel behind the debt bar
        self._panel(screen, x - 6, y - 6, self.bar_width + 12, self.bar_height + 32)
        
        # Background bar
        bg_rect = pygame.Rect(x, y, self.bar_width, self.bar_height)
        pygame.draw.rect(screen, (18, 22, 36), bg_rect, border_radius=4)
        
        if self._debt_manager:
            debt_pct = min(1.0, self._debt_display / Settings.BANKRUPTCY_THRESHOLD)
            tier = self._debt_manager.current_tier
        else:
            debt_pct = 0
            tier = 0
        
        # Tier color gradient
        tier_colors = [
            getattr(COLORS, 'TIER_CLEAR', (80, 200, 120)),
            getattr(COLORS, 'TIER_MILD', (120, 200, 80)),
            getattr(COLORS, 'TIER_MODERATE', (200, 200, 60)),
            getattr(COLORS, 'TIER_SEVERE', (220, 140, 40)),
            getattr(COLORS, 'TIER_CRITICAL', (255, 60, 60)),
            getattr(COLORS, 'TIER_BANKRUPTCY', (200, 30, 80)),
        ]
        fill_color = tier_colors[min(tier, len(tier_colors) - 1)]
        
        if tier >= 3:
            pulse = (math.sin(self._warning_pulse) + 1) / 2
            fill_color = (
                min(255, fill_color[0] + int(40 * pulse)),
                max(0, fill_color[1] - int(20 * pulse)),
                fill_color[2],
            )
        
        fill_width = int(self.bar_width * debt_pct)
        if fill_width > 0:
            fill_rect = pygame.Rect(x, y, fill_width, self.bar_height)
            pygame.draw.rect(screen, fill_color, fill_rect, border_radius=4)
            # Glow shimmer on leading edge
            edge_surf = pygame.Surface((4, self.bar_height), pygame.SRCALPHA)
            edge_surf.fill((*fill_color, 120))
            screen.blit(edge_surf, (x + fill_width - 2, y))
        
        # Thin accent border on bar
        pygame.draw.rect(screen, (*fill_color, 180) if fill_width > 0 else (50, 60, 80),
                        bg_rect, 1, border_radius=4)
        
        # Tier threshold markers
        for threshold in [3, 6, 10, 15]:
            marker_x = x + int(self.bar_width * (threshold / Settings.BANKRUPTCY_THRESHOLD))
            pygame.draw.line(screen, (60, 70, 100), (marker_x, y + 2), (marker_x, y + self.bar_height - 2), 1)
        
        # Debt text (below bar)
        if self._debt_manager:
            debt_text = f"DEBT {self._debt_display:.1f}s"
            tier_name = Settings.DEBT_TIERS[tier]['name'].upper()
            
            text_surface = self.font_tiny.render(debt_text, True, (160, 170, 200))
            screen.blit(text_surface, (x + 2, y + self.bar_height + 4))
            
            tier_surface = self.font_tiny.render(tier_name, True, fill_color)
            screen.blit(tier_surface, (x + self.bar_width - tier_surface.get_width() - 2, y + self.bar_height + 4))
    
    def _render_freeze_indicator(self, screen: pygame.Surface) -> None:
        if not self._time_engine:
            return
        
        center_x = Settings.SCREEN_WIDTH // 2
        y = self.margin
        accent = getattr(COLORS, 'MENU_ACCENT', (0, 200, 255))
        
        if self._time_engine.is_frozen():
            flash = (math.sin(self._freeze_flash * 3) + 1) / 2
            color = (
                int(accent[0] * 0.5 + 255 * 0.5 * flash),
                int(min(255, accent[1] + 40 * flash)),
                int(min(255, accent[2] + 20 * flash)),
            )
            
            text = "TIME FROZEN"
            text_surface = self.font_large.render(text, True, color)
            text_rect = text_surface.get_rect(centerx=center_x, top=y)
            
            bg_rect = text_rect.inflate(24, 12)
            self._panel(screen, bg_rect.x, bg_rect.y, bg_rect.width, bg_rect.height,
                       border_color=color, alpha=190)
            
            screen.blit(text_surface, text_rect)
            
            duration_text = f"+{self._time_engine.freeze_duration:.1f}s"
            duration_surface = self.font_small.render(duration_text, True, (180, 200, 240))
            duration_rect = duration_surface.get_rect(centerx=center_x, top=text_rect.bottom + 6)
            screen.blit(duration_surface, duration_rect)
        else:
            if self._time_engine.time_scale > 1.0:
                speed_text = f"TIME: {self._time_engine.time_scale:.1f}x"
                sc = getattr(COLORS, 'TIER_SEVERE', (220, 140, 40))
                text_surface = self.font_medium.render(speed_text, True, sc)
                text_rect = text_surface.get_rect(centerx=center_x, top=y)
                screen.blit(text_surface, text_rect)
    
    def _render_anchor_status(self, screen: pygame.Surface) -> None:
        if not self._anchor_system:
            return
        
        slot_size = 28
        slot_gap = 8
        num = self._anchor_system.max_anchors
        total_w = num * slot_size + (num - 1) * slot_gap
        x_start = Settings.SCREEN_WIDTH - self.margin - total_w
        y = self.margin
        
        # Panel behind anchors
        self._panel(screen, x_start - 8, y - 6, total_w + 16, slot_size + 30)
        
        accent = getattr(COLORS, 'ANCHOR', (0, 200, 200))
        
        for i in range(num):
            sx = x_start + i * (slot_size + slot_gap)
            slot_rect = pygame.Rect(sx, y, slot_size, slot_size)
            
            anchor = self._anchor_system.anchors[i]
            
            if anchor:
                decay_pct = anchor.get_decay_percentage()
                fill_h = int(slot_size * decay_pct)
                fill_rect = pygame.Rect(sx, y + slot_size - fill_h, slot_size, fill_h)
                
                # Color fades from accent to dim as it decays
                a_col = (
                    int(accent[0] * decay_pct),
                    int(accent[1] * decay_pct),
                    int(accent[2] * decay_pct),
                )
                pygame.draw.rect(screen, a_col, fill_rect, border_radius=4)
            
            pygame.draw.rect(screen, (50, 60, 90), slot_rect, 1, border_radius=4)
            
            num_surface = self.font_tiny.render(str(i + 1), True, (100, 110, 140))
            num_rect = num_surface.get_rect(center=(sx + slot_size // 2, y + slot_size // 2))
            screen.blit(num_surface, num_rect)
        
        instr_text = "Q: Place  E: Recall"
        instr_surface = self.font_tiny.render(instr_text, True, (80, 90, 120))
        screen.blit(instr_surface, (x_start, y + slot_size + 4))
    
    def _render_level_info(self, screen: pygame.Surface) -> None:
        if not self._level_manager:
            return
        
        info = self._level_manager.get_level_info()
        if not info:
            return
        
        x = self.margin
        y = Settings.SCREEN_HEIGHT - self.margin - 62
        
        level_num = info.get('index', 1)
        level_name = info.get('name', 'Unknown')
        
        panel_w = 320
        panel_h = 52
        self._panel(screen, x, y, panel_w, panel_h)
        
        accent = getattr(COLORS, 'MENU_ACCENT', (0, 200, 255))
        name_text = f"LEVEL {level_num}: {level_name}"
        name_surface = self.font_medium.render(name_text, True, accent)
        screen.blit(name_surface, (x + 10, y + 6))
        
        time_val = info.get('time', 0)
        time_text = f"{time_val:.1f}s"
        time_surface = self.font_tiny.render(time_text, True, (120, 140, 170))
        screen.blit(time_surface, (x + 10, y + 32))
        
        hint = info.get('hint', '')
        if hint and time_val < 5.0:
            hint_alpha = int(200 * max(0, 1 - time_val / 5.0))
            hint_surface = self.font_small.render(hint, True, (hint_alpha, hint_alpha, int(hint_alpha * 0.7)))
            hint_rect = hint_surface.get_rect(centerx=Settings.SCREEN_WIDTH // 2, bottom=Settings.SCREEN_HEIGHT - 40)
            screen.blit(hint_surface, hint_rect)
    
    def _render_fps(self, screen: pygame.Surface) -> None:
        fps_text = "60 FPS"
        fps_surface = self.font_tiny.render(fps_text, True, (60, 70, 90))
        screen.blit(fps_surface, 
                   (Settings.SCREEN_WIDTH - fps_surface.get_width() - self.margin,
                    Settings.SCREEN_HEIGHT - fps_surface.get_height() - self.margin))
    
    def render_controls(self, screen: pygame.Surface) -> None:
        x = self.margin
        y = Settings.SCREEN_HEIGHT - 100
        
        controls = [
            "WASD - Move",
            "SPACE - Freeze Time",
            "Q / E - Anchor",
            "ESC - Pause",
        ]
        for i, text in enumerate(controls):
            surface = self.font_tiny.render(text, True, (70, 80, 100))
            screen.blit(surface, (x, y + i * 18))
    
    # ============================================
    # V2.0 HUD RENDERING
    # ============================================
    
    def _render_momentum_meter(self, screen: pygame.Surface) -> None:
        x = Settings.SCREEN_WIDTH - self.margin - 160
        y = self.margin + 72
        
        bar_width = 140
        bar_height = 14
        
        self._panel(screen, x - 6, y - 22, bar_width + 12, bar_height + 28)
        
        bg_rect = pygame.Rect(x, y, bar_width, bar_height)
        pygame.draw.rect(screen, (18, 22, 36), bg_rect, border_radius=3)
        
        max_momentum = self._v2_data.get('max_momentum', 10)
        fill_pct = self._momentum_display / max_momentum if max_momentum > 0 else 0
        fill_width = int(bar_width * min(1.0, fill_pct))
        
        if fill_width > 0:
            r = int(lerp(0, 255, fill_pct))
            g = int(lerp(200, 200, fill_pct))
            b = int(lerp(255, 80, fill_pct))
            fill_color = (r, g, b)
            fill_rect = pygame.Rect(x, y, fill_width, bar_height)
            pygame.draw.rect(screen, fill_color, fill_rect, border_radius=3)
        
        pygame.draw.rect(screen, (50, 60, 90), bg_rect, 1, border_radius=3)
        
        label_surface = self.font_tiny.render("MOMENTUM", True, (100, 110, 140))
        screen.blit(label_surface, (x, y - 16))
        
        value_text = f"{self._momentum_display:.1f}x"
        value_surface = self.font_tiny.render(value_text, True, (180, 200, 240))
        value_rect = value_surface.get_rect(right=x + bar_width, top=y - 16)
        screen.blit(value_surface, value_rect)
    
    def _render_fragment_energy(self, screen: pygame.Surface) -> None:
        x = Settings.SCREEN_WIDTH - self.margin - 160
        y = self.margin + 118
        
        fragments = self._v2_data.get('fragments_collected', 0)
        burst_ready = self._v2_data.get('burst_ready', False)
        burst_active = self._v2_data.get('burst_active', False)
        
        orb_radius = 8
        orb_spacing = 24
        total_w = 5 * orb_spacing
        self._panel(screen, x - 6, y - 20, total_w + 12, orb_radius * 2 + 28)
        
        accent = getattr(COLORS, 'MENU_ACCENT', (0, 200, 255))
        accent2 = getattr(COLORS, 'MENU_ACCENT2', (220, 50, 255))
        
        for i in range(5):
            ox = x + i * orb_spacing + orb_radius
            oy = y + orb_radius
            
            if i < fragments:
                color = accent if not burst_ready else accent2
                if burst_ready:
                    pulse = (math.sin(self._fragment_pulse + i * 0.5) + 1) / 2
                    glow_r = orb_radius + 2 + int(3 * pulse)
                    glow_col = (*accent2, int(80 * pulse))
                    glow_surf = pygame.Surface((glow_r * 2 + 2, glow_r * 2 + 2), pygame.SRCALPHA)
                    pygame.draw.circle(glow_surf, glow_col, (glow_r + 1, glow_r + 1), glow_r)
                    screen.blit(glow_surf, (ox - glow_r - 1, oy - glow_r - 1))
                pygame.draw.circle(screen, color, (ox, oy), orb_radius)
            else:
                pygame.draw.circle(screen, (24, 28, 44), (ox, oy), orb_radius)
                pygame.draw.circle(screen, (50, 60, 80), (ox, oy), orb_radius, 1)
        
        if burst_active:
            label = "BURST ACTIVE!"
            label_color = (255, 200, 80)
        elif burst_ready:
            label = "PRESS B - BURST"
            label_color = accent2
        else:
            label = "FRAGMENTS"
            label_color = (100, 110, 140)
        
        label_surface = self.font_tiny.render(label, True, label_color)
        screen.blit(label_surface, (x, y - 16))
    
    def _render_ability_cooldowns(self, screen: pygame.Surface) -> None:
        x = Settings.SCREEN_WIDTH - self.margin - 180
        y = Settings.SCREEN_HEIGHT - self.margin - 75
        
        panel_w = 160
        panel_h = 66
        self._panel(screen, x, y, panel_w, panel_h)
        
        accent = getattr(COLORS, 'MENU_ACCENT', (0, 200, 255))
        
        # Clone
        clone_cd = self._v2_data.get('clone_cooldown', 0)
        clone_rec = self._v2_data.get('clone_recording', False)
        
        if clone_rec:
            ct = "[C] RECORDING..."
            cc = (255, 140, 80)
        elif clone_cd > 0:
            ct = f"[C] Clone: {clone_cd:.1f}s"
            cc = (80, 85, 110)
        else:
            ct = "[C] Clone Ready"
            cc = accent
        
        screen.blit(self.font_tiny.render(ct, True, cc), (x + 8, y + 6))
        
        # Rewind
        rev_avail = self._v2_data.get('reversal_available', False)
        rev_uses = self._v2_data.get('reversal_uses', 0)
        
        if rev_avail:
            rt = f"[R] Rewind ({rev_uses})"
            rc = getattr(COLORS, 'MENU_ACCENT2', (220, 50, 255))
        else:
            rt = "[R] Rewind: USED"
            rc = (60, 60, 80)
        
        screen.blit(self.font_tiny.render(rt, True, rc), (x + 8, y + 24))
        
        # Resonance
        res_state = self._v2_data.get('resonance_state', 'idle')
        res_prog = self._v2_data.get('resonance_progress', 0)
        
        if res_state == 'warning':
            rs_t = "WAVE INCOMING"
            rs_c = (255, 190, 60)
        elif res_state == 'active':
            rs_t = "WAVE ACTIVE!"
            rs_c = (255, 70, 70)
        else:
            rs_t = f"Wave: {int(res_prog * 100)}%"
            rs_c = (80, 90, 120)
        
        screen.blit(self.font_tiny.render(rs_t, True, rs_c), (x + 8, y + 44))
