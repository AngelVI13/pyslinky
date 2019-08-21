import sys
import logging

import grpc
import pygame
import protos.adapter_pb2
import protos.adapter_pb2_grpc

from app.defines import *
from app.helpers import Helpers
from lib.board import Board


logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)


class Game:
    def __init__(self, screen_width, screen_height):
        self.canvas = pygame.display.set_mode((screen_width, screen_height))
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.clock = pygame.time.Clock()

        self.helpers = Helpers()  # class defines helper functions

        # indicates if board should be drawn in reverse i.e. black is on the bottom of the screen
        self.revesed_board = False
        self.square_loc = self.helpers.compute_square_locations(self.revesed_board)

        # --- Board related vars
        self.board = Board()
        self.board.parse_fen(START_FEN)  # mate in two '3k4/8/8/3K4/8/8/1Q6/8 w --'
        self.move_history = []
        # --- Engine process
        self.stub = None
        self.engine_info = None
        self.movetime = '1500'  # default engine move time in ms
        # --

        self.highlighted_moves = []
        self.promotion_moves = []
        # after promotion moves are drawn, this stores info about where each promotion move is drawn on the board
        self.promotion_choices = {}
        self.clicked_square_idx = None
        # --- Images
        # -- Squares
        dark_square = pygame.image.load('assets/square brown dark_png_128px.png')
        light_square = pygame.image.load('assets/square brown light_png_128px.png')
        black_square = pygame.image.load('assets/square gray dark _png_128px.png')
        highlight_check_square = pygame.image.load('assets/highlighted_1.png')
        highlight_square = pygame.image.load('assets/highlighted_2.png')
        highlight_move_square = pygame.image.load('assets/highlighted_3.png')
        self.dark_square = pygame.transform.scale(dark_square, (SQUARE_SIZE, SQUARE_SIZE))
        self.light_square = pygame.transform.scale(light_square, (SQUARE_SIZE, SQUARE_SIZE))
        self.black_square = pygame.transform.scale(black_square, (SQUARE_SIZE, SQUARE_SIZE))
        self.highlight_check_square = highlight_check_square
        self.highlight_square = highlight_square
        self.highlight_move_square = highlight_move_square

        self.piece_images = self.helpers.load_assets()

        self.user_side = WHITE
        self.user_name = 'Player1'
        self.fen = ''
        self.last_move = ''
        self.in_check_sq = None
        self.engine_triggered = False

    def reset_board(self):
        self.board = Board()
        self.board.parse_fen(START_FEN)
        self.move_history = []
        self.movetime = '1500'

        self.reset_highlighted_moves()

        self.user_side = WHITE
        self.fen = ''
        self.last_move = ''
        self.in_check_sq = None
        self.engine_triggered = False

    def reset_highlighted_moves(self):  # Resets all highlighted squares
        self.clicked_square_idx = None
        self.highlighted_moves = []
        self.promotion_moves = []
        self.promotion_choices = {}

    def parse_engine_info(self, call_future):  # todo use info from here to display engine info
        response = call_future.result()
        out = response.text

        engine_info = {}
        for line in out.split('\n'):
            if 'id name' in line:
                _, name = line.split('id name', maxsplit=1)
                engine_info['name'] = name.strip()
            elif 'id author' in line:
                _, author = line.split('id author', maxsplit=1)
                engine_info['author'] = author.strip()

        self.engine_info = engine_info

    def connect_to_engine(self, port):
        # --- Connect to engine process
        channel = grpc.insecure_channel(f'localhost:{port}')
        self.stub = protos.adapter_pb2_grpc.AdapterStub(channel)
        self.init_engine_uci()
        self.engine_info = None
        # --

    def init_engine_uci(self):
        message = protos.adapter_pb2.Request(text="uci\n", timeout=1)  # todo move engine command definitions to their own class
        call_future = self.stub.ExecuteEngineCommand.future(message)
        call_future.add_done_callback(self.parse_engine_info)

    def play_game(self, engine_options, settings):
        self.reset_board()
        self.connect_to_engine(port=engine_options["engine_port"])

        if settings:
            fen = settings['fen_text']

            if '<optional>' in fen:
                self.fen = START_FEN
            elif len(fen) > 10:
                self.fen = fen
            else:
                Exception('Invalid fen')

            self.board.parse_fen(self.fen)

            _, setting_idx = settings['difficulty']
            _, movetime = DIFFICULTY_SETTINGS[setting_idx]
            self.movetime = movetime

            _, side_idx = settings['engine_side']
            _, engine_side = ENGINE_SIDE_SETTINGS[side_idx]
            self.user_side = engine_side ^ 1  # the user side is the opposite of the engine

            if self.user_side == BLACK:
                self.revesed_board = True  # show board from user perspective
                self.square_loc = self.helpers.compute_square_locations(self.revesed_board)
            else:
                self.revesed_board = False

            self.user_name = settings['player_name']

        self.run()

    def run(self):
        done = False
        while not done:
            # check for game result:
            if self.board.get_result(self.board.playerJustMoved):
                self.draw_board()  # draw last board state before game over
                return self.game_over()  # return back to main menu

            # If it is the opposite side's turn and the engine hasn't been triggered already
            # and the engine has been initialized i.e. engine_info is available
            if self.user_side ^ 1 == self.board.side and self.engine_triggered is False and self.engine_info:
                self.make_engine_move()
                self.engine_triggered = True

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True

                if event.type == pygame.MOUSEBUTTONUP:
                    if self.user_side == self.board.side:
                        self.handle_mouse_click(event.pos)

            self.draw_board()

            pygame.display.flip()
            self.clock.tick(10)  # 10 FPS

    def draw_board(self):
        """Draws all board related information: squares, info banner, pieces etc"""
        self.canvas.fill(pygame.Color('black'))
        self.draw_info_banner()
        self.draw_squares()
        self.draw_clicked_square()  # highlight clicked sq
        self.draw_highlighted_move()  # draw last made move
        self.draw_highlighted_squares()  # available moves for square
        self.draw_sq_in_check()  # draw square in check
        self.draw_pos()
        self.draw_promotion_moves()

    def game_over(self):
        for i in self.square_loc:
            self.helpers.blit_alpha(self.canvas, self.black_square, self.square_loc[i], opacity=100)

        self.helpers.display_text("Game Over", font_type="sans", font_size=50, canvas=self.canvas,
                                  location=(self.screen_width // 2 - 110, self.screen_height // 2 - 50), bold=True)
        self.helpers.display_text("Click anywhere to go back to main menu", font_type="sans", font_size=20,
                                  canvas=self.canvas, location=(self.screen_width // 2 - 160,
                                                                self.screen_height // 2 + 20), bold=True)
        # todo add info who won
        pygame.display.flip()

        done = False
        while not done:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()

                if event.type == pygame.MOUSEBUTTONUP:
                    return  # return back to main menu

            self.clock.tick(10)  # 10 FPS todo replace with const

    def handle_mouse_click(self, pos):
        sq_idx = self.helpers.get_square_under_mouse(pos, reversed_=self.revesed_board)

        if self.promotion_moves and sq_idx in self.promotion_choices:
            # if user clicked on the available promotion options
            self.move_piece(self.promotion_choices[sq_idx])
            self.reset_highlighted_moves()

        if self.clicked_square_idx is not None and sq_idx != self.clicked_square_idx:
            # get all moves where selected piece can move to and check if
            # sq_idx is one of them
            to_sq_str = self.helpers.get_sq_str(sq_idx)
            moves_for_square = list(filter(lambda move: to_sq_str in move[self.helpers.to_square],
                                           self.highlighted_moves))
            if len(moves_for_square) == 1:
                move_str = self.helpers.get_move_str(self.clicked_square_idx, sq_idx)
                self.move_piece(move_str)
                self.clicked_square_idx = None
                self.highlighted_moves = []
            elif len(moves_for_square) > 1:
                # this is the case for promotions a lot of moves match the 'FROM' and 'TO' squares
                # but differ in the promotion piece
                self.promotion_moves = moves_for_square
            else:
                # selected square is not one of the available moves -> reset clicking options
                self.reset_highlighted_moves()
        elif self.clicked_square_idx is not None and sq_idx == self.clicked_square_idx:
            # if clicked on same square disable highlighting
            self.reset_highlighted_moves()
        else:
            self.highlighted_moves = self.get_allowed_moves(sq_idx)
            if self.highlighted_moves:  # I have allowed moves for this square -> set it as clicked
                self.clicked_square_idx = sq_idx

    def move_piece(self, move_str):
        self.last_move = move_str
        self.board.make_move(self.board.parse_move(move_str))

        in_check = self.board.is_square_attacked(self.board.kingSquare[self.board.side],
                                                 self.board.side ^ 1)
        # if we are in check get square that should be highlighted
        sq = self.get_draw_square(self.board.kingSquare[self.board.side])
        self.in_check_sq = sq if in_check else None

        # this is used to track evey move since starting position
        self.move_history.append(move_str)

    def get_position_string(self):
        command = "position"
        if self.fen:
            command = ' '.join([command, 'fen', self.fen])
        else:
            command = ' '.join([command, 'startpos'])

        if self.move_history:
            command = ' '.join([command, 'moves', *self.move_history])
        return ''.join([command, '\n'])

    def parse_engine_response(self, call_future):
        response = call_future.result()
        out = response.text
        logging.info(out)
        move_ = out.split('bestmove ')[-1]  # todo make this nicer
        move_ = move_.split(' ')[0]  # take the first word after bestmove
        move_ = move_.strip()
        logging.info(f'Received move: {move_}')
        self.board.parse_move(move_)
        self.board.make_move(self.board.parse_move(move_))
        self.last_move = move_
        self.move_history.append(self.last_move)

        in_check = self.board.is_square_attacked(self.board.kingSquare[self.board.side], self.board.side ^ 1)
        # if we are in check get square that should be highlighted
        sq = self.get_draw_square(self.board.kingSquare[self.board.side])
        self.in_check_sq = sq if in_check else None

        self.engine_triggered = False  # reset to default value

    def parse_isready_and_set_position(self, call_future):
        response = call_future.result()
        out = response.text
        logging.info(f'Response to isready: {out}')
        assert 'readyok' in out

        # set position
        command = self.get_position_string()
        message = protos.adapter_pb2.Request(text=command, timeout=1)
        logging.info(f'Sending: {message}')
        call_future = self.stub.ExecuteEngineCommand.future(message)  # no response is expected
        call_future.add_done_callback(self.send_go_command)

    def send_go_command(self, _):
        """This method is called from parse_isready_and_set_position. Setting position command
        does not return any response so here we simply send GO command to engine with
        predefined parameters.
        """

        # set parameters and start engine search
        # 4 seconds timeout for a request that takes 3 seconds
        message = protos.adapter_pb2.Request(text=f"go movetime {self.movetime}\n", timeout=2)
        logging.info(f'Sending: {message}')
        call_future = self.stub.ExecuteEngineCommand.future(message)
        call_future.add_done_callback(self.parse_engine_response)

    def make_engine_move(self):
        """This starts a callback chain that asks engine if it is ready then sends the engine
        the position to search and then sends GO command and parses response of engine analysis.
        """
        message = protos.adapter_pb2.Request(text="isready\n", timeout=1)
        logging.info(f'Sending: {message}')
        call_future = self.stub.ExecuteEngineCommand.future(message)
        call_future.add_done_callback(self.parse_isready_and_set_position)

    def get_allowed_moves(self, sq):
        def is_start_square(move_):
            # check if sq matches the from part of move notation
            return self.helpers.get_sq_str(sq) in move_[self.helpers.from_square]

        moves = self.board.get_moves()
        # convert moves to string
        moves = map(lambda move_: self.board.moveGenerator.print_move(move_), moves)
        # filter out moves that don't start with the same start square
        moves_for_square = list(filter(is_start_square, moves))
        return moves_for_square

    def get_draw_square(self, sq: int) -> int:
        """Convert a square from 120 board representation of chess logic
        to 64-based representation of GUI grid.
        """
        sq = self.board.conversion.Sq120ToSq64[sq]
        row, col = divmod(sq, ROWS)
        sq = (ROWS - row - 1) * ROWS + col
        return sq

    def draw_info_banner(self):
        """Draw banner at the bottom of the screen indicating player names and whose turn it is to move"""
        banner_y = ROWS * SQUARE_SIZE

        # draw banner background
        colour = BROWN_COLOR
        banner = pygame.Surface((self.screen_width, INFO_HEIGHT))
        banner.fill(color=colour)
        self.canvas.blit(banner, (0, banner_y))

        separator_thickness = 2  # 2px thickness of separators
        # draw separator from game canvas to banner canvas
        sep = pygame.Surface((self.screen_width, separator_thickness))
        sep.fill(color=BLACK_COLOR)
        self.canvas.blit(sep, (0, banner_y))

        # vertical separator
        vsep = pygame.Surface((separator_thickness, INFO_HEIGHT))
        vsep.fill(color=BLACK_COLOR)
        self.canvas.blit(vsep, (self.screen_width // 2 - separator_thickness // 2, banner_y))

        # draw side to move highlight
        highlight_size = (self.screen_width // 2 - separator_thickness // 2, banner_y - separator_thickness)
        if self.board.side == WHITE:
            highlight_location = (0, banner_y + separator_thickness)
        else:
            highlight_location = (self.screen_width // 2 + separator_thickness // 2, banner_y + separator_thickness)

        highlight_colour = LIGHT_BROWN_COLOR
        side_highlight = pygame.Surface(highlight_size)
        side_highlight.fill(color=highlight_colour)
        self.canvas.blit(side_highlight, highlight_location)

        if self.engine_info:  # give some time for engine to load before displaying names
            # add player names
            x_padding = y_padding = 10
            white_location = (x_padding, banner_y + y_padding)
            black_location = (self.screen_width // 2 + separator_thickness // 2 + x_padding, banner_y + y_padding)
            white_name = self.user_name if self.user_side == WHITE else self.engine_info['name']
            black_name = self.user_name if self.user_side == BLACK else self.engine_info['name']

            self.helpers.display_text(text=white_name, font_type="sans", font_size=30, canvas=self.canvas,
                                      location=white_location, bold=True, color='white')

            self.helpers.display_text(text=black_name, font_type="sans", font_size=30, canvas=self.canvas,
                                      location=black_location, bold=True, color='black')

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
                idx = self.get_draw_square(idx)
                w, h = self.square_loc[idx]
                image_w, image_h = IMAGE_SIZES[piece]
                padding_w, padding_h = (SQUARE_SIZE - image_w) // 2, (SQUARE_SIZE - image_h) // 2
                self.canvas.blit(self.piece_images[piece], (w + padding_w, h + padding_h))

    def draw_clicked_square(self):
        if self.clicked_square_idx is not None:
            self.canvas.blit(self.highlight_square, self.square_loc[self.clicked_square_idx])

    def draw_highlighted_squares(self):
        drawn_squares = set()
        for move in self.highlighted_moves:
            to_sq = move[self.helpers.to_square]  # the highlighted square is the destination square
            sq = self.helpers.get_sq_from_str(to_sq)

            # when there is a promotion, we are drawing a lot of squares
            # one on top of each other because the moves are the same except for
            # what the promotion piece is
            if sq not in drawn_squares:
                drawn_squares.add(sq)
                self.canvas.blit(self.highlight_square, self.square_loc[sq])

    def draw_highlighted_move(self):
        if self.last_move:
            from_sq_str, to_sq_str = self.last_move[self.helpers.from_square], self.last_move[self.helpers.to_square]
            from_sq, to_sq = self.helpers.get_sq_from_str(from_sq_str), self.helpers.get_sq_from_str(to_sq_str)
            self.canvas.blit(self.highlight_move_square, self.square_loc[from_sq])
            self.canvas.blit(self.highlight_move_square, self.square_loc[to_sq])

    def draw_promotion_moves(self):
        if self.promotion_moves:
            if self.user_side == WHITE:
                promotion_pieces = [WHITE_QUEEN, WHITE_ROOK, WHITE_BISHOP, WHITE_KNIGHT]
            else:
                promotion_pieces = [BLACK_QUEEN, BLACK_ROOK, BLACK_BISHOP, BLACK_KNIGHT]

            move = self.promotion_moves[0]  # take one of the moves to compute the to_sq
            to_sq = self.helpers.get_sq_from_str(move[self.helpers.to_square])  # destination slice
            starting_square = to_sq

            # row increment is used to determine if to put promotion options from bottom up or top down
            # it depends on which part of the board the promotion is taking place
            row_increment = ROWS
            if starting_square + ROWS >= BOARD_SIZE:
                row_increment = -ROWS

            # find the squares on which to put the promotion options
            image_squares = [starting_square + idx*row_increment for idx, _ in enumerate(promotion_pieces)]

            self.promotion_choices = {}  # used to store which sq indicates which promotion option

            # iterate over all promotion options and blit them vertically starting from the destination square
            # Make sure to blit the background as opaque and center the pieces inside the squares
            for piece, sq, move in zip(promotion_pieces, image_squares, self.promotion_moves):
                self.promotion_choices[sq] = move  # save promotion move to the drawn promotion option
                w, h = self.square_loc[sq]
                image_w, image_h = IMAGE_SIZES[piece]
                padding_w, padding_h = (SQUARE_SIZE - image_w) // 2, (SQUARE_SIZE - image_h) // 2
                self.helpers.blit_alpha(self.canvas, self.black_square, self.square_loc[sq], opacity=170)
                self.canvas.blit(self.piece_images[piece], (w + padding_w, h + padding_h))

    def draw_sq_in_check(self):
        if self.in_check_sq:
            self.canvas.blit(self.highlight_check_square, self.square_loc[self.in_check_sq])


if __name__ == '__main__':
    pygame.init()
    game = Game(DEFAULT_CANVAS_WIDTH, DEFAULT_CANVAS_HEIGHT)
    game.run()
