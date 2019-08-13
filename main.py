import subprocess
from functools import partial

import pygame
from defines import *

import logging

from lib.board import Board

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)


def get_string_between_markers(text, start_marker, end_marker):
    # find start string
    start_idx = text.find(start_marker)
    # remove everything preceding it from text
    text = text[start_idx + len(start_marker):]

    # find end of string
    end_idx = text.find(end_marker)
    # remove everything after it from text
    result = text[:end_idx]
    # clean up leading and trailing whitespaces
    result = result.strip()
    return result


class EngineResponse:
    # todo end strings are always EOL -> don't need to define them separately
    # todo 2. Instead of having small callbacks just parse output in a dict and return that ?
    fen_start_str = 'FEN: '
    fen_end_str = '\n'

    move_start_str = 'Engine move is '
    move_end_str = '\n'

    king_sq_start_str = 'KingSq: '
    king_sq_end_str = '\n'

    in_check_start_str = 'InCheck: '
    in_check_end_str = '\n'

    extract_fen = partial(get_string_between_markers, start_marker=fen_start_str, end_marker=fen_end_str)
    extract_move = partial(get_string_between_markers, start_marker=move_start_str, end_marker=move_end_str)
    extract_king_sq = partial(get_string_between_markers, start_marker=king_sq_start_str, end_marker=king_sq_end_str)
    extract_in_check = partial(get_string_between_markers, start_marker=in_check_start_str, end_marker=in_check_end_str)


