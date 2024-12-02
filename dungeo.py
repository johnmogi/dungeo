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
    WARRIOR = 1
    SCOUT = 2
    SHAMAN = 3

class TileType(Enum):
    EMPTY = 1
    MONSTER = 2
    TREASURE = 3
    STORY = 4

class Tile:
    def __init__(self, type, revealed=False):
        self.type = type
        self.revealed = revealed

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
                rand = random.random()
                if rand < 0.5:
                    tile_type = TileType.EMPTY
                elif rand < 0.75:
                    tile_type = TileType.MONSTER
                elif rand < 0.9:
                    tile_type = TileType.TREASURE
                else:
                    tile_type = TileType.STORY
                row.append(Tile(tile_type))
            self.grid.append(row)
        
        # Ensure starting tile is empty and revealed
        self.grid[self.player_pos[1]][self.player_pos[0]] = Tile(TileType.EMPTY, True)

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
        self.title_font = pygame.font.Font(None, 74)
        self.menu_font = pygame.font.Font(None, 36)

        self.game_board = None
        self.player_stats = None

    def init_game(self):
        self.game_board = GameBoard()
        self.player_stats = {
            "hp": self.class_stats[self.selected_class]["HP"],
            "max_hp": self.class_stats[self.selected_class]["HP"],
            "atk": self.class_stats[self.selected_class]["ATK"],
            "def": self.class_stats[self.selected_class]["DEF"],
            "spirit": 3,
            "max_spirit": 3
        }

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
            if event.key == pygame.K_ESCAPE:
                self.state = GameState.MAIN_MENU
            elif event.key == pygame.K_w:
                self.selected_class = CharacterClass.WARRIOR
            elif event.key == pygame.K_s:
                self.selected_class = CharacterClass.SCOUT
            elif event.key == pygame.K_m:
                self.selected_class = CharacterClass.SHAMAN
            elif event.key == pygame.K_r:  # Random name generation
                self.character_name = self.generate_random_name()
            elif event.key == pygame.K_RETURN and self.selected_class and self.character_name:
                self.init_game()
                self.state = GameState.GAME_BOARD
            elif event.key == pygame.K_BACKSPACE:
                self.character_name = self.character_name[:-1]
            elif len(self.character_name) < 15 and event.unicode.isalnum():
                self.character_name += event.unicode

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
            self.state = GameState.COMBAT
        elif tile_type == TileType.TREASURE:
            # TODO: Implement treasure collection
            pass
        elif tile_type == TileType.STORY:
            # TODO: Implement story events
            pass

    def draw_hex_tile(self, x, y, revealed, tile_type):
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

        pygame.draw.polygon(self.screen, color, points)
        pygame.draw.polygon(self.screen, WHITE, points, 1)

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
                self.draw_hex_tile(x, y, tile.revealed, tile.type)
        
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
        self.screen.fill(BLACK)
        
        # Draw title
        title_surface = self.title_font.render("Create Your Character", True, GOLD)
        title_rect = title_surface.get_rect(center=(WINDOW_WIDTH // 2, 50))
        self.screen.blit(title_surface, title_rect)
        
        # Draw class options
        classes = [
            ("WARRIOR (W)", CharacterClass.WARRIOR),
            ("SCOUT (S)", CharacterClass.SCOUT),
            ("SHAMAN (M)", CharacterClass.SHAMAN)
        ]
        
        for i, (class_name, class_type) in enumerate(classes):
            color = GOLD if self.selected_class == class_type else WHITE
            text_surface = self.menu_font.render(class_name, True, color)
            self.screen.blit(text_surface, (50, 200 + i * 50))
        
        # Draw stats if class is selected
        if self.selected_class:
            stats = self.class_stats[self.selected_class]
            stats_pos_x = WINDOW_WIDTH - 250
            self.screen.blit(self.menu_font.render(f"HP:  {stats['HP']}", True, WHITE), (stats_pos_x, 200))
            self.screen.blit(self.menu_font.render(f"ATK: {stats['ATK']}", True, WHITE), (stats_pos_x, 250))
            self.screen.blit(self.menu_font.render(f"DEF: {stats['DEF']}", True, WHITE), (stats_pos_x, 300))
        
        # Draw name input
        name_text = self.menu_font.render(f"Name: {self.character_name}_", True, WHITE)
        self.screen.blit(name_text, (50, 400))
        
        # Draw random name button
        random_text = self.menu_font.render("[R] Random Name", True, WHITE)
        self.screen.blit(random_text, (50, 450))
        
        # Draw navigation buttons
        back = self.menu_font.render("[ESC] Back", True, GRAY)
        begin = self.menu_font.render("[ENTER] Begin Quest", True, GOLD if self.selected_class and self.character_name else GRAY)
        self.screen.blit(back, (50, WINDOW_HEIGHT - 50))
        self.screen.blit(begin, (WINDOW_WIDTH - 250, WINDOW_HEIGHT - 50))

    def draw_combat(self):
        self.screen.fill(BLACK)
        text_surface = self.title_font.render("COMBAT", True, WHITE)
        text_rect = text_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        self.screen.blit(text_surface, text_rect)

    def draw_ending(self):
        self.screen.fill(BLACK)
        text_surface = self.title_font.render("THE END", True, GOLD)
        text_rect = text_surface.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
        self.screen.blit(text_surface, text_rect)

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if self.state == GameState.MAIN_MENU:
                    self.handle_main_menu_input(event)
                elif self.state == GameState.SETTINGS:
                    self.handle_settings_input(event)
                elif self.state == GameState.CHARACTER_SELECT:
                    self.handle_character_select_input(event)
                elif self.state == GameState.GAME_BOARD:
                    self.handle_game_board_input(event)
            
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
