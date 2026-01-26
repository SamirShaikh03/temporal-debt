"""
Enhanced Level Data - Bigger, more interesting maps with diverse enemy patterns.

This module defines expanded level layouts with:
- Larger 25x14 tile grids
- Diverse enemy types and patrol patterns
- Multiple paths and secrets
- Environmental variety
- Progressive difficulty
"""

from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field

from ..core.settings import Settings
from ..core.utils import Vector2


@dataclass
class EntityData:
    """
    Data for spawning an entity in a level.
    
    This is level-design data, not the actual entity.
    """
    entity_type: str
    grid_x: int
    grid_y: int
    properties: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def position(self) -> Vector2:
        """Get pixel position from grid position."""
        return Vector2(
            self.grid_x * Settings.TILE_SIZE,
            self.grid_y * Settings.TILE_SIZE
        )


@dataclass  
class LevelData:
    """
    Complete data for a level.
    
    Contains all information needed to construct a level:
    - Tile map
    - Entity placements
    - Special positions
    - Level metadata
    """
    name: str
    description: str
    tile_map: List[str]  # String representation of tiles
    entities: List[EntityData] = field(default_factory=list)
    
    # Metadata
    par_time: float = 60.0  # Target completion time
    max_debt_allowed: float = 30.0  # Fail if exceeded (optional)
    hint: str = ""  # Hint text shown at level start
    
    def get_spawn_point(self) -> Vector2:
        """Find spawn point from tile map."""
        for y, row in enumerate(self.tile_map):
            for x, char in enumerate(row):
                if char == 'S':
                    return Vector2(
                        x * Settings.TILE_SIZE + Settings.TILE_SIZE // 4,
                        y * Settings.TILE_SIZE + Settings.TILE_SIZE // 4
                    )
        # Default to top-left
        return Vector2(Settings.TILE_SIZE, Settings.TILE_SIZE)
    
    def get_exit_point(self) -> Vector2:
        """Find exit point from tile map."""
        for y, row in enumerate(self.tile_map):
            for x, char in enumerate(row):
                if char == 'E':
                    return Vector2(
                        x * Settings.TILE_SIZE,
                        y * Settings.TILE_SIZE
                    )
        # Default to bottom-right
        return Vector2(
            (len(self.tile_map[0]) - 2) * Settings.TILE_SIZE,
            (len(self.tile_map) - 2) * Settings.TILE_SIZE
        )
    
    def get_checkpoints(self) -> List[Vector2]:
        """Find all checkpoint positions."""
        checkpoints = []
        for y, row in enumerate(self.tile_map):
            for x, char in enumerate(row):
                if char == 'C':
                    checkpoints.append(Vector2(
                        x * Settings.TILE_SIZE,
                        y * Settings.TILE_SIZE
                    ))
        return checkpoints


class Level:
    """
    Runtime level instance.
    
    Created from LevelData when a level is loaded.
    Tracks runtime state like completion and time.
    """
    
    def __init__(self, data: LevelData):
        self.name = data.name
        self.description = data.description
        self.completed = False
        self.completion_time = 0.0
        self._data = data


# =============================================================================
# LEVEL 1: THE VAULT - Tutorial Level
# =============================================================================

LEVEL_1 = LevelData(
    name="THE VAULT",
    description="Learn the basics of temporal manipulation",
    hint="Use WASD to move. Hold SPACE to freeze time. Reach the green exit.",
    tile_map=[
        "##########################",
        "#.....#.........#.....D.#",
        "#.S...#.........#...D...#",
        "#.....#.................#",
        "#.......................#",
        "###.....................#",
        "#.......................#",
        "#...................#####",
        "#.......................#",
        "#.......................#",
        "#.....####.....####.....#",
        "#.......................#",
        "#.....................E.#",
        "##########################",
    ],
    entities=[
        # Single slow patrol drone - horizontal
        EntityData(
            entity_type='patrol_drone',
            grid_x=12,
            grid_y=6,
            properties={
                'drone_type': 'linear',
                'patrol_points': [(8, 6), (16, 6)],
                'speed': 60
            }
        ),
    ],
    par_time=45.0,
    max_debt_allowed=25.0
)


