#
# A basic Pygame 2D RPG prototype with a start menu, character movement,
# a simple dungeon with enemies and NPCs, and life points.
#
import pygame
import sys
import numpy as np
import random
import math

# --- Initialization ---
pygame.init()
pygame.mixer.init() # Initialize the sound mixer

# --- Constants ---
SCREEN_INFO = pygame.display.Info()
SCREEN_WIDTH = SCREEN_INFO.current_w
SCREEN_HEIGHT = SCREEN_INFO.current_h
# Calculate TILE_SIZE dynamically to fit the screen
TILE_SIZE = min(SCREEN_WIDTH // 20, SCREEN_HEIGHT // 14)
PLAYER_SIZE = TILE_SIZE // 2  # New constant for smaller player size
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 200, 0)
DARK_GREEN = (0, 150, 0)
WALL_COLOR = (100, 100, 100)
FLOOR_COLOR = (50, 50, 50)
PLAYER_COLOR = (255, 0, 0)
NPC_COLOR = (0, 0, 255)
ENEMY_COLOR = (200, 50, 50) # Red color for enemies
TORCH_COLOR = (255, 255, 0)
DOOR_COLOR = (139, 69, 19) # SaddleBrown for the door
KEY_COLOR = (255, 215, 0) # Gold for the key
LIFE_BAR_COLOR = (0, 255, 0) # Green for life bar
LIFE_BAR_BG_COLOR = (255, 0, 0) # Red for life bar background
STAMINA_BAR_COLOR = (0, 191, 255) # Deep Sky Blue
STAMINA_BAR_BG_COLOR = (25, 25, 25) # Dark gray

# NEW POWER-UP COLORS
FOG_CLEAR_COLOR = (128, 0, 128) # Purple
ENEMY_BOMB_COLOR = (255, 255, 255) # White
HEAL_COLOR = (0, 255, 0) # Green

# --- Game States ---
GAME_STATES = {
    "MENU": 0,
    "GAME": 1,
    "DIALOGUE": 2,
    "GAME_OVER": 3,
    "OPTIONS": 4, # New state for the options menu
    "AUDIO_OPTIONS": 5, # New state for audio options
    "CONTROLS_OPTIONS": 6, # New state for controls options
    "PAUSED": 7, # New state for the pause menu
    "REBINDING_KEY": 8, # New state for key re-binding
}

# Create the display in fullscreen mode
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("My Story-Driven RPG")
clock = pygame.time.Clock()

# Set initial game state to the menu
current_state = GAME_STATES["MENU"]
current_level = 1

# --- Text and Fonts ---
font = pygame.font.Font(None, 74)
small_font = pygame.font.Font(None, 40)
dialogue_font = pygame.font.Font(None, 24)

# --- Keybindings Dictionary ---
# A dictionary to hold the current keybindings.
# This makes it easy to change them dynamically.
KEY_BINDINGS = {
    "move_up": pygame.K_w,
    "move_down": pygame.K_s,
    "move_left": pygame.K_a,
    "move_right": pygame.K_d,
    "sprint": pygame.K_LSHIFT,
    "interact": pygame.K_SPACE,
}

# Variable to track which key is being re-bound
rebind_target = None

# --- Audio Settings ---
music_volume = 0.5  # Initial volume level (0.0 to 1.0)
is_muted = False    # Flag to check if the game is muted
pygame.mixer.music.set_volume(music_volume)

# --- Sound Effects ---
def generate_unlock_sound():
    """Generates a simple 'unlock' sound effect using two short tones."""
    sample_rate = 44100
    duration = 0.2  # duration in seconds
    frequency1 = 880  # A5
    frequency2 = 1320 # E6

    # Create time arrays for two parts of the sound
    t1 = np.linspace(0., duration, int(sample_rate * duration / 2), False)
    t2 = np.linspace(0., duration, int(sample_rate * duration / 2), False)

    # Generate sine waves for each part
    tone1 = 0.5 * np.sin(2 * np.pi * frequency1 * t1)
    tone2 = 0.5 * np.sin(2 * np.pi * frequency2 * t2)

    # Combine the tones
    sound_data = np.concatenate((tone1, tone2))

    # Scale to 16-bit integer format and convert to bytes
    sound_data_int16 = (sound_data * 32767).astype(np.int16)
    
    # Create the Pygame Sound object
    return pygame.mixer.Sound(sound_data_int16.tobytes())

def generate_damage_sound():
    """Generates a low, quick tone for taking damage."""
    sample_rate = 44100
    duration = 0.1
    frequency = 100 # Low frequency for a 'thud' sound
    t = np.linspace(0., duration, int(sample_rate * duration), False)
    sound_data = 0.5 * np.sin(2 * np.pi * frequency * t)
    sound_data_int16 = (sound_data * 32767).astype(np.int16)
    return pygame.mixer.Sound(sound_data_int16.tobytes())

def generate_collect_sound():
    """Generates a high, pleasant tone for collecting items."""
    sample_rate = 44100
    duration = 0.1
    frequency = 1000 # High frequency
    t = np.linspace(0., duration, int(sample_rate * duration), False)
    sound_data = 0.5 * np.sin(2 * np.pi * frequency * t)
    sound_data_int16 = (sound_data * 32767).astype(np.int16)
    return pygame.mixer.Sound(sound_data_int16.tobytes())
    
def generate_dialogue_sound():
    """Generates a soft, quick 'pop' for dialogue."""
    sample_rate = 44100
    duration = 0.05
    frequency = 500
    t = np.linspace(0., duration, int(sample_rate * duration), False)
    sound_data = 0.3 * np.sin(2 * np.pi * frequency * t) * np.exp(-t * 20) # A little decay
    sound_data_int16 = (sound_data * 32767).astype(np.int16)
    return pygame.mixer.Sound(sound_data_int16.tobytes())

def generate_game_over_sound():
    """Generates a long, descending tone for game over."""
    sample_rate = 44100
    duration = 1.5
    t = np.linspace(0., duration, int(sample_rate * duration), False)
    # Descending frequency from 400Hz to 100Hz
    frequency = 400 * np.exp(-t / 0.5) + 100
    sound_data = 0.5 * np.sin(2 * np.pi * frequency * t)
    sound_data_int16 = (sound_data * 32767).astype(np.int16)
    return pygame.mixer.Sound(sound_data_int16.tobytes())

