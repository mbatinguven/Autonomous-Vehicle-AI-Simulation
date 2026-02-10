"""
simulation.py - Main game simulation with cinematic rendering.

Coordinates all systems:
- Camera with smooth follow and zoom
- Layered rendering with post-processing
- Particle effects
- Dynamic lighting
- Audio management
- Path computation via algorithms
"""

import pygame
import os

from constants import (
    FPS, TILE_SIZE, COLORS, DEFAULT_SETTINGS,
    ALGO_BFS, ALGO_GREEDY, ALGO_ASTAR,
    SOUND_CLICK, SOUND_LIGHT_CHANGE, SOUND_GOAL, SOUND_ERROR,
    SOUND_AMBIENT, SOUND_ENGINE,
    BLOOM_ENABLED, PARTICLES_ENABLED, MINIMAP_ENABLED,
)
from grid import Grid
from agent import Agent
from traffic_light import TrafficLightManager
from camera import Camera, CameraController
from renderer import Renderer
from particles import ParticleSystem
from lighting import LightingSystem
from postprocess import PostProcessor
from ui import StatusPanel, Minimap, ControlsHint, ToastManager, FontManager
from algorithms import compute_path
from npc import NPCManager
from sensor import Sensor, SensorVisualizer
from dynamic_obstacles import DynamicObstacleManager, DynamicObstacleRenderer
from pedestrian import PedestrianManager, PedestrianRenderer


class AudioManager:
    """Manages game audio and sound effects."""
    
    def __init__(self):
        self.enabled = True
        self.master_volume = 0.8
        self.sfx_volume = 0.6
        self.music_volume = 0.3
        
        self._sounds = {}
        self._music_playing = False
        
        self._load_sounds()
    
    def _load_sounds(self):
        """Load sound effects."""
        sounds = {
            "click": SOUND_CLICK,
            "light": SOUND_LIGHT_CHANGE,
            "goal": SOUND_GOAL,
            "error": SOUND_ERROR,
        }
        
        for name, path in sounds.items():
            if os.path.exists(path):
                try:
                    self._sounds[name] = pygame.mixer.Sound(path)
                except:
                    pass
    
    def play(self, name):
        """Play a sound effect."""
        if not self.enabled or name not in self._sounds:
            return
        try:
            sound = self._sounds[name]
            sound.set_volume(self.master_volume * self.sfx_volume)
            sound.play()
        except:
            pass
    
    def update_volumes(self, master=None, sfx=None, music=None):
        """Update volume levels."""
        if master is not None:
            self.master_volume = master
        if sfx is not None:
            self.sfx_volume = sfx
        if music is not None:
            self.music_volume = music


