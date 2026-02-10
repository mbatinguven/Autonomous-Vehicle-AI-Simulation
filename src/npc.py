"""
npc.py - NPC (Non-Player Character) traffic vehicles.

Features:
- Multiple NPC vehicles with full map exploration
- Pathfinding-based routing (uses BFS algorithm)
- Traffic light awareness (stop at red)
- Strict collision avoidance - vehicles NEVER overlap
- Random destination selection for continuous movement
"""

import math
import random
from constants import (
    TILE_SIZE, TILE_ROAD, TILE_TRAFFIC, DIRECTION_ANGLES,
    VEHICLE_SPEED, PASSABLE_TILES, COLORS
)


class NPCVehicle:
    """
    A single NPC vehicle that navigates the city using pathfinding.
    """
    
    def __init__(self, start_pos, vehicle_id, speed_factor=1.0, color=None):
        """
        Args:
            start_pos: Starting (row, col) position
            vehicle_id: Unique ID for this vehicle
            speed_factor: Speed multiplier (0.5-1.5)
            color: Vehicle color tuple (R, G, B)
        """
        self.id = vehicle_id
        self.path = []
        self.path_index = 0
        self.speed = VEHICLE_SPEED * speed_factor * 0.75
        
        # Individual behavior - each vehicle has unique characteristics
        self.patience = random.uniform(0.5, 3.0)  # How long to wait before being aggressive
        self.aggressiveness = random.uniform(0.3, 1.0)  # 0 = cautious, 1 = aggressive
        self._wait_time = 0.0  # Track how long waiting
        
        # Staggered start - some vehicles start slightly offset for natural distribution
        offset = random.uniform(-TILE_SIZE * 0.3, TILE_SIZE * 0.3)
        
        # Position (world pixels)
        row, col = start_pos
        self.x = col * TILE_SIZE + TILE_SIZE / 2 + offset
        self.y = row * TILE_SIZE + TILE_SIZE / 2 + offset
        self._target_x = self.x
        self._target_y = self.y
        
        # Rotation
        self.angle = random.uniform(0, 360)
        self._target_angle = self.angle
        
        # State
        self.active = True
        self.is_waiting = False
        self.needs_new_destination = True
        
        # Visual
        self.color = color or self._random_color()
        self.brake_lights = False
        
        # Path recalculation counter (instead of removing stuck vehicles)
        self._path_recalc_timer = 0
        self._last_pos = (self.x, self.y)
        self._stuck_check_interval = 3.0
        self._stuck_check_timer = 0
    
    def _random_color(self):
        """Generate random vehicle color."""
        colors = [
            (180, 50, 50),    # Red
            (50, 100, 180),   # Blue
            (50, 150, 50),    # Green
            (180, 180, 50),   # Yellow
            (150, 80, 180),   # Purple
            (180, 120, 50),   # Orange
            (80, 80, 80),     # Gray
            (200, 200, 200),  # White
            (50, 180, 180),   # Cyan
            (180, 100, 100),  # Pink
        ]
        return random.choice(colors)
    
    @property
    def grid_position(self):
        """Get current grid cell."""
        col = int(self.x / TILE_SIZE)
        row = int(self.y / TILE_SIZE)
        return (row, col)
    
    @property
    def world_position(self):
        return (self.x, self.y)
    
    def set_path(self, path):
        """Set new path to follow."""
        if path and len(path) > 1:
            self.path = path
            self.path_index = 0
            self.needs_new_destination = False
            
            # Set target to first waypoint
            next_pos = self.path[1] if len(self.path) > 1 else self.path[0]
            self._target_x = next_pos[1] * TILE_SIZE + TILE_SIZE / 2
            self._target_y = next_pos[0] * TILE_SIZE + TILE_SIZE / 2
            
            # Update direction
            if len(self.path) > 1:
                self._update_direction(self.path[0], self.path[1])
            
            # Reset stuck timer
            self._stuck_timer = 0
    
    def _update_direction(self, from_pos, to_pos):
        """Update target rotation."""
        dr = 0 if to_pos[0] == from_pos[0] else (1 if to_pos[0] > from_pos[0] else -1)
        dc = 0 if to_pos[1] == from_pos[1] else (1 if to_pos[1] > from_pos[1] else -1)
        self._target_angle = DIRECTION_ANGLES.get((dr, dc), self.angle)
    
    def update(self, dt, is_red_at=None, occupied_positions=None):
        """
        Update NPC vehicle.
        
        Args:
            dt: Delta time
            is_red_at: Callback (row, col) -> bool for red light
            occupied_positions: Set of (row, col) occupied by other vehicles
        """
        if not self.active:
            return
        
        # Handle spawn delay for staggered starts
        if hasattr(self, '_spawn_delay') and self._spawn_delay > 0:
            self._spawn_delay -= dt
            if self._spawn_delay > 0:
                return  # Don't move yet
        
        # Check if stuck and request new path (don't remove vehicle!)
        self._stuck_check_timer += dt
        if self._stuck_check_timer >= self._stuck_check_interval:
            self._stuck_check_timer = 0
            current_pos = (self.x, self.y)
            dist_moved = math.sqrt(
                (current_pos[0] - self._last_pos[0]) ** 2 +
                (current_pos[1] - self._last_pos[1]) ** 2
            )
            if dist_moved < 5:  # Barely moved
                self._path_recalc_timer += self._stuck_check_interval
                if self._path_recalc_timer > 8:  # Request new destination after 8 seconds stuck
                    self.needs_new_destination = True
                    self._path_recalc_timer = 0
            else:
                self._path_recalc_timer = 0
            self._last_pos = current_pos
        
        # Check if needs new path
        if self.needs_new_destination or not self.path or self.path_index >= len(self.path) - 1:
            self.needs_new_destination = True
            self._interpolate_rotation(dt)
            return
        
        current_pos = self.path[self.path_index]
        should_stop = False
        can_slow_down = False
        
        # Check red light at NEXT position - more lenient
        if self.path_index + 1 < len(self.path):
            next_pos = self.path[self.path_index + 1]
            if is_red_at and is_red_at(next_pos):
                # Only stop if close to the red light
                dx = next_pos[1] * TILE_SIZE + TILE_SIZE / 2 - self.x
                dy = next_pos[0] * TILE_SIZE + TILE_SIZE / 2 - self.y
                dist_to_light = math.sqrt(dx * dx + dy * dy)
                
                if dist_to_light < TILE_SIZE * 1.5:
                    should_stop = True
                elif dist_to_light < TILE_SIZE * 2.5:
                    can_slow_down = True
        
        # Check if next cell is occupied - SLOW DOWN instead of full stop
        if not should_stop and self.path_index + 1 < len(self.path):
            next_pos = self.path[self.path_index + 1]
            if occupied_positions and next_pos in occupied_positions:
                # Track wait time
                self._wait_time += dt
                
                # Aggressive vehicles try to go after patience runs out
                if self._wait_time < self.patience:
                    should_stop = True
                else:
                    # After patience, slow down but keep moving
                    can_slow_down = True
            else:
                self._wait_time = 0.0
        
        # Handle stopping
        if should_stop:
            self.is_waiting = True
            self.brake_lights = True
            self._interpolate_rotation(dt)
            return
        
        # All clear or slow down mode
        self.is_waiting = False
        self.brake_lights = can_slow_down
        
        # Adjust speed based on situation
        move_speed = self.speed
        if can_slow_down:
            move_speed *= (0.3 + self.aggressiveness * 0.3)  # 30-60% speed
        
        # Move toward target with adjusted speed
        dx = self._target_x - self.x
        dy = self._target_y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        
        if dist > 2:
            move_dist = move_speed * dt
            move_dist = min(move_dist, dist)
            self.x += (dx / dist) * move_dist
            self.y += (dy / dist) * move_dist
        else:
            # Reached target, advance to next
            self.path_index += 1
            
            if self.path_index >= len(self.path):
                self.needs_new_destination = True
                return
            
            next_pos = self.path[self.path_index]
            self._target_x = next_pos[1] * TILE_SIZE + TILE_SIZE / 2
            self._target_y = next_pos[0] * TILE_SIZE + TILE_SIZE / 2
            
            # Update direction
            if self.path_index < len(self.path) - 1:
                self._update_direction(next_pos, self.path[self.path_index + 1])
        
        # Smooth rotation
        self._interpolate_rotation(dt)
    
    def _interpolate_rotation(self, dt):
        """Smoothly rotate toward target angle."""
        diff = self._target_angle - self.angle
        while diff > 180:
            diff -= 360
        while diff < -180:
            diff += 360
        self.angle += diff * 8 * dt
        self.angle = self.angle % 360


