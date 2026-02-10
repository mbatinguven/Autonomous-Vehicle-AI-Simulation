"""
ui.py - Modern UI component system.

Features:
- Semi-transparent panels with blur effect
- Animated buttons with hover states
- Status displays
- Minimap
- Sliders and toggles
- Toast notifications
"""

import pygame
import math
from constants import (
    COLORS, UI_PANEL_OPACITY, UI_PANEL_RADIUS,
    UI_FONT_SIZE_TINY, UI_FONT_SIZE_SMALL, UI_FONT_SIZE_MEDIUM, 
    UI_FONT_SIZE_LARGE, UI_FONT_SIZE_TITLE, UI_FONT_FAMILY,
    UI_ANIMATION_SPEED, MINIMAP_SIZE, MINIMAP_MARGIN, MINIMAP_OPACITY,
    TILE_SIZE, TILE_ROAD, TILE_OBSTACLE, TILE_START, TILE_GOAL, TILE_TRAFFIC
)


class FontManager:
    """Manages font loading and caching."""
    
    _fonts = {}
    _initialized = False
    
    @classmethod
    def init(cls):
        """Initialize fonts."""
        if cls._initialized:
            return
        
        sizes = {
            "tiny": UI_FONT_SIZE_TINY,
            "small": UI_FONT_SIZE_SMALL,
            "medium": UI_FONT_SIZE_MEDIUM,
            "large": UI_FONT_SIZE_LARGE,
            "title": UI_FONT_SIZE_TITLE,
        }
        
        for name, size in sizes.items():
            try:
                cls._fonts[name] = pygame.font.SysFont(UI_FONT_FAMILY, size)
                cls._fonts[f"{name}_bold"] = pygame.font.SysFont(UI_FONT_FAMILY, size, bold=True)
            except:
                cls._fonts[name] = pygame.font.Font(None, size)
                cls._fonts[f"{name}_bold"] = pygame.font.Font(None, size)
        
        cls._initialized = True
    
    @classmethod
    def get(cls, name="medium", bold=False):
        """Get a font by name."""
        cls.init()
        key = f"{name}_bold" if bold else name
        return cls._fonts.get(key, cls._fonts.get("medium"))


class Panel:
    """Semi-transparent UI panel with optional border glow."""
    
    def __init__(self, x, y, width, height, opacity=UI_PANEL_OPACITY):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.opacity = opacity
        self.border_color = COLORS["ui_border"]
        self.show_border_glow = False
        self.glow_color = COLORS["ui_border_glow"]
        
        self._surface = None
        self._dirty = True
    
    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def set_position(self, x, y):
        self.x = x
        self.y = y
    
    def set_size(self, width, height):
        self.width = width
        self.height = height
        self._dirty = True
    
    def _render(self):
        """Pre-render the panel."""
        self._surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        # Background
        bg_color = (*COLORS["ui_panel"][:3], self.opacity)
        pygame.draw.rect(self._surface, bg_color, 
                        (0, 0, self.width, self.height), 
                        border_radius=UI_PANEL_RADIUS)
        
        # Border
        pygame.draw.rect(self._surface, self.border_color,
                        (0, 0, self.width, self.height),
                        width=1, border_radius=UI_PANEL_RADIUS)
        
        self._dirty = False
    
    def draw(self, surface):
        """Draw the panel to a surface."""
        if self._dirty or self._surface is None:
            self._render()
        
        # Draw glow if enabled
        if self.show_border_glow:
            glow = pygame.Surface((self.width + 10, self.height + 10), pygame.SRCALPHA)
            pygame.draw.rect(glow, (*self.glow_color[:3], 30),
                           (0, 0, self.width + 10, self.height + 10),
                           border_radius=UI_PANEL_RADIUS + 2)
            surface.blit(glow, (self.x - 5, self.y - 5))
        
        surface.blit(self._surface, (self.x, self.y))


