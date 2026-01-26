"""
Collision System - Handles all collision detection and response.

This system manages:
- Player vs wall collisions (blocking)
- Player vs enemy collisions (death)
- Player vs interactable collisions (triggers)
- Entity vs entity collisions (custom responses)

Design Philosophy:
- Grid-based spatial partitioning for efficiency
- Collision layers for different interaction types
- Callbacks for flexible response handling
"""

from typing import List, Tuple, Dict, Set, Callable, Optional, TYPE_CHECKING
from dataclasses import dataclass
from enum import IntFlag, auto
import pygame

from ..core.settings import Settings
from ..core.utils import Vector2

if TYPE_CHECKING:
    from ..entities.base_entity import BaseEntity


class CollisionLayer(IntFlag):
    """
    Collision layers for filtering what can collide with what.
    
    Uses IntFlag for bitwise operations allowing entities
    to be on multiple layers.
    """
    NONE = 0
    PLAYER = auto()
    ENEMY = auto()
    WALL = auto()
    TRIGGER = auto()
    PROJECTILE = auto()
    INTERACTABLE = auto()
    HAZARD = auto()


@dataclass
class CollisionResult:
    """
    Result of a collision check.
    
    Contains information about what collided and how.
    """
    collided: bool
    entity_a: 'BaseEntity'
    entity_b: 'BaseEntity'
    overlap: Vector2
    normal: Vector2
    
    @staticmethod
    def none() -> 'CollisionResult':
        """Create a no-collision result."""
        return CollisionResult(False, None, None, Vector2.zero(), Vector2.zero())


