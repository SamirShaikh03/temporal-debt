#!/usr/bin/env python3
# /// script
# dependencies = ["pygame-ce"]
# ///
"""
TEMPORAL DEBT 2.0
=================
A puzzle-adventure game where time is a resource, currency, and enemy.

Controls: WASD/Arrows=Move, SPACE=Freeze Time, Q=Place Anchor, E=Recall, ESC=Pause
"""

import asyncio
import sys
import os

print("=" * 50)
print("   TEMPORAL DEBT 2.0 - Starting...")
print("=" * 50)

# Add src to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Detect WASM/Pygbag environment
IS_WASM = sys.platform == "emscripten"

print(f"Platform: {sys.platform}")
print(f"WASM mode: {IS_WASM}")
print(f"Python: {sys.version}")


async def main_async():
    """Async entry point for both desktop and web."""
    print("main_async() started")

    # Import pygame first - must work in all environments
    import pygame
    pygame.init()
    print("pygame initialized")

    # Setup display
    screen = pygame.display.set_mode((1280, 720))
    pygame.display.set_caption("TEMPORAL DEBT 2.0")
    clock = pygame.time.Clock()
    print("Display ready: 1280x720")

    # If WASM, show click-to-start screen BEFORE importing game
    if IS_WASM:
        print("Showing click-to-start screen...")
        font = pygame.font.Font(None, 72)
        small_font = pygame.font.Font(None, 36)
        tiny_font = pygame.font.Font(None, 28)

        waiting = True
        frame = 0
        while waiting:
            screen.fill((15, 15, 35))

            # Title
            title_surf = font.render("TEMPORAL DEBT 2.0", True, (80, 180, 255))
            screen.blit(title_surf, title_surf.get_rect(center=(640, 200)))

            # Subtitle
            sub = small_font.render("Time is a loan you cannot afford.", True, (180, 180, 220))
            screen.blit(sub, sub.get_rect(center=(640, 270)))

            # Pulsing click prompt
            pulse = abs((frame % 90) - 45) / 45.0
            r = int(200 + 55 * pulse)
            g = int(150 + 105 * pulse)
            click_text = font.render("CLICK TO START", True, (r, g, 0))
            screen.blit(click_text, click_text.get_rect(center=(640, 400)))

            # Controls
            ctrl = tiny_font.render("WASD = Move | SPACE = Freeze Time | Q/E = Anchors | ESC = Pause", True, (120, 120, 160))
            screen.blit(ctrl, ctrl.get_rect(center=(640, 520)))

            # Status line
            status = tiny_font.render("Game loaded. Click anywhere to begin!", True, (80, 220, 80))
            screen.blit(status, status.get_rect(center=(640, 600)))

            pygame.display.flip()
            clock.tick(30)

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit()
                    return
                if ev.type == pygame.MOUSEBUTTONDOWN or ev.type == pygame.KEYDOWN:
                    waiting = False
                    break

            await asyncio.sleep(0)

        print("Click detected! Loading game...")

    # NOW import the game (deferred to avoid import crashes before display is ready)
    Game = None
    try:
        print("Importing game modules...")
        from src.core.game import Game
        print("Game modules imported successfully!")
    except Exception as e:
        print(f"IMPORT ERROR: {e}")
        import traceback
        traceback.print_exc()

        # Show error on screen
        err_font = pygame.font.Font(None, 36)
        screen.fill((60, 0, 0))
        lines = [
            "Failed to load game modules!",
            f"Error: {str(e)[:80]}",
            "",
            "Check browser console (F12) for details.",
        ]
        for i, line in enumerate(lines):
            color = (255, 100, 100) if i == 0 else (255, 200, 200)
            surf = err_font.render(line, True, color)
            screen.blit(surf, surf.get_rect(center=(640, 250 + i * 50)))
        pygame.display.flip()

        # Keep error visible
        while True:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit()
                    return
            await asyncio.sleep(0.1)

    if Game is None:
        return

    # Run the game
    try:
        game = Game()
        print("Game initialized! Starting main loop...")

        while game.running:
            game.run()
            await asyncio.sleep(0)

        game.cleanup()
        print("Thanks for playing TEMPORAL DEBT!")

    except Exception as e:
        print(f"RUNTIME ERROR: {e}")
        import traceback
        traceback.print_exc()

        # Show runtime error on screen
        err_font = pygame.font.Font(None, 36)
        screen.fill((60, 0, 0))
        lines = [
            "Runtime Error!",
            f"{str(e)[:80]}",
            "",
            "Press F12 for details. Refresh to retry.",
        ]
        for i, line in enumerate(lines):
            color = (255, 100, 100) if i == 0 else (255, 200, 200)
            surf = err_font.render(line, True, color)
            screen.blit(surf, surf.get_rect(center=(640, 250 + i * 50)))
        pygame.display.flip()

        if IS_WASM:
            while True:
                for ev in pygame.event.get():
                    if ev.type == pygame.QUIT:
                        return
                await asyncio.sleep(0.1)


def main():
    """Synchronous wrapper for desktop."""
    asyncio.run(main_async())
    return 0


# Entry point
asyncio.run(main_async())
