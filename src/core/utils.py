"""
Utility functions and classes used throughout the game.

These are generic helpers that don't belong to any specific system.
"""

import math
from typing import Tuple


class Vector2:
    """
    Simple 2D vector class for game mathematics.
    
    Design Decision:
    While pygame has pygame.math.Vector2, we implement our own for:
    - Learning purposes (good for portfolio)
    - Custom methods specific to our needs
    - Type consistency throughout codebase
    
    Usage:
        pos = Vector2(100, 200)
        vel = Vector2(5, 0)
        new_pos = pos + vel * dt
    """
    
    __slots__ = ('x', 'y')  # Memory optimization
    
    def __init__(self, x: float = 0, y: float = 0):
        self.x = float(x)
        self.y = float(y)
    
    def __add__(self, other: 'Vector2') -> 'Vector2':
        return Vector2(self.x + other.x, self.y + other.y)
    
    def __sub__(self, other: 'Vector2') -> 'Vector2':
        return Vector2(self.x - other.x, self.y - other.y)
    
    def __mul__(self, scalar: float) -> 'Vector2':
        return Vector2(self.x * scalar, self.y * scalar)
    
    def __rmul__(self, scalar: float) -> 'Vector2':
        return self.__mul__(scalar)
    
    def __truediv__(self, scalar: float) -> 'Vector2':
        if scalar == 0:
            return Vector2(0, 0)
        return Vector2(self.x / scalar, self.y / scalar)
    
    def __neg__(self) -> 'Vector2':
        return Vector2(-self.x, -self.y)
    
    def __eq__(self, other: 'Vector2') -> bool:
        if not isinstance(other, Vector2):
            return False
        return abs(self.x - other.x) < 0.0001 and abs(self.y - other.y) < 0.0001
    
    def __repr__(self) -> str:
        return f"Vector2({self.x:.2f}, {self.y:.2f})"
    
    def __iter__(self):
        """Allow unpacking: x, y = vector"""
        yield self.x
        yield self.y
    
    @property
    def tuple(self) -> Tuple[float, float]:
        """Get as tuple for pygame compatibility."""
        return (self.x, self.y)
    
    @property
    def int_tuple(self) -> Tuple[int, int]:
        """Get as integer tuple for pixel positions."""
        return (int(self.x), int(self.y))
    
    def copy(self) -> 'Vector2':
        """Create a copy of this vector."""
        return Vector2(self.x, self.y)
    
    def magnitude(self) -> float:
        """Get the length of this vector."""
        return math.sqrt(self.x ** 2 + self.y ** 2)
    
    def magnitude_squared(self) -> float:
        """Get squared length (faster, for comparisons)."""
        return self.x ** 2 + self.y ** 2
    
    def normalized(self) -> 'Vector2':
        """Get a unit vector in the same direction."""
        mag = self.magnitude()
        if mag == 0:
            return Vector2(0, 0)
        return Vector2(self.x / mag, self.y / mag)
    
    def normalize(self) -> 'Vector2':
        """Normalize in place and return self."""
        mag = self.magnitude()
        if mag > 0:
            self.x /= mag
            self.y /= mag
        return self
    
    def dot(self, other: 'Vector2') -> float:
        """Dot product with another vector."""
        return self.x * other.x + self.y * other.y
    
    def distance_to(self, other: 'Vector2') -> float:
        """Distance to another point."""
        return (other - self).magnitude()
    
    def distance_squared_to(self, other: 'Vector2') -> float:
        """Squared distance (faster for comparisons)."""
        return (other - self).magnitude_squared()
    
    def lerp(self, target: 'Vector2', t: float) -> 'Vector2':
        """Linear interpolation toward target."""
        t = clamp(t, 0, 1)
        return Vector2(
            self.x + (target.x - self.x) * t,
            self.y + (target.y - self.y) * t
        )
    
    def angle_to(self, other: 'Vector2') -> float:
        """Angle to another vector in radians."""
        return math.atan2(other.y - self.y, other.x - self.x)
    
    def rotated(self, angle: float) -> 'Vector2':
        """Return this vector rotated by angle (radians)."""
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        return Vector2(
            self.x * cos_a - self.y * sin_a,
            self.x * sin_a + self.y * cos_a
        )
    
    @staticmethod
    def from_angle(angle: float, magnitude: float = 1.0) -> 'Vector2':
        """Create a vector from an angle and magnitude."""
        return Vector2(
            math.cos(angle) * magnitude,
            math.sin(angle) * magnitude
        )
    
    @staticmethod
    def zero() -> 'Vector2':
        """Create a zero vector."""
        return Vector2(0, 0)
    
    @staticmethod
    def one() -> 'Vector2':
        """Create a (1, 1) vector."""
        return Vector2(1, 1)


