import pygame
import sys
import os
from enum import Enum
import random
import math

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60
GRID_SIZE = 9
TILE_SIZE = 60
HEADER_HEIGHT = 80
ACTION_BAR_HEIGHT = 100

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
GOLD = (255, 215, 0)

class GameState(Enum):
    MAIN_MENU = 1
    SETTINGS = 2
    CHARACTER_SELECT = 3
    GAME_BOARD = 4
    COMBAT = 5
    ENDING = 6

class CharacterClass(Enum):
    WARRIOR = ("Warrior", "", "Tank class with high HP and defense", {
        'HP': 120, 'ATK': 8, 'DEF': 10, 'SPD': 5,
        'description': "A stalwart defender skilled in combat",
        'special': "Shield Bash - Deals damage and increases defense"
    })
    SCOUT = ("Scout", "", "Agile class with high speed and attack", {
        'HP': 80, 'ATK': 12, 'DEF': 5, 'SPD': 12,
        'description': "A swift hunter with deadly precision",
        'special': "Rapid Strike - Deals multiple hits in succession"
    })
    SHAMAN = ("Shaman", "", "Magical class with balanced stats", {
        'HP': 90, 'ATK': 10, 'DEF': 7, 'SPD': 8,
        'description': "A mystic wielder of ancient magic",
        'special': "Healing Wave - Restores HP and boosts attack"
    })

class TileType(Enum):
    EMPTY = 1
    MONSTER = 2
    TREASURE = 3
    STORY = 4
    WALL = 5
    BOSS_ROOM = 6

class MonsterType(Enum):
    # Format: (name, symbol, hp_mult, atk_mult, def_mult, special_ability)
    # Level 1-2 monsters
    SLIME = ("Slime", "🟢", 0.8, 0.7, 0.5, "Splits into two when damaged")
    RAT = ("Giant Rat", "🐀", 0.6, 1.0, 0.4, "Inflicts poison damage")
    BAT = ("Vampire Bat", "🦇", 0.5, 0.8, 0.3, "Life steal attack")
    
    # Level 3-4 monsters
    SKELETON = ("Skeleton Warrior", "💀", 0.9, 1.1, 0.8, "Bone armor reduces damage")
    GOBLIN = ("Goblin Rogue", "👺", 0.8, 1.2, 0.6, "Steals gold on hit")
    WOLF = ("Dire Wolf", "🐺", 1.0, 1.3, 0.7, "Pack tactics increase damage")
    
    # Level 5-7 monsters
    GHOST = ("Haunted Spirit", "👻", 0.8, 1.4, 1.2, "Phases through attacks")
    ORC = ("Orc Warrior", "👹", 1.3, 1.5, 1.0, "Berserker rage when low HP")
    
    # Level 8+ boss monsters
    DRAGON = ("Ancient Dragon", "🐲", 2.0, 1.8, 1.6, "Breathes fire")
    DEMON = ("Demon Lord", "👿", 1.8, 2.0, 1.5, "Summons minions")

class Tile:
    def __init__(self, type, revealed=False, char=''):
        self.type = type
        self.revealed = revealed
        self.char = char

class Monster:
    def __init__(self, level):
        self.level = level
        # Choose monster type based on level
        if level < 3:
            choices = [MonsterType.SLIME, MonsterType.RAT, MonsterType.BAT]
        elif level < 5:
            choices = [MonsterType.SKELETON, MonsterType.GOBLIN, MonsterType.WOLF]
        elif level < 8:
            choices = [MonsterType.GHOST, MonsterType.ORC]
        else:
            choices = [MonsterType.DRAGON, MonsterType.DEMON]
        
        self.type = random.choice(choices)
        base_hp = 50 + level * 10
        base_atk = 5 + level * 2
        base_def = 3 + level
        
        self.name = self.type.value[0]
        self.emoji = self.type.value[1]
        self.hp = int(base_hp * self.type.value[2])
        self.max_hp = self.hp
        self.atk = int(base_atk * self.type.value[3])
        self.def_ = int(base_def * self.type.value[4])
        self.special_ability = self.type.value[5]
        self.exp_reward = 20 + level * 10

