from const import *
class Board:
    def __init__(self):
        self.squares = []
    def _create(self):
        self.squares = [[0 for row in range(ROWS)] for col in range(COLS)]
        print(self.squares)

    def _add_piece(self, colour):
        pass