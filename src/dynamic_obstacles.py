"""
dynamic_obstacles.py - Dynamic obstacle system.

Features:
- Random obstacle spawning during simulation
- Temporary obstacles (road work, accidents)
- Moving obstacles
- Automatic path recalculation trigger
"""

import random
import math
from constants import TILE_SIZE, TILE_ROAD, TILE_OBSTACLE, PASSABLE_TILES


class DynamicObstacle:
    """
    A single dynamic obstacle that can appear/disappear.
    """
    
    def __init__(self, row, col, obstacle_type="roadwork", duration=None):
        """
        Args:
            row, col: Grid position
            obstacle_type: "roadwork", "accident", "construction", "debris"
            duration: Lifetime in seconds (None = permanent until removed)
        """
        self.row = row
        self.col = col
        self.type = obstacle_type
        self.duration = duration
        self.time_alive = 0
        self.active = True
        
        # World position
        self.x = col * TILE_SIZE + TILE_SIZE / 2
        self.y = row * TILE_SIZE + TILE_SIZE / 2
        
        # Visual
        self.flash_timer = 0
        self.flash_state = False
        
        # Type-specific colors
        self.colors = {
            "roadwork": (255, 180, 0),      # Orange
            "accident": (255, 60, 60),       # Red
            "construction": (255, 220, 0),   # Yellow
            "debris": (120, 100, 80),        # Brown
        }
        self.color = self.colors.get(obstacle_type, (255, 180, 0))
    
    @property
    def grid_position(self):
        return (self.row, self.col)
    
    def update(self, dt):
        """Update obstacle state."""
        if not self.active:
            return False
        
        self.time_alive += dt
        
        # Check duration
        if self.duration and self.time_alive >= self.duration:
            self.active = False
            return True  # Changed
        
        # Flash animation (for warning)
        self.flash_timer += dt
        if self.flash_timer >= 0.5:
            self.flash_timer = 0
            self.flash_state = not self.flash_state
        
        return False
    
    def is_expired(self):
        """Check if obstacle should be removed."""
        return not self.active


class DynamicObstacleManager:
    """
    Manages dynamic obstacles in the simulation.
    """
    
    def __init__(self):
        self.obstacles = []
        self.spawn_timer = 0
        self.spawn_interval = 15.0  # Seconds between random spawns
        self.spawn_enabled = True
        self.max_obstacles = 3
        
        # Callback for when obstacles change
        self.on_obstacle_changed = None
    
    def spawn_random(self, grid_data, avoid_positions=None):
        """
        Spawn a random obstacle on a road tile.
        
        Args:
            grid_data: Grid array
            avoid_positions: List of (row, col) to avoid
            
        Returns:
            DynamicObstacle or None
        """
        if len(self.obstacles) >= self.max_obstacles:
            return None
        
        rows = len(grid_data)
        cols = len(grid_data[0]) if rows > 0 else 0
        
        # Find valid road positions
        candidates = []
        for r in range(rows):
            for c in range(cols):
                cell = grid_data[r][c]
                if cell == TILE_ROAD or cell == 0:
                    # Check if not near avoid positions
                    too_close = False
                    if avoid_positions:
                        for pos in avoid_positions:
                            dist = abs(r - pos[0]) + abs(c - pos[1])
                            if dist < 3:
                                too_close = True
                                break
                    
                    # Check if not already occupied
                    for obs in self.obstacles:
                        if obs.row == r and obs.col == c:
                            too_close = True
                            break
                    
                    if not too_close:
                        candidates.append((r, c))
        
        if not candidates:
            return None
        
        # Pick random position
        row, col = random.choice(candidates)
        
        # Random type and duration
        types = ["roadwork", "accident", "construction", "debris"]
        obs_type = random.choice(types)
        duration = random.uniform(10, 30)  # 10-30 seconds
        
        obstacle = DynamicObstacle(row, col, obs_type, duration)
        self.obstacles.append(obstacle)
        
        # Trigger callback
        if self.on_obstacle_changed:
            self.on_obstacle_changed()
        
        return obstacle
    
    def add_obstacle(self, row, col, obstacle_type="roadwork", duration=None):
        """Manually add an obstacle."""
        obstacle = DynamicObstacle(row, col, obstacle_type, duration)
        self.obstacles.append(obstacle)
        
        if self.on_obstacle_changed:
            self.on_obstacle_changed()
        
        return obstacle
    
    def remove_obstacle(self, row, col):
        """Remove obstacle at position."""
        for obs in self.obstacles[:]:
            if obs.row == row and obs.col == col:
                self.obstacles.remove(obs)
                if self.on_obstacle_changed:
                    self.on_obstacle_changed()
                return True
        return False
    
    def update(self, dt, grid_data, player_pos=None):
        """
        Update all obstacles.
        
        Args:
            dt: Delta time
            grid_data: Grid for spawning
            player_pos: (row, col) player position to avoid
        """
        changed = False
        
        # Update existing obstacles
        for obs in self.obstacles[:]:
            if obs.update(dt):
                changed = True
            if obs.is_expired():
                self.obstacles.remove(obs)
                changed = True
        
        # Random spawn
        if self.spawn_enabled:
            self.spawn_timer += dt
            if self.spawn_timer >= self.spawn_interval:
                self.spawn_timer = 0
                avoid = [player_pos] if player_pos else []
                if self.spawn_random(grid_data, avoid):
                    changed = True
        
        if changed and self.on_obstacle_changed:
            self.on_obstacle_changed()
        
        return changed
    
    def get_blocked_positions(self):
        """Get list of (row, col) blocked by dynamic obstacles."""
        return [(obs.row, obs.col) for obs in self.obstacles if obs.active]
    
    def is_blocked(self, row, col):
        """Check if position is blocked by dynamic obstacle."""
        for obs in self.obstacles:
            if obs.active and obs.row == row and obs.col == col:
                return True
        return False
    
    def clear(self):
        """Remove all obstacles."""
        self.obstacles.clear()
        if self.on_obstacle_changed:
            self.on_obstacle_changed()
    
    def toggle_spawning(self):
        """Toggle automatic spawning."""
        self.spawn_enabled = not self.spawn_enabled
        return self.spawn_enabled


