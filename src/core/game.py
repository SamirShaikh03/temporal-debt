"""
Main Game Class - The core game loop and state management.

This is the orchestrator that brings all systems together.
It manages the game loop, state transitions, and coordinates
all subsystems.

Design Philosophy:
- Clean separation of concerns
- State machine for game flow
- Fixed timestep for consistent physics

TEMPORAL DEBT 2.0 - Added new systems:
- Temporal Momentum System
- Resonance Events
- Chrono-Clone System
- Time Reversal System
- Fragment Collection
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

# V2.0 Systems
from ..systems.momentum_system import MomentumSystem
from ..systems.resonance_system import ResonanceSystem
from ..systems.chrono_clone_system import ChronoCloneSystem
from ..systems.time_reversal_system import TimeReversalSystem
from ..systems.audio_manager import AudioManager, SoundType, get_audio_manager

from ..levels.level_manager import LevelManager

from ..ui.hud import HUD
from ..ui.menus import MainMenu, PauseMenu, GameOverScreen, VictoryScreen, ControlsScreen
from ..ui.feedback import ScreenEffects, ParticleSystem
from ..ui.tutorial import TutorialOverlay, ControlsDisplay, GameTips


class GameState(Enum):
    """Game state machine states."""
    MAIN_MENU = auto()
    CONTROLS = auto()
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
    
    TEMPORAL DEBT 2.0:
    - Momentum system rewards not freezing
    - Resonance waves create timing challenges
    - Clone system enables new puzzle strategies
    - Time reversal provides emergency escape
    """
    
    def __init__(self):
        """Initialize the game."""
        # Initialize pygame (safe to call multiple times)
        pygame.init()
        
        # Initialize mixer with error handling (may fail in WASM)
        try:
            pygame.mixer.init()
        except Exception as e:
            print(f"Warning: Audio initialization failed: {e}")
        
        pygame.display.set_caption(Settings.TITLE + " 2.0")
        
        # Get or create display (reuses existing display if already created)
        try:
            self.screen = pygame.display.get_surface()
            if self.screen is None:
                self.screen = pygame.display.set_mode(
                    (Settings.SCREEN_WIDTH, Settings.SCREEN_HEIGHT)
                )
                print(f"Display initialized: {Settings.SCREEN_WIDTH}x{Settings.SCREEN_HEIGHT}")
            else:
                print("Reusing existing display")
        except Exception as e:
            print(f"Error initializing display: {e}")
            raise
        
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
        
        # V2.0 Systems
        self.momentum_system: Optional[MomentumSystem] = None
        self.resonance_system: Optional[ResonanceSystem] = None
        self.clone_system: Optional[ChronoCloneSystem] = None
        self.reversal_system: Optional[TimeReversalSystem] = None
        
        # V2.0 Fragment manager (from interactables_v2)
        self.fragment_manager = None
        
        # Level management
        self.level_manager: Optional[LevelManager] = None
        
        # UI
        self.hud: Optional[HUD] = None
        self.main_menu = MainMenu()
        self.pause_menu = PauseMenu()
        self.game_over_screen = GameOverScreen()
        self.victory_screen = VictoryScreen()
        self.controls_screen = ControlsScreen()
        
        # Effects
        self.screen_effects = ScreenEffects()
        self.particles = ParticleSystem()
        
        # Tutorial & Controls Display
        self.tutorial = TutorialOverlay()
        self.controls_display = ControlsDisplay()
        self.game_tips = GameTips()
        self.show_tutorial = True  # Flag for first-time players
        
        # Audio System
        self.audio: Optional[AudioManager] = None
        try:
            self.audio = get_audio_manager()
        except Exception as e:
            print(f"Warning: Audio system failed to initialize: {e}")
        
        # Tracking
        self.total_play_time = 0.0
        self.total_debt_incurred = 0.0
        self._death_timer = 0.0
        self._transition_timer = 0.0
        self._freeze_hold_time = 0.0  # Track how long freeze is held
        self._pod_sound_cooldown = 0.0  # Cooldown for pod deposit sound
        
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
        if self.audio:
            self.audio.play(SoundType.PLAYER_DEATH)
    
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
        if self.audio:
            self.audio.play(SoundType.LEVEL_COMPLETE)
    
    def _on_debt_tier_changed(self, event_data) -> None:
        """Handle debt tier change."""
        new_tier = event_data.data.get('new_tier', 0)
        self.screen_effects.set_debt_tier(new_tier)
        
        if new_tier >= 3:
            self.screen_effects.trigger_shake(new_tier * 2)
            if self.audio:
                self.audio.play(SoundType.DEBT_WARNING)
    
    def _on_bankruptcy(self, _event_data) -> None:
        """Handle bankruptcy event."""
        self.screen_effects.flash(COLORS.TIER_BANKRUPTCY, 300)
        self.screen_effects.trigger_shake(25)
        if self.audio:
            self.audio.play(SoundType.DEBT_CRITICAL)
    
    def _on_time_frozen(self, _event_data) -> None:
        """Handle time freeze start."""
        self.screen_effects.set_freeze_active(True)
        if self.audio:
            self.audio.play(SoundType.TIME_FREEZE_START)
            self.audio.play(SoundType.TIME_FREEZE_LOOP, volume=0.3, loop=True)
    
    def _on_time_unfrozen(self, _event_data) -> None:
        """Handle time unfreeze."""
        self.screen_effects.set_freeze_active(False)
        if self.audio:
            self.audio.stop(SoundType.TIME_FREEZE_LOOP)
            self.audio.play(SoundType.TIME_FREEZE_END)
    
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
        
        # V2.0 Systems initialization
        self.momentum_system = MomentumSystem(self.event_manager)
        self.resonance_system = ResonanceSystem(self.event_manager)
        self.resonance_system.set_systems(self.time_engine, self.debt_manager)
        self.clone_system = ChronoCloneSystem(self.event_manager)
        self.reversal_system = TimeReversalSystem(self.event_manager)
        self.reversal_system.set_debt_manager(self.debt_manager)
        
        # Import and create fragment manager
        try:
            from ..entities.interactables_v2 import FragmentManager
            self.fragment_manager = FragmentManager()
        except ImportError:
            self.fragment_manager = None
        
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
        
        # Set V2 systems on HUD if available
        if hasattr(self.hud, 'set_v2_systems'):
            self.hud.set_v2_systems(
                self.momentum_system,
                self.resonance_system,
                self.clone_system,
                self.reversal_system,
                self.fragment_manager
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
        """Main game loop - single frame execution for web compatibility."""
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
    
    def cleanup(self) -> None:
        """Cleanup when game ends."""
        if self.audio:
            self.audio.cleanup()
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
            
            elif self.state == GameState.CONTROLS:
                self._handle_menu_event(event, self.controls_screen)
            
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
        
        # Play menu sounds
        if event.type == pygame.KEYDOWN and self.audio:
            if event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_w, pygame.K_s):
                self.audio.play(SoundType.MENU_SELECT, volume=0.5)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE) and result:
                self.audio.play(SoundType.MENU_CONFIRM)
        
        if result == "start":
            self.start_game()
        elif result == "quit":
            self.running = False
        elif result == "controls":
            self.state = GameState.CONTROLS
        elif result == "back":
            self.state = GameState.MAIN_MENU
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
                        if self.audio:
                            self.audio.play(SoundType.ANCHOR_PLACE)
            
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
                        if self.audio:
                            self.audio.play(SoundType.ANCHOR_RECALL)
            
            elif event.key == pygame.K_TAB:
                # Toggle controls display
                self.controls_display.toggle()
            
            # V2.0 Controls
            elif event.key == pygame.K_c:
                # Spawn chrono-clone
                if self.clone_system and self.clone_system.can_spawn_clone:
                    if self.clone_system.spawn_clone():
                        self.screen_effects.flash((150, 200, 255), 80)
                        if self.level_manager and self.level_manager.player:
                            self.particles.emit(
                                self.level_manager.player.center,
                                count=20,
                                color=(150, 200, 255),
                                speed=80,
                                lifetime=0.6
                            )
                        if self.audio:
                            self.audio.play(SoundType.CLONE_SPAWN)
            
            elif event.key == pygame.K_r:
                # Time reversal (V2) or restart level (debug)
                if self.reversal_system and self.reversal_system.can_rewind:
                    snapshot = self.reversal_system.initiate_rewind()
                    if snapshot and self.level_manager and self.level_manager.player:
                        # Restore player position
                        self.level_manager.player.position = snapshot.player_position
                        self.screen_effects.flash((200, 150, 255), 200)
                        if self.audio:
                            self.audio.play(SoundType.REWIND_ACTIVATE)
                elif Settings.DEBUG_MODE:
                    self._restart_level()
            
            elif event.key == pygame.K_b:
                # Activate slow-motion burst from fragments
                if self.fragment_manager and self.fragment_manager.can_burst:
                    if self.fragment_manager.activate_burst():
                        self.screen_effects.flash((200, 220, 255), 150)
                        if self.level_manager and self.level_manager.player:
                            self.particles.emit(
                                self.level_manager.player.center,
                                count=30,
                                color=(200, 220, 255),
                                speed=100,
                                lifetime=0.8
                            )
                        if self.audio:
                            self.audio.play(SoundType.FRAGMENT_BURST)
    
    def _update(self, dt: float) -> None:
        """Update game state."""
        if self.state == GameState.MAIN_MENU:
            self.main_menu.update(dt)
        
        elif self.state == GameState.CONTROLS:
            self.controls_screen.update(dt)
        
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
        
        # ============================================
        # V2.0 SYSTEM UPDATES
        # ============================================
        
        # Determine if player is moving
        player_moving = False
        if self.level_manager and self.level_manager.player:
            player = self.level_manager.player
            player_moving = player.velocity.magnitude() > 0
        
        # Update momentum system
        if self.momentum_system:
            self.momentum_system.update(dt)
            # Apply momentum debt reduction to debt manager
            if self.debt_manager and hasattr(self.debt_manager, 'set_momentum_multiplier'):
                self.debt_manager.set_momentum_multiplier(
                    self.momentum_system.debt_reduction_multiplier
                )
        
        # Update resonance system
        if self.resonance_system:
            self.resonance_system.update(dt, player_moving)
        
        # Update clone system (record player position)
        if self.clone_system and self.level_manager and self.level_manager.player:
            self.clone_system.update(dt, self.level_manager.player.center)
        
        # Update reversal system (record game state)
        if self.reversal_system and self.level_manager and self.level_manager.player:
            player = self.level_manager.player
            debt = self.debt_manager.current_debt if self.debt_manager else 0
            tier = self.debt_manager.current_tier if self.debt_manager else 0
            self.reversal_system.record_state(
                player.position,
                player.velocity,
                self.level_manager.entities,
                debt,
                tier,
                dt
            )
            self.reversal_system.update(dt)
        
        # Update fragment manager
        if self.fragment_manager:
            self.fragment_manager.update(dt)
            # Apply slow-motion effect if burst is active
            if self.fragment_manager.is_burst_active and self.time_engine:
                # Slow down game time during burst (handled in time engine)
                pass
        
        # V2.0 Entity Interactions
        self._update_v2_interactions(dt)
        
        # ============================================
        # DANGER ZONE PUNISHMENT
        # ============================================
        self._update_danger_zone(dt, game_dt)
        
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
    
    def _update_danger_zone(self, dt: float, game_dt: float) -> None:
        """Punish the player while inside a danger zone (hazard tile)."""
        if not self.level_manager or not self.level_manager.player:
            return
        
        player = self.level_manager.player
        player_rect = player.get_rect()
        
        in_danger = False
        
        # Check hazard tiles
        for tile in getattr(self.level_manager, 'get_hazard_rects', lambda: [])():
            if player_rect.colliderect(tile):
                in_danger = True
                break
        
        # Also treat any enemy collision zone as danger
        # (enemies already kill the player via collision, but debt leech drains)
        
        # Toggle flag on player (used for visual effects)
        if hasattr(player, '_in_danger_zone'):
            player._in_danger_zone = in_danger
        
        if in_danger:
            # Slow the player down
            slow = getattr(Settings, 'DANGER_ZONE_SLOW_FACTOR', 0.65)
            if hasattr(player, '_danger_slow_active'):
                player._danger_slow_active = True
            player.velocity = player.velocity * slow
            
            # Accrue extra debt
            if self.debt_manager:
                rate = getattr(Settings, 'DANGER_ZONE_DAMAGE_RATE', 1.5)
                self.debt_manager.accrue_debt(rate * dt)
        else:
            if hasattr(player, '_danger_slow_active'):
                player._danger_slow_active = False

    def _update_v2_interactions(self, dt: float) -> None:
        """Handle V2.0 entity interactions."""
        if not self.level_manager or not self.level_manager.player:
            return
        
        player = self.level_manager.player
        player_rect = player.get_rect()
        
        # Import V2 entities
        try:
            from ..entities.interactables_v2 import TimeDilationZone, TemporalFragment, DebtTransferPod
        except ImportError:
            return
        
        keys = pygame.key.get_pressed()
        
        # Active debt multiplier from dilation zones
        total_multiplier = 1.0
        
        for entity in self.level_manager.entities:
            # Time Dilation Zones
            if isinstance(entity, TimeDilationZone):
                if entity.check_player_inside(player_rect):
                    total_multiplier *= entity.debt_multiplier
                entity.update(dt)
            
            # Temporal Fragments
            elif isinstance(entity, TemporalFragment) and not entity.collected:
                if player_rect.colliderect(entity.get_rect()) and self.debt_manager:
                    result = entity.collect(self.debt_manager)
                    if result['success']:
                        # Add to fragment manager
                        if self.fragment_manager:
                            self.fragment_manager.add_fragment(
                                result['fragment_id'],
                                result['fragment_value']
                            )
                        # Visual feedback
                        self.particles.emit(
                            entity.center,
                            count=20,
                            color=(200, 220, 255),
                            speed=60,
                            lifetime=0.8
                        )
                        self.screen_effects.flash((200, 220, 255), 80)
                        # Audio feedback
                        if self.audio:
                            self.audio.play(SoundType.FRAGMENT_COLLECT)
                entity.update(dt)
            
            # Debt Transfer Pods
            elif isinstance(entity, DebtTransferPod):
                if player_rect.colliderect(entity.get_rect()):
                    # Hold F to deposit debt
                    if keys[pygame.K_f] and self.debt_manager:
                        deposited = entity.deposit_debt(self.debt_manager, dt)
                        if deposited > 0:
                            # Visual feedback
                            self.particles.emit(
                                player.center,
                                count=3,
                                color=(255, 200, 100),
                                speed=30,
                                lifetime=0.3
                            )
                            # Audio feedback (throttled)
                            if self.audio:
                                self._pod_sound_cooldown -= dt
                                if self._pod_sound_cooldown <= 0:
                                    self.audio.play(SoundType.POD_DEPOSIT, volume=0.5)
                                    self._pod_sound_cooldown = 0.2
                    else:
                        entity.stop_deposit()
                else:
                    entity.stop_deposit()
                entity.update(dt)
        
        # Apply combined zone multiplier to debt manager
        # (This would need debt_manager modification to support)
    
    def _render(self) -> None:
        """Render the current state."""
        # Clear screen
        self.screen.fill(COLORS.BLACK)
        
        if self.state == GameState.MAIN_MENU:
            self.main_menu.render(self.screen)
        
        elif self.state == GameState.CONTROLS:
            self.controls_screen.render(self.screen)
        
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
        
        # ============================================
        # V2.0 SYSTEM RENDERING
        # ============================================
        
        # Render chrono clones
        if self.clone_system:
            self.clone_system.render(self.game_surface)
        
        # Render reversal effects
        if self.reversal_system:
            self.reversal_system.render(self.game_surface)
        
        # Render resonance wave effect
        if self.resonance_system:
            self.resonance_system.render(self.game_surface)
        
        # Render particles
        self.particles.render(self.game_surface)
        
        # Apply screen effects
        self.screen_effects.render(self.game_surface)
        
        # Blit game surface with shake offset
        offset = (int(shake.x), int(shake.y))
        self.screen.blit(self.game_surface, offset)
        
        # Render HUD on top (not affected by shake)
        if self.hud:
            # Update HUD with V2 data
            self._update_hud_v2_data()
            self.hud.render(self.screen)
    
    def _update_hud_v2_data(self) -> None:
        """Update HUD with V2.0 system data."""
        if not self.hud:
            return
        
        # Set V2 data on HUD if it supports it
        if hasattr(self.hud, 'set_v2_data'):
            v2_data = {
                'momentum': self.momentum_system.momentum if self.momentum_system else 0,
                'max_momentum': self.momentum_system.MAX_MOMENTUM if self.momentum_system else 10,
                'resonance_progress': self.resonance_system.wave_progress if self.resonance_system else 0,
                'resonance_state': self.resonance_system.phase.name.lower() if self.resonance_system else 'calm',
                'clone_cooldown': self.clone_system.cooldown_remaining if self.clone_system else 0,
                'clone_recording': self.clone_system.is_recording if self.clone_system else False,
                'reversal_available': self.reversal_system.uses_remaining > 0 if self.reversal_system else False,
                'reversal_uses': self.reversal_system.uses_remaining if self.reversal_system else 0,
                'fragments_collected': self.fragment_manager.fragments_collected if self.fragment_manager else 0,
                'fragment_energy': self.fragment_manager.fragment_energy if self.fragment_manager else 0,
                'burst_ready': self.fragment_manager.is_burst_ready if self.fragment_manager else False,
                'burst_active': self.fragment_manager.is_burst_active if self.fragment_manager else False,
            }
            self.hud.set_v2_data(v2_data)
    
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
        
        # Reset V2.0 systems
        if self.momentum_system:
            self.momentum_system.reset()
        if self.resonance_system:
            self.resonance_system.reset()
        if self.clone_system:
            self.clone_system.reset()
        if self.reversal_system:
            self.reversal_system.reset()
        if self.fragment_manager:
            self.fragment_manager.reset()
        
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
            
            # Reset V2.0 systems for new level
            if self.momentum_system:
                self.momentum_system.reset()
            if self.resonance_system:
                self.resonance_system.reset()
            if self.clone_system:
                self.clone_system.reset()
            if self.reversal_system:
                self.reversal_system.reset()
            if self.fragment_manager:
                self.fragment_manager.reset()
            
            self.particles.clear()
            self.screen_effects.reset()
            self.state = GameState.PLAYING
        else:
            self.state = GameState.MAIN_MENU
