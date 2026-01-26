# TEMPORAL DEBT
## Technical Architecture Document

---

# 1. PROJECT STRUCTURE

```
temporal_debt/
│
├── main.py                     # Entry point
├── requirements.txt            # Dependencies
├── README.md                   # Project documentation
│
├── docs/
│   ├── GAME_DESIGN_DOCUMENT.md
│   └── TECHNICAL_ARCHITECTURE.md
│
├── src/
│   ├── __init__.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── game.py             # Main game class
│   │   ├── settings.py         # Global configuration
│   │   ├── events.py           # Custom event system
│   │   └── utils.py            # Utility functions
│   │
│   ├── systems/
│   │   ├── __init__.py
│   │   ├── time_engine.py      # Time manipulation system
│   │   ├── debt_manager.py     # Debt tracking and interest
│   │   ├── echo_system.py      # Temporal echo predictions
│   │   ├── anchor_system.py    # Time anchor management
│   │   ├── collision.py        # Collision detection
│   │   └── audio_manager.py    # Sound hooks and management
│   │
│   ├── entities/
│   │   ├── __init__.py
│   │   ├── base_entity.py      # Base entity class
│   │   ├── player.py           # Player character
│   │   ├── enemies.py          # Enemy types
│   │   ├── hazards.py          # Environmental hazards
│   │   └── interactables.py    # Interactive objects
│   │
│   ├── levels/
│   │   ├── __init__.py
│   │   ├── level_manager.py    # Level loading and transitions
│   │   ├── level_data.py       # Level definitions
│   │   └── tile.py             # Tile and environment classes
│   │
│   ├── ui/
│   │   ├── __init__.py
│   │   ├── hud.py              # In-game HUD
│   │   ├── menus.py            # Menu screens
│   │   ├── feedback.py         # Visual feedback effects
│   │   └── transitions.py      # Screen transitions
│   │
│   └── effects/
│       ├── __init__.py
│       ├── particles.py        # Particle systems
│       ├── screen_effects.py   # Post-processing effects
│       └── shaders.py          # Color manipulation
│
└── assets/
    ├── fonts/
    ├── sounds/
    └── sprites/
```

---

# 2. CLASS ARCHITECTURE

## 2.1 Core Classes

### Game (src/core/game.py)
```
Game
├── Properties
│   ├── screen: pygame.Surface
│   ├── clock: pygame.Clock
│   ├── running: bool
│   ├── state: GameState
│   ├── time_engine: TimeEngine
│   ├── debt_manager: DebtManager
│   ├── level_manager: LevelManager
│   └── ui_manager: UIManager
│
├── Methods
│   ├── run() → Main game loop
│   ├── handle_events() → Process input
│   ├── update(dt) → Update game state
│   ├── render() → Draw everything
│   ├── change_state(new_state) → State transitions
│   └── quit() → Cleanup and exit
```

### Settings (src/core/settings.py)
```
Settings (Constants)
├── Display
│   ├── SCREEN_WIDTH: 1280
│   ├── SCREEN_HEIGHT: 720
│   ├── FPS: 60
│   └── TITLE: "TEMPORAL DEBT"
│
├── Gameplay
│   ├── DEBT_ACCRUAL_RATE: 1.5
│   ├── DEBT_TIERS: dict[range, tier_config]
│   ├── MAX_ANCHORS: 3
│   ├── ANCHOR_DECAY_TIME: 30.0
│   └── BANKRUPTCY_THRESHOLD: 20.0
│
├── Physics
│   ├── PLAYER_SPEED: 200
│   ├── GRAVITY: 0 (top-down game)
│   └── TILE_SIZE: 64
│
└── Colors
    ├── UI colors
    ├── Debt tier colors
    └── Effect colors
```

## 2.2 System Classes

### TimeEngine (src/systems/time_engine.py)
```
TimeEngine
├── Properties
│   ├── frozen: bool
│   ├── time_scale: float (1.0 = normal)
│   ├── frozen_duration: float
│   ├── debt_manager: DebtManager (reference)
│   └── affected_entities: list[Entity]
│
├── Methods
│   ├── freeze() → Start time freeze
│   ├── unfreeze() → End time freeze
│   ├── update(real_dt) → Update time calculations
│   ├── get_game_dt() → Return scaled delta time
│   ├── get_world_speed() → Current world speed multiplier
│   └── is_frozen() → Check freeze state
│
├── Events Emitted
│   ├── TIME_FROZEN
│   ├── TIME_UNFROZEN
│   └── TIME_SCALE_CHANGED
```

