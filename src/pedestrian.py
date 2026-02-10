"""
pedestrian.py - Pedestrian and crosswalk system.

Features:
- Crosswalk zones on the map (auto-generated)
- Pedestrians that walk across crosswalks
- Pedestrians wait for safe crossing
- Vehicle must stop for pedestrians
- Dynamic crosswalk updates when grid changes
"""

import math
import random
from constants import TILE_SIZE, COLORS


class Pedestrian:
    """
    A single pedestrian that roams between different crosswalks.
    Never stops - always walking to random crosswalks.
    """
    
    def __init__(self, start_x, start_y, end_x, end_y, speed=50, current_crosswalk=None):
        """
        Args:
            start_x, start_y: Starting world position
            end_x, end_y: Destination world position
            speed: Walking speed in pixels/second
            current_crosswalk: Current crosswalk reference
        """
        # Position
        self.x = start_x
        self.y = start_y
        self.start_x = start_x
        self.start_y = start_y
        self.end_x = end_x
        self.end_y = end_y
        
        # Movement - always walking, never finished
        self.speed = speed
        self.walking = False
        self.finished = False  # Never set to True
        self.returning = False
        
        # Crosswalk navigation
        self.current_crosswalk = current_crosswalk
        self.target_crosswalk = None
        self.needs_new_crosswalk = False
        self.crosses_completed = 0  # Track number of crossings
        
        # Wait for safe crossing
        self.wait_timer = 0
        self.wait_time = random.uniform(0.3, 1.5)  # Quick wait times
        
        # Animation
        self.walk_frame = 0
        self.walk_timer = 0
        
        # Visual variation
        self.color = random.choice([
            (200, 80, 80),    # Red shirt
            (80, 120, 200),   # Blue shirt
            (80, 180, 80),    # Green shirt
            (200, 180, 80),   # Yellow shirt
            (180, 100, 180),  # Purple shirt
            (200, 200, 200),  # White shirt
            (100, 100, 100),  # Gray
            (220, 150, 100),  # Tan
        ])
        self.size = random.uniform(0.8, 1.2)
    
    @property
    def world_position(self):
        return (self.x, self.y)
    
    @property
    def grid_position(self):
        col = int(self.x / TILE_SIZE)
        row = int(self.y / TILE_SIZE)
        return (row, col)
    
    def update(self, dt, is_safe_to_cross=True):
        """Update pedestrian state - roams between crosswalks, never finishes."""
        # If not walking yet, wait for safe crossing
        if not self.walking:
            if is_safe_to_cross:
                self.wait_timer += dt
                if self.wait_timer >= self.wait_time:
                    self.walking = True
            else:
                self.wait_timer = max(0, self.wait_timer - dt * 0.5)
            return
        
        # Walk toward destination
        target_x = self.end_x if not self.returning else self.start_x
        target_y = self.end_y if not self.returning else self.start_y
        
        dx = target_x - self.x
        dy = target_y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        
        if dist > 2:
            # Move
            move_dist = self.speed * dt
            self.x += (dx / dist) * move_dist
            self.y += (dy / dist) * move_dist
            
            # Animation
            self.walk_timer += dt
            if self.walk_timer >= 0.12:
                self.walk_timer = 0
                self.walk_frame = (self.walk_frame + 1) % 4
        else:
            # Reached destination - complete crossing
            self.crosses_completed += 1
            
            # After 2-4 crossings, request new crosswalk
            if self.crosses_completed >= random.randint(2, 4):
                self.needs_new_crosswalk = True
                self.crosses_completed = 0
            
            # Turn around and continue
            self.returning = not self.returning
            self.wait_timer = 0
            self.wait_time = random.uniform(0.5, 2.0)  # Short wait before turning back
            self.walking = False
            # Never set finished = True, pedestrians loop forever
    
    def set_new_crosswalk(self, new_crosswalk):
        """Assign pedestrian to a new crosswalk."""
        if not new_crosswalk:
            return
        
        self.current_crosswalk = new_crosswalk
        self.target_crosswalk = None
        self.needs_new_crosswalk = False
        
        # Set new start and end positions
        if random.random() > 0.5:
            self.start_x, self.start_y = new_crosswalk.start
            self.end_x, self.end_y = new_crosswalk.end
        else:
            self.start_x, self.start_y = new_crosswalk.end
            self.end_x, self.end_y = new_crosswalk.start
        
        # Move to new crosswalk instantly (teleport)
        self.x = self.start_x
        self.y = self.start_y
        self.returning = False
        self.walking = False
        self.wait_timer = 0
        self.wait_time = random.uniform(0.2, 1.0)
    
    def _get_progress(self):
        """Get crossing progress 0-1."""
        total_dist = math.sqrt(
            (self.end_x - self.start_x) ** 2 + 
            (self.end_y - self.start_y) ** 2
        )
        current_dist = math.sqrt(
            (self.x - self.start_x) ** 2 + 
            (self.y - self.start_y) ** 2
        )
        return current_dist / total_dist if total_dist > 0 else 1


