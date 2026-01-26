"""
Time Engine - The core system that manages time manipulation.

This is the heart of TEMPORAL DEBT's unique mechanic. The Time Engine:
- Tracks whether time is frozen
- Calculates the appropriate delta time for entities
- Coordinates with the Debt Manager
- Emits events for other systems to respond

Design Philosophy:
The Time Engine doesn't directly modify entities. Instead, it provides
time information that entities use to update themselves. This keeps
the system decoupled and testable.
"""

from typing import TYPE_CHECKING
from ..core.events import EventManager, GameEvent, get_event_manager
from ..core.settings import Settings

if TYPE_CHECKING:
    from ..systems.debt_manager import DebtManager


class TimeEngine:
    """
    Manages the flow of time in the game world.
    
    The Time Engine is responsible for:
    1. Tracking freeze state (when player holds SPACE)
    2. Providing scaled delta time based on debt tier
    3. Coordinating time events across systems
    
    Time Concepts:
    - real_dt: Actual time passed (frame time)
    - game_dt: Time experienced by game entities (can be 0 when frozen, >1 when repaying)
    - time_scale: Multiplier applied to real_dt to get game_dt
    """
    
    def __init__(self, debt_manager: 'DebtManager' = None, event_manager: EventManager = None):
        """
        Initialize the Time Engine.
        
        Args:
            debt_manager: Reference to debt system for speed calculations
            event_manager: Event system for broadcasting state changes
        """
        # State
        self._frozen = False
        self._time_scale = 1.0  # Current time multiplier
        
        # Tracking
        self._freeze_duration = 0.0  # How long current freeze has lasted
        self._total_freeze_time = 0.0  # Lifetime frozen time
        
        # References
        self._debt_manager = debt_manager
        self._event_manager = event_manager or get_event_manager()
        
        # Cached values
        self._last_game_dt = 0.0
    
    @property
    def frozen(self) -> bool:
        """Whether time is currently frozen."""
        return self._frozen
    
    @property
    def time_scale(self) -> float:
        """Current time scale multiplier."""
        return self._time_scale
    
    @property
    def freeze_duration(self) -> float:
        """Duration of current freeze in seconds."""
        return self._freeze_duration
    
    def set_debt_manager(self, debt_manager: 'DebtManager') -> None:
        """Set the debt manager reference after initialization."""
        self._debt_manager = debt_manager
    
    def freeze(self) -> None:
        """
        Begin a time freeze.
        
        Called when player starts holding SPACE.
        The freeze continues until unfreeze() is called.
        """
        if self._frozen:
            return  # Already frozen
        
        self._frozen = True
        self._freeze_duration = 0.0
        self._time_scale = 0.0  # World stops
        
        # Notify other systems
        self._event_manager.emit(GameEvent.TIME_FROZEN, {
            'total_frozen_time': self._total_freeze_time
        })
    
    def unfreeze(self) -> None:
        """
        End a time freeze.
        
        Called when player releases SPACE.
        Time resumes, potentially at accelerated rate due to debt.
        """
        if not self._frozen:
            return  # Already unfrozen
        
        freeze_cost = self._freeze_duration
        
        self._frozen = False
        self._total_freeze_time += self._freeze_duration
        
        # Calculate new time scale based on debt
        self._update_time_scale()
        
        # Notify other systems
        self._event_manager.emit(GameEvent.TIME_UNFROZEN, {
            'freeze_duration': freeze_cost,
            'new_time_scale': self._time_scale
        })
    
    def update(self, real_dt: float) -> None:
        """
        Update the time engine each frame.
        
        Args:
            real_dt: Real time passed since last frame (from clock)
        
        This method:
        1. Tracks freeze duration
        2. Updates time scale based on debt
        3. Calculates the game_dt for this frame
        """
        if self._frozen:
            # Track how long we've been frozen
            self._freeze_duration += real_dt
            
            # Accrue debt while frozen
            if self._debt_manager:
                debt_amount = real_dt * Settings.DEBT_ACCRUAL_RATE
                self._debt_manager.accrue_debt(debt_amount)
            
            # World is stopped
            self._last_game_dt = 0.0
        else:
            # Time is flowing - calculate scaled dt
            self._update_time_scale()
            self._last_game_dt = real_dt * self._time_scale
            
            # Repay debt during normal time
            if self._debt_manager and self._debt_manager.current_debt > 0:
                self._debt_manager.repay_debt(real_dt)
    
    def _update_time_scale(self) -> None:
        """
        Update time scale based on current debt tier.
        
        Higher debt = faster world = harder game.
        """
        if self._debt_manager:
            self._time_scale = self._debt_manager.get_world_speed_multiplier()
        else:
            self._time_scale = 1.0
        
        # Notify if scale changed significantly
        # (Could add hysteresis here to avoid spam)
    
    def get_game_dt(self) -> float:
        """
        Get the delta time for game entities.
        
        Returns:
            Scaled delta time. 0 when frozen, >1.0 when repaying debt.
        """
        return self._last_game_dt
    
    def get_player_dt(self, real_dt: float) -> float:
        """
        Get delta time for player movement.
        
        The player can always move, even in frozen time.
        During debt repayment, player moves at normal speed
        while world accelerates around them.
        
        Returns:
            Delta time for player (always based on real_dt)
        """
        return real_dt
    
    def get_world_speed(self) -> float:
        """
        Get current world speed multiplier.
        
        Returns:
            1.0 for normal, 0.0 for frozen, >1.0 for accelerated
        """
        return self._time_scale
    
    def is_frozen(self) -> bool:
        """Check if time is currently frozen."""
        return self._frozen
    
    def reset(self) -> None:
        """
        Reset the time engine to initial state.
        Called on level restart or game reset.
        """
        self._frozen = False
        self._time_scale = 1.0
        self._freeze_duration = 0.0
        self._last_game_dt = 0.0
        # Note: total_freeze_time persists (lifetime stat)
    
    def get_stats(self) -> dict:
        """
        Get time engine statistics.
        
        Returns:
            Dictionary of current state and stats
        """
        return {
            'frozen': self._frozen,
            'time_scale': self._time_scale,
            'freeze_duration': self._freeze_duration,
            'total_freeze_time': self._total_freeze_time
        }
