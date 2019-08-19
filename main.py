import logging

import pygame
import pygameMenu

from defines import *
from gui import Game


logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)


class MainMenu:
    def __init__(self, screen_width, screen_height, game_obj):
        self.canvas = pygame.display.set_mode((screen_width, screen_height))
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.clock = pygame.time.Clock()
        self.game = game_obj
        self.data = {}

        # Main menu
        self.main_menu = pygameMenu.Menu(self.canvas, bgfun=self.menu_background,
                                         font=pygameMenu.font.FONT_BEBAS, title="Slinky",
                                         font_color=(0, 0, 0),
                                         font_size=30,
                                         menu_alpha=100,
                                         menu_color=(0x7c, 0x4c, 0x3e),
                                         menu_height=self.screen_height,
                                         menu_width=self.screen_width,
                                         onclose=pygameMenu.events.DISABLE_CLOSE,
                                         option_shadow=False,
                                         window_height=self.screen_height,
                                         window_width=self.screen_width
                                         )  # -> Menu object

        # Settings menu
        self.settings_menu = pygameMenu.Menu(self.canvas,
                                             bgfun=self.menu_background,
                                             color_selected=(255, 255, 255),
                                             font=pygameMenu.font.FONT_HELVETICA,
                                             font_color=(0, 0, 0),
                                             font_size=25,
                                             font_size_title=50,
                                             menu_alpha=100,
                                             menu_color=(0x7c, 0x4c, 0x3e),
                                             menu_height=self.screen_height,
                                             menu_width=self.screen_width,
                                             onclose=pygameMenu.events.DISABLE_CLOSE,
                                             title='Settings',
                                             widget_alignment=pygameMenu.locals.ALIGN_LEFT,
                                             window_height=self.screen_height,
                                             window_width=self.screen_width
                                             )

        # Add text inputs with different configurations
        self.settings_menu.add_text_input('Name: ', default='Player1', textinput_id='player_name')
        self.settings_menu.add_text_input('FEN: ', default='<optional>', textinput_id='fen_text')
        # Create selector with difficulty options
        self.settings_menu.add_selector('Select difficulty (1-10)',
                                        DIFFICULTY_SETTINGS,
                                        selector_id='difficulty',
                                        default=4)

        self.settings_menu.add_option('Store data', self.data_fun)  # Call function
        self.settings_menu.add_option('Return to main menu', pygameMenu.events.BACK,
                                      align=pygameMenu.locals.ALIGN_CENTER)

        self.main_menu.add_option('Play', self.start_game)
        self.main_menu.add_option('Settings', self.settings_menu)
        self.main_menu.add_option('Quit', pygameMenu.events.EXIT)

        self.main_menu.set_fps(fps=MENU_FPS)

    def start_game(self):
        self.game.play_game(settings=self.data)

    def menu_background(self):
        self.canvas.fill(pygame.Color('black'))

    def data_fun(self):
        """Save the data from the menu."""
        self.data = self.settings_menu.get_input_data()

    def show(self):
        done = False
        while not done:
            self.clock.tick(MENU_FPS)

            # Application events
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    done = True

            # Main menu
            self.main_menu.mainloop(events)

            # Flip surface
            pygame.display.flip()


if __name__ == '__main__':
    pygame.init()
    game = Game(DEFAULT_CANVAS_WIDTH, DEFAULT_CANVAS_HEIGHT)
    menu = MainMenu(DEFAULT_CANVAS_WIDTH, DEFAULT_CANVAS_HEIGHT, game)
    menu.show()
