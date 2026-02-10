"""
agent.py - Premium autonomous vehicle with advanced animations.

Features:
- Smooth LERP movement between grid cells
- Direction-based rotation with interpolation
- Idle wobble animation when waiting
- Acceleration-based body tilt
- Brake light activation
- Dust particle emission control
- Speed-based animation states
- Collision avoidance
"""

import math
from constants import (
    TILE_SIZE, DIRECTION_ANGLES,
    VEHICLE_SPEED, VEHICLE_LERP_SPEED,
    VEHICLE_ACCELERATION, VEHICLE_DECELERATION,
    VEHICLE_WOBBLE_SPEED, VEHICLE_WOBBLE_AMOUNT,
    VEHICLE_TILT_AMOUNT, VEHICLE_DUST_RATE
)


class Agent:
    """
    Premium autonomous vehicle with cinematic animations.
    
    The agent operates in world pixel coordinates for smooth rendering,
    while path following uses grid (row, col) coordinates.
    """
    
    def __init__(self):
        # World position (pixels)
        self.x = 0.0
        self.y = 0.0
        
        # Target position for interpolation
        self._target_x = 0.0
        self._target_y = 0.0
        
        # Velocity for physics
        self._velocity = 0.0
        self._max_velocity = VEHICLE_SPEED
        
        # Rotation (degrees, 0 = up, clockwise)
        self.angle = 0.0
        self._target_angle = 0.0
        
        # Path following
        self._path = []
        self._path_index = 0
        
        # Animation state
        self._wobble_time = 0.0
        self._wobble_offset_x = 0.0
        self._wobble_offset_y = 0.0
        self._tilt_amount = 0.0
        self._acceleration_state = 0.0  # -1 to 1 (braking to accelerating)
        
        # Status
        self._is_moving = False
        self._is_waiting = False
        self._is_braking = False
        self._arrived = False
        self._brake_lights = False
        
        # Dust emission
        self._dust_accumulator = 0.0
        self.emit_dust = False
    
    # =========================================================================
    # PROPERTIES
    # =========================================================================
    
    @property
    def position(self):
        """Get world position with wobble offset."""
        return (self.x + self._wobble_offset_x, 
                self.y + self._wobble_offset_y + self._tilt_amount)
    
    @property
    def render_x(self):
        return self.x + self._wobble_offset_x
    
    @property
    def render_y(self):
        return self.y + self._wobble_offset_y + self._tilt_amount
    
    @property
    def grid_position(self):
        """Get current grid cell (row, col)."""
        col = int(self.x / TILE_SIZE)
        row = int(self.y / TILE_SIZE)
        return (row, col)
    
    @property
    def path(self):
        return self._path.copy()
    
    @property
    def path_index(self):
        return self._path_index
    
    @property
    def has_path(self):
        return len(self._path) > 0
    
    @property
    def is_moving(self):
        return self._is_moving
    
    @property
    def is_waiting(self):
        return self._is_waiting
    
    @property
    def at_goal(self):
        return self._arrived
    
    @property
    def brake_lights_on(self):
        return self._brake_lights or self._is_waiting or self._is_braking
    
    @property
    def status(self):
        if not self._path:
            return "No Path"
        elif self._arrived:
            return "Arrived"
        elif self._is_waiting:
            return "Waiting"
        else:
            return "Moving"
    
    @property
    def speed_normalized(self):
        """Get speed as 0-1 for audio/effects."""
        return self._velocity / self._max_velocity if self._max_velocity > 0 else 0
    
    # =========================================================================
    # PATH MANAGEMENT
    # =========================================================================
    
    def set_path(self, path):
        """
        Set a new path to follow.
        
        Args:
            path: List of (row, col) tuples
        """
        self._path = path.copy() if path else []
        self._path_index = 0
        self._arrived = False
        self._is_waiting = False
        
        if self._path:
            # Start at first cell
            row, col = self._path[0]
            self.x = col * TILE_SIZE + TILE_SIZE / 2
            self.y = row * TILE_SIZE + TILE_SIZE / 2
            self._target_x = self.x
            self._target_y = self.y
            
            # Set initial direction
            if len(self._path) > 1:
                next_row, next_col = self._path[1]
                self._update_direction(row, col, next_row, next_col)
                self.angle = self._target_angle
    
    def set_position(self, row, col):
        """Directly set position without path."""
        self.x = col * TILE_SIZE + TILE_SIZE / 2
        self.y = row * TILE_SIZE + TILE_SIZE / 2
        self._target_x = self.x
        self._target_y = self.y
    
    def continue_with_new_path(self, path):
        """
        Continue from current position with a new path.
        Does NOT reset position - agent stays where it is.
        
        Args:
            path: New path starting from current position
        """
        if not path:
            return
        
        self._path = path.copy()
        self._path_index = 0
        self._arrived = False
        self._is_waiting = False
        
        # Don't change position - stay where we are
        # Just set target to next waypoint
        if len(self._path) > 1:
            next_row, next_col = self._path[1]
            self._target_x = next_col * TILE_SIZE + TILE_SIZE / 2
            self._target_y = next_row * TILE_SIZE + TILE_SIZE / 2
            
            # Update direction
            current_row, current_col = self._path[0]
            self._update_direction(current_row, current_col, next_row, next_col)
    
    def reset(self):
        """Reset agent state."""
        self._path = []
        self._path_index = 0
        self._velocity = 0
        self._is_moving = False
        self._is_waiting = False
        self._arrived = False
        self._brake_lights = False
    
    # =========================================================================
    # UPDATE LOGIC
    # =========================================================================
    
    def update(self, dt, is_red_light_at=None, npc_positions=None, 
               crosswalk_positions=None, pedestrian_positions=None):
        """
        Update agent physics and animation.
        
        Args:
            dt: Delta time in seconds
            is_red_light_at: Callback (row, col) -> bool for red light check
            npc_positions: List of (x, y) NPC world positions
            crosswalk_positions: List of (row, col) crosswalk positions
            pedestrian_positions: List of (x, y) pedestrian world positions
            
        Returns:
            True if agent reached a new path node
        """
        self.emit_dust = False
        reached_node = False
        
        if not self._path:
            self._is_moving = False
            self._is_waiting = False
            self._update_idle_animation(dt)
            return False
        
        # Clamp path index
        self._path_index = max(0, min(self._path_index, len(self._path) - 1))
        
        # Check if at goal
        if self._path_index >= len(self._path) - 1:
            self._arrived = True
            self._is_moving = False
            self._brake_lights = True
            self._decelerate(dt)
            self._move_toward_target(dt)
            return False
        
        # Get current and NEXT position in path
        current_row, current_col = self._path[self._path_index]
        next_row, next_col = self._path[self._path_index + 1] if self._path_index + 1 < len(self._path) else (current_row, current_col)
        
        # CRITICAL: Reset all flags first
        self._is_waiting = False
        self._is_moving = True
        self._brake_lights = False
        should_stop = False
        speed_mult = 1.0
        
        # Check for red light at NEXT cell - MUST STOP
        if is_red_light_at and is_red_light_at((next_row, next_col)):
            should_stop = True
        
        # Check for NPC vehicles AHEAD - MUST STOP
        if not should_stop and npc_positions:
            if not hasattr(self, '_wait_timer'):
                self._wait_timer = 0.0
            
            npc_ahead = False
            for npc_x, npc_y in npc_positions:
                dist = math.sqrt((self.x - npc_x) ** 2 + (self.y - npc_y) ** 2)
                if dist < TILE_SIZE * 2.0:  # Detection range
                    # Check if NPC is AHEAD
                    dx = npc_x - self.x
                    dy = npc_y - self.y
                    angle_to_npc = math.degrees(math.atan2(dx, -dy)) % 360
                    angle_diff = abs(angle_to_npc - self.angle)
                    if angle_diff > 180:
                        angle_diff = 360 - angle_diff
                    
                    if angle_diff < 70 and dist < TILE_SIZE * 1.5:  # Close ahead
                        npc_ahead = True
                        break
            
            if npc_ahead:
                self._wait_timer += dt
                if self._wait_timer < 4.0:  # Wait 4 seconds max
                    should_stop = True
                else:
                    # After timeout, move very slowly
                    speed_mult = min(speed_mult, 0.2)
            else:
                self._wait_timer = 0.0
        
        # Check for pedestrians ONLY in the NEXT BLOCK's crosswalk - MUST STOP
        if not should_stop and pedestrian_positions and crosswalk_positions:
            # Get next cell crosswalk check
            next_cell = (next_row, next_col)
            is_next_crosswalk = next_cell in crosswalk_positions
            
            if is_next_crosswalk:
                # Only check pedestrians who are ACTUALLY ON the next crosswalk
                next_cw_x = next_col * TILE_SIZE + TILE_SIZE / 2
                next_cw_y = next_row * TILE_SIZE + TILE_SIZE / 2
                
                for ped_x, ped_y in pedestrian_positions:
                    # First: Check if pedestrian's GRID POSITION is on a crosswalk
                    ped_grid_col = int(ped_x / TILE_SIZE)
                    ped_grid_row = int(ped_y / TILE_SIZE)
                    ped_grid_pos = (ped_grid_row, ped_grid_col)
                    
                    # CRITICAL: Only care if pedestrian is ON a crosswalk (not in building area)
                    if ped_grid_pos not in crosswalk_positions:
                        continue  # Pedestrian is NOT on any crosswalk, ignore them
                    
                    # Check if pedestrian is in/near the NEXT crosswalk specifically
                    ped_dist_to_next_cw = math.sqrt((ped_x - next_cw_x) ** 2 + (ped_y - next_cw_y) ** 2)
                    if ped_dist_to_next_cw < TILE_SIZE * 0.8:  # Must be very close to next crosswalk
                        # Check if pedestrian is ahead of vehicle
                        dist = math.sqrt((self.x - ped_x) ** 2 + (self.y - ped_y) ** 2)
                        if dist < TILE_SIZE * 2.5:
                            dx = ped_x - self.x
                            dy = ped_y - self.y
                            angle_to_ped = math.degrees(math.atan2(dx, -dy)) % 360
                            angle_diff = abs(angle_to_ped - self.angle)
                            if angle_diff > 180:
                                angle_diff = 360 - angle_diff
                            
                            if angle_diff < 70:  # Pedestrian ahead in crosswalk
                                should_stop = True
                                break
        
        # If should stop, do it and return early
        if should_stop:
            self._is_waiting = True
            self._is_moving = False
            self._brake_lights = True
            self._decelerate(dt)
            self._update_idle_animation(dt)
            return False
        
        # Calculate speed multiplier for crosswalks AHEAD (slow down only if pedestrians present)
        if crosswalk_positions and pedestrian_positions:
            for cw_row, cw_col in crosswalk_positions:
                cw_x = cw_col * TILE_SIZE + TILE_SIZE / 2
                cw_y = cw_row * TILE_SIZE + TILE_SIZE / 2
                dist = math.sqrt((self.x - cw_x) ** 2 + (self.y - cw_y) ** 2)
                
                if dist < TILE_SIZE * 3:  # Check 3 tiles ahead
                    # Check if crosswalk is AHEAD
                    dx = cw_x - self.x
                    dy = cw_y - self.y
                    angle_to_cw = math.degrees(math.atan2(dx, -dy)) % 360
                    angle_diff = abs(angle_to_cw - self.angle)
                    if angle_diff > 180:
                        angle_diff = 360 - angle_diff
                    
                    if angle_diff < 60:  # Crosswalk is ahead
                        # Check if there's a pedestrian ON this crosswalk
                        has_pedestrian_on_crosswalk = False
                        for ped_x, ped_y in pedestrian_positions:
                            # Check pedestrian's grid position
                            ped_grid_col = int(ped_x / TILE_SIZE)
                            ped_grid_row = int(ped_y / TILE_SIZE)
                            ped_grid_pos = (ped_grid_row, ped_grid_col)
                            
                            # If pedestrian is ON this crosswalk
                            if ped_grid_pos == (cw_row, cw_col):
                                has_pedestrian_on_crosswalk = True
                                break
                        
                        # Only slow down if pedestrian is present on crosswalk
                        # README spec: 4 blocks → 75%, 1 block → 35% speed
                        if has_pedestrian_on_crosswalk:
                            if dist < TILE_SIZE * 1.0:  # 1 block away
                                speed_mult = min(speed_mult, 0.35)
                            elif dist < TILE_SIZE * 2.0:  # 2 blocks away
                                speed_mult = min(speed_mult, 0.50)
                            elif dist < TILE_SIZE * 3.0:  # 3 blocks away
                                speed_mult = min(speed_mult, 0.65)
                            elif dist < TILE_SIZE * 4.0:  # 4 blocks away
                                speed_mult = min(speed_mult, 0.75)
        
        # Update state
        self._is_waiting = False
        self._is_moving = True
        self._brake_lights = speed_mult < 0.6
        
        # Accelerate with speed limit
        self._accelerate(dt, speed_mult)
        
        # Move toward target
        self._move_toward_target(dt)
        
        # Check if reached current target
        dist = self._distance_to_target()
        if dist < 3:
            # Advance to next cell
            self._path_index += 1
            reached_node = True
            
            if self._path_index < len(self._path):
                next_row, next_col = self._path[self._path_index]
                self._target_x = next_col * TILE_SIZE + TILE_SIZE / 2
                self._target_y = next_row * TILE_SIZE + TILE_SIZE / 2
                
                # Update direction for next segment
                if self._path_index < len(self._path) - 1:
                    after_row, after_col = self._path[self._path_index + 1]
                    self._update_direction(next_row, next_col, after_row, after_col)
        
        # Update dust emission
        self._update_dust_emission(dt)
        
        # Update animation (wobble, tilt)
        self._update_movement_animation(dt)
        
        return reached_node
    
    def _accelerate(self, dt, speed_mult=1.0):
        """Apply acceleration with optional speed limit."""
        max_vel = self._max_velocity * speed_mult
        
        # If current velocity is higher than target, decelerate
        if self._velocity > max_vel:
            self._velocity -= VEHICLE_DECELERATION * dt * 2
            self._velocity = max(max_vel, self._velocity)
        else:
            self._velocity += VEHICLE_ACCELERATION * dt
            self._velocity = min(self._velocity, max_vel)
        
        self._acceleration_state = min(1, self._acceleration_state + dt * 3)
    
    def _decelerate(self, dt):
        """Apply deceleration/braking."""
        self._velocity -= VEHICLE_DECELERATION * dt
        self._velocity = max(0, self._velocity)
        self._acceleration_state = max(-1, self._acceleration_state - dt * 5)
    
    def _move_toward_target(self, dt):
        """Move toward target position using velocity."""
        dx = self._target_x - self.x
        dy = self._target_y - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        
        if dist > 0.1:
            # Calculate movement
            move_dist = self._velocity * dt
            move_dist = min(move_dist, dist)  # Don't overshoot
            
            self.x += (dx / dist) * move_dist
            self.y += (dy / dist) * move_dist
        else:
            self.x = self._target_x
            self.y = self._target_y
        
        # Smooth rotation
        self._interpolate_rotation(dt)
    
    def _interpolate_rotation(self, dt):
        """Smoothly interpolate rotation toward target."""
        angle_diff = self._target_angle - self.angle
        
        # Normalize to -180 to 180
        while angle_diff > 180:
            angle_diff -= 360
        while angle_diff < -180:
            angle_diff += 360
        
        # Lerp
        self.angle += angle_diff * VEHICLE_LERP_SPEED * dt
        self.angle = self.angle % 360
    
    def _update_direction(self, from_row, from_col, to_row, to_col):
        """Update target rotation based on direction."""
        dr = 0 if to_row == from_row else (1 if to_row > from_row else -1)
        dc = 0 if to_col == from_col else (1 if to_col > from_col else -1)
        
        self._target_angle = DIRECTION_ANGLES.get((dr, dc), self.angle)
    
    def _distance_to_target(self):
        """Calculate distance to current target."""
        dx = self._target_x - self.x
        dy = self._target_y - self.y
        return math.sqrt(dx * dx + dy * dy)
    
    # =========================================================================
    # ANIMATION
    # =========================================================================
    
    def _update_idle_animation(self, dt):
        """Update wobble animation when idle/waiting."""
        self._wobble_time += dt * VEHICLE_WOBBLE_SPEED
        
        # Gentle sinusoidal wobble
        self._wobble_offset_x = math.sin(self._wobble_time) * VEHICLE_WOBBLE_AMOUNT * 0.5
        self._wobble_offset_y = math.cos(self._wobble_time * 0.7) * VEHICLE_WOBBLE_AMOUNT * 0.3
        
        # Decay tilt when stopped
        self._tilt_amount *= 0.9
    
    def _update_movement_animation(self, dt):
        """Update animations while moving."""
        # Reduce wobble when moving
        self._wobble_offset_x *= 0.9
        self._wobble_offset_y *= 0.9
        
        # Body tilt based on acceleration
        target_tilt = self._acceleration_state * VEHICLE_TILT_AMOUNT
        self._tilt_amount += (target_tilt - self._tilt_amount) * dt * 8
    
    def _update_dust_emission(self, dt):
        """Update dust particle emission."""
        if self._velocity > self._max_velocity * 0.3:
            self._dust_accumulator += VEHICLE_DUST_RATE * (self._velocity / self._max_velocity)
            
            if self._dust_accumulator >= 1:
                self._dust_accumulator -= 1
                self.emit_dust = True
    
    # =========================================================================
    # UTILITY
    # =========================================================================
    
    def get_progress(self):
        """Get path progress as 0-1."""
        if not self._path or len(self._path) <= 1:
            return 1.0 if self._arrived else 0.0
        return self._path_index / (len(self._path) - 1)
    
    def get_dust_spawn_position(self):
        """Get position for dust particle spawn (behind vehicle)."""
        angle_rad = math.radians(self.angle + 180)
        offset = 20
        spawn_x = self.x + math.sin(angle_rad) * offset
        spawn_y = self.y - math.cos(angle_rad) * offset
        return (spawn_x, spawn_y)
