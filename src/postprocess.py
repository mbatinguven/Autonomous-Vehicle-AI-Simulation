"""
postprocess.py - Post-processing effects pipeline (no numpy required).

Features:
- HDR-like bloom effect (simplified)
- Vignette
- Color grading
- Screen compositing
"""

import pygame
from constants import (
    BLOOM_ENABLED, BLOOM_INTENSITY, BLOOM_THRESHOLD, 
    BLOOM_BLUR_PASSES, BLOOM_SCALE, COLORS
)


class BloomEffect:
    """
    HDR-like bloom effect using downscale, blur, and composite.
    Uses only pygame functions (no numpy required).
    """
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.enabled = BLOOM_ENABLED
        self.intensity = BLOOM_INTENSITY
        self.blur_passes = BLOOM_BLUR_PASSES
        self.scale = BLOOM_SCALE
        
        # Working surfaces
        self._init_surfaces()
    
    def _init_surfaces(self):
        """Initialize working surfaces."""
        # Downscaled size for blur
        self.small_w = max(1, self.width // self.scale)
        self.small_h = max(1, self.height // self.scale)
        
        self.blur_surface = pygame.Surface((self.small_w, self.small_h))
        self.bloom_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
    
    def resize(self, width, height):
        """Handle screen resize."""
        self.width = width
        self.height = height
        self._init_surfaces()
    
    def _blur(self, surface):
        """Apply blur using scale down/up technique."""
        w, h = surface.get_size()
        
        for _ in range(self.blur_passes):
            # Scale down
            half_w = max(1, w // 2)
            half_h = max(1, h // 2)
            temp = pygame.transform.smoothscale(surface, (half_w, half_h))
            # Scale back up
            pygame.transform.smoothscale(temp, (w, h), surface)
        
        return surface
    
    def apply(self, source):
        """
        Apply bloom effect - ONLY to bright light sources.
        Does NOT affect the overall scene brightness.
        """
        if not self.enabled:
            return source
        
        # Downscale source
        pygame.transform.smoothscale(source, (self.small_w, self.small_h), self.blur_surface)
        
        # CRITICAL: Darken the blur surface to remove non-bright areas
        # This prevents the "white veil" effect
        darken = pygame.Surface((self.small_w, self.small_h))
        darken.fill((60, 60, 60))  # Subtract darkness to isolate bright spots
        self.blur_surface.blit(darken, (0, 0), special_flags=pygame.BLEND_RGB_SUB)
        
        # Blur it
        self._blur(self.blur_surface)
        
        # Upscale back to full resolution
        pygame.transform.smoothscale(self.blur_surface, (self.width, self.height), self.bloom_surface)
        
        # Composite - very subtle, only visible around actual lights
        result = source.copy()
        
        # VERY LOW alpha (15-25 range max)
        bloom_alpha = int(255 * self.intensity * 0.2)
        self.bloom_surface.set_alpha(bloom_alpha)
        result.blit(self.bloom_surface, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        
        return result


class VignetteEffect:
    """
    Vignette darkening at screen edges - night driving atmosphere.
    """
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.intensity = 0.35  # Stronger vignette for night mode
        
        self._surface = None
        self._create_surface()
    
    def _create_surface(self):
        """Pre-render the vignette overlay - very subtle."""
        self._surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        
        center_x = self.width // 2
        center_y = self.height // 2
        max_dist = (center_x ** 2 + center_y ** 2) ** 0.5
        
        # Draw radial gradient - only at far edges
        step = 8
        for y in range(0, self.height, step):
            for x in range(0, self.width, step):
                dx = x + step // 2 - center_x
                dy = y + step // 2 - center_y
                dist = (dx ** 2 + dy ** 2) ** 0.5
                
                # Normalized distance
                norm_dist = dist / max_dist
                
                # Night mode: start vignette earlier for atmosphere
                if norm_dist > 0.4:
                    t = (norm_dist - 0.4) / 0.6
                    alpha = int(t * t * 255 * self.intensity)
                    alpha = min(120, alpha)  # Higher cap for night
                    
                    if alpha > 0:
                        pygame.draw.rect(self._surface, (0, 0, 0, alpha), 
                                       (x, y, step, step))
    
    def resize(self, width, height):
        """Handle screen resize."""
        self.width = width
        self.height = height
        self._create_surface()
    
    def apply(self, surface):
        """Apply vignette to surface."""
        surface.blit(self._surface, (0, 0))
        return surface
    
    def get_surface(self):
        """Get the vignette overlay surface."""
        return self._surface


class ColorGrading:
    """
    Simple color grading using surface blending.
    """
    
    def __init__(self):
        # Color tint (RGB)
        self.tint = (255, 255, 255)
        self.tint_strength = 0.0  # 0-1
    
    def set_cinematic(self):
        """Apply warm cinematic tint."""
        self.tint = (255, 250, 240)
        self.tint_strength = 0.1
    
    def set_night(self):
        """Apply cool night tint."""
        self.tint = (200, 210, 255)
        self.tint_strength = 0.15
    
    def apply(self, surface):
        """Apply color grading."""
        if self.tint_strength <= 0 or self.tint == (255, 255, 255):
            return surface
        
        # Create tint overlay
        tint_surf = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        alpha = int(255 * self.tint_strength)
        tint_surf.fill((*self.tint, alpha))
        
        # Blend with multiply for subtle effect
        surface.blit(tint_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        return surface


class PostProcessor:
    """
    Main post-processing pipeline coordinating all effects.
    """
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        
        # Effects
        self.bloom = BloomEffect(width, height)
        self.vignette = VignetteEffect(width, height)
        self.color_grading = ColorGrading()
        
        # Effect toggles
        self.bloom_enabled = BLOOM_ENABLED
        self.vignette_enabled = True
        self.color_grading_enabled = False  # Disabled by default
    
    def resize(self, width, height):
        """Handle screen resize."""
        self.width = width
        self.height = height
        self.bloom.resize(width, height)
        self.vignette.resize(width, height)
    
    def process(self, source):
        """
        Apply all post-processing effects.
        
        Args:
            source: The rendered scene surface
            
        Returns:
            Processed surface
        """
        result = source
        
        # Apply effects in order
        if self.bloom_enabled:
            result = self.bloom.apply(result)
        
        if self.color_grading_enabled:
            result = self.color_grading.apply(result)
        
        if self.vignette_enabled:
            result = self.vignette.apply(result)
        
        return result
    
    def get_vignette(self):
        """Get vignette surface for separate compositing."""
        return self.vignette.get_surface()
    
    def toggle_bloom(self):
        """Toggle bloom effect."""
        self.bloom_enabled = not self.bloom_enabled
        self.bloom.enabled = self.bloom_enabled
        return self.bloom_enabled
    
    def set_bloom_intensity(self, intensity):
        """Set bloom intensity (0-1)."""
        self.bloom.intensity = max(0, min(1, intensity))


class RenderPipeline:
    """
    Complete render pipeline with multiple layers and post-processing.
    """
    
    def __init__(self, width, height):
        self.width = width
        self.height = height
        
        # Layer surfaces
        self.layers = {
            "background": pygame.Surface((width, height)),
            "ground": pygame.Surface((width, height), pygame.SRCALPHA),
            "shadows": pygame.Surface((width, height), pygame.SRCALPHA),
            "objects": pygame.Surface((width, height), pygame.SRCALPHA),
            "particles": pygame.Surface((width, height), pygame.SRCALPHA),
            "lighting": pygame.Surface((width, height), pygame.SRCALPHA),
            "ui": pygame.Surface((width, height), pygame.SRCALPHA),
        }
        
        # Composite surface
        self._composite = pygame.Surface((width, height))
        
        # Post-processor
        self.post = PostProcessor(width, height)
    
    def resize(self, width, height):
        """Handle screen resize."""
        self.width = width
        self.height = height
        
        for name in self.layers:
            if name == "background":
                self.layers[name] = pygame.Surface((width, height))
            else:
                self.layers[name] = pygame.Surface((width, height), pygame.SRCALPHA)
        
        self._composite = pygame.Surface((width, height))
        self.post.resize(width, height)
    
    def clear_layer(self, name):
        """Clear a specific layer."""
        if name in self.layers:
            if name == "background":
                self.layers[name].fill(COLORS["background"])
            else:
                self.layers[name].fill((0, 0, 0, 0))
    
    def clear_all(self):
        """Clear all layers."""
        for name in self.layers:
            self.clear_layer(name)
    
    def get_layer(self, name):
        """Get a layer surface for drawing."""
        return self.layers.get(name)
    
    def composite(self):
        """Composite all layers into final image."""
        # Start with background
        self._composite.blit(self.layers["background"], (0, 0))
        
        # Layer order
        layer_order = ["ground", "shadows", "objects", "particles", "lighting"]
        
        for name in layer_order:
            self._composite.blit(self.layers[name], (0, 0))
        
        # Apply post-processing
        result = self.post.process(self._composite)
        
        # Add UI on top (no post-processing)
        result.blit(self.layers["ui"], (0, 0))
        
        return result
    
    def render_to_screen(self, screen):
        """Composite and render to screen."""
        final = self.composite()
        screen.blit(final, (0, 0))
