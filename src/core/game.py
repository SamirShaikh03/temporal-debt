"""
Main Game Class - The core game loop and state management.

This is the orchestrator that brings all systems together.
It manages the game loop, state transitions, and coordinates
all subsystems.

Design Philosophy:
- Clean separation of concerns
- State machine for game flow
- Fixed timestep for consistent physics
"""

import pygame
from enum import Enum, auto
from typing import Optional

from .settings import Settings, COLORS
from .events import GameEvent, get_event_manager, reset_event_manager
from .utils import Vector2

from ..systems.time_engine import TimeEngine
from ..systems.debt_manager import DebtManager
from ..systems.echo_system import EchoSystem
from ..systems.anchor_system import AnchorSystem

from ..levels.level_manager import LevelManager

from ..ui.hud import HUD
from ..ui.menus import MainMenu, PauseMenu, GameOverScreen, VictoryScreen
from ..ui.feedback import ScreenEffects, ParticleSystem
from ..ui.tutorial import TutorialOverlay, ControlsDisplay, GameTips


class GameState(Enum):
    """Game state machine states."""
    MAIN_MENU = auto()
    TUTORIAL = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    VICTORY = auto()
    LEVEL_TRANSITION = auto()


class Game:
    """
    Main game class that orchestrates everything.
    
    Responsibilities:
    - Initialize pygame and subsystems
    - Run the main game loop
    - Handle state transitions
    - Coordinate updates and rendering
    """
    
    def __init__(self):
        """Initialize the game."""
        # Initialize pygame
        pygame.init()
        pygame.mixer.init()
        pygame.display.set_caption(Settings.TITLE)
        
        # Create display with double buffering
        self.screen = pygame.display.set_mode(
            (Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT),
            pygame.DOUBLEBUF
        )
        self.clock = pygame.time.Clock()
        
        # Create game surface for effects
        self.game_surface = pygame.Surface(
            (Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT)
        )
        
        # Game state
        self.running = True
        self.state = GameState.MAIN_MENU
        
        # Event system
        reset_event_manager()
        self.event_manager = get_event_manager()
        self._subscribe_to_events()
        
        # Core systems (initialized when game starts)
        self.time_engine: Optional[TimeEngine] = None
        self.debt_manager: Optional[DebtManager] = None
        self.echo_system: Optional[EchoSystem] = None
        self.anchor_system: Optional[AnchorSystem] = None
        
        # Level management
        self.level_manager: Optional[LevelManager] = None
        
        # UI
        self.hud: Optional[HUD] = None
        self.main_menu = MainMenu()
        self.pause_menu = PauseMenu()
        self.game_over_screen = GameOverScreen()
        self.victory_screen = VictoryScreen()
        
        # Effects
        self.screen_effects = ScreenEffects()
        self.particles = ParticleSystem()
        
        # Tutorial & Controls Display
        self.tutorial = TutorialOverlay()
        self.controls_display = ControlsDisplay()
        self.game_tips = GameTips()
        self.show_tutorial = True  # Flag for first-time players
        
        # Tracking
        self.total_play_time = 0.0
        self.total_debt_incurred = 0.0
        self._death_timer = 0.0
        self._transition_timer = 0.0
        self._freeze_hold_time = 0.0  # Track how long freeze is held
        
        # Input state
        self._space_held = False
        self._last_keys = None
        self._player_has_moved = False
    
    def _subscribe_to_events(self) -> None:
        """Subscribe to game events."""
        self.event_manager.subscribe(GameEvent.PLAYER_DIED, self._on_player_died)
        self.event_manager.subscribe(GameEvent.LEVEL_COMPLETED, self._on_level_completed)
        self.event_manager.subscribe(GameEvent.DEBT_TIER_CHANGED, self._on_debt_tier_changed)
        self.event_manager.subscribe(GameEvent.BANKRUPTCY_STARTED, self._on_bankruptcy)
        self.event_manager.subscribe(GameEvent.TIME_FROZEN, self._on_time_frozen)
        self.event_manager.subscribe(GameEvent.TIME_UNFROZEN, self._on_time_unfrozen)
    
    def _on_player_died(self, event_data) -> None:
        """Handle player death event."""
        pos = event_data.data.get('position', (Settings.SCREEN_WIDTH // 2, Settings.SCREEN_HEIGHT // 2))
        self.screen_effects.flash(COLORS.TIER_BANKRUPTCY, 200)
        self.screen_effects.trigger_shake(15)
        self.particles.emit(
            Vector2(pos[0], pos[1]),
            count=40,
            color=COLORS.DRONE,
            speed=150,
            lifetime=1.0
        )
        self._death_timer = 1.5
    
    def _on_level_completed(self, _event_data) -> None:
        """Handle level completion event."""
        self.screen_effects.flash(COLORS.EXIT_ZONE, 150)
        
        # Update victory screen
        if self.level_manager:
            level_info = self.level_manager.get_level_info()
            is_final = not self.level_manager.has_next_level()
            
            self.victory_screen.set_stats(
                level_name=level_info.get('name', 'Unknown'),
                time=level_info.get('time', 0),
                debt=self.total_debt_incurred,
                is_final=is_final
            )
        
        self.state = GameState.VICTORY
    
    def _on_debt_tier_changed(self, event_data) -> None:
        """Handle debt tier change."""
        new_tier = event_data.data.get('new_tier', 0)
        self.screen_effects.set_debt_tier(new_tier)
        
        if new_tier >= 3:
            self.screen_effects.trigger_shake(new_tier * 2)
    
    def _on_bankruptcy(self, _event_data) -> None:
        """Handle bankruptcy event."""
        self.screen_effects.flash(COLORS.TIER_BANKRUPTCY, 300)
        self.screen_effects.trigger_shake(25)
    
    def _on_time_frozen(self, _event_data) -> None:
        """Handle time freeze start."""
        self.screen_effects.set_freeze_active(True)
    
    def _on_time_unfrozen(self, _event_data) -> None:
        """Handle time unfreeze."""
        self.screen_effects.set_freeze_active(False)
    
    def _init_game_systems(self) -> None:
        """Initialize game systems for a new game."""
        # Reset event manager
        reset_event_manager()
        self.event_manager = get_event_manager()
        self._subscribe_to_events()
        
        # Create debt manager first (time engine needs it)
        self.debt_manager = DebtManager(self.event_manager)
        
        # Create time engine with debt manager
        self.time_engine = TimeEngine(self.debt_manager, self.event_manager)
        
        # Link time engine to debt manager
        self.debt_manager.set_time_engine(self.time_engine)
        
        # Create other systems
        self.echo_system = EchoSystem()
        self.anchor_system = AnchorSystem(self.debt_manager, self.event_manager)
        
        # Create level manager
        self.level_manager = LevelManager(self.event_manager)
        self.level_manager.set_systems(self.debt_manager, self.time_engine)
        
        # Create HUD
        self.hud = HUD()
        self.hud.set_systems(
            self.debt_manager,
            self.time_engine,
            self.anchor_system,
            self.level_manager
        )
        
        # Reset tracking
        self.total_play_time = 0.0
        self.total_debt_incurred = 0.0
        self._death_timer = 0.0
        self._space_held = False
        self._freeze_hold_time = 0.0
        self._player_has_moved = False
        
        # Clear particles and effects
        self.particles.clear()
        self.screen_effects.reset()
        
        # Reset tutorial for new game
        self.tutorial = TutorialOverlay()
    
    def start_game(self) -> None:
        """Start a new game."""
        self._init_game_systems()
        self.level_manager.load_level(0)
        
        # Show tutorial for first level
        if self.show_tutorial:
            self.state = GameState.TUTORIAL
        else:
            self.state = GameState.PLAYING
    
    def run(self) -> None:
        """Main game loop."""
        while self.running:
            # Calculate delta time
            dt = self.clock.tick(Settings.FPS) / 1000.0
            dt = min(dt, 0.1)  # Cap dt to prevent spiral of death
            
            # Handle events
            self._handle_events()
            
            # Update based on state
            self._update(dt)
            
            # Render
            self._render()
            
            # Update display
            pygame.display.flip()
        
        pygame.quit()
    
    def _handle_events(self) -> None:
        """Process pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return
            
            # Route events based on state
            if self.state == GameState.MAIN_MENU:
                self._handle_menu_event(event, self.main_menu)
            
            elif self.state == GameState.TUTORIAL:
                self._handle_tutorial_event(event)
            
            elif self.state == GameState.PLAYING:
                self._handle_gameplay_event(event)
            
            elif self.state == GameState.PAUSED:
                self._handle_menu_event(event, self.pause_menu)
            
            elif self.state == GameState.GAME_OVER:
                self._handle_menu_event(event, self.game_over_screen)
            
            elif self.state == GameState.VICTORY:
                self._handle_menu_event(event, self.victory_screen)
    
    def _handle_menu_event(self, event: pygame.event.Event, menu) -> None:
        """Handle events in menu states."""
        result = menu.handle_input(event)
        
        if result == "start":
            self.start_game()
        elif result == "quit":
            self.running = False
        elif result == "resume":
            self.state = GameState.PLAYING
        elif result == "restart":
            self._restart_level()
        elif result == "restart_game":
            self.start_game()
        elif result == "main_menu":
            self.state = GameState.MAIN_MENU
        elif result == "next_level":
            self._next_level()
    
    def _handle_tutorial_event(self, event: pygame.event.Event) -> None:
        """Handle events during tutorial."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                # Skip tutorial
                self.tutorial.skip()
                self.state = GameState.PLAYING
            else:
                # Let tutorial handle input
                self.tutorial.handle_input(event)
        
        # Check if tutorial completed
        if self.tutorial.is_complete():
            self.show_tutorial = False  # Don't show again this session
            self.state = GameState.PLAYING
    
    def _handle_gameplay_event(self, event: pygame.event.Event) -> None:
        """Handle events during gameplay."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state = GameState.PAUSED
            
            elif event.key == pygame.K_q:
                # Place anchor
                if self.anchor_system and self.level_manager and self.level_manager.player:
                    success = self.anchor_system.place_anchor(
                        self.level_manager.player.center
                    )
                    if success:
                        self.particles.emit(
                            self.level_manager.player.center,
                            count=15,
                            color=COLORS.ANCHOR,
                            speed=50,
                            lifetime=0.5
                        )
            
            elif event.key == pygame.K_e:
                # Recall to anchor
                if self.anchor_system and self.level_manager and self.level_manager.player:
                    new_pos = self.anchor_system.recall_to_nearest(
                        self.level_manager.player.center
                    )
                    if new_pos:
                        old_pos = self.level_manager.player.center
                        self.level_manager.player.position = new_pos
                        self.screen_effects.flash(COLORS.ANCHOR, 100)
                        self.particles.emit(old_pos, count=20, color=COLORS.ANCHOR, speed=80)
                        self.particles.emit(new_pos, count=25, color=COLORS.ANCHOR, speed=100)
            
            elif event.key == pygame.K_TAB:
                # Toggle controls display
                self.controls_display.toggle()
            
            elif event.key == pygame.K_r and Settings.DEBUG_MODE:
                self._restart_level()
    
    def _update(self, dt: float) -> None:
        """Update game state."""
        if self.state == GameState.MAIN_MENU:
            self.main_menu.update(dt)
        
        elif self.state == GameState.TUTORIAL:
            self._update_tutorial(dt)
        
        elif self.state == GameState.PLAYING:
            self._update_gameplay(dt)
        
        elif self.state == GameState.PAUSED:
            self.game_tips.update(dt)  # Update tips while paused
        
        elif self.state == GameState.GAME_OVER:
            self.particles.update(dt)
            self.screen_effects.update(dt)
        
        elif self.state == GameState.VICTORY:
            self.screen_effects.update(dt)
        
        # Always update screen effects in playing state
        if self.state == GameState.PLAYING:
            self.screen_effects.update(dt)
    
    def _update_tutorial(self, dt: float) -> None:
        """Update tutorial overlay."""
        self.tutorial.update(dt)
        
        # Track player actions for tutorial progression
        keys = pygame.key.get_pressed()
        
        # Check for movement
        if keys[pygame.K_w] or keys[pygame.K_a] or keys[pygame.K_s] or keys[pygame.K_d]:
            if not self._player_has_moved:
                self._player_has_moved = True
                self.tutorial.notify_action('moved')
        
        # Check for freeze (held for 2s)
        if keys[pygame.K_SPACE]:
            self._freeze_hold_time += dt
            if self._freeze_hold_time >= 2.0:
                self.tutorial.notify_action('frozen_2s')
                self._freeze_hold_time = 0
        else:
            self._freeze_hold_time = 0
        
        # Check for anchor placement
        if keys[pygame.K_q]:
            self.tutorial.notify_action('anchor_placed')
        
        # Check if tutorial completed
        if self.tutorial.is_complete():
            self.show_tutorial = False
            self.state = GameState.PLAYING
    
    def _update_gameplay(self, dt: float) -> None:
        """Update gameplay systems."""
        # Check for death timer (delayed game over)
        if self._death_timer > 0:
            self._death_timer -= dt
            self.particles.update(dt)
            if self._death_timer <= 0:
                cause = "Caught by enemy!"
                if self.debt_manager and self.debt_manager.current_debt >= Settings.BANKRUPTCY_THRESHOLD:
                    cause = "Temporal Bankruptcy!"
                self.game_over_screen.set_death_message(cause)
                self.state = GameState.GAME_OVER
            return
        
        # Get current key state
        keys = pygame.key.get_pressed()
        
        # Handle time freeze input (SPACE)
        if keys[pygame.K_SPACE]:
            if self.time_engine and not self.time_engine.is_frozen():
                self.time_engine.freeze()
                self._space_held = True
        else:
            if self.time_engine and self.time_engine.is_frozen() and self._space_held:
                self.time_engine.unfreeze()
                self._space_held = False
        
        # Update time engine
        if self.time_engine:
            self.time_engine.update(dt)
            game_dt = self.time_engine.get_game_dt()
        else:
            game_dt = dt
        
        # Update player input and movement
        if self.level_manager and self.level_manager.player:
            player = self.level_manager.player
            
            # Handle movement input
            player.handle_input(keys)
            
            # Get walls for collision
            walls = self.level_manager.get_wall_rects()
            
            # Player always moves at real time (immune to freeze)
            player.update_with_collision(dt, walls)
        
        # Update level entities
        if self.level_manager:
            self.level_manager.update(dt, game_dt)
        
        # Update echo system during freeze
        if self.time_engine and self.time_engine.is_frozen():
            if self.echo_system and self.level_manager:
                entities_with_prediction = [
                    e for e in self.level_manager.entities
                    if hasattr(e, 'get_predicted_positions')
                ]
                self.echo_system.activate()
                debt = self.debt_manager.current_debt if self.debt_manager else 0
                self.echo_system.update(entities_with_prediction, debt)
        else:
            if self.echo_system:
                self.echo_system.deactivate()
        
        # Update anchor system
        if self.anchor_system:
            self.anchor_system.update(dt)
        
        # Update HUD
        if self.hud:
            self.hud.update(dt)
        
        # Update particles
        self.particles.update(dt)
        
        # Track stats
        self.total_play_time += dt
        if self.debt_manager:
            self.total_debt_incurred = max(self.total_debt_incurred, 
                                           self.debt_manager.total_debt_accrued)
        
        # Check for bankruptcy death
        if self.debt_manager and self.debt_manager.is_bankrupt:
            if self.debt_manager.current_debt > Settings.BANKRUPTCY_THRESHOLD + 5:
                if self.level_manager and self.level_manager.player:
                    self.level_manager.player.die()
    
    def _render(self) -> None:
        """Render the current state."""
        # Clear screen
        self.screen.fill(COLORS.BLACK)
        
        if self.state == GameState.MAIN_MENU:
            self.main_menu.render(self.screen)
        
        elif self.state == GameState.TUTORIAL:
            self._render_gameplay()
            self.tutorial.render(self.screen)
        
        elif self.state == GameState.PLAYING:
            self._render_gameplay()
        
        elif self.state == GameState.PAUSED:
            self._render_gameplay()
            self.pause_menu.render(self.screen)
            # Show tip
            self.game_tips.render(self.screen, Settings.SCREEN_HEIGHT - 100)
        
        elif self.state == GameState.GAME_OVER:
            self._render_gameplay()
            self.game_over_screen.render(self.screen)
        
        elif self.state == GameState.VICTORY:
            self._render_gameplay()
            self.victory_screen.render(self.screen)
    
    def _render_gameplay(self) -> None:
        """Render gameplay state."""
        # Get screen shake offset
        shake = self.screen_effects.get_shake_offset()
        
        # Use game surface for effects
        self.game_surface.fill(COLORS.BLACK)
        
        # Render level (includes tiles, entities, player)
        if self.level_manager:
            self.level_manager.render(self.game_surface)
        
        # Render echoes (during freeze)
        if self.echo_system:
            self.echo_system.render(self.game_surface)
        
        # Render anchors
        if self.anchor_system:
            self.anchor_system.render(self.game_surface)
        
        # Render particles
        self.particles.render(self.game_surface)
        
        # Apply screen effects
        self.screen_effects.render(self.game_surface)
        
        # Blit game surface with shake offset
        offset = (int(shake.x), int(shake.y))
        self.screen.blit(self.game_surface, offset)
        
        # Render HUD on top (not affected by shake)
        if self.hud:
            self.hud.render(self.screen)
    
    def _restart_level(self) -> None:
        """Restart the current level."""
        if self.level_manager:
            self.level_manager.reload_level()
        if self.debt_manager:
            self.debt_manager.reset()
        if self.time_engine:
            self.time_engine.reset()
        if self.anchor_system:
            self.anchor_system.clear_all()
        
        self.particles.clear()
        self.screen_effects.reset()
        self._death_timer = 0
        self._space_held = False
        self.state = GameState.PLAYING
    
    def _next_level(self) -> None:
        """Advance to next level."""
        if self.level_manager and self.level_manager.has_next_level():
            self.level_manager.next_level()
            if self.debt_manager:
                self.debt_manager.reset()
            if self.time_engine:
                self.time_engine.reset()
            if self.anchor_system:
                self.anchor_system.clear_all()
            
            self.particles.clear()
            self.screen_effects.reset()
            self.state = GameState.PLAYING
        else:
            self.state = GameState.MAIN_MENU
