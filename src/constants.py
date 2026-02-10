"""
constants.py - Configuration for AAA Mini City Autonomous Vehicle Simulation.

Comprehensive configuration for:
- Display & rendering
- Visual effects (bloom, shadows, particles)
- Audio settings
- Tile system
- Colors & themes
- Animation timing
"""

import os

# ============================================================================
# PATHS
# ============================================================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
SOUNDS_DIR = os.path.join(ASSETS_DIR, "sounds")

# Asset files
ASSET_TILESET = os.path.join(ASSETS_DIR, "tileset.png")
ASSET_VEHICLE = os.path.join(ASSETS_DIR, "vehicle.png")
ASSET_TRAFFIC_LIGHT = os.path.join(ASSETS_DIR, "traffic_light.png")
ASSET_SKYLINE = os.path.join(ASSETS_DIR, "skyline.png")
ASSET_PARTICLES = os.path.join(ASSETS_DIR, "particles.png")

# Sound files
SOUND_AMBIENT = os.path.join(SOUNDS_DIR, "ambient.wav")
SOUND_ENGINE = os.path.join(SOUNDS_DIR, "engine.wav")
SOUND_CLICK = os.path.join(SOUNDS_DIR, "click.wav")
SOUND_LIGHT_CHANGE = os.path.join(SOUNDS_DIR, "light.wav")
SOUND_GOAL = os.path.join(SOUNDS_DIR, "goal.wav")
SOUND_ERROR = os.path.join(SOUNDS_DIR, "error.wav")

# ============================================================================
# DISPLAY SETTINGS
# ============================================================================
TILE_SIZE = 64                  # Pixel size of each tile
FPS = 60                        # Target frames per second
DEFAULT_WIDTH = 1280            # Default window width
DEFAULT_HEIGHT = 720            # Default window height
FULLSCREEN = False              # Start in fullscreen

# ============================================================================
# GRID SETTINGS
# ============================================================================
GRID_COLS = 20                  # Number of columns
GRID_ROWS = 12                  # Number of rows

# ============================================================================
# CAMERA SETTINGS
# ============================================================================
CAMERA_LERP_SPEED = 4.0         # Camera follow smoothness
CAMERA_ZOOM_MIN = 0.5           # Minimum zoom level
CAMERA_ZOOM_MAX = 2.0           # Maximum zoom level
CAMERA_ZOOM_SPEED = 0.1         # Zoom per scroll tick
CAMERA_EDGE_MARGIN = 100        # Pixels from edge before camera moves

# ============================================================================
# VEHICLE SETTINGS
# ============================================================================
VEHICLE_SPEED = 200.0           # Base pixels per second
VEHICLE_LERP_SPEED = 8.0        # Movement interpolation
VEHICLE_ACCELERATION = 400.0    # Pixels per second squared
VEHICLE_DECELERATION = 600.0    # Braking speed
VEHICLE_WOBBLE_SPEED = 3.0      # Idle wobble frequency
VEHICLE_WOBBLE_AMOUNT = 1.5     # Idle wobble pixels
VEHICLE_TILT_AMOUNT = 3.0       # Acceleration tilt pixels
VEHICLE_DUST_RATE = 0.05        # Dust particles per frame

# ============================================================================
# TRAFFIC LIGHT TIMING (seconds)
# ============================================================================
TRAFFIC_RED_TIME = 4.0
TRAFFIC_YELLOW_TIME = 1.5
TRAFFIC_GREEN_TIME = 4.0
TRAFFIC_TRANSITION_TIME = 0.3   # Fade transition duration

# ============================================================================
# LIGHTING SETTINGS - NIGHT MODE
# ============================================================================
AMBIENT_LIGHT_LEVEL = 0.55      # Base ambient - darker for night driving
VEHICLE_LIGHT_RADIUS = 160      # Headlight cone radius - larger at night
VEHICLE_LIGHT_INTENSITY = 0.35  # Headlight brightness - more visible
SHADOW_OFFSET_X = 4             # Shadow direction X
SHADOW_OFFSET_Y = 6             # Shadow direction Y
SHADOW_OPACITY = 130            # Shadow alpha - deeper shadows
AO_STRENGTH = 60                # Ambient occlusion strength