def generate_level_up_sound():
    """Generates a short, ascending tone for leveling up."""
    sample_rate = 44100
    duration = 0.5
    t = np.linspace(0., duration, int(sample_rate * duration), False)
    # Ascending frequency from 200Hz to 800Hz
    frequency = 200 * np.exp(t * 2)
    sound_data = 0.5 * np.sin(2 * np.pi * frequency * t)
    sound_data_int16 = (sound_data * 32767).astype(np.int16)
    return pygame.mixer.Sound(sound_data_int16.tobytes())

# Generate the sounds once at the start
unlock_sound = generate_unlock_sound()
damage_sound = generate_damage_sound()
collect_sound = generate_collect_sound()
dialogue_sound = generate_dialogue_sound()
game_over_sound = generate_game_over_sound()
level_up_sound = generate_level_up_sound()

# --- Game Classes ---

class Player(pygame.sprite.Sprite):
    """Represents the player character."""
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((PLAYER_SIZE, PLAYER_SIZE))
        self.image.fill(PLAYER_COLOR)
        # Center the player within the tile they spawned on
        self.rect = self.image.get_rect(center=(x + TILE_SIZE/2, y + TILE_SIZE/2))
        self.base_speed = 5 # Increased from 4 to 5 for slightly faster movement
        self.sprint_speed = self.base_speed * 1.75 # Sprint speed is 1.75x base speed
        self.has_key = False
        self.life_points = 100
        self.invulnerable_timer = 0
        self.is_flashing = False
        self.inventory = [] # New list to store collected power-ups
        
        # New stamina system attributes
        self.max_stamina = 100
        self.stamina = self.max_stamina
        self.stamina_drain_rate = 1.5 # How much stamina is lost per frame while sprinting
        self.stamina_recharge_rate = 1 # How much stamina is gained per frame when not sprinting
        self.is_sprinting = False

    def update(self, dx, dy, walls, doors):
        """
        Update player position with collision detection.
        This function now checks for collisions with both walls and locked doors.
        It also handles stamina drain and recharge.
        """
        # Update stamina based on action
        if self.is_sprinting and self.stamina > 0:
            self.stamina -= self.stamina_drain_rate
            if self.stamina < 0:
                self.stamina = 0
                self.is_sprinting = False # Stop sprinting if stamina runs out
        else:
            self.stamina = min(self.max_stamina, self.stamina + self.stamina_recharge_rate)
        
        # Determine the current speed
        current_speed = self.sprint_speed if self.is_sprinting and self.stamina > 0 else self.base_speed

        # Normalize diagonal movement to prevent faster movement
        if dx != 0 and dy != 0:
            dx /= 1.414
            dy /= 1.414
        
        # Apply the determined speed to the movement vectors
        new_dx = dx * current_speed
        new_dy = dy * current_speed

        new_rect = self.rect.copy()
        new_rect.x += new_dx
        new_rect.y += new_dy

        # Check for collision with walls, locked doors, and screen boundaries
        can_move = True
        for wall in walls:
            if new_rect.colliderect(wall):
                can_move = False
                break
        
        # Check for collision with locked doors
        if can_move:
            for door in doors:
                if door.locked and new_rect.colliderect(door.rect):
                    can_move = False
                    break
        
        # Check for screen boundary collision
        if new_rect.left < 0 or new_rect.right > SCREEN_WIDTH or new_rect.top < 0 or new_rect.bottom > SCREEN_HEIGHT:
            can_move = False

        if can_move:
            self.rect.topleft = (new_rect.x, new_rect.y)

        # Update invulnerability timer
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= 1
            # Flash the player to indicate invulnerability
            if self.invulnerable_timer % 10 < 5:
                self.image.fill(WHITE)
            else:
                self.image.fill(PLAYER_COLOR)
        else:
            self.image.fill(PLAYER_COLOR)


class NPC(pygame.sprite.Sprite):
    """Represents a non-player character."""
    def __init__(self, x, y, dialogue, patrol_range=20):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(NPC_COLOR)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.dialogue = dialogue
        self.speed = 1
        
        # Define the patrol area for slight movement
        self.patrol_start = (x, y)
        self.patrol_end = (x + patrol_range, y + patrol_range)

        # Choose a random initial movement direction for both axes
        self.move_direction_x = random.choice([-1, 1])
        self.move_direction_y = random.choice([-1, 1])
    
    def update(self):
        """Update the NPC's position within its patrol area."""
        self.rect.x += self.speed * self.move_direction_x
        self.rect.y += self.speed * self.move_direction_y

        # Reverse direction if hitting horizontal boundaries
        if self.rect.x > self.patrol_end[0] or self.rect.x < self.patrol_start[0]:
            self.move_direction_x *= -1
        # Reverse direction if hitting vertical boundaries
        if self.rect.y > self.patrol_end[1] or self.rect.y < self.patrol_start[1]:
            self.move_direction_y *= -1

class Door(pygame.sprite.Sprite):
    """Represents a door that can transition to another level."""
    def __init__(self, x, y, locked=True):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(DOOR_COLOR)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.locked = locked

class Key(pygame.sprite.Sprite):
    """Represents a key that can be collected."""
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(KEY_COLOR)
        self.rect = self.image.get_rect(topleft=(x, y))

class Enemy(pygame.sprite.Sprite):
    """Represents a moving enemy."""
    def __init__(self, x, y, patrol_range):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(ENEMY_COLOR)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.speed = 2
        
        # Define the patrol area
        self.patrol_start = (x, y)
        self.patrol_end = (x + patrol_range, y + patrol_range)

        # Choose a random initial movement direction for both axes
        self.move_direction_x = random.choice([-1, 1])
        self.move_direction_y = random.choice([-1, 1])

    def update(self):
        """Update the enemy's position within its patrol area."""
        self.rect.x += self.speed * self.move_direction_x
        self.rect.y += self.speed * self.move_direction_y

        # Reverse direction if hitting horizontal boundaries
        if self.rect.x > self.patrol_end[0] or self.rect.x < self.patrol_start[0]:
            self.move_direction_x *= -1
        # Reverse direction if hitting vertical boundaries
        if self.rect.y > self.patrol_end[1] or self.rect.y < self.patrol_start[1]:
            self.move_direction_y *= -1

