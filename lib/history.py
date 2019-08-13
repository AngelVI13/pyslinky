from ctypes import c_uint64


class Undo:
    """Structure to hold history related information allowing for a move to be undone (taken back).
    This is used to easily traverse the game tree.
    """
    __slots__ = ['move', 'castlePermissions', 'enPassantSquare', 'fiftyMove', 'posKey']

    def __init__(self):
        self.move: int = 0
        self.castlePermissions: int = 0
        self.enPassantSquare: int = 0
        self.fiftyMove: int = 0
        self.posKey: c_uint64 = 0