class DynamicObstacleRenderer:
    """
    Renders dynamic obstacles with warning effects.
    """
    
    def render(self, surface, obstacle, camera):
        """Render a single dynamic obstacle."""
        import pygame
        
        screen_x, screen_y = camera.world_to_screen(obstacle.x, obstacle.y)
        
        # Glow/warning effect
        glow_size = 50
        glow_surf = pygame.Surface((glow_size, glow_size), pygame.SRCALPHA)
        glow_color = (*obstacle.color, 60 if obstacle.flash_state else 30)
        pygame.draw.circle(glow_surf, glow_color, (glow_size//2, glow_size//2), glow_size//2)
        surface.blit(glow_surf, (screen_x - glow_size//2, screen_y - glow_size//2))
        
        # Obstacle icon based on type
        icon_size = 32
        icon_surf = pygame.Surface((icon_size, icon_size), pygame.SRCALPHA)
        
        if obstacle.type == "roadwork":
            # Construction cone
            pygame.draw.polygon(icon_surf, obstacle.color, 
                              [(16, 4), (6, 28), (26, 28)])
            pygame.draw.polygon(icon_surf, (255, 255, 255),
                              [(14, 10), (10, 20), (22, 20), (18, 10)])
        
        elif obstacle.type == "accident":
            # Warning triangle
            pygame.draw.polygon(icon_surf, obstacle.color,
                              [(16, 2), (2, 30), (30, 30)])
            pygame.draw.polygon(icon_surf, (255, 255, 255),
                              [(16, 8), (8, 26), (24, 26)])
            # Exclamation
            pygame.draw.rect(icon_surf, obstacle.color, (14, 12, 4, 8))
            pygame.draw.rect(icon_surf, obstacle.color, (14, 22, 4, 4))
        
        elif obstacle.type == "construction":
            # Barrier
            pygame.draw.rect(icon_surf, obstacle.color, (4, 10, 24, 12))
            pygame.draw.rect(icon_surf, (255, 255, 255), (4, 14, 8, 4))
            pygame.draw.rect(icon_surf, (255, 255, 255), (20, 14, 8, 4))
        
        else:  # debris
            # Rocks
            pygame.draw.circle(icon_surf, obstacle.color, (10, 20), 8)
            pygame.draw.circle(icon_surf, obstacle.color, (22, 18), 6)
            pygame.draw.circle(icon_surf, obstacle.color, (16, 12), 5)
        
        surface.blit(icon_surf, (screen_x - icon_size//2, screen_y - icon_size//2))
        
        # Duration indicator (if timed)
        if obstacle.duration:
            remaining = max(0, obstacle.duration - obstacle.time_alive)
            if remaining < 5:  # Show when less than 5 seconds
                font = pygame.font.SysFont("Consolas", 12)
                text = font.render(f"{remaining:.0f}s", True, (255, 255, 255))
                surface.blit(text, (screen_x - 10, screen_y + 18))
    
    def render_all(self, surface, obstacles, camera):
        """Render all dynamic obstacles."""
        for obs in obstacles:
            if obs.active:
                self.render(surface, obs, camera)

