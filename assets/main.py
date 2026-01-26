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

import asyncio
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Detect WASM/Pygbag environment
try:
    import platform as _platform
    IS_WASM = _platform.system() == "Emscripten" or sys.platform == "emscripten"
except:
    IS_WASM = False

from src.core.game import Game


async def main_async():
    """
    Async entry point - works for both desktop and web.
    
    Required for Pygbag/WASM to work properly.
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
    
    if IS_WASM:
        print("Running in browser (WASM mode)...")
    else:
        print("Running in desktop mode...")
    print()
    
    try:
        game = Game()
        print("Game initialized successfully!")
        
        # Main game loop with async yield for browser compatibility
        while game.running:
            game.run()
            # CRITICAL: yield control to browser event loop
            await asyncio.sleep(0)
        
        game.cleanup()
        print("\nThanks for playing TEMPORAL DEBT!")
        
    except KeyboardInterrupt:
        print("\nGame interrupted.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        # Keep error visible in browser
        if IS_WASM:
            while True:
                await asyncio.sleep(1)


def main():
    """Synchronous wrapper for desktop compatibility."""
    asyncio.run(main_async())
    return 0


# Entry point - works for both pygbag and direct execution
if __name__ == "__main__":
    asyncio.run(main_async())
