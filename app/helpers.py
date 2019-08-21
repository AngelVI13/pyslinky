import pygame

from app.defines import *


class Helpers:
    from_square = slice(0, 2)
    to_square = slice(2, 4)

    @classmethod
    def get_move_str(cls, from_sq, to_sq):
        return f'{cls.get_sq_str(from_sq)}{cls.get_sq_str(to_sq)}'

    @staticmethod
    def get_sq_str(sq):
        row, col = divmod(sq, ROWS)
        return f'{FILE_CHAR[col]}{ROWS - row}'  # subtraction is needed since index 0 is a8 and not a1

    @staticmethod
    def get_sq_from_str(sq_str):
        file, rank = sq_str
        file, rank = FILE_INT[file], int(rank)
        sq = (ROWS - rank) * ROWS + file
        return sq

    @staticmethod
    def compute_square_locations(reversed_=False):
        square_loc = {}
        for i in range(BOARD_SIZE):
            row, col = divmod(i, ROWS)

            if reversed_:
                square_loc[BOARD_SIZE - i - 1] = (col * SQUARE_SIZE, row * SQUARE_SIZE)
            else:
                square_loc[i] = (col * SQUARE_SIZE, row * SQUARE_SIZE)
        return square_loc

    @staticmethod
    def display_text(text, font_type, font_size, canvas, location, bold=False, italic=False, color='white'):
        # SysFont(name, size, bold=False, italic=False) -> Font
        font = pygame.font.SysFont(font_type, font_size, bold, italic)

        # render(text, antialias, color, background=None) -> Surface
        text_surface = font.render(text, True, pygame.Color(color))

        canvas.blit(text_surface, location)

    @staticmethod
    def get_square_under_mouse(coords, reversed_):
        width, height = coords
        width_idx = width // SQUARE_SIZE  # todo might need to add offset or sth here later
        height_idx = height // SQUARE_SIZE
        square_idx = height_idx * ROWS + width_idx
        return square_idx if not reversed_ else BOARD_SIZE - square_idx - 1

    @staticmethod
    def blit_alpha(canvas, source, location, opacity):
        x, y = location
        temp = pygame.Surface((source.get_width(), source.get_height())).convert()
        temp.blit(canvas, (-x, -y))
        temp.blit(source, (0, 0))
        temp.set_alpha(opacity)
        canvas.blit(temp, location)

    @staticmethod
    def load_assets():
        # load all images
        d = {k: pygame.image.load(v) for k, v in IMAGE_PATHS.items()}
        # scale them
        return {k: pygame.transform.scale(v, IMAGE_SIZES[k]) for k, v in d.items()}
