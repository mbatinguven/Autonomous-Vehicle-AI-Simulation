"""
particles.py - Advanced 2D particle system for cinematic effects.

Supports:
- Multiple emitter types (dust, smoke, sparks, ambient)
- Per-particle physics (velocity, friction, gravity)
- Fade, scale, and color animations
- Blending modes
- Performance-optimized batch rendering
"""

import pygame
import random
import math
from constants import (
    PARTICLE_MAX_COUNT, DUST_LIFETIME, DUST_SIZE, SMOKE_LIFETIME,
    SPARK_LIFETIME, AMBIENT_PARTICLE_RATE, COLORS, PARTICLES_ENABLED
)


class Particle:
    """Single particle with physics and visual properties."""
    
    __slots__ = [
        'x', 'y', 'vx', 'vy', 'ax', 'ay',
        'lifetime', 'max_lifetime',
        'size', 'start_size', 'end_size',
        'color', 'start_color', 'end_color',
        'alpha', 'start_alpha', 'end_alpha',
        'friction', 'gravity',
        'rotation', 'rotation_speed',
        'blend_mode', 'alive'
    ]
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset particle to default state."""
        self.x = 0
        self.y = 0
        self.vx = 0
        self.vy = 0
        self.ax = 0
        self.ay = 0
        self.lifetime = 0
        self.max_lifetime = 1.0
        self.size = 4
        self.start_size = 4
        self.end_size = 0
        self.color = (255, 255, 255)
        self.start_color = (255, 255, 255)
        self.end_color = (255, 255, 255)
        self.alpha = 255
        self.start_alpha = 255
        self.end_alpha = 0
        self.friction = 0.98
        self.gravity = 0
        self.rotation = 0
        self.rotation_speed = 0
        self.blend_mode = pygame.BLEND_ALPHA_SDL2
        self.alive = False
    
    def spawn(self, x, y, vx=0, vy=0, lifetime=1.0, size=4, color=(255, 255, 255)):
        """Spawn the particle with initial values."""
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.lifetime = 0
        self.max_lifetime = lifetime
        self.size = size
        self.start_size = size
        self.color = color
        self.start_color = color
        self.alpha = 255
        self.start_alpha = 255
        self.alive = True
    
    def update(self, dt):
        """Update particle physics and lifetime."""
        if not self.alive:
            return
        
        # Update lifetime
        self.lifetime += dt
        if self.lifetime >= self.max_lifetime:
            self.alive = False
            return
        
        # Progress (0 to 1)
        t = self.lifetime / self.max_lifetime
        
        # Apply acceleration
        self.vx += self.ax * dt
        self.vy += self.ay * dt
        
        # Apply gravity
        self.vy += self.gravity * dt
        
        # Apply friction
        self.vx *= self.friction
        self.vy *= self.friction
        
        # Update position
        self.x += self.vx * dt
        self.y += self.vy * dt
        
        # Update rotation
        self.rotation += self.rotation_speed * dt
        
        # Interpolate size
        self.size = self.start_size + (self.end_size - self.start_size) * t
        
        # Interpolate alpha
        self.alpha = int(self.start_alpha + (self.end_alpha - self.start_alpha) * t)
        
        # Interpolate color
        self.color = (
            int(self.start_color[0] + (self.end_color[0] - self.start_color[0]) * t),
            int(self.start_color[1] + (self.end_color[1] - self.start_color[1]) * t),
            int(self.start_color[2] + (self.end_color[2] - self.start_color[2]) * t),
        )


class ParticleEmitter:
    """Base emitter class for spawning particles."""
    
    def __init__(self, x=0, y=0):
        self.x = x
        self.y = y
        self.active = True
        self.rate = 10  # Particles per second
        self._accumulator = 0
    
    def set_position(self, x, y):
        self.x = x
        self.y = y
    
    def configure_particle(self, particle):
        """Override to configure spawned particles."""
        pass
    
    def update(self, dt, particle_pool):
        """Spawn particles based on rate."""
        if not self.active:
            return
        
        self._accumulator += self.rate * dt
        
        while self._accumulator >= 1:
            self._accumulator -= 1
            particle = particle_pool.get_particle()
            if particle:
                self.configure_particle(particle)


class DustEmitter(ParticleEmitter):
    """Emits dust particles behind moving vehicles."""
    
    def __init__(self, x=0, y=0):
        super().__init__(x, y)
        self.rate = 30
        self.direction = 0  # Degrees
        self.speed_factor = 1.0
    
    def configure_particle(self, p):
        # Spawn behind vehicle
        angle_rad = math.radians(self.direction + 180)
        offset = random.uniform(5, 15)
        
        p.spawn(
            x=self.x + math.sin(angle_rad) * offset + random.uniform(-5, 5),
            y=self.y + math.cos(angle_rad) * offset + random.uniform(-5, 5),
            vx=random.uniform(-20, 20),
            vy=random.uniform(-10, 20),
            lifetime=DUST_LIFETIME * random.uniform(0.8, 1.2),
            size=random.randint(DUST_SIZE[0], DUST_SIZE[1]),
            color=COLORS["particle_dust"]
        )
        p.end_size = 0
        p.start_alpha = int(150 * self.speed_factor)
        p.end_alpha = 0
        p.friction = 0.95
        p.gravity = -10  # Float up slightly


class SmokeEmitter(ParticleEmitter):
    """Emits smoke from building chimneys."""
    
    def __init__(self, x=0, y=0):
        super().__init__(x, y)
        self.rate = 2
    
    def configure_particle(self, p):
        p.spawn(
            x=self.x + random.uniform(-3, 3),
            y=self.y,
            vx=random.uniform(-5, 5),
            vy=random.uniform(-30, -15),
            lifetime=SMOKE_LIFETIME * random.uniform(0.8, 1.2),
            size=random.randint(8, 16),
            color=COLORS["particle_smoke"]
        )
        p.end_size = random.randint(20, 35)
        p.start_alpha = 120
        p.end_alpha = 0
        p.friction = 0.99
        p.gravity = -5


class SparkEmitter(ParticleEmitter):
    """Emits sparks for traffic light changes."""
    
    def __init__(self, x=0, y=0):
        super().__init__(x, y)
        self.rate = 0  # Burst mode
        self._burst_count = 0
    
    def burst(self, count=15):
        """Trigger a burst of sparks."""
        self._burst_count = count
    
    def configure_particle(self, p):
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(50, 150)
        
        p.spawn(
            x=self.x + random.uniform(-5, 5),
            y=self.y + random.uniform(-5, 5),
            vx=math.cos(angle) * speed,
            vy=math.sin(angle) * speed,
            lifetime=SPARK_LIFETIME * random.uniform(0.5, 1.5),
            size=random.randint(2, 4),
            color=COLORS["particle_spark"]
        )
        p.end_size = 0
        p.start_alpha = 255
        p.end_alpha = 0
        p.friction = 0.92
        p.gravity = 100
    
    def update(self, dt, particle_pool):
        # Handle burst mode
        while self._burst_count > 0:
            self._burst_count -= 1
            particle = particle_pool.get_particle()
            if particle:
                self.configure_particle(particle)


class AmbientEmitter(ParticleEmitter):
    """Emits subtle floating dust particles in the city."""
    
    def __init__(self, bounds):
        super().__init__(0, 0)
        self.bounds = bounds  # (x, y, width, height)
        self.rate = AMBIENT_PARTICLE_RATE * 60  # Convert to per-second
    
    def configure_particle(self, p):
        x, y, w, h = self.bounds
        
        p.spawn(
            x=random.uniform(x, x + w),
            y=random.uniform(y, y + h),
            vx=random.uniform(-10, 10),
            vy=random.uniform(-5, 5),
            lifetime=random.uniform(3, 6),
            size=random.randint(1, 3),
            color=(200, 200, 210)
        )
        p.end_size = p.size
        p.start_alpha = 0
        p.end_alpha = 0
        p.friction = 0.995
        
        # Fade in then out
        p.max_lifetime = p.lifetime
        # Custom handling needed for fade-in-out


class ParticlePool:
    """Object pool for efficient particle management."""
    
    def __init__(self, max_particles=PARTICLE_MAX_COUNT):
        self.particles = [Particle() for _ in range(max_particles)]
        self._free_indices = list(range(max_particles))
        self.active_count = 0
    
    def get_particle(self):
        """Get a free particle from the pool."""
        if not self._free_indices:
            return None
        
        idx = self._free_indices.pop()
        particle = self.particles[idx]
        particle.reset()
        self.active_count += 1
        return particle
    
    def update(self, dt):
        """Update all active particles."""
        self._free_indices.clear()
        self.active_count = 0
        
        for i, p in enumerate(self.particles):
            if p.alive:
                p.update(dt)
                if not p.alive:
                    self._free_indices.append(i)
                else:
                    self.active_count += 1
            else:
                self._free_indices.append(i)
    
    def get_active_particles(self):
        """Yield all active particles."""
        for p in self.particles:
            if p.alive:
                yield p


class ParticleSystem:
    """
    Main particle system managing all emitters and rendering.
    """
    
    def __init__(self):
        self.enabled = PARTICLES_ENABLED
        self.pool = ParticlePool()
        self.emitters = []
        
        # Cached surface for batch rendering
        self._render_surface = None
    
    def add_emitter(self, emitter):
        """Add an emitter to the system."""
        self.emitters.append(emitter)
        return emitter
    
    def remove_emitter(self, emitter):
        """Remove an emitter."""
        if emitter in self.emitters:
            self.emitters.remove(emitter)
    
    def clear_emitters(self):
        """Remove all emitters."""
        self.emitters.clear()
    
    def create_dust_emitter(self, x=0, y=0):
        """Create and add a dust emitter."""
        emitter = DustEmitter(x, y)
        return self.add_emitter(emitter)
    
    def create_smoke_emitter(self, x, y):
        """Create and add a smoke emitter."""
        emitter = SmokeEmitter(x, y)
        return self.add_emitter(emitter)
    
    def create_spark_emitter(self, x, y):
        """Create and add a spark emitter."""
        emitter = SparkEmitter(x, y)
        return self.add_emitter(emitter)
    
    def create_ambient_emitter(self, bounds):
        """Create ambient floating particles."""
        emitter = AmbientEmitter(bounds)
        return self.add_emitter(emitter)
    
    def burst_sparks(self, x, y, count=15):
        """Spawn a burst of sparks at position."""
        emitter = SparkEmitter(x, y)
        emitter.burst(count)
        emitter.update(0, self.pool)
        # Don't add to permanent emitters
    
    def update(self, dt):
        """Update all emitters and particles."""
        if not self.enabled:
            return
        
        # Update emitters
        for emitter in self.emitters:
            emitter.update(dt, self.pool)
        
        # Update particles
        self.pool.update(dt)
    
    def render(self, surface, camera_x=0, camera_y=0):
        """
        Render all particles to a surface.
        
        Args:
            surface: Target surface
            camera_x, camera_y: Camera offset
        """
        if not self.enabled:
            return
        
        for p in self.pool.get_active_particles():
            # Calculate screen position
            screen_x = int(p.x - camera_x)
            screen_y = int(p.y - camera_y)
            
            # Skip if off-screen
            if (screen_x < -50 or screen_x > surface.get_width() + 50 or
                screen_y < -50 or screen_y > surface.get_height() + 50):
                continue
            
            # Create particle surface
            size = max(1, int(p.size))
            particle_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            
            # Draw particle (soft circle)
            color_with_alpha = (*p.color, max(0, min(255, p.alpha)))
            pygame.draw.circle(particle_surf, color_with_alpha, (size, size), size)
            
            # Blit to main surface
            surface.blit(particle_surf, (screen_x - size, screen_y - size))
    
    def get_stats(self):
        """Get particle system statistics."""
        return {
            "active": self.pool.active_count,
            "max": len(self.pool.particles),
            "emitters": len(self.emitters),
        }

