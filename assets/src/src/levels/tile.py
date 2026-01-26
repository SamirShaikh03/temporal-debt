"""
Tile System - Building blocks for level environments.

Tiles are the fundamental units of level geometry.
They define walkable space, walls, and special zones.

Design Philosophy:
- Simple tile types for clear visual language
- Tiles are data, entities are behavior
- Easy to create new level layouts
"""

from enum import Enum, auto
from typing import Tuple
import pygame

from ..core.settings import Settings, COLORS


class TileType(Enum):
    """
    Types of tiles available in levels.
    
    Each tile type has specific properties for
    collision, rendering, and game logic.
    """
    EMPTY = auto()      # Walkable floor
    WALL = auto()       # Solid obstacle
    SPAWN = auto()      # Player spawn point
    EXIT = auto()        # Level exit
    CHECKPOINT = auto() # Save point
    HAZARD = auto()     # Instant death zone
    
    # Special floor types
    FLOOR_DARK = auto()
    FLOOR_LIGHT = auto()


class Tile:
    """
    A single tile in the level grid.
    
    Tiles are purely data - they don't update themselves.
    The level manager handles tile rendering and collision.
    """
    
    # Tile properties lookup
    PROPERTIES = {
        TileType.EMPTY: {
            'solid': False,
            'color': COLORS.FLOOR,
            'hazard': False
        },
        TileType.WALL: {
            'solid': True,
            'color': COLORS.WALL,
            'hazard': False
        },
        TileType.SPAWN: {
            'solid': False,
            'color': (50, 100, 50),
            'hazard': False
        },
        TileType.EXIT: {
            'solid': False,
            'color': COLORS.EXIT_ZONE,
            'hazard': False
        },
        TileType.CHECKPOINT: {
            'solid': False,
            'color': COLORS.CHECKPOINT,
            'hazard': False
        },
        TileType.HAZARD: {
            'solid': False,
            'color': (150, 50, 50),
            'hazard': True
        },
        TileType.FLOOR_DARK: {
            'solid': False,
            'color': (25, 25, 35),
            'hazard': False
        },
        TileType.FLOOR_LIGHT: {
            'solid': False,
            'color': (40, 40, 50),
            'hazard': False
        },
    }
    
    def __init__(self, tile_type: TileType, grid_x: int, grid_y: int):
        """
        Initialize a tile.
        
        Args:
            tile_type: Type of tile
            grid_x: X position in grid
            grid_y: Y position in grid
        """
        self.type = tile_type
        self.grid_x = grid_x
        self.grid_y = grid_y
        
        # Calculate pixel position
        self.x = grid_x * Settings.TILE_SIZE
        self.y = grid_y * Settings.TILE_SIZE
        
        # Cache properties
        props = self.PROPERTIES.get(tile_type, self.PROPERTIES[TileType.EMPTY])
        self.solid = props['solid']
        self.color = props['color']
        self.hazard = props['hazard']
        
        # Cache rect for collision
        self.rect = pygame.Rect(self.x, self.y, 
                               Settings.TILE_SIZE, Settings.TILE_SIZE)
    
    def get_rect(self) -> pygame.Rect:
        """Get tile's collision rectangle."""
        return self.rect
    
    def render(self, screen: pygame.Surface) -> None:
        """
        Render the tile with enhanced visuals.
        
        Args:
            screen: Surface to render to
        """
        # Base color fill
        pygame.draw.rect(screen, self.color, self.rect)
        
        # Add subtle grid pattern to floors
        if not self.solid and not self.hazard:
            # Subtle checkerboard pattern
            if (self.grid_x + self.grid_y) % 2 == 0:
                pattern_color = (
                    min(255, self.color[0] + 5),
                    min(255, self.color[1] + 5),
                    min(255, self.color[2] + 8)
                )
                inner_rect = self.rect.inflate(-4, -4)
                pygame.draw.rect(screen, pattern_color, inner_rect)
        
        # Wall rendering with 3D effect
        if self.solid:
            # Top highlight
            pygame.draw.line(screen, (80, 85, 100), 
                           (self.x, self.y), 
                           (self.x + Settings.TILE_SIZE - 1, self.y), 2)
            # Left highlight
            pygame.draw.line(screen, (70, 75, 90), 
                           (self.x, self.y), 
                           (self.x, self.y + Settings.TILE_SIZE - 1), 2)
            # Bottom shadow
            pygame.draw.line(screen, (30, 32, 45), 
                           (self.x, self.y + Settings.TILE_SIZE - 1), 
                           (self.x + Settings.TILE_SIZE - 1, self.y + Settings.TILE_SIZE - 1), 2)
            # Right shadow
            pygame.draw.line(screen, (35, 38, 50), 
                           (self.x + Settings.TILE_SIZE - 1, self.y), 
                           (self.x + Settings.TILE_SIZE - 1, self.y + Settings.TILE_SIZE - 1), 2)
        
        # Hazard rendering with warning stripes
        if self.hazard:
            stripe_color = (200, 60, 60)
            for i in range(0, Settings.TILE_SIZE * 2, 20):
                pygame.draw.line(screen, stripe_color,
                               (self.x + i - Settings.TILE_SIZE, self.y),
                               (self.x + i, self.y + Settings.TILE_SIZE), 3)
            # Border
            pygame.draw.rect(screen, (255, 80, 80), self.rect, 2)
    
    def render_highlight(self, screen: pygame.Surface, 
                        color: Tuple[int, int, int, int]) -> None:
        """
        Render with highlight overlay.
        
        Args:
            screen: Surface to render to
            color: RGBA highlight color
        """
        self.render(screen)
        
        highlight = pygame.Surface((Settings.TILE_SIZE, Settings.TILE_SIZE), pygame.SRCALPHA)
        highlight.fill(color)
        screen.blit(highlight, (self.x, self.y))


