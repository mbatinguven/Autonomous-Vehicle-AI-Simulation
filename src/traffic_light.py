"""
traffic_light.py - Advanced animated traffic light system.

Features:
- Three-state cycle (Red → Green → Yellow)
- Smooth state transitions with fade
- Glow effects integration
- Sound trigger callbacks
- Spark emission on change
"""

import math
from constants import (
    TRAFFIC_RED_TIME, TRAFFIC_YELLOW_TIME, TRAFFIC_GREEN_TIME,
    TRAFFIC_TRANSITION_TIME, TILE_SIZE
)


class TrafficLight:
    """
    Single traffic light with animated state transitions.
    
    States cycle: RED → GREEN → YELLOW → RED
    """
    
    STATE_RED = "red"
    STATE_YELLOW = "yellow"
    STATE_GREEN = "green"
    
    def __init__(self, position=None, offset=0.0):
        """
        Args:
            position: Grid position (row, col)
            offset: Time offset for desync (seconds)
        """
        self.position = position
        
        # Timing
        self.red_time = TRAFFIC_RED_TIME
        self.green_time = TRAFFIC_GREEN_TIME
        self.yellow_time = TRAFFIC_YELLOW_TIME
        self.transition_time = TRAFFIC_TRANSITION_TIME
        
        # Current time in cycle
        self._elapsed = offset
        
        # State tracking
        self._current_state = self.STATE_RED
        self._previous_state = None
        self._state_changed = False
        self._transition_progress = 1.0  # 0 = transitioning, 1 = stable
        
        # Glow intensity (for rendering)
        self.glow_intensity = 1.0
        self._pulse_time = 0
    
    @property
    def cycle_duration(self):
        return self.red_time + self.green_time + self.yellow_time
    
    @property
    def state(self):
        return self._current_state
    
    @property
    def state_changed(self):
        """True if state changed this frame."""
        return self._state_changed
    
    @property
    def time_remaining(self):
        """Time remaining in current state."""
        time_in_cycle = self._elapsed % self.cycle_duration
        
        if time_in_cycle < self.red_time:
            return self.red_time - time_in_cycle
        elif time_in_cycle < self.red_time + self.green_time:
            return (self.red_time + self.green_time) - time_in_cycle
        else:
            return self.cycle_duration - time_in_cycle
    
    @property
    def world_position(self):
        """Get world pixel position."""
        if self.position is None:
            return (0, 0)
        row, col = self.position
        return (col * TILE_SIZE + TILE_SIZE / 2, row * TILE_SIZE + TILE_SIZE / 2)
    
    def _calculate_state(self):
        """Calculate current state from elapsed time."""
        time_in_cycle = self._elapsed % self.cycle_duration
        
        if time_in_cycle < self.red_time:
            return self.STATE_RED
        elif time_in_cycle < self.red_time + self.green_time:
            return self.STATE_GREEN
        else:
            return self.STATE_YELLOW
    
    def is_red(self):
        return self._current_state == self.STATE_RED
    
    def is_green(self):
        return self._current_state == self.STATE_GREEN
    
    def is_yellow(self):
        return self._current_state == self.STATE_YELLOW
    
    def should_stop(self):
        """Check if vehicle should stop (red or yellow about to turn red)."""
        if self._current_state == self.STATE_RED:
            return True
        if self._current_state == self.STATE_YELLOW and self.time_remaining < 0.5:
            return True
        return False
    
    def update(self, dt):
        """
        Update traffic light state.
        
        Returns:
            True if state changed
        """
        self._elapsed += dt
        self._state_changed = False
        
        # Calculate new state
        new_state = self._calculate_state()
        
        if new_state != self._current_state:
            self._previous_state = self._current_state
            self._current_state = new_state
            self._state_changed = True
            self._transition_progress = 0.0
        
        # Update transition
        if self._transition_progress < 1.0:
            self._transition_progress += dt / self.transition_time
            self._transition_progress = min(1.0, self._transition_progress)
        
        # Update glow pulse
        self._pulse_time += dt
        base_glow = 0.8 + 0.2 * math.sin(self._pulse_time * 3)
        
        # Boost glow during transition
        if self._transition_progress < 1.0:
            self.glow_intensity = base_glow + 0.5 * (1 - self._transition_progress)
        else:
            self.glow_intensity = base_glow
        
        return self._state_changed
    
    def reset(self, offset=0.0):
        """Reset to beginning of cycle."""
        self._elapsed = offset
        self._current_state = self._calculate_state()
        self._state_changed = False
        self._transition_progress = 1.0


class TrafficLightManager:
    """
    Manages multiple traffic lights with coordinated updates.
    """
    
    def __init__(self):
        self._lights = {}  # position -> TrafficLight
        self._state_changed_this_frame = False
        self._changed_positions = []  # For spark effects
    
    @property
    def lights(self):
        return list(self._lights.values())
    
    @property
    def positions(self):
        return list(self._lights.keys())
    
    @property
    def state_changed(self):
        return self._state_changed_this_frame
    
    @property
    def changed_positions(self):
        """Get positions where lights changed this frame."""
        return self._changed_positions
    
    def add_light(self, position, offset=None):
        """Add a traffic light at position."""
        import random
        if offset is None:
            offset = random.uniform(0, 3)
        
        light = TrafficLight(position, offset)
        self._lights[position] = light
        return light
    
    def remove_light(self, position):
        """Remove traffic light at position."""
        if position in self._lights:
            del self._lights[position]
            return True
        return False
    
    def get_light(self, position):
        """Get traffic light at position."""
        return self._lights.get(position)
    
    def is_red_at(self, position):
        """Check if red light at position."""
        light = self._lights.get(position)
        return light.is_red() if light else False
    
    def should_stop_at(self, position):
        """Check if vehicle should stop at position."""
        light = self._lights.get(position)
        return light.should_stop() if light else False
    
    def get_state_at(self, position):
        """Get light state at position."""
        light = self._lights.get(position)
        return light.state if light else None
    
    def get_time_remaining_at(self, position):
        """Get time remaining at position."""
        light = self._lights.get(position)
        return light.time_remaining if light else 0.0
    
    def get_nearest_timer(self):
        """Get smallest time remaining across all lights."""
        if not self._lights:
            return 0.0
        return min(l.time_remaining for l in self._lights.values())
    
    def update(self, dt):
        """Update all traffic lights."""
        self._state_changed_this_frame = False
        self._changed_positions.clear()
        
        for pos, light in self._lights.items():
            if light.update(dt):
                self._state_changed_this_frame = True
                self._changed_positions.append(pos)
    
    def clear(self):
        """Remove all lights."""
        self._lights.clear()
    
    def sync_with_grid(self, grid_positions):
        """
        Sync lights with grid traffic positions.
        
        Adds new lights and removes old ones.
        """
        current = set(self._lights.keys())
        target = set(grid_positions)
        
        # Add new
        for pos in target - current:
            self.add_light(pos)
        
        # Remove old
        for pos in current - target:
            self.remove_light(pos)
