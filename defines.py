DEFAULT_CANVAS_WIDTH = 800
DEFAULT_CANVAS_HEIGHT = 600
SQUARE_SIZE = 64
ROWS = 8
BOARD_SIZE = ROWS * ROWS

PAWN_PADDING_LEFT = 8
PAWN_PADDING_TOP = 3

PIECE_RANGE = range(-6, 7, 1)

(BKING, BQUEEN, BROOK, BBISHOP, BKNIGHT, BPAWN,  # [-6;-1]
 EMPTY,  # [0]
 WPAWN, WKNIGHT, WBISHOP, WROOK, WQUEEN, WKING) = PIECE_RANGE  # [1;6]

START_POS = [
    BROOK, BKNIGHT, BBISHOP, BQUEEN, BKING, BBISHOP, BKNIGHT, BROOK,
    *[BPAWN]*ROWS,
    *[EMPTY]*ROWS,
    *[EMPTY]*ROWS,
    *[EMPTY]*ROWS,
    *[EMPTY]*ROWS,
    *[WPAWN]*ROWS,
    WROOK, WKNIGHT, WBISHOP, WQUEEN, WKING, WBISHOP, WKNIGHT, WROOK,
]

FILE_CHAR = dict(zip(range(ROWS), ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']))
FILE_INT = {v: k for k, v in FILE_CHAR.items()}  # inverting above dict so we can get int from char

IMAGE_PATHS = {
    BPAWN: 'assets/b_pawn_png_128px.png',
    WPAWN: 'assets/w_pawn_png_128px.png',
    BKNIGHT: 'assets/b_knight_png_128px.png',
    WKNIGHT: 'assets/w_knight_png_128px.png',
    BBISHOP: 'assets/b_bishop_png_128px.png',
    WBISHOP: 'assets/w_bishop_png_128px.png',
    BROOK: 'assets/b_rook_png_128px.png',
    WROOK: 'assets/w_rook_png_128px.png',
    BQUEEN: 'assets/b_queen_png_128px.png',
    WQUEEN: 'assets/w_queen_png_128px.png',
    BKING: 'assets/b_king_png_128px.png',
    WKING: 'assets/w_king_png_128px.png',
}

IMAGE_SIZES = {
    #    : (w, h)
    BPAWN: (48, 58),
    WPAWN: (48, 58),
    BKNIGHT: (52, 58),
    WKNIGHT: (52, 58),
    BBISHOP: (58, 58),
    WBISHOP: (58, 58),
    BROOK: (53, 58),
    WROOK: (53, 58),
    BQUEEN: (58, 52),
    WQUEEN: (58, 52),
    BKING: (58, 58),
    WKING: (58, 58),
}
