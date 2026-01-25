# TEMPORAL DEBT

![Temporal Debt Banner](https://github.com/user-attachments/assets/f3c6e3f3-9b1e-4b6f-8e0a-9e3f3b4f5a1f)

> *Time is a loan you cannot afford.*

A puzzle-adventure game where the player can borrow time from the future to solve the present — but every second borrowed must be repaid later with interest.

## 📸 Gameplay Screenshot

![Temporal Debt Gameplay](https://github.com/user-attachments/assets/b8c7d4e9-2f3a-4e5b-9c1d-8e6f7a2b3c4d)

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Pygame](https://img.shields.io/badge/Pygame-2.5+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🎮 Concept

**TEMPORAL DEBT** subverts the typical time-manipulation power fantasy. Instead of giving players godlike control over time, it treats time freezing as a Faustian bargain — powerful but costly.

### Core Mechanics

- **Time Freeze (SPACE)**: Hold to freeze time. You can move and plan while the world is stopped.
- **Temporal Debt**: Every second frozen accrues 1.5 seconds of debt.
- **Debt Repayment**: When time resumes, the world accelerates until your debt is repaid.
- **Debt Tiers**: Higher debt means faster world speed, creating escalating difficulty.
- **Temporal Bankruptcy**: Exceed 20 seconds of debt and face extreme consequences.

### Unique Systems

| System | Description |
|--------|-------------|
| **Temporal Echoes** | When frozen, see where enemies will be in the future |
| **Time Anchors** | Place up to 3 save points, recall at the cost of debt |
| **Debt Sinks** | Crystals that absorb debt (limited uses) |
| **Temporal Hunters** | Enemies that only move when time is frozen |
| **Debt Shadows** | Manifestations of high debt that chase you |

## 🚀 Getting Started

### Requirements

- Python 3.8+
- Pygame 2.5+

### Installation

```bash
# Clone or download the repository
cd temporal_debt

# Install dependencies
pip install -r requirements.txt

# Run the game
python main.py
```

## 🎯 Controls

| Key | Action |
|-----|--------|
| WASD / Arrows | Move |
| SPACE (hold) | Freeze Time |
| Q | Place Time Anchor |
| E | Recall to Nearest Anchor |
| ESC | Pause Game |

## 📁 Project Structure

```
temporal_debt/
├── main.py                 # Entry point
├── requirements.txt        # Dependencies
├── README.md              # This file
│
├── docs/
│   ├── GAME_DESIGN_DOCUMENT.md
│   └── TECHNICAL_ARCHITECTURE.md
│
└── src/
    ├── core/              # Core game systems
    │   ├── game.py        # Main game class
    │   ├── settings.py    # Configuration
    │   ├── events.py      # Event system
    │   └── utils.py       # Utilities
    │
    ├── systems/           # Game mechanics
    │   ├── time_engine.py     # Time manipulation
    │   ├── debt_manager.py    # Debt tracking
    │   ├── echo_system.py     # Temporal echoes
    │   ├── anchor_system.py   # Time anchors
    │   └── collision.py       # Collision detection
    │
    ├── entities/          # Game objects
    │   ├── player.py
    │   ├── enemies.py
    │   └── interactables.py
    │
    ├── levels/            # Level system
    │   ├── level_manager.py
    │   ├── level_data.py
    │   └── tile.py
    │
    └── ui/                # User interface
        ├── hud.py
        ├── menus.py
        └── feedback.py
```

## 🎲 Levels

### Level 1: The Vault
*Learn to borrow time... and pay it back.*
- Introduction to time freezing
- Simple patrol patterns
- First debt sink

### Level 2: The Gauntlet
*Multiple threats. Plan your path carefully.*
- Multiple patrol drones
- Introduction to Temporal Hunters
- Checkpoint system

### Level 3: The Debt Chamber
*Face the consequences of borrowed time.*
- Complex enemy patterns
- Debt bombs
- Master-level challenge

## 🧠 Design Philosophy

### Time as Consequence
Unlike other time-manipulation games, freezing time in TEMPORAL DEBT isn't free. This creates:
- **Strategic depth**: When to freeze? For how long?
- **Tension**: Debt creates anxiety and urgency
- **Mastery expression**: Expert players minimize debt

### The Debt Spiral
High debt → faster world → harder gameplay → need to freeze → more debt

This feedback loop is intentional. It rewards restraint and punishes spam.

### Economic Metaphor
The debt system mirrors real-world lending:
- **Interest compounds** at higher tiers
- **Bankruptcy** has severe consequences
- **Debt sinks** are limited resources

## 🔧 Technical Highlights

- **Clean Architecture**: Modular, well-documented codebase
- **Event System**: Decoupled communication between systems
- **Time Engine**: Sophisticated time scaling and freeze mechanics
- **Spatial Partitioning**: Efficient collision detection
- **State Machine**: Clean game state management

## 🚀 Future Development Ideas

- **Story Mode**: Narrative explaining the Temporal Borrower's origin
- **Endless Mode**: Procedurally generated rooms with escalating difficulty
- **Multiplayer**: Shared debt between players
- **More Enemies**: Debt Lords as boss encounters
- **Audio**: Dynamic music that responds to debt level

## � Deployment

Anyone with a link can play your game in their browser!

## ���📜 License

MIT License - Feel free to use, modify, and distribute.

---

*TEMPORAL DEBT - A game about the cost of power.*
