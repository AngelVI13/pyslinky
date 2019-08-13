from lib.constants import *


class Conversion:
    """Initializes square conversions lists to map from 120 to 64 based lib representation,
    Initialize lists that hold information about which rank & file a square is on the lib.
    """
    def __init__(self):
        sq64 = 0
        self.FilesBoard: List[int] = [OFF_BOARD] * BOARD_SQUARE_NUMBER
        self.RanksBoard: List[int] = [OFF_BOARD] * BOARD_SQUARE_NUMBER
        self.Sq120ToSq64: List[int] = [0] * BOARD_SQUARE_NUMBER
        self.Sq64ToSq120: List[int] = [0] * 64

        for rank in range(RANK_8 + 1):
            for file in range(FILE_H + 1):
                sq = convert_file_rank_to_square(file, rank)
                self.FilesBoard[sq] = file
                self.RanksBoard[sq] = rank

                self.Sq64ToSq120[sq64] = sq
                self.Sq120ToSq64[sq] = sq64
                sq64 += 1


def convert_file_rank_to_square(file: int, rank: int) -> int:
    """Converts given file and rank to a square index (120-based)"""
    return (21 + file) + (rank * 10)
