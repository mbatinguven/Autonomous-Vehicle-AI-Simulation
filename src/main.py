"""
main.py - Entry point for AAA Mini City Autonomous Vehicle Simulation.

A cinematic-quality city simulation featuring:
- Tile-based rendering with parallax backgrounds
- Smooth vehicle movement with animations
- Dynamic lighting and shadows
- Particle effects (dust, sparks, smoke)
- Post-processing (bloom, vignette)
- Multiple pathfinding algorithms (BFS, Greedy, A*)
- Full menu system with settings

Usage:
    python main.py [--fullscreen]

Controls:
    Mouse:
        Left-click   - Place/remove based on edit mode
        Right-click  - Set start position
        Middle-click - Set goal position
        Scroll       - Zoom in/out
    
    Keyboard:
        1, 2, 3 - Switch algorithm (BFS, Greedy, A*)
        O       - Edit mode: Obstacles
        T       - Edit mode: Traffic lights
        R       - Reset map
        N       - Generate new random map
        M       - Toggle minimap
        B       - Toggle bloom effect
        F11     - Toggle fullscreen
        SPACE   - Recalculate path
        ESC     - Pause menu
"""

import sys
import os
import pygame

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def print_banner():
    """Print startup banner."""
    banner = r"""
    ╔══════════════════════════════════════════════════════════════════╗
    ║                                                                  ║
    ║   ███╗   ███╗██╗███╗   ██╗██╗     ██████╗██╗████████╗██╗   ██╗  ║
    ║   ████╗ ████║██║████╗  ██║██║    ██╔════╝██║╚══██╔══╝╚██╗ ██╔╝  ║
    ║   ██╔████╔██║██║██╔██╗ ██║██║    ██║     ██║   ██║    ╚████╔╝   ║
    ║   ██║╚██╔╝██║██║██║╚██╗██║██║    ██║     ██║   ██║     ╚██╔╝    ║
    ║   ██║ ╚═╝ ██║██║██║ ╚████║██║    ╚██████╗██║   ██║      ██║     ║
    ║   ╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝     ╚═════╝╚═╝   ╚═╝      ╚═╝     ║
    ║                                                                  ║
    ║         AAA Autonomous Vehicle Simulation                        ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def check_and_generate_assets():
    """Check if assets exist, generate if missing."""
    from constants import ASSETS_DIR, ASSET_TILESET
    
    if not os.path.exists(ASSET_TILESET):
        print("\n[!] Assets not found. Generating...")
        print("-" * 50)
        try:
            from asset_generator import generate_all
            generate_all()
        except Exception as e:
            print(f"[!] Could not generate assets: {e}")
            print("    Simulation will use fallback graphics.")
        print("-" * 50)
    else:
        print("[✓] Assets found.")


def initialize_pygame(fullscreen=False):
    """Initialize pygame and create display."""
    pygame.init()
    pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
    
    from constants import DEFAULT_WIDTH, DEFAULT_HEIGHT
    
    if fullscreen:
        info = pygame.display.Info()
        width, height = info.current_w, info.current_h
        flags = pygame.FULLSCREEN | pygame.HWSURFACE | pygame.DOUBLEBUF
    else:
        width, height = DEFAULT_WIDTH, DEFAULT_HEIGHT
        flags = pygame.HWSURFACE | pygame.DOUBLEBUF | pygame.RESIZABLE
    
    screen = pygame.display.set_mode((width, height), flags)
    pygame.display.set_caption("Mini City - Autonomous Vehicle Simulation")
    
    return screen, fullscreen


def run_game(start_fullscreen=False):
    """Main game loop with state management."""
    from constants import DEFAULT_SETTINGS
    from menus import MainMenu, PauseMenu, SettingsMenu
    from simulation import Simulation
    
    screen, is_fullscreen = initialize_pygame(start_fullscreen)
    settings = DEFAULT_SETTINGS.copy()
    
    state = "menu"
    sim = None
    
    while state != "exit":
        if state == "menu":
            # Main menu
            menu = MainMenu(screen)
            result = menu.run()
            
            if result == "start":
                state = "game"
            elif result == "settings":
                state = "settings_menu"
            else:
                state = "exit"
        
        elif state == "settings_menu":
            # Settings from main menu
            settings_menu = SettingsMenu(screen, settings)
            result = settings_menu.run()
            
            if result == "back":
                settings = settings_menu.get_settings()
                state = "menu"
            else:
                state = "exit"
        
        elif state == "game":
            # Create or resume simulation
            if sim is None:
                sim = Simulation(screen, settings)
            
            result = sim.run()
            
            if result == "pause":
                # Show pause menu
                pause = PauseMenu(screen)
                background = sim.get_screenshot()
                pause_result = pause.run(background)
                
                if pause_result == "resume":
                    continue
                elif pause_result == "settings":
                    settings_menu = SettingsMenu(screen, settings)
                    settings_menu.run()
                    settings = settings_menu.get_settings()
                elif pause_result == "menu":
                    sim = None
                    state = "menu"
                else:
                    state = "exit"
            
            elif result == "toggle_fullscreen":
                # Toggle fullscreen
                is_fullscreen = not is_fullscreen
                screen, _ = initialize_pygame(is_fullscreen)
                if sim:
                    sim.screen = screen
                    sim.resize(screen.get_width(), screen.get_height())
            
            elif result == "quit":
                state = "exit"
    
    # Cleanup
    pygame.mixer.quit()
    pygame.quit()


def main():
    """Main entry point."""
    # Parse arguments
    fullscreen = "--fullscreen" in sys.argv or "-f" in sys.argv
    
    # Print banner
    print_banner()
    
    # Print info
    print("\n[i] Initializing Mini City Simulation...")
    print(f"[i] Python: {sys.version.split()[0]}")
    print(f"[i] Pygame: {pygame.version.ver}")
    print(f"[i] Mode: {'Fullscreen' if fullscreen else 'Windowed'}")
    
    # Check assets
    check_and_generate_assets()
    
    print("\n[i] Starting simulation...")
    print("=" * 60)
    
    try:
        run_game(start_fullscreen=fullscreen)
    except KeyboardInterrupt:
        print("\n\n[!] Interrupted by user.")
    except Exception as e:
        print(f"\n[!] Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("[✓] Mini City Simulation ended.")
    print("    Thank you for playing!")
    print("=" * 60)


if __name__ == "__main__":
    main()
