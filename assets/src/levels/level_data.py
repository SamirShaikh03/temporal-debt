"""
Level Data - Definitions for all game levels.

Each level is defined as structured data that can be
loaded by the LevelManager. This separates level design
from level logic.

Design Philosophy:
- Levels are pure data (declarative design)
- Easy to add new levels
- Clear progression of mechanics
"""

from typing import List, Dict, Any
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
    Runtime level instance created from LevelData.
    
    This is what the game actually uses during play.
    """
    
    def __init__(self, data: LevelData):
        """
        Initialize level from data.
        
        Args:
            data: Level definition data
        """
        self.data = data
        self.name = data.name
        self.description = data.description
        
        # Positions
        self.spawn_point = data.get_spawn_point()
        self.exit_point = data.get_exit_point()
        self.checkpoints = data.get_checkpoints()
        
        # Dimensions
        self.height = len(data.tile_map)
        self.width = len(data.tile_map[0]) if self.height > 0 else 0
        
        # State
        self.completed = False
        self.completion_time = 0.0


# ============================================================
# LEVEL DEFINITIONS
# ============================================================

LEVEL_1 = LevelData(
    name="The Vault",
    description="Learn to borrow time... and pay it back.",
    par_time=45.0,
    tile_map=[
        "####################",
        "#S.................#",
        "#..................#",
        "#....######........#",
        "#....#....#........#",
        "#....#....#....#####",
        "#....#....#....#...#",
        "#....######....#.E.#",
        "#..............#...#",
        "#..........#####...#",
        "####################",
    ],
    entities=[
        # Tutorial patrol drone - slow, simple pattern
        EntityData(
            entity_type="patrol_drone",
            grid_x=10, grid_y=5,
            properties={
                "patrol_points": [(10, 5), (10, 8)],
                "speed": 80
            }
        ),
        # Debt sink for learning
        EntityData(
            entity_type="debt_sink",
            grid_x=8, grid_y=8,
            properties={"uses": 2}
        ),
    ]
)

LEVEL_2 = LevelData(
    name="The Gauntlet",
    description="Multiple threats. Plan your path carefully.",
    par_time=75.0,
    tile_map=[
        "####################",
        "#S.....#...........#",
        "#......#...........#",
        "#......#....####...#",
        "#..C...#....#..#...#",
        "####...#....#..#...#",
        "#......#....#..#...#",
        "#..#####....#..#...#",
        "#...........#......#",
        "#...........#..C..E#",
        "####################",
    ],
    entities=[
        # Patrol drones creating a gauntlet
        EntityData(
            entity_type="patrol_drone",
            grid_x=4, grid_y=2,
            properties={
                "patrol_points": [(4, 2), (4, 6)],
                "speed": 100
            }
        ),
        EntityData(
            entity_type="patrol_drone", 
            grid_x=9, grid_y=4,
            properties={
                "patrol_points": [(9, 4), (14, 4)],
                "speed": 120
            }
        ),
        EntityData(
            entity_type="patrol_drone",
            grid_x=12, grid_y=7,
            properties={
                "patrol_points": [(12, 7), (12, 9)],
                "speed": 90
            }
        ),
        # Temporal Hunter - punishes freeze spam
        EntityData(
            entity_type="temporal_hunter",
            grid_x=15, grid_y=2,
            properties={"speed": 140}
        ),
        # Debt sinks
        EntityData(
            entity_type="debt_sink",
            grid_x=1, grid_y=6,
            properties={"uses": 1}
        ),
        EntityData(
            entity_type="debt_sink", 
            grid_x=16, grid_y=8,
            properties={"uses": 1}
        ),
    ]
)

LEVEL_3 = LevelData(
    name="The Debt Chamber",
    description="Face the consequences of borrowed time.",
    par_time=120.0,
    tile_map=[
        "####################",
        "#S.................#",
        "#..................#",
        "###.###....###.###.#",
        "#.....#....#.....#.#",
        "#..C..#....#..C..#.#",
        "#.....#....#.....#.#",
        "###.###....###.###.#",
        "#..................#",
        "#.................E#",
        "####################",
    ],
    entities=[
        # Multiple patrol drones
        EntityData(
            entity_type="patrol_drone",
            grid_x=7, grid_y=2,
            properties={
                "patrol_points": [(7, 2), (12, 2)],
                "drone_type": "linear",
                "speed": 130
            }
        ),
        EntityData(
            entity_type="patrol_drone",
            grid_x=7, grid_y=8,
            properties={
                "patrol_points": [(7, 8), (12, 8)],
                "drone_type": "linear", 
                "speed": 130
            }
        ),
        # Circular patrol
        EntityData(
            entity_type="patrol_drone",
            grid_x=10, grid_y=5,
            properties={
                "drone_type": "circular",
                "orbit_radius": 80,
                "orbit_speed": 1.5
            }
        ),
        # Temporal Hunters - serious threat
        EntityData(
            entity_type="temporal_hunter",
            grid_x=3, grid_y=4,
            properties={"speed": 160}
        ),
        EntityData(
            entity_type="temporal_hunter",
            grid_x=16, grid_y=4,
            properties={"speed": 160}
        ),
        # Debt sinks - limited resources
        EntityData(
            entity_type="debt_sink",
            grid_x=4, grid_y=5,
            properties={"uses": 1, "absorption_amount": 4.0}
        ),
        EntityData(
            entity_type="debt_sink",
            grid_x=14, grid_y=5,
            properties={"uses": 1, "absorption_amount": 4.0}
        ),
        # Debt bomb for added chaos
        EntityData(
            entity_type="debt_bomb",
            grid_x=10, grid_y=3,
            properties={
                "trigger_type": "proximity",
                "payload": 4.0,
                "radius": 120
            }
        ),
    ]
)

# All levels in order
ALL_LEVELS = [LEVEL_1, LEVEL_2, LEVEL_3]
