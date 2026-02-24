"""
Level Manager - Handles level loading, transitions, and state.

The Level Manager is responsible for:
- Loading level data into playable levels
- Managing level entities
- Handling level completion and transitions
- Tracking player progress

Design Philosophy:
- Clean separation between level data and runtime
- Easy to add checkpoints and save states
- Smooth transitions between levels
"""

from typing import List, Optional, Dict, Any, TYPE_CHECKING
import pygame

from .level_data import Level, LevelData, EntityData, ALL_LEVELS
# Try to use enhanced levels if available
try:
    from .level_data_enhanced import ALL_LEVELS as ENHANCED_LEVELS
    ALL_LEVELS = ENHANCED_LEVELS
except ImportError:
    pass
from .tile import TileGrid
from ..core.settings import Settings
from ..core.utils import Vector2
from ..core.events import EventManager, GameEvent, get_event_manager
from ..entities.player import Player

if TYPE_CHECKING:
    from ..systems.debt_manager import DebtManager
    from ..systems.time_engine import TimeEngine
from ..entities.enemies import PatrolDrone, TemporalHunter, DebtShadow

# New V3 enemies (safe import)
try:
    from ..entities.enemies import PhaseShifter, DebtLeech, SwarmDrone
    _has_v3_enemies = True
except ImportError:
    _has_v3_enemies = False

from ..entities.interactables import DebtSink, DebtBomb, TimedDoor, ExitZone, Checkpoint