class Button:
    """Animated button with hover and click states."""
    
    def __init__(self, x, y, width, height, text, callback=None):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.callback = callback
        
        # State
        self.hovered = False
        self.pressed = False
        self.disabled = False
        
        # Animation
        self._hover_progress = 0.0
        self._press_progress = 0.0
    
    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def update(self, dt):
        """Update button animations."""
        target_hover = 1.0 if self.hovered else 0.0
        self._hover_progress += (target_hover - self._hover_progress) * UI_ANIMATION_SPEED * dt
        
        target_press = 1.0 if self.pressed else 0.0
        self._press_progress += (target_press - self._press_progress) * UI_ANIMATION_SPEED * 2 * dt
    
    def handle_event(self, event):
        """Handle mouse events."""
        if self.disabled:
            return False
        
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.hovered:
                self.pressed = True
                return True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.pressed:
                self.pressed = False
                if self.hovered and self.callback:
                    self.callback()
                return True
        
        return False
    
    def draw(self, surface):
        """Draw the button."""
        # Calculate colors based on state
        if self.disabled:
            bg_color = COLORS["button_disabled"]
            text_color = COLORS["ui_text_dim"]
        else:
            # Interpolate between normal and hover colors
            bg_color = self._lerp_color(
                COLORS["button_normal"],
                COLORS["button_hover"],
                self._hover_progress
            )
            text_color = COLORS["ui_text"]
        
        # Press effect (shrink slightly)
        press_offset = int(self._press_progress * 2)
        rect = pygame.Rect(
            self.x + press_offset,
            self.y + press_offset,
            self.width - press_offset * 2,
            self.height - press_offset * 2
        )
        
        # Draw button
        pygame.draw.rect(surface, bg_color, rect, border_radius=8)
        pygame.draw.rect(surface, COLORS["ui_border"], rect, width=1, border_radius=8)
        
        # Draw text
        font = FontManager.get("medium", bold=True)
        text_surf = font.render(self.text, True, text_color)
        text_rect = text_surf.get_rect(center=rect.center)
        surface.blit(text_surf, text_rect)
    
    def _lerp_color(self, c1, c2, t):
        """Linearly interpolate between two colors."""
        return tuple(int(c1[i] + (c2[i] - c1[i]) * t) for i in range(3))


class Slider:
    """Horizontal slider for value adjustment."""
    
    def __init__(self, x, y, width, min_val=0, max_val=100, value=50, label=""):
        self.x = x
        self.y = y
        self.width = width
        self.height = 30
        self.min_val = min_val
        self.max_val = max_val
        self.value = value
        self.label = label
        
        self.dragging = False
        self.hovered = False
    
    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    @property
    def normalized(self):
        """Get value as 0-1."""
        return (self.value - self.min_val) / (self.max_val - self.min_val)
    
    def handle_event(self, event):
        """Handle mouse events."""
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
            if self.dragging:
                self._update_value(event.pos[0])
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.hovered:
                self.dragging = True
                self._update_value(event.pos[0])
                return True
        
        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.dragging = False
        
        return False
    
    def _update_value(self, mouse_x):
        """Update value based on mouse position."""
        track_x = self.x + 10
        track_width = self.width - 20
        
        t = (mouse_x - track_x) / track_width
        t = max(0, min(1, t))
        
        self.value = self.min_val + t * (self.max_val - self.min_val)
    
    def draw(self, surface):
        """Draw the slider."""
        # Label
        if self.label:
            font = FontManager.get("small")
            label_surf = font.render(f"{self.label}: {int(self.value)}", True, COLORS["ui_text"])
            surface.blit(label_surf, (self.x, self.y - 18))
        
        # Track
        track_rect = pygame.Rect(self.x + 10, self.y + 12, self.width - 20, 6)
        pygame.draw.rect(surface, COLORS["button_normal"], track_rect, border_radius=3)
        
        # Fill
        fill_width = int((self.width - 20) * self.normalized)
        fill_rect = pygame.Rect(self.x + 10, self.y + 12, fill_width, 6)
        pygame.draw.rect(surface, COLORS["ui_accent"], fill_rect, border_radius=3)
        
        # Handle
        handle_x = self.x + 10 + fill_width
        handle_color = COLORS["ui_text"] if self.hovered or self.dragging else COLORS["ui_text_dim"]
        pygame.draw.circle(surface, handle_color, (handle_x, self.y + 15), 8)


class Toggle:
    """Toggle switch for boolean values."""
    
    def __init__(self, x, y, value=True, label=""):
        self.x = x
        self.y = y
        self.width = 50
        self.height = 26
        self.value = value
        self.label = label
        
        self._progress = 1.0 if value else 0.0
        self.hovered = False
    
    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)
    
    def toggle(self):
        self.value = not self.value
    
    def update(self, dt):
        target = 1.0 if self.value else 0.0
        self._progress += (target - self._progress) * UI_ANIMATION_SPEED * dt
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.hovered:
                self.toggle()
                return True
        
        return False
    
    def draw(self, surface):
        """Draw the toggle."""
        # Label
        if self.label:
            font = FontManager.get("small")
            label_surf = font.render(self.label, True, COLORS["ui_text"])
            surface.blit(label_surf, (self.x + self.width + 10, self.y + 4))
        
        # Track
        track_color = COLORS["ui_accent"] if self.value else COLORS["button_normal"]
        pygame.draw.rect(surface, track_color, self.rect, border_radius=13)
        
        # Knob
        knob_x = self.x + 4 + int((self.width - 26) * self._progress)
        knob_color = COLORS["ui_text"]
        pygame.draw.circle(surface, knob_color, (knob_x + 9, self.y + 13), 9)