def clamp(value: float, min_val: float, max_val: float) -> float:
    """
    Clamp a value between minimum and maximum bounds.
    
    Args:
        value: The value to clamp
        min_val: Minimum allowed value
        max_val: Maximum allowed value
    
    Returns:
        The clamped value
    """
    return max(min_val, min(value, max_val))


def lerp(start: float, end: float, t: float) -> float:
    """
    Linear interpolation between two values.
    
    Args:
        start: Starting value
        end: Ending value
        t: Interpolation factor (0-1)
    
    Returns:
        Interpolated value
    """
    t = clamp(t, 0, 1)
    return start + (end - start) * t


def inverse_lerp(start: float, end: float, value: float) -> float:
    """
    Get the interpolation factor for a value between start and end.
    
    Args:
        start: Range start
        end: Range end
        value: The value to find t for
    
    Returns:
        The t value (0-1) representing where value falls in the range
    """
    if abs(end - start) < 0.0001:
        return 0
    return clamp((value - start) / (end - start), 0, 1)


def remap(value: float, in_min: float, in_max: float, out_min: float, out_max: float) -> float:
    """
    Remap a value from one range to another.
    
    Args:
        value: The input value
        in_min, in_max: Input range
        out_min, out_max: Output range
    
    Returns:
        The remapped value
    """
    t = inverse_lerp(in_min, in_max, value)
    return lerp(out_min, out_max, t)


def smooth_step(edge0: float, edge1: float, x: float) -> float:
    """
    Smooth step interpolation (Hermite).
    Creates smooth transitions with ease-in and ease-out.
    
    Args:
        edge0: Lower edge
        edge1: Upper edge
        x: Value to interpolate
    
    Returns:
        Smoothly interpolated value (0-1)
    """
    t = clamp((x - edge0) / (edge1 - edge0), 0, 1)
    return t * t * (3 - 2 * t)


def ease_out_quad(t: float) -> float:
    """Quadratic ease-out function."""
    return 1 - (1 - t) ** 2


def ease_in_quad(t: float) -> float:
    """Quadratic ease-in function."""
    return t * t


def ease_in_out_quad(t: float) -> float:
    """Quadratic ease-in-out function."""
    if t < 0.5:
        return 2 * t * t
    return 1 - (-2 * t + 2) ** 2 / 2


def sign(value: float) -> int:
    """Get the sign of a value (-1, 0, or 1)."""
    if value > 0:
        return 1
    elif value < 0:
        return -1
    return 0


def approach(current: float, target: float, delta: float) -> float:
    """
    Move current toward target by delta amount.
    Will not overshoot target.
    
    Args:
        current: Current value
        target: Target value
        delta: Maximum amount to move (should be positive)
    
    Returns:
        New value closer to target
    """
    if current < target:
        return min(current + delta, target)
    return max(current - delta, target)


def wrap_angle(angle: float) -> float:
    """Wrap angle to [-pi, pi] range."""
    while angle > math.pi:
        angle -= 2 * math.pi
    while angle < -math.pi:
        angle += 2 * math.pi
    return angle


def rect_center(x: float, y: float, width: float, height: float) -> Tuple[float, float]:
    """Get the center point of a rectangle."""
    return (x + width / 2, y + height / 2)


def point_in_rect(px: float, py: float, rx: float, ry: float, rw: float, rh: float) -> bool:
    """Check if a point is inside a rectangle."""
    return rx <= px <= rx + rw and ry <= py <= ry + rh


def rects_overlap(r1: Tuple, r2: Tuple) -> bool:
    """
    Check if two rectangles overlap.
    
    Args:
        r1, r2: Tuples of (x, y, width, height)
    
    Returns:
        True if rectangles overlap
    """
    x1, y1, w1, h1 = r1
    x2, y2, w2, h2 = r2
    
    return (x1 < x2 + w2 and x1 + w1 > x2 and
            y1 < y2 + h2 and y1 + h1 > y2)


def format_time(seconds: float, show_decimals: bool = True) -> str:
    """
    Format seconds into a readable time string.
    
    Args:
        seconds: Time in seconds
        show_decimals: Whether to show decimal places
    
    Returns:
        Formatted string like "1:23.45" or "1:23"
    """
    minutes = int(seconds // 60)
    secs = seconds % 60
    
    if show_decimals:
        return f"{minutes}:{secs:05.2f}"
    return f"{minutes}:{int(secs):02d}"