class GameBoard:
    def __init__(self):
        self.grid = []
        self.player_pos = (4, 4)  # Center of 9x9 grid
        self.generate_board()

    def generate_board(self):
        # Generate tiles based on probability
        for y in range(GRID_SIZE):
            row = []
            for x in range(GRID_SIZE):
                # Add walls around the edges but ensure there's a path
                if (x == 0 or x == GRID_SIZE-1 or y == 0 or y == GRID_SIZE-1) and (x, y) != (4, 0) and (x, y) != (4, GRID_SIZE-1):
                    tile_type = TileType.WALL
                    char = '#'
                else:
                    rand = random.random()
                    if rand < 0.65:  # Increased empty space probability
                        tile_type = TileType.EMPTY
                        char = ''
                    elif rand < 0.80:  # Reduced monster probability
                        tile_type = TileType.MONSTER
                        char = ''
                    elif rand < 0.90:  # Increased treasure probability
                        tile_type = TileType.TREASURE
                        char = '$'
                    else:
                        tile_type = TileType.STORY
                        char = '?'
                row.append(Tile(tile_type, False, char))
            self.grid.append(row)
        
        # Ensure starting tile is empty and revealed
        self.grid[self.player_pos[1]][self.player_pos[0]] = Tile(TileType.EMPTY, True, '')
        
        # Generate a boss room away from start
        while True:
            boss_x = random.randint(2, GRID_SIZE - 3)
            boss_y = random.randint(2, GRID_SIZE - 3)
            # Ensure boss room is at least 3 tiles away from start
            if abs(boss_x - self.player_pos[0]) + abs(boss_y - self.player_pos[1]) >= 3:
                self.grid[boss_y][boss_x] = Tile(TileType.BOSS_ROOM, False, 'B')
                break
        
        # Add some guaranteed treasure rooms
        treasure_count = 0
        while treasure_count < 3:  # Ensure at least 3 treasure rooms
            x = random.randint(1, GRID_SIZE - 2)
            y = random.randint(1, GRID_SIZE - 2)
            if self.grid[y][x].type == TileType.EMPTY:
                self.grid[y][x] = Tile(TileType.TREASURE, False, '$')
                treasure_count += 1

    def reveal_tile(self, x, y):
        if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
            self.grid[y][x].revealed = True
            return self.grid[y][x].type
        return None

    def move_player(self, dx, dy):
        new_x = self.player_pos[0] + dx
        new_y = self.player_pos[1] + dy
        
        if 0 <= new_x < GRID_SIZE and 0 <= new_y < GRID_SIZE:
            self.player_pos = (new_x, new_y)
            return self.reveal_tile(new_x, new_y)
        return None

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Dungeo")
        self.clock = pygame.time.Clock()
        self.state = GameState.MAIN_MENU
        self.sound_on = True
        self.menu_index = 0
        self.menu_options = ["New Game", "Settings", "Exit"]
        self.settings_options = ["Sound: ON", "God Mode: OFF"]
        self.settings_index = 0
        self.character_name = ""
        self.selected_class = None
        self.class_stats = {
            CharacterClass.WARRIOR: {"HP": 100, "ATK": 8, "DEF": 7},
            CharacterClass.SCOUT: {"HP": 70, "ATK": 10, "DEF": 5},
            CharacterClass.SHAMAN: {"HP": 80, "ATK": 6, "DEF": 6}
        }
        self.god_mode = False
        
        # Load assets
        self.background = pygame.image.load(os.path.join('assets', 'dungeo.jpg'))
        self.background = pygame.transform.scale(self.background, (WINDOW_WIDTH, WINDOW_HEIGHT))
        
        # Font setup
        try:
            self.emoji_font = pygame.font.SysFont('segoe ui emoji', 32)  # Windows emoji font
        except:
            try:
                self.emoji_font = pygame.font.SysFont('apple color emoji', 32)  # Mac emoji font
            except:
                self.emoji_font = pygame.font.Font(None, 32)  # Fallback to default
        
        self.title_font = pygame.font.Font(None, 74)
        self.menu_font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)

        # Load sounds
        self.sounds = {}
        try:
            self.sounds['select'] = pygame.mixer.Sound('assets/select.wav')
            self.sounds['confirm'] = pygame.mixer.Sound('assets/confirm.wav')
            self.sounds['back'] = pygame.mixer.Sound('assets/back.wav')
        except:
            # If sound files are missing, create silent sounds
            empty_sound = pygame.mixer.Sound(buffer=b'')
            self.sounds = {
                'select': empty_sound,
                'confirm': empty_sound,
                'back': empty_sound
            }
        
        # Set sound volumes
        for sound in self.sounds.values():
            sound.set_volume(0.3)
        
        self.game_board = None
        self.player_stats = None
        self.current_monster = None
        self.combat_options = ["Attack", "Defend", "Special", "Run"]
        self.combat_index = 0
        self.combat_message = ""
        self.combat_turn = "player"  # player or monster

    def init_game(self):
        # Initialize game board
        self.game_board = GameBoard()
        
        # Get stats from CharacterClass enum
        class_data = CharacterClass[self.selected_class].value[3]
        
        # Initialize player stats
        self.player_stats = {
            'name': self.character_name,
            'class': self.selected_class,
            'level': 1,
            'exp': 0,
            'hp': class_data['HP'],
            'max_hp': class_data['HP'],
            'atk': class_data['ATK'],
            'def': class_data['DEF'],
            'spd': class_data['SPD'],
            'spirit': 100,
            'max_spirit': 100
        }
        
        # Initialize combat variables
        self.combat_options = ["Attack", "Defend", "Special", "Run"]
        self.combat_index = 0
        self.combat_message = ""
        self.combat_turn = "player"
        self.current_monster = None

    def generate_random_name(self):
        prefixes = ["Brave", "Swift", "Wise", "Shadow", "Storm", "Moon", "Sun", "Star"]
        suffixes = ["walker", "hunter", "seeker", "spirit", "runner", "watcher"]
        return f"{random.choice(prefixes)}{random.choice(suffixes)}"

    def handle_main_menu_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_UP, pygame.K_w]:
                self.menu_index = (self.menu_index - 1) % len(self.menu_options)
            elif event.key in [pygame.K_DOWN, pygame.K_s]:
                self.menu_index = (self.menu_index + 1) % len(self.menu_options)
            elif event.key in [pygame.K_RETURN, pygame.K_SPACE]:
                self.select_menu_option()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            # Check if any menu option was clicked
            for i, option in enumerate(self.menu_options):
                text_surface = self.menu_font.render(option, True, WHITE)
                text_rect = text_surface.get_rect(center=(WINDOW_WIDTH // 2, 300 + i * 50))
                if text_rect.collidepoint(mouse_pos):
                    self.menu_index = i
                    self.select_menu_option()

    def select_menu_option(self):
        if self.menu_options[self.menu_index] == "New Game":
            self.state = GameState.CHARACTER_SELECT
            self.selected_class = None
            self.character_name = ""
        elif self.menu_options[self.menu_index] == "Settings":
            self.state = GameState.SETTINGS
        elif self.menu_options[self.menu_index] == "Exit":
            pygame.quit()
            sys.exit()

    def handle_settings_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state = GameState.MAIN_MENU
            elif event.key in [pygame.K_UP, pygame.K_w]:
                self.settings_index = (self.settings_index - 1) % len(self.settings_options)
            elif event.key in [pygame.K_DOWN, pygame.K_s]:
                self.settings_index = (self.settings_index + 1) % len(self.settings_options)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = pygame.mouse.get_pos()
            for i, option in enumerate(self.settings_options):
                text_surface = self.menu_font.render(option, True, WHITE)
                text_rect = text_surface.get_rect(center=(WINDOW_WIDTH // 2, 300 + i * 50))
                if text_rect.collidepoint(mouse_pos):
                    if "Sound" in option:
                        self.sound_on = not self.sound_on
                        self.settings_options[0] = f"Sound: {'ON' if self.sound_on else 'OFF'}"
                    elif "God Mode" in option:
                        self.god_mode = not self.god_mode
                        self.settings_options[1] = f"God Mode: {'ON' if self.god_mode else 'OFF'}"

    def handle_character_select_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                classes = list(CharacterClass)
                current_idx = classes.index(CharacterClass[self.selected_class]) if self.selected_class else 0
                new_idx = (current_idx - 1) % len(classes)
                self.selected_class = classes[new_idx].name
                self.play_sound('select')
            elif event.key == pygame.K_RIGHT:
                classes = list(CharacterClass)
                current_idx = classes.index(CharacterClass[self.selected_class]) if self.selected_class else 0
                new_idx = (current_idx + 1) % len(classes)
                self.selected_class = classes[new_idx].name
                self.play_sound('select')
            elif event.key == pygame.K_RETURN:
                if self.selected_class:
                    self.character_name = f"Hero_{random.randint(1000, 9999)}"
                    self.initialize_player_stats()
                    self.state = GameState.GAME_BOARD
                    self.play_sound('confirm')
            elif event.key == pygame.K_ESCAPE:
                self.state = GameState.MAIN_MENU
                self.play_sound('back')
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_x, mouse_y = pygame.mouse.get_pos()
                
                # Calculate box positions
                box_width = 220
                box_height = 400
                spacing = 40
                total_width = (box_width * 3) + (spacing * 2)
                start_x = (WINDOW_WIDTH - total_width) // 2
                start_y = 100
                
                # Check if click is within any character box
                for i, char_class in enumerate(CharacterClass):
                    box_x = start_x + (box_width + spacing) * i
                    box_rect = pygame.Rect(box_x, start_y, box_width, box_height)
                    
                    if box_rect.collidepoint(mouse_x, mouse_y):
                        if self.selected_class != char_class.name:
                            self.selected_class = char_class.name
                            self.play_sound('select')
                        else:  # Double click to confirm
                            self.character_name = f"Hero_{random.randint(1000, 9999)}"
                            self.initialize_player_stats()
                            self.state = GameState.GAME_BOARD
                            self.play_sound('confirm')

    def initialize_player_stats(self):
        # Get the selected class's stats
        class_data = CharacterClass[self.selected_class].value[3]
        
        self.player_stats = {
            'name': self.character_name,
            'class': self.selected_class,
            'level': 1,
            'exp': 0,
            'hp': class_data['HP'],
            'max_hp': class_data['HP'],
            'atk': class_data['ATK'],
            'def': class_data['DEF'],
            'spd': class_data['SPD'],
            'spirit': 100,
            'max_spirit': 100
        }

    def handle_game_board_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.state = GameState.MAIN_MENU
            elif event.key in [pygame.K_LEFT, pygame.K_a]:
                tile_type = self.game_board.move_player(-1, 0)
                self.process_tile_event(tile_type)
            elif event.key in [pygame.K_RIGHT, pygame.K_d]:
                tile_type = self.game_board.move_player(1, 0)
                self.process_tile_event(tile_type)
            elif event.key in [pygame.K_UP, pygame.K_w]:
                tile_type = self.game_board.move_player(0, -1)
                self.process_tile_event(tile_type)
            elif event.key in [pygame.K_DOWN, pygame.K_s]:
                tile_type = self.game_board.move_player(0, 1)
                self.process_tile_event(tile_type)

    def process_tile_event(self, tile_type):
        if tile_type == TileType.MONSTER:
            self.current_monster = Monster(self.player_stats['level'])
            self.combat_index = 0
            self.combat_message = f"A {self.current_monster.name} appears!"
            self.combat_turn = "player"
            self.state = GameState.COMBAT
        elif tile_type == TileType.TREASURE:
            # Heal player and give spirit points
            heal = min(20, self.player_stats['max_hp'] - self.player_stats['hp'])
            self.player_stats['hp'] += heal
            spirit_gain = min(20, self.player_stats['max_spirit'] - self.player_stats['spirit'])
            self.player_stats['spirit'] += spirit_gain
            if heal > 0 or spirit_gain > 0:
                self.combat_message = f"Found treasure! Healed {heal} HP and gained {spirit_gain} Spirit!"
        elif tile_type == TileType.STORY:
            self.combat_message = "You discover an ancient inscription..."
        elif tile_type == TileType.BOSS_ROOM:
            self.current_monster = Monster(self.player_stats['level'] + 5)
            self.combat_index = 0
            self.combat_message = f"A {self.current_monster.name} appears!"
            self.combat_turn = "player"
            self.state = GameState.COMBAT

    def handle_combat_input(self, event):
        if event.type == pygame.KEYDOWN:
            if self.combat_turn == "player":
                if event.key in [pygame.K_UP, pygame.K_w]:
                    self.combat_index = (self.combat_index - 1) % len(self.combat_options)
                elif event.key in [pygame.K_DOWN, pygame.K_s]:
                    self.combat_index = (self.combat_index + 1) % len(self.combat_options)
                elif event.key in [pygame.K_SPACE, pygame.K_RETURN]:
                    self.execute_combat_action()

    def execute_combat_action(self):
        action = self.combat_options[self.combat_index]
        
        if action == "Attack":
            # Calculate damage
            damage = max(1, self.player_stats['atk'] - self.current_monster.def_)
            self.current_monster.hp -= damage
            self.combat_message = f"You deal {damage} damage!"
            
        elif action == "Defend":
            # Increase defense temporarily and heal
            self.player_stats['def'] += 2
            heal = min(10, self.player_stats['max_hp'] - self.player_stats['hp'])
            self.player_stats['hp'] += heal
            self.combat_message = f"Defense up! Healed {heal} HP!"
            
        elif action == "Special" and self.player_stats['spirit'] >= 20:
            # Special attack that uses spirit points
            self.player_stats['spirit'] -= 20
            damage = self.player_stats['atk'] * 2
            self.current_monster.hp -= damage
            self.combat_message = f"Special attack deals {damage} damage!"
            
        elif action == "Run":
            # Can't run from boss battles
            if self.current_monster.level >= self.player_stats['level'] + 5:
                self.combat_message = "Cannot escape from a boss battle!"
                return
            # 50% chance to run
            if random.random() > 0.5:
                self.state = GameState.GAME_BOARD
                self.combat_message = "Got away safely!"
                return
            else:
                self.combat_message = "Couldn't escape!"
    
        # Check if monster is defeated
        if self.current_monster.hp <= 0:
            self.player_stats['exp'] += self.current_monster.exp_reward
            victory_message = f"{self.current_monster.name} defeated! Gained {self.current_monster.exp_reward} EXP!"
            
            # Check if this was a boss monster
            if self.current_monster.level >= self.player_stats['level'] + 5:
                victory_message += "\nCongratulations! You have defeated the boss and won the game!"
                self.combat_message = victory_message
                self.state = GameState.ENDING
                return
                
            self.combat_message = victory_message
            # Level up check
            if self.player_stats['exp'] >= self.player_stats['level'] * 100:
                self.player_stats['level'] += 1
                self.player_stats['exp'] = 0
                self.player_stats['max_hp'] += 10
                self.player_stats['hp'] = self.player_stats['max_hp']
                self.player_stats['atk'] += 2
                self.player_stats['def'] += 1
                self.combat_message += f"\nLevel Up! Now level {self.player_stats['level']}!"
            self.state = GameState.GAME_BOARD
            return
        
        # Monster's turn
        self.combat_turn = "monster"
        pygame.time.set_timer(pygame.USEREVENT, 1000)  # Monster attacks after 1 second

    def handle_monster_turn(self):
        # Calculate monster damage
        damage = max(1, self.current_monster.atk - self.player_stats['def'])
        self.player_stats['hp'] -= damage
        self.combat_message = f"{self.current_monster.name} deals {damage} damage!"
        
        # Reset temporary defense buff
        class_data = CharacterClass[self.selected_class].value[3]
        self.player_stats['def'] = class_data['DEF']
        
        # Check if player is defeated
        if self.player_stats['hp'] <= 0:
            self.state = GameState.ENDING
        else:
            self.combat_turn = "player"

    def handle_ending_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                self.state = GameState.MAIN_MENU
                self.player_stats = None
                self.game_board = None
                self.current_monster = None
                self.combat_message = ""
                self.combat_turn = "player"
                self.combat_index = 0

    def play_sound(self, sound_name):
        """Play a sound effect if it exists"""
        if sound_name in self.sounds:
            try:
                self.sounds[sound_name].play()
            except:
                pass  # Silently fail if sound playback fails

    def draw_hex_tile(self, x, y, revealed, tile_type, char):
        # Calculate pixel coordinates for hexagonal grid
        pixel_x = WINDOW_WIDTH // 2 + (x - self.game_board.player_pos[0]) * TILE_SIZE * 0.75
        pixel_y = WINDOW_HEIGHT // 2 + (y - self.game_board.player_pos[1]) * TILE_SIZE
        if x % 2:
            pixel_y += TILE_SIZE // 2

        # Draw hex shape
        points = []
        for i in range(6):
            angle = i * 60 - 30
            px = pixel_x + TILE_SIZE // 2 * math.cos(math.radians(angle))
            py = pixel_y + TILE_SIZE // 2 * math.sin(math.radians(angle))
            points.append((px, py))

        color = GRAY
        if revealed:
            if tile_type == TileType.EMPTY:
                color = (50, 50, 50)
            elif tile_type == TileType.MONSTER:
                color = (150, 50, 50)
            elif tile_type == TileType.TREASURE:
                color = (150, 150, 50)
            elif tile_type == TileType.STORY:
                color = (50, 50, 150)
            elif tile_type == TileType.WALL:
                color = (100, 100, 100)
            elif tile_type == TileType.BOSS_ROOM:
                # Pulsating red color for boss room
                pulse = (math.sin(pygame.time.get_ticks() * 0.005) + 1) * 0.5
                red = int(200 + pulse * 55)
                color = (red, 0, 0)

        pygame.draw.polygon(self.screen, color, points)
        pygame.draw.polygon(self.screen, WHITE, points, 1)

        # Draw tile character or symbol
        if revealed:
            symbol = char
            if tile_type == TileType.WALL:
                symbol = '#'
            elif tile_type == TileType.BOSS_ROOM:
                symbol = '☠'  # Skull symbol for boss room
        
            if symbol:
                char_surface = self.menu_font.render(symbol, True, WHITE)
                char_rect = char_surface.get_rect(center=(pixel_x, pixel_y))
                self.screen.blit(char_surface, char_rect)

    def draw_header(self):
        # Draw header background
        pygame.draw.rect(self.screen, (30, 30, 30), (0, 0, WINDOW_WIDTH, HEADER_HEIGHT))
        
        # Draw player info
        name_text = self.menu_font.render(self.character_name, True, WHITE)
        self.screen.blit(name_text, (20, 20))
        
        # Draw HP bar
        hp_text = f"HP: {self.player_stats['hp']}/{self.player_stats['max_hp']}"
        hp_surface = self.menu_font.render(hp_text, True, WHITE)
        self.screen.blit(hp_surface, (200, 20))
        
        # Draw Spirit points
        spirit_text = f"Spirit: {self.player_stats['spirit']}/{self.player_stats['max_spirit']}"
        spirit_surface = self.menu_font.render(spirit_text, True, WHITE)
        self.screen.blit(spirit_surface, (400, 20))

    def draw_action_bar(self):
        # Draw action bar background
        bar_rect = (0, WINDOW_HEIGHT - ACTION_BAR_HEIGHT, WINDOW_WIDTH, ACTION_BAR_HEIGHT)
        pygame.draw.rect(self.screen, (30, 30, 30), bar_rect)
        
        # Draw controls help
        controls_text = "Controls: Arrow Keys/WASD to move | ESC for menu"
        controls_surface = self.menu_font.render(controls_text, True, WHITE)
        self.screen.blit(controls_surface, (20, WINDOW_HEIGHT - 40))

    def draw_game_board(self):
        if not self.game_board:
            self.init_game()

        self.screen.fill(BLACK)
        
        # Draw game board grid
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                tile = self.game_board.grid[y][x]
                self.draw_hex_tile(x, y, tile.revealed, tile.type, tile.char)
        
        # Draw header and action bar
        self.draw_header()
        self.draw_action_bar()

    def draw_main_menu(self):
        # Draw background
        self.screen.blit(self.background, (0, 0))
        
        # Draw title
        title_surface = self.title_font.render("DUNGEO", True, GOLD)
        title_rect = title_surface.get_rect(center=(WINDOW_WIDTH // 2, 150))
        self.screen.blit(title_surface, title_rect)
        
        # Draw menu options
        for i, option in enumerate(self.menu_options):
            color = GOLD if i == self.menu_index else WHITE
            text_surface = self.menu_font.render(option, True, color)
            text_rect = text_surface.get_rect(center=(WINDOW_WIDTH // 2, 300 + i * 50))
            self.screen.blit(text_surface, text_rect)
        
        # Draw sound status
        sound_text = "Sound: ON" if self.sound_on else "Sound: OFF"
        sound_surface = self.menu_font.render(sound_text, True, WHITE)
        self.screen.blit(sound_surface, (10, WINDOW_HEIGHT - 30))

    def draw_settings(self):
        self.screen.fill(BLACK)
        
        # Draw title
        title_surface = self.title_font.render("SETTINGS", True, GOLD)
        title_rect = title_surface.get_rect(center=(WINDOW_WIDTH // 2, 150))
        self.screen.blit(title_surface, title_rect)
        
        # Draw options
        for i, option in enumerate(self.settings_options):
            color = GOLD if i == self.settings_index else WHITE
            text_surface = self.menu_font.render(option, True, color)
            text_rect = text_surface.get_rect(center=(WINDOW_WIDTH // 2, 300 + i * 50))
            self.screen.blit(text_surface, text_rect)
        
        # Draw back instruction
        back_text = "Press ESC to return to main menu"
        back_surface = self.menu_font.render(back_text, True, GRAY)
        back_rect = back_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 50))
        self.screen.blit(back_surface, back_rect)

    def draw_character_select(self):
        # Draw semi-transparent background
        bg_surface = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
        bg_surface.fill((20, 20, 40))
        bg_surface.set_alpha(230)
        self.screen.blit(bg_surface, (0, 0))

        # Draw title with shadow effect
        title_shadow = self.title_font.render("Choose Your Hero", True, (0, 0, 0))
        title = self.title_font.render("Choose Your Hero", True, GOLD)
        shadow_rect = title_shadow.get_rect(center=(WINDOW_WIDTH // 2 + 2, 52))
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 50))
        self.screen.blit(title_shadow, shadow_rect)
        self.screen.blit(title, title_rect)

        # Calculate positions for three character boxes with more height
        box_width = 220
        box_height = 450  # Increased height
        spacing = 40
        total_width = (box_width * 3) + (spacing * 2)
        start_x = (WINDOW_WIDTH - total_width) // 2
        start_y = 90  # Moved up slightly

        # Draw character boxes
        for i, char_class in enumerate(CharacterClass):
            x = start_x + (box_width + spacing) * i
            y = start_y
            
            # Draw box background with gradient effect
            is_selected = char_class.name == self.selected_class
            if is_selected:
                for j in range(box_height):
                    alpha = 100 + (j / box_height) * 155
                    line_color = (60, 60, 100, alpha)
                    pygame.draw.line(self.screen, line_color, 
                                   (x, y + j), (x + box_width, y + j))
            else:
                pygame.draw.rect(self.screen, (40, 40, 60), (x, y, box_width, box_height))
            
            # Draw selection effects
            if is_selected:
                # Glowing border effect
                for offset in range(3):
                    border_alpha = 255 - (offset * 60)
                    border_color = (*GOLD, border_alpha)
                    pygame.draw.rect(self.screen, border_color, 
                                   (x - offset, y - offset, 
                                    box_width + offset * 2, box_height + offset * 2), 
                                   1)
            else:
                pygame.draw.rect(self.screen, (100, 100, 140), 
                               (x, y, box_width, box_height), 1)

            # Draw class name with icon
            class_icons = {
                'WARRIOR': '⚔️',
                'SCOUT': '🏹',
                'SHAMAN': '✨'
            }
            icon = class_icons.get(char_class.name, '')
            name_text = f"{icon} {char_class.value[0]}"
            name_shadow = self.menu_font.render(name_text, True, (0, 0, 0))
            name_surface = self.menu_font.render(name_text, True, 
                                               GOLD if is_selected else WHITE)
            
            name_rect = name_surface.get_rect(center=(x + box_width//2, y + 30))
            self.screen.blit(name_shadow, (name_rect.x + 1, name_rect.y + 1))
            self.screen.blit(name_surface, name_rect)

            # Draw character image or placeholder
            image_rect = pygame.Rect(x + 35, y + 60, 150, 150)
            try:
                image = pygame.image.load(f"assets/{char_class.name.lower()}.png")
                image = pygame.transform.scale(image, (150, 150))
                if not is_selected:
                    dark = pygame.Surface(image.get_size()).convert_alpha()
                    dark.fill((0, 0, 0, 100))
                    image.blit(dark, (0, 0))
                self.screen.blit(image, image_rect)
            except:
                pygame.draw.rect(self.screen, (80, 80, 100), image_rect)
                placeholder = self.menu_font.render(char_class.value[1], True, WHITE)
                placeholder_rect = placeholder.get_rect(center=image_rect.center)
                self.screen.blit(placeholder, placeholder_rect)

            # Draw class description with better spacing
            desc = char_class.value[2]
            desc_words = desc.split()
            desc_lines = []
            current_line = []
            
            for word in desc_words:
                current_line.append(word)
                test_line = ' '.join(current_line)
                if self.small_font.size(test_line)[0] > box_width - 30:  # Using small_font
                    if len(current_line) > 1:
                        current_line.pop()
                        desc_lines.append(' '.join(current_line))
                        current_line = [word]
                    else:
                        desc_lines.append(test_line)
                        current_line = []
            
            if current_line:
                desc_lines.append(' '.join(current_line))

            # Draw description with increased spacing
            desc_y = y + 230
            for line in desc_lines:
                desc_surface = self.small_font.render(line, True, 
                                                   WHITE if is_selected else GRAY)
                desc_rect = desc_surface.get_rect(center=(x + box_width//2, desc_y))
                self.screen.blit(desc_surface, desc_rect)
                desc_y += 25  # Increased line spacing

            # Draw stats bars with icons and better spacing
            stats = char_class.value[3]
            stat_y = y + 320  # Moved down slightly
            stat_icons = {
                'HP': '❤️',
                'ATK': '⚔️',
                'DEF': '🛡️',
                'SPD': '⚡'
            }
            
            for stat, value in [('HP', stats['HP']), ('ATK', stats['ATK']), 
                              ('DEF', stats['DEF']), ('SPD', stats['SPD'])]:
                # Draw stat label with icon
                icon = stat_icons[stat]
                stat_text = f"{icon} {stat}"
                text_surface = self.small_font.render(stat_text, True, WHITE)
                self.screen.blit(text_surface, (x + 10, stat_y))
                
                # Draw stat bar
                bar_width = 120
                bar_height = 15
                bar_x = x + 80
                pygame.draw.rect(self.screen, (60, 60, 60), 
                               (bar_x, stat_y + 2, bar_width, bar_height))
                value_width = int((value / 100) * bar_width)
                
                # Choose color based on stat value
                if value >= 100 * 0.8:
                    color = (0, 255, 0)  # Green for high stats
                elif value >= 100 * 0.5:
                    color = (255, 255, 0)  # Yellow for medium stats
                else:
                    color = (255, 128, 0)  # Orange for lower stats
                
                pygame.draw.rect(self.screen, color, 
                               (bar_x, stat_y + 2, value_width, bar_height))
                pygame.draw.rect(self.screen, WHITE, 
                               (bar_x, stat_y + 2, bar_width, bar_height), 1)
                
                stat_y += 30  # Increased spacing between stats

            # Draw special ability with icon
            special_y = y + box_height - 40
            special_text = f"✨ {stats['special']}"
            special_surface = self.small_font.render(special_text, True,
                                                   GOLD if is_selected else WHITE)
            special_rect = special_surface.get_rect(center=(x + box_width//2, special_y))
            self.screen.blit(special_surface, special_rect)

        # Draw controls with better visibility
        controls_text = "← → Select   |   Click or ENTER to Confirm   |   ESC Back"
        controls_shadow = self.menu_font.render(controls_text, True, (0, 0, 0))
        controls_surface = self.menu_font.render(controls_text, True, WHITE)
        controls_rect = controls_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 30))
        self.screen.blit(controls_shadow, (controls_rect.x + 1, controls_rect.y + 1))
        self.screen.blit(controls_surface, controls_rect)

    def draw_combat(self):
        self.screen.fill(BLACK)
        
        # Draw monster info with emoji
        monster_symbol = self.current_monster.emoji
        monster_info = f"{self.current_monster.name} {monster_symbol} Lvl.{self.current_monster.level}"
        
        # Try to render emoji with special font
        monster_text = self.emoji_font.render(monster_info, True, WHITE)
        monster_rect = monster_text.get_rect(center=(WINDOW_WIDTH // 2, 50))
        self.screen.blit(monster_text, monster_rect)
        
        # Draw large monster emoji
        large_emoji = self.emoji_font.render(monster_symbol, True, WHITE)
        emoji_rect = large_emoji.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3))
        scaled_emoji = pygame.transform.scale(large_emoji, (96, 96))
        scaled_rect = scaled_emoji.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 3))
        self.screen.blit(scaled_emoji, scaled_rect)
        
        # Draw monster special ability
        ability_text = f"Special: {self.current_monster.special_ability}"
        ability_surface = self.small_font.render(ability_text, True, GOLD)
        ability_rect = ability_surface.get_rect(center=(WINDOW_WIDTH // 2, 80))
        self.screen.blit(ability_surface, ability_rect)
        
        # Draw monster HP with colored bar
        monster_hp = f"HP: {self.current_monster.hp}/{self.current_monster.max_hp}"
        hp_text = self.menu_font.render(monster_hp, True, WHITE)
        hp_rect = hp_text.get_rect(center=(WINDOW_WIDTH // 2, 110))
        self.screen.blit(hp_text, hp_rect)
        
        # Draw monster HP bar with gradient
        bar_width = 300
        bar_height = 20
        bar_x = (WINDOW_WIDTH - bar_width) // 2
        bar_y = 130
        
        # Background
        pygame.draw.rect(self.screen, (50, 0, 0), (bar_x, bar_y, bar_width, bar_height))
        # HP with gradient
        hp_ratio = self.current_monster.hp / self.current_monster.max_hp
        hp_width = int(hp_ratio * bar_width)
        for i in range(hp_width):
            # Create a gradient from red to yellow based on HP percentage
            color_ratio = i / bar_width
            red = 200
            green = int(150 * color_ratio)
            pygame.draw.line(self.screen, (red, green, 0), 
                            (bar_x + i, bar_y), (bar_x + i, bar_y + bar_height))
        # Border
        pygame.draw.rect(self.screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 1)
        
        # Draw player stats
        self.draw_header()
        
        # Draw combat message
        message_text = self.combat_message
        message_surface = self.menu_font.render(message_text, True, GOLD)
        message_rect = message_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
        self.screen.blit(message_surface, message_rect)
        
        # Draw combat options with ASCII symbols
        option_icons = {
            "Attack": ">",
            "Defend": "[",
            "Special": "*",
            "Run": "<"
        }
        
        for i, option in enumerate(self.combat_options):
            color = GOLD if i == self.combat_index else WHITE
            if option == "Special":
                if self.player_stats['spirit'] >= 20:
                    text = f"{option_icons[option]} {option} (20 Spirit)"
                else:
                    text = f"{option_icons[option]} {option} (Not enough Spirit)"
                    color = GRAY
            else:
                text = f"{option_icons[option]} {option}"
        
            # Draw selection arrow
            if i == self.combat_index:
                text = "=>" + text
            else:
                text = "  " + text
        
            option_text = self.menu_font.render(text, True, color)
            self.screen.blit(option_text, (50, WINDOW_HEIGHT - 200 + i * 40))
    
        # Draw turn indicator
        turn_text = ">> Your Turn" if self.combat_turn == "player" else ">> Enemy Turn"
        turn_surface = self.menu_font.render(turn_text, True, GOLD)
        self.screen.blit(turn_surface, (WINDOW_WIDTH - 200, WINDOW_HEIGHT - 50))

    def draw_ending(self):
        self.screen.fill(BLACK)
        
        # Draw victory title with glow effect
        title_text = "VICTORY!" if self.player_stats['hp'] > 0 else "HEROIC SACRIFICE!"
        for offset in range(3):
            glow_alpha = 255 - (offset * 60)
            glow_surface = self.title_font.render(title_text, True, (*GOLD, glow_alpha))
            glow_rect = glow_surface.get_rect(center=(WINDOW_WIDTH // 2 + offset, WINDOW_HEIGHT // 4 + offset))
            self.screen.blit(glow_surface, glow_rect)
        
        title_surface = self.title_font.render(title_text, True, GOLD)
        title_rect = title_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 4))
        self.screen.blit(title_surface, title_rect)
        
        # Draw player stats
        stats_text = [
            f"Hero: {self.character_name}",
            f"Class: {self.selected_class}",
            f"Level: {self.player_stats['level']}",
            f"Final HP: {max(0, self.player_stats['hp'])}/{self.player_stats['max_hp']}",
            f"Attack: {self.player_stats['atk']}",
            f"Defense: {self.player_stats['def']}",
            "Press ENTER to return to main menu"
        ]
        
        # Add special message for dying while winning
        if self.player_stats['hp'] <= 0:
            stats_text.insert(-1, "You defeated the boss at the cost of your life!")
        
        for i, text in enumerate(stats_text):
            text_surface = self.menu_font.render(text, True, WHITE)
            text_rect = text_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + i * 40))
            self.screen.blit(text_surface, text_rect)

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.USEREVENT:  # Monster turn timer
                    if self.state == GameState.COMBAT and self.combat_turn == "monster":
                        self.handle_monster_turn()
                
                if self.state == GameState.MAIN_MENU:
                    self.handle_main_menu_input(event)
                elif self.state == GameState.SETTINGS:
                    self.handle_settings_input(event)
                elif self.state == GameState.CHARACTER_SELECT:
                    self.handle_character_select_input(event)
                elif self.state == GameState.GAME_BOARD:
                    self.handle_game_board_input(event)
                elif self.state == GameState.COMBAT:
                    self.handle_combat_input(event)
                elif self.state == GameState.ENDING:
                    self.handle_ending_input(event)
            
            # Clear screen
            self.screen.fill(BLACK)
            
            # Draw current state
            if self.state == GameState.MAIN_MENU:
                self.draw_main_menu()
            elif self.state == GameState.SETTINGS:
                self.draw_settings()
            elif self.state == GameState.CHARACTER_SELECT:
                self.draw_character_select()
            elif self.state == GameState.GAME_BOARD:
                self.draw_game_board()
            elif self.state == GameState.COMBAT:
                self.draw_combat()
            elif self.state == GameState.ENDING:
                self.draw_ending()
            
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()