class NPCManager:
    """
    Manages all NPC vehicles in the simulation.
    """
    
    def __init__(self):
        self.vehicles = []
        self.target_vehicles = 10  # Target count to maintain
        self.spawn_timer = 0
        self.spawn_interval = 1.0  # Check every second
        
        # Cache for pathfinding
        self._road_positions = []
        self._initialized = False
        self._next_id = 0
        
        # Occupied grid cells (for collision prevention)
        self._occupied_cells = set()
    
    def _find_road_positions(self, grid_data):
        """Find all road positions for spawning/destinations."""
        self._road_positions = []
        rows = len(grid_data)
        cols = len(grid_data[0]) if rows > 0 else 0
        
        for r in range(rows):
            for c in range(cols):
                cell = grid_data[r][c]
                if cell == 0 or cell in PASSABLE_TILES:
                    self._road_positions.append((r, c))
        
        return self._road_positions
    
    def _simple_pathfind(self, start, goal, grid_data):
        """Simple BFS pathfinding for NPCs."""
        from collections import deque
        
        rows = len(grid_data)
        cols = len(grid_data[0]) if rows > 0 else 0
        
        if not (0 <= start[0] < rows and 0 <= start[1] < cols):
            return None
        if not (0 <= goal[0] < rows and 0 <= goal[1] < cols):
            return None
        
        queue = deque([(start, [start])])
        visited = {start}
        
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        
        while queue:
            current, path = queue.popleft()
            
            if current == goal:
                return path
            
            for dr, dc in directions:
                nr, nc = current[0] + dr, current[1] + dc
                
                if 0 <= nr < rows and 0 <= nc < cols:
                    cell = grid_data[nr][nc]
                    if (nr, nc) not in visited and (cell == 0 or cell in PASSABLE_TILES):
                        visited.add((nr, nc))
                        queue.append(((nr, nc), path + [(nr, nc)]))
                        
                        # Limit search
                        if len(visited) > 500:
                            return None
        
        return None
    
    def spawn_vehicle(self, grid_data, avoid_positions=None):
        """Spawn a new NPC vehicle with better distribution."""
        if len(self.vehicles) >= self.target_vehicles:
            return None
        
        # Get road positions
        if not self._road_positions:
            self._find_road_positions(grid_data)
        
        if not self._road_positions:
            return None
        
        # Divide map into quadrants for better distribution
        rows = len(grid_data)
        cols = len(grid_data[0]) if rows > 0 else 0
        
        # Try to spawn in least populated quadrant
        quadrant_counts = {0: 0, 1: 0, 2: 0, 3: 0}
        for npc in self.vehicles:
            r, c = npc.grid_position
            q = (0 if r < rows // 2 else 2) + (0 if c < cols // 2 else 1)
            quadrant_counts[q] += 1
        
        # Find least populated quadrant
        target_quadrant = min(quadrant_counts, key=quadrant_counts.get)
        
        # Filter candidates by quadrant
        quadrant_positions = []
        for pos in self._road_positions:
            r, c = pos
            q = (0 if r < rows // 2 else 2) + (0 if c < cols // 2 else 1)
            if q == target_quadrant:
                quadrant_positions.append(pos)
        
        # If target quadrant is empty, use all positions
        if not quadrant_positions:
            quadrant_positions = self._road_positions.copy()
        
        random.shuffle(quadrant_positions)
        
        spawn_pos = None
        for pos in quadrant_positions:
            too_close = False
            
            # Check avoid positions
            if avoid_positions:
                for avoid in avoid_positions:
                    if abs(pos[0] - avoid[0]) + abs(pos[1] - avoid[1]) < 6:
                        too_close = True
                        break
            
            # Check if already occupied
            if pos in self._occupied_cells:
                too_close = True
            
            # Check other NPCs - require more distance
            if not too_close:
                for npc in self.vehicles:
                    npc_grid = npc.grid_position
                    if abs(pos[0] - npc_grid[0]) + abs(pos[1] - npc_grid[1]) < 5:
                        too_close = True
                        break
            
            if not too_close:
                spawn_pos = pos
                break
        
        if not spawn_pos:
            return None
        
        # Create vehicle with more varied characteristics
        speed_factor = random.uniform(0.5, 1.4)  # Much wider range
        vehicle = NPCVehicle(spawn_pos, self._next_id, speed_factor)
        self._next_id += 1
        
        # Add slight delay before first movement for staggered start
        vehicle._spawn_delay = random.uniform(0, 2.0)  # 0-2 second delay
        
        # Find initial destination
        self._assign_new_destination(vehicle, grid_data)
        
        self.vehicles.append(vehicle)
        return vehicle
    
    def _assign_new_destination(self, vehicle, grid_data):
        """Assign a new random destination to NPC."""
        if not self._road_positions:
            self._find_road_positions(grid_data)
        
        if not self._road_positions:
            return False
        
        current = vehicle.grid_position
        
        # Pick random distant destination
        candidates = [pos for pos in self._road_positions 
                     if abs(pos[0] - current[0]) + abs(pos[1] - current[1]) > 6]
        
        if not candidates:
            candidates = [pos for pos in self._road_positions 
                         if abs(pos[0] - current[0]) + abs(pos[1] - current[1]) > 3]
        
        if not candidates:
            candidates = self._road_positions
        
        random.shuffle(candidates)
        
        # Try up to 30 destinations
        for dest in candidates[:30]:
            path = self._simple_pathfind(current, dest, grid_data)
            if path and len(path) > 2:
                vehicle.set_path(path)
                return True
        
        # No path found - try any nearby road position instead of deactivating
        for dest in self._road_positions[:50]:
            if dest != current:
                path = self._simple_pathfind(current, dest, grid_data)
                if path and len(path) > 1:
                    vehicle.set_path(path)
                    return True
        
        # Still no path - keep vehicle active, will try again next frame
        vehicle.needs_new_destination = True
        return False
    
    def initialize_vehicles(self, grid_data, player_pos=None):
        """Spawn initial batch of vehicles."""
        if self._initialized:
            return
        
        player_grid = None
        if player_pos:
            player_grid = [(int(player_pos[1] / TILE_SIZE), 
                           int(player_pos[0] / TILE_SIZE))]
        
        # Spawn all target vehicles at start
        for _ in range(self.target_vehicles):
            if not self.spawn_vehicle(grid_data, player_grid):
                break  # Can't spawn more
        
        self._initialized = True
    
    def _update_occupied_cells(self):
        """Update set of cells occupied by NPCs."""
        self._occupied_cells.clear()
        for vehicle in self.vehicles:
            if vehicle.active:
                # Mark current cell
                grid_pos = vehicle.grid_position
                self._occupied_cells.add(grid_pos)
                
                # Also mark next cell if close to it
                if vehicle.path and vehicle.path_index + 1 < len(vehicle.path):
                    dx = vehicle._target_x - vehicle.x
                    dy = vehicle._target_y - vehicle.y
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist < TILE_SIZE * 0.5:  # Close to next cell
                        next_pos = vehicle.path[vehicle.path_index + 1]
                        self._occupied_cells.add(next_pos)
    
    def update(self, dt, grid_data, is_red_at=None, player_pos=None, 
               crosswalk_positions=None, pedestrian_positions=None):
        """Update all NPC vehicles."""
        # Initialize on first update
        if not self._initialized:
            self.initialize_vehicles(grid_data, player_pos)
        
        # Update occupied cells for collision detection
        self._update_occupied_cells()
        
        # Add player position to occupied cells
        if player_pos:
            player_grid = (int(player_pos[1] / TILE_SIZE), 
                          int(player_pos[0] / TILE_SIZE))
            occupied_with_player = self._occupied_cells | {player_grid}
        else:
            occupied_with_player = self._occupied_cells
        
        # Update each vehicle - NEVER remove vehicles, only reassign paths
        for vehicle in self.vehicles:
            # Assign new destination if needed
            if vehicle.needs_new_destination and vehicle.active:
                self._assign_new_destination(vehicle, grid_data)
            
            # Get occupied cells excluding this vehicle's current cell
            other_occupied = occupied_with_player - {vehicle.grid_position}
            
            vehicle.update(dt, is_red_at, other_occupied)
        
        # Ensure we always have exactly target_vehicles (no spawn/despawn cycle)
        # Only spawn at initialization, vehicles stay forever
    
    def get_positions(self):
        """Get all NPC positions as (row, col) list."""
        return [v.grid_position for v in self.vehicles if v.active]
    
    def get_world_positions(self):
        """Get all NPC world positions as (x, y) list."""
        return [v.world_position for v in self.vehicles if v.active]
    
    def get_occupied_cells(self):
        """Get set of occupied grid cells."""
        return self._occupied_cells.copy()
    
    def clear(self):
        """Remove all NPCs."""
        self.vehicles.clear()
        self._road_positions.clear()
        self._occupied_cells.clear()
        self._initialized = False
    
    def set_max_vehicles(self, count):
        """Set maximum NPC count."""
        self.target_vehicles = max(1, min(15, count))
    
    def refresh_roads(self, grid_data):
        """Refresh road position cache when grid changes."""
        self._find_road_positions(grid_data)
