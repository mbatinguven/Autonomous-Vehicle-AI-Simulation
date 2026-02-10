"""
grid.py - Grid/map data structure for Mini City Simulation.

Handles:
- 2D grid storage and manipulation
- Cell queries (is_passable, find_start, find_goal)
- Map loading, saving, and random generation
"""

import random
import json
import os

from constants import (
    TILE_ROAD, TILE_OBSTACLE, TILE_START, TILE_GOAL, TILE_TRAFFIC,
    PASSABLE_TILES, DEFAULT_CITY_MAP, GRID_ROWS, GRID_COLS,
)


class Grid:
    """
    Manages the city grid map.
    
    Tile values:
    - 0: Road (passable)
    - 1: Building/obstacle (blocked)
    - "S": Start position
    - "G": Goal position
    - "T": Traffic light (passable)
    """
    
    def __init__(self):
        """Initialize grid with default map."""
        self.data = None
        self.rows = 0
        self.cols = 0
        self.reset()
    
    def reset(self):
        """Reset to default city map."""
        self.data = [row[:] for row in DEFAULT_CITY_MAP]
        self.rows = len(self.data)
        self.cols = len(self.data[0]) if self.data else 0
    
    def clear(self, fill=TILE_ROAD):
        """Clear grid with single value."""
        self.data = [[fill for _ in range(self.cols)] for _ in range(self.rows)]
    
    def is_valid(self, row, col):
        """Check if coordinates are within bounds."""
        return 0 <= row < self.rows and 0 <= col < self.cols
    
    def get_cell(self, row, col):
        """Get cell value, None if out of bounds."""
        if not self.is_valid(row, col):
            return None
        return self.data[row][col]
    
    def set_cell(self, row, col, value):
        """Set cell value."""
        if self.is_valid(row, col):
            self.data[row][col] = value
            return True
        return False
    
    def is_passable(self, row, col):
        """Check if cell is passable for pathfinding."""
        if not self.is_valid(row, col):
            return False
        return self.data[row][col] in PASSABLE_TILES
    
    # Alias for algorithm compatibility
    def is_free(self, row, col):
        return self.is_passable(row, col)
    
    def find_start(self):
        """Find start position (row, col) or None."""
        for r in range(self.rows):
            for c in range(self.cols):
                if self.data[r][c] == TILE_START:
                    return (r, c)
        return None
    
    def find_goal(self):
        """Find goal position (row, col) or None."""
        for r in range(self.rows):
            for c in range(self.cols):
                if self.data[r][c] == TILE_GOAL:
                    return (r, c)
        return None
    
    def find_traffic_lights(self):
        """Find all traffic light positions."""
        positions = []
        for r in range(self.rows):
            for c in range(self.cols):
                if self.data[r][c] == TILE_TRAFFIC:
                    positions.append((r, c))
        return positions
    
    def toggle_obstacle(self, row, col):
        """Toggle between road and obstacle."""
        if not self.is_valid(row, col):
            return False
        cell = self.data[row][col]
        if cell == TILE_ROAD:
            self.data[row][col] = TILE_OBSTACLE
            return True
        elif cell == TILE_OBSTACLE:
            self.data[row][col] = TILE_ROAD
            return True
        return False
    
    def toggle_traffic_light(self, row, col):
        """Toggle traffic light at position."""
        if not self.is_valid(row, col):
            return False
        cell = self.data[row][col]
        if cell == TILE_TRAFFIC:
            self.data[row][col] = TILE_ROAD
            return True
        elif cell == TILE_ROAD:
            self.data[row][col] = TILE_TRAFFIC
            return True
        return False
    
    def _clear_type(self, tile_type):
        """Remove all cells of a type."""
        for r in range(self.rows):
            for c in range(self.cols):
                if self.data[r][c] == tile_type:
                    self.data[r][c] = TILE_ROAD
    
    def set_start(self, row, col):
        """Set start position, removing existing."""
        if not self.is_valid(row, col):
            return False
        if self.data[row][col] == TILE_OBSTACLE:
            return False
        self._clear_type(TILE_START)
        self.data[row][col] = TILE_START
        return True
    
    def set_goal(self, row, col):
        """Set goal position, removing existing."""
        if not self.is_valid(row, col):
            return False
        if self.data[row][col] == TILE_OBSTACLE:
            return False
        self._clear_type(TILE_GOAL)
        self.data[row][col] = TILE_GOAL
        return True
    
    def generate_random(self, seed=None):
        """Generate a random city-like map."""
        if seed is not None:
            random.seed(seed)
        
        self.clear(TILE_OBSTACLE)
        
        # Create road network
        spacing = 3
        
        # Horizontal roads
        for r in range(0, self.rows, spacing):
            for c in range(self.cols):
                self.data[r][c] = TILE_ROAD
        
        # Vertical roads
        for c in range(0, self.cols, spacing):
            for r in range(self.rows):
                self.data[r][c] = TILE_ROAD
        
        # Random connections
        for _ in range(int(self.rows * self.cols * 0.08)):
            r = random.randint(0, self.rows - 1)
            c = random.randint(0, self.cols - 1)
            self.data[r][c] = TILE_ROAD
        
        # Place start and goal
        road_cells = [(r, c) for r in range(self.rows) for c in range(self.cols)
                     if self.data[r][c] == TILE_ROAD]
        
        if len(road_cells) >= 2:
            start = random.choice(road_cells)
            self.data[start[0]][start[1]] = TILE_START
            road_cells.remove(start)
            
            # Goal far from start
            goal = max(road_cells, key=lambda c: abs(c[0]-start[0]) + abs(c[1]-start[1]))
            self.data[goal[0]][goal[1]] = TILE_GOAL
            road_cells.remove(goal)
            
            # Traffic lights
            if road_cells:
                for _ in range(min(3, len(road_cells))):
                    tl = random.choice(road_cells)
                    self.data[tl[0]][tl[1]] = TILE_TRAFFIC
                    road_cells.remove(tl)
    
    def get_data(self):
        """Get grid data for algorithms."""
        return self.data
    
    def copy_data(self):
        """Get a deep copy of grid data."""
        return [row[:] for row in self.data]