class Simulation:
    """
    Main simulation class with all cinematic features.
    """
    
    def __init__(self, screen, settings=None):
        """
        Initialize simulation.
        
        Args:
            screen: Pygame display surface
            settings: Optional settings dict
        """
        self.screen = screen
        self.width = screen.get_width()
        self.height = screen.get_height()
        
        self.settings = settings or DEFAULT_SETTINGS.copy()
        
        # Initialize fonts
        FontManager.init()
        
        # Core systems
        self.grid = Grid()
        self.agent = Agent()
        self.traffic_manager = TrafficLightManager()
        self.npc_manager = NPCManager()
        
        # Sensor system
        self.sensor = Sensor(range_distance=4, fov_angle=70)
        self.sensor_viz = SensorVisualizer()
        self.sensor_viz.visible = False  # Toggle with 'V' key
        
        # Dynamic obstacles
        self.dynamic_obstacles = DynamicObstacleManager()
        self.dynamic_obstacle_renderer = DynamicObstacleRenderer()
        self.dynamic_obstacles.on_obstacle_changed = self._on_dynamic_obstacle_change
        
        # Pedestrian system
        self.pedestrians = PedestrianManager()
        self.pedestrian_renderer = PedestrianRenderer()
        self.pedestrians.setup_from_grid(self.grid.get_data())
        
        # Camera
        self.camera = Camera(self.width, self.height)
        self.camera_controller = CameraController(self.camera)
        self.camera.center_on_grid(self.grid.cols, self.grid.rows, immediate=True)
        self.camera.set_bounds(0, 0, self.grid.cols * TILE_SIZE, self.grid.rows * TILE_SIZE)
        
        # Rendering
        self.renderer = Renderer(self.width, self.height)
        self.post_processor = PostProcessor(self.width, self.height)
        self.lighting = LightingSystem(self.width, self.height)
        self.particles = ParticleSystem()
        
        # Apply settings
        self.post_processor.bloom_enabled = self.settings.get("bloom_enabled", BLOOM_ENABLED)
        self.particles.enabled = self.settings.get("particles_enabled", PARTICLES_ENABLED)
        
        # UI
        self.status_panel = StatusPanel(20, 20)
        self.minimap = Minimap(self.width, self.height)
        self.minimap.visible = self.settings.get("minimap_enabled", MINIMAP_ENABLED)
        self.controls_hint = ControlsHint(self.width, self.height)
        self.toast_manager = ToastManager(self.width, self.height)
        self.ui_visible = True  # Toggle with U key
        
        # Audio
        self.audio = AudioManager()
        
        # Game state
        self.clock = pygame.time.Clock()
        self.fps = 60
        self.running = True
        self.paused = False
        
        # Algorithm
        self.current_algo = ALGO_ASTAR
        self.path = []
        
        self.waiting_at_goal = False # Hedefte bekleme modu açık mı?
        self.goal_timer = 0.0        # Süreyi sayacak sayaç
        # Input
        self.hover_cell = None
        self.edit_mode = "obstacle"
        
        # Initialize
        self._sync_traffic_lights()
        self._recalculate_path()
        
        # Create dust emitter for vehicle
        self._dust_emitter = self.particles.create_dust_emitter()
        
        # Show welcome toast
        self.toast_manager.show("Welcome to Mini City!", 3.0, COLORS["ui_accent"])
    
    def _sync_traffic_lights(self):
        """Sync traffic lights with grid."""
        positions = self.grid.find_traffic_lights()
        self.traffic_manager.sync_with_grid(positions)
        
        # Update lighting
        self.lighting.clear_traffic_lights()
        for pos in positions:
            world_x = pos[1] * TILE_SIZE + TILE_SIZE // 2
            world_y = pos[0] * TILE_SIZE + TILE_SIZE // 2
            self.lighting.add_traffic_light(world_x, world_y)
    
    def _recalculate_path(self, from_current_position=False):
        """
        Recalculate path with current algorithm.
        
        Args:
            from_current_position: If True, calculate from agent's current position
                                   instead of start marker
        """
        goal = self.grid.find_goal()
        
        # Determine start position
        if from_current_position and self.agent.has_path:
            # Use agent's current grid position
            start = self.agent.grid_position
        else:
            # Use grid's start marker
            start = self.grid.find_start()
        
        # Get grid data and apply dynamic obstacles
        grid_data = self.grid.get_data()
        blocked = self.dynamic_obstacles.get_blocked_positions()
        
        # Create modified grid with dynamic obstacles
        modified_grid = [row[:] for row in grid_data]
        for r, c in blocked:
            if 0 <= r < len(modified_grid) and 0 <= c < len(modified_grid[0]):
                modified_grid[r][c] = 1  # Mark as obstacle
        
        self.path = compute_path(
            self.current_algo,
            modified_grid,
            start,
            goal
        )
        
        if self.path:
            if from_current_position:
                # Don't reset agent position, just update path
                self.agent.continue_with_new_path(self.path)
            else:
                self.agent.set_path(self.path)
        elif start and goal:
            self.audio.play("error")
            self.toast_manager.show("No path found!", 2.0, COLORS["ui_error"])
    
    def _on_dynamic_obstacle_change(self):
        """Called when dynamic obstacles change."""
        self._recalculate_path(from_current_position=True)
        self.toast_manager.show("Road condition changed!", 1.5, COLORS["ui_warning"])
    
    def handle_events(self):
        """Process input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return "quit"
            
            elif event.type == pygame.KEYDOWN:
                result = self._handle_key(event.key)
                if result:
                    return result
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:  # Scroll up
                    self.camera_controller.handle_scroll(1)
                elif event.button == 5:  # Scroll down
                    self.camera_controller.handle_scroll(-1)
                else:
                    self._handle_mouse_click(event.button, event.pos)
            
            elif event.type == pygame.MOUSEMOTION:
                self._update_hover(event.pos)
        
        return None
    
    def _handle_key(self, key):
        """Handle keyboard input."""
        # -----------------------------------------------------------
        # 1-2-3: ALGORİTMA DEĞİŞTİRME (Oyun dururken de çalışır)
        # -----------------------------------------------------------
        if key == pygame.K_1:
            self.current_algo = ALGO_BFS
            # Oyun durmuş olsa bile yolu tekrar hesapla ve ekrana çiz
            self._recalculate_path(from_current_position=True)
            self.audio.play("click")
            self.toast_manager.show(f"Algorithm: {ALGO_BFS}", 1.5)
        
        elif key == pygame.K_2:
            self.current_algo = ALGO_GREEDY
            self._recalculate_path(from_current_position=True)
            self.audio.play("click")
            self.toast_manager.show(f"Algorithm: {ALGO_GREEDY}", 1.5)
        
        elif key == pygame.K_3:
            self.current_algo = ALGO_ASTAR
            self._recalculate_path(from_current_position=True)
            self.audio.play("click")
            self.toast_manager.show(f"Algorithm: {ALGO_ASTAR}", 1.5)
        
        # -----------------------------------------------------------
        # SPACE: SADECE BAŞLATMA VE DURDURMA (PAUSE TOGGLE)
        # -----------------------------------------------------------
        elif key == pygame.K_SPACE:
            # Eğer oyun zaten durmuşsa (PAUSED) -> BAŞLAT
            if self.paused:
                self.paused = False
                self.toast_manager.show("Simülasyon Başladı! 🚀", 1.5, COLORS["ui_success"])
            # Eğer oyun akıyorsa -> DURDUR (İstersen burayı kapatabilirsin)
            else:
                self.paused = True
                self.toast_manager.show("Simülasyon Durduruldu ⏸️", 1.5, COLORS["ui_warning"])
            
            self.audio.play("click")
        # L - Last Start (Aracı son belirlenen başlangıç noktasına ışınla)
        elif key == pygame.K_l:
            self.paused = True  # Oyunu durdur ki hemen kaçmasın
            self._recalculate_path(from_current_position=False) # False = Başlangıç noktasına dön
            self.audio.play("click")
            self.toast_manager.show("Başlangıca Dönüldü ↩️ SPACE ile Başlat", 2.0, COLORS["ui_accent"])
        # -----------------------------------------------------------
        # DİĞER KONTROLLER
        # -----------------------------------------------------------
        elif key == pygame.K_t:
            self.edit_mode = "traffic"
            self.toast_manager.show("Edit: Traffic Lights", 1.0)
        elif key == pygame.K_o:
            self.edit_mode = "obstacle"
            self.toast_manager.show("Edit: Obstacles", 1.0)
        
        elif key == pygame.K_r: # RESET
            self.grid.reset()
            self._sync_traffic_lights()
            self.npc_manager.clear()
            self.dynamic_obstacles.clear()
            self.pedestrians.clear()
            self.pedestrians.setup_from_grid(self.grid.get_data())
            self._recalculate_path()
            self.audio.play("click")
            self.toast_manager.show("Map Reset", 1.5)
            self.paused = False # Resetlenince hareket başlasın mı? İstersen True yap.
        
        elif key == pygame.K_n: # RANDOM MAP
            import random
            self.grid.generate_random(seed=random.randint(0, 99999))
            self._sync_traffic_lights()
            self.npc_manager.clear()
            self.dynamic_obstacles.clear()
            self.pedestrians.clear()
            self.pedestrians.setup_from_grid(self.grid.get_data())
            self._recalculate_path()
            self.audio.play("click")
            self.toast_manager.show("New Random Map", 1.5)
        
        elif key == pygame.K_m:
            self.minimap.toggle()
            self.audio.play("click")
        
        elif key == pygame.K_u:
            self.ui_visible = not self.ui_visible
            self.audio.play("click")
        
        elif key == pygame.K_b:
            enabled = self.post_processor.toggle_bloom()
            self.toast_manager.show(f"Bloom: {'ON' if enabled else 'OFF'}", 1.0)
        
        elif key == pygame.K_v:
            self.sensor_viz.visible = not self.sensor_viz.visible
            self.toast_manager.show(f"Sensor View: {'ON' if self.sensor_viz.visible else 'OFF'}", 1.0)
        
        elif key == pygame.K_d:
            enabled = self.dynamic_obstacles.toggle_spawning()
            self.toast_manager.show(f"Dynamic Obstacles: {'ON' if enabled else 'OFF'}", 1.0)
        
        elif key == pygame.K_F11:
            return "toggle_fullscreen"
        
        elif key == pygame.K_ESCAPE:
            return "pause"
        
        return None
    
    def _handle_mouse_click(self, button, pos):
        """Handle mouse clicks."""
        cell = self.camera.screen_to_grid(pos[0], pos[1], self.grid.rows, self.grid.cols)
        
        if not cell:
            return
        
        row, col = cell
        changed = False
        
        # Left click
        if button == 1:
            if self.edit_mode == "obstacle":
                changed = self.grid.toggle_obstacle(row, col)
            elif self.edit_mode == "traffic":
                changed = self.grid.toggle_traffic_light(row, col)
        
        # Right click - set start
        elif button == 3:
            changed = self.grid.set_start(row, col)
        
        # Middle click - set goal
        elif button == 2:
            changed = self.grid.set_goal(row, col)
        
        if changed:
            self.audio.play("click")
            self._sync_traffic_lights()
            self.npc_manager.refresh_roads(self.grid.get_data())
            self.pedestrians.setup_from_grid(self.grid.get_data())
            
            # Sağ tık (3) ise başlangıç noktası değişmiştir, aracı oraya ışınla (resetle)
            # Diğer durumlarda araç olduğu yerden devam etsin
            force_reset = (button == 3)
            if force_reset: 
                self.paused = True # Sağ tık yapınca oyunu dondur
                self.toast_manager.show("Başlangıç değişti. SPACE ile başlat.", 2.0)
            self._recalculate_path(from_current_position=not force_reset)
    
    def _update_hover(self, pos):
        """Update hover cell."""
        self.hover_cell = self.camera.screen_to_grid(
            pos[0], pos[1], self.grid.rows, self.grid.cols
        )
    
    def update(self, dt):
        """Update simulation state."""
        if self.paused:
            return
        
        # Update traffic lights
        self.traffic_manager.update(dt)
        
        # Update dynamic obstacles
        player_grid = self.agent.grid_position
        self.dynamic_obstacles.update(dt, self.grid.get_data(), player_grid)
        
        # Play sound on light change
        if self.traffic_manager.state_changed:
            self.audio.play("light")
            # Spawn sparks
            for pos in self.traffic_manager.changed_positions:
                wx = pos[1] * TILE_SIZE + TILE_SIZE - 16
                wy = pos[0] * TILE_SIZE + 32
                self.particles.burst_sparks(wx, wy, 12)
        
        # Get positions for collision detection
        def is_red_at(pos):
            return self.traffic_manager.is_red_at(pos)
        
        npc_world_positions = self.npc_manager.get_world_positions()
        crosswalk_positions = self.pedestrians.get_crosswalk_positions()
        pedestrian_positions = self.pedestrians.get_positions()
        
        # Update agent with all collision info
        self.agent.update(
            dt, is_red_at,
            npc_positions=npc_world_positions,
            crosswalk_positions=crosswalk_positions,
            pedestrian_positions=pedestrian_positions
        )
        
        # Update NPC vehicles with grid-based collision
        player_pos = (self.agent.x, self.agent.y)
        self.npc_manager.update(
            dt, self.grid.get_data(), is_red_at, player_pos
        )
        
        # Update pedestrians
        all_vehicle_positions = [(self.agent.x, self.agent.y)]
        all_vehicle_positions.extend(npc_world_positions)
        self.pedestrians.update(dt, all_vehicle_positions, self.grid.get_data())
        
        # Store pedestrian positions for sensor
        self.pedestrian_positions = pedestrian_positions
        
        # Update sensor (for visualization only, agent handles collision internally)
        self.sensor.scan(
            self.agent.x, self.agent.y, self.agent.angle,
            self.grid.get_data(),
            npc_world_positions,
            self.pedestrian_positions
        )
        
        # Camera follow vehicle
        self.camera_controller.set_follow_target(self.agent)
        self.camera_controller.update(dt)
        
        # Update dust emitter
        if self.agent.emit_dust:
            spawn_x, spawn_y = self.agent.get_dust_spawn_position()
            self._dust_emitter.set_position(spawn_x, spawn_y)
            self._dust_emitter.direction = self.agent.angle
            self._dust_emitter.speed_factor = self.agent.speed_normalized
            self._dust_emitter.active = True
        else:
            self._dust_emitter.active = False
        
        # Update particles
        self.particles.update(dt)
        
        # Update lighting
        self.lighting.vehicle_light.set_position(self.agent.x, self.agent.y)
        self.lighting.vehicle_light.set_direction(self.agent.angle)
        self.lighting.update(dt)
        
        # Update renderer animations
        self.renderer.update(dt)
        
        # Update UI
        self.toast_manager.update(dt)
        
        
        # Check for goal reached (HEDEF KONTROLÜ VE OTO-RESET)
       # -----------------------------------------------------------
        # HEDEF KONTROLÜ VE OTOMATİK DEVAM ETME (LOOP)
        # -----------------------------------------------------------
        
        # 1. Hedefe yeni vardıysa (ve henüz bekleme moduna girmediyse)
        if self.agent.at_goal and self.agent.status == "Arrived" and not self.waiting_at_goal:
            self.waiting_at_goal = True   # Bekleme modunu aç
            self.goal_timer = 0.0         # Sayacı sıfırla
            self.audio.play("goal")       # Sesi çal
            self.toast_manager.show("Hedefe Varıldı! 2sn Bekleniyor... ⏳", 2.0, COLORS["ui_success"])

        # 2. Eğer bekleme modundaysak süreyi say
        if self.waiting_at_goal:
            self.goal_timer += dt  # Geçen zamanı ekle
            
            # Süre doldu mu? (Buradaki 2.0 saniyedir, istersen değiştir)
            if self.goal_timer >= 2.0:
                self.waiting_at_goal = False # Beklemeyi bitir
                self.goal_timer = 0.0
                
                # Aracı başlangıca ışınla (Reset)
                self._recalculate_path(from_current_position=False)
                
                # SİMÜLASYON DURMASIN, DEVAM ETSİN
                self.paused = False 
                
                self.toast_manager.show("Yeni Tur Başlıyor! 🔄", 1.5, COLORS["ui_accent"])
    
    def render(self):
        """Render the simulation."""
        # Clear
        self.screen.fill(COLORS["background"])
        
        # Create working surface
        game_surface = pygame.Surface((self.width, self.height))
        
        # Background
        self.renderer.render_background(game_surface, self.camera)
        
        # Grid tiles
        self.renderer.render_grid(game_surface, self.grid.get_data(), self.camera)
        
        # Path
        self.renderer.render_path(game_surface, self.path, self.agent.path_index, self.camera)
        
        # Traffic lights
        for light in self.traffic_manager.lights:
            if light.position:
                self.renderer.render_traffic_light(
                    game_surface,
                    light.position[0],
                    light.position[1],
                    light.state,
                    self.camera
                )
        
        # Dynamic obstacles
        self.dynamic_obstacle_renderer.render_all(
            game_surface,
            self.dynamic_obstacles.obstacles,
            self.camera
        )
        
        # Pedestrians and crosswalks
        self.pedestrian_renderer.render_all(
            game_surface,
            self.pedestrians,
            self.camera
        )
        
        # NPC Vehicles
        for npc in self.npc_manager.vehicles:
            if npc.active:
                self.renderer.render_npc_vehicle(
                    game_surface,
                    npc.x,
                    npc.y,
                    npc.angle,
                    npc.color,
                    npc.brake_lights,
                    self.camera
                )
        
        # Player Vehicle
        self.renderer.render_vehicle(
            game_surface,
            self.agent.x,
            self.agent.y,
            self.agent.angle,
            self.agent.is_waiting or self.agent.brake_lights_on,
            self.camera
        )
        
        # Sensor visualization (if enabled)
        if self.sensor_viz.visible:
            self.sensor_viz.render(game_surface, self.sensor, self.camera)
        
        # Particles
        cam_x, cam_y = self.camera.x - self.width // 2, self.camera.y - self.height // 2
        self.particles.render(game_surface, cam_x, cam_y)
        
        # Post-processing
        processed = self.post_processor.process(game_surface)
        self.screen.blit(processed, (0, 0))
        
        # UI (no post-processing) - toggle with U key
        if self.ui_visible:
            self.status_panel.update_stats(
                self.current_algo,
                self.fps,
                self.agent.status,
                len(self.path),
                npc_count=len(self.npc_manager.vehicles),
                pedestrian_count=len(self.pedestrians.pedestrians)
            )
            self.status_panel.draw(self.screen)
            
            # Minimap
            self.minimap.update(self.grid.get_data(), self.agent.grid_position)
            self.minimap.draw(self.screen)
        
        # Toasts
        self.toast_manager.draw(self.screen)
        
        # Hover indicator
        if self.hover_cell:
            row, col = self.hover_cell
            sx, sy = self.camera.grid_to_screen(row, col)
            hover_surf = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            hover_surf.fill((255, 255, 255, 30))
            self.screen.blit(hover_surf, (sx - TILE_SIZE // 2, sy - TILE_SIZE // 2))
        
        pygame.display.flip()
    
    def run(self):
        """Main game loop."""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.fps = int(self.clock.get_fps())
            
            result = self.handle_events()
            if result:
                return result
            
            self.update(dt)
            self.render()
        
        return "quit"
    
    def get_screenshot(self):
        """Get current screen as surface."""
        return self.screen.copy()
    
    def resize(self, width, height):
        """Handle window resize."""
        self.width = width
        self.height = height
        self.camera.resize(width, height)
        self.renderer.resize(width, height)
        self.post_processor.resize(width, height)
        self.lighting.resize(width, height)
        self.minimap.reposition(width, height)
        self.controls_hint.reposition(width, height)
