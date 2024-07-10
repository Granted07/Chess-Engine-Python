from const import *
from piece import King


class Ai:
    def __init__(self, board, player):
        self.evaluation = 0
        self.board = board
        self.depth = 2
        self.player = player

    def static_eval(self):
        self.evaluation = 0
        for row in range(ROWS):
            for col in range(COLS):
                if self.board.squares[row][col].has_piece():
                    piece = self.board.squares[row][col].piece
                    if not isinstance(piece, King):
                        self.evaluation += piece.value
        print(self.evaluation)

    def game_over(self):
        for row in range(ROWS):
            for col in range(COLS):
                if self.board.squares[row][col].has_enemy_piece(self.player):
                    piece = self.board.squares[row][col].piece
                    piece.clear_moves()
                    self.board.calc_moves(piece, row, col)
                    move_list = [str(m) for m in piece.moves]
                    if len(move_list) != 0:
                        return False
        return True

    def minimax(self):
        if self.depth == 0 or self.game_over():
            pass