class LevelManager:
    """
    Manages level loading, state, and transitions.
    
    Features:
    - Load levels from LevelData
    - Spawn and track entities
    - Handle level completion
    - Manage checkpoints
    """
    
    def __init__(self, event_manager: EventManager = None):
        """
        Initialize the level manager.
        
        Args:
            event_manager: Event system for level events
        """
        self._event_manager = event_manager or get_event_manager()
        
        # Level state
        self.current_level: Optional[Level] = None
        self.current_level_index = 0
        self.levels = ALL_LEVELS
        
        # Tile grid
        self.tile_grid: Optional[TileGrid] = None
        
        # Entities
        self.entities: List[Any] = []
        self.player: Optional[Player] = None
        self.exit_zone: Optional[ExitZone] = None
        self.checkpoints: List[Checkpoint] = []
        
        # References (set externally)
        self._debt_manager = None
        self._time_engine = None
        
        # State
        self.level_complete = False
        self.level_time = 0.0
    
    def set_systems(self, debt_manager: 'DebtManager', time_engine: 'TimeEngine') -> None:
        """Set system references for entities."""
        self._debt_manager = debt_manager
        self._time_engine = time_engine
    
    def load_level(self, index: int) -> bool:
        """
        Load a level by index.
        
        Args:
            index: Level index to load
            
        Returns:
            True if level loaded successfully
        """
        if index < 0 or index >= len(self.levels):
            return False
        
        self.current_level_index = index
        level_data = self.levels[index]
        
        # Create level instance
        self.current_level = Level(level_data)
        
        # Reset state
        self.level_complete = False
        self.level_time = 0.0
        self.entities.clear()
        self.checkpoints.clear()
        
        # Create tile grid
        self._load_tile_grid(level_data)
        
        # Create player
        self._spawn_player(level_data)
        
        # Create exit zone
        self._spawn_exit(level_data)
        
        # Spawn entities from level data
        self._spawn_entities(level_data)
        
        # Spawn checkpoints
        self._spawn_checkpoints(level_data)
        
        # Emit event
        self._event_manager.emit(GameEvent.LEVEL_STARTED, {
            'level_index': index,
            'level_name': level_data.name
        })
        
        return True
    
    def reload_level(self) -> bool:
        """Reload the current level."""
        return self.load_level(self.current_level_index)
    
    def next_level(self) -> bool:
        """
        Advance to the next level.
        
        Returns:
            True if next level exists and loaded
        """
        return self.load_level(self.current_level_index + 1)
    
    def _load_tile_grid(self, level_data: LevelData) -> None:
        """Create tile grid from level data."""
        height = len(level_data.tile_map)
        width = len(level_data.tile_map[0]) if height > 0 else 0
        
        self.tile_grid = TileGrid(width, height)
        self.tile_grid.from_string_map(level_data.tile_map)
    
    def _spawn_player(self, level_data: LevelData) -> None:
        """Spawn player at level spawn point."""
        spawn = level_data.get_spawn_point()
        self.player = Player(spawn, self._event_manager)
        self.player.spawn_position = spawn.copy()
        self.player.last_checkpoint = spawn.copy()
    
    def _spawn_exit(self, level_data: LevelData) -> None:
        """Spawn exit zone."""
        exit_pos = level_data.get_exit_point()
        self.exit_zone = ExitZone(exit_pos)
        self.entities.append(self.exit_zone)
    
    def _spawn_checkpoints(self, level_data: LevelData) -> None:
        """Spawn checkpoint entities."""
        for pos in level_data.get_checkpoints():
            checkpoint = Checkpoint(pos)
            self.checkpoints.append(checkpoint)
            self.entities.append(checkpoint)
    
    def _spawn_entities(self, level_data: LevelData) -> None:
        """Spawn all entities defined in level data."""
        for entity_data in level_data.entities:
            entity = self._create_entity(entity_data)
            if entity:
                self.entities.append(entity)
    
    def _create_entity(self, data: EntityData) -> Optional[Any]:
        """
        Create an entity from EntityData.
        
        Args:
            data: Entity definition
            
        Returns:
            Created entity instance
        """
        position = data.position
        props = data.properties
        
        if data.entity_type == "patrol_drone":
            # Convert grid patrol points to pixels
            patrol_points = []
            for px, py in props.get("patrol_points", []):
                patrol_points.append(Vector2(
                    px * Settings.TILE_SIZE + Settings.TILE_SIZE // 2,
                    py * Settings.TILE_SIZE + Settings.TILE_SIZE // 2
                ))
            
            drone = PatrolDrone(
                position=position,
                patrol_points=patrol_points,
                drone_type=props.get("drone_type", "linear"),
                speed=props.get("speed")
            )
            
            # Set circular orbit params if applicable
            if props.get("drone_type") == "circular":
                drone.orbit_center = Vector2(
                    position.x + Settings.TILE_SIZE // 2,
                    position.y + Settings.TILE_SIZE // 2
                )
                drone.orbit_radius = props.get("orbit_radius", 100)
                drone.orbit_speed = props.get("orbit_speed", 1.0)
            
            return drone
        
        elif data.entity_type == "temporal_hunter":
            hunter = TemporalHunter(
                position=position,
                speed=props.get("speed")
            )
            # Target will be set after player is spawned
            return hunter
        
        elif data.entity_type == "debt_sink":
            sink = DebtSink(
                position=position,
                uses=props.get("uses", 1),
                absorption_amount=props.get("absorption_amount")
            )
            if self._debt_manager:
                sink.set_debt_manager(self._debt_manager)
            return sink
        
        elif data.entity_type == "debt_bomb":
            bomb = DebtBomb(
                position=position,
                trigger_type=props.get("trigger_type", "proximity"),
                payload=props.get("payload"),
                radius=props.get("radius")
            )
            return bomb
        
        elif data.entity_type == "timed_door":
            door = TimedDoor(
                position=position,
                open_duration=props.get("open_duration")
            )
            return door
        
        # V3.0 Enemy Types
        elif data.entity_type == "phase_shifter" and _has_v3_enemies:
            shifter = PhaseShifter(position=position)
            return shifter
        
        elif data.entity_type == "debt_leech" and _has_v3_enemies:
            leech = DebtLeech(position=position)
            return leech
        
        elif data.entity_type == "swarm_drone" and _has_v3_enemies:
            drone = SwarmDrone(
                position=position,
                target=self.player,
            )
            return drone
        
        # V2.0 Entity Types
        elif data.entity_type == "temporal_fragment":
            try:
                from ..entities.interactables_v2 import TemporalFragment
                fragment = TemporalFragment(
                    position=position,
                    fragment_id=props.get("fragment_id", 0)
                )
                return fragment
            except ImportError:
                return None
        
        elif data.entity_type == "dilation_zone":
            try:
                from ..entities.interactables_v2 import TimeDilationZone
                zone = TimeDilationZone(
                    position=position,
                    zone_type=props.get("zone_type", "safe"),
                    width=props.get("width", 128),
                    height=props.get("height", 128)
                )
                return zone
            except ImportError:
                return None
        
        elif data.entity_type == "debt_transfer_pod":
            try:
                from ..entities.interactables_v2 import DebtTransferPod
                pod = DebtTransferPod(
                    position=position,
                    pod_id=props.get("pod_id", 0)
                )
                return pod
            except ImportError:
                return None
        
        return None
    
    def update(self, dt: float, game_dt: float) -> None:
        """
        Update level state.
        
        Args:
            dt: Real delta time
            game_dt: Game delta time (affected by time scale)
        """
        if self.level_complete:
            return
        
        self.level_time += dt
        
        # Update entities
        for entity in self.entities:
            if not entity.active:
                continue
            
            # Different entities update differently
            if isinstance(entity, PatrolDrone):
                entity.update(game_dt)
            elif isinstance(entity, TemporalHunter):
                is_frozen = self._time_engine and self._time_engine.is_frozen()
                entity.update(dt, is_frozen)
            elif isinstance(entity, DebtShadow):
                debt = self._debt_manager.current_debt if self._debt_manager else 0
                entity.update(dt, debt)
            elif _has_v3_enemies and isinstance(entity, PhaseShifter):
                entity.update(dt)
            elif _has_v3_enemies and isinstance(entity, DebtLeech):
                entity.update(dt, self._debt_manager)
            elif _has_v3_enemies and isinstance(entity, SwarmDrone):
                entity.update(dt)
            elif isinstance(entity, DebtBomb):
                player_pos = self.player.center if self.player else None
                explosion = entity.update(game_dt, player_pos)
                if explosion:
                    self._handle_explosion(explosion)
            else:
                entity.update(game_dt)
        
        # Set hunter targets
        for entity in self.entities:
            if isinstance(entity, TemporalHunter) and self.player:
                entity.set_target(self.player)
            elif _has_v3_enemies and isinstance(entity, PhaseShifter) and self.player:
                entity.set_target(self.player)
            elif _has_v3_enemies and isinstance(entity, DebtLeech) and self.player:
                entity.set_target(self.player)
        
        # Check player-exit collision
        if self.player and self.exit_zone:
            if self.player.get_rect().colliderect(self.exit_zone.get_rect()):
                self._complete_level()
        
        # Check checkpoint collisions
        if self.player:
            for checkpoint in self.checkpoints:
                if not checkpoint.is_activated:
                    if self.player.get_rect().colliderect(checkpoint.get_rect()):
                        checkpoint.activate()
                        self.player.set_checkpoint(checkpoint.position)
                        self._event_manager.emit(GameEvent.CHECKPOINT_REACHED, {
                            'position': (checkpoint.position.x, checkpoint.position.y)
                        })
        
        # Check debt sink collisions
        if self.player:
            for entity in self.entities:
                if isinstance(entity, DebtSink) and not entity.is_depleted:
                    if self.player.get_rect().colliderect(entity.get_rect()):
                        entity.activate()
        
        # Check enemy collisions
        if self.player and not self.player.is_invulnerable:
            player_rect = self.player.get_rect()
            kill_types = [PatrolDrone, TemporalHunter, DebtShadow]
            if _has_v3_enemies:
                kill_types.extend([PhaseShifter, SwarmDrone])
            for entity in self.entities:
                if isinstance(entity, tuple(kill_types)):
                    if player_rect.colliderect(entity.get_rect()):
                        self.player.die()
                        break
        
        # Spawn debt shadows at high debt
        if self._debt_manager and self._debt_manager.current_debt >= Settings.SHADOW_SPAWN_DEBT:
            self._maybe_spawn_debt_shadow()
        
        # Remove inactive entities
        self.entities = [e for e in self.entities if e.active]
    
    def _handle_explosion(self, explosion: dict) -> None:
        """Handle debt bomb explosion effects."""
        # Time acceleration zone effect not yet implemented
        # Currently only provides visual feedback

    
    def _maybe_spawn_debt_shadow(self) -> None:
        """Potentially spawn a debt shadow."""
        # Check if we already have shadows
        shadow_count = sum(1 for e in self.entities if isinstance(e, DebtShadow))
        
        # Limit shadows based on debt
        max_shadows = int(self._debt_manager.current_debt / 10)
        
        if shadow_count < max_shadows and self.player:
            # Spawn shadow at edge of screen
            import random
            edge = random.choice(['left', 'right', 'top', 'bottom'])
            
            if edge == 'left':
                pos = Vector2(0, random.randint(0, Settings.SCREEN_HEIGHT))
            elif edge == 'right':
                pos = Vector2(Settings.SCREEN_WIDTH, random.randint(0, Settings.SCREEN_HEIGHT))
            elif edge == 'top':
                pos = Vector2(random.randint(0, Settings.SCREEN_WIDTH), 0)
            else:
                pos = Vector2(random.randint(0, Settings.SCREEN_WIDTH), Settings.SCREEN_HEIGHT)
            
            shadow = DebtShadow(pos, self.player)
            self.entities.append(shadow)
    
    def _complete_level(self) -> None:
        """Handle level completion."""
        self.level_complete = True
        
        if self.current_level:
            self.current_level.completed = True
            self.current_level.completion_time = self.level_time
        
        self._event_manager.emit(GameEvent.LEVEL_COMPLETED, {
            'level_index': self.current_level_index,
            'time': self.level_time
        })
    
    def render(self, screen: pygame.Surface) -> None:
        """
        Render the level.
        
        Args:
            screen: Surface to render to
        """
        # Import V2 entities for type checking
        try:
            from ..entities.interactables_v2 import TimeDilationZone, TemporalFragment, DebtTransferPod
            has_v2_entities = True
        except ImportError:
            has_v2_entities = False
        
        # Render tiles
        if self.tile_grid:
            self.tile_grid.render(screen)
        
        # First layer: Dilation zones (background effect)
        if has_v2_entities:
            for entity in self.entities:
                if isinstance(entity, TimeDilationZone):
                    entity.render(screen)
        
        # Second layer: interactables
        for entity in self.entities:
            if isinstance(entity, (DebtSink, DebtBomb, TimedDoor)):
                entity.render(screen)
            elif has_v2_entities and isinstance(entity, DebtTransferPod):
                entity.render(screen)
        
        # Third layer: checkpoints and exit
        for entity in self.entities:
            if isinstance(entity, (Checkpoint, ExitZone)):
                entity.render(screen)
        
        # Fourth layer: collectibles (fragments)
        if has_v2_entities:
            for entity in self.entities:
                if isinstance(entity, TemporalFragment):
                    entity.render(screen)
        
        # Fifth layer: enemies
        enemy_types = [PatrolDrone, TemporalHunter, DebtShadow]
        if _has_v3_enemies:
            enemy_types.extend([PhaseShifter, DebtLeech, SwarmDrone])
        for entity in self.entities:
            if isinstance(entity, tuple(enemy_types)):
                entity.render(screen)
        
        # Player renders last (on top)
        if self.player:
            self.player.render(screen)
    
    def get_wall_rects(self) -> List[pygame.Rect]:
        """Get all wall collision rectangles."""
        if self.tile_grid:
            return self.tile_grid.get_wall_rects()
        return []
    
    def get_hazard_rects(self) -> List[pygame.Rect]:
        """Get rectangles for all hazard tiles (danger zones)."""
        if self.tile_grid:
            return self.tile_grid.get_hazard_rects()
        return []
    
    def has_next_level(self) -> bool:
        """Check if there's another level after current."""
        return self.current_level_index < len(self.levels) - 1
    
    def get_level_info(self) -> Dict[str, Any]:
        """Get current level information."""
        if not self.current_level:
            return {}
        
        # Try to get hint from level data
        hint = ""
        if self.current_level_index < len(self.levels):
            level_data = self.levels[self.current_level_index]
            hint = getattr(level_data, 'hint', '')
        
        return {
            'name': self.current_level.name,
            'description': self.current_level.description,
            'index': self.current_level_index + 1,
            'total': len(self.levels),
            'time': self.level_time,
            'completed': self.level_complete,
            'hint': hint
        }