# =============================================================================
# LEVEL 2: CLOCKWORK MAZE - Introduce Complex Patterns
# =============================================================================

LEVEL_2 = LevelData(
    name="CLOCKWORK MAZE",
    description="Navigate the circular guardians",
    hint="The circular drone orbits the center. Time your moves carefully!",
    tile_map=[
        "##########################",
        "#........#.....#........#",
        "#.S......#..D..#........#",
        "#........................#",
        "#........................#",
        "#####..#####.#####..######",
        "#........................#",
        "#........................#",
        "#........................#",
        "#..####.....#####...####.#",
        "#........................#",
        "#..........D.............#",
        "#......................E.#",
        "##########################",
    ],
    entities=[
        # Circular patrol drone in center
        EntityData(
            entity_type='patrol_drone',
            grid_x=12,
            grid_y=7,
            properties={
                'drone_type': 'circular',
                'orbit_radius': 96,
                'orbit_speed': 1.5,
                'speed': 80
            }
        ),
        # Horizontal patrol - top corridor
        EntityData(
            entity_type='patrol_drone',
            grid_x=4,
            grid_y=3,
            properties={
                'drone_type': 'linear',
                'patrol_points': [(2, 3), (7, 3)],
                'speed': 90
            }
        ),
        # Horizontal patrol - bottom
        EntityData(
            entity_type='patrol_drone',
            grid_x=16,
            grid_y=11,
            properties={
                'drone_type': 'linear',
                'patrol_points': [(14, 11), (21, 11)],
                'speed': 100
            }
        ),
        # Vertical patrol
        EntityData(
            entity_type='patrol_drone',
            grid_x=19,
            grid_y=3,
            properties={
                'drone_type': 'linear',
                'patrol_points': [(19, 2), (19, 4)],
                'speed': 70
            }
        ),
    ],
    par_time=60.0,
    max_debt_allowed=22.0
)


# =============================================================================
# LEVEL 3: THE GAUNTLET - High Pressure
# =============================================================================

LEVEL_3 = LevelData(
    name="THE GAUNTLET",
    description="Timing is everything",
    hint="Watch out for the Temporal Hunter - it moves ONLY when time is frozen!",
    tile_map=[
        "##########################",
        "#S.......................#",
        "#........................#",
        "#..##..##..##..##..##....#",
        "#..##..##..##..##..##....#",
        "#........................#",
        "#..........D.............#",
        "#........................#",
        "#..##..##..##..##..##....#",
        "#..##..##..##..##..##....#",
        "#......................D.#",
        "#........................#",
        "#......................E.#",
        "##########################",
    ],
    entities=[
        # Multiple vertical patrols between pillars
        EntityData(
            entity_type='patrol_drone',
            grid_x=5,
            grid_y=5,
            properties={
                'drone_type': 'linear',
                'patrol_points': [(5, 2), (5, 5)],
                'speed': 110
            }
        ),
        EntityData(
            entity_type='patrol_drone',
            grid_x=9,
            grid_y=6,
            properties={
                'drone_type': 'linear',
                'patrol_points': [(9, 6), (9, 11)],
                'speed': 100
            }
        ),
        EntityData(
            entity_type='patrol_drone',
            grid_x=13,
            grid_y=5,
            properties={
                'drone_type': 'linear',
                'patrol_points': [(13, 2), (13, 5)],
                'speed': 120
            }
        ),
        EntityData(
            entity_type='patrol_drone',
            grid_x=17,
            grid_y=6,
            properties={
                'drone_type': 'linear',
                'patrol_points': [(17, 6), (17, 11)],
                'speed': 95
            }
        ),
        # Horizontal sweeper at top
        EntityData(
            entity_type='patrol_drone',
            grid_x=12,
            grid_y=2,
            properties={
                'drone_type': 'linear',
                'patrol_points': [(2, 2), (22, 2)],
                'speed': 140
            }
        ),
        # Temporal Hunter in center
        EntityData(
            entity_type='temporal_hunter',
            grid_x=11,
            grid_y=6,
            properties={
                'speed': 100
            }
        ),
    ],
    par_time=50.0,
    max_debt_allowed=20.0
)