class Torch(pygame.sprite.Sprite):
    """Represents a static torch light source."""
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE // 2, TILE_SIZE // 2))
        self.image.fill(TORCH_COLOR)
        self.rect = self.image.get_rect(center=(x, y))

class PowerUp(pygame.sprite.Sprite):
    """Represents a collectible power-up."""
    def __init__(self, x, y, color, type):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=(x, y))
        self.type = type

# --- Dungeon Generation ---
def _is_valid_spawn_pos(x, y, layout, padding=1):
    """Checks if a position is a valid floor tile with padding."""
    # Check if the tile is within bounds
    if not (0 < y < len(layout) - 1 and 0 < x < len(layout[0]) - 1):
        return False
    # Check if the tile is a floor
    if layout[y][x] != 0:
        return False
    # Check for padding
    for dy in range(-padding, padding + 1):
        for dx in range(-padding, padding + 1):
            if layout[y + dy][x + dx] != 0:
                return False
    return True


def _generate_simple_dungeon(width, height):
    """Generates a simple, empty square dungeon."""
    layout = [[1 for _ in range(width)] for _ in range(height)]
    # Create the floor
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            layout[y][x] = 0
    return layout

def _generate_maze_dungeon(width, height):
    """Generates a maze using a simplified randomized depth-first search (DFS)."""
    layout = [[1 for _ in range(width)] for _ in range(height)]
    stack = []
    
    # Start at a random even-numbered cell
    start_x = random.randrange(1, width, 2)
    start_y = random.randrange(1, height, 2)
    
    layout[start_y][start_x] = 0
    stack.append((start_x, start_y))

    while stack:
        current_x, current_y = stack.pop()
        
        # Define possible neighbors to move to (2 steps away)
        neighbors = []
        if current_x > 1: neighbors.append((current_x - 2, current_y))
        if current_x < width - 2: neighbors.append((current_x + 2, current_y))
        if current_y > 1: neighbors.append((current_x, current_y - 2))
        if current_y < height - 2: neighbors.append((current_x, current_y + 2))

        unvisited_neighbors = []
        for nx, ny in neighbors:
            if layout[ny][nx] == 1:
                unvisited_neighbors.append((nx, ny))

        if unvisited_neighbors:
            stack.append((current_x, current_y))
            next_x, next_y = random.choice(unvisited_neighbors)
            
            # Carve a path to the neighbor
            wall_x = current_x + (next_x - current_x) // 2
            wall_y = current_y + (next_y - current_y) // 2
            layout[wall_y][wall_x] = 0
            layout[next_y][next_x] = 0
            
            stack.append((next_x, next_y))
            
    return layout

def generate_dungeon(level):
    """Generates a full dungeon with all objects based on the level."""
    # Define a base dungeon size
    width = SCREEN_WIDTH // TILE_SIZE
    height = SCREEN_HEIGHT // TILE_SIZE

    if level == 1:
        layout = _generate_simple_dungeon(width, height)
    else:
        # Increase complexity by creating a maze
        layout = _generate_maze_dungeon(width, height)
    
    # Find all floor tiles to place items on
    floor_tiles = []
    for y in range(1, height - 1):
        for x in range(1, width - 1):
            if layout[y][x] == 0:
                floor_tiles.append((x, y))

    # Place player spawn at a random floor tile
    player_spawn_pos = random.choice(floor_tiles)
    floor_tiles.remove(player_spawn_pos)

    # Place key and NPC at random floor tiles
    key_pos = random.choice(floor_tiles)
    floor_tiles.remove(key_pos)
    
    npc_pos = random.choice(floor_tiles)
    floor_tiles.remove(npc_pos)

    # Place power-ups
    power_ups_to_spawn = []
    if floor_tiles:
        heal_pos = random.choice(floor_tiles)
        floor_tiles.remove(heal_pos)
        power_ups_to_spawn.append({"pos": heal_pos, "type": "heal"})
    if floor_tiles:
        enemy_bomb_pos = random.choice(floor_tiles)
        floor_tiles.remove(enemy_bomb_pos)
        power_ups_to_spawn.append({"pos": enemy_bomb_pos, "type": "enemy_bomb"})
    if floor_tiles:
        fog_clear_pos = random.choice(floor_tiles)
        floor_tiles.remove(fog_clear_pos)
        power_ups_to_spawn.append({"pos": fog_clear_pos, "type": "fog_clear"})
    
    # Place enemies
    num_enemies = min(level + 1, 5) # Increase number of enemies per level
    enemies_to_spawn = []
    for _ in range(num_enemies):
        if not floor_tiles:
            break
        enemy_pos = random.choice(floor_tiles)
        floor_tiles.remove(enemy_pos)
        enemies_to_spawn.append({"pos": enemy_pos, "patrol_range": random.randint(50, 150)})

    # Place torches
    num_torches = 3
    torches_to_spawn = []
    for _ in range(num_torches):
        if not floor_tiles:
            break
        torch_pos = random.choice(floor_tiles)
        floor_tiles.remove(torch_pos)
        torches_to_spawn.append({"pos": torch_pos})

    # Place door at a random wall tile
    door_pos = None
    wall_tiles = []
    for y in range(height):
        for x in range(width):
            if layout[y][x] == 1 and (y == 0 or y == height - 1 or x == 0 or x == width - 1):
                wall_tiles.append((x, y))
    
    door_pos = random.choice(wall_tiles)
    
    # Carve a space for the door
    layout[door_pos[1]][door_pos[0]] = 0
    # To ensure the door is accessible, create a small path to it
    if door_pos[1] == 0:
        layout[1][door_pos[0]] = 0
    elif door_pos[1] == height - 1:
        layout[height - 2][door_pos[0]] = 0
    elif door_pos[0] == 0:
        layout[door_pos[1]][1] = 0
    elif door_pos[0] == width - 1:
        layout[door_pos[1]][width - 2] = 0
    

    return {
        "layout": layout,
        "npcs": [{"pos": npc_pos, "dialogue": "You need to find a key to unlock the door!", "patrol_range": 20}],
        "enemies": enemies_to_spawn,
        "torches": torches_to_spawn,
        "doors": [{"pos": door_pos, "locked": True}],
        "keys": [{"pos": key_pos}],
        "power_ups": power_ups_to_spawn,
        "player_spawn_pos": player_spawn_pos
    }