### DebtManager (src/systems/debt_manager.py)
```
DebtManager
├── Properties
│   ├── current_debt: float (seconds)
│   ├── total_debt_accrued: float (lifetime)
│   ├── current_tier: int (0-4)
│   ├── interest_rate: float
│   ├── is_bankrupt: bool
│   ├── repayment_rate: float
│   └── time_engine: TimeEngine (reference)
│
├── Methods
│   ├── accrue_debt(amount) → Add debt with interest
│   ├── repay_debt(amount) → Remove debt
│   ├── update(dt) → Process debt changes
│   ├── get_tier() → Current debt tier
│   ├── get_interest_rate() → Current interest rate
│   ├── get_world_speed_multiplier() → Speed for current tier
│   ├── trigger_bankruptcy() → Enter bankruptcy state
│   ├── recover_from_bankruptcy() → Exit bankruptcy
│   └── absorb_debt(amount) → External debt reduction (sinks)
│
├── Events Emitted
│   ├── DEBT_CHANGED
│   ├── TIER_CHANGED
│   ├── BANKRUPTCY_STARTED
│   └── BANKRUPTCY_ENDED
```

### EchoSystem (src/systems/echo_system.py)
```
EchoSystem
├── Properties
│   ├── echoes: dict[entity_id, list[EchoFrame]]
│   ├── prediction_duration: float (3.0 seconds)
│   ├── echo_interval: float (0.1 seconds)
│   ├── accuracy_modifier: float (based on debt)
│   └── active: bool
│
├── Methods
│   ├── activate() → Start generating echoes
│   ├── deactivate() → Stop generating echoes
│   ├── update(entities) → Recalculate predictions
│   ├── predict_path(entity) → Calculate future positions
│   ├── render(screen) → Draw echo trails
│   └── set_accuracy(debt_level) → Adjust prediction accuracy
│
├── EchoFrame (Data Class)
│   ├── position: Vector2
│   ├── timestamp: float
│   └── alpha: float
```

### AnchorSystem (src/systems/anchor_system.py)
```
AnchorSystem
├── Properties
│   ├── anchors: list[TimeAnchor]
│   ├── max_anchors: int (3)
│   ├── decay_time: float (30.0)
│   └── recall_debt_cost: float (2.0)
│
├── Methods
│   ├── place_anchor(position, world_state) → Create anchor
│   ├── recall_to_anchor(anchor_index) → Teleport to anchor
│   ├── update(dt) → Process decay
│   ├── remove_oldest() → Remove when exceeding max
│   ├── get_anchor_positions() → For rendering
│   └── clear_all() → Reset on level change
│
├── TimeAnchor (Data Class)
│   ├── position: Vector2
│   ├── creation_time: float
│   ├── remaining_time: float
│   └── world_snapshot: dict (optional)
```

## 2.3 Entity Classes

### BaseEntity (src/entities/base_entity.py)
```
BaseEntity (Abstract)
├── Properties
│   ├── id: str (unique identifier)
│   ├── position: Vector2
│   ├── velocity: Vector2
│   ├── size: tuple[int, int]
│   ├── rect: pygame.Rect
│   ├── affected_by_time: bool
│   ├── visible: bool
│   └── active: bool
│
├── Methods
│   ├── update(dt) → Abstract update
│   ├── render(screen) → Abstract render
│   ├── get_predicted_position(time) → For echo system
│   ├── on_collision(other) → Collision callback
│   └── get_rect() → Get collision rectangle
```

### Player (src/entities/player.py)
```
Player(BaseEntity)
├── Additional Properties
│   ├── speed: float
│   ├── is_dead: bool
│   ├── spawn_position: Vector2
│   ├── input_vector: Vector2
│   └── can_move: bool
│
├── Methods
│   ├── handle_input(keys, events) → Process input
│   ├── update(dt) → Movement and state
│   ├── render(screen) → Draw player
│   ├── die() → Handle death
│   ├── respawn() → Reset to spawn
│   └── on_collision(other) → Handle collisions
```