# =============================================================================
# LEVEL 4: SEEKER'S DOMAIN - Intelligent Enemies
# =============================================================================

LEVEL_4 = LevelData(
    name="SEEKER'S DOMAIN",
    description="They can smell fear... and frozen time",
    hint="The red drone follows you! Use obstacles and timing to escape.",
    tile_map=[
        "##########################",
        "#..........#.............#",
        "#.S........#.............#",
        "#..........#.............#",
        "#....###...#....###......#",
        "#........................#",
        "#...D..............D.....#",
        "#........................#",
        "#....###...#....###......#",
        "#..........#.............#",
        "#..........#..........D..#",
        "#..........#.............#",
        "#....................E...#",
        "##########################",
    ],
    entities=[
        # Seeker drone - follows player!
        EntityData(
            entity_type='patrol_drone',
            grid_x=12,
            grid_y=6,
            properties={
                'drone_type': 'seeker',
                'speed': 50
            }
        ),
        # Guardian at exit - circular
        EntityData(
            entity_type='patrol_drone',
            grid_x=21,
            grid_y=10,
            properties={
                'drone_type': 'circular',
                'orbit_radius': 64,
                'orbit_speed': 1.8,
                'speed': 90
            }
        ),
        # Barrier patrols
        EntityData(
            entity_type='patrol_drone',
            grid_x=6,
            grid_y=3,
            properties={
                'drone_type': 'linear',
                'patrol_points': [(2, 3), (9, 3)],
                'speed': 100
            }
        ),
        EntityData(
            entity_type='patrol_drone',
            grid_x=17,
            grid_y=10,
            properties={
                'drone_type': 'linear',
                'patrol_points': [(14, 10), (19, 10)],
                'speed': 110
            }
        ),
        # Temporal Hunter
        EntityData(
            entity_type='temporal_hunter',
            grid_x=7,
            grid_y=6,
            properties={
                'speed': 80
            }
        ),
    ],
    par_time=45.0,
    max_debt_allowed=18.0
)


# =============================================================================
# LEVEL 5: THE DEBT CHAMBER - Maximum Pressure
# =============================================================================

LEVEL_5 = LevelData(
    name="THE DEBT CHAMBER",
    description="The final test of temporal mastery",
    hint="Red zones (H) add debt instantly! Use debt sinks (D) wisely.",
    tile_map=[
        "##########################",
        "#........................#",
        "#.S..HH..........HH......#",
        "#....HH..........HH......#",
        "#.......#########........#",
        "#........................#",
        "####.........DD.......####",
        "#........................#",
        "#.......#########........#",
        "#....HH..........HH......#",
        "#....HH..........HH......#",
        "#........................#",
        "#......................E.#",
        "##########################",
    ],
    entities=[
        # Multiple seekers
        EntityData(
            entity_type='patrol_drone',
            grid_x=8,
            grid_y=6,
            properties={
                'drone_type': 'seeker',
                'speed': 45
            }
        ),
        EntityData(
            entity_type='patrol_drone',
            grid_x=16,
            grid_y=6,
            properties={
                'drone_type': 'seeker',
                'speed': 45
            }
        ),
        # Circular guard near exit
        EntityData(
            entity_type='patrol_drone',
            grid_x=20,
            grid_y=11,
            properties={
                'drone_type': 'circular',
                'orbit_radius': 72,
                'orbit_speed': 2.0,
                'speed': 100
            }
        ),
        # Fast horizontal sweepers
        EntityData(
            entity_type='patrol_drone',
            grid_x=12,
            grid_y=1,
            properties={
                'drone_type': 'linear',
                'patrol_points': [(2, 1), (22, 1)],
                'speed': 180
            }
        ),
        EntityData(
            entity_type='patrol_drone',
            grid_x=12,
            grid_y=11,
            properties={
                'drone_type': 'linear',
                'patrol_points': [(2, 11), (18, 11)],
                'speed': 160
            }
        ),
        # Multiple Temporal Hunters
        EntityData(
            entity_type='temporal_hunter',
            grid_x=6,
            grid_y=5,
            properties={
                'speed': 90
            }
        ),
        EntityData(
            entity_type='temporal_hunter',
            grid_x=18,
            grid_y=7,
            properties={
                'speed': 90
            }
        ),
        # Debt sinks at center
        EntityData(
            entity_type='debt_sink',
            grid_x=11,
            grid_y=6,
            properties={
                'uses': 2,
                'absorption_amount': 5.0
            }
        ),
        EntityData(
            entity_type='debt_sink',
            grid_x=12,
            grid_y=6,
            properties={
                'uses': 2,
                'absorption_amount': 5.0
            }
        ),
    ],
    par_time=40.0,
    max_debt_allowed=15.0
)