# NEW FOG OF WAR GLOBAL VARIABLES
TILE_GRID_WIDTH = SCREEN_WIDTH // TILE_SIZE
TILE_GRID_HEIGHT = SCREEN_HEIGHT // TILE_SIZE
visited_tiles = np.zeros((TILE_GRID_HEIGHT, TILE_GRID_WIDTH), dtype=bool)


def load_map(map_data):
    """Loads a new map from the generated map data."""
    global player, walls, npcs, torches, active_dialogue, keys, doors, enemies, visited_tiles, power_ups
    
    # Reset game objects for the new map
    walls = []
    npcs = pygame.sprite.Group()
    torches = pygame.sprite.Group()
    doors = pygame.sprite.Group()
    keys = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    power_ups = pygame.sprite.Group()
    active_dialogue = None
    
    # Reset visited tiles for the new map
    visited_tiles = np.zeros((TILE_GRID_HEIGHT, TILE_GRID_WIDTH), dtype=bool)

    # Populate walls from map layout
    for row_idx, row in enumerate(map_data["layout"]):
        for col_idx, cell in enumerate(row):
            x = col_idx * TILE_SIZE
            y = row_idx * TILE_SIZE
            if cell == 1:
                wall_rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
                walls.append(wall_rect)

    # Place player at the specified spawn position
    spawn_pos = (map_data["player_spawn_pos"][0] * TILE_SIZE, map_data["player_spawn_pos"][1] * TILE_SIZE)
    if player is None:
        player = Player(spawn_pos[0], spawn_pos[1])
    else:
        player.rect.center = (spawn_pos[0] + TILE_SIZE/2, spawn_pos[1] + TILE_SIZE/2)
        player.has_key = False # Reset key on new map
        player.life_points = 100 # Reset life points
        player.inventory = [] # Reset inventory
        player.stamina = player.max_stamina # Refill stamina on new level

    # Create NPCs from map data
    for npc_data in map_data["npcs"]:
        npcs.add(NPC(npc_data["pos"][0] * TILE_SIZE, npc_data["pos"][1] * TILE_SIZE, npc_data["dialogue"], npc_data["patrol_range"]))

    # Create enemies from map data
    for enemy_data in map_data["enemies"]:
        enemies.add(Enemy(enemy_data["pos"][0] * TILE_SIZE, enemy_data["pos"][1] * TILE_SIZE, enemy_data["patrol_range"]))

    # Create torches from map data
    for torch_data in map_data["torches"]:
        torches.add(Torch(torch_data["pos"][0] * TILE_SIZE + TILE_SIZE // 2, torch_data["pos"][1] * TILE_SIZE + TILE_SIZE // 2))

    # Create keys from map data
    for key_data in map_data["keys"]:
        keys.add(Key(key_data["pos"][0] * TILE_SIZE, key_data["pos"][1] * TILE_SIZE))
    
    # Create doors from map data
    for door_data in map_data["doors"]:
        doors.add(Door(door_data["pos"][0] * TILE_SIZE, door_data["pos"][1] * TILE_SIZE, door_data["locked"]))

    # Create power-ups from map data
    for pu_data in map_data["power_ups"]:
        color = None
        if pu_data["type"] == "heal":
            color = HEAL_COLOR
        elif pu_data["type"] == "enemy_bomb":
            color = ENEMY_BOMB_COLOR
        elif pu_data["type"] == "fog_clear":
            color = FOG_CLEAR_COLOR
        if color:
            power_ups.add(PowerUp(pu_data["pos"][0] * TILE_SIZE, pu_data["pos"][1] * TILE_SIZE, color, pu_data["type"]))


# Initial map load
current_dungeon_data = generate_dungeon(current_level)
# Add the 'player' variable initialization here.
player = None
load_map(current_dungeon_data)

# --- Functions for drawing different screens ---

def get_key_name(key_code):
    """Converts a pygame key code to a readable string."""
    return pygame.key.name(key_code).upper()

def draw_menu():
    """Draws the main menu screen."""
    screen.fill(BLACK)
    
    # Title text
    title_text = font.render("A Hero's Journey", True, WHITE)
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4))
    screen.blit(title_text, title_rect)
    
    # Start button text
    start_text = small_font.render("Start Game", True, WHITE)
    start_rect = start_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
    
    # Options button text (new)
    options_text = small_font.render("Options", True, WHITE)
    options_rect = options_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 70))
    
    # Simple button logic: change color on hover
    mouse_pos = pygame.mouse.get_pos()
    
    # Draw Start button
    start_button_color = GREEN if start_rect.inflate(20, 10).collidepoint(mouse_pos) else DARK_GREEN
    pygame.draw.rect(screen, start_button_color, start_rect.inflate(20, 10), border_radius=10)
    screen.blit(start_text, start_rect)
    
    # Draw Options button
    options_button_color = GREEN if options_rect.inflate(20, 10).collidepoint(mouse_pos) else DARK_GREEN
    pygame.draw.rect(screen, options_button_color, options_rect.inflate(20, 10), border_radius=10)
    screen.blit(options_text, options_rect)

def draw_options_menu():
    """Draws the options menu screen."""
    screen.fill(BLACK)
    
    # Title text
    title_text = font.render("Options", True, WHITE)
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4))
    screen.blit(title_text, title_rect)

    # Audio button
    audio_text = small_font.render("Audio", True, WHITE)
    audio_rect = audio_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 50))
    audio_button_color = GREEN if audio_rect.inflate(20, 10).collidepoint(pygame.mouse.get_pos()) else DARK_GREEN
    pygame.draw.rect(screen, audio_button_color, audio_rect.inflate(20, 10), border_radius=10)
    screen.blit(audio_text, audio_rect)

    # Controls button
    controls_text = small_font.render("Controls", True, WHITE)
    controls_rect = controls_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
    controls_button_color = GREEN if controls_rect.inflate(20, 10).collidepoint(pygame.mouse.get_pos()) else DARK_GREEN
    pygame.draw.rect(screen, controls_button_color, controls_rect.inflate(20, 10), border_radius=10)
    screen.blit(controls_text, controls_rect)

    # Back button
    back_text = small_font.render("Back", True, WHITE)
    back_rect = back_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50))
    back_button_color = GREEN if back_rect.inflate(20, 10).collidepoint(pygame.mouse.get_pos()) else DARK_GREEN
    pygame.draw.rect(screen, back_button_color, back_rect.inflate(20, 10), border_radius=10)
    screen.blit(back_text, back_rect)