class TileGrid:
    """
    A 2D grid of tiles representing a level's geometry.
    
    Provides efficient access to tiles by grid position
    and collision queries.
    """
    
    def __init__(self, width: int, height: int):
        """
        Initialize an empty tile grid.
        
        Args:
            width: Grid width in tiles
            height: Grid height in tiles
        """
        self.width = width
        self.height = height
        
        # Initialize with empty tiles
        self.tiles = [
            [Tile(TileType.EMPTY, x, y) for x in range(width)]
            for y in range(height)
        ]
        
        # Cache wall rects for collision
        self._wall_rects: list = []
        self._dirty = True
    
    def set_tile(self, grid_x: int, grid_y: int, tile_type: TileType) -> None:
        """
        Set a tile at grid position.
        
        Args:
            grid_x: X position in grid
            grid_y: Y position in grid
            tile_type: Type to set
        """
        if 0 <= grid_x < self.width and 0 <= grid_y < self.height:
            self.tiles[grid_y][grid_x] = Tile(tile_type, grid_x, grid_y)
            self._dirty = True
    
    def get_tile(self, grid_x: int, grid_y: int) -> Tile:
        """
        Get tile at grid position.
        
        Args:
            grid_x: X position in grid
            grid_y: Y position in grid
            
        Returns:
            Tile at position, or None if out of bounds
        """
        if 0 <= grid_x < self.width and 0 <= grid_y < self.height:
            return self.tiles[grid_y][grid_x]
        return None
    
    def get_tile_at_pixel(self, x: float, y: float) -> Tile:
        """
        Get tile at pixel position.
        
        Args:
            x: X pixel position
            y: Y pixel position
            
        Returns:
            Tile at position, or None if out of bounds
        """
        grid_x = int(x // Settings.TILE_SIZE)
        grid_y = int(y // Settings.TILE_SIZE)
        return self.get_tile(grid_x, grid_y)
    
    def get_wall_rects(self) -> list:
        """
        Get all wall collision rectangles.
        
        Returns:
            List of pygame.Rect for all solid tiles
        """
        if self._dirty:
            self._wall_rects = []
            for row in self.tiles:
                for tile in row:
                    if tile.solid:
                        self._wall_rects.append(tile.rect)
            self._dirty = False
        
        return self._wall_rects
    
    def is_solid(self, grid_x: int, grid_y: int) -> bool:
        """Check if tile at position is solid."""
        tile = self.get_tile(grid_x, grid_y)
        return tile is not None and tile.solid
    
    def is_solid_at_pixel(self, x: float, y: float) -> bool:
        """Check if position is in a solid tile."""
        tile = self.get_tile_at_pixel(x, y)
        return tile is not None and tile.solid
    
    def render(self, screen: pygame.Surface) -> None:
        """
        Render all tiles.
        
        Args:
            screen: Surface to render to
        """
        for row in self.tiles:
            for tile in row:
                tile.render(screen)
    
    def from_string_map(self, string_map: list) -> None:
        """
        Load tiles from a string representation.
        
        Args:
            string_map: List of strings, each char is a tile
            
        Legend:
            '.' = Empty floor
            '#' = Wall
            'S' = Spawn point
            'E' = Exit
            'C' = Checkpoint
            'X' = Hazard
            ' ' = Empty (dark floor)
        """
        tile_chars = {
            '.': TileType.EMPTY,
            '#': TileType.WALL,
            'S': TileType.SPAWN,
            'E': TileType.EXIT,
            'C': TileType.CHECKPOINT,
            'X': TileType.HAZARD,
            ' ': TileType.FLOOR_DARK,
            '-': TileType.FLOOR_LIGHT,
        }
        
        for y, row in enumerate(string_map):
            for x, char in enumerate(row):
                if x < self.width and y < self.height:
                    tile_type = tile_chars.get(char, TileType.EMPTY)
                    self.set_tile(x, y, tile_type)
