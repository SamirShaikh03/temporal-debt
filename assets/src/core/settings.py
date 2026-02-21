"""
Global game configuration and constants.
All tunable parameters are centralized here for easy balancing.
"""


class Settings:
    """
    Central configuration for TEMPORAL DEBT.
    
    Design Philosophy:
    - All magic numbers are named constants
    - Related settings are grouped logically
    - Comments explain the design intent
    """
    
    # ===================
    # DISPLAY SETTINGS
    # ===================
    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 720
    FPS = 60
    TITLE = "TEMPORAL DEBT"
    
    # Tile size affects level design granularity
    TILE_SIZE = 48  # Smaller tiles for bigger levels
    
    # Grid dimensions for level design
    GRID_WIDTH = SCREEN_WIDTH // TILE_SIZE  # ~26 tiles
    GRID_HEIGHT = SCREEN_HEIGHT // TILE_SIZE  # ~15 tiles (with HUD space)
    
    # ===================
    # TIME SYSTEM SETTINGS
    # ===================
    
    # Debt accrual: 1 second frozen = 1.5 seconds of debt
    # This creates the "interest" feeling - you always owe more than you borrowed
    DEBT_ACCRUAL_RATE = 1.5
    
    # Debt tiers define escalating consequences
    # Structure: (max_debt, interest_rate, world_speed, color_intensity)
    DEBT_TIERS = {
        0: {"name": "clear", "max_debt": 0, "interest": 1.0, "speed": 1.0, "tint": (0, 0, 0)},
        1: {"name": "mild", "max_debt": 3, "interest": 1.0, "speed": 1.0, "tint": (0, 0, 0)},
        2: {"name": "moderate", "max_debt": 6, "interest": 1.25, "speed": 1.5, "tint": (50, 0, 0)},
        3: {"name": "severe", "max_debt": 10, "interest": 1.5, "speed": 2.0, "tint": (100, 20, 0)},
        4: {"name": "critical", "max_debt": 15, "interest": 2.0, "speed": 3.0, "tint": (150, 40, 0)},
        5: {"name": "bankruptcy", "max_debt": 20, "interest": 3.0, "speed": 4.0, "tint": (200, 60, 0)},
    }
    
    # Bankruptcy threshold - beyond this, severe consequences
    BANKRUPTCY_THRESHOLD = 20.0
    
    # Bankruptcy recovery requires surviving this duration
    BANKRUPTCY_SURVIVAL_TIME = 5.0
    
    # ===================
    # ANCHOR SYSTEM SETTINGS
    # ===================
    
    # Maximum simultaneous anchors
    MAX_ANCHORS = 3
    
    # Anchors decay after this many real seconds
    ANCHOR_DECAY_TIME = 30.0
    
    # Recalling to anchor adds instant debt
    ANCHOR_RECALL_DEBT = 2.0
    
    # ===================
    # PLAYER SETTINGS
    # ===================
    
    # Base movement speed (pixels per second)
    PLAYER_SPEED = 250.0
    
    # Player size for collision (slightly smaller for tighter spaces)
    PLAYER_SIZE = (36, 36)
    
    # Respawn invulnerability duration
    RESPAWN_INVULN_TIME = 1.5
    
    # ===================
    # ENEMY SETTINGS
    # ===================
    
    # Patrol drone speed
    DRONE_SPEED = 120.0
    
    # Seeker drone detection range
    SEEKER_RANGE = 300.0
    SEEKER_SPEED = 150.0
    
    # Temporal Hunter speed (only moves during freeze)
    HUNTER_SPEED = 180.0
    
    # Debt Shadow spawn threshold
    SHADOW_SPAWN_DEBT = 10.0
    SHADOW_SPEED = 100.0
    
    # ===================
    # INTERACTABLE SETTINGS
    # ===================
    
    # Debt sink absorption
    DEBT_SINK_AMOUNT = 3.0
    
    # Debt bomb payload
    DEBT_BOMB_PAYLOAD = 5.0
    DEBT_BOMB_RADIUS = 150.0
    
    # Timed door settings
    DOOR_OPEN_DURATION = 3.0
    
    # ===================
    # ECHO SYSTEM SETTINGS
    # ===================
    
    # How far into the future to predict
    ECHO_PREDICTION_DURATION = 3.0
    
    # Time between echo frames
    ECHO_INTERVAL = 0.1
    
    # Echo visibility
    ECHO_BASE_ALPHA = 180
    ECHO_FADE_RATE = 0.7  # Each subsequent echo is this fraction of previous
    
    # ===================
    # VISUAL SETTINGS
    # ===================
    
    # Colors
    class Colors:
        # UI Colors
        WHITE = (255, 255, 255)
        BLACK = (0, 0, 0)
        GRAY = (128, 128, 128)
        DARK_GRAY = (64, 64, 64)
        
        # Game element colors
        PLAYER = (100, 200, 255)
        PLAYER_FROZEN = (150, 220, 255)
        
        WALL = (60, 60, 80)
        FLOOR = (30, 30, 40)
        
        # Enemy colors
        DRONE = (255, 100, 100)
        HUNTER = (180, 50, 180)
        SHADOW = (40, 0, 60)
        
        # Interactable colors
        DEBT_SINK = (100, 255, 150)
        DEBT_MIRROR = (200, 200, 255)
        DEBT_BOMB = (255, 200, 100)
        DOOR_CLOSED = (139, 69, 19)
        DOOR_OPEN = (69, 139, 69)
        
        # Effect colors
        ANCHOR = (255, 215, 0)
        ANCHOR_FADING = (255, 215, 0, 128)
        ECHO = (100, 150, 255)
        
        # Time freeze overlay
        FREEZE_TINT = (50, 80, 120, 80)
        
        # Debt tier colors (progressive red shift)
        TIER_CLEAR = (50, 200, 100)
        TIER_MILD = (150, 200, 50)
        TIER_MODERATE = (200, 200, 50)
        TIER_SEVERE = (255, 150, 50)
        TIER_CRITICAL = (255, 80, 50)
        TIER_BANKRUPTCY = (255, 0, 50)
        
        # UI specific
        HUD_BACKGROUND = (20, 20, 30, 200)
        DEBT_BAR_BG = (40, 40, 50)
        DEBT_BAR_FILL = (255, 100, 100)
        
        EXIT_ZONE = (100, 255, 100)
        CHECKPOINT = (255, 255, 100)
    
    # ===================
    # SCREEN EFFECT SETTINGS
    # ===================
    
    # Screen shake parameters
    SHAKE_INTENSITY_BASE = 5
    SHAKE_DECAY = 0.9
    
    # Vignette during high debt
    VIGNETTE_INTENSITY = 0.3
    
    # ===================
    # V2.0 FEATURE SETTINGS
    # ===================
    
    # Temporal Momentum System
    MOMENTUM_MAX = 10.0
    MOMENTUM_BUILD_RATE = 1.0  # Points per second
    MOMENTUM_DRAIN_RATE = 2.0  # Points per second during freeze
    MOMENTUM_DEBT_REDUCTION = 0.05  # 5% per point
    
    # Resonance System
    RESONANCE_MIN_INTERVAL = 15.0
    RESONANCE_MAX_INTERVAL = 20.0
    RESONANCE_WARNING_DURATION = 2.0
    RESONANCE_WAVE_DURATION = 1.5
    RESONANCE_FROZEN_PENALTY = 3.0
    RESONANCE_MOVING_BONUS = 0.5
    
    # Chrono-Clone System
    CLONE_RECORDING_DURATION = 5.0
    CLONE_COOLDOWN = 8.0
    
    # Time Reversal System
    REVERSAL_COST = 8.0
    REVERSAL_DURATION = 3.0
    REVERSAL_USES_PER_LIFE = 1
    
    # Temporal Fragments
    FRAGMENT_DEBT_REDUCTION = 1.5
    FRAGMENTS_FOR_BURST = 5
    BURST_DURATION = 2.0
    BURST_TIME_SCALE = 0.3
    
    # Time Dilation Zones
    SAFE_ZONE_MULTIPLIER = 0.75
    DANGER_ZONE_MULTIPLIER = 2.0
    
    # Debt Transfer Pods
    POD_MAX_DEBT = 5.0
    POD_DEPOSIT_RATE = 2.0
    POD_RELEASE_RADIUS = 150.0
    
    # ===================
    # AUDIO HOOKS (for future implementation)
    # ===================
    
    SOUND_ENABLED = False  # Set to True when audio files exist
    
    # Volume levels
    MASTER_VOLUME = 0.8
    SFX_VOLUME = 0.7
    MUSIC_VOLUME = 0.5
    
    # ===================
    # DEBUG SETTINGS
    # ===================
    
    DEBUG_MODE = False
    SHOW_COLLISION_BOXES = False
    SHOW_PATROL_PATHS = False
    SHOW_FPS = True
    GOD_MODE = False  # Invulnerability for testing


# Create a convenient alias
COLORS = Settings.Colors