def draw_audio_menu():
    """Draws a placeholder for the audio settings menu."""
    screen.fill(BLACK)
    
    # Title text
    title_text = font.render("Audio Settings", True, WHITE)
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4))
    screen.blit(title_text, title_rect)

    # Volume Slider
    slider_width = 300
    slider_height = 20
    slider_x = SCREEN_WIDTH / 2 - slider_width / 2
    slider_y = SCREEN_HEIGHT / 2 - 50
    slider_rect = pygame.Rect(slider_x, slider_y, slider_width, slider_height)
    
    # Draw slider background
    pygame.draw.rect(screen, DARK_GREEN, slider_rect, border_radius=5)
    
    # Draw the current volume level bar
    volume_bar_width = slider_width * music_volume
    volume_bar_rect = pygame.Rect(slider_x, slider_y, volume_bar_width, slider_height)
    pygame.draw.rect(screen, GREEN, volume_bar_rect, border_radius=5)
    
    # Draw the slider handle
    handle_x = slider_x + volume_bar_width
    handle_rect = pygame.Rect(handle_x - 5, slider_y - 5, 10, slider_height + 10)
    pygame.draw.rect(screen, WHITE, handle_rect)
    
    # Volume text
    volume_text = small_font.render(f"Volume: {int(music_volume * 100)}%", True, WHITE)
    volume_rect = volume_text.get_rect(center=(SCREEN_WIDTH / 2, slider_y - 30))
    screen.blit(volume_text, volume_rect)

    # Mute button
    mute_text_str = "Unmute" if is_muted else "Mute"
    mute_text = small_font.render(mute_text_str, True, WHITE)
    mute_rect = mute_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 30))
    mute_button_color = GREEN if mute_rect.inflate(20, 10).collidepoint(pygame.mouse.get_pos()) else DARK_GREEN
    pygame.draw.rect(screen, mute_button_color, mute_rect.inflate(20, 10), border_radius=10)
    screen.blit(mute_text, mute_rect)

    # Back button
    back_text = small_font.render("Back", True, WHITE)
    back_rect = back_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 100))
    back_button_color = GREEN if back_rect.inflate(20, 10).collidepoint(pygame.mouse.get_pos()) else DARK_GREEN
    pygame.draw.rect(screen, back_button_color, back_rect.inflate(20, 10), border_radius=10)
    screen.blit(back_text, back_rect)


def draw_controls_menu():
    """Draws the controls settings menu with rebindable keys."""
    screen.fill(BLACK)
    
    # Title text
    title_text = font.render("Controls", True, WHITE)
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 4))
    screen.blit(title_text, title_rect)
    
    # Display the keybinding options
    key_y_start = SCREEN_HEIGHT / 2 - 100
    button_x_start = SCREEN_WIDTH / 2 + 50
    
    for i, (action, key_code) in enumerate(KEY_BINDINGS.items()):
        # Action label
        action_name = action.replace('_', ' ').title()
        action_text = small_font.render(action_name, True, WHITE)
        action_rect = action_text.get_rect(right=SCREEN_WIDTH / 2 - 10, centery=key_y_start + i * 50)
        screen.blit(action_text, action_rect)
        
        # Key button
        key_name = get_key_name(key_code)
        key_text = small_font.render(key_name, True, WHITE)
        
        # Check if this is the key currently being re-bound
        if rebind_target == action:
            key_text = small_font.render("Press a key...", True, WHITE)
            key_button_color = (150, 150, 150) # Gray color to show it's active
        else:
            key_button_color = GREEN if pygame.Rect(button_x_start, action_rect.y - 10, 150, 40).collidepoint(pygame.mouse.get_pos()) else DARK_GREEN
        
        key_rect = key_text.get_rect(left=button_x_start, centery=action_rect.centery)
        key_button_rect = key_rect.inflate(20, 10)
        pygame.draw.rect(screen, key_button_color, key_button_rect, border_radius=10)
        screen.blit(key_text, key_rect)

    # Back button
    back_text = small_font.render("Back", True, WHITE)
    back_rect = back_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 150))
    back_button_color = GREEN if back_rect.inflate(20, 10).collidepoint(pygame.mouse.get_pos()) else DARK_GREEN
    pygame.draw.rect(screen, back_button_color, back_rect.inflate(20, 10), border_radius=10)
    screen.blit(back_text, back_rect)

def draw_game_over():
    """Draws the game over screen."""
    screen.fill(BLACK)
    game_over_text = font.render("Game Over", True, (255, 0, 0))
    game_over_rect = game_over_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
    screen.blit(game_over_text, game_over_rect)

    restart_text = small_font.render("Press R to Restart", True, WHITE)
    restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 100))
    screen.blit(restart_text, restart_rect)
    
def draw_pause_menu():
    """Draws the pause menu screen as a semi-transparent overlay."""
    # Create a semi-transparent surface
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 150)) # Black with 150/255 opacity
    screen.blit(overlay, (0, 0))

    # Title text
    title_text = font.render("Paused", True, WHITE)
    title_rect = title_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 3))
    screen.blit(title_text, title_rect)

    # Resume button
    resume_text = small_font.render("Resume", True, WHITE)
    resume_rect = resume_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
    resume_button_color = GREEN if resume_rect.inflate(20, 10).collidepoint(pygame.mouse.get_pos()) else DARK_GREEN
    pygame.draw.rect(screen, resume_button_color, resume_rect.inflate(20, 10), border_radius=10)
    screen.blit(resume_text, resume_rect)

    # Exit to Main Menu button
    exit_text = small_font.render("Exit to Main Menu", True, WHITE)
    exit_rect = exit_text.get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 60))
    exit_button_color = GREEN if exit_rect.inflate(20, 10).collidepoint(pygame.mouse.get_pos()) else DARK_GREEN
    pygame.draw.rect(screen, exit_button_color, exit_rect.inflate(20, 10), border_radius=10)
    screen.blit(exit_text, exit_rect)

