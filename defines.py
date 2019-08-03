DEFAULT_CANVAS_WIDTH = 800
DEFAULT_CANVAS_HEIGHT = 600
SQUARE_SIZE = 64
ROWS = 8
BOARD_SIZE = ROWS * ROWS

PAWN_PADDING_LEFT = 8
PAWN_PADDING_TOP = 3

(BKING, BQUEEN, BROOK, BBISHOP, BKNIGHT, BPAWN,  # [-6;-1]
 EMPTY,  # [0]
 WPAWN, WKNIGHT, WBISHOP, WROOK, WQUEEN, WKING) = range(-6, 7, 1)  # [1;6]

START_POS = [
    BROOK, BKNIGHT, BBISHOP, BKING, BQUEEN, BBISHOP, BKNIGHT, BROOK,
    *[BPAWN]*ROWS,
    *[EMPTY]*ROWS,
    *[EMPTY]*ROWS,
    *[EMPTY]*ROWS,
    *[EMPTY]*ROWS,
    *[WPAWN]*ROWS,
    WROOK, WKNIGHT, WBISHOP, WQUEEN, WKING, WBISHOP, WKNIGHT, WROOK,
]
print(START_POS)
