#!/usr/bin/env python3
"""
TEMPORAL DEBT
=============

A puzzle-adventure game where time is a resource, currency, and enemy.

Freeze time to solve puzzles - but every second borrowed must be repaid
with interest. Overuse creates chaos.

Controls:
---------
WASD/Arrows - Move
SPACE (hold) - Freeze Time
Q - Place Time Anchor
E - Recall to Nearest Anchor
ESC - Pause

Running:
--------
    python main.py

Requirements:
-------------
    pygame >= 2.5.0

Author: Temporal Debt Studio
Version: 1.0.0
"""

import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.game import Game


def main():
    """
    Entry point for TEMPORAL DEBT.
    
    Creates and runs the main game instance.
    """
    print("=" * 50)
    print("        TEMPORAL DEBT")
    print("    Time is a loan you cannot afford.")
    print("=" * 50)
    print()
    print("Controls:")
    print("  WASD/Arrows  - Move")
    print("  SPACE (hold) - Freeze Time")
    print("  Q            - Place Anchor")
    print("  E            - Recall to Anchor")
    print("  ESC          - Pause")
    print()
    print("Starting game...")
    print()
    
    try:
        game = Game()
        # Desktop version: wrap single-frame run() in a loop
        while game.running:
            game.run()
        game.cleanup()
    except KeyboardInterrupt:
        print("\nGame interrupted.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    print("\nThanks for playing TEMPORAL DEBT!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
