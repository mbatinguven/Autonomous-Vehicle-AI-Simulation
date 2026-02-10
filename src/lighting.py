"""
lighting.py - Dynamic lighting and shadow system.

Features:
- Global ambient lighting
- Vehicle headlight cone
- Traffic light glow
- Tile shadows with directional offset
- Ambient occlusion simulation
- Normal-map style shading effect
"""

import pygame
import math
from constants import (
    AMBIENT_LIGHT_LEVEL, VEHICLE_LIGHT_RADIUS, VEHICLE_LIGHT_INTENSITY,
    SHADOW_OFFSET_X, SHADOW_OFFSET_Y, SHADOW_OPACITY, AO_STRENGTH,
    TILE_SIZE, COLORS
)


class LightSource:
    """Base class for light sources."""
    
    def __init__(self, x=0, y=0, radius=100, color=(255, 255, 255), intensity=1.0):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.intensity = intensity
        self.active = True
        self._cached_surface = None
        self._last_radius = 0
    
    def set_position(self, x, y):
        self.x = x
        self.y = y
    
    def get_surface(self):
        """Get the pre-rendered light surface."""
        if self._cached_surface is None or self._last_radius != self.radius:
            self._create_surface()
            self._last_radius = self.radius
        return self._cached_surface
    
    def _create_surface(self):
        """Create the light gradient surface."""
        diameter = int(self.radius * 2)
        self._cached_surface = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        
        # Draw radial gradient
        center = self.radius
        for r in range(int(self.radius), 0, -1):
            # Calculate falloff (quadratic for smooth light)
            t = r / self.radius
            alpha = int((1 - t * t) * 255 * self.intensity)
            
            color = (*self.color[:3], alpha)
            pygame.draw.circle(self._cached_surface, color, (center, center), r)


class VehicleLight(LightSource):
    """Headlight/flashlight effect for vehicle."""
    
    def __init__(self):
        super().__init__(
            radius=VEHICLE_LIGHT_RADIUS,
            color=COLORS["vehicle_headlight"],
            intensity=VEHICLE_LIGHT_INTENSITY
        )
        self.direction = 0  # Degrees, 0 = up
        self.cone_angle = 60  # Degrees of cone spread
        self.brake_active = False
        self._cone_surface = None
    
    def set_direction(self, angle):
        """Set light direction."""
        self.direction = angle
        self._cone_surface = None  # Invalidate cache
    
    def get_cone_surface(self):
        """Get the directional cone light surface."""
        if self._cone_surface is None:
            self._create_cone_surface()
        return self._cone_surface
    
    def _create_cone_surface(self):
        """Create a cone-shaped light."""
        diameter = int(self.radius * 2)
        self._cone_surface = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        
        center = self.radius
        
        # Draw cone using polygon mask
        angle_rad = math.radians(self.direction)
        half_cone = math.radians(self.cone_angle / 2)
        
        # Cone points
        points = [(center, center)]
        steps = 20
        for i in range(steps + 1):
            a = angle_rad - half_cone + (half_cone * 2 * i / steps)
            # Flip because pygame Y is down
            px = center + math.sin(a) * self.radius
            py = center - math.cos(a) * self.radius
            points.append((px, py))
        
        # Draw base gradient circle
        for r in range(int(self.radius), 0, -2):
            t = r / self.radius
            alpha = int((1 - t * t) * 200 * self.intensity)
            color = (*self.color[:3], alpha)
            pygame.draw.circle(self._cone_surface, color, (center, center), r)
        
        # Create mask surface
        mask = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
        pygame.draw.polygon(mask, (255, 255, 255, 255), points)
        
        # Apply mask
        self._cone_surface.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)


class TrafficLightGlow(LightSource):
    """Glow effect for traffic lights."""
    
    def __init__(self, x=0, y=0, state="red"):
        color = self._state_to_color(state)
        super().__init__(x, y, radius=50, color=color, intensity=0.5)
        self.state = state
        self.pulse_time = 0
    
    def _state_to_color(self, state):
        colors = {
            "red": COLORS["light_red"],
            "yellow": COLORS["light_yellow"],
            "green": COLORS["light_green"],
        }
        return colors.get(state, COLORS["light_red"])
    
    def set_state(self, state):
        if state != self.state:
            self.state = state
            self.color = self._state_to_color(state)
            self._cached_surface = None
    
    def update(self, dt):
        # Subtle pulse effect
        self.pulse_time += dt
        pulse = 0.8 + 0.2 * math.sin(self.pulse_time * 3)
        self.intensity = 0.5 * pulse


