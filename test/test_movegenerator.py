import unittest
from lib.constants import START_FEN, BLACK, WHITE
from lib.board import Board


class TestMoveGenerator(unittest.TestCase):
    def test_start_fen_white(self):
        board = Board()
        board.parse_fen(START_FEN)
        moves = board.moveGenerator.generate_all_moves()

        self.assertEqual(len(moves), 20)

    def test_start_fen_black(self):
        board = Board()
        board.parse_fen(START_FEN)
        board.side = BLACK
        moves = board.moveGenerator.generate_all_moves()

        self.assertEqual(len(moves), 20)

    def test_complex_fen_white(self):
        board = Board()
        complex_fen = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"

        board.parse_fen(complex_fen)
        moves = board.moveGenerator.generate_all_moves()

        self.assertEqual(len(moves), 48)

    def test_complex_fen_white_2(self):
        board = Board()
        complex_fen = "R6R/3Q4/1Q4Q1/4Q3/2Q4Q/Q4Q2/pp1Q4/kBNN1KB1 w -- 0 1"

        board.parse_fen(complex_fen)
        moves = board.moveGenerator.generate_all_moves()

        self.assertEqual(len(moves), 218)

    def test_complex_fen_black(self):
        board = Board()
        complex_fen = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R b KQkq - 0 1"

        board.parse_fen(complex_fen)
        moves = board.moveGenerator.generate_all_moves()

        self.assertEqual(len(moves), 43)


if __name__ == '__main__':
    unittest.main()