# =============================================================================
# LEVEL 6: INFINITY LOOP - Bonus Challenge
# =============================================================================

LEVEL_6 = LevelData(
    name="INFINITY LOOP",
    description="The eternal dance of time",
    hint="Master the rhythm of the circular guardians. Patience is key.",
    tile_map=[
        "##########################",
        "#........................#",
        "#........................#",
        "#..###..............###..#",
        "#..#S#..............#E#..#",
        "#..#.#..............#.#..#",
        "#..........DDD...........#",
        "#..#.#..............#.#..#",
        "#..#.#..............#.#..#",
        "#..###..............###..#",
        "#........................#",
        "#........................#",
        "#........................#",
        "##########################",
    ],
    entities=[
        # Ring of circular drones - outer ring
        EntityData(
            entity_type='patrol_drone',
            grid_x=12,
            grid_y=2,
            properties={
                'drone_type': 'circular',
                'orbit_radius': 168,
                'orbit_speed': 0.8,
                'speed': 70
            }
        ),
        EntityData(
            entity_type='patrol_drone',
            grid_x=12,
            grid_y=11,
            properties={
                'drone_type': 'circular',
                'orbit_radius': 168,
                'orbit_speed': 0.8,
                'speed': 70
            }
        ),
        # Inner ring - opposite direction (faster)
        EntityData(
            entity_type='patrol_drone',
            grid_x=9,
            grid_y=6,
            properties={
                'drone_type': 'circular',
                'orbit_radius': 96,
                'orbit_speed': -1.2,
                'speed': 90
            }
        ),
        EntityData(
            entity_type='patrol_drone',
            grid_x=15,
            grid_y=6,
            properties={
                'drone_type': 'circular',
                'orbit_radius': 96,
                'orbit_speed': -1.2,
                'speed': 90
            }
        ),
        # Temporal Hunters guarding passages
        EntityData(
            entity_type='temporal_hunter',
            grid_x=6,
            grid_y=6,
            properties={
                'speed': 100
            }
        ),
        EntityData(
            entity_type='temporal_hunter',
            grid_x=18,
            grid_y=6,
            properties={
                'speed': 100
            }
        ),
        # Debt sinks in center
        EntityData(
            entity_type='debt_sink',
            grid_x=11,
            grid_y=6,
            properties={
                'uses': 3,
                'absorption_amount': 4.0
            }
        ),
        EntityData(
            entity_type='debt_sink',
            grid_x=12,
            grid_y=6,
            properties={
                'uses': 3,
                'absorption_amount': 4.0
            }
        ),
        EntityData(
            entity_type='debt_sink',
            grid_x=13,
            grid_y=6,
            properties={
                'uses': 3,
                'absorption_amount': 4.0
            }
        ),
    ],
    par_time=30.0,
    max_debt_allowed=12.0
)


# =============================================================================
# ALL LEVELS LIST
# =============================================================================

ALL_LEVELS = [
    LEVEL_1,
    LEVEL_2,
    LEVEL_3,
    LEVEL_4,
    LEVEL_5,
    LEVEL_6
]

# Level selection helper
def get_level(index: int) -> Optional[LevelData]:
    """Get level by index (0-based)."""
    if 0 <= index < len(ALL_LEVELS):
        return ALL_LEVELS[index]
    return None

def get_level_count() -> int:
    """Get total number of levels."""
    return len(ALL_LEVELS)