# ============================================================================
# BLOOM SETTINGS
# ============================================================================
BLOOM_ENABLED = True
BLOOM_INTENSITY = 0.22          # Bloom strength - visible glow for night
BLOOM_THRESHOLD = 200           # Lower threshold for night atmosphere
BLOOM_BLUR_PASSES = 2           # Number of blur iterations
BLOOM_SCALE = 4                 # Downscale factor for performance

# ============================================================================
# PARTICLE SETTINGS
# ============================================================================
PARTICLES_ENABLED = True
PARTICLE_MAX_COUNT = 500        # Maximum active particles
DUST_LIFETIME = 1.5             # Seconds
DUST_SIZE = (3, 8)              # Min/max size
SMOKE_LIFETIME = 4.0            # Chimney smoke duration
SPARK_LIFETIME = 0.5            # Traffic light sparks
AMBIENT_PARTICLE_RATE = 0.02    # Floating dust spawn rate

# ============================================================================
# MINIMAP SETTINGS
# ============================================================================
MINIMAP_ENABLED = True
MINIMAP_SIZE = 160              # Pixels
MINIMAP_MARGIN = 20             # Distance from screen edge
MINIMAP_OPACITY = 200           # Alpha value
MINIMAP_SCALE = 0.1             # Scale relative to full map

# ============================================================================
# UI SETTINGS
# ============================================================================
UI_PANEL_OPACITY = 200          # Panel background alpha
UI_PANEL_BLUR = True            # Enable panel blur effect
UI_PANEL_RADIUS = 16            # Corner radius
UI_ANIMATION_SPEED = 8.0        # UI transition speed

# Menu button settings
MENU_BUTTON_WIDTH = 280
MENU_BUTTON_HEIGHT = 56
MENU_BUTTON_SPACING = 16

UI_FONT_FAMILY = "Consolas"
UI_FONT_SIZE_TINY = 12
UI_FONT_SIZE_SMALL = 14
UI_FONT_SIZE_MEDIUM = 18
UI_FONT_SIZE_LARGE = 24
UI_FONT_SIZE_TITLE = 48
UI_FONT_SIZE_HUGE = 64

# ============================================================================
# AUDIO SETTINGS
# ============================================================================
AUDIO_ENABLED = True
MASTER_VOLUME = 0.8
MUSIC_VOLUME = 0.3
SFX_VOLUME = 0.6
AMBIENT_VOLUME = 0.2

# ============================================================================
# TILE VALUES - Grid cell types
# ============================================================================
TILE_ROAD = 0                   # Passable road
TILE_OBSTACLE = 1               # Building/obstacle
TILE_START = "S"                # Start position
TILE_GOAL = "G"                 # Goal position
TILE_TRAFFIC = "T"              # Traffic light

# Passable tiles for pathfinding
PASSABLE_TILES = (TILE_ROAD, TILE_START, TILE_GOAL, TILE_TRAFFIC)

# ============================================================================
# TILESET LAYOUT (8 columns x 8 rows = 64 tiles)
# ============================================================================
TILESET_COLS = 8
TILESET_ROWS = 8

