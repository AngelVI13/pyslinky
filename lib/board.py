from copy import deepcopy

from lib.constants import *
from lib.conversion import Conversion, convert_file_rank_to_square
from lib.movegenerator import MoveGenerator
from lib.history import Undo


class Board:
    def __init__(self):
        self.pieces: List[int] = [0] * BOARD_SQUARE_NUMBER
        self.side: int = 0
        self.playerJustMoved: int = BLACK  # At the root pretend the player just moved is p2 - p1 has the first move
        self.castlePermissions: int = 0  # castle permissions
        # position key is a unique key stored for each position (used to keep track of 3fold repetition)
        self.posKey: c_uint64 = c_uint64(0)
        self.kingSquare: List[int] = [0] * 2  # White's & black's king position
        self.enPassantSquare: int = 0  # square in which en passant capture is possible
        self.fiftyMove: int = 0  # how many moves from the fifty move rule have been made
        self.histPly: int = 0  # how many half moves have been made
        # Create fixed size list that stores current position and variables before a move is made
        self.history: List[Undo] = [Undo() for _ in range(MAX_GAME_MOVES)]

        # The piece list below make it easier to determine drawn positions or insufficient material
        self.pieceNumber: List[int] = [0] * 13  # how many pieces of each type are there currently on the lib

        # Create related objects
        self.hashData = HashData()
        self.moveGenerator = MoveGenerator(self)
        self.conversion = Conversion()

    def __str__(self):
        board_rep = ["\nGame Board:\n\n"]

        for rank in reversed(range(RANK_8 + 1)):
            rank_line = ["{}  ".format(rank + 1)]
            for file in range(FILE_H + 1):
                sq = convert_file_rank_to_square(file, rank)
                piece = self.pieces[sq]
                rank_line.append(" {} ".format(PIECE_CHARACTER_STRING[piece]))

            rank_line.append('\n')
            board_rep.append(''.join(rank_line))

        board_rep.append("\n   ")

        bottom_line = []
        for file in range(FILE_H + 1):
            bottom_line.append(" {} ".format(chr(ord('a') + file)).upper())

        board_rep.append(''.join(bottom_line))

        board_rep.append("\n\n")
        board_rep.append("side: {}\n".format(SIDE_CHAR[self.side]))
        board_rep.append("enPas: {}\n".format(self.enPassantSquare))

        # Compute castling permissions. w_kca - white kingside castling, b_qca - black queenside castling etc
        w_kca = "-"
        if self.castlePermissions & WHITE_KING_CASTLING != 0:
            w_kca = "K"

        w_qca = "-"
        if self.castlePermissions & WHITE_QUEEN_CASTLING != 0:
            w_qca = "Q"

        b_kca = "-"
        if self.castlePermissions & BLACK_KING_CASTLING != 0:
            b_kca = "k"

        b_qca = "-"
        if self.castlePermissions & BLACK_QUEEN_CASTLING != 0:
            b_qca = "q"

        board_rep.append("castle: {}{}{}{}\n".format(w_kca, w_qca, b_kca, b_qca))
        board_rep.append("PosKey: {}\n".format(self.posKey))

        return ''.join(board_rep)

    def __eq__(self, other):
        if not len(self.pieces) == sum([1 for i, j in zip(self.pieces, other.pieces) if i == j]):
            return False

        if self.side != other.side:
            return False

        if self.playerJustMoved != other.playerJustMoved:
            return False

        if self.castlePermissions != other.castlePermissions:
            return False

        if self.posKey.value != other.posKey.value:
            return False

        if not len(self.kingSquare) == sum([1 for i, j in zip(self.kingSquare, other.kingSquare) if i == j]):
            return False

        if self.enPassantSquare != other.enPassantSquare:
            return False

        if self.fiftyMove != other.fiftyMove:
            return False

        if self.histPly != other.histPly:
            return False

        if not len(self.pieceNumber) == sum([1 for i, j in zip(self.pieceNumber, other.pieceNumber) if i == j]):
            return False

        return True

    def __hash__(self):
        """Generate a unique hashkey for a given position"""
        final_key: c_uint64 = 0

        for sq in range(BOARD_SQUARE_NUMBER):
            piece = self.pieces[sq]
            # Do not calculate hashkey for squares that are not on the actual lib, i.e. have value of NO_SQUARE
            # Also do not calculate hashkey for an empty square
            if piece != NO_SQUARE and piece != EMPTY and piece != OFF_BOARD:
                # Check if we have a valid piece
                assert WHITE_PAWN <= piece <= BLACK_KING
                # Add/remove (xor) the hash value for a given piece and for a given position from the final hash value
                final_key ^= self.hashData.pieceKeys[piece][sq]

        if self.side == WHITE:
            final_key ^= self.hashData.sideKey

        if self.enPassantSquare != NO_SQUARE:
            assert 0 <= self.enPassantSquare < BOARD_SQUARE_NUMBER
            # We have already generated hash keys for all pieces + EMPTY
            # => the hashkeys for value empty are used for en passant hash calculations
            final_key ^= self.hashData.pieceKeys[EMPTY][self.enPassantSquare]

        assert 0 <= self.castlePermissions <= 15

        final_key ^= self.hashData.castleKeys[self.castlePermissions]

        return c_uint64(final_key)

    def __copy__(self):
        return deepcopy(self)

    def reset(self):
        # Set all lib positions to OFF_BOARD
        for i in range(BOARD_SQUARE_NUMBER):
            self.pieces[i] = OFF_BOARD

        # Set all real lib positions to EMPTY
        for i in range(64):
            self.pieces[self.conversion.Sq64ToSq120[i]] = EMPTY

        # Reset piece number
        for i in range(13):  # todo replace magical number
            self.pieceNumber[i] = 0

        self.kingSquare[WHITE] = NO_SQUARE
        self.kingSquare[BLACK] = NO_SQUARE

        self.side = BOTH
        self.enPassantSquare = NO_SQUARE
        self.fiftyMove = 0
        self.histPly = 0
        self.castlePermissions = 0
        self.posKey = 0

    def _parse_fen_pieces(self, fen) -> int:
        """Parses fen piece & square information and return char index of fen string at end of parsing"""

        rank = RANK_8  # we start from rank 8 since the notation starts from rank 8
        file = FILE_A
        char_idx = 0

        while (rank >= RANK_1) and char_idx < len(fen):
            count = 1
            char = fen[char_idx]

            if char in PIECE_NOTATION_MAP:
                # If we have a piece related char -> set the piece to corresponding value, i.e p -> BLACK_PAWN
                piece = PIECE_NOTATION_MAP[char]
            elif char in ("1", "2", "3", "4", "5", "6", "7", "8"):
                # otherwise it must be a count of a number of empty squares
                piece = EMPTY
                count = int(char)  # get number of empty squares and store in count
            elif char in ("/", " "):
                # if we have / or space then we are either at the end of the rank or at the end of the piece list
                # -> reset variables and continue the while loop
                rank -= 1
                file = FILE_A
                char_idx += 1
                continue
            else:
                raise ValueError("------------!!! --- FEN error --- !!!------------------")

            # This loop, skips over all empty positions in a rank
            # When it comes to a piece that is different that "1"-"8" it places it on the corresponding square
            for i in range(count):
                sq64 = rank * 8 + file
                sq120 = self.conversion.Sq64ToSq120[sq64]
                if piece != EMPTY:
                    self.pieces[sq120] = piece

                file += 1

            char_idx += 1

        return char_idx

    def _parse_fen_options(self, fen, char_idx):
        """Parses position information i.e. en passant square, castling permission etc. from fen str and starting
        char index (index points to part of fen that starts listing position options)
        """
        # char should be set to the side to move part of the FEN string here
        char = fen[char_idx]
        assert (char == "w" or char == "b")

        self.side = WHITE if char == "w" else BLACK
        self.playerJustMoved = BLACK if self.side == WHITE else WHITE

        # move character pointer 2 characters further and it should now point to
        # the start of the castling permissions part of FEN
        char_idx += 2

        # Iterate over the next 4 chars-they show if white is allowed to castle king or queenside and the same for black
        for i in range(4):
            char = fen[char_idx]
            if char == " ":
                # when we hit a space, it means there are no more castling permissions => break
                break

            # Depending on the char, enable the corresponding castling permission related bit
            if char is "K":
                self.castlePermissions |= WHITE_KING_CASTLING
            elif char is "Q":
                self.castlePermissions |= WHITE_QUEEN_CASTLING
            elif char is "k":
                self.castlePermissions |= BLACK_KING_CASTLING
            elif char is "q":
                self.castlePermissions |= BLACK_QUEEN_CASTLING
            else:
                break

            char_idx += 1

        assert 0 <= self.castlePermissions <= 15
        # move to the en passant square related part of FEN
        char_idx += 1
        char = fen[char_idx]

        if char != "-":
            file = FILE_NOTATION_MAP[char]
            char_idx += 1
            rank = int(fen[char_idx])  # get rank number
            rank -= 1  # decrement rank to match our indexes, i.e. Rank1 == 0

            assert FILE_A <= file <= FILE_H
            assert RANK_1 <= rank <= RANK_8

            self.enPassantSquare = convert_file_rank_to_square(file, rank)

    def parse_fen(self, fen: str):
        """parse fen position string and setup a position accordingly"""

        assert (fen != "")

        self.reset()  # resets lib

        char_idx = self._parse_fen_pieces(fen)
        self._parse_fen_options(fen, char_idx)

        self.posKey = self.__hash__()  # generate pos key for new position
        self.update_material_lists()

    def update_material_lists(self):  # todo why not do this while parsing fen pieces
        """updates all material related piece lists"""
        for index in range(BOARD_SQUARE_NUMBER):
            piece = self.pieces[index]
            if piece != OFF_BOARD and piece != EMPTY:
                colour = PIECE_COLOR_MAP[piece]

                self.pieceNumber[piece] += 1  # increment piece number

                if piece == WHITE_KING or piece == BLACK_KING:
                    self.kingSquare[colour] = index

    def parse_move(self, move_str: str) -> int:
        """Parses user move and returns the MOVE int value from the GeneratedMoves for the
        position, that matches the moveStr input. For example if moveStr = 'a2a3'
        loops over all possible moves for the position, finds that move int i.e. 1451231 and returns it
        """
        # check if files for 'from' and 'to' squares are valid i.e. between 1-8
        # todo fix this to use the same method in the gui
        if move_str[1] > "8" or move_str[1] < "1":
            return NO_MOVE

        if move_str[3] > "8" or move_str[3] < "1":
            return NO_MOVE

        # check if ranks for 'from' and 'to' squares are valid i.e. between a-h
        if move_str[0] > "h" or move_str[0] < "a":
            return NO_MOVE

        if move_str[2] > "h" or move_str[2] < "a":
            return NO_MOVE

        from_ = convert_file_rank_to_square((ord(move_str[0]) - ord("a")), (ord(move_str[1]) - ord("1")))
        to = convert_file_rank_to_square((ord(move_str[2]) - ord("a")), (ord(move_str[3]) - ord("1")))

        # print("Move string: {}, from: {} to: {}".format(move_str, from_, to))

        assert self.is_square_on_board(from_) and self.is_square_on_board(to)

        move_list = self.generate_moves()

        for move_ in move_list:
            # print('From: {}, to: {}'.format(FromSq(move), ToSq(move)))
            if get_from_square(move_) == from_ and get_to_square(move_) == to:
                prom_piece = get_promoted_bits(move_)
                if prom_piece != EMPTY:
                    if IS_PIECE_ROOK_QUEEN[prom_piece] and not IS_PIECE_BISHOP_QUEEN[prom_piece] and move_str[4] == "r":
                        return move_
                    elif not IS_PIECE_ROOK_QUEEN[prom_piece] and IS_PIECE_BISHOP_QUEEN[prom_piece] and (
                            move_str[4] == "b"):
                        return move_
                    elif IS_PIECE_ROOK_QUEEN[prom_piece] and IS_PIECE_BISHOP_QUEEN[prom_piece] and move_str[4] == "q":
                        return move_
                    elif IS_PIECE_KNIGHT[prom_piece] and move_str[4] == "n":
                        return move_

                    continue

                # must not be a promotion -> return move
                return move_

        return NO_MOVE

    def is_square_on_board(self, square) -> bool:
        return self.conversion.FilesBoard[square] != OFF_BOARD

    @staticmethod
    def is_side_valid(side) -> bool:
        return side == WHITE or side == BLACK

    @staticmethod
    def is_piece_valid(piece) -> bool:
        return WHITE_PAWN <= piece <= BLACK_KING

    @staticmethod
    def is_piece_valid_or_empty(piece) -> bool:
        return EMPTY <= piece <= BLACK_KING

    def is_square_attacked(self, sq: int, side: int) -> bool:  # todo move this to movegen ?
        """Determines if a given square is attacked from the opponent.
        NOTE: side here is the attacking side
        """
        assert self.is_square_on_board(sq)
        assert self.is_side_valid(side)

        # pawns
        # if attacking side is white and there are pawns infornt to the left and right of us, then we are attacked
        if side == WHITE:
            if self.pieces[sq - 11] == WHITE_PAWN or self.pieces[sq - 9] == WHITE_PAWN:
                return True

        else:
            if self.pieces[sq + 11] == BLACK_PAWN or self.pieces[sq + 9] == BLACK_PAWN:
                return True

        # knights
        # Loop through 8 directions
        for index in range(8):
            # find what piece is in that direction
            pce = self.pieces[sq + KNIGHT_MOVE_INCREMENT[index]]
            # if there is a knight of the opposite side at that piece -> return True
            if pce != OFF_BOARD and IS_PIECE_KNIGHT[pce] and PIECE_COLOR_MAP[pce] == side:
                return True

        # rooks, queens
        for index in range(4):
            dir_ = ROOK_MOVE_INCREMENT[index]  # get current direction
            to_sq = sq + dir_  # take the first square
            pce = self.pieces[to_sq]  # see what piece is there
            while pce != OFF_BOARD:  # while the piece is not OFF_BOARD
                if pce != EMPTY:  # if we hit a piece
                    # if that piece is a rook or queen from the opposite side
                    if IS_PIECE_ROOK_QUEEN[pce] and PIECE_COLOR_MAP[pce] == side:
                        return True  # our square is under attack -> return True

                    break  # otherwise we hit a piece that is not an attacker -> try another direction

                to_sq += dir_  # increment new piece square and perform check again
                pce = self.pieces[to_sq]  # get new piece

        # bishops, queens
        for index in range(4):  # todo could be rewriten as for _, dir = range bishopDir !!!!!!
            dir_ = BISHOP_MOVE_INCREMENT[index]
            to_sq = sq + dir_
            pce = self.pieces[to_sq]
            while pce != OFF_BOARD:
                if pce != EMPTY:
                    if IS_PIECE_BISHOP_QUEEN[pce] and PIECE_COLOR_MAP[pce] == side:
                        return True

                    break

                to_sq += dir_
                pce = self.pieces[to_sq]

        # kings
        for index in range(8):
            pce = self.pieces[sq + KING_MOVE_INCREMENT[index]]
            if pce != OFF_BOARD and IS_PIECE_KING[pce] and PIECE_COLOR_MAP[pce] == side:
                return True

        return False

    def generate_moves(self):
        return filter(lambda move: self.is_move_legal(move), self.moveGenerator.generate_all_moves())

    def get_moves(self):  # needed for uct simulation
        return list(self.generate_moves())

    def is_move_legal(self, move_: int) -> bool:
        """Does a simplified version of make_move, however it does not update any hashtables or special squares.
        it only makes a move and checks that the side to move is still in check after the move => move is illegal.
        """
        is_legal = True

        from_ = get_from_square(move_)
        to = get_to_square(move_)

        # Make sure all input info is valid
        assert self.is_square_on_board(from_)
        assert self.is_square_on_board(to)
        assert self.is_side_valid(self.side)
        assert self.is_piece_valid(self.pieces[from_])

        # if this is an en passant move
        if move_ & MOVE_FLAG_ENPASS != 0:
            # if the side thats making the capture is white
            # then we need to remove the black pawn right behind the new position of the white piece
            # i.e. new_pos - 10 -> translated to array index
            if self.side == WHITE:
                self.clear_piece(to - 10)
            else:
                self.clear_piece(to + 10)

        elif move_ & MOVE_FLAG_CASTLE != 0:
            # if its a castling move, based on the TO square, make the appopriate move, otherwise assert False
            if to == C1:
                self.move_piece(A1, D1)
            elif to == C8:
                self.move_piece(A8, D8)
            elif to == G1:
                self.move_piece(H1, F1)
            elif to == G8:
                self.move_piece(H8, F8)
            else:
                pass

        # get what piece, if any, was captured in the move and if something was actually captured
        # i.e. captured piece is not empty remove captured piece and reset fifty move rule
        captured = get_captured_bits(move_)
        if captured != EMPTY:
            assert self.is_piece_valid(captured)
            self.clear_piece(to)

        self.move_piece(from_, to)

        # get promoted piece and if its not empty, clear old piece (pawn)
        # and add new piece (whatever was the selected promotion piece)
        promoted_piece = get_promoted_bits(move_)
        if promoted_piece != EMPTY:
            assert self.is_piece_valid(promoted_piece) and not IS_PIECE_PAWN[promoted_piece]
            self.clear_piece(to)
            self.add_piece(to, promoted_piece)

        # if we move the king -> update king square
        if IS_PIECE_KING[self.pieces[to]]:
            self.kingSquare[self.side] = to

        # need to save current side before flipping side bit in order to check if opponent is attacking
        side = self.side
        self.side ^= 1  # change side to move

        # check if after this move, our king is in check -> if yes -> illegal move
        if self.is_square_attacked(self.kingSquare[side], self.side):
            is_legal = False  # ILLEGAL MOVE

        # ---- Undo move
        self.side ^= 1

        if MOVE_FLAG_ENPASS & move_ != 0:
            if self.side == WHITE:
                self.add_piece(to - 10, BLACK_PAWN)
            else:
                self.add_piece(to + 10, WHITE_PAWN)

        elif MOVE_FLAG_CASTLE & move_ != 0:
            if to == C1:
                self.move_piece(D1, A1)
            elif to == C8:
                self.move_piece(D8, A8)
            elif to == G1:
                self.move_piece(F1, H1)
            elif to == G8:
                self.move_piece(F8, H8)
            else:
                pass
                assert False  # todo ?

        self.move_piece(to, from_)

        if IS_PIECE_KING[self.pieces[from_]]:
            self.kingSquare[self.side] = from_

        if captured != EMPTY:
            self.add_piece(to, captured)

        if promoted_piece != EMPTY:
            self.clear_piece(from_)
            if PIECE_COLOR_MAP[get_promoted_bits(move_)] == WHITE:
                self.add_piece(from_, WHITE_PAWN)
            else:
                self.add_piece(from_, BLACK_PAWN)

        return is_legal

    # MakeMove perform a move
    # return False if the side to move has left themselves in check after the move i.e. illegal move
    def make_move(self, move_: int) -> bool:
        from_ = get_from_square(move_)
        to = get_to_square(move_)

        # Make sure all input info is valid
        assert self.is_square_on_board(from_)
        assert self.is_square_on_board(to)
        assert self.is_side_valid(self.side)
        assert self.is_piece_valid(self.pieces[from_])

        # Store has value before we do any hashing in/out of pieces etc
        history_element = self.history[self.histPly]  # get pointer to history element and update its values
        history_element.posKey = self.posKey

        # if this is an en passant move
        if move_ & MOVE_FLAG_ENPASS != 0:
            # if the side thats making the capture is white
            # then we need to remove the black pawn right behind the new position of the white piece
            # i.e. new_pos - 10 -> translated to array index
            if self.side == WHITE:
                self.clear_piece(to - 10)
            else:
                self.clear_piece(to + 10)

        elif move_ & MOVE_FLAG_CASTLE != 0:
            # if its a castling move, based on the TO square, make the appopriate move, otherwise assert False
            if to == C1:
                self.move_piece(A1, D1)
            elif to == C8:
                self.move_piece(A8, D8)
            elif to == G1:
                self.move_piece(H1, F1)
            elif to == G8:
                self.move_piece(H8, F8)
            else:
                pass

        # If the current enpassant square is SET, then we hash in the poskey
        if self.enPassantSquare != NO_SQUARE:
            self.hashData.hash_enpassant(self)

        self.hashData.hash_castle_permissions(self)  # hash out the castling permissions

        # store information to the history array about this move
        history_element = self.history[self.histPly]  # get pointer to history element and update its values
        history_element.move = move_
        history_element.fiftyMove = self.fiftyMove
        history_element.enPassantSquare = self.enPassantSquare
        history_element.castlePermissions = self.castlePermissions

        # if a rook or king has moved the remove the respective castling permission from_ castlePermissions
        self.castlePermissions &= self.hashData.CASTLE_PERMISSIONS[from_]
        self.castlePermissions &= self.hashData.CASTLE_PERMISSIONS[to]
        self.enPassantSquare = NO_SQUARE  # set enpassant square to no square

        self.hashData.hash_castle_permissions(self)  # hash back in the castling perm

        self.fiftyMove += 1  # increment fifty move rule

        # get what piece, if any, was captured in the move and if something was actually captured
        # i.e. captured piece is not empty remove captured piece and reset fifty move rule
        captured = get_captured_bits(move_)
        if captured != EMPTY:
            assert self.is_piece_valid(captured)
            self.clear_piece(to)
            self.fiftyMove = 0

        # increase half-move counter and ply counter values
        self.histPly += 1

        # check if we need to set a new en passant square i.e. if this is a pawn start
        # then depending on the side find the piece just behind the new pawn destination
        # i.e. A4 -> compute A3 and set that as a possible enpassant capture square
        if IS_PIECE_PAWN[self.pieces[from_]]:
            self.fiftyMove = 0
            if move_ & MOVE_FLAG_PAWN_START != 0:
                if self.side == WHITE:
                    self.enPassantSquare = from_ + 10
                    assert self.conversion.RanksBoard[self.enPassantSquare] == RANK_3
                else:
                    self.enPassantSquare = from_ - 10
                    assert self.conversion.RanksBoard[self.enPassantSquare] == RANK_6

                self.hashData.hash_enpassant(self)  # hash in the enpass

        self.playerJustMoved ^= 1
        self.move_piece(from_, to)

        # get promoted piece and if its not empty, clear old piece (pawn)
        # and add new piece (whatever was the selected promotion piece)
        promoted_piece = get_promoted_bits(move_)
        if promoted_piece != EMPTY:
            assert self.is_piece_valid(promoted_piece) and not IS_PIECE_PAWN[promoted_piece]
            self.clear_piece(to)
            self.add_piece(to, promoted_piece)

        # if we move the king -> update king square
        if IS_PIECE_KING[self.pieces[to]]:
            self.kingSquare[self.side] = to

        # need to save current side before flipping side bit in order to check if opponent is attacking
        side = self.side
        self.side ^= 1  # change side to move
        self.hashData.hash_side(self)  # hash in the new side

        # check if after this move, our king is in check -> if yes -> illegal move
        if self.is_square_attacked(self.kingSquare[side], self.side):
            self.take_move()
            return False

        return True

    # TakeMove revert move, opposite to MakeMove()
    def take_move(self):
        self.histPly -= 1

        move_ = self.history[self.histPly].move
        from_ = get_from_square(move_)
        to = get_to_square(move_)

        assert self.is_square_on_board(from_)
        assert self.is_square_on_board(to)

        if self.enPassantSquare != NO_SQUARE:
            self.hashData.hash_enpassant(self)

        self.hashData.hash_castle_permissions(self)

        self.castlePermissions = self.history[self.histPly].castlePermissions
        self.fiftyMove = self.history[self.histPly].fiftyMove
        self.enPassantSquare = self.history[self.histPly].enPassantSquare

        if self.enPassantSquare != NO_SQUARE:
            self.hashData.hash_enpassant(self)

        self.hashData.hash_castle_permissions(self)

        self.playerJustMoved ^= 1
        self.side ^= 1
        self.hashData.hash_side(self)

        if MOVE_FLAG_ENPASS & move_ != 0:
            if self.side == WHITE:
                self.add_piece(to - 10, BLACK_PAWN)
            else:
                self.add_piece(to + 10, WHITE_PAWN)

        elif MOVE_FLAG_CASTLE & move_ != 0:
            if to == C1:
                self.move_piece(D1, A1)
            elif to == C8:
                self.move_piece(D8, A8)
            elif to == G1:
                self.move_piece(F1, H1)
            elif to == G8:
                self.move_piece(F8, H8)
            else:
                pass
                assert False  # todo ?

        self.move_piece(to, from_)

        if IS_PIECE_KING[self.pieces[from_]]:
            self.kingSquare[self.side] = from_

        captured = get_captured_bits(move_)
        if captured != EMPTY:
            assert (self.is_piece_valid(captured))
            self.add_piece(to, captured)

        promoted = get_promoted_bits(move_)
        if promoted != EMPTY:
            assert self.is_piece_valid(get_promoted_bits(move_)) and not IS_PIECE_PAWN[get_promoted_bits(move_)]
            self.clear_piece(from_)
            if PIECE_COLOR_MAP[get_promoted_bits(move_)] == WHITE:
                self.add_piece(from_, WHITE_PAWN)
            else:
                self.add_piece(from_, BLACK_PAWN)

    def clear_piece(self, sq: int):
        assert self.is_square_on_board(sq)
        piece = self.pieces[sq]
        assert self.is_piece_valid(piece)

        self.hashData.hash_piece(piece, sq, self)
        self.pieces[sq] = EMPTY
        self.pieceNumber[piece] -= 1

    def add_piece(self, sq: int, piece: int):
        assert self.is_piece_valid(piece)
        assert self.is_square_on_board(sq)

        self.hashData.hash_piece(piece, sq, self)

        self.pieces[sq] = piece
        self.pieceNumber[piece] += 1

    def move_piece(self, from_: int, to: int):
        assert self.is_square_on_board(from_)
        assert self.is_square_on_board(to)

        piece = self.pieces[from_]

        # hash the piece out of the from square and then later hash it back in to the new square
        self.hashData.hash_piece(piece, from_, self)
        self.pieces[from_] = EMPTY

        self.hashData.hash_piece(piece, to, self)
        self.pieces[to] = piece

    def get_threefold_repetition_count(self) -> int:
        """Detects how many repetitions for a given position"""
        repetition = 0

        for i in range(self.histPly):
            if self.history[i].posKey.value == self.posKey.value:
                repetition += 1

        return repetition

    def is_position_draw(self) -> bool:
        """Determine if position is a draw"""

        # if there are pawns on the lib the one of the sides can get mated
        if self.pieceNumber[WHITE_PAWN] != 0 or self.pieceNumber[BLACK_PAWN] != 0:
            return False

        # if there are major pieces on the lib the one of the sides can get mated
        if self.pieceNumber[WHITE_QUEEN] != 0 or self.pieceNumber[BLACK_QUEEN] != 0 or self.pieceNumber[
            WHITE_ROOK] != 0 or (
                self.pieceNumber[BLACK_ROOK] != 0):
            return False

        if self.pieceNumber[WHITE_BISHOP] > 1 or self.pieceNumber[BLACK_BISHOP] > 1:
            return False

        if self.pieceNumber[WHITE_KNIGHT] > 1 or self.pieceNumber[BLACK_KNIGHT] > 1:
            return False

        if self.pieceNumber[WHITE_KNIGHT] != 0 and self.pieceNumber[WHITE_BISHOP] != 0:
            return False

        if self.pieceNumber[BLACK_KNIGHT] != 0 and self.pieceNumber[BLACK_BISHOP] != 0:
            return False

        return True

    def get_result(self, player_jm):
        """is called every time a move is made this method is called to check if the game is ended"""

        if self.fiftyMove > 100:
            # print("1/2-1/2:fifty move rule (claimed by Hugo)\n")
            return DRAW

        if self.get_threefold_repetition_count() >= 2:
            # print("1/2-1/2:3-fold repetition (claimed by Hugo)\n")
            return DRAW

        if self.is_position_draw():
            # print("1/2-1/2:insufficient material (claimed by Hugo)\n")
            return DRAW

        # we have legal moves -> game is not over
        if len(list(self.generate_moves())) != 0:
            return None

        in_check = self.is_square_attacked(self.kingSquare[self.side], self.side ^ 1)

        if in_check:
            if self.side == player_jm:  # if i am the side in mate -> loss, else win
                # print("0-1:black mates (claimed by Hugo)\n")
                return LOSS

            # print("1-0:white mates (claimed by Hugo)\n")
            return WIN

        # not in check but no legal moves left -> stalemate
        # print("\n1/2-1/2:stalemate (claimed by Hugo)\n")
        return DRAW


if __name__ == '__main__':
    # todo add unittests for ParseFen, UpdateMaterial, Hashing etc !!!!!!!!!!!!!!!!!!!!!!

    b = Board()
    # move_gen_test_fen = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"
    move_gen_test_fen = "R6R/3Q4/1Q4Q1/4Q3/2Q4Q/Q4Q2/pp1Q4/kBNN1KB1 b --"
    b.parse_fen(move_gen_test_fen)
    print(b)
    moves = b.generate_moves()
    print(len(list(moves)))