class StatusPanel:
    """Game status display panel with controls."""
    
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.panel = Panel(x, y, 260, 320)  # Taller for controls
        
        # Display values
        self.algorithm = "A*"
        self.fps = 60
        self.status = "Moving"
        self.path_length = 0
        self.npc_count = 0
        self.pedestrian_count = 0
    
    def update_stats(self, algorithm, fps, status, path_length, light_timer=0, grid_size=(0,0), 
                     npc_count=0, pedestrian_count=0):
        """Update displayed statistics."""
        self.algorithm = algorithm
        self.fps = fps
        self.status = status
        self.path_length = path_length
        self.npc_count = npc_count
        self.pedestrian_count = pedestrian_count
    
    def draw(self, surface):
        """Draw the status panel with controls."""
        self.panel.draw(surface)
        
        # Get fonts
        font = FontManager.get("small")
        font_tiny = FontManager.get("tiny")
        font_bold = FontManager.get("medium", bold=True)
        
        x = self.x + 14
        y = self.y + 14
        line_height = 22
        
        # Title
        text = font_bold.render("SIMULATION", True, COLORS["ui_accent"])
        surface.blit(text, (x, y))
        y += line_height + 4
        
        # Algorithm
        text = font.render(f"Algorithm: {self.algorithm}", True, COLORS["ui_text"])
        surface.blit(text, (x, y))
        y += line_height
        
        # FPS
        fps_color = COLORS["ui_success"] if self.fps >= 55 else COLORS["ui_warning"]
        text = font.render(f"FPS: {self.fps}", True, fps_color)
        surface.blit(text, (x, y))
        y += line_height
        
        # Status
        status_colors = {
            "Moving": COLORS["status_moving"],
            "Waiting": COLORS["status_waiting"],
            "Arrived": COLORS["status_arrived"],
            "No Path": COLORS["status_no_path"],
        }
        status_color = status_colors.get(self.status, COLORS["ui_text"])
        text = font.render(f"Status: {self.status}", True, status_color)
        surface.blit(text, (x, y))
        y += line_height
        
        # Path & Traffic
        text = font.render(f"Path: {self.path_length} | NPCs: {self.npc_count} | Peds: {self.pedestrian_count}", True, COLORS["ui_text_dim"])
        surface.blit(text, (x, y))
        y += line_height + 8
        
        # Divider
        pygame.draw.line(surface, COLORS["ui_border"], (x, y), (x + 230, y), 1)
        y += 10
        
        # Controls header
        text = font_bold.render("CONTROLS", True, COLORS["ui_accent"])
        surface.blit(text, (x, y))
        y += line_height
        
        # Control list
        controls = [
            ("1/2/3", "BFS / Greedy / A*"),
            ("LMB", "Place/Remove Obstacle"),
            ("RMB", "Set Start"),
            ("MMB", "Set Goal"),
            ("T/O", "Traffic / Obstacle Mode"),
            ("R/N", "Reset / New Map"),
            ("V/D", "Sensor / Dyn.Obstacles"),
            ("M/U", "Minimap / Hide UI"),
            ("SPC", "Recalc Path"),
            ("ESC", "Pause Menu"),
        ]
        
        for key, desc in controls:
            # Key in accent color
            key_text = font_tiny.render(f"[{key}]", True, COLORS["ui_accent"])
            surface.blit(key_text, (x, y))
            
            # Description
            desc_text = font_tiny.render(desc, True, COLORS["ui_text_dim"])
            surface.blit(desc_text, (x + 50, y))
            y += 14