# Tile indices by category
class TileIndex:
    # Roads (row 0-1)
    ROAD_H = 0              # Horizontal road
    ROAD_V = 1              # Vertical road
    ROAD_CROSS = 2          # 4-way intersection
    ROAD_T_UP = 3           # T facing up
    ROAD_T_DOWN = 4         # T facing down
    ROAD_T_LEFT = 5         # T facing left
    ROAD_T_RIGHT = 6        # T facing right
    ROAD_CORNER_TL = 7      # Corner top-left
    ROAD_CORNER_TR = 8      # Corner top-right
    ROAD_CORNER_BL = 9      # Corner bottom-left
    ROAD_CORNER_BR = 10     # Corner bottom-right
    ROAD_END_UP = 11        # Dead end up
    ROAD_END_DOWN = 12      # Dead end down
    ROAD_END_LEFT = 13      # Dead end left
    ROAD_END_RIGHT = 14     # Dead end right
    SIDEWALK = 15           # Sidewalk
    
    # Buildings (row 2-3)
    BUILDING_1 = 16
    BUILDING_2 = 17
    BUILDING_3 = 18
    BUILDING_4 = 19
    BUILDING_5 = 20
    BUILDING_6 = 21
    BUILDING_7 = 22
    BUILDING_8 = 23
    BUILDING_TALL_1 = 24
    BUILDING_TALL_2 = 25
    BUILDING_SHOP_1 = 26
    BUILDING_SHOP_2 = 27
    BUILDING_OFFICE = 28
    BUILDING_HOUSE_1 = 29
    BUILDING_HOUSE_2 = 30
    BUILDING_FACTORY = 31
    
    # Nature & Decoration (row 4-5)
    GRASS = 32
    GRASS_DARK = 33
    TREE_1 = 34
    TREE_2 = 35
    PARK = 36
    WATER = 37
    FOUNTAIN = 38
    BENCH = 39
    LAMP_POST = 40
    TRASH_CAN = 41
    FLOWER_BED = 42
    HEDGE = 43
    PARKING = 44
    CROSSWALK_H = 45
    CROSSWALK_V = 46
    MANHOLE = 47
    
    # Special (row 6-7)
    EMPTY = 48
    BLOCKED = 49
    START_MARKER = 50
    GOAL_MARKER = 51
    TRAFFIC_LIGHT_BASE = 52
    ARROW_UP = 53
    ARROW_DOWN = 54
    ARROW_LEFT = 55
    ARROW_RIGHT = 56

# ============================================================================
# COLOR PALETTE - Night driving theme
# ============================================================================
COLORS = {
    # Backgrounds - deep night colors
    "background": (3, 4, 8),
    "background_light": (8, 10, 16),
    "sky_top": (8, 12, 28),
    "sky_bottom": (2, 3, 8),
    
    # UI Colors
    "ui_panel": (12, 14, 22, 200),
    "ui_panel_light": (20, 24, 35, 220),
    "ui_border": (45, 55, 75),
    "ui_border_glow": (70, 130, 200),
    "ui_text": (235, 240, 250),
    "ui_text_dim": (130, 140, 160),
    "ui_text_bright": (255, 255, 255),
    "ui_accent": (80, 180, 255),
    "ui_success": (80, 255, 140),
    "ui_warning": (255, 200, 80),
    "ui_error": (255, 90, 90),
    
    # Buttons
    "button_normal": (35, 42, 58),
    "button_hover": (55, 75, 110),
    "button_active": (70, 110, 170),
    "button_disabled": (25, 28, 35),
    
    # Game elements - VIBRANT colors
    "path_glow": (50, 180, 255, 80),
    "path_line": (80, 200, 255),
    "path_dot": (120, 220, 255),
    "path_pulse": (180, 240, 255),
    
    "vehicle_glow": (255, 200, 80, 50),
    "vehicle_brake": (255, 50, 30),
    "vehicle_headlight": (255, 252, 245),
    
    "light_red": (255, 40, 40),
    "light_yellow": (255, 230, 50),
    "light_green": (40, 255, 90),
    "light_glow_red": (255, 60, 60, 70),
    "light_glow_green": (60, 255, 100, 70),
    
    "shadow": (0, 0, 0, 100),
    "shadow_soft": (0, 0, 0, 50),
    "ambient_occlusion": (0, 0, 0, 60),
    
    "particle_dust": (180, 160, 140),
    "particle_smoke": (100, 100, 110),
    "particle_spark": (255, 240, 180),
    
    # Status colors
    "status_moving": (80, 200, 255),
    "status_waiting": (255, 180, 80),
    "status_arrived": (80, 255, 140),
    "status_no_path": (255, 100, 100),
}

