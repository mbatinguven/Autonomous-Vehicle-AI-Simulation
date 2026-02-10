"""
asset_generator.py - Generate high-quality placeholder assets.

Creates:
- City tileset (8x8 = 64 tiles)
- Vehicle sprite with detail
- Traffic light animation sheet
- Skyline background
- UI elements
- Sound effects
"""

import os
import pygame
import math
import struct
import random

# Initialize pygame
pygame.init()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")
TILE_SIZE = 64


def ensure_dirs():
    """Create asset directories."""
    os.makedirs(ASSETS_DIR, exist_ok=True)
    os.makedirs(SOUNDS_DIR, exist_ok=True)


def create_tileset():
    """
    Create detailed city tileset (8x8 tiles = 512x512).
    """
    cols, rows = 8, 8
    tileset = pygame.Surface((cols * TILE_SIZE, rows * TILE_SIZE), pygame.SRCALPHA)
    
    # Colors - VIBRANT high-contrast palette
    ROAD = (65, 68, 75)           # Brighter asphalt
    ROAD_LIGHT = (72, 75, 82)     # Slightly lighter variant
    ROAD_LINE = (210, 200, 100)   # Bright yellow markings
    SIDEWALK = (140, 135, 125)    # Brighter sidewalk
    GRASS = (65, 115, 60)         # Rich green
    GRASS_DARK = (55, 100, 50)    # Darker but still vibrant
    
    def draw_road_base(surf, x, y):
        """Draw road base with sidewalk."""
        rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
        pygame.draw.rect(surf, SIDEWALK, rect)
        inner = pygame.Rect(x + 6, y + 6, TILE_SIZE - 12, TILE_SIZE - 12)
        pygame.draw.rect(surf, ROAD, inner)
    
    def draw_road_h(surf, x, y):
        """Horizontal road with markings."""
        pygame.draw.rect(surf, SIDEWALK, (x, y, TILE_SIZE, TILE_SIZE))
        pygame.draw.rect(surf, ROAD, (x, y + 6, TILE_SIZE, TILE_SIZE - 12))
        # Center line dashes
        for i in range(0, TILE_SIZE, 16):
            pygame.draw.rect(surf, ROAD_LINE, (x + i + 2, y + TILE_SIZE // 2 - 1, 10, 2))
    
    def draw_road_v(surf, x, y):
        """Vertical road with markings."""
        pygame.draw.rect(surf, SIDEWALK, (x, y, TILE_SIZE, TILE_SIZE))
        pygame.draw.rect(surf, ROAD, (x + 6, y, TILE_SIZE - 12, TILE_SIZE))
        for i in range(0, TILE_SIZE, 16):
            pygame.draw.rect(surf, ROAD_LINE, (x + TILE_SIZE // 2 - 1, y + i + 2, 2, 10))
    
    def draw_intersection(surf, x, y):
        """4-way intersection."""
        pygame.draw.rect(surf, SIDEWALK, (x, y, TILE_SIZE, TILE_SIZE))
        # Center area
        pygame.draw.rect(surf, ROAD, (x + 6, y + 6, TILE_SIZE - 12, TILE_SIZE - 12))
        # Extensions
        pygame.draw.rect(surf, ROAD, (x + 6, y, TILE_SIZE - 12, 6))
        pygame.draw.rect(surf, ROAD, (x + 6, y + TILE_SIZE - 6, TILE_SIZE - 12, 6))
        pygame.draw.rect(surf, ROAD, (x, y + 6, 6, TILE_SIZE - 12))
        pygame.draw.rect(surf, ROAD, (x + TILE_SIZE - 6, y + 6, 6, TILE_SIZE - 12))
    
    def draw_corner(surf, x, y, corner):
        """Corner road piece."""
        pygame.draw.rect(surf, SIDEWALK, (x, y, TILE_SIZE, TILE_SIZE))
        pygame.draw.rect(surf, ROAD, (x + 6, y + 6, TILE_SIZE - 12, TILE_SIZE - 12))
        # Extend based on corner type
        if corner in ("tl", "tr"):
            pygame.draw.rect(surf, ROAD, (x + 6, y + TILE_SIZE - 6, TILE_SIZE - 12, 6))
        if corner in ("bl", "br"):
            pygame.draw.rect(surf, ROAD, (x + 6, y, TILE_SIZE - 12, 6))
        if corner in ("tl", "bl"):
            pygame.draw.rect(surf, ROAD, (x + TILE_SIZE - 6, y + 6, 6, TILE_SIZE - 12))
        if corner in ("tr", "br"):
            pygame.draw.rect(surf, ROAD, (x, y + 6, 6, TILE_SIZE - 12))
    
    def draw_building(surf, x, y, color, floors=3, style=0):
        """Draw a building with windows."""
        # Ground
        pygame.draw.rect(surf, GRASS_DARK, (x, y, TILE_SIZE, TILE_SIZE))
        
        margin = 5
        w = TILE_SIZE - margin * 2
        h = TILE_SIZE - margin * 2
        
        # Building body
        pygame.draw.rect(surf, color, (x + margin, y + margin, w, h), border_radius=2)
        
        # Roof shadow
        darker = tuple(max(0, c - 25) for c in color)
        pygame.draw.rect(surf, darker, (x + margin, y + margin, w, 8), 
                        border_top_left_radius=2, border_top_right_radius=2)
        
        # Windows - brighter, more vivid
        window_color = (200, 220, 255) if random.random() > 0.3 else (80, 95, 120)
        for row in range(floors):
            for col in range(2):
                wx = x + margin + 10 + col * 24
                wy = y + margin + 15 + row * 15
                pygame.draw.rect(surf, window_color, (wx, wy, 10, 10))
    
    def draw_grass(surf, x, y, variant=0):
        """Grass tile with texture."""
        pygame.draw.rect(surf, GRASS if variant == 0 else GRASS_DARK, 
                        (x, y, TILE_SIZE, TILE_SIZE))
        # Texture dots
        random.seed(x * 100 + y + variant)
        for _ in range(8):
            px = x + random.randint(5, TILE_SIZE - 5)
            py = y + random.randint(5, TILE_SIZE - 5)
            c = GRASS_DARK if variant == 0 else GRASS
            pygame.draw.circle(surf, c, (px, py), random.randint(2, 4))
    
    # Row 0: Road pieces
    draw_road_h(tileset, 0 * TILE_SIZE, 0)
    draw_road_v(tileset, 1 * TILE_SIZE, 0)
    draw_intersection(tileset, 2 * TILE_SIZE, 0)
    draw_intersection(tileset, 3 * TILE_SIZE, 0)  # T-up
    draw_intersection(tileset, 4 * TILE_SIZE, 0)  # T-down
    draw_intersection(tileset, 5 * TILE_SIZE, 0)  # T-left
    draw_intersection(tileset, 6 * TILE_SIZE, 0)  # T-right
    draw_corner(tileset, 7 * TILE_SIZE, 0, "tl")
    
    # Row 1: More roads and corners
    draw_corner(tileset, 0 * TILE_SIZE, TILE_SIZE, "tr")
    draw_corner(tileset, 1 * TILE_SIZE, TILE_SIZE, "bl")
    draw_corner(tileset, 2 * TILE_SIZE, TILE_SIZE, "br")
    draw_road_h(tileset, 3 * TILE_SIZE, TILE_SIZE)
    draw_road_v(tileset, 4 * TILE_SIZE, TILE_SIZE)
    draw_road_h(tileset, 5 * TILE_SIZE, TILE_SIZE)
    # Sidewalk only
    pygame.draw.rect(tileset, SIDEWALK, (6 * TILE_SIZE, TILE_SIZE, TILE_SIZE, TILE_SIZE))
    pygame.draw.rect(tileset, SIDEWALK, (7 * TILE_SIZE, TILE_SIZE, TILE_SIZE, TILE_SIZE))
    
    # Row 2-3: Buildings - VIBRANT, saturated colors
    building_colors = [
        (110, 100, 90), (95, 110, 130), (125, 105, 90), (90, 100, 120),
        (120, 100, 85), (100, 120, 110), (130, 115, 95), (100, 90, 115),
        (140, 125, 110), (115, 130, 145), (105, 95, 120), (130, 120, 105),
        (110, 125, 115), (125, 115, 135), (115, 105, 125), (135, 125, 110),
    ]
    
    for i in range(16):
        col = i % 8
        row = 2 + i // 8
        draw_building(tileset, col * TILE_SIZE, row * TILE_SIZE, 
                     building_colors[i], floors=2 + (i % 3), style=i)
    
    # Row 4-5: Nature and decoration
    draw_grass(tileset, 0 * TILE_SIZE, 4 * TILE_SIZE, 0)
    draw_grass(tileset, 1 * TILE_SIZE, 4 * TILE_SIZE, 1)
    
    # Tree
    x, y = 2 * TILE_SIZE, 4 * TILE_SIZE
    draw_grass(tileset, x, y, 0)
    pygame.draw.rect(tileset, (70, 50, 35), (x + 28, y + 35, 8, 20))
    pygame.draw.circle(tileset, (40, 80, 40), (x + 32, y + 28), 18)
    pygame.draw.circle(tileset, (35, 70, 35), (x + 32, y + 24), 12)
    
    # Park with trees
    x, y = 3 * TILE_SIZE, 4 * TILE_SIZE
    draw_grass(tileset, x, y, 0)
    pygame.draw.circle(tileset, (45, 85, 45), (x + 20, y + 20), 12)
    pygame.draw.circle(tileset, (45, 85, 45), (x + 44, y + 44), 12)
    
    # Water
    x, y = 4 * TILE_SIZE, 4 * TILE_SIZE
    pygame.draw.rect(tileset, (35, 70, 120), (x, y, TILE_SIZE, TILE_SIZE))
    # Wave lines
    for i in range(3):
        pygame.draw.arc(tileset, (50, 85, 140), 
                       (x + 10, y + 15 + i * 18, 44, 12), 0, math.pi, 2)
    
    # More grass variants
    for i in range(5, 8):
        draw_grass(tileset, i * TILE_SIZE, 4 * TILE_SIZE, i % 2)
    
    # Row 5
    for i in range(8):
        draw_grass(tileset, i * TILE_SIZE, 5 * TILE_SIZE, i % 2)
    
    # Row 6-7: Special tiles
    # Empty/blocked
    pygame.draw.rect(tileset, (25, 28, 32), (0, 6 * TILE_SIZE, TILE_SIZE, TILE_SIZE))
    pygame.draw.line(tileset, (40, 45, 50), (10, 6 * TILE_SIZE + 10), 
                    (TILE_SIZE - 10, 6 * TILE_SIZE + TILE_SIZE - 10), 2)
    pygame.draw.line(tileset, (40, 45, 50), (TILE_SIZE - 10, 6 * TILE_SIZE + 10),
                    (10, 6 * TILE_SIZE + TILE_SIZE - 10), 2)
    
    # Fill remaining with grass
    for row in range(6, 8):
        for col in range(1, 8):
            draw_grass(tileset, col * TILE_SIZE, row * TILE_SIZE, (row + col) % 2)
    
    return tileset


def create_vehicle():
    """Create detailed vehicle sprite (48x48)."""
    size = 48
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Body color
    body = (230, 190, 60)
    body_dark = (190, 150, 40)
    window = (50, 70, 100)
    
    # Main body (pointing UP)
    pygame.draw.rect(surf, body, (14, 8, 20, 32), border_radius=5)
    
    # Hood highlight
    pygame.draw.rect(surf, (250, 210, 80), (16, 10, 16, 8), border_radius=3)
    
    # Roof/cabin darker
    pygame.draw.rect(surf, body_dark, (16, 18, 16, 12), border_radius=2)
    
    # Windshield
    pygame.draw.rect(surf, window, (17, 19, 14, 6), border_radius=2)
    
    # Rear window
    pygame.draw.rect(surf, window, (17, 32, 14, 5), border_radius=2)
    
    # Headlights
    pygame.draw.circle(surf, (255, 255, 220), (18, 12), 3)
    pygame.draw.circle(surf, (255, 255, 220), (30, 12), 3)
    
    # Tail lights
    pygame.draw.circle(surf, (255, 60, 60), (18, 38), 2)
    pygame.draw.circle(surf, (255, 60, 60), (30, 38), 2)
    
    # Side mirrors
    pygame.draw.rect(surf, body_dark, (11, 20, 3, 4), border_radius=1)
    pygame.draw.rect(surf, body_dark, (34, 20, 3, 4), border_radius=1)
    
    return surf


def create_traffic_light():
    """Create traffic light sprite sheet (3 frames: R, Y, G)."""
    frame_w, frame_h = 32, 64
    sheet = pygame.Surface((frame_w * 3, frame_h), pygame.SRCALPHA)
    
    housing = (35, 38, 45)
    pole = (50, 55, 60)
    off = (30, 32, 35)
    
    states = [
        ((255, 60, 60), off, off),      # Red
        (off, (255, 220, 50), off),     # Yellow
        (off, off, (60, 255, 90)),      # Green
    ]
    
    for i, (red, yellow, green) in enumerate(states):
        x = i * frame_w
        
        # Pole
        pygame.draw.rect(sheet, pole, (x + 13, 42, 6, 22))
        
        # Housing
        pygame.draw.rect(sheet, housing, (x + 5, 2, 22, 42), border_radius=4)
        
        # Lights
        pygame.draw.circle(sheet, red, (x + 16, 12), 6)
        pygame.draw.circle(sheet, yellow, (x + 16, 24), 6)
        pygame.draw.circle(sheet, green, (x + 16, 36), 6)
        
        # Glow for active light
        active_colors = [red, yellow, green]
        for j, c in enumerate(active_colors):
            if c != off:
                glow = pygame.Surface((20, 20), pygame.SRCALPHA)
                pygame.draw.circle(glow, (*c[:3], 80), (10, 10), 10)
                sheet.blit(glow, (x + 6, 2 + j * 12))
    
    return sheet


def create_skyline():
    """Create city skyline background (1920x400)."""
    width, height = 1920, 400
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    
    # Sky gradient
    for y in range(height):
        t = y / height
        r = int(20 + t * 10)
        g = int(25 + t * 15)
        b = int(45 + t * 25)
        pygame.draw.line(surf, (r, g, b), (0, y), (width, y))
    
    # Stars
    random.seed(42)
    for _ in range(150):
        x = random.randint(0, width)
        y = random.randint(0, height // 2)
        alpha = random.randint(50, 200)
        size = random.choice([1, 1, 1, 2])
        star_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
        pygame.draw.circle(star_surf, (255, 255, 255, alpha), (size, size), size)
        surf.blit(star_surf, (x, y))
    
    # Buildings
    building_color = (15, 18, 28)
    x = 0
    while x < width:
        w = random.randint(50, 120)
        h = random.randint(120, 320)
        base_y = height - 50
        
        pygame.draw.rect(surf, building_color, (x, base_y - h, w, h + 50))
        
        # Windows
        for wy in range(base_y - h + 15, base_y - 20, 18):
            for wx in range(x + 8, x + w - 8, 14):
                if random.random() > 0.35:
                    lit = random.random() > 0.6
                    color = (60, 75, 100) if lit else (25, 30, 40)
                    pygame.draw.rect(surf, color, (wx, wy, 8, 10))
        
        x += w + random.randint(-15, 25)
    
    return surf


def create_wav(filepath, duration_ms=100, frequency=440):
    """Create a simple WAV file."""
    sample_rate = 22050
    num_samples = int(sample_rate * duration_ms / 1000)
    
    wav = bytearray()
    wav.extend(b'RIFF')
    wav.extend(struct.pack('<I', 36 + num_samples))
    wav.extend(b'WAVE')
    wav.extend(b'fmt ')
    wav.extend(struct.pack('<I', 16))
    wav.extend(struct.pack('<H', 1))
    wav.extend(struct.pack('<H', 1))
    wav.extend(struct.pack('<I', sample_rate))
    wav.extend(struct.pack('<I', sample_rate))
    wav.extend(struct.pack('<H', 1))
    wav.extend(struct.pack('<H', 8))
    wav.extend(b'data')
    wav.extend(struct.pack('<I', num_samples))
    
    for i in range(num_samples):
        t = i / sample_rate
        # Envelope
        env = min(1, i / 500) * max(0, 1 - i / num_samples)
        sample = int(127 + 50 * env * math.sin(2 * math.pi * frequency * t))
        wav.append(max(0, min(255, sample)))
    
    with open(filepath, 'wb') as f:
        f.write(wav)


def create_sounds():
    """Create placeholder sound effects."""
    sounds = [
        ("click.wav", 60, 900),
        ("light.wav", 150, 500),
        ("goal.wav", 300, 880),
        ("error.wav", 200, 200),
        ("engine.wav", 500, 80),
        ("ambient.wav", 2000, 60),
    ]
    
    for name, duration, freq in sounds:
        path = os.path.join(SOUNDS_DIR, name)
        create_wav(path, duration, freq)
        print(f"  Created: sounds/{name}")


def generate_all():
    """Generate all placeholder assets."""
    print("=" * 50)
    print("Generating AAA Mini City Assets")
    print("=" * 50)
    
    ensure_dirs()
    
    # Tileset
    print("\nCreating tileset...")
    tileset = create_tileset()
    pygame.image.save(tileset, os.path.join(ASSETS_DIR, "tileset.png"))
    print(f"  Created: tileset.png ({tileset.get_width()}x{tileset.get_height()})")
    
    # Vehicle
    print("\nCreating vehicle sprite...")
    vehicle = create_vehicle()
    pygame.image.save(vehicle, os.path.join(ASSETS_DIR, "vehicle.png"))
    print(f"  Created: vehicle.png ({vehicle.get_width()}x{vehicle.get_height()})")
    
    # Traffic light
    print("\nCreating traffic light sheet...")
    traffic = create_traffic_light()
    pygame.image.save(traffic, os.path.join(ASSETS_DIR, "traffic_light.png"))
    print(f"  Created: traffic_light.png ({traffic.get_width()}x{traffic.get_height()})")
    
    # Skyline
    print("\nCreating skyline background...")
    skyline = create_skyline()
    pygame.image.save(skyline, os.path.join(ASSETS_DIR, "skyline.png"))
    print(f"  Created: skyline.png ({skyline.get_width()}x{skyline.get_height()})")
    
    # Sounds
    print("\nCreating sound effects...")
    create_sounds()
    
    print("\n" + "=" * 50)
    print("All assets generated successfully!")
    print(f"Location: {ASSETS_DIR}")
    print("=" * 50)


if __name__ == "__main__":
    generate_all()
    pygame.quit()
