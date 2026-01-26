"""
Debt Manager - Tracks and calculates temporal debt.

The Debt Manager is the consequence system for time manipulation.
Every second of frozen time creates debt that must be repaid with interest.

Design Philosophy:
This system makes the abstract concept of "time debt" tangible through:
- Clear tiers with escalating consequences
- Visual feedback via events
- Economic metaphors (interest, bankruptcy)
"""

from typing import Tuple
from ..core.events import EventManager, GameEvent, get_event_manager
from ..core.settings import Settings



class DebtManager:
    """
    Manages temporal debt accumulation and repayment.
    
    Core Concepts:
    - Debt accrues when time is frozen (at 1.5x rate)
    - Debt repays automatically when time flows
    - Higher debt = higher interest on new debt
    - Extreme debt triggers "bankruptcy" state
    
    The debt system creates a feedback loop:
    High debt → faster world → harder gameplay → need to freeze → more debt
    
    This is intentional - it creates escalating tension and rewards
    players who use time manipulation sparingly.
    """
    
    def __init__(self, event_manager: EventManager = None):
        """
        Initialize the Debt Manager.
        
        Args:
            event_manager: Event system for broadcasting changes
        """
        # Core state
        self._current_debt = 0.0  # Current debt in seconds
        self._current_tier = 0  # Current debt tier (0-5)
        
        # Bankruptcy state
        self._is_bankrupt = False
        self._bankruptcy_timer = 0.0
        
        # Statistics
        self._total_debt_accrued = 0.0
        self._total_debt_repaid = 0.0
        self._peak_debt = 0.0
        self._times_bankrupt = 0
        
        # References
        self._event_manager = event_manager or get_event_manager()
        self._time_engine = None  # Set later via set_time_engine()
        
        # Cache previous tier to detect changes
        self._previous_tier = 0
    
    @property
    def current_debt(self) -> float:
        """Current debt in seconds."""
        return self._current_debt
    
    @property
    def current_tier(self) -> int:
        """Current debt tier (0-5)."""
        return self._current_tier
    
    @property
    def is_bankrupt(self) -> bool:
        """Whether currently in bankruptcy state."""
        return self._is_bankrupt
    
    @property
    def total_debt_accrued(self) -> float:
        """Total debt accrued over lifetime."""
        return self._total_debt_accrued
    
    def set_time_engine(self, time_engine) -> None:
        """Set reference to time engine for updates."""
        self._time_engine = time_engine
    
    def accrue_debt(self, amount: float) -> None:
        """
        Add debt with interest based on current tier.
        
        Args:
            amount: Base debt amount in seconds
        
        The actual debt added is: amount × current_interest_rate
        This creates compounding difficulty at higher tiers.
        """
        if amount <= 0:
            return
        
        # Apply interest from current tier
        interest_rate = self.get_interest_rate()
        actual_debt = amount * interest_rate
        
        # Add to debt
        old_debt = self._current_debt
        self._current_debt += actual_debt
        
        # Update statistics
        self._total_debt_accrued += actual_debt
        self._peak_debt = max(self._peak_debt, self._current_debt)
        
        # Check for tier changes
        self._update_tier()
        
        # Check for bankruptcy
        if self._current_debt >= Settings.BANKRUPTCY_THRESHOLD and not self._is_bankrupt:
            self._trigger_bankruptcy()
        
        # Emit debt changed event
        self._event_manager.emit(GameEvent.DEBT_CHANGED, {
            'old_debt': old_debt,
            'new_debt': self._current_debt,
            'change': actual_debt,
            'tier': self._current_tier
        })
    
    def repay_debt(self, real_dt: float) -> None:
        """
        Repay debt over time.
        
        Args:
            real_dt: Real time passed (repayment happens at real time rate)
        
        Debt repays at 1:1 rate with real time, but the world
        is moving faster, creating the "rush" feeling.
        """
        if self._current_debt <= 0:
            return
        
        old_debt = self._current_debt
        
        # Repay at real time rate
        # Higher tiers make the world faster but don't change repayment speed
        repayment = real_dt
        self._current_debt = max(0, self._current_debt - repayment)
        self._total_debt_repaid += repayment
        
        # Check if bankruptcy recovery
        if self._is_bankrupt:
            self._bankruptcy_timer += real_dt
            if self._bankruptcy_timer >= Settings.BANKRUPTCY_SURVIVAL_TIME:
                self._end_bankruptcy()
            elif self._current_debt == 0:
                self._end_bankruptcy()
        
        # Update tier
        self._update_tier()
        
        # Emit change event
        self._event_manager.emit(GameEvent.DEBT_CHANGED, {
            'old_debt': old_debt,
            'new_debt': self._current_debt,
            'change': -repayment,
            'tier': self._current_tier
        })
    
    def absorb_debt(self, amount: float) -> float:
        """
        Immediately remove debt (from debt sinks).
        
        Args:
            amount: Amount of debt to absorb
        
        Returns:
            Actual amount absorbed (may be less if debt was lower)
        """
        actual_absorbed = min(amount, self._current_debt)
        old_debt = self._current_debt
        self._current_debt -= actual_absorbed
        
        self._update_tier()
        
        # Emit absorption event
        self._event_manager.emit(GameEvent.DEBT_ABSORBED, {
            'amount': actual_absorbed,
            'remaining_debt': self._current_debt
        })
        
        self._event_manager.emit(GameEvent.DEBT_CHANGED, {
            'old_debt': old_debt,
            'new_debt': self._current_debt,
            'change': -actual_absorbed,
            'tier': self._current_tier
        })
        
        return actual_absorbed
    
    def _update_tier(self) -> None:
        """
        Update the current debt tier based on debt level.
        
        Tier thresholds (from Settings):
        - Tier 0: 0 debt (clear)
        - Tier 1: 0-3 seconds (mild)
        - Tier 2: 3-6 seconds (moderate)
        - Tier 3: 6-10 seconds (severe)
        - Tier 4: 10-15 seconds (critical)
        - Tier 5: 15+ seconds (bankruptcy)
        """
        # Determine new tier based on debt
        new_tier = 0
        for tier_num in range(5, -1, -1):
            tier_data = Settings.DEBT_TIERS[tier_num]
            if self._current_debt >= tier_data['max_debt']:
                new_tier = tier_num
                break
            elif tier_num == 0:
                new_tier = 0 if self._current_debt == 0 else 1
        
        # Correct tier calculation
        if self._current_debt == 0:
            new_tier = 0
        elif self._current_debt <= 3:
            new_tier = 1
        elif self._current_debt <= 6:
            new_tier = 2
        elif self._current_debt <= 10:
            new_tier = 3
        elif self._current_debt <= 15:
            new_tier = 4
        else:
            new_tier = 5
        
        # Emit event if tier changed
        if new_tier != self._previous_tier:
            self._current_tier = new_tier
            self._event_manager.emit(GameEvent.DEBT_TIER_CHANGED, {
                'old_tier': self._previous_tier,
                'new_tier': new_tier,
                'tier_name': Settings.DEBT_TIERS[new_tier]['name']
            })
            self._previous_tier = new_tier
    
    def _trigger_bankruptcy(self) -> None:
        """Enter bankruptcy state - extreme consequences."""
        self._is_bankrupt = True
        self._bankruptcy_timer = 0.0
        self._times_bankrupt += 1
        
        self._event_manager.emit(GameEvent.BANKRUPTCY_STARTED, {
            'debt': self._current_debt,
            'times_bankrupt': self._times_bankrupt
        })
    
    def _end_bankruptcy(self) -> None:
        """Exit bankruptcy state."""
        self._is_bankrupt = False
        self._bankruptcy_timer = 0.0
        
        self._event_manager.emit(GameEvent.BANKRUPTCY_ENDED, {
            'debt': self._current_debt,
            'survival_time': Settings.BANKRUPTCY_SURVIVAL_TIME
        })
    
    def get_interest_rate(self) -> float:
        """
        Get current interest rate for new debt.
        
        Returns:
            Interest multiplier (1.0 = no interest)
        """
        return Settings.DEBT_TIERS[self._current_tier]['interest']
    
    def get_world_speed_multiplier(self) -> float:
        """
        Get world speed multiplier based on debt tier.
        
        Returns:
            Speed multiplier (1.0 = normal, higher = faster)
        """
        if self._is_bankrupt:
            return 5.0  # Extreme speed during bankruptcy
        return Settings.DEBT_TIERS[self._current_tier]['speed']
    
    def get_tier_tint(self) -> Tuple[int, int, int]:
        """
        Get the screen tint color for current tier.
        
        Returns:
            RGB tuple for screen overlay
        """
        return Settings.DEBT_TIERS[self._current_tier]['tint']
    
    def get_debt_percentage(self) -> float:
        """
        Get debt as percentage of bankruptcy threshold.
        
        Returns:
            0.0 to 1.0+ (can exceed 1.0 if beyond threshold)
        """
        return self._current_debt / Settings.BANKRUPTCY_THRESHOLD
    
    def reset(self) -> None:
        """Reset debt to zero (on level restart)."""
        self._current_debt = 0.0
        self._current_tier = 0
        self._is_bankrupt = False
        self._bankruptcy_timer = 0.0
        self._previous_tier = 0
        
        self._event_manager.emit(GameEvent.DEBT_CHANGED, {
            'old_debt': self._current_debt,
            'new_debt': 0,
            'change': 0,
            'tier': 0
        })
    
    def get_stats(self) -> dict:
        """
        Get debt statistics.
        
        Returns:
            Dictionary of current state and lifetime stats
        """
        return {
            'current_debt': self._current_debt,
            'current_tier': self._current_tier,
            'tier_name': Settings.DEBT_TIERS[self._current_tier]['name'],
            'is_bankrupt': self._is_bankrupt,
            'total_accrued': self._total_debt_accrued,
            'total_repaid': self._total_debt_repaid,
            'peak_debt': self._peak_debt,
            'times_bankrupt': self._times_bankrupt,
            'interest_rate': self.get_interest_rate(),
            'world_speed': self.get_world_speed_multiplier()
        }
