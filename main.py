import subprocess

import grpc
import pygame
from defines import *
import protos.adapter_pb2
import protos.adapter_pb2_grpc

from lib.board import Board

import logging

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)


class Game:
    def __init__(self, screen_width, screen_height):
        self.canvas = pygame.display.set_mode((screen_width, screen_height))
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.clock = pygame.time.Clock()

        self.square_loc = self.compute_square_locations()

        # --- Board related vars
        self.board = Board()
        self.board.parse_fen(START_FEN)
        self.move_history = []
        # --- Engine process
        channel = grpc.insecure_channel('localhost:50051')
        self.stub = protos.adapter_pb2_grpc.AdapterStub(channel)
        self.init_engine_uci()
        # --

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
        self.fen = ''
        self.last_move = ''
        self.in_check_sq = None
        self.engine_triggered = False

    @staticmethod
    def load_assets():
        # load all images
        d = {k: pygame.image.load(v) for k, v in IMAGE_PATHS.items()}
        # scale them
        return {k: pygame.transform.scale(v, IMAGE_SIZES[k]) for k, v in d.items()}

    @staticmethod
    def parse_engine_info(call_future):  # todo use info from here to display engine info
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

        print(engine_info)
        return engine_info

    def init_engine_uci(self):
        message = protos.adapter_pb2.Request(text="uci\n", timeout=1)
        call_future = self.stub.ExecuteEngineCommand.future(message)
        call_future.add_done_callback(self.parse_engine_info)

    def run(self):

        done = False
        while not done:
            if self.user_side != self.board.side and self.engine_triggered is False:
                self.make_engine_move()
                self.engine_triggered = True

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    done = True

                if event.type == pygame.MOUSEBUTTONUP:
                    if self.user_side == self.board.side:
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
        square_idx = height_idx * ROWS + width_idx
        return square_idx

    def move_piece(self, from_sq, to_sq):
        move_str = self.get_move_str(from_sq, to_sq)
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
        move_ = out.split('bestmove ')[-1]  # .strip()  # todo make this nicer
        move_ = move_.split(' ')[0]  # take the first word after bestmove
        move_ = move_.strip()
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
        logging.info(out)
        assert 'readyok' in out

        # set position
        command = self.get_position_string()
        message = protos.adapter_pb2.Request(text=command, timeout=1)
        call_future = self.stub.ExecuteEngineCommand.future(message)  # no response is expected
        call_future.add_done_callback(self.send_go_command)

    def send_go_command(self, _):
        """This method is called from parse_isready_and_set_position. Setting position command
        does not return any response so here we simply send GO command to engine with
        predefined parameters.
        """

        # set parameters and start engine search
        # 4 seconds timeout for a request that takes 3 seconds
        message = protos.adapter_pb2.Request(text="go movetime 3000\n", timeout=2)
        call_future = self.stub.ExecuteEngineCommand.future(message)
        call_future.add_done_callback(self.parse_engine_response)

    def make_engine_move(self):
        """This starts a callback chain that asks engine if it is ready then sends the engine
        the position to search and then sends GO command and parses response of engine analysis.
        """
        message = protos.adapter_pb2.Request(text="isready\n", timeout=1)
        call_future = self.stub.ExecuteEngineCommand.future(message)
        call_future.add_done_callback(self.parse_isready_and_set_position)

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

        moves = self.board.get_moves()
        # convert moves to string
        moves = map(lambda move_: self.board.moveGenerator.print_move(move_), moves)
        # filter out moves that don't start with the same start square
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

    def get_draw_square(self, sq: int) -> int:
        """Convert a square from 120 board representation of chess logic
        to 64-based representation of GUI grid.
        """
        sq = self.board.conversion.Sq120ToSq64[sq]
        row, col = divmod(sq, ROWS)
        sq = (ROWS - row - 1) * ROWS + col
        return sq

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
        for move in self.highlighted_moves:
            # todo here need to take into account promotions
            to_sq = move[2:]  # the highlighted square is the destination square
            sq = self.get_sq_from_str(to_sq)
            self.canvas.blit(self.highlight_square, self.square_loc[sq])

    def draw_highlighted_move(self):
        if self.last_move:
            from_sq_str, to_sq_str = self.last_move[:2], self.last_move[2:4]
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