class ShadowCaster:
    """Handles shadow rendering for tiles and objects."""
    
    def __init__(self):
        self.offset_x = SHADOW_OFFSET_X
        self.offset_y = SHADOW_OFFSET_Y
        self.opacity = SHADOW_OPACITY
        self._shadow_cache = {}
    
    def create_tile_shadow(self, width, height):
        """Create a shadow surface for a rectangular tile."""
        cache_key = (width, height)
        if cache_key in self._shadow_cache:
            return self._shadow_cache[cache_key]
        
        # Create shadow with soft edges
        shadow = pygame.Surface((width + 10, height + 10), pygame.SRCALPHA)
        
        # Main shadow rectangle
        shadow_color = (0, 0, 0, self.opacity)
        shadow_rect = pygame.Rect(self.offset_x, self.offset_y, width, height)
        pygame.draw.rect(shadow, shadow_color, shadow_rect, border_radius=4)
        
        # Soften edges with smaller rectangles
        for i in range(3):
            shrink = i * 2
            alpha = self.opacity - i * 20
            if alpha > 0:
                inner_rect = shadow_rect.inflate(-shrink * 2, -shrink * 2)
                pygame.draw.rect(shadow, (0, 0, 0, alpha), inner_rect, border_radius=2)
        
        self._shadow_cache[cache_key] = shadow
        return shadow
    
    def create_vehicle_shadow(self, width, height):
        """Create an elliptical shadow for vehicle."""
        cache_key = ("vehicle", width, height)
        if cache_key in self._shadow_cache:
            return self._shadow_cache[cache_key]
        
        # Elliptical shadow
        shadow = pygame.Surface((width + 20, height + 20), pygame.SRCALPHA)
        center = (width // 2 + 10, height // 2 + 12)
        
        # Draw multiple ellipses for soft edge
        for i in range(5):
            alpha = self.opacity - i * 15
            if alpha > 0:
                w = width // 2 - i * 2
                h = height // 3 - i
                if w > 0 and h > 0:
                    rect = pygame.Rect(center[0] - w, center[1] - h, w * 2, h * 2)
                    pygame.draw.ellipse(shadow, (0, 0, 0, alpha), rect)
        
        self._shadow_cache[cache_key] = shadow
        return shadow


class AmbientOcclusion:
    """Simulates ambient occlusion at tile corners and edges."""
    
    def __init__(self, strength=AO_STRENGTH):
        self.strength = strength
        self._corner_cache = {}
    
    def create_corner_shadow(self, size, corner_type):
        """
        Create corner AO shadow.
        
        corner_type: "tl", "tr", "bl", "br"
        """
        cache_key = (size, corner_type)
        if cache_key in self._corner_cache:
            return self._corner_cache[cache_key]
        
        surface = pygame.Surface((size, size), pygame.SRCALPHA)
        
        # Draw gradient corner
        for i in range(size):
            for j in range(size):
                # Distance from corner
                if corner_type == "tl":
                    dist = math.sqrt(i * i + j * j)
                elif corner_type == "tr":
                    dist = math.sqrt((size - i) ** 2 + j * j)
                elif corner_type == "bl":
                    dist = math.sqrt(i * i + (size - j) ** 2)
                else:  # br
                    dist = math.sqrt((size - i) ** 2 + (size - j) ** 2)
                
                # Normalize and invert
                t = min(1, dist / size)
                alpha = int((1 - t) * self.strength)
                
                if alpha > 0:
                    surface.set_at((i, j), (0, 0, 0, alpha))
        
        self._corner_cache[cache_key] = surface
        return surface
    
    def create_edge_shadow(self, length, direction):
        """
        Create edge AO shadow.
        
        direction: "top", "bottom", "left", "right"
        """
        thickness = 8
        
        if direction in ("top", "bottom"):
            surface = pygame.Surface((length, thickness), pygame.SRCALPHA)
            for y in range(thickness):
                if direction == "top":
                    t = y / thickness
                else:
                    t = 1 - y / thickness
                alpha = int((1 - t) * self.strength)
                pygame.draw.line(surface, (0, 0, 0, alpha), (0, y), (length, y))
        else:
            surface = pygame.Surface((thickness, length), pygame.SRCALPHA)
            for x in range(thickness):
                if direction == "left":
                    t = x / thickness
                else:
                    t = 1 - x / thickness
                alpha = int((1 - t) * self.strength)
                pygame.draw.line(surface, (0, 0, 0, alpha), (x, 0), (x, length))
        
        return surface


class NormalMapShading:
    """Simulates normal-map style lighting on tiles."""
    
    def __init__(self, light_dir=(1, 1)):
        """
        light_dir: Normalized direction from which light comes (x, y)
        """
        self.light_dir = light_dir
        self._normalize_light()
    
    def _normalize_light(self):
        mag = math.sqrt(self.light_dir[0] ** 2 + self.light_dir[1] ** 2)
        if mag > 0:
            self.light_dir = (self.light_dir[0] / mag, self.light_dir[1] / mag)
    
    def apply_to_surface(self, surface, height_map=None):
        """
        Apply pseudo-normal shading to a surface.
        
        If no height_map, creates a simple edge highlight effect.
        """
        width, height = surface.get_size()
        result = surface.copy()
        
        # Create highlight and shadow overlays
        highlight = pygame.Surface((width, height), pygame.SRCALPHA)
        shadow = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Simple edge-based shading
        # Highlight on top-left edges, shadow on bottom-right
        highlight_strength = 20
        shadow_strength = 30
        
        # Top edge highlight
        pygame.draw.line(highlight, (255, 255, 255, highlight_strength),
                        (0, 0), (width, 0), 2)
        # Left edge highlight
        pygame.draw.line(highlight, (255, 255, 255, highlight_strength),
                        (0, 0), (0, height), 2)
        
        # Bottom edge shadow
        pygame.draw.line(shadow, (0, 0, 0, shadow_strength),
                        (0, height - 1), (width, height - 1), 2)
        # Right edge shadow
        pygame.draw.line(shadow, (0, 0, 0, shadow_strength),
                        (width - 1, 0), (width - 1, height), 2)
        
        result.blit(highlight, (0, 0))
        result.blit(shadow, (0, 0))
        
        return result


class LightingSystem:
    """
    Main lighting system coordinating all light effects.
    """
    
    def __init__(self, screen_width, screen_height):
        self.width = screen_width
        self.height = screen_height
        
        # Ambient level (0-1)
        self.ambient = AMBIENT_LIGHT_LEVEL
        
        # Light sources
        self.vehicle_light = VehicleLight()
        self.traffic_lights = []
        
        # Shadow systems
        self.shadow_caster = ShadowCaster()
        self.ambient_occlusion = AmbientOcclusion()
        self.normal_shading = NormalMapShading()
        
        # Render surfaces
        self._light_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        self._shadow_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
    
    def resize(self, width, height):
        """Handle screen resize."""
        self.width = width
        self.height = height
        self._light_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        self._shadow_surface = pygame.Surface((width, height), pygame.SRCALPHA)
    
    def add_traffic_light(self, x, y, state="red"):
        """Add a traffic light glow source."""
        light = TrafficLightGlow(x, y, state)
        self.traffic_lights.append(light)
        return light
    
    def clear_traffic_lights(self):
        """Remove all traffic light glows."""
        self.traffic_lights.clear()
    
    def update(self, dt):
        """Update all light sources."""
        for light in self.traffic_lights:
            light.update(dt)
    
    def render_lighting(self, camera_x=0, camera_y=0):
        """
        Render the lighting overlay.
        
        Returns a surface to be blended with the scene.
        """
        # Clear to ambient darkness
        ambient_color = int(255 * (1 - self.ambient))
        self._light_surface.fill((0, 0, 0, ambient_color))
        
        # Add vehicle light
        if self.vehicle_light.active:
            light_surf = self.vehicle_light.get_cone_surface()
            x = int(self.vehicle_light.x - camera_x - self.vehicle_light.radius)
            y = int(self.vehicle_light.y - camera_y - self.vehicle_light.radius)
            self._light_surface.blit(light_surf, (x, y), special_flags=pygame.BLEND_RGBA_SUB)
        
        # Add traffic light glows
        for light in self.traffic_lights:
            if light.active:
                light_surf = light.get_surface()
                x = int(light.x - camera_x - light.radius)
                y = int(light.y - camera_y - light.radius)
                self._light_surface.blit(light_surf, (x, y), special_flags=pygame.BLEND_RGBA_SUB)
        
        return self._light_surface
    
    def get_tile_shadow(self, tile_size=TILE_SIZE):
        """Get a pre-rendered tile shadow."""
        return self.shadow_caster.create_tile_shadow(tile_size, tile_size)
    
    def get_vehicle_shadow(self, width, height):
        """Get a vehicle shadow surface."""
        return self.shadow_caster.create_vehicle_shadow(width, height)