class Crosswalk:
    """
    A crosswalk zone where pedestrians can cross.
    """
    
    def __init__(self, row, col, direction="horizontal"):
        """
        Args:
            row, col: Grid position
            direction: "horizontal" or "vertical"
        """
        self.row = row
        self.col = col
        self.direction = direction
        
        # World position (center)
        self.x = col * TILE_SIZE + TILE_SIZE / 2
        self.y = row * TILE_SIZE + TILE_SIZE / 2
        
        # Crossing path (extends to sidewalk)
        if direction == "horizontal":
            self.start = (self.x - TILE_SIZE * 0.7, self.y)
            self.end = (self.x + TILE_SIZE * 0.7, self.y)
        else:
            self.start = (self.x, self.y - TILE_SIZE * 0.7)
            self.end = (self.x, self.y + TILE_SIZE * 0.7)
    
    @property
    def grid_position(self):
        return (self.row, self.col)


class PedestrianManager:
    """
    Manages crosswalks and pedestrians.
    """
    
    def __init__(self):
        self.crosswalks = []
        self.pedestrians = []
        
        self.spawn_timer = 0
        self.spawn_interval = 1.0  # Check every second
        self.target_pedestrians = 12  # Target count to maintain
        
        # Track grid state for dynamic updates
        self._grid_hash = None
        self._initialized = False
    
    def add_crosswalk(self, row, col, direction="horizontal"):
        """Add a crosswalk at grid position."""
        # Check if already exists
        for cw in self.crosswalks:
            if cw.row == row and cw.col == col:
                return cw
        
        crosswalk = Crosswalk(row, col, direction)
        self.crosswalks.append(crosswalk)
        return crosswalk
    
    def remove_crosswalk_at(self, row, col):
        """Remove crosswalk at position."""
        self.crosswalks = [cw for cw in self.crosswalks 
                          if not (cw.row == row and cw.col == col)]
    
    def spawn_pedestrian_at_crosswalk(self, crosswalk):
        """Spawn a pedestrian at a crosswalk."""
        if len(self.pedestrians) >= self.target_pedestrians:
            return None
        
        # Random side to start
        if random.random() > 0.5:
            start = crosswalk.start
            end = crosswalk.end
        else:
            start = crosswalk.end
            end = crosswalk.start
        
        speed = random.uniform(45, 80)
        pedestrian = Pedestrian(start[0], start[1], end[0], end[1], speed, crosswalk)
        self.pedestrians.append(pedestrian)
        return pedestrian
    
    def initialize_pedestrians(self):
        """Spawn initial batch of pedestrians."""
        if self._initialized or not self.crosswalks:
            return
        
        # Spawn all target pedestrians at start
        for _ in range(self.target_pedestrians):
            if self.crosswalks:
                crosswalk = random.choice(self.crosswalks)
                self.spawn_pedestrian_at_crosswalk(crosswalk)
        
        self._initialized = True
    
    def update(self, dt, vehicle_positions=None, grid_data=None):
        """
        Update all pedestrians.
        
        Args:
            dt: Delta time
            vehicle_positions: List of (x, y) vehicle world positions
            grid_data: Current grid (for dynamic crosswalk validation)
        """
        # Check if grid changed and validate crosswalks
        if grid_data:
            self._validate_crosswalks(grid_data)
        
        # Initialize on first update
        if not self._initialized and self.crosswalks:
            self.initialize_pedestrians()
        
        # Ensure we have target pedestrians (only spawn if below target, pedestrians never removed)
        if len(self.pedestrians) < self.target_pedestrians and self.crosswalks:
            self.spawn_timer += dt
            if self.spawn_timer >= self.spawn_interval:
                self.spawn_timer = 0
                # Spawn more pedestrians to reach target
                while len(self.pedestrians) < self.target_pedestrians and self.crosswalks:
                    crosswalk = random.choice(self.crosswalks)
                    if not self.spawn_pedestrian_at_crosswalk(crosswalk):
                        break
        
        # Update pedestrians - they roam between crosswalks forever
        for ped in self.pedestrians:
            # Check if pedestrian needs new crosswalk
            if ped.needs_new_crosswalk and self.crosswalks and len(self.crosswalks) > 1:
                # Pick a random different crosswalk
                available_crosswalks = [cw for cw in self.crosswalks if cw != ped.current_crosswalk]
                if available_crosswalks:
                    new_crosswalk = random.choice(available_crosswalks)
                    ped.set_new_crosswalk(new_crosswalk)
            
            # Check if safe (no vehicles nearby)
            is_safe = True
            if vehicle_positions:
                for vx, vy in vehicle_positions:
                    dist = math.sqrt((ped.x - vx) ** 2 + (ped.y - vy) ** 2)
                    if dist < TILE_SIZE * 2:
                        is_safe = False
                        break
            
            ped.update(dt, is_safe)
            # Pedestrians never finish - they roam between crosswalks forever
    
    def _validate_crosswalks(self, grid_data):
        """Remove crosswalks where buildings now exist."""
        rows = len(grid_data)
        cols = len(grid_data[0]) if rows > 0 else 0
        
        valid_crosswalks = []
        for cw in self.crosswalks:
            # Check if position is still a road
            if 0 <= cw.row < rows and 0 <= cw.col < cols:
                cell = grid_data[cw.row][cw.col]
                if cell == 0 or cell == "T":  # Road or traffic light
                    valid_crosswalks.append(cw)
        
        self.crosswalks = valid_crosswalks
    
    def get_positions(self):
        """Get all pedestrian world positions."""
        return [ped.world_position for ped in self.pedestrians]
    
    def get_grid_positions(self):
        """Get all pedestrian grid positions."""
        return [ped.grid_position for ped in self.pedestrians]
    
    def get_crosswalk_positions(self):
        """Get all crosswalk grid positions."""
        return [cw.grid_position for cw in self.crosswalks]
    
    def clear(self):
        """Remove all pedestrians."""
        self.pedestrians.clear()
    
    def clear_all(self):
        """Remove all pedestrians and crosswalks."""
        self.pedestrians.clear()
        self.crosswalks.clear()
        self._initialized = False
    
    def setup_from_grid(self, grid_data):
        """
        Auto-detect crosswalk locations from grid.
        Places crosswalks at suitable road positions.
        """
        self.crosswalks.clear()
        
        rows = len(grid_data)
        cols = len(grid_data[0]) if rows > 0 else 0
        
        # Find crosswalk positions - roads adjacent to buildings
        for r in range(1, rows - 1):
            for c in range(1, cols - 1):
                cell = grid_data[r][c]
                if cell == 0:  # Road
                    # Check if it's a good crosswalk location
                    # Option 1: Vertical crossing (buildings left and right)
                    if grid_data[r][c-1] == 1 and grid_data[r][c+1] == 1:
                        # Make sure road continues up/down
                        if (grid_data[r-1][c] == 0 or grid_data[r-1][c] in ("S", "G", "T")) and \
                           (grid_data[r+1][c] == 0 or grid_data[r+1][c] in ("S", "G", "T")):
                            self.add_crosswalk(r, c, "horizontal")
                    
                    # Option 2: Horizontal crossing (buildings up and down)
                    elif grid_data[r-1][c] == 1 and grid_data[r+1][c] == 1:
                        # Make sure road continues left/right
                        if (grid_data[r][c-1] == 0 or grid_data[r][c-1] in ("S", "G", "T")) and \
                           (grid_data[r][c+1] == 0 or grid_data[r][c+1] in ("S", "G", "T")):
                            self.add_crosswalk(r, c, "vertical")
        
        # If not enough crosswalks, add some at intersections
        if len(self.crosswalks) < 3:
            for r in range(2, rows - 2, 3):
                for c in range(2, cols - 2, 3):
                    if grid_data[r][c] == 0:
                        # Count adjacent roads
                        adj_roads = 0
                        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < rows and 0 <= nc < cols:
                                if grid_data[nr][nc] == 0 or grid_data[nr][nc] in ("S", "G", "T"):
                                    adj_roads += 1
                        
                        if adj_roads >= 2:
                            direction = "horizontal" if random.random() > 0.5 else "vertical"
                            self.add_crosswalk(r, c, direction)


