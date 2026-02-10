"""
algorithms.py - Pathfinding algorithms for the autonomous vehicle simulation.

Provides BFS, Greedy Best-First, and A* algorithms.
All algorithms work with (row, col) integer coordinates.

API:
    compute_path(algo_name: str, grid, start, goal) -> list[tuple[int, int]]
"""

from collections import deque
import heapq
from constants import TILE_ROAD, TILE_START, TILE_GOAL, TILE_TRAFFIC, TILE_OBSTACLE

# Passable tiles for pathfinding
PASSABLE = (TILE_ROAD, TILE_START, TILE_GOAL, TILE_TRAFFIC)


def _is_passable(grid, row, col):
    """Check if cell is passable."""
    if row < 0 or col < 0:
        return False
    if row >= len(grid) or col >= len(grid[0]):
        return False
    return grid[row][col] in PASSABLE


def _manhattan(a, b):
    """Manhattan distance heuristic."""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _reconstruct(came_from, start, goal):
    """Reconstruct path from came_from map."""
    if goal not in came_from:
        return []
    path = []
    current = goal
    while current is not None:
        path.append(current)
        current = came_from.get(current)
    path.reverse()
    return path


DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


def bfs(grid, start, goal):
    """Breadth-First Search - guarantees shortest path."""
    if not start or not goal:
        return []
    
    queue = deque([start])
    came_from = {start: None}
    
    while queue:
        current = queue.popleft()
        if current == goal:
            break
        
        row, col = current
        for dr, dc in DIRECTIONS:
            nr, nc = row + dr, col + dc
            neighbor = (nr, nc)
            if _is_passable(grid, nr, nc) and neighbor not in came_from:
                came_from[neighbor] = current
                queue.append(neighbor)
    
    return _reconstruct(came_from, start, goal)


def greedy(grid, start, goal, max_steps=2000):
    """
    Greedy Best-First with backtracking support.
    Falls back to BFS if greedy gets stuck.
    """
    if not start or not goal:
        return []
    
    current = start
    path = [current]
    visited = {current}
    stuck_count = 0
    
    for _ in range(max_steps):
        if current == goal:
            return path  # Success!
        
        row, col = current
        
        # Collect all valid neighbors sorted by heuristic
        neighbors = []
        for dr, dc in DIRECTIONS:
            nr, nc = row + dr, col + dc
            neighbor = (nr, nc)
            if _is_passable(grid, nr, nc) and neighbor not in visited:
                h = _manhattan(neighbor, goal)
                neighbors.append((h, neighbor))
        
        if neighbors:
            # Sort by heuristic and pick best
            neighbors.sort(key=lambda x: x[0])
            best = neighbors[0][1]
            current = best
            path.append(current)
            visited.add(current)
            stuck_count = 0
        else:
            # Dead end - backtrack
            stuck_count += 1
            if stuck_count > 50 or len(path) <= 1:
                # Too many backtracks, use BFS instead
                return bfs(grid, start, goal)
            
            # Backtrack: remove last position and try again
            if len(path) > 1:
                path.pop()
                current = path[-1]
    
    # If greedy didn't reach goal, fall back to BFS
    if current != goal:
        return bfs(grid, start, goal)
    
    return path


def astar(grid, start, goal):
    """A* Search - optimal pathfinding."""
    if not start or not goal:
        return []
    
    open_set = [(0, start)]
    came_from = {start: None}
    g_score = {start: 0}
    
    while open_set:
        _, current = heapq.heappop(open_set)
        
        if current == goal:
            break
        
        row, col = current
        for dr, dc in DIRECTIONS:
            nr, nc = row + dr, col + dc
            neighbor = (nr, nc)
            
            if not _is_passable(grid, nr, nc):
                continue
            
            cell = grid[nr][nc]

            if cell == TILE_TRAFFIC:
                step_cost = 2
            else:
                step_cost = 1

            tentative_g = g_score[current] + step_cost
            
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                g_score[neighbor] = tentative_g
                f = tentative_g + _manhattan(neighbor, goal)
                heapq.heappush(open_set, (f, neighbor))
                came_from[neighbor] = current
    
    return _reconstruct(came_from, start, goal)


def compute_path(algo_name, grid, start, goal):
    """
    Main API for path computation.
    
    Args:
        algo_name: "BFS", "Greedy", or "A*"
        grid: 2D list with tile values
        start: (row, col) tuple or None
        goal: (row, col) tuple or None
    
    Returns:
        List of (row, col) tuples or empty list
    """
    if start is None or goal is None:
        return []
    
    if algo_name == "BFS":
        return bfs(grid, start, goal)
    elif algo_name == "Greedy":
        return greedy(grid, start, goal)
    elif algo_name == "A*":
        return astar(grid, start, goal)
    else:
        return []
