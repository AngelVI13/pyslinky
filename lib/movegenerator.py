from lib.constants import *


# get_move_int creates and returns a move int from given move information
def get_move_int(from_sq: int, to_sq: int, capture_piece: int, promotion_piece: int, flag: int) -> int:
    return from_sq | (to_sq << 7) | (capture_piece << 14) | (promotion_piece << 20) | flag


class MoveGenerator:
    def __init__(self, board):
        self.pos = board
        self.piece_move_handler = {
            OFF_BOARD: self.empty_handler,
            EMPTY: self.empty_handler,
            WHITE_PAWN: self.generate_pawn_moves,
            WHITE_KNIGHT: self.generate_non_sliding_moves,
            WHITE_BISHOP: self.generate_sliding_moves,
            WHITE_ROOK: self.generate_sliding_moves,
            WHITE_QUEEN: self.generate_sliding_moves,
            WHITE_KING: self.generate_non_sliding_moves,
            BLACK_PAWN: self.generate_pawn_moves,
            BLACK_KNIGHT: self.generate_non_sliding_moves,
            BLACK_BISHOP: self.generate_sliding_moves,
            BLACK_ROOK: self.generate_sliding_moves,
            BLACK_QUEEN: self.generate_sliding_moves,
            BLACK_KING: self.generate_non_sliding_moves,
        }

    def print_move(self, move: int) -> str:
        file_from = self.pos.conversion.FilesBoard[get_from_square(move)]
        rank_from = self.pos.conversion.RanksBoard[get_from_square(move)]
        file_to = self.pos.conversion.FilesBoard[get_to_square(move)]
        rank_to = self.pos.conversion.RanksBoard[get_to_square(move)]

        promoted = get_promoted_bits(move)

        move_str = (chr(ord("a") + file_from) + chr(ord("1") + rank_from) +
                    chr(ord("a") + file_to) + chr(ord("1") + rank_to))

        # if this move is a promotion, add char of the piece we promote to at the end of the move string
        # i.e. if a7a8q -> we promote to Queen
        if promoted != 0:
            piece_char = "q"
            if IS_PIECE_KNIGHT[promoted]:
                piece_char = "n"
            elif IS_PIECE_ROOK_QUEEN[promoted] and not IS_PIECE_BISHOP_QUEEN[promoted]:
                piece_char = "r"
            elif not IS_PIECE_ROOK_QUEEN[promoted] and IS_PIECE_BISHOP_QUEEN[promoted]:
                piece_char = "b"

            move_str += piece_char

        return move_str

    def add_white_pawn_capture_move(self, from_: int, to: int, cap: int, move_list: List) -> List:
        assert self.pos.is_piece_valid_or_empty(cap)
        assert self.pos.is_square_on_board(from_)
        assert self.pos.is_square_on_board(to)

        if self.pos.conversion.RanksBoard[from_] == RANK_7:
            # add all promotion with capture related moves
            move_list.append(get_move_int(from_, to, cap, WHITE_QUEEN, 0))
            move_list.append(get_move_int(from_, to, cap, WHITE_ROOK, 0))
            move_list.append(get_move_int(from_, to, cap, WHITE_BISHOP, 0))
            move_list.append(get_move_int(from_, to, cap, WHITE_KNIGHT, 0))
        else:
            # add normal capture moves without promotion
            move_list.append(get_move_int(from_, to, cap, EMPTY, 0))

        return move_list

    def add_white_pawn_move(self, from_: int, to: int, move_list: List) -> List:
        assert self.pos.is_square_on_board(from_)
        assert self.pos.is_square_on_board(to)

        if self.pos.conversion.RanksBoard[from_] == RANK_7:
            # add normal promotion without capture
            move_list.append(get_move_int(from_, to, EMPTY, WHITE_QUEEN, 0))
            move_list.append(get_move_int(from_, to, EMPTY, WHITE_ROOK, 0))
            move_list.append(get_move_int(from_, to, EMPTY, WHITE_BISHOP, 0))
            move_list.append(get_move_int(from_, to, EMPTY, WHITE_KNIGHT, 0))
        else:
            move_list.append(get_move_int(from_, to, EMPTY, EMPTY, 0))

        return move_list

    def add_black_pawn_capture_move(self, from_: int, to: int, cap: int, move_list: List) -> List:
        assert self.pos.is_piece_valid_or_empty(cap)
        assert self.pos.is_square_on_board(from_)
        assert self.pos.is_square_on_board(to)

        if self.pos.conversion.RanksBoard[from_] == RANK_2:
            # add all promotion with capture related moves
            move_list.append(get_move_int(from_, to, cap, BLACK_QUEEN, 0))
            move_list.append(get_move_int(from_, to, cap, BLACK_ROOK, 0))
            move_list.append(get_move_int(from_, to, cap, BLACK_BISHOP, 0))
            move_list.append(get_move_int(from_, to, cap, BLACK_KNIGHT, 0))
        else:
            # add normal capture moves without promotion
            move_list.append(get_move_int(from_, to, cap, EMPTY, 0))

        return move_list

    def add_black_pawn_move(self, from_: int, to: int, move_list: List) -> List:
        assert self.pos.is_square_on_board(from_)
        assert self.pos.is_square_on_board(to)

        if self.pos.conversion.RanksBoard[from_] == RANK_2:
            # add normal promotion without capture
            move_list.append(get_move_int(from_, to, EMPTY, BLACK_QUEEN, 0))
            move_list.append(get_move_int(from_, to, EMPTY, BLACK_ROOK, 0))
            move_list.append(get_move_int(from_, to, EMPTY, BLACK_BISHOP, 0))
            move_list.append(get_move_int(from_, to, EMPTY, BLACK_KNIGHT, 0))
        else:
            move_list.append(get_move_int(from_, to, EMPTY, EMPTY, 0))

        return move_list

    # noinspection PyMethodMayBeStatic
    def empty_handler(self, *_):
        return []

    def generate_pawn_moves(self, sq, _) -> List:
        move_list = []

        enemy = BLACK
        pawn_rank = RANK_2
        forward_one_sq, forward_two_sq, capture_left_sq, capture_right_sq = 10, 20, 9, 11
        pawn_move_handler, pawn_capture_move_handler = self.add_white_pawn_move, self.add_white_pawn_capture_move

        if self.pos.side == BLACK:
            enemy = WHITE
            pawn_rank = RANK_7
            forward_one_sq, forward_two_sq, capture_left_sq, capture_right_sq = -10, -20, -9, -11
            pawn_move_handler, pawn_capture_move_handler = self.add_black_pawn_move, self.add_black_pawn_capture_move

        # add simple pawn move forward if next sq is empty
        if self.pos.pieces[sq + forward_one_sq] == EMPTY:
            move_list = pawn_move_handler(sq, sq + forward_one_sq, move_list)
            # if we are on the second rank, generate a double pawn move if 4th rank sq is empty
            if self.pos.conversion.RanksBoard[sq] == pawn_rank and self.pos.pieces[sq + forward_two_sq] == EMPTY:
                # don't forget to set the flag for PAWN START
                move_list.append(get_move_int(sq, (sq + forward_two_sq), EMPTY, EMPTY, MOVE_FLAG_PAWN_START))

        # Capture to the left and right
        # check if the square that we are capturing on is on the lib and that it has a black piece on it
        if self.pos.is_square_on_board(sq + capture_left_sq) and (
                PIECE_COLOR_MAP[self.pos.pieces[sq + capture_left_sq]] == enemy):
            move_list = pawn_capture_move_handler(sq, sq + capture_left_sq,
                                                  self.pos.pieces[sq + capture_left_sq], move_list)

        # check if the square that we are capturing on is on the lib and that it has a black piece on it
        if self.pos.is_square_on_board(sq + capture_right_sq) and (
                PIECE_COLOR_MAP[self.pos.pieces[sq + capture_right_sq]] == enemy):
            move_list = pawn_capture_move_handler(sq, sq + capture_right_sq,
                                                  self.pos.pieces[sq + capture_right_sq], move_list)

        if self.pos.enPassantSquare != NO_SQUARE:
            # check if the sq+9 square is equal to the enpassant square that we have stored in our pos
            if sq + capture_left_sq == self.pos.enPassantSquare:
                move_list.append(get_move_int(sq, sq + capture_left_sq, EMPTY, EMPTY, MOVE_FLAG_ENPASS))

            if sq + capture_right_sq == self.pos.enPassantSquare:
                move_list.append(get_move_int(sq, sq + capture_right_sq, EMPTY, EMPTY, MOVE_FLAG_ENPASS))

        return move_list

    def generate_sliding_moves(self, sq, piece) -> List:
        move_list = []

        for index in range(DIRECTIONS_OF_MOVEMENT[piece]):
            dir_ = PIECE_MOVEMENT_INCREMENT[piece][index]
            target_sq = sq + dir_

            # while we are still on the lib, take a sliding piece and add a possible move
            # until we see another piece or we hit the edge of the lib
            while self.pos.is_square_on_board(target_sq):
                # BLACK ^ 1 == WHITE       WHITE ^ 1 == BLACK
                if self.pos.pieces[target_sq] != EMPTY:
                    if PIECE_COLOR_MAP[self.pos.pieces[target_sq]] == self.pos.side ^ 1:
                        move_list.append(get_move_int(sq, target_sq, self.pos.pieces[target_sq], EMPTY, 0))

                    break  # if we hit a non-empty square, we break from this direction

                move_list.append(get_move_int(sq, target_sq, EMPTY, EMPTY, 0))
                target_sq += dir_

        return move_list

    def generate_non_sliding_moves(self, sq, piece) -> List:
        move_list = []

        for index in range(DIRECTIONS_OF_MOVEMENT[piece]):
            dir_ = PIECE_MOVEMENT_INCREMENT[piece][index]
            target_sq = sq + dir_

            if not self.pos.is_square_on_board(target_sq):
                continue

            # BLACK ^ 1 == WHITE       WHITE ^ 1 == BLACK
            if self.pos.pieces[target_sq] != EMPTY:
                if PIECE_COLOR_MAP[self.pos.pieces[target_sq]] == self.pos.side ^ 1:
                    move_list.append(get_move_int(sq, target_sq, self.pos.pieces[target_sq], EMPTY, 0))
                continue

            move_list.append(get_move_int(sq, target_sq, EMPTY, EMPTY, 0))

        return move_list

    def generate_castling_moves(self) -> List:
        move_list = []

        if self.pos.side == WHITE:
            # if the position allows white king castling
            # here we do not check if square G1 (final square after castling) is attacked
            # this will be handled at the end of the deftion where we will verify that all generated
            # moves are legal
            if (self.pos.castlePermissions & WHITE_KING_CASTLING) != 0:
                if self.pos.pieces[F1] == EMPTY and self.pos.pieces[G1] == EMPTY:
                    if not self.pos.is_square_attacked(E1, BLACK) and not self.pos.is_square_attacked(F1, BLACK):
                        move_list.append(get_move_int(E1, G1, EMPTY, EMPTY, MOVE_FLAG_CASTLE))

            if (self.pos.castlePermissions & WHITE_QUEEN_CASTLING) != 0:
                if self.pos.pieces[D1] == EMPTY and self.pos.pieces[C1] == EMPTY and self.pos.pieces[B1] == EMPTY:
                    if not self.pos.is_square_attacked(E1, BLACK) and not self.pos.is_square_attacked(D1, BLACK):
                        move_list.append(get_move_int(E1, C1, EMPTY, EMPTY, MOVE_FLAG_CASTLE))

        else:
            # castling
            if (self.pos.castlePermissions & BLACK_KING_CASTLING) != 0:
                if self.pos.pieces[F8] == EMPTY and self.pos.pieces[G8] == EMPTY:
                    if not self.pos.is_square_attacked(E8, WHITE) and not self.pos.is_square_attacked(F8, WHITE):
                        move_list.append(get_move_int(E8, G8, EMPTY, EMPTY, MOVE_FLAG_CASTLE))

            if (self.pos.castlePermissions & BLACK_QUEEN_CASTLING) != 0:
                if self.pos.pieces[D8] == EMPTY and self.pos.pieces[C8] == EMPTY and self.pos.pieces[B8] == EMPTY:
                    if not self.pos.is_square_attacked(E8, WHITE) and not self.pos.is_square_attacked(D8, WHITE):
                        move_list.append(get_move_int(E8, C8, EMPTY, EMPTY, MOVE_FLAG_CASTLE))

        return move_list

    def generate_all_moves(self) -> List:
        move_list = []

        move_list.extend(self.generate_castling_moves())

        for sq in range(BOARD_SQUARE_NUMBER):
            piece = self.pos.pieces[sq]

            if piece == OFF_BOARD or PIECE_COLOR_MAP[piece] != self.pos.side:
                continue

            handler = self.piece_move_handler[piece]
            moves = handler(sq, piece)
            move_list.extend(moves)

        return move_list
