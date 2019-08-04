import pygame
from defines import *


class Board:
    def __init__(self):
        pass


class Game:
    def __init__(self, screen_width, screen_height):
        self.canvas = pygame.display.set_mode((screen_width, screen_height))
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.clock = pygame.time.Clock()

        self.square_loc = self.compute_square_locations()
        # --- Images
        # -- Squares
        dark_square = pygame.image.load('assets/square brown dark_png_128px.png')
        light_square = pygame.image.load('assets/square brown light_png_128px.png')
        self.dark_square = pygame.transform.scale(dark_square, (SQUARE_SIZE, SQUARE_SIZE))
        self.light_square = pygame.transform.scale(light_square, (SQUARE_SIZE, SQUARE_SIZE))

        self.piece_images = {}
        # -- Pawns
        # todo are member variables needed ?
        black_pawn = pygame.image.load('assets/b_pawn_png_128px.png')
        white_pawn = pygame.image.load('assets/w_pawn_png_128px.png')
        self.black_pawn = pygame.transform.scale(black_pawn, (48, 58))
        self.white_pawn = pygame.transform.scale(white_pawn, (48, 58))

        self.piece_images[BPAWN] = self.black_pawn
        self.piece_images[WPAWN] = self.white_pawn

        # -- Knights
        black_knight = pygame.image.load('assets/b_knight_png_128px.png')
        white_knight = pygame.image.load('assets/w_knight_png_128px.png')
        self.black_knight = pygame.transform.scale(black_knight, (52, 58))
        self.white_knight = pygame.transform.scale(white_knight, (52, 58))

        self.piece_images[BKNIGHT] = self.black_knight
        self.piece_images[WKNIGHT] = self.white_knight

        # -- Bishops
        black_bishop = pygame.image.load('assets/b_bishop_png_128px.png')
        white_bishop = pygame.image.load('assets/w_bishop_png_128px.png')
        self.black_bishop = pygame.transform.scale(black_bishop, (58, 58))
        self.white_bishop = pygame.transform.scale(white_bishop, (58, 58))

        self.piece_images[BBISHOP] = self.black_bishop
        self.piece_images[WBISHOP] = self.white_bishop

        # -- Rooks
        black_rook = pygame.image.load('assets/b_rook_png_128px.png')
        white_rook = pygame.image.load('assets/w_rook_png_128px.png')
        self.black_rook = pygame.transform.scale(black_rook, (53, 58))
        self.white_rook = pygame.transform.scale(white_rook, (53, 58))

        self.piece_images[BROOK] = self.black_rook
        self.piece_images[WROOK] = self.white_rook

        # -- Queens
        black_queen = pygame.image.load('assets/b_queen_png_128px.png')
        white_queen = pygame.image.load('assets/w_queen_png_128px.png')
        self.black_queen = pygame.transform.scale(black_queen, (58, 52))
        self.white_queen = pygame.transform.scale(white_queen, (58, 52))

        self.piece_images[BQUEEN] = self.black_queen
        self.piece_images[WQUEEN] = self.white_queen

        # -- Kings
        black_king = pygame.image.load('assets/b_king_png_128px.png')
        white_king = pygame.image.load('assets/w_king_png_128px.png')
        self.black_king = pygame.transform.scale(black_king, (58, 58))
        self.white_king = pygame.transform.scale(white_king, (58, 58))

        self.piece_images[BKING] = self.black_king
        self.piece_images[WKING] = self.white_king

    def run(self):
        done = False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True

            self.canvas.fill(pygame.Color('black'))

            self.draw_squares()
            self.draw_pos()

            pygame.display.flip()

            self.clock.tick(10)

    def draw_squares(self):
        for i in range(BOARD_SIZE):
            row, _ = divmod(i, ROWS)
            idx = i + row  # this ensures that the start of each row varies from one row to the other
            if idx % 2 == 0:  # if value is even draw light else draw dark square
                self.canvas.blit(self.light_square, self.square_loc[i])
            else:
                self.canvas.blit(self.dark_square, self.square_loc[i])

    def draw_pos(self):
        for idx, piece in enumerate(START_POS):
            if piece != EMPTY:
                self.canvas.blit(self.piece_images[piece], self.square_loc[idx])

    def draw_pawns(self):
        width, height = self.square_loc[59]
        self.canvas.blit(self.white_pawn, (width + PAWN_PADDING_LEFT, height + PAWN_PADDING_TOP))

    @staticmethod
    def compute_square_locations():
        square_loc = {}
        for i in range(BOARD_SIZE):
            row, col = divmod(i, ROWS)
            square_loc[i] = (col * SQUARE_SIZE, row * SQUARE_SIZE)
        return square_loc

    @staticmethod
    def display_text(text, font_type, font_size, canvas, location, bold=False, italic=False):
        # SysFont(name, size, bold=False, italic=False) -> Font
        font = pygame.font.SysFont(font_type, font_size, bold, italic)

        # render(text, antialias, color, background=None) -> Surface
        text_surface = font.render(text, True, pygame.Color('white'))

        canvas.blit(text_surface, location)


if __name__ == '__main__':
    pygame.init()
    game = Game(DEFAULT_CANVAS_WIDTH, DEFAULT_CANVAS_HEIGHT)
    game.run()
