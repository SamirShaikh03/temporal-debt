#!/usr/bin/env python3
"""
TEMPORAL DEBT - Web Version
Entry point for browser deployment via Pygbag

This version uses asyncio to work with Pygbag's WebAssembly requirements.
"""
import asyncio
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.game import Game


async def main():
    """
    Async entry point for web deployment.
    
    Required for Pygbag to work properly. The game loop needs to yield
    control back to the browser periodically using asyncio.sleep(0).
    """
    print("=" * 50)
    print("        TEMPORAL DEBT")
    print("    Time is a loan you cannot afford.")
    print("=" * 50)
    print("\nLoading web version...")
    print("Controls: WASD/Arrows=Move, SPACE=Freeze Time")
    print()
    
    try:
        game = Game()
        
        # Main game loop with async yield
        while game.running:
            game.run()
            await asyncio.sleep(0)  # Yield control to browser
        
        game.cleanup()
        print("\nThank you for playing TEMPORAL DEBT!")
        
    except Exception as e:
        print(f"Error running game: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