### Enemies (src/entities/enemies.py)
```
PatrolDrone(BaseEntity)
├── Properties
│   ├── patrol_points: list[Vector2]
│   ├── current_target_index: int
│   ├── patrol_speed: float
│   └── drone_type: str ('linear', 'circular', 'seeker')
│
├── Methods
│   ├── update(dt) → Patrol movement
│   ├── get_predicted_position(time) → Path prediction
│   └── render(screen) → Draw drone

TemporalHunter(BaseEntity)
├── Properties
│   ├── target: Player (reference)
│   ├── hunt_speed: float
│   ├── active_only_when_frozen: bool
│   └── detection_range: float
│
├── Methods
│   ├── update(dt, time_frozen) → Conditional movement
│   ├── chase_target() → Move toward player
│   └── render(screen) → Draw hunter

DebtShadow(BaseEntity)
├── Properties
│   ├── target: Player (reference)
│   ├── spawn_debt_threshold: float (10.0)
│   ├── dissolve_at_zero_debt: bool
│   └── shadow_speed: float
│
├── Methods
│   ├── update(dt, current_debt) → Conditional existence
│   ├── chase() → Follow player
│   └── dissolve() → Fade away
```

### Interactables (src/entities/interactables.py)
```
DebtSink(BaseEntity)
├── Properties
│   ├── absorption_amount: float (3.0)
│   ├── uses_remaining: int
│   └── recharge_time: float (optional)
│
├── Methods
│   ├── activate(debt_manager) → Absorb debt
│   ├── update(dt) → Recharge logic
│   └── render(screen) → Draw with state

DebtMirror(BaseEntity)
├── Properties
│   ├── facing_direction: Vector2
│   ├── reflection_active: bool
│   └── stored_debt: float
│
├── Methods
│   ├── absorb_debt(amount) → Store incoming debt
│   ├── emit_debt_projectile() → Create debt bullet
│   └── render(screen) → Draw mirror

DebtBomb(BaseEntity)
├── Properties
│   ├── trigger_type: str ('proximity', 'interaction')
│   ├── debt_payload: float
│   ├── explosion_radius: float
│   └── triggered: bool
│
├── Methods
│   ├── trigger() → Start explosion
│   ├── explode() → Apply time acceleration zone
│   └── render(screen) → Draw bomb

TimedDoor(BaseEntity)
├── Properties
│   ├── open: bool
│   ├── open_duration: float
│   ├── trigger_zones: list[Rect]
│   └── linked_switches: list
│
├── Methods
│   ├── open() → Open door
│   ├── close() → Close door
│   ├── update(dt) → Timer logic
│   └── render(screen) → Draw door state
```

## 2.4 Level Classes

### LevelManager (src/levels/level_manager.py)
```
LevelManager
├── Properties
│   ├── current_level: Level
│   ├── level_index: int
│   ├── levels: list[LevelData]
│   ├── entities: list[BaseEntity]
│   └── checkpoints: list[Checkpoint]
│
├── Methods
│   ├── load_level(index) → Load level data
│   ├── reload_current_level() → Restart level
│   ├── next_level() → Progress to next
│   ├── get_entities() → Return all entities
│   ├── get_tiles() → Return tile data
│   ├── update(dt) → Update level state
│   └── render(screen) → Draw level
```

### Level (src/levels/level_data.py)
```
Level
├── Properties
│   ├── name: str
│   ├── tiles: list[list[Tile]]
│   ├── spawn_point: Vector2
│   ├── exit_point: Vector2
│   ├── entities: list[EntityData]
│   ├── checkpoints: list[Vector2]
│   └── width, height: int
│
├── Methods
│   ├── get_tile_at(position) → Return tile
│   ├── is_solid(position) → Collision check
│   └── get_spawn_point() → Starting position
```

---

# 3. GAME LOOP ARCHITECTURE

## 3.1 Main Loop Flow