class PedestrianRenderer:
    """
    Renders pedestrians and crosswalks.
    """
    
    def render_crosswalk(self, surface, crosswalk, camera):
        """Render a crosswalk."""
        import pygame
        
        screen_x, screen_y = camera.world_to_screen(crosswalk.x, crosswalk.y)
        
        # Zebra stripes
        stripe_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        
        if crosswalk.direction == "horizontal":
            for i in range(0, TILE_SIZE, 10):
                pygame.draw.rect(stripe_surf, (255, 255, 255, 200),
                               (i + 2, TILE_SIZE//4, 6, TILE_SIZE//2))
        else:
            for i in range(0, TILE_SIZE, 10):
                pygame.draw.rect(stripe_surf, (255, 255, 255, 200),
                               (TILE_SIZE//4, i + 2, TILE_SIZE//2, 6))
        
        surface.blit(stripe_surf, (screen_x - TILE_SIZE//2, screen_y - TILE_SIZE//2))
    
    def render_pedestrian(self, surface, pedestrian, camera):
        """Render a single pedestrian."""
        import pygame
        
        screen_x, screen_y = camera.world_to_screen(pedestrian.x, pedestrian.y)
        
        size = int(18 * pedestrian.size)
        
        # Body
        body_surf = pygame.Surface((size, size + 10), pygame.SRCALPHA)
        
        # Shadow
        pygame.draw.ellipse(body_surf, (0, 0, 0, 50), 
                           (size//4, size + 4, size//2, 4))
        
        # Head
        head_color = (235, 200, 165)  # Skin tone
        pygame.draw.circle(body_surf, head_color, (size//2, 5), 4)
        
        # Hair
        hair_color = random.choice([(40, 30, 20), (80, 50, 30), (20, 20, 20)]) if not hasattr(pedestrian, '_hair') else pedestrian._hair
        pedestrian._hair = hair_color
        pygame.draw.arc(body_surf, hair_color, (size//2 - 4, 1, 8, 6), 0, 3.14, 2)
        
        # Body/shirt
        pygame.draw.rect(body_surf, pedestrian.color,
                        (size//4, 8, size//2, 10), border_radius=2)
        
        # Legs (animate walking)
        leg_offset = 2 if pedestrian.walk_frame % 2 == 0 else -2
        pygame.draw.rect(body_surf, (50, 50, 60),
                        (size//4 + leg_offset, 17, 3, 8))
        pygame.draw.rect(body_surf, (50, 50, 60),
                        (size//2 - leg_offset, 17, 3, 8))
        
        surface.blit(body_surf, (screen_x - size//2, screen_y - size//2 - 6))
    
    def render_all(self, surface, pedestrian_manager, camera):
        """Render all crosswalks and pedestrians."""
        # Crosswalks first (under pedestrians)
        for cw in pedestrian_manager.crosswalks:
            self.render_crosswalk(surface, cw, camera)
        
        # Pedestrians
        for ped in pedestrian_manager.pedestrians:
            self.render_pedestrian(surface, ped, camera)
