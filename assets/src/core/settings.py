"""
Global game configuration and constants.
All tunable parameters are centralized here for easy balancing.

TEMPORAL DEBT 3.0 — Psychological Horror / Neon Abyss Theme
Color Psychology:
  - Deep blacks and dark cyans create unease
  - Pulsing magentas/reds signal danger subconsciously
  - Cool teal calms — then is ripped away during debt spikes
  - Gold accents feel "earned" — anchors, rewards
"""


class Settings:
    """
    Central configuration for TEMPORAL DEBT.
    
    Design Philosophy:
    - All magic numbers are named constants
    - Related settings are grouped logically
    - Difficulty tuned 30-40 % harder than v2
    """
    
    # ===================
    # DISPLAY SETTINGS
    # ===================
    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 720
    FPS = 60
    TITLE = "TEMPORAL DEBT"
    
    TILE_SIZE = 48
    GRID_WIDTH = SCREEN_WIDTH // TILE_SIZE
    GRID_HEIGHT = SCREEN_HEIGHT // TILE_SIZE
    
    # ===================
    # TIME SYSTEM SETTINGS  (+35 % harder)
    # ===================
    
    # Debt accrues faster — every second frozen costs 2.0s (was 1.5)
    DEBT_ACCRUAL_RATE = 2.0
    
    # Tightened tier thresholds and harsher multipliers
    DEBT_TIERS = {
        0: {"name": "clear",      "max_debt": 0,  "interest": 1.0,  "speed": 1.0,  "tint": (0, 0, 0)},
        1: {"name": "mild",       "max_debt": 2,  "interest": 1.1,  "speed": 1.15, "tint": (0, 10, 20)},
        2: {"name": "moderate",   "max_debt": 4,  "interest": 1.4,  "speed": 1.7,  "tint": (40, 0, 30)},
        3: {"name": "severe",     "max_debt": 7,  "interest": 1.8,  "speed": 2.4,  "tint": (100, 10, 40)},
        4: {"name": "critical",   "max_debt": 11, "interest": 2.5,  "speed": 3.5,  "tint": (160, 30, 60)},
        5: {"name": "bankruptcy", "max_debt": 16, "interest": 3.5,  "speed": 5.0,  "tint": (220, 50, 80)},
    }
    
    BANKRUPTCY_THRESHOLD = 16.0   # was 20 — punishes greed faster
    BANKRUPTCY_SURVIVAL_TIME = 4.0
    
    # ===================
    # ANCHOR SYSTEM SETTINGS
    # ===================
    MAX_ANCHORS = 3
    ANCHOR_DECAY_TIME = 22.0      # was 30 — forces quicker decision-making
    ANCHOR_RECALL_DEBT = 3.0      # was 2 — costlier safety net
    
    # ===================
    # PLAYER SETTINGS
    # ===================
    PLAYER_SPEED = 230.0          # was 250 — slightly slower = more tense
    PLAYER_SIZE = (34, 34)        # tighter hitbox
    RESPAWN_INVULN_TIME = 1.0     # was 1.5 — less free time
    
    # ===================
    # ENEMY SETTINGS  (+30-40 % faster / meaner)
    # ===================
    DRONE_SPEED = 160.0           # was 120
    SEEKER_RANGE = 380.0          # was 300
    SEEKER_SPEED = 195.0          # was 150
    HUNTER_SPEED = 240.0          # was 180
    SHADOW_SPAWN_DEBT = 7.0       # was 10 — shadows arrive earlier
    SHADOW_SPEED = 135.0          # was 100
    
    # ===================
    # DANGER ZONE PUNISHMENT
    # ===================
    DANGER_ZONE_DAMAGE_RATE = 1.5   # debt/sec while standing in danger zone
    DANGER_ZONE_SLOW_FACTOR = 0.65  # player moves 35 % slower in danger
    SAFE_ZONE_HEAL_RATE = 0.3       # debt reduced/sec in safe zone (slow)
    
    # ===================
    # INTERACTABLE SETTINGS
    # ===================
    DEBT_SINK_AMOUNT = 2.5        # was 3 — less generous
    DEBT_BOMB_PAYLOAD = 6.0       # was 5 — harsher
    DEBT_BOMB_RADIUS = 170.0
    DOOR_OPEN_DURATION = 2.5      # was 3 — tighter timing
    
    # ===================
    # ECHO SYSTEM SETTINGS
    # ===================
    ECHO_PREDICTION_DURATION = 3.0
    ECHO_INTERVAL = 0.1
    ECHO_BASE_ALPHA = 180
    ECHO_FADE_RATE = 0.7
    
    # ===================
    # VISUAL SETTINGS — Neon Abyss / Psychological Theme
    # ===================
    
    class Colors:
        # Core palette
        WHITE       = (240, 240, 250)
        BLACK       = (6, 6, 14)
        GRAY        = (100, 105, 120)
        DARK_GRAY   = (35, 38, 50)
        
        # Player — cool teal, shifts to electric cyan when frozen
        PLAYER        = (0, 220, 210)
        PLAYER_FROZEN = (100, 255, 255)
        PLAYER_TRAIL  = (0, 180, 170, 60)   # after-image ghost
        
        # Environment — dark, moody
        WALL  = (28, 30, 48)
        WALL_HIGHLIGHT = (50, 55, 80)
        WALL_SHADOW    = (14, 14, 28)
        FLOOR = (14, 16, 26)
        FLOOR_ALT = (18, 20, 32)
        
        # Enemies — aggressive warm tones
        DRONE       = (255, 60, 80)      # neon red-pink
        DRONE_GLOW  = (255, 60, 80, 60)
        HUNTER      = (200, 50, 220)     # electric purple
        HUNTER_GLOW = (200, 50, 220, 80)
        SHADOW      = (60, 0, 80)
        SHADOW_EYE  = (255, 30, 90)
        
        # NEW enemies
        PHASE_SHIFTER = (255, 170, 0)    # hot amber — teleporting enemy
        DEBT_LEECH    = (180, 255, 0)    # acid green — drains your debt upward
        SWARM_DRONE   = (255, 100, 150)  # pink swarm units
        
        # Interactable colors
        DEBT_SINK   = (0, 255, 180)
        DEBT_MIRROR = (180, 180, 255)
        DEBT_BOMB   = (255, 180, 50)
        DOOR_CLOSED = (120, 50, 20)
        DOOR_OPEN   = (40, 200, 100)
        
        # Effects — gold anchors, blue echoes
        ANCHOR        = (255, 200, 50)
        ANCHOR_FADING = (255, 200, 50, 100)
        ECHO          = (80, 140, 255)
        
        # Time freeze overlay — desaturated blue wash
        FREEZE_TINT = (30, 60, 100, 90)
        
        # Debt tier colors — psychological gradient:
        # green-calm → amber-anxiety → red-panic → magenta-doom
        TIER_CLEAR      = (0, 230, 160)
        TIER_MILD       = (160, 220, 50)
        TIER_MODERATE   = (240, 200, 30)
        TIER_SEVERE     = (255, 130, 30)
        TIER_CRITICAL   = (255, 50, 70)
        TIER_BANKRUPTCY = (220, 0, 80)
        
        # UI-specific
        HUD_BACKGROUND = (10, 12, 22, 210)
        HUD_BORDER     = (50, 60, 90)
        DEBT_BAR_BG    = (25, 28, 42)
        DEBT_BAR_FILL  = (255, 60, 80)
        
        EXIT_ZONE       = (0, 255, 140)
        EXIT_ZONE_GLOW  = (0, 255, 140, 40)
        CHECKPOINT       = (255, 230, 80)
        CHECKPOINT_GLOW  = (255, 230, 80, 50)
        
        # Danger/safe zone
        DANGER_ZONE      = (255, 40, 60)
        DANGER_ZONE_BG   = (80, 10, 20, 80)
        SAFE_ZONE        = (40, 140, 255)
        SAFE_ZONE_BG     = (20, 40, 80, 60)
        
        # Menu accents
        MENU_BG        = (8, 10, 20)
        MENU_GRID      = (18, 22, 40)
        MENU_ACCENT    = (0, 200, 255)
        MENU_ACCENT2   = (220, 50, 255)
        MENU_TEXT       = (200, 210, 230)
        MENU_TEXT_DIM   = (100, 110, 130)
    
    # ===================
    # SCREEN EFFECT SETTINGS
    # ===================
    SHAKE_INTENSITY_BASE = 7      # was 5 — more impactful
    SHAKE_DECAY = 0.88
    VIGNETTE_INTENSITY = 0.4
    
    # Chromatic aberration on high debt
    CHROMATIC_OFFSET_MAX = 4
    
    # ===================
    # V2.0 / V3.0 FEATURE SETTINGS
    # ===================
    
    # Temporal Momentum System
    MOMENTUM_MAX = 10.0
    MOMENTUM_BUILD_RATE = 0.8     # was 1.0 — harder to build
    MOMENTUM_DRAIN_RATE = 3.0     # was 2.0 — drains faster
    MOMENTUM_DEBT_REDUCTION = 0.04
    
    # Resonance System — more frequent, harsher
    RESONANCE_MIN_INTERVAL = 10.0
    RESONANCE_MAX_INTERVAL = 16.0
    RESONANCE_WARNING_DURATION = 1.5
    RESONANCE_WAVE_DURATION = 2.0
    RESONANCE_FROZEN_PENALTY = 4.5
    RESONANCE_MOVING_BONUS = 0.3
    
    # Chrono-Clone System
    CLONE_RECORDING_DURATION = 4.0
    CLONE_COOLDOWN = 10.0
    
    # Time Reversal System
    REVERSAL_COST = 10.0
    REVERSAL_DURATION = 2.5
    REVERSAL_USES_PER_LIFE = 1
    
    # Temporal Fragments
    FRAGMENT_DEBT_REDUCTION = 1.0   # was 1.5
    FRAGMENTS_FOR_BURST = 5
    BURST_DURATION = 1.5
    BURST_TIME_SCALE = 0.35
    
    # Time Dilation Zones
    SAFE_ZONE_MULTIPLIER = 0.8     # was 0.75
    DANGER_ZONE_MULTIPLIER = 2.5   # was 2.0
    
    # Debt Transfer Pods
    POD_MAX_DEBT = 4.0
    POD_DEPOSIT_RATE = 1.5
    POD_RELEASE_RADIUS = 170.0
    
    # ===================
    # NEW: PHASE SHIFTER ENEMY
    # ===================
    PHASE_SHIFTER_SPEED = 100.0
    PHASE_SHIFTER_TELEPORT_COOLDOWN = 4.0
    PHASE_SHIFTER_TELEPORT_RANGE = 200.0
    
    # ===================
    # NEW: DEBT LEECH ENEMY
    # ===================
    DEBT_LEECH_SPEED = 70.0
    DEBT_LEECH_RANGE = 180.0
    DEBT_LEECH_DRAIN_RATE = 2.0   # debt/sec added to player when close
    
    # ===================
    # NEW: SWARM DRONE
    # ===================
    SWARM_DRONE_SPEED = 200.0
    SWARM_DRONE_SIZE = (24, 24)
    SWARM_DRONE_LIFETIME = 6.0
    
    # ===================
    # AUDIO
    # ===================
    SOUND_ENABLED = False
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
    GOD_MODE = False


# Create a convenient alias
COLORS = Settings.Colors