```
┌─────────────────────────────────────────────────────────────┐
│                      MAIN LOOP                               │
│                                                              │
│  ┌─────────┐    ┌──────────┐    ┌────────┐    ┌──────────┐ │
│  │ Events  │ → │  Update   │ → │ Render │ → │ Present  │ │
│  └─────────┘    └──────────┘    └────────┘    └──────────┘ │
│       ↑                                              │       │
│       └──────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘

Events:
├── Pygame events (input, window)
├── Custom game events
└── System events (debt changes, etc.)

Update:
├── Time Engine (calculate game dt)
├── Debt Manager (process debt)
├── Entities (player, enemies)
├── Systems (echoes, anchors)
├── Level (environment)
└── UI (HUD updates)

Render:
├── Level background
├── Entities
├── Effects (particles, echoes)
├── Screen effects (tint, shake)
└── UI overlay
```

## 3.2 Time-Aware Update System

```python
# Pseudocode for time-aware updates
def update(real_dt):
    # 1. TimeEngine calculates game_dt based on time_scale
    game_dt = time_engine.get_game_dt(real_dt)
    
    # 2. If time is frozen, game_dt = 0 for most entities
    if time_engine.is_frozen():
        # Player updates with real_dt (can move in frozen time)
        player.update(real_dt)
        
        # Echoes calculate predictions
        echo_system.update(entities)
        
        # Temporal Hunters update (they move in frozen time)
        for hunter in temporal_hunters:
            hunter.update(real_dt)
        
        # Debt accrues
        debt_manager.accrue_debt(real_dt * DEBT_ACCRUAL_RATE)
    else:
        # Normal update with potentially accelerated game_dt
        for entity in entities:
            entity.update(game_dt)
        
        # Debt repays during normal time
        if debt_manager.current_debt > 0:
            debt_manager.repay_debt(real_dt)
    
    # 3. Always update
    anchor_system.update(real_dt)
    ui.update(real_dt)
```

---

# 4. EVENT SYSTEM

## 4.1 Custom Events

```python
# Event types (src/core/events.py)
class GameEvent:
    # Time events
    TIME_FROZEN = 'time_frozen'
    TIME_UNFROZEN = 'time_unfrozen'
    TIME_SCALE_CHANGED = 'time_scale_changed'
    
    # Debt events
    DEBT_CHANGED = 'debt_changed'
    DEBT_TIER_CHANGED = 'debt_tier_changed'
    BANKRUPTCY_STARTED = 'bankruptcy_started'
    BANKRUPTCY_ENDED = 'bankruptcy_ended'
    
    # Anchor events
    ANCHOR_PLACED = 'anchor_placed'
    ANCHOR_RECALLED = 'anchor_recalled'
    ANCHOR_EXPIRED = 'anchor_expired'
    
    # Game events
    PLAYER_DIED = 'player_died'
    LEVEL_COMPLETED = 'level_completed'
    CHECKPOINT_REACHED = 'checkpoint_reached'
```

## 4.2 Observer Pattern

```
EventManager
├── listeners: dict[event_type, list[callback]]
├── subscribe(event_type, callback)
├── unsubscribe(event_type, callback)
└── emit(event_type, data)
```

---

# 5. RENDERING PIPELINE

## 5.1 Layer Order

```
Layer 0: Background tiles
Layer 1: Floor decorations
Layer 2: Interactables (sinks, mirrors, bombs)
Layer 3: Enemies
Layer 4: Player
Layer 5: Temporal echoes (when frozen)
Layer 6: Particles
Layer 7: Screen effects (tint, shake)
Layer 8: UI/HUD
Layer 9: Menus (when active)
```

## 5.2 Screen Effects Pipeline

```
Base Frame
    │
    ▼
┌─────────────────┐
│ Color Grading   │ ← Based on debt tier
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Screen Shake    │ ← During high debt
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Vignette        │ ← During bankruptcy
└─────────────────┘
    │
    ▼
┌─────────────────┐
│ Flash Effects   │ ← On events (death, level complete)
└─────────────────┘
    │
    ▼
Final Frame
```

---

# 6. COLLISION SYSTEM

## 6.1 Collision Types

