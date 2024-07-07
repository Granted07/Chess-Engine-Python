class Square:
    def __init__(self, row: int, col: int, piece=None):
        self.row = row
        self.col = col
        self.piece = piece

    def has_piece(self):
        return self.piece is not None