# ============================================================================
# ALGORITHM NAMES
# ============================================================================
ALGO_BFS = "BFS"
ALGO_GREEDY = "Greedy"
ALGO_ASTAR = "A*"
AVAILABLE_ALGORITHMS = [ALGO_BFS, ALGO_GREEDY, ALGO_ASTAR]

# ============================================================================
# DIRECTION VECTORS & ANGLES
# ============================================================================
DIRECTION_ANGLES = {
    (0, -1): 270,   # Left
    (0, 1): 90,     # Right
    (-1, 0): 0,     # Up
    (1, 0): 180,    # Down
    (-1, -1): 315,  # Up-Left
    (-1, 1): 45,    # Up-Right
    (1, -1): 225,   # Down-Left
    (1, 1): 135,    # Down-Right
}

# ============================================================================
# DEFAULT CITY MAP
# ============================================================================
DEFAULT_CITY_MAP = [
    [1,   1,   1,   0,   0,   0,   0,   0,   1,   1,   1,   1,   0,   0,   0,   0,   1,   1,   1,   1],
    [1,  "S", 0,   0,   1,   1,   0,   0,   0,   0,   0,   0,   0,   1,   1,   0,   0,   0,   1,   1],
    [0,   0,   0,   0,   0,   0,   0,   0,   1,   0,   0,   1,   0,   0,   0,   0,   0,   0,   0,   0],
    [1,   1,   0,   1,   1,   1,   0,   1,   1,   0,   0,   1,   1,   0,   1,   1,   1,   0,   1,   1],
    [0,   0,   0,   0,  "T", 0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  "T", 0,   0,   0,   0],
    [1,   1,   0,   1,   1,   1,   0,   1,   1,   1,   1,   1,   1,   0,   1,   1,   1,   0,   1,   1],
    [0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0],
    [1,   1,   0,   1,   1,   0,   1,   1,   0,   1,   1,   0,   1,   1,   0,   1,   1,   0,   1,   1],
    [0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0],
    [1,   1,   0,   1,   1,   0,   1,   1,   0,   1,   0,   1,   1,   0,   1,   1,   0,   1,   1,   1],
    [1,   1,   0,   0,   0,   0,   0,   0,   0,   0,   0,   0,  "T", 0,   0,   0,   0,   0,   0,  "G"],
    [1,   1,   1,   1,   1,   0,   1,   1,   1,   1,   1,   1,   1,   0,   1,   1,   1,   1,   1,   1],
]

# ============================================================================
# POST-PROCESSING LAYERS
# ============================================================================
class RenderLayer:
    BACKGROUND = 0      # Sky, parallax
    GROUND = 1          # Roads, grass
    SHADOWS = 2         # Tile shadows
    BUILDINGS = 3       # Building tiles
    DECORATIONS = 4     # Trees, lamps, etc
    PATH = 5            # Navigation path
    TRAFFIC_LIGHTS = 6  # Traffic light sprites
    VEHICLE = 7         # Player vehicle
    PARTICLES = 8       # All particles
    LIGHTING = 9        # Light overlay
    BLOOM = 10          # Bloom effect
    UI = 11             # User interface
    MINIMAP = 12        # Minimap overlay

# ============================================================================
# SETTINGS DEFAULTS (for save/load)
# ============================================================================
DEFAULT_SETTINGS = {
    "master_volume": MASTER_VOLUME,
    "music_volume": MUSIC_VOLUME,
    "sfx_volume": SFX_VOLUME,
    "bloom_enabled": BLOOM_ENABLED,
    "particles_enabled": PARTICLES_ENABLED,
    "minimap_enabled": MINIMAP_ENABLED,
    "fullscreen": FULLSCREEN,
    "camera_zoom": 1.0,
}