```
Collision Matrix:
                   │ Wall │ Player │ Enemy │ Projectile │ Trigger │
───────────────────┼──────┼────────┼───────┼────────────┼─────────│
Player             │ Stop │   -    │ Death │   Effect   │ Activate│
Enemy              │ Stop │ Death  │   -   │   Effect   │    -    │
Projectile         │ Stop │ Effect │ Effect│     -      │    -    │
```

## 6.2 Collision Detection Approach

- Use pygame Rect for AABB collision
- Spatial partitioning for optimization (grid-based)
- Collision callbacks for specific interactions

---

# 7. STATE MANAGEMENT

## 7.1 Game States

```
GameState (Enum)
├── MAIN_MENU
├── PLAYING
├── PAUSED
├── LEVEL_TRANSITION
├── GAME_OVER
└── VICTORY
```

## 7.2 State Machine

```
┌────────────┐
│ MAIN_MENU  │ ──────────────────────┐
└────────────┘                        │
      │                               │
      │ Start Game                    │
      ▼                               │
┌────────────┐                        │
│  PLAYING   │ ←─────────────────┐    │
└────────────┘                   │    │
      │         │                │    │
      │ ESC     │ Die            │    │
      ▼         ▼                │    │
┌────────┐  ┌──────────┐         │    │
│ PAUSED │  │GAME_OVER │         │    │
└────────┘  └──────────┘         │    │
      │           │              │    │
      │ Resume    │ Retry        │    │
      ▼           └──────────────┘    │
┌────────────┐                        │
│  PLAYING   │                        │
└────────────┘                        │
      │                               │
      │ Complete Level 3              │
      ▼                               │
┌────────────┐                        │
│  VICTORY   │ ───────────────────────┘
└────────────┘    Return to Menu
```

---

# 8. DATA FLOW

## 8.1 Frame Update Flow

```
Input → Player → Time Engine → Debt Manager → Entities → Collision → Events → UI
  │                                                           │
  └───────────────────────────────────────────────────────────┘
                    Feedback (Visual, Audio)
```

## 8.2 Time Freeze Data Flow

```
SPACE Pressed
    │
    ▼
TimeEngine.freeze()
    │
    ├─→ Emit TIME_FROZEN event
    │
    ├─→ EchoSystem.activate()
    │
    └─→ UI updates (freeze indicator)

While Frozen:
    │
    ├─→ Player moves (real_dt)
    ├─→ Echoes render
    ├─→ DebtManager accrues debt
    └─→ Temporal Hunters activate

SPACE Released
    │
    ▼
TimeEngine.unfreeze()
    │
    ├─→ Emit TIME_UNFROZEN event
    ├─→ EchoSystem.deactivate()
    ├─→ Calculate total debt accrued
    └─→ Begin repayment phase
```

---

# 9. OPTIMIZATION STRATEGIES

## 9.1 Performance Targets

- Maintain 60 FPS on mid-range hardware
- Echo calculations < 2ms per frame
- Collision detection < 1ms per frame
- Rendering < 10ms per frame

## 9.2 Optimization Techniques

1. **Object Pooling**: Reuse particles, projectiles
2. **Spatial Partitioning**: Grid for collision detection
3. **Dirty Rectangles**: Only redraw changed areas (optional)
4. **Echo Caching**: Cache predictions, update on demand
5. **Level of Detail**: Reduce effects at high entity counts

---

# 10. EXTENSIBILITY

## 10.1 Adding New Enemies

```python
class NewEnemy(BaseEntity):
    def __init__(self, position, **kwargs):
        super().__init__(position)
        # Custom initialization
    
    def update(self, dt):
        # Custom behavior
    
    def get_predicted_position(self, time):
        # For echo system
    
    def render(self, screen):
        # Custom rendering
```

## 10.2 Adding New Levels

```python
LEVEL_4 = LevelData(
    name="New Level",
    tiles=[...],  # 2D array
    spawn_point=(x, y),
    exit_point=(x, y),
    entities=[
        EntityData(type='patrol_drone', position=(x, y), **config),
        # ... more entities
    ]
)
```

---

*Technical Architecture v1.0*
*TEMPORAL DEBT - Systems Design*
