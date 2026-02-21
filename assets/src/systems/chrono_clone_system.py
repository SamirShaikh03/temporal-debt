"""
Chrono-Clone System - Create temporal echoes that replay player movements.

Players can spawn a "clone" that replays their movements from the last
few seconds. This creates puzzle-solving opportunities and tactical options.

Design Philosophy:
- Enable creative puzzle solutions
- Provide distraction/decoy mechanics
- Cost-free but skill-gated
- Visual feedback shows clone capabilities
"""

from typing import List, Optional, Tuple, TYPE_CHECKING
from dataclasses import dataclass
from collections import deque
import pygame
import math

from ..core.settings import Settings, COLORS
from ..core.events import EventManager, GameEvent, get_event_manager
from ..core.utils import Vector2, get_font

if TYPE_CHECKING:
    from ..entities.player import Player


@dataclass
class MovementFrame:
    """A single frame of recorded player movement."""
    position: Vector2
    timestamp: float


class ChronoClone:
    """
    A temporal clone that replays recorded movements.
    
    The clone follows a pre-recorded path, creating various
    strategic opportunities for the player.
    """
    
    def __init__(self, frames: List[MovementFrame], size: Tuple[int, int]):
        """
        Initialize a chrono-clone.
        
        Args:
            frames: Recorded movement frames to replay
            size: Visual size matching player
        """
        self.frames = frames
        self.size = size
        self.current_index = 0
        self.position = frames[0].position.copy() if frames else Vector2.zero()
        self.active = True
        self.completed = False
        
        # Visual state
        self._alpha = 180
        self._pulse_timer = 0.0
        
        # Playback
        self._playback_time = 0.0
        self._playback_speed = 1.0
    
    def update(self, dt: float) -> None:
        """
        Update clone position along recorded path.
        
        Args:
            dt: Delta time
        """
        if not self.active or self.completed or not self.frames:
            return
        
        self._playback_time += dt * self._playback_speed
        self._pulse_timer += dt * 4
        
        # Find the appropriate frame based on playback time
        while (self.current_index < len(self.frames) - 1 and
               self._playback_time >= self.frames[self.current_index + 1].timestamp):
            self.current_index += 1
        
        if self.current_index >= len(self.frames) - 1:
            self.completed = True
            self.active = False
            return
        
        # Interpolate between frames
        current_frame = self.frames[self.current_index]
        next_frame = self.frames[self.current_index + 1]
        
        # Calculate interpolation factor
        frame_duration = next_frame.timestamp - current_frame.timestamp
        if frame_duration > 0:
            t = (self._playback_time - current_frame.timestamp) / frame_duration
            t = max(0, min(1, t))
            
            # Lerp position
            self.position = Vector2(
                current_frame.position.x + (next_frame.position.x - current_frame.position.x) * t,
                current_frame.position.y + (next_frame.position.y - current_frame.position.y) * t
            )
    
    def render(self, screen: pygame.Surface) -> None:
        """Render the chrono-clone."""
        if not self.active:
            return
        
        # Pulsing alpha
        pulse = (math.sin(self._pulse_timer) + 1) / 2
        alpha = int(self._alpha * (0.7 + 0.3 * pulse))
        
        # Create clone surface
        clone_surf = pygame.Surface(self.size, pygame.SRCALPHA)
        
        # Clone color (ghostly blue version of player)
        color = (150, 200, 255, alpha)
        pygame.draw.rect(clone_surf, color, (0, 0, self.size[0], self.size[1]))
        
        # Inner glow
        inner_color = (200, 230, 255, alpha // 2)
        inner_rect = (4, 4, self.size[0] - 8, self.size[1] - 8)
        pygame.draw.rect(clone_surf, inner_color, inner_rect)
        
        # Draw "CLONE" text indicator
        try:
            font = get_font('Arial', 10)
            label = font.render("CLONE", True, (255, 255, 255, alpha))
            screen.blit(label, (self.position.x, self.position.y - 15))
        except Exception:
            pass
        
        screen.blit(clone_surf, self.position.int_tuple)
    
    def get_rect(self) -> pygame.Rect:
        """Get collision rectangle for clone."""
        return pygame.Rect(
            int(self.position.x),
            int(self.position.y),
            self.size[0],
            self.size[1]
        )


class ChronoCloneSystem:
    """
    Manages chrono-clones and movement recording.
    
    Features:
    - Continuously records player movement (last 5 seconds)
    - Press key to spawn clone that replays recording
    - One clone at a time
    - Clone can distract enemies and trigger pressure plates
    - Cooldown between clone spawns
    """
    
    # Configuration
    RECORDING_DURATION = 5.0  # Seconds of movement to record
    RECORDING_INTERVAL = 0.05  # Seconds between recorded frames
    CLONE_COOLDOWN = 8.0  # Seconds between clone spawns
    MAX_FRAMES = int(RECORDING_DURATION / RECORDING_INTERVAL)
    
    def __init__(self, event_manager: EventManager = None):
        """
        Initialize the Chrono-Clone System.
        
        Args:
            event_manager: Event system for notifications
        """
        self._event_manager = event_manager or get_event_manager()
        
        # Recording
        self._recording: deque[MovementFrame] = deque(maxlen=self.MAX_FRAMES)
        self._record_timer = 0.0
        self._total_recording_time = 0.0
        
        # Clone
        self._current_clone: Optional[ChronoClone] = None
        self._cooldown_timer = 0.0
        
        # Player reference
        self._player_size = Settings.PLAYER_SIZE
        
        # Statistics
        self._clones_spawned = 0
        self._successful_distractions = 0  # Tracked externally
    
    @property
    def can_spawn_clone(self) -> bool:
        """Whether a clone can currently be spawned."""
        return (self._cooldown_timer <= 0 and 
                self._current_clone is None and
                len(self._recording) > 10)
    
    @property
    def has_active_clone(self) -> bool:
        """Whether a clone is currently active."""
        return self._current_clone is not None and self._current_clone.active
    
    @property
    def cooldown_remaining(self) -> float:
        """Seconds remaining until clone can be spawned."""
        return max(0, self._cooldown_timer)
    
    @property
    def cooldown_percentage(self) -> float:
        """Cooldown progress (0.0 = ready, 1.0 = just used)."""
        if self._cooldown_timer <= 0:
            return 0.0
        return self._cooldown_timer / self.CLONE_COOLDOWN
    
    @property
    def is_recording(self) -> bool:
        """Whether the system is actively recording (always true if enough frames)."""
        return len(self._recording) >= 10
    
    def record_position(self, position: Vector2, dt: float) -> None:
        """
        Record player position for later replay.
        
        Args:
            position: Current player position
            dt: Delta time
        """
        self._record_timer += dt
        self._total_recording_time += dt
        
        if self._record_timer >= self.RECORDING_INTERVAL:
            self._record_timer = 0.0
            self._recording.append(MovementFrame(
                position=position.copy(),
                timestamp=self._total_recording_time
            ))
    
    def spawn_clone(self) -> bool:
        """
        Spawn a chrono-clone using recorded movement.
        
        Returns:
            True if clone was spawned successfully
        """
        if not self.can_spawn_clone:
            return False
        
        # Convert recording to list and normalize timestamps
        frames = list(self._recording)
        if not frames:
            return False
        
        # Normalize timestamps to start from 0
        first_time = frames[0].timestamp
        normalized_frames = [
            MovementFrame(
                position=f.position.copy(),
                timestamp=f.timestamp - first_time
            )
            for f in frames
        ]
        
        # Create clone
        self._current_clone = ChronoClone(normalized_frames, self._player_size)
        self._cooldown_timer = self.CLONE_COOLDOWN
        self._clones_spawned += 1
        
        # Emit event
        self._event_manager.emit(GameEvent.ENTITY_SPAWNED, {
            'type': 'chrono_clone',
            'position': (normalized_frames[0].position.x, normalized_frames[0].position.y)
        })
        
        return True
    
    def update(self, dt: float, player_position: Vector2 = None) -> None:
        """
        Update the clone system.
        
        Args:
            dt: Delta time
            player_position: Current player position for recording
        """
        # Record player position
        if player_position:
            self.record_position(player_position, dt)
        
        # Update cooldown
        if self._cooldown_timer > 0:
            self._cooldown_timer -= dt
        
        # Update active clone
        if self._current_clone:
            self._current_clone.update(dt)
            
            if self._current_clone.completed:
                self._current_clone = None
    
    def render(self, screen: pygame.Surface) -> None:
        """Render the chrono-clone and UI elements."""
        # Render active clone
        if self._current_clone:
            self._current_clone.render(screen)
        
        # Render cooldown indicator
        self._render_cooldown_indicator(screen)
    
    def _render_cooldown_indicator(self, screen: pygame.Surface) -> None:
        """Render the clone cooldown indicator."""
        x = Settings.SCREEN_WIDTH - 120
        y = 140
        
        try:
            font = get_font('Arial', 12)
        except Exception:
            font = pygame.font.Font(None, 14)
        
        # Label
        if self.can_spawn_clone:
            text = "CLONE READY [C]"
            color = (150, 200, 255)
        elif self.has_active_clone:
            text = "CLONE ACTIVE"
            color = (100, 180, 255)
        else:
            text = f"CLONE: {self._cooldown_timer:.1f}s"
            color = (128, 128, 128)
        
        text_surf = font.render(text, True, color)
        screen.blit(text_surf, (x, y))
        
        # Progress bar for cooldown
        bar_width = 100
        bar_height = 4
        
        pygame.draw.rect(screen, COLORS.DARK_GRAY, (x, y + 15, bar_width, bar_height))
        
        if self._cooldown_timer > 0:
            progress = 1.0 - (self._cooldown_timer / self.CLONE_COOLDOWN)
            fill_width = int(bar_width * progress)
            pygame.draw.rect(screen, (150, 200, 255), (x, y + 15, fill_width, bar_height))
        else:
            # Full bar when ready
            pygame.draw.rect(screen, (150, 200, 255), (x, y + 15, bar_width, bar_height))
    
    def get_clone_rect(self) -> Optional[pygame.Rect]:
        """Get the collision rect of the active clone, if any."""
        if self._current_clone and self._current_clone.active:
            return self._current_clone.get_rect()
        return None
    
    def reset(self) -> None:
        """Reset the system (e.g., on level change)."""
        self._recording.clear()
        self._record_timer = 0.0
        self._total_recording_time = 0.0
        self._current_clone = None
        self._cooldown_timer = 0.0
    
    def get_stats(self) -> dict:
        """Get clone statistics."""
        return {
            'clones_spawned': self._clones_spawned,
            'successful_distractions': self._successful_distractions
        }
