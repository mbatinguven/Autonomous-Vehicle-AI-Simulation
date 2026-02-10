"""
sensor.py - Vehicle sensor simulation system.

Simulates front-facing sensors for obstacle detection:
- Proximity sensor (detects objects ahead)
- Range finder (measures distance)
- Cone-based detection area
"""

import math
from constants import TILE_SIZE, TILE_OBSTACLE, TILE_ROAD, PASSABLE_TILES


class Sensor:
    """
    Simulated vehicle sensor for obstacle detection.
    
    Provides:
    - Forward distance to nearest obstacle
    - Detection of NPCs and pedestrians
    - Cone-based field of view
    """
    
    def __init__(self, range_distance=3, fov_angle=60):
        """
        Args:
            range_distance: Detection range in tiles
            fov_angle: Field of view in degrees
        """
        self.range = range_distance
        self.fov = fov_angle  # Degrees
        
        # Sensor readings
        self.front_distance = float('inf')  # Distance to nearest obstacle (tiles)
        self.front_clear = True
        self.left_clear = True
        self.right_clear = True
        
        # Detected objects
        self.detected_obstacles = []  # List of (row, col, distance, type)
        self.detected_npcs = []       # List of (x, y, distance)
        self.detected_pedestrians = []
        
        # Raw readings for visualization
        self.ray_hits = []  # List of (start_x, start_y, end_x, end_y, hit)
    
    def scan(self, vehicle_x, vehicle_y, vehicle_angle, grid_data, 
             npc_positions=None, pedestrian_positions=None):
        """
        Perform sensor scan from vehicle position.
        
        Args:
            vehicle_x, vehicle_y: Vehicle world position
            vehicle_angle: Vehicle heading in degrees
            grid_data: 2D grid array
            npc_positions: List of (x, y) NPC world positions
            pedestrian_positions: List of (x, y) pedestrian positions
            
        Returns:
            dict with sensor readings
        """
        self.detected_obstacles = []
        self.detected_npcs = []
        self.detected_pedestrians = []
        self.ray_hits = []
        
        self.front_distance = float('inf')
        self.front_clear = True
        self.left_clear = True
        self.right_clear = True
        
        # Cast multiple rays
        num_rays = 5
        half_fov = self.fov / 2
        
        for i in range(num_rays):
            # Calculate ray angle
            t = i / (num_rays - 1) if num_rays > 1 else 0.5
            ray_angle = vehicle_angle - half_fov + (t * self.fov)
            
            # Cast ray
            hit, distance, hit_type, hit_pos = self._cast_ray(
                vehicle_x, vehicle_y, ray_angle, 
                grid_data, npc_positions, pedestrian_positions
            )
            
            # Store ray for visualization
            rad = math.radians(ray_angle)
            end_x = vehicle_x + math.sin(rad) * (distance * TILE_SIZE)
            end_y = vehicle_y - math.cos(rad) * (distance * TILE_SIZE)
            self.ray_hits.append((vehicle_x, vehicle_y, end_x, end_y, hit))
            
            # Update readings based on ray position
            if i == num_rays // 2:  # Center ray
                self.front_distance = distance
                self.front_clear = not hit or distance > 1.5
            elif i < num_rays // 2:  # Left rays
                if hit and distance < 1.5:
                    self.left_clear = False
            else:  # Right rays
                if hit and distance < 1.5:
                    self.right_clear = False
            
            # Record detection
            if hit:
                if hit_type == "obstacle":
                    self.detected_obstacles.append((*hit_pos, distance, hit_type))
                elif hit_type == "npc":
                    self.detected_npcs.append((*hit_pos, distance))
                elif hit_type == "pedestrian":
                    self.detected_pedestrians.append((*hit_pos, distance))
        
        return self.get_readings()
    
    def _cast_ray(self, start_x, start_y, angle, grid_data, 
                  npc_positions=None, pedestrian_positions=None):
        """
        Cast a single ray and find first hit.
        
        Returns:
            (hit, distance, type, position)
        """
        rad = math.radians(angle)
        dx = math.sin(rad)
        dy = -math.cos(rad)
        
        rows = len(grid_data)
        cols = len(grid_data[0]) if rows > 0 else 0
        
        # Step along ray
        step_size = TILE_SIZE / 4  # Sub-tile precision
        max_steps = int(self.range * TILE_SIZE / step_size)
        
        for step in range(1, max_steps + 1):
            check_x = start_x + dx * step * step_size
            check_y = start_y + dy * step * step_size
            
            distance_tiles = (step * step_size) / TILE_SIZE
            
            # Check NPC collision first (dynamic)
            if npc_positions:
                for npc_pos in npc_positions:
                    npc_x, npc_y = npc_pos
                    dist_to_npc = math.sqrt(
                        (check_x - npc_x) ** 2 + (check_y - npc_y) ** 2
                    )
                    if dist_to_npc < TILE_SIZE * 0.6:
                        return (True, distance_tiles, "npc", (npc_x, npc_y))
            
            # Check pedestrian collision
            if pedestrian_positions:
                for ped_pos in pedestrian_positions:
                    ped_x, ped_y = ped_pos
                    dist_to_ped = math.sqrt(
                        (check_x - ped_x) ** 2 + (check_y - ped_y) ** 2
                    )
                    if dist_to_ped < TILE_SIZE * 0.4:
                        return (True, distance_tiles, "pedestrian", (ped_x, ped_y))
            
            # Check grid obstacle
            grid_col = int(check_x / TILE_SIZE)
            grid_row = int(check_y / TILE_SIZE)
            
            if 0 <= grid_row < rows and 0 <= grid_col < cols:
                cell = grid_data[grid_row][grid_col]
                if cell == TILE_OBSTACLE or cell == 1:
                    return (True, distance_tiles, "obstacle", (grid_row, grid_col))
            else:
                # Out of bounds = obstacle
                return (True, distance_tiles, "boundary", (grid_row, grid_col))
        
        # No hit within range
        return (False, self.range, None, None)
    
    def get_readings(self):
        """Get all sensor readings as dict."""
        return {
            "front_distance": self.front_distance,
            "front_clear": self.front_clear,
            "left_clear": self.left_clear,
            "right_clear": self.right_clear,
            "obstacles": len(self.detected_obstacles),
            "npcs": len(self.detected_npcs),
            "pedestrians": len(self.detected_pedestrians),
            "danger_level": self._calculate_danger_level(),
        }
    
    def _calculate_danger_level(self):
        """
        Calculate danger level 0-1 based on detections.
        """
        danger = 0.0
        
        # Close obstacles increase danger
        if self.front_distance < 1:
            danger += 0.8
        elif self.front_distance < 2:
            danger += 0.4
        elif self.front_distance < 3:
            danger += 0.2
        
        # NPCs and pedestrians
        if self.detected_npcs:
            min_dist = min(d[2] for d in self.detected_npcs)
            if min_dist < 1.5:
                danger += 0.5
        
        if self.detected_pedestrians:
            min_dist = min(d[2] for d in self.detected_pedestrians)
            if min_dist < 2:
                danger += 0.7  # Pedestrians are high priority
        
        return min(1.0, danger)
    
    def should_brake(self):
        """Determine if vehicle should brake based on sensor data."""
        # Brake if obstacle too close
        if self.front_distance < 1.5:
            return True
        
        # Brake for close NPCs
        if self.detected_npcs:
            for npc in self.detected_npcs:
                if npc[2] < 2:
                    return True
        
        # Always brake for pedestrians
        if self.detected_pedestrians:
            for ped in self.detected_pedestrians:
                if ped[2] < 2.5:
                    return True
        
        return False
    
    def should_stop(self):
        """Determine if vehicle should stop completely."""
        if self.front_distance < 0.8:
            return True
        
        if self.detected_pedestrians:
            for ped in self.detected_pedestrians:
                if ped[2] < 1.5:
                    return True
        
        return False