class Game:
    def __init__(self, screen_width, screen_height):
        self.canvas = pygame.display.set_mode((screen_width, screen_height))
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.clock = pygame.time.Clock()

        self.square_loc = self.compute_square_locations()
        self.board = Board()
        self.board.parse_fen(START_FEN)
        self.move_history = []
        self.highlighted_moves = []
        self.clicked_square_idx = None
        # --- Images
        # -- Squares
        dark_square = pygame.image.load('assets/square brown dark_png_128px.png')
        light_square = pygame.image.load('assets/square brown light_png_128px.png')
        highlight_check_square = pygame.image.load('assets/highlighted_1.png')
        highlight_square = pygame.image.load('assets/highlighted_2.png')
        highlight_move_square = pygame.image.load('assets/highlighted_3.png')
        self.dark_square = pygame.transform.scale(dark_square, (SQUARE_SIZE, SQUARE_SIZE))
        self.light_square = pygame.transform.scale(light_square, (SQUARE_SIZE, SQUARE_SIZE))
        self.highlight_check_square = highlight_check_square
        self.highlight_square = highlight_square
        self.highlight_move_square = highlight_move_square

        self.piece_images = self.load_assets()

        self.user_side = WHITE
        self.side_to_move = WHITE
        self.fen = ''
        self.last_move = ''
        self.in_check_sq = None

    @staticmethod
    def load_assets():
        # load all images
        d = {k: pygame.image.load(v) for k, v in IMAGE_PATHS.items()}
        # scale them
        return {k: pygame.transform.scale(v, IMAGE_SIZES[k]) for k, v in d.items()}

    def run(self):

        done = False
        while not done:
            if self.user_side != self.side_to_move:
                self.make_engine_move()
                self.side_to_move ^= 1

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True

                if event.type == pygame.MOUSEBUTTONUP:
                    if self.user_side == self.side_to_move:
                        self.handle_mouse_click(event.pos)

            self.canvas.fill(pygame.Color('black'))

            self.draw_squares()
            self.draw_clicked_square()  # highlight clicked sq
            self.draw_highlighted_squares()  # available moves for square
            self.draw_highlighted_move()  # draw last made move
            self.draw_sq_in_check()  # draw square in check
            self.draw_pos()

            pygame.display.flip()

            self.clock.tick(10)

    def handle_mouse_click(self, pos):
        sq_idx = self.get_square_under_mouse(pos)
        if self.clicked_square_idx is not None and sq_idx != self.clicked_square_idx:
            # get all moves where selected piece can move to and check if
            # sq_idx is one of them
            to_sq_str = self.get_sq_str(sq_idx)
            moves_for_square = filter(lambda move: to_sq_str in move[2:], self.highlighted_moves)
            if len(list(moves_for_square)) != 0:
                self.move_piece(self.clicked_square_idx, sq_idx)
                self.clicked_square_idx = None
                self.highlighted_moves = []
                self.side_to_move ^= 1  # switch side to move
        elif self.clicked_square_idx is not None and sq_idx == self.clicked_square_idx:
            # if clicked on same square disable highlighting
            self.clicked_square_idx = None
            self.highlighted_moves = []
        else:
            self.highlighted_moves = self.get_allowed_moves(sq_idx)
            if self.highlighted_moves:  # I have allowed moves for this square -> set it as clicked
                self.clicked_square_idx = sq_idx

    @staticmethod
    def get_square_under_mouse(coords):
        width, height = coords
        width_idx = width // SQUARE_SIZE  # todo might need to add offset or sth here later
        height_idx = height // SQUARE_SIZE
        square_idx = height_idx*ROWS + width_idx
        return square_idx

    def move_piece(self, from_sq, to_sq):
        move_str = self.get_move_str(from_sq, to_sq)
        self.last_move = move_str
        # response = self.exec_engine_request([move_str])
        print(f'move: {move_str}')
        print(self.board)
        self.board.make_move(self.board.parse_move(move_str))
        print(self.board)

        in_check = self.board.is_square_attacked(self.board.kingSquare[self.board.side],
                                                 self.board.side ^ 1)  # EngineResponse.extract_in_check(output)
        # if we are in check get square that should be highlighted
        self.in_check_sq = self.board.kingSquare[self.board.side] if in_check else None
        # todo this doesn't work -> sq_in_check is a moveint that is 120 based not 64

        # this is used to track evey move since starting position
        self.move_history.append(move_str)

    @staticmethod
    def parse_engine_moves(moves_str: str):
        idx = moves_str.find("Moves found:")  # find start of moves string
        moves_str = moves_str[idx:]  # remove everything before that from string
        idx = moves_str.find("->")  # find delimiter where moves start
        moves_str = moves_str[idx + len("->"):].strip()  # remove everything before it
        moves = moves_str.split(",")  # split moves based on commas
        moves = map(lambda m: m.strip(), moves)  # remove extra whitespaces from move str
        return filter(lambda x: x != '', moves)  # return all non empty strings

    def get_position_string(self):
        command = "position"
        if self.fen:
            command = ' '.join([command, 'fen', self.fen])
        else:
            command = ' '.join([command, 'startpos'])
        return command

    # todo move to board side
    # def parse_fen(self, fen):
    #     fen_parts = fen.split()
    #     piece_layouts, *_ = fen_parts
    #
    #     piece_layouts = piece_layouts.split('/')
    #     flipped = ''.join(piece_layouts)
    #
    #     char_size = 1
    #     index = 0
    #     while flipped:
    #         piece, flipped = flipped[:char_size], flipped[char_size:]
    #         if piece in PIECE_MAP:
    #             self.pos[index] = PIECE_MAP[piece]
    #             index += 1
    #         else:  # there is a digit
    #             for _ in range(int(piece)):
    #                 self.pos[index] = EMPTY
    #                 index += 1

    def make_engine_move(self):
        # output = self.exec_engine_request(["go"])
        # todo hold this in some history in order to display or whatever
        move_int = self.board.get_moves()[0]  # EngineResponse.extract_move(output)
        print(f'Engine move {self.board.moveGenerator.print_move(move_int)}')
        print(self.board)
        self.board.make_move(move_int)
        print(self.board)
        self.last_move = self.board.moveGenerator.print_move(move_int)

        in_check = self.board.is_square_attacked(self.board.kingSquare[self.board.side], self.board.side ^ 1)  # EngineResponse.extract_in_check(output)
        # if we are in check get square that should be highlighted
        self.in_check_sq = self.board.kingSquare[self.board.side] if in_check else None

    # todo for every engine request, parse all game state relevant output
    # todo side to move, fen, poskey etc,
    # todo also add check that if Game is Over is found
    # todo will stop game
    def exec_engine_request(self, commands):
        command = "slinky.exe"
        position = self.get_position_string()
        parameters = ', '.join([f'{position}', *commands])
        logging.info('Exec req params: {}'.format(parameters))
        engine = subprocess.run([command, parameters], stdout=subprocess.PIPE)
        output = engine.stdout.decode('utf-8')
        logging.info(output)
        return output

    def get_allowed_moves(self, sq):
        def is_start_square(move_):
            # check if sq matches the from part of move notation
            return self.get_sq_str(sq) in move_[:2]

        # output = self.exec_engine_request(["getmoves"])
        # moves = self.parse_engine_moves(output)
        moves = self.board.get_moves()
        moves = map(lambda move_: self.board.moveGenerator.print_move(move_), moves)
        moves_for_square = list(filter(is_start_square, moves))
        return moves_for_square

    @classmethod
    def get_move_str(cls, from_sq, to_sq):
        return f'{cls.get_sq_str(from_sq)}{cls.get_sq_str(to_sq)}'

    def get_move_from_str(self, move_str):  # todo promotion moves
        from_sq = move_str[:2]
        to_sq = move_str[2:]
        return self.get_sq_from_str(from_sq), self.get_sq_from_str(to_sq)

    @staticmethod
    def get_sq_str(sq):
        row, col = divmod(sq, ROWS)
        return f'{FILE_CHAR[col]}{ROWS - row}'  # subtraction is needed since index 0 is a8 and not a1

    def draw_squares(self):
        for i in range(BOARD_SIZE):
            row, _ = divmod(i, ROWS)
            idx = i + row  # this ensures that the start of each row varies from one row to the other
            if idx % 2 == 0:  # if value is even draw light else draw dark square
                self.canvas.blit(self.light_square, self.square_loc[i])
            else:
                self.canvas.blit(self.dark_square, self.square_loc[i])

    def draw_pos(self):
        for idx, piece in enumerate(self.board.pieces):
            if piece != EMPTY and piece != OFF_BOARD:
                idx = self.board.conversion.Sq120ToSq64[idx]
                row, col = divmod(idx, ROWS)
                # print(idx, row, col)
                idx = (ROWS - row - 1) * ROWS + col
                w, h = self.square_loc[idx]
                image_w, image_h = IMAGE_SIZES[piece]
                padding_w, padding_h = (SQUARE_SIZE - image_w) // 2, (SQUARE_SIZE - image_h) // 2
                self.canvas.blit(self.piece_images[piece], (w + padding_w, h + padding_h))

    def draw_clicked_square(self):
        if self.clicked_square_idx is not None:
            self.canvas.blit(self.highlight_square, self.square_loc[self.clicked_square_idx])

    def draw_highlighted_squares(self):
        for move in self.highlighted_moves:
            # todo here need to take into account promotions
            to_sq = move[2:]  # the highlighted square is the destination square
            sq = self.get_sq_from_str(to_sq)
            self.canvas.blit(self.highlight_square, self.square_loc[sq])

    def draw_highlighted_move(self):
        if self.last_move:
            from_sq_str, to_sq_str = self.last_move[:2], self.last_move[2:4]  # todo handle promotions
            from_sq, to_sq = self.get_sq_from_str(from_sq_str), self.get_sq_from_str(to_sq_str)
            self.canvas.blit(self.highlight_move_square, self.square_loc[from_sq])
            self.canvas.blit(self.highlight_move_square, self.square_loc[to_sq])

    def draw_sq_in_check(self):
        if self.in_check_sq:
            self.canvas.blit(self.highlight_check_square, self.square_loc[self.in_check_sq])

    @staticmethod
    def get_sq_from_str(sq_str):
        file, rank = sq_str
        file, rank = FILE_INT[file], int(rank)
        sq = (ROWS - rank) * ROWS + file
        return sq

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
