from lib.constants import *

DEFAULT_CANVAS_WIDTH = 8*64  # 800
DEFAULT_CANVAS_HEIGHT = 8*64  # 600
SQUARE_SIZE = 64
ROWS = 8
BOARD_SIZE = ROWS * ROWS

PAWN_PADDING_LEFT = 8
PAWN_PADDING_TOP = 3

FILE_CHAR = dict(zip(range(ROWS), ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']))
FILE_INT = {v: k for k, v in FILE_CHAR.items()}  # inverting above dict so we can get int from char

IMAGE_PATHS = {
    BLACK_PAWN: 'assets/b_pawn_png_128px.png',
    WHITE_PAWN: 'assets/w_pawn_png_128px.png',
    BLACK_KNIGHT: 'assets/b_knight_png_128px.png',
    WHITE_KNIGHT: 'assets/w_knight_png_128px.png',
    BLACK_BISHOP: 'assets/b_bishop_png_128px.png',
    WHITE_BISHOP: 'assets/w_bishop_png_128px.png',
    BLACK_ROOK: 'assets/b_rook_png_128px.png',
    WHITE_ROOK: 'assets/w_rook_png_128px.png',
    BLACK_QUEEN: 'assets/b_queen_png_128px.png',
    WHITE_QUEEN: 'assets/w_queen_png_128px.png',
    BLACK_KING: 'assets/b_king_png_128px.png',
    WHITE_KING: 'assets/w_king_png_128px.png',
}

IMAGE_SIZES = {
    #    : (w, h)
    BLACK_PAWN: (48, 58),
    WHITE_PAWN: (48, 58),
    BLACK_KNIGHT: (52, 58),
    WHITE_KNIGHT: (52, 58),
    BLACK_BISHOP: (58, 58),
    WHITE_BISHOP: (58, 58),
    BLACK_ROOK: (53, 58),
    WHITE_ROOK: (53, 58),
    BLACK_QUEEN: (58, 52),
    WHITE_QUEEN: (58, 52),
    BLACK_KING: (58, 58),
    WHITE_KING: (58, 58),
}
