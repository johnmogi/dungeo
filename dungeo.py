import pygame
import sys
import os
from enum import Enum

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Constants
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
GOLD = (255, 215, 0)

class GameState(Enum):
    MAIN_MENU = 1
    CHARACTER_SELECT = 2
    GAME_BOARD = 3
    COMBAT = 4

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Dungeo")
        self.clock = pygame.time.Clock()
        self.state = GameState.MAIN_MENU
        self.sound_on = True
        self.god_mode = False
        self.menu_index = 0
        self.menu_options = ["Start Game", "Options", "God Mode", "Exit"]
        
        # Load assets
        self.background = pygame.image.load(os.path.join('assets', 'dungeo.jpg'))
        self.background = pygame.transform.scale(self.background, (WINDOW_WIDTH, WINDOW_HEIGHT))
        
        # Font setup
        self.title_font = pygame.font.Font(None, 74)
        self.menu_font = pygame.font.Font(None, 36)

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
        if self.menu_options[self.menu_index] == "Start Game":
            self.state = GameState.CHARACTER_SELECT
        elif self.menu_options[self.menu_index] == "Options":
            self.sound_on = not self.sound_on
        elif self.menu_options[self.menu_index] == "God Mode":
            password = input("Enter password: ")  # This is temporary, we'll make a proper UI for this
            if password == "1234":
                self.god_mode = True
        elif self.menu_options[self.menu_index] == "Exit":
            pygame.quit()
            sys.exit()

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
        
        # Draw god mode status if active
        if self.god_mode:
            god_surface = self.menu_font.render("God Mode: Active", True, GOLD)
            self.screen.blit(god_surface, (WINDOW_WIDTH - 200, WINDOW_HEIGHT - 30))

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if self.state == GameState.MAIN_MENU:
                    self.handle_main_menu_input(event)
            
            # Clear screen
            self.screen.fill(BLACK)
            
            # Draw current state
            if self.state == GameState.MAIN_MENU:
                self.draw_main_menu()
            
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()
