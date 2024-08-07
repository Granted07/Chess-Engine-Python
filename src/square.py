class Square:
    def __init__(self, row: int, col: int, piece=None):
        self.row = row
        self.col = col
        self.piece = piece

    def __eq__(self, other):
        return self.row == other.row and self.col == other.col

    def has_piece(self):
        return self.piece is not None

    def isempty(self):
        return not self.has_piece()

    def has_team_piece(self, colour):
        return self.has_piece() and self.piece.colour == colour

    def has_enemy_piece(self, colour):
        return self.has_piece() and self.piece.colour != colour

    def isempty_or_enemy(self, colour):
        return self.isempty() or self.has_enemy_piece(colour)


    @staticmethod
    def in_range(*args):
        for arg in args:
            if arg < 0 or arg > 7:
                return False
        return True

# print(Square.in_range(8,2,5,3))