def draw_game():
    """Draws the main game screen with dungeon, player, and NPCs."""
    # Draw the dungeon walls and floor
    screen.fill(FLOOR_COLOR)
    for wall in walls:
        pygame.draw.rect(screen, WALL_COLOR, wall)

    # Draw the doors, keys, and enemies
    doors.draw(screen)
    keys.draw(screen)
    enemies.draw(screen)
    power_ups.draw(screen)

    # Draw the player and NPCs
    npcs.draw(screen)
    screen.blit(player.image, player.rect)
    
    # --- Optimized Lighting Effect ---
    # Create a light mask with a transparent background
    light_mask = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    
    # Add a global ambient light that makes the unlit areas not completely dark
    ambient_light_level = 50  # Adjust as needed, from 0 to 255
    light_mask.fill((0, 0, 0, 255 - ambient_light_level))
    
    # Define a radius for the light sources
    light_radius = 200

    # Draw a light circle for each light source
    light_sources = [(s.rect.centerx, s.rect.centery) for s in torches]
    # The player also emits light
    light_sources.append(player.rect.center)
    
    for light_x, light_y in light_sources:
        # Create a surface for a single light gradient
        light_surface = pygame.Surface((light_radius * 2, light_radius * 2), pygame.SRCALPHA)
        # Create a gradient effect
        for i in range(light_radius, 0, -1):
            alpha = 255 - (i / light_radius) * 255
            pygame.draw.circle(light_surface, (255, 255, 255, alpha), (light_radius, light_radius), i)
        
        # Blit the light surface onto the main light mask using a blend mode
        light_mask.blit(light_surface, (light_x - light_radius, light_y - light_radius), special_flags=pygame.BLEND_RGBA_SUB)

    # Apply the final light mask to the screen
    screen.blit(light_mask, (0, 0))

    # --- Fog of War Effect ---
    # Convert player's position to tile coordinates
    player_tile_x = player.rect.centerx // TILE_SIZE
    player_tile_y = player.rect.centery // TILE_SIZE

    # Get the player's current view radius in tiles
    view_radius_tiles = 3 

    # Mark tiles around the player as visited
    for y_offset in range(-view_radius_tiles, view_radius_tiles + 1):
        for x_offset in range(-view_radius_tiles, view_radius_tiles + 1):
            tile_x = player_tile_x + x_offset
            tile_y = player_tile_y + y_offset
            
            # Check for valid grid coordinates
            if 0 <= tile_x < TILE_GRID_WIDTH and 0 <= tile_y < TILE_GRID_HEIGHT:
                # Mark as visited only if it's within a circle from the player's center
                dist_sq = (tile_x - player_tile_x)**2 + (tile_y - player_tile_y)**2
                if dist_sq <= view_radius_tiles**2:
                    visited_tiles[tile_y, tile_x] = True

    # Create the fog surface
    fog_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    fog_color_seen = (0, 0, 0, 150) # Darken seen areas
    fog_color_unseen = (0, 0, 0, 255) # Completely black for unseen areas

    for y in range(TILE_GRID_HEIGHT):
        for x in range(TILE_GRID_WIDTH):
            if visited_tiles[y, x]:
                # Draw a semi-transparent dark rectangle over previously visited tiles
                fog_rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(fog_surface, fog_color_seen, fog_rect)
            else:
                # Draw a completely black rectangle over unvisited tiles
                fog_rect = pygame.Rect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                pygame.draw.rect(fog_surface, fog_color_unseen, fog_rect)

    # Create a clear circle around the player to represent their immediate view
    player_view_radius_pixels = view_radius_tiles * TILE_SIZE
    pygame.draw.circle(fog_surface, (0, 0, 0, 0), player.rect.center, player_view_radius_pixels)

    # Blit the fog of war surface onto the screen
    screen.blit(fog_surface, (0, 0))

    # Draw the life bar
    bar_width = 200
    bar_height = 20
    bar_x = 10
    bar_y = 10
    pygame.draw.rect(screen, LIFE_BAR_BG_COLOR, (bar_x, bar_y, bar_width, bar_height))
    current_life_width = (player.life_points / 100) * bar_width
    pygame.draw.rect(screen, LIFE_BAR_COLOR, (bar_x, bar_y, current_life_width, bar_height))
    life_text = small_font.render(f"HP: {player.life_points}", True, WHITE)
    screen.blit(life_text, (bar_x + bar_width + 10, bar_y - 5))
    
    # Draw the stamina bar
    stamina_bar_x = 10
    stamina_bar_y = bar_y + bar_height + 10
    pygame.draw.rect(screen, STAMINA_BAR_BG_COLOR, (stamina_bar_x, stamina_bar_y, bar_width, bar_height))
    current_stamina_width = (player.stamina / player.max_stamina) * bar_width
    pygame.draw.rect(screen, STAMINA_BAR_COLOR, (stamina_bar_x, stamina_bar_y, current_stamina_width, bar_height))
    stamina_text = small_font.render(f"Stamina: {int(player.stamina)}", True, WHITE)
    screen.blit(stamina_text, (stamina_bar_x + bar_width + 10, stamina_bar_y - 5))
    
    # Draw the inventory section
    inventory_x = stamina_bar_x
    inventory_y = stamina_bar_y + bar_height + 10 # Position it below the stamina bar
    
    # Draw a container for the inventory
    inventory_size = 50
    inventory_spacing = 10
    num_slots = 4
    total_inventory_width = (inventory_size + inventory_spacing) * num_slots - inventory_spacing
    
    # Draw each slot
    for i in range(num_slots):
        slot_rect = pygame.Rect(inventory_x + i * (inventory_size + inventory_spacing), inventory_y, inventory_size, inventory_size)
        pygame.draw.rect(screen, WALL_COLOR, slot_rect, 2) # Draw a border for each slot

    # Draw the key icon if the player has the key
    if player.has_key:
        key_icon_rect = pygame.Rect(inventory_x, inventory_y, inventory_size, inventory_size)
        pygame.draw.rect(screen, KEY_COLOR, key_icon_rect)
    
    # Draw collected power-ups
    for i, item_type in enumerate(player.inventory):
        color = None
        if item_type == "heal":
            color = HEAL_COLOR
        elif item_type == "enemy_bomb":
            color = ENEMY_BOMB_COLOR
        elif item_type == "fog_clear":
            color = FOG_CLEAR_COLOR
        if color:
            item_rect = pygame.Rect(inventory_x + (i + 1) * (inventory_size + inventory_spacing), inventory_y, inventory_size, inventory_size)
            pygame.draw.rect(screen, color, item_rect)

