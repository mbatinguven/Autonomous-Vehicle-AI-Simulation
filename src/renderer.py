"""
renderer.py - Advanced layered rendering engine.

Features:
- Tileset-based rendering with auto-selection
- Layered compositing (ground → shadows → objects → effects)
- Parallax background with city skyline
- Path visualization with glow and animated dots
- Integration with lighting, particles, and post-processing
"""

import pygame
import math
import os
from constants import (
    TILE_SIZE, TILESET_COLS, COLORS, TileIndex,
    TILE_ROAD, TILE_OBSTACLE, TILE_START, TILE_GOAL, TILE_TRAFFIC,
    ASSET_TILESET, ASSET_VEHICLE, ASSET_TRAFFIC_LIGHT, ASSET_SKYLINE,
    SHADOW_OFFSET_X, SHADOW_OFFSET_Y, SHADOW_OPACITY
)


class Tileset:
    """Manages tileset loading and tile extraction."""
    
    def __init__(self, path, tile_size=TILE_SIZE):
        self.tile_size = tile_size
        self.tiles = {}
        self._surface = None
        
        if os.path.exists(path):
            self._surface = pygame.image.load(path).convert_alpha()
            self._extract_tiles()
        else:
            self._create_fallback()
    
    def _extract_tiles(self):
        """Extract individual tiles from tileset."""
        cols = self._surface.get_width() // self.tile_size
        rows = self._surface.get_height() // self.tile_size
        
        for row in range(rows):
            for col in range(cols):
                idx = row * cols + col
                rect = pygame.Rect(
                    col * self.tile_size,
                    row * self.tile_size,
                    self.tile_size,
                    self.tile_size
                )
                tile = self._surface.subsurface(rect).copy()
                self.tiles[idx] = tile
    
    def _create_fallback(self):
        """Create fallback tiles - VIBRANT high-contrast colors."""
        # Road tiles - cleaner, brighter asphalt
        road_colors = [(65, 70, 78), (70, 75, 82)]
        # Buildings - richer, more saturated colors
        building_colors = [(95, 85, 75), (105, 95, 85), (85, 100, 115), (100, 90, 80)]
        
        # Create basic tiles
        for i in range(64):
            tile = pygame.Surface((self.tile_size, self.tile_size), pygame.SRCALPHA)
            
            if i < 16:  # Roads - brighter asphalt
                color = road_colors[i % 2]
                tile.fill(color)
                # Add road markings - bright yellow
                if i in (0, 6):  # Horizontal
                    pygame.draw.line(tile, (200, 190, 100), 
                                   (0, self.tile_size // 2), 
                                   (self.tile_size, self.tile_size // 2), 2)
                elif i in (1, 7):  # Vertical
                    pygame.draw.line(tile, (200, 190, 100),
                                   (self.tile_size // 2, 0),
                                   (self.tile_size // 2, self.tile_size), 2)
            elif i < 32:  # Buildings - richer colors
                color = building_colors[(i - 16) % len(building_colors)]
                margin = 4
                pygame.draw.rect(tile, (55, 60, 50),  # Ground - cleaner
                               (0, 0, self.tile_size, self.tile_size))
                pygame.draw.rect(tile, color,
                               (margin, margin, 
                                self.tile_size - margin * 2,
                                self.tile_size - margin * 2),
                               border_radius=2)
                # Windows - brighter, more vivid
                for wy in range(12, self.tile_size - 12, 14):
                    for wx in range(12, self.tile_size - 12, 16):
                        pygame.draw.rect(tile, (180, 200, 240),
                                       (wx, wy, 6, 8))
            else:  # Grass/nature - richer green
                tile.fill((60, 100, 55))
                # Add texture
                for _ in range(5):
                    x = (i * 17 + _ * 23) % self.tile_size
                    y = (i * 13 + _ * 31) % self.tile_size
                    pygame.draw.circle(tile, (55, 90, 50), (x, y), 3)
            
            self.tiles[i] = tile
    
    def get_tile(self, index):
        """Get a tile by index."""
        return self.tiles.get(index, self.tiles.get(0))


class SkylineBackground:
    """Parallax city skyline background."""
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self._surface = None
        self._create_skyline()
    
    def _create_skyline(self):
        """Generate a city skyline background."""
        self._surface = pygame.Surface((self.width * 2, self.height), pygame.SRCALPHA)
        
        # Sky gradient
        for y in range(self.height):
            t = y / self.height
            r = int(COLORS["sky_top"][0] + (COLORS["sky_bottom"][0] - COLORS["sky_top"][0]) * t)
            g = int(COLORS["sky_top"][1] + (COLORS["sky_bottom"][1] - COLORS["sky_top"][1]) * t)
            b = int(COLORS["sky_top"][2] + (COLORS["sky_bottom"][2] - COLORS["sky_top"][2]) * t)
            pygame.draw.line(self._surface, (r, g, b), (0, y), (self.width * 2, y))
        
        # Stars
        import random
        random.seed(42)
        for _ in range(100):
            x = random.randint(0, self.width * 2)
            y = random.randint(0, self.height // 2)
            alpha = random.randint(50, 150)
            pygame.draw.circle(self._surface, (255, 255, 255, alpha), (x, y), 1)
        
        # Buildings silhouette
        building_color = (15, 18, 25)
        base_y = self.height - 100
        
        buildings = []
        x = 0
        while x < self.width * 2:
            w = random.randint(30, 80)
            h = random.randint(80, 250)
            buildings.append((x, base_y - h, w, h + 100))
            x += w + random.randint(-10, 20)
        
        for bx, by, bw, bh in buildings:
            pygame.draw.rect(self._surface, building_color, (bx, by, bw, bh))
            
            # Windows
            for wy in range(by + 10, by + bh - 20, 15):
                for wx in range(bx + 5, bx + bw - 5, 12):
                    if random.random() > 0.3:
                        window_color = (40, 50, 70) if random.random() > 0.7 else (25, 30, 40)
                        pygame.draw.rect(self._surface, window_color, (wx, wy, 6, 8))
    
    def resize(self, width, height):
        """Handle resize."""
        self.width = width
        self.height = height
        self._create_skyline()
    
    def draw(self, surface, parallax_offset=0):
        """Draw skyline with parallax."""
        offset = int(parallax_offset * 0.3) % self.width
        surface.blit(self._surface, (-offset, 0))


class PathRenderer:
    """Renders the navigation path with effects."""
    
    def __init__(self):
        self._pulse_time = 0
        self._dot_positions = []
    
    def update(self, dt):
        """Update path animations."""
        self._pulse_time += dt
    
    def render(self, surface, path, current_index, camera):
        """
        Render the path with glow and animated dots.
        
        Args:
            surface: Target surface
            path: List of (row, col) tuples
            current_index: Current position in path
            camera: Camera for coordinate transform
        """
        if len(path) < 2:
            return
        
        # Convert to screen coordinates
        points = []
        for r, c in path:
            sx, sy = camera.grid_to_screen(r, c)
            points.append((int(sx), int(sy)))
        
        # Draw glow (wider, semi-transparent)
        if len(points) >= 2:
            glow_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
            pygame.draw.lines(glow_surf, (*COLORS["path_glow"][:3], 60), False, points, 12)
            pygame.draw.lines(glow_surf, (*COLORS["path_glow"][:3], 40), False, points, 20)
            surface.blit(glow_surf, (0, 0))
        
        # Draw main path line (future portion)
        future_points = points[max(0, current_index):]
        if len(future_points) >= 2:
            pygame.draw.lines(surface, COLORS["path_line"], False, future_points, 3)
        
        # Animated moving dots along path
        self._render_moving_dots(surface, points, current_index)
        
        # Static dots at nodes
        for i, point in enumerate(points):
            if i >= current_index:
                pygame.draw.circle(surface, COLORS["path_dot"], point, 4)
                pygame.draw.circle(surface, COLORS["background"], point, 2)
    
    def _render_moving_dots(self, surface, points, current_index):
        """Render animated dots moving along the path."""
        if len(points) < 2:
            return
        
        # Calculate total path length
        total_length = 0
        segments = []
        for i in range(len(points) - 1):
            dx = points[i + 1][0] - points[i][0]
            dy = points[i + 1][1] - points[i][1]
            length = math.sqrt(dx * dx + dy * dy)
            segments.append(length)
            total_length += length
        
        if total_length < 1:
            return
        
        # Draw multiple moving dots
        num_dots = max(1, int(total_length / 80))
        speed = 100  # Pixels per second
        
        for i in range(num_dots):
            # Calculate position along path
            offset = (self._pulse_time * speed + i * total_length / num_dots) % total_length
            
            # Find which segment and position within it
            cumulative = 0
            for j, seg_len in enumerate(segments):
                if cumulative + seg_len > offset:
                    t = (offset - cumulative) / seg_len
                    x = points[j][0] + (points[j + 1][0] - points[j][0]) * t
                    y = points[j][1] + (points[j + 1][1] - points[j][1]) * t
                    
                    # Only draw if ahead of current position
                    if j >= current_index:
                        # Pulsing alpha
                        alpha = int(150 + 50 * math.sin(self._pulse_time * 4 + i))
                        dot_surf = pygame.Surface((12, 12), pygame.SRCALPHA)
                        pygame.draw.circle(dot_surf, (*COLORS["path_pulse"][:3], alpha), (6, 6), 5)
                        surface.blit(dot_surf, (int(x) - 6, int(y) - 6))
                    break
                cumulative += seg_len


class Renderer:
    """
    Main rendering engine coordinating all visual systems.
    """
    
    def __init__(self, screen_width, screen_height):
        self.width = screen_width
        self.height = screen_height
        
        # Load tileset
        self.tileset = Tileset(ASSET_TILESET)
        
        # Background
        self.skyline = SkylineBackground(screen_width, screen_height)
        
        # Path renderer
        self.path_renderer = PathRenderer()
        
        # Vehicle sprite
        self.vehicle_sprite = self._load_vehicle()
        self.vehicle_rotations = self._prerender_rotations(self.vehicle_sprite)
        
        # Traffic light sprites
        self.traffic_light_sheet = self._load_traffic_lights()
        
        # Shadow surface (reusable)
        self._tile_shadow = self._create_tile_shadow()
        
        # Render surfaces
        self._ground_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        self._object_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
    
    def _load_vehicle(self):
        """Load vehicle sprite."""
        if os.path.exists(ASSET_VEHICLE):
            return pygame.image.load(ASSET_VEHICLE).convert_alpha()
        
        # Fallback
        size = 48
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.rect(surf, (220, 180, 50), (12, 8, 24, 32), border_radius=6)
        pygame.draw.rect(surf, (60, 80, 100), (14, 18, 20, 8), border_radius=2)
        pygame.draw.circle(surf, (255, 255, 200), (16, 12), 3)
        pygame.draw.circle(surf, (255, 255, 200), (32, 12), 3)
        return surf
    
    def _prerender_rotations(self, sprite):
        """Pre-render rotated versions of sprite."""
        rotations = {}
        for angle in range(0, 360, 15):  # Every 15 degrees
            rotations[angle] = pygame.transform.rotate(sprite, -angle)
        return rotations
    
    def _load_traffic_lights(self):
        """Load traffic light sprite sheet."""
        if os.path.exists(ASSET_TRAFFIC_LIGHT):
            return pygame.image.load(ASSET_TRAFFIC_LIGHT).convert_alpha()
        
        # Fallback - 3 frames horizontal
        sheet = pygame.Surface((96, 64), pygame.SRCALPHA)
        colors = [(255, 60, 60), (255, 220, 50), (60, 255, 80)]
        
        for i, color in enumerate(colors):
            x = i * 32
            pygame.draw.rect(sheet, (40, 40, 45), (x + 6, 4, 20, 38), border_radius=4)
            pygame.draw.rect(sheet, (60, 60, 65), (x + 14, 40, 4, 24))
            
            # Lights
            for j, c in enumerate([(60, 60, 60)] * 3):
                pygame.draw.circle(sheet, c, (x + 16, 12 + j * 12), 5)
            pygame.draw.circle(sheet, color, (x + 16, 12 + i * 12), 5)
        
        return sheet
    
    def _create_tile_shadow(self):
        """Create reusable tile shadow."""
        shadow = pygame.Surface((TILE_SIZE + 10, TILE_SIZE + 10), pygame.SRCALPHA)
        shadow_color = (0, 0, 0, SHADOW_OPACITY)
        pygame.draw.rect(shadow, shadow_color,
                        (SHADOW_OFFSET_X, SHADOW_OFFSET_Y, TILE_SIZE, TILE_SIZE),
                        border_radius=4)
        return shadow
    
    def resize(self, width, height):
        """Handle screen resize."""
        self.width = width
        self.height = height
        self.skyline.resize(width, height)
        self._ground_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        self._object_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    
    def update(self, dt):
        """Update animated elements."""
        self.path_renderer.update(dt)
    
    def render_background(self, surface, camera):
        """Render the parallax background."""
        self.skyline.draw(surface, camera.x)
    
    def render_grid(self, surface, grid_data, camera):
        """
        Render the grid tiles with shadows.
        """
        rows = len(grid_data)
        cols = len(grid_data[0]) if grid_data else 0
        
        # Determine visible range
        view = camera.view_rect
        start_col = max(0, int(view.left / TILE_SIZE) - 1)
        end_col = min(cols, int(view.right / TILE_SIZE) + 2)
        start_row = max(0, int(view.top / TILE_SIZE) - 1)
        end_row = min(rows, int(view.bottom / TILE_SIZE) + 2)
        
        # First pass: ground tiles and shadows
        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                cell = grid_data[row][col]
                screen_x, screen_y = camera.world_to_screen(col * TILE_SIZE, row * TILE_SIZE)
                
                # Get tile index
                if cell == TILE_OBSTACLE:
                    # Draw shadow first
                    surface.blit(self._tile_shadow, (screen_x - 2, screen_y - 2))
                    
                    # Building tile
                    tile_idx = TileIndex.BUILDING_1 + ((row + col) % 8)
                else:
                    # Road tile (auto-select based on neighbors)
                    tile_idx = self._get_road_tile(grid_data, row, col, rows, cols)
                
                tile = self.tileset.get_tile(tile_idx)
                surface.blit(tile, (screen_x, screen_y))
                
                # Draw markers for start/goal
                if cell == TILE_START:
                    self._draw_marker(surface, screen_x, screen_y, COLORS["ui_accent"], "S")
                elif cell == TILE_GOAL:
                    self._draw_marker(surface, screen_x, screen_y, COLORS["ui_success"], "G")
    
    def _get_road_tile(self, grid_data, row, col, rows, cols):
        """Determine which road tile to use based on neighbors."""
        def is_road(r, c):
            if r < 0 or c < 0 or r >= rows or c >= cols:
                return False
            cell = grid_data[r][c]
            return cell in (TILE_ROAD, TILE_START, TILE_GOAL, TILE_TRAFFIC)
        
        up = is_road(row - 1, col)
        down = is_road(row + 1, col)
        left = is_road(row, col - 1)
        right = is_road(row, col + 1)
        
        connections = sum([up, down, left, right])
        
        if connections >= 3:
            return TileIndex.ROAD_CROSS
        elif up and down and not left and not right:
            return TileIndex.ROAD_V
        elif left and right and not up and not down:
            return TileIndex.ROAD_H
        elif connections == 2:
            if up and right:
                return TileIndex.ROAD_CORNER_BL
            elif up and left:
                return TileIndex.ROAD_CORNER_BR
            elif down and right:
                return TileIndex.ROAD_CORNER_TL
            elif down and left:
                return TileIndex.ROAD_CORNER_TR
            else:
                return TileIndex.ROAD_CROSS
        else:
            return TileIndex.ROAD_CROSS
    
    def _draw_marker(self, surface, x, y, color, text):
        """Draw start/goal marker."""
        center_x = x + TILE_SIZE // 2
        center_y = y + TILE_SIZE // 2
        
        # Glow
        glow = pygame.Surface((50, 50), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*color[:3], 60), (25, 25), 25)
        surface.blit(glow, (center_x - 25, center_y - 25))
        
        # Text
        from ui import FontManager
        font = FontManager.get("large", bold=True)
        text_surf = font.render(text, True, color)
        text_rect = text_surf.get_rect(center=(center_x, center_y))
        surface.blit(text_surf, text_rect)
    
    def render_path(self, surface, path, current_index, camera):
        """Render the navigation path."""
        self.path_renderer.render(surface, path, current_index, camera)
    
    def render_vehicle(self, surface, x, y, angle, is_waiting, camera):
        """
        Render the vehicle with shadow and effects.
        
        Args:
            surface: Target surface
            x, y: World pixel position
            angle: Rotation in degrees
            is_waiting: Whether waiting at light (tints vehicle)
            camera: Camera for transform
        """
        screen_x, screen_y = camera.world_to_screen(x, y)
        
        # Get rotated sprite
        snapped_angle = (round(angle / 15) * 15) % 360
        sprite = self.vehicle_rotations.get(snapped_angle, self.vehicle_sprite)
        
        # Shadow
        shadow = pygame.Surface((50, 30), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 80), (0, 0, 50, 30))
        surface.blit(shadow, (screen_x - 25, screen_y - 8))
        
        # Glow under vehicle
        glow = pygame.Surface((60, 60), pygame.SRCALPHA)
        glow_color = COLORS["vehicle_brake"] if is_waiting else COLORS["vehicle_glow"][:3]
        pygame.draw.circle(glow, (*glow_color, 50), (30, 30), 28)
        surface.blit(glow, (screen_x - 30, screen_y - 26))
        
        # Vehicle sprite
        if is_waiting:
            sprite = sprite.copy()
            sprite.fill((255, 180, 150), special_flags=pygame.BLEND_RGB_MULT)
        
        rect = sprite.get_rect(center=(int(screen_x), int(screen_y)))
        surface.blit(sprite, rect)
        
        # Brake lights when waiting
        if is_waiting:
            brake_surf = pygame.Surface((20, 10), pygame.SRCALPHA)
            pygame.draw.rect(brake_surf, (*COLORS["vehicle_brake"], 200), (0, 0, 20, 10), border_radius=3)
            # Position behind vehicle based on angle
            angle_rad = math.radians(angle)
            offset_x = -math.sin(angle_rad) * 15
            offset_y = math.cos(angle_rad) * 15
            surface.blit(brake_surf, (screen_x + offset_x - 10, screen_y + offset_y - 5))
    
    def render_traffic_light(self, surface, row, col, state, camera):
        """Render a traffic light at grid position."""
        screen_x, screen_y = camera.world_to_screen(col * TILE_SIZE, row * TILE_SIZE)
        
        # Select frame from sheet
        frame_map = {"red": 0, "yellow": 1, "green": 2}
        frame = frame_map.get(state, 0)
        
        frame_w = self.traffic_light_sheet.get_width() // 3
        frame_h = self.traffic_light_sheet.get_height()
        
        src_rect = pygame.Rect(frame * frame_w, 0, frame_w, frame_h)
        dest_x = screen_x + TILE_SIZE - frame_w - 4
        dest_y = screen_y + 4
        
        # Glow effect
        glow_colors = {
            "red": COLORS["light_glow_red"],
            "yellow": (255, 220, 50, 80),
            "green": COLORS["light_glow_green"],
        }
        glow_color = glow_colors.get(state, COLORS["light_glow_red"])
        
        glow = pygame.Surface((60, 60), pygame.SRCALPHA)
        pygame.draw.circle(glow, glow_color, (30, 30), 28)
        surface.blit(glow, (dest_x + frame_w // 2 - 30, dest_y + 20 - 30))
        
        # Traffic light sprite
        surface.blit(self.traffic_light_sheet, (dest_x, dest_y), src_rect)
    
    def render_npc_vehicle(self, surface, x, y, angle, color, is_braking, camera):
        """
        Render an NPC vehicle.
        
        Args:
            surface: Target surface
            x, y: World pixel position
            angle: Rotation in degrees
            color: Vehicle body color (R, G, B)
            is_braking: Show brake lights
            camera: Camera for transform
        """
        screen_x, screen_y = camera.world_to_screen(x, y)
        
        # Shadow
        shadow = pygame.Surface((46, 26), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 70), (0, 0, 46, 26))
        surface.blit(shadow, (screen_x - 23, screen_y - 6))
        
        # Create NPC vehicle sprite (simpler than player)
        size = 40
        npc_surf = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Body
        body_rect = pygame.Rect(8, 5, 24, 30)
        pygame.draw.rect(npc_surf, color, body_rect, border_radius=4)
        
        # Windshield
        pygame.draw.rect(npc_surf, (60, 80, 100), (11, 10, 18, 8), border_radius=2)
        
        # Headlights
        pygame.draw.circle(npc_surf, (255, 250, 200), (12, 8), 3)
        pygame.draw.circle(npc_surf, (255, 250, 200), (28, 8), 3)
        
        # Tail lights
        tail_color = (255, 50, 30) if is_braking else (150, 30, 30)
        pygame.draw.rect(npc_surf, tail_color, (10, 32, 6, 3))
        pygame.draw.rect(npc_surf, tail_color, (24, 32, 6, 3))
        
        # Rotate
        rotated = pygame.transform.rotate(npc_surf, -angle)
        rect = rotated.get_rect(center=(int(screen_x), int(screen_y)))
        surface.blit(rotated, rect)
        
        # Brake light glow when braking
        if is_braking:
            glow = pygame.Surface((30, 30), pygame.SRCALPHA)
            pygame.draw.circle(glow, (255, 50, 30, 60), (15, 15), 12)
            angle_rad = math.radians(angle)
            offset_x = -math.sin(angle_rad) * 18
            offset_y = math.cos(angle_rad) * 18
            surface.blit(glow, (screen_x + offset_x - 15, screen_y + offset_y - 15))
