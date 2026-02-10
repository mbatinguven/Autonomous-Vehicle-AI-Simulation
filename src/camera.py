"""
camera.py - Smooth camera system with zoom and follow.

Features:
- Smooth lerp following of target
- Mouse wheel zoom with limits
- Screen shake effects
- Parallax support
- World-to-screen coordinate transforms
"""

import pygame
import math
import random
from constants import (
    CAMERA_LERP_SPEED, CAMERA_ZOOM_MIN, CAMERA_ZOOM_MAX, 
    CAMERA_ZOOM_SPEED, TILE_SIZE
)


class Camera:
    """
    Camera system for smooth scrolling and zoom.
    
    The camera tracks a position in world space and provides
    transforms to convert world coordinates to screen space.
    """
    
    def __init__(self, screen_width, screen_height):
        # Screen dimensions
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # World position (center of view)
        self.x = 0.0
        self.y = 0.0
        
        # Target position for smooth follow
        self.target_x = 0.0
        self.target_y = 0.0
        
        # Zoom
        self.zoom = 1.0
        self.target_zoom = 1.0
        
        # Smooth follow settings
        self.lerp_speed = CAMERA_LERP_SPEED
        self.zoom_lerp_speed = 6.0
        
        # World bounds (optional limits)
        self.bounds = None  # (min_x, min_y, max_x, max_y)
        
        # Screen shake
        self._shake_intensity = 0
        self._shake_duration = 0
        self._shake_offset = (0, 0)
        
        # Parallax layers
        self._parallax_layers = []
    
    @property
    def offset_x(self):
        """Get the X offset for rendering (includes shake)."""
        return -self.x + self.screen_width / 2 + self._shake_offset[0]
    
    @property
    def offset_y(self):
        """Get the Y offset for rendering (includes shake)."""
        return -self.y + self.screen_height / 2 + self._shake_offset[1]
    
    @property
    def view_rect(self):
        """Get the visible world rectangle."""
        half_w = (self.screen_width / 2) / self.zoom
        half_h = (self.screen_height / 2) / self.zoom
        return pygame.Rect(
            self.x - half_w,
            self.y - half_h,
            half_w * 2,
            half_h * 2
        )
    
    def resize(self, width, height):
        """Handle screen resize."""
        self.screen_width = width
        self.screen_height = height
    
    def set_position(self, x, y, immediate=False):
        """
        Set camera position.
        
        Args:
            x, y: World coordinates
            immediate: If True, snap immediately without lerping
        """
        self.target_x = x
        self.target_y = y
        if immediate:
            self.x = x
            self.y = y
    
    def set_zoom(self, zoom, immediate=False):
        """
        Set zoom level.
        
        Args:
            zoom: Zoom multiplier (1.0 = normal)
            immediate: If True, snap immediately
        """
        self.target_zoom = max(CAMERA_ZOOM_MIN, min(CAMERA_ZOOM_MAX, zoom))
        if immediate:
            self.zoom = self.target_zoom
    
    def zoom_by(self, delta):
        """Adjust zoom by delta amount."""
        self.set_zoom(self.target_zoom + delta * CAMERA_ZOOM_SPEED)
    
    def set_bounds(self, min_x, min_y, max_x, max_y):
        """Set world bounds to constrain camera."""
        self.bounds = (min_x, min_y, max_x, max_y)
    
    def clear_bounds(self):
        """Remove camera bounds."""
        self.bounds = None
    
    def center_on_grid(self, grid_cols, grid_rows, immediate=True):
        """Center camera on a grid."""
        center_x = (grid_cols * TILE_SIZE) / 2
        center_y = (grid_rows * TILE_SIZE) / 2
        self.set_position(center_x, center_y, immediate)
    
    def follow(self, target_x, target_y):
        """Set target for smooth following."""
        self.target_x = target_x
        self.target_y = target_y
    
    def shake(self, intensity=10, duration=0.3):
        """
        Trigger screen shake effect.
        
        Args:
            intensity: Maximum shake offset in pixels
            duration: How long shake lasts in seconds
        """
        self._shake_intensity = intensity
        self._shake_duration = duration
    
    def update(self, dt):
        """Update camera position and effects."""
        # Smooth position interpolation
        self.x += (self.target_x - self.x) * self.lerp_speed * dt
        self.y += (self.target_y - self.y) * self.lerp_speed * dt
        
        # Smooth zoom interpolation
        self.zoom += (self.target_zoom - self.zoom) * self.zoom_lerp_speed * dt
        
        # Apply bounds
        if self.bounds:
            min_x, min_y, max_x, max_y = self.bounds
            half_w = (self.screen_width / 2) / self.zoom
            half_h = (self.screen_height / 2) / self.zoom
            
            self.x = max(min_x + half_w, min(max_x - half_w, self.x))
            self.y = max(min_y + half_h, min(max_y - half_h, self.y))
        
        # Update screen shake
        if self._shake_duration > 0:
            self._shake_duration -= dt
            shake_t = self._shake_duration / 0.3  # Normalize
            current_intensity = self._shake_intensity * shake_t
            self._shake_offset = (
                random.uniform(-current_intensity, current_intensity),
                random.uniform(-current_intensity, current_intensity)
            )
        else:
            self._shake_offset = (0, 0)
    
    def world_to_screen(self, world_x, world_y):
        """
        Convert world coordinates to screen coordinates.
        
        Args:
            world_x, world_y: Position in world space
            
        Returns:
            (screen_x, screen_y) tuple
        """
        # Apply zoom and offset
        screen_x = (world_x - self.x) * self.zoom + self.screen_width / 2
        screen_y = (world_y - self.y) * self.zoom + self.screen_height / 2
        
        # Apply shake
        screen_x += self._shake_offset[0]
        screen_y += self._shake_offset[1]
        
        return (screen_x, screen_y)
    
    def screen_to_world(self, screen_x, screen_y):
        """
        Convert screen coordinates to world coordinates.
        
        Args:
            screen_x, screen_y: Position on screen
            
        Returns:
            (world_x, world_y) tuple
        """
        world_x = (screen_x - self.screen_width / 2) / self.zoom + self.x
        world_y = (screen_y - self.screen_height / 2) / self.zoom + self.y
        return (world_x, world_y)
    
    def screen_to_grid(self, screen_x, screen_y, grid_rows, grid_cols):
        """
        Convert screen coordinates to grid cell.
        
        Returns:
            (row, col) tuple or None if outside grid
        """
        world_x, world_y = self.screen_to_world(screen_x, screen_y)
        
        col = int(world_x / TILE_SIZE)
        row = int(world_y / TILE_SIZE)
        
        if 0 <= row < grid_rows and 0 <= col < grid_cols:
            return (row, col)
        return None
    
    def grid_to_screen(self, row, col):
        """Convert grid cell to screen coordinates (center of cell)."""
        world_x = col * TILE_SIZE + TILE_SIZE / 2
        world_y = row * TILE_SIZE + TILE_SIZE / 2
        return self.world_to_screen(world_x, world_y)
    
    def is_visible(self, world_x, world_y, margin=50):
        """Check if a world position is visible on screen."""
        screen_x, screen_y = self.world_to_screen(world_x, world_y)
        return (
            -margin <= screen_x <= self.screen_width + margin and
            -margin <= screen_y <= self.screen_height + margin
        )
    
    def is_rect_visible(self, rect):
        """Check if a world rectangle is at least partially visible."""
        view = self.view_rect
        return view.colliderect(rect)
    
    def get_parallax_offset(self, depth):
        """
        Get offset for parallax layer.
        
        Args:
            depth: 0 = no parallax, 1 = maximum parallax
            
        Returns:
            (offset_x, offset_y) tuple
        """
        parallax_x = self.x * depth * 0.5
        parallax_y = self.y * depth * 0.5
        return (parallax_x, parallax_y)
    
    def get_render_offset(self):
        """Get the current render offset as integers."""
        return (int(self.offset_x), int(self.offset_y))
    
    def get_scaled_tile_size(self):
        """Get tile size adjusted for current zoom."""
        return int(TILE_SIZE * self.zoom)


