from lib.constants import *

SQUARE_SIZE = 64
ROWS = 8
BOARD_SIZE = ROWS * ROWS
INFO_HEIGHT = 50
DEFAULT_CANVAS_WIDTH = ROWS * SQUARE_SIZE
DEFAULT_CANVAS_HEIGHT = ROWS * SQUARE_SIZE + INFO_HEIGHT

# in pixels, corresponding from top left edge of square (based on 64x64pixel square)
PAWN_PADDING_LEFT = 8
PAWN_PADDING_TOP = 3

MENU_FPS = 10

FILE_CHAR = dict(zip(range(ROWS), ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']))
FILE_INT = {v: k for k, v in FILE_CHAR.items()}  # inverting above dict so we can get int from char

# the second elements of the tuples are the duration in milliseconds for which the engine is allowed to
# think before making a move
DIFFICULTY_SETTINGS = [
    ('1', '500'),
    ('2', '800'),
    ('3', '1000'),
    ('4', '1200'),
    ('5', '1500'),
    ('6', '1800'),
    ('7', '2000'),
    ('8', '2500'),
    ('9', '3000'),
    ('10', '5000')
]

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