def draw_dialogue(text):
    """Draws a dialogue box at the bottom of the screen."""
    # Semi-transparent background
    dialogue_box = pygame.Surface((SCREEN_WIDTH, 100), pygame.SRCALPHA)
    dialogue_box.fill((0, 0, 0, 150))
    
    # Dialogue text
    dialogue_text = dialogue_font.render(text, True, WHITE)
    dialogue_rect = dialogue_text.get_rect(center=(SCREEN_WIDTH / 2, 50))
    
    dialogue_box.blit(dialogue_text, dialogue_rect)
    screen.blit(dialogue_box, (0, SCREEN_HEIGHT - 100))

# --- Main Game Loop ---
def main():
    global current_state, active_dialogue, current_map_key, walls, npcs, torches, doors, player, keys, enemies, current_level, current_dungeon_data, power_ups, visited_tiles, rebind_target, KEY_BINDINGS, music_volume, is_muted
    running = True
    
    # Store the last unmuted volume level
    last_volume = music_volume
    
    while running:
        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if current_state == GAME_STATES["MENU"]:
                    start_text_rect = small_font.render("Start Game", True, WHITE).get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
                    start_button_rect = start_text_rect.inflate(20, 10)
                    
                    options_text_rect = small_font.render("Options", True, WHITE).get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 70))
                    options_button_rect = options_text_rect.inflate(20, 10)
                    
                    if start_button_rect.collidepoint(mouse_pos):
                        print("Starting game...")
                        current_state = GAME_STATES["GAME"]
                    elif options_button_rect.collidepoint(mouse_pos):
                        print("Opening options menu...")
                        current_state = GAME_STATES["OPTIONS"]
                elif current_state == GAME_STATES["OPTIONS"]:
                    audio_text_rect = small_font.render("Audio", True, WHITE).get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 - 50))
                    audio_button_rect = audio_text_rect.inflate(20, 10)
                    
                    controls_text_rect = small_font.render("Controls", True, WHITE).get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
                    controls_button_rect = controls_text_rect.inflate(20, 10)
                    
                    back_text_rect = small_font.render("Back", True, WHITE).get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 50))
                    back_button_rect = back_text_rect.inflate(20, 10)
                    
                    if audio_button_rect.collidepoint(mouse_pos):
                        current_state = GAME_STATES["AUDIO_OPTIONS"]
                    elif controls_button_rect.collidepoint(mouse_pos):
                        current_state = GAME_STATES["CONTROLS_OPTIONS"]
                    elif back_button_rect.collidepoint(mouse_pos):
                        current_state = GAME_STATES["MENU"]
                elif current_state == GAME_STATES["AUDIO_OPTIONS"]:
                    back_text_rect = small_font.render("Back", True, WHITE).get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 100))
                    back_button_rect = back_text_rect.inflate(20, 10)
                    
                    # Volume Slider
                    slider_width = 300
                    slider_height = 20
                    slider_x = SCREEN_WIDTH / 2 - slider_width / 2
                    slider_y = SCREEN_HEIGHT / 2 - 50
                    slider_rect = pygame.Rect(slider_x, slider_y, slider_width, slider_height)
                    
                    # Mute button
                    mute_text_rect = small_font.render("Mute", True, WHITE).get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 30))
                    mute_button_rect = mute_text_rect.inflate(20, 10)
                    
                    if slider_rect.collidepoint(mouse_pos):
                        # Calculate new volume based on mouse position
                        new_volume = (mouse_pos[0] - slider_x) / slider_width
                        music_volume = max(0, min(1, new_volume))
                        pygame.mixer.music.set_volume(music_volume)
                        is_muted = False # Unmute if the slider is adjusted
                        last_volume = music_volume
                    elif mute_button_rect.collidepoint(mouse_pos):
                        is_muted = not is_muted
                        if is_muted:
                            pygame.mixer.music.set_volume(0)
                        else:
                            pygame.mixer.music.set_volume(last_volume)
                    elif back_button_rect.collidepoint(mouse_pos):
                        current_state = GAME_STATES["OPTIONS"]
                elif current_state == GAME_STATES["CONTROLS_OPTIONS"]:
                    back_text_rect = small_font.render("Back", True, WHITE).get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 150))
                    
                    # Handle clicks on the keybinding buttons
                    key_y_start = SCREEN_HEIGHT / 2 - 100
                    button_x_start = SCREEN_WIDTH / 2 + 50
                    
                    for i, (action, key_code) in enumerate(KEY_BINDINGS.items()):
                        key_rect = small_font.render(get_key_name(key_code), True, WHITE).get_rect(left=button_x_start, centery=key_y_start + i * 50)
                        key_button_rect = key_rect.inflate(20, 10)
                        if key_button_rect.collidepoint(mouse_pos):
                            rebind_target = action
                            current_state = GAME_STATES["REBINDING_KEY"]
                            break

                    back_button_rect = back_text_rect.inflate(20, 10)
                    if back_button_rect.collidepoint(mouse_pos):
                        current_state = GAME_STATES["OPTIONS"]
                elif current_state == GAME_STATES["PAUSED"]:
                    resume_text_rect = small_font.render("Resume", True, WHITE).get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
                    resume_button_rect = resume_text_rect.inflate(20, 10)
                    
                    exit_text_rect = small_font.render("Exit to Main Menu", True, WHITE).get_rect(center=(SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2 + 60))
                    exit_button_rect = exit_text_rect.inflate(20, 10)
                    
                    if resume_button_rect.collidepoint(mouse_pos):
                        current_state = GAME_STATES["GAME"]
                    elif exit_button_rect.collidepoint(mouse_pos):
                        current_level = 1
                        current_dungeon_data = generate_dungeon(current_level)
                        load_map(current_dungeon_data)
                        current_state = GAME_STATES["MENU"]

            elif event.type == pygame.KEYDOWN:
                if current_state == GAME_STATES["REBINDING_KEY"]:
                    # Re-bind the key
                    if rebind_target:
                        KEY_BINDINGS[rebind_target] = event.key
                        rebind_target = None
                        current_state = GAME_STATES["CONTROLS_OPTIONS"]
                elif event.key == pygame.K_ESCAPE:
                    if current_state == GAME_STATES["GAME"]:
                        current_state = GAME_STATES["PAUSED"]
                    elif current_state == GAME_STATES["PAUSED"]:
                        current_state = GAME_STATES["GAME"]
                    elif current_state == GAME_STATES["GAME_OVER"]:
                        running = False
                elif current_state == GAME_STATES["DIALOGUE"]:
                    # Press any key to exit dialogue
                    active_dialogue = None
                    current_state = GAME_STATES["GAME"]
                elif current_state == GAME_STATES["GAME_OVER"]:
                    if event.key == pygame.K_r:
                        # Restart the game from level 1
                        current_level = 1
                        current_dungeon_data = generate_dungeon(current_level)
                        load_map(current_dungeon_data)
                        current_state = GAME_STATES["MENU"]
                elif current_state == GAME_STATES["GAME"]:
                    if event.key == KEY_BINDINGS["interact"]:
                        # Create an interaction rect that is slightly larger than the player's rect
                        interaction_rect = player.rect.inflate(TILE_SIZE // 2, TILE_SIZE // 2)

                        # Check for NPC interaction
                        npc_interacted = False
                        for npc in npcs:
                            if interaction_rect.colliderect(npc.rect):
                                # Restore a small amount of life when interacting with an NPC
                                player.life_points = min(100, player.life_points + 20)
                                active_dialogue = f"{npc.dialogue} Your life has been restored to {player.life_points}!"
                                current_state = GAME_STATES["DIALOGUE"]
                                dialogue_sound.play()
                                npc_interacted = True
                                break
                        
                        if not npc_interacted:
                            # Check for key collection
                            key_collected = pygame.sprite.spritecollideany(player, keys)
                            if key_collected:
                                keys.remove(key_collected)
                                player.has_key = True
                                active_dialogue = "You found a key! It might open something."
                                current_state = GAME_STATES["DIALOGUE"]
                                collect_sound.play()
                            
                            # Check for power-up collection
                            power_up_collected = pygame.sprite.spritecollideany(player, power_ups)
                            if power_up_collected:
                                if power_up_collected.type == "heal":
                                    player.life_points = min(100, player.life_points + 50)
                                    active_dialogue = f"You used a healing potion! Your life is now {player.life_points}."
                                elif power_up_collected.type == "enemy_bomb":
                                    enemies.empty()
                                    active_dialogue = "All enemies have been vanquished!"
                                elif power_up_collected.type == "fog_clear":
                                    visited_tiles.fill(True)
                                    active_dialogue = "The fog of war has been lifted!"
                                
                                # Add the power-up to the player's inventory and remove it from the map
                                player.inventory.append(power_up_collected.type)
                                power_ups.remove(power_up_collected)
                                current_state = GAME_STATES["DIALOGUE"]
                                collect_sound.play()

                            # Check for door interaction to unlock
                            for door in doors:
                                if door.locked and interaction_rect.colliderect(door.rect):
                                    if player.has_key:
                                        door.locked = False
                                        unlock_sound.play()
                                        active_dialogue = "The door is now unlocked. You can pass."
                                        current_state = GAME_STATES["DIALOGUE"]
                                        player.has_key = False
                                    else:
                                        active_dialogue = "The door is locked. You need a key."
                                        current_state = GAME_STATES["DIALOGUE"]
            
            elif event.type == pygame.KEYUP:
                if event.key == KEY_BINDINGS["sprint"]:
                    player.is_sprinting = False

        if current_state == GAME_STATES["MENU"]:
            draw_menu()
        elif current_state == GAME_STATES["OPTIONS"]:
            draw_options_menu()
        elif current_state == GAME_STATES["AUDIO_OPTIONS"]:
            draw_audio_menu()
        elif current_state == GAME_STATES["CONTROLS_OPTIONS"]:
            draw_controls_menu()
        elif current_state == GAME_STATES["REBINDING_KEY"]:
            draw_controls_menu() # Keep drawing the controls menu
        elif current_state == GAME_STATES["PAUSED"]:
            draw_game() # Draw the game screen first
            draw_pause_menu() # Then draw the overlay on top
        elif current_state == GAME_STATES["GAME"]:
            # Player input
            keys_pressed = pygame.key.get_pressed()
            dx, dy = 0, 0
            
            # Check for sprinting key and sufficient stamina
            if keys_pressed[KEY_BINDINGS["sprint"]] and player.stamina > 0:
                player.is_sprinting = True
            else:
                player.is_sprinting = False

            # Check for movement using both WASD and arrow keys
            if keys_pressed[KEY_BINDINGS["move_up"]] or keys_pressed[pygame.K_UP]:
                dy -= 1
            if keys_pressed[KEY_BINDINGS["move_down"]] or keys_pressed[pygame.K_DOWN]:
                dy += 1
            if keys_pressed[KEY_BINDINGS["move_left"]] or keys_pressed[pygame.K_LEFT]:
                dx -= 1
            if keys_pressed[KEY_BINDINGS["move_right"]] or keys_pressed[pygame.K_RIGHT]:
                dx += 1

            player.update(dx, dy, walls, doors)

            # Update enemies and NPCs
            enemies.update()
            npcs.update()

            # Check for enemy collision with player
            if player.invulnerable_timer == 0:
                enemy_collision = pygame.sprite.spritecollideany(player, enemies)
                if enemy_collision:
                    player.life_points -= 20
                    damage_sound.play()
                    player.invulnerable_timer = 60 # Set a 60-frame invulnerability period
                    if player.life_points <= 0:
                        game_over_sound.play()
                        current_state = GAME_STATES["GAME_OVER"]
            
            # Check for door transition
            for door in doors:
                if not door.locked and player.rect.colliderect(door.rect):
                    level_up_sound.play()
                    current_level += 1
                    current_dungeon_data = generate_dungeon(current_level)
                    load_map(current_dungeon_data)

            # Draw everything
            draw_game()

        elif current_state == GAME_STATES["DIALOGUE"]:
            draw_game()
            draw_dialogue(active_dialogue)
        
        elif current_state == GAME_STATES["GAME_OVER"]:
            draw_game_over()

        # Update the display
        pygame.display.flip()
        
        # Cap the frame rate
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()