class SpatialGrid:
    """
    Spatial partitioning grid for efficient collision detection.
    
    Divides the world into cells. Only entities in the same
    or adjacent cells need to be checked against each other.
    """
    
    def __init__(self, cell_size: int = 128):
        """
        Initialize spatial grid.
        
        Args:
            cell_size: Size of each grid cell in pixels
        """
        self.cell_size = cell_size
        self.cells: Dict[Tuple[int, int], Set[str]] = {}
        self.entity_cells: Dict[str, Set[Tuple[int, int]]] = {}
    
    def _get_cell_coords(self, x: float, y: float) -> Tuple[int, int]:
        """Get cell coordinates for a position."""
        return (int(x // self.cell_size), int(y // self.cell_size))
    
    def _get_entity_cells(self, rect: pygame.Rect) -> Set[Tuple[int, int]]:
        """Get all cells an entity occupies."""
        cells = set()
        
        # Get corners
        min_cell = self._get_cell_coords(rect.left, rect.top)
        max_cell = self._get_cell_coords(rect.right, rect.bottom)
        
        # Add all cells in range
        for x in range(min_cell[0], max_cell[0] + 1):
            for y in range(min_cell[1], max_cell[1] + 1):
                cells.add((x, y))
        
        return cells
    
    def insert(self, entity_id: str, rect: pygame.Rect) -> None:
        """
        Insert an entity into the grid.
        
        Args:
            entity_id: Unique entity identifier
            rect: Entity's bounding rectangle
        """
        cells = self._get_entity_cells(rect)
        self.entity_cells[entity_id] = cells
        
        for cell in cells:
            if cell not in self.cells:
                self.cells[cell] = set()
            self.cells[cell].add(entity_id)
    
    def remove(self, entity_id: str) -> None:
        """Remove an entity from the grid."""
        if entity_id not in self.entity_cells:
            return
        
        for cell in self.entity_cells[entity_id]:
            if cell in self.cells:
                self.cells[cell].discard(entity_id)
        
        del self.entity_cells[entity_id]
    
    def update(self, entity_id: str, rect: pygame.Rect) -> None:
        """Update an entity's position in the grid."""
        self.remove(entity_id)
        self.insert(entity_id, rect)
    
    def get_nearby(self, rect: pygame.Rect) -> Set[str]:
        """
        Get all entity IDs near a rectangle.
        
        Checks the rect's cells and all adjacent cells.
        """
        nearby = set()
        cells = self._get_entity_cells(rect)
        
        # Include adjacent cells
        expanded_cells = set()
        for cx, cy in cells:
            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    expanded_cells.add((cx + dx, cy + dy))
        
        # Collect entities
        for cell in expanded_cells:
            if cell in self.cells:
                nearby.update(self.cells[cell])
        
        return nearby
    
    def clear(self) -> None:
        """Clear all entities from grid."""
        self.cells.clear()
        self.entity_cells.clear()


class CollisionSystem:
    """
    Central collision detection and response system.
    
    Features:
    - Spatial partitioning for efficiency
    - Layer-based collision filtering
    - Callback system for collision responses
    - AABB collision detection
    """
    
    def __init__(self):
        """Initialize the collision system."""
        self.spatial_grid = SpatialGrid(cell_size=Settings.TILE_SIZE * 2)
        self.entities: Dict[str, 'BaseEntity'] = {}
        self.static_colliders: List[pygame.Rect] = []  # Walls, etc.
        
        # Collision callbacks: (layer_a, layer_b) -> callback
        self.callbacks: Dict[Tuple[CollisionLayer, CollisionLayer], 
                            Callable[[CollisionResult], None]] = {}
    
    def register_entity(self, entity: 'BaseEntity') -> None:
        """
        Register an entity for collision detection.
        
        Args:
            entity: Entity to register
        """
        self.entities[entity.id] = entity
        self.spatial_grid.insert(entity.id, entity.get_rect())
    
    def unregister_entity(self, entity_id: str) -> None:
        """Remove an entity from collision detection."""
        if entity_id in self.entities:
            del self.entities[entity_id]
        self.spatial_grid.remove(entity_id)
    
    def set_static_colliders(self, rects: List[pygame.Rect]) -> None:
        """
        Set static world colliders (walls).
        
        Args:
            rects: List of wall rectangles
        """
        self.static_colliders = rects.copy()
    
    def add_callback(self, layer_a: CollisionLayer, layer_b: CollisionLayer,
                    callback: Callable[[CollisionResult], None]) -> None:
        """
        Register a collision callback.
        
        Args:
            layer_a, layer_b: Layers that trigger this callback
            callback: Function to call on collision
        """
        self.callbacks[(layer_a, layer_b)] = callback
        # Also register reverse order
        self.callbacks[(layer_b, layer_a)] = callback
    
    def update(self) -> List[CollisionResult]:
        """
        Update spatial grid and check all collisions.
        
        Returns:
            List of collision results
        """
        collisions = []
        
        # Update spatial grid positions
        for entity_id, entity in self.entities.items():
            if entity.active:
                self.spatial_grid.update(entity_id, entity.get_rect())
        
        # Check entity-entity collisions
        checked_pairs: Set[Tuple[str, str]] = set()
        
        for entity_id, entity in self.entities.items():
            if not entity.active:
                continue
            
            # Get nearby entities
            nearby_ids = self.spatial_grid.get_nearby(entity.get_rect())
            
            for other_id in nearby_ids:
                if other_id == entity_id:
                    continue
                
                # Avoid duplicate checks
                pair = tuple(sorted([entity_id, other_id]))
                if pair in checked_pairs:
                    continue
                checked_pairs.add(pair)
                
                other = self.entities.get(other_id)
                if other is None or not other.active:
                    continue
                
                # Check layer compatibility
                if not self._should_check_collision(entity, other):
                    continue
                
                # Check actual collision
                result = self._check_collision(entity, other)
                if result.collided:
                    collisions.append(result)
                    self._handle_collision(result)
        
        return collisions
    
    def check_static_collision(self, rect: pygame.Rect) -> Tuple[bool, Vector2]:
        """
        Check collision against static world geometry.
        
        Args:
            rect: Rectangle to check
            
        Returns:
            (collided, push_vector) - push_vector moves rect out of collision
        """
        total_push = Vector2.zero()
        collided = False
        
        for wall in self.static_colliders:
            if rect.colliderect(wall):
                collided = True
                push = self._calculate_push_vector(rect, wall)
                total_push = total_push + push
        
        return collided, total_push
    
    def check_point_collision(self, point: Vector2, layer: CollisionLayer = None) -> Optional['BaseEntity']:
        """
        Check if a point collides with any entity.
        
        Args:
            point: Point to check
            layer: Optional layer filter
            
        Returns:
            First colliding entity, or None
        """
        point_rect = pygame.Rect(int(point.x), int(point.y), 1, 1)
        nearby = self.spatial_grid.get_nearby(point_rect)
        
        for entity_id in nearby:
            entity = self.entities.get(entity_id)
            if entity is None or not entity.active:
                continue
            
            if layer and not (entity.collision_layer & layer):
                continue
            
            if entity.get_rect().collidepoint(point.int_tuple):
                return entity
        
        return None
    
    def raycast(self, start: Vector2, direction: Vector2, max_distance: float,
               layer: CollisionLayer = None) -> Optional[Tuple['BaseEntity', float]]:
        """
        Cast a ray and find first collision.
        
        Args:
            start: Ray origin
            direction: Ray direction (should be normalized)
            max_distance: Maximum ray length
            layer: Optional layer filter
            
        Returns:
            (entity, distance) or None if no hit
        """
        # Simple step-based raycast
        step = 5.0  # Check every 5 pixels
        current = start.copy()
        
        for dist in range(0, int(max_distance), int(step)):
            current = start + direction * dist
            
            # Check point collision
            entity = self.check_point_collision(current, layer)
            if entity:
                return (entity, dist)
            
            # Check static collision
            for wall in self.static_colliders:
                if wall.collidepoint(current.int_tuple):
                    return (None, dist)  # Hit wall
        
        return None
    
    def _should_check_collision(self, entity_a: 'BaseEntity', 
                                entity_b: 'BaseEntity') -> bool:
        """Check if two entities should be tested for collision."""
        # Check if they share any collision mask bits
        a_layer = getattr(entity_a, 'collision_layer', CollisionLayer.NONE)
        b_layer = getattr(entity_b, 'collision_layer', CollisionLayer.NONE)
        a_mask = getattr(entity_a, 'collision_mask', CollisionLayer.NONE)
        b_mask = getattr(entity_b, 'collision_mask', CollisionLayer.NONE)
        
        return bool((a_layer & b_mask) or (b_layer & a_mask))
    
    def _check_collision(self, entity_a: 'BaseEntity', 
                        entity_b: 'BaseEntity') -> CollisionResult:
        """Perform AABB collision check between two entities."""
        rect_a = entity_a.get_rect()
        rect_b = entity_b.get_rect()
        
        if not rect_a.colliderect(rect_b):
            return CollisionResult.none()
        
        # Calculate overlap and normal
        overlap = self._calculate_overlap(rect_a, rect_b)
        normal = self._calculate_normal(rect_a, rect_b)
        
        return CollisionResult(
            collided=True,
            entity_a=entity_a,
            entity_b=entity_b,
            overlap=overlap,
            normal=normal
        )
    
    def _calculate_overlap(self, rect_a: pygame.Rect, 
                          rect_b: pygame.Rect) -> Vector2:
        """Calculate overlap vector between two rectangles."""
        # Calculate overlap on each axis
        overlap_x = min(rect_a.right, rect_b.right) - max(rect_a.left, rect_b.left)
        overlap_y = min(rect_a.bottom, rect_b.bottom) - max(rect_a.top, rect_b.top)
        
        return Vector2(overlap_x, overlap_y)
    
    def _calculate_normal(self, rect_a: pygame.Rect, 
                         rect_b: pygame.Rect) -> Vector2:
        """Calculate collision normal (pointing from A to B)."""
        center_a = Vector2(rect_a.centerx, rect_a.centery)
        center_b = Vector2(rect_b.centerx, rect_b.centery)
        
        diff = center_b - center_a
        if diff.magnitude() == 0:
            return Vector2(1, 0)  # Default normal
        
        return diff.normalized()
    
    def _calculate_push_vector(self, moving: pygame.Rect, 
                              static: pygame.Rect) -> Vector2:
        """Calculate vector to push moving rect out of static rect."""
        # Find minimum translation distance on each axis
        left_push = static.left - moving.right
        right_push = static.right - moving.left
        up_push = static.top - moving.bottom
        down_push = static.bottom - moving.top
        
        # Find smallest absolute push
        min_x = left_push if abs(left_push) < abs(right_push) else right_push
        min_y = up_push if abs(up_push) < abs(down_push) else down_push
        
        # Push along axis with smallest overlap
        if abs(min_x) < abs(min_y):
            return Vector2(min_x, 0)
        return Vector2(0, min_y)
    
    def _handle_collision(self, result: CollisionResult) -> None:
        """Handle a collision by calling registered callbacks."""
        layer_a = getattr(result.entity_a, 'collision_layer', CollisionLayer.NONE)
        layer_b = getattr(result.entity_b, 'collision_layer', CollisionLayer.NONE)
        
        # Find matching callback
        key = (layer_a, layer_b)
        if key in self.callbacks:
            self.callbacks[key](result)
        
        # Also call entity callbacks
        if hasattr(result.entity_a, 'on_collision'):
            result.entity_a.on_collision(result.entity_b, result)
        if hasattr(result.entity_b, 'on_collision'):
            result.entity_b.on_collision(result.entity_a, result)
    
    def clear(self) -> None:
        """Clear all collision data."""
        self.entities.clear()
        self.static_colliders.clear()
        self.spatial_grid.clear()
