import math
import os


class Piece:
    def __init__(self, name: str, colour: str, value: int, texture=None, texture_rect=None):
        self.name = name
        self.colour = colour
        value_sign = 1 if colour == 'white' else -1
        self.value = value_sign * value
        self.texture = texture
        self.set_texture()
        self.texture_rect = texture_rect
        self.moves = []
        self.moved = False

    def set_texture(self, size=80):
        self.texture = os.path.join(
            f'assets/images/{size}px/{self.colour[0].upper()}{self.name.upper()}.png'
        )

    def add_moves(self, move):
        self.moves.append(move)


class Pawn(Piece):
    def __init__(self, colour: str):
        super().__init__('pawn', colour, 1.0)
        self.dir = -1 if colour == 'white' else 1


class Knight(Piece):
    def __init__(self, colour: str):
        super().__init__('knight', colour, 3.0)


class Bishop(Piece):
    def __init__(self, colour: str):
        super().__init__('bishop', colour, 3.001)


class Rook(Piece):
    def __init__(self, colour: str):
        super().__init__('rook', colour, 5)


class Queen(Piece):
    def __init__(self, colour: str):
        super().__init__('queen', colour, 9)


class King(Piece):
    def __init__(self, colour: str):
        super().__init__('king', colour, value=math.inf)
