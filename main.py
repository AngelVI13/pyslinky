import subprocess

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
        self.pos = START_POS
        self.move_history = []
        # --- Images
        # -- Squares
        dark_square = pygame.image.load('assets/square brown dark_png_128px.png')
        light_square = pygame.image.load('assets/square brown light_png_128px.png')
        highlight_square = pygame.image.load('assets/square gray light _png_128px.png')
        self.dark_square = pygame.transform.scale(dark_square, (SQUARE_SIZE, SQUARE_SIZE))
        self.light_square = pygame.transform.scale(light_square, (SQUARE_SIZE, SQUARE_SIZE))
        self.highlight_square = pygame.transform.scale(highlight_square , (SQUARE_SIZE, SQUARE_SIZE))

        self.piece_images = {}
        # -- Pawns
        # todo are member variables needed ?
        black_pawn = pygame.image.load('assets/b_pawn_png_128px.png')
        white_pawn = pygame.image.load('assets/w_pawn_png_128px.png')
        # todo move scaling values to dict so that they can be used later
        # todo to determine the padding from top and bottom needed
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
        clicked_square_idx = None

        done = False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True

                if event.type == pygame.MOUSEBUTTONUP:
                    sq_idx = self.get_square_under_mouse(event.pos)
                    moves = self.get_allowed_moves(sq_idx)

                    if clicked_square_idx is not None and sq_idx != clicked_square_idx:
                        self.move_piece(clicked_square_idx, sq_idx)
                        clicked_square_idx = None
                    else:
                        if moves:  # I have allowed moves for this square -> set it as clicked
                            clicked_square_idx = sq_idx

            self.canvas.fill(pygame.Color('black'))

            self.draw_squares()
            self.draw_clicked_square(clicked_square_idx)  # highlight clicked sq
            self.draw_pos()

            pygame.display.flip()

            self.clock.tick(10)

    @staticmethod
    def get_square_under_mouse(coords):
        width, height = coords
        width_idx = width // SQUARE_SIZE  # todo might need to add offset or sth here later
        height_idx = height // SQUARE_SIZE
        square_idx = height_idx*ROWS + width_idx
        return square_idx

    def move_piece(self, from_sq, to_sq):
        piece_from = self.pos[from_sq]
        self.pos[from_sq] = EMPTY  # remove piece from square
        self.pos[to_sq] = piece_from  # put piece in destination

        # this is used to track evey move since starting position
        self.move_history.append(self.get_move_str(from_sq, to_sq))

    def parse_engine_moves(self, moves_str: str):
        idx = moves_str.find("Moves found:")  # find start of moves string
        moves_str = moves_str[idx:]  # remove everything before that from string
        idx = moves_str.find("->")  # find delimiter where moves start
        moves_str = moves_str[idx + len("->"):].strip()  # remove everything before it
        moves = moves_str.split(",")  # split moves based on commas
        moves = map(lambda m: m.strip(), moves)  # remove extra whitespaces from move str
        return filter(lambda x: x != '', moves)  # return all non empty strings

    def get_allowed_moves(self, sq):
        def is_start_square(move_):
            # check if sq matches the from part of move notation
            return self.get_sq_str(sq) in move_[:2]

        # todo instead of sending new, start sending what UCI protocol does
        # todo i.e. position startpos d2d4 (position indicates new position, startpos means start,
        #  todo d2d4... all moves after start pos)
        engine = subprocess.run(["slinky.exe", "new, getmoves"], stdout=subprocess.PIPE)
        output = engine.stdout.decode('utf-8')
        moves = self.parse_engine_moves(output)
        moves_for_square = list(filter(is_start_square, moves))
        return moves_for_square

    @classmethod
    def get_move_str(cls, from_sq, to_sq):
        return f'{cls.get_sq_str(from_sq)}{cls.get_sq_str(to_sq)}'

    @staticmethod
    def get_sq_str(sq):
        row, col = divmod(sq, ROWS)
        return f'{RANK_CHAR[col]}{ROWS-row}'  # subtraction is needed since index 0 is a8 and not a1

    def draw_squares(self):
        for i in range(BOARD_SIZE):
            row, _ = divmod(i, ROWS)
            idx = i + row  # this ensures that the start of each row varies from one row to the other
            if idx % 2 == 0:  # if value is even draw light else draw dark square
                self.canvas.blit(self.light_square, self.square_loc[i])
            else:
                self.canvas.blit(self.dark_square, self.square_loc[i])

    def draw_pos(self):
        for idx, piece in enumerate(self.pos):
            if piece != EMPTY:
                self.canvas.blit(self.piece_images[piece], self.square_loc[idx])

    def draw_clicked_square(self, sq):
        if sq is not None:
            self.canvas.blit(self.highlight_square, self.square_loc[sq])

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