class SensorVisualizer:
    """
    Renders sensor rays and detection zones for debugging/visualization.
    """
    
    def __init__(self):
        self.visible = True
        self.show_rays = True
        self.show_zones = True
    
    def render(self, surface, sensor, camera):
        """
        Render sensor visualization.
        
        Args:
            surface: Target pygame surface
            sensor: Sensor instance with ray_hits
            camera: Camera for coordinate transform
        """
        import pygame
        
        if not self.visible:
            return
        
        # Draw detection cone
        if self.show_zones and sensor.ray_hits:
            # Create semi-transparent cone
            first_ray = sensor.ray_hits[0]
            last_ray = sensor.ray_hits[-1]
            
            start_screen = camera.world_to_screen(first_ray[0], first_ray[1])
            
            # Cone points
            points = [start_screen]
            for ray in sensor.ray_hits:
                end_screen = camera.world_to_screen(ray[2], ray[3])
                points.append(end_screen)
            
            if len(points) >= 3:
                cone_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
                pygame.draw.polygon(cone_surf, (100, 200, 255, 30), points)
                surface.blit(cone_surf, (0, 0))
        
        # Draw rays
        if self.show_rays:
            for ray in sensor.ray_hits:
                start_x, start_y, end_x, end_y, hit = ray
                
                start_screen = camera.world_to_screen(start_x, start_y)
                end_screen = camera.world_to_screen(end_x, end_y)
                
                # Color based on hit
                if hit:
                    color = (255, 80, 80, 180)  # Red for hit
                else:
                    color = (80, 255, 80, 100)  # Green for clear
                
                import pygame
                ray_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
                pygame.draw.line(ray_surf, color, start_screen, end_screen, 2)
                surface.blit(ray_surf, (0, 0))
                
                # Hit marker
                if hit:
                    pygame.draw.circle(surface, (255, 50, 50), 
                                      (int(end_screen[0]), int(end_screen[1])), 5)

