import subprocess
import time
from functools import partial
import threading
from queue import Queue, Empty

import grpc
import pygame
from defines import *
import protos.adapter_pb2
import protos.adapter_pb2_grpc



from lib.board import Board

import logging
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

        # --- Board related vars
        self.board = Board()
        self.board.parse_fen(START_FEN)
        self.move_history = []
        # --- Engine process
        channel = grpc.insecure_channel('localhost:50051')
        self.stub = protos.adapter_pb2_grpc.AdapterStub(channel)
        print(self.init_engine_uci())  # todo use info from here to display engine info
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

    @staticmethod
    def load_assets():
        # load all images
        d = {k: pygame.image.load(v) for k, v in IMAGE_PATHS.items()}
        # scale them
        return {k: pygame.transform.scale(v, IMAGE_SIZES[k]) for k, v in d.items()}

    def init_engine_uci(self):
        message = protos.adapter_pb2.Request(text="uci\n", timeout=1)
        response = self.stub.ExecuteEngineCommand(message)

        out = response.text

        engine_info = {}
        for line in out.split('\n'):
            if 'id name' in line:
                _, name = line.split('id name', maxsplit=1)
                engine_info['name'] = name.strip()
            elif 'id author' in line:
                _, author = line.split('id author', maxsplit=1)
                engine_info['author'] = author.strip()

        return engine_info

    @staticmethod
    def output_reader(proc, out_queue: Queue, in_queue: Queue):
        while True:
            line = proc.stdout.readline()
            out_queue.put(line.decode('utf-8'))

            try:
                val = in_queue.get()
            except Empty:
                continue
            else:
                if val is True:
                    break  # terminate thread
        # for line in iter(proc.stdout.readline, b''):
        #     queue.put(line.decode('utf-8'))

    def run(self):

        done = False
        while not done:
            if self.user_side != self.board.side:
                time.sleep(2)
                self.make_engine_move()

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
        square_idx = height_idx*ROWS + width_idx
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
        message = protos.adapter_pb2.Request(text="isready\n", timeout=1)
        response = self.stub.ExecuteEngineCommand(message)

        out = response.text
        assert 'readyok' in out

        # set position
        command = self.get_position_string()
        message = protos.adapter_pb2.Request(text=command, timeout=1)
        _ = self.stub.ExecuteEngineCommand(message)  # no response is expected

        # set parameters and start engine search
        # 4 seconds timeout for a request that takes 3 seconds
        message = protos.adapter_pb2.Request(text="go movetime 3000\n", timeout=2)
        response = self.stub.ExecuteEngineCommand(message)
        out = response.text
        logging.info(out)
        move_ = out.split('bestmove ')[-1]   # .strip()  # todo make this nicer
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

    def exec_engine_command(self, command):
        # todo use some gRPC to a Go service that executes engine commands
        in_queue = Queue()  # move this somewhere else -> don't create a queue for every thread
        t = threading.Thread(target=self.output_reader, args=(self.engine_process, self.engine_out_queue, in_queue, ))
        t.start()

        self.engine_process.stdin.write(command)  # UCI start command
        self.engine_process.stdin.flush()

        time.sleep(3)
        out = []
        while not self.engine_out_queue.empty():
            out.append(self.engine_out_queue.get())

        in_queue.put(True)  # signal to thread to end todo needed ?
        return out

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