class Minimap:
    """Minimap displaying the city overview."""
    
    def __init__(self, screen_width, screen_height):
        self.size = MINIMAP_SIZE
        self.margin = MINIMAP_MARGIN
        self.opacity = MINIMAP_OPACITY
        
        self.x = screen_width - self.size - self.margin
        self.y = self.margin
        
        self.visible = True
        self._surface = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        
        # Colors for minimap
        self.colors = {
            TILE_ROAD: (60, 65, 75),
            TILE_OBSTACLE: (100, 95, 90),
            TILE_START: COLORS["ui_accent"],
            TILE_GOAL: COLORS["ui_success"],
            TILE_TRAFFIC: COLORS["light_red"],
        }
    
    def reposition(self, screen_width, screen_height):
        """Reposition minimap for new screen size."""
        self.x = screen_width - self.size - self.margin
        self.y = self.margin
    
    def update(self, grid_data, vehicle_pos=None, camera_rect=None):
        """Update minimap display."""
        if not self.visible:
            return
        
        self._surface.fill((0, 0, 0, 0))
        
        rows = len(grid_data)
        cols = len(grid_data[0]) if grid_data else 0
        
        if rows == 0 or cols == 0:
            return
        
        # Calculate cell size
        cell_w = self.size / cols
        cell_h = self.size / rows
        
        # Draw grid
        for r in range(rows):
            for c in range(cols):
                cell = grid_data[r][c]
                color = self.colors.get(cell, self.colors[TILE_ROAD])
                
                rect = pygame.Rect(
                    int(c * cell_w),
                    int(r * cell_h),
                    max(1, int(cell_w)),
                    max(1, int(cell_h))
                )
                pygame.draw.rect(self._surface, color, rect)
        
        # Draw vehicle position
        if vehicle_pos:
            vx = int(vehicle_pos[1] * cell_w + cell_w / 2)
            vy = int(vehicle_pos[0] * cell_h + cell_h / 2)
            pygame.draw.circle(self._surface, COLORS["vehicle_glow"][:3], (vx, vy), 4)
        
        # Draw border
        pygame.draw.rect(self._surface, COLORS["ui_border"], 
                        (0, 0, self.size, self.size), 2, border_radius=4)
    
    def draw(self, surface):
        """Draw minimap to screen."""
        if not self.visible:
            return
        
        # Background
        bg = pygame.Surface((self.size + 8, self.size + 8), pygame.SRCALPHA)
        pygame.draw.rect(bg, (*COLORS["ui_panel"][:3], self.opacity),
                        (0, 0, self.size + 8, self.size + 8), border_radius=6)
        surface.blit(bg, (self.x - 4, self.y - 4))
        
        # Minimap content
        surface.blit(self._surface, (self.x, self.y))
    
    def toggle(self):
        """Toggle minimap visibility."""
        self.visible = not self.visible


class Toast:
    """Temporary notification message."""
    
    def __init__(self, text, duration=2.0, color=None):
        self.text = text
        self.duration = duration
        self.color = color or COLORS["ui_text"]
        self.elapsed = 0
        self.alpha = 0
        self._phase = "in"  # "in", "show", "out"
    
    @property
    def alive(self):
        return self.elapsed < self.duration
    
    def update(self, dt):
        self.elapsed += dt
        
        fade_time = 0.3
        if self.elapsed < fade_time:
            self.alpha = int(255 * (self.elapsed / fade_time))
        elif self.elapsed > self.duration - fade_time:
            remaining = self.duration - self.elapsed
            self.alpha = int(255 * (remaining / fade_time))
        else:
            self.alpha = 255
    
    def draw(self, surface, x, y):
        font = FontManager.get("medium")
        text_surf = font.render(self.text, True, self.color)
        text_surf.set_alpha(self.alpha)
        
        # Background
        padding = 12
        bg_w = text_surf.get_width() + padding * 2
        bg_h = text_surf.get_height() + padding
        
        bg = pygame.Surface((bg_w, bg_h), pygame.SRCALPHA)
        pygame.draw.rect(bg, (*COLORS["ui_panel"][:3], int(200 * self.alpha / 255)),
                        (0, 0, bg_w, bg_h), border_radius=6)
        
        surface.blit(bg, (x - bg_w // 2, y))
        surface.blit(text_surf, (x - text_surf.get_width() // 2, y + padding // 2))


class ToastManager:
    """Manages toast notifications."""
    
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.toasts = []
    
    def show(self, text, duration=2.0, color=None):
        """Show a new toast."""
        toast = Toast(text, duration, color)
        self.toasts.append(toast)
    
    def update(self, dt):
        """Update all toasts."""
        for toast in self.toasts:
            toast.update(dt)
        
        # Remove dead toasts
        self.toasts = [t for t in self.toasts if t.alive]
    
    def draw(self, surface):
        """Draw all toasts."""
        y = self.screen_height - 100
        for toast in self.toasts:
            toast.draw(surface, self.screen_width // 2, y)
            y -= 50


class ControlsHint:
    """Placeholder - no longer used, controls are in StatusPanel."""
    
    def __init__(self, screen_width, screen_height):
        pass
    
    def reposition(self, screen_width, screen_height):
        pass
    
    def draw(self, surface):
        pass  # No longer draws anything