class CameraController:
    """
    High-level camera controller with multiple modes.
    """
    
    MODE_FREE = "free"
    MODE_FOLLOW = "follow"
    MODE_FIXED = "fixed"
    
    def __init__(self, camera):
        self.camera = camera
        self.mode = self.MODE_FOLLOW
        self.follow_target = None
        
        # Edge scrolling
        self.edge_scroll_enabled = False
        self.edge_scroll_speed = 500
        self.edge_margin = 50
    
    def set_mode(self, mode):
        """Set camera control mode."""
        self.mode = mode
    
    def set_follow_target(self, target):
        """
        Set the object to follow.
        
        Target should have x, y attributes.
        """
        self.follow_target = target
        self.mode = self.MODE_FOLLOW
    
    def update(self, dt, mouse_pos=None):
        """Update camera based on mode."""
        if self.mode == self.MODE_FOLLOW and self.follow_target:
            # Follow target with lead
            target_x = self.follow_target.x
            target_y = self.follow_target.y
            self.camera.follow(target_x, target_y)
        
        elif self.mode == self.MODE_FREE and self.edge_scroll_enabled and mouse_pos:
            # Edge scrolling
            mx, my = mouse_pos
            dx, dy = 0, 0
            
            if mx < self.edge_margin:
                dx = -self.edge_scroll_speed * dt
            elif mx > self.camera.screen_width - self.edge_margin:
                dx = self.edge_scroll_speed * dt
            
            if my < self.edge_margin:
                dy = -self.edge_scroll_speed * dt
            elif my > self.camera.screen_height - self.edge_margin:
                dy = self.edge_scroll_speed * dt
            
            if dx or dy:
                self.camera.set_position(
                    self.camera.target_x + dx,
                    self.camera.target_y + dy
                )
        
        self.camera.update(dt)
    
    def handle_scroll(self, delta):
        """Handle mouse wheel for zoom."""
        self.camera.zoom_by(delta)

