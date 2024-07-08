from const import *
from move import Move
from square import Square
from piece import *


class Board:
    def __init__(self):
        self.squares = [[0 for row in range(ROWS)] for col in range(COLS)]
        self._create()
        self._add_piece('white')
        self._add_piece('black')

    def calc_moves(self, piece, row: int, col: int):

        """
        Calculates all possible moves for a piece
        :param piece:
        :param row:
        :param col:
        :return:
        """

        def knight_moves():
            # 8 possible moves, all variations of 2,1
            possible_moves = [
                (row - 2, col + 1),
                (row - 2, col - 1),
                (row + 2, col + 1),
                (row + 2, col - 1),
                (row + 1, col - 2),
                (row - 1, col - 2),
                (row + 1, col + 2),
                (row - 1, col + 2),
            ]
            for possible_move in possible_moves:
                possible_move_row, possible_move_col = possible_move
                if Square.in_range(possible_move_row, possible_move_col):
                    if self.squares[possible_move_row][possible_move_col].isempty_or_enemy(piece.colour):
                        initial = Square(row, col)
                        final = Square(possible_move_row, possible_move_col)  # piece = piece
                        move = Move(initial, final)
                        piece.add_move(move)

        def pawn_moves():
            # steps
            steps = 1 if piece.moved else 2
            # vertical
            start = row + piece.dir
            end = row + (piece.dir*(1+steps))
            for possible_move_row in range(start, end, piece.dir):
                if Square.in_range(possible_move_row):
                    if self.squares[possible_move_row][col].isempty():
                        initial = Square(possible_move_row, col)
                        final = Square(possible_move_row, col)
                        move = Move(initial, final)
                        piece.add_move(move)
                    else:
                        break
                        # therefore blocked
                else:
                    break
                    # not in range
            # diagonal/taking
            possible_move_row = row + piece.dir
            possible_move_cols = [col-1, col+1]
            for possible_move_col in possible_move_cols:
                if Square.in_range(possible_move_row, possible_move_col):
                    if self.squares[possible_move_row][possible_move_col].has_enemy_piece(piece.colour):
                        initial = Square(possible_move_row, possible_move_col)
                        final = Square(possible_move_row, possible_move_col)
                        move = Move(initial, final)
                        piece.add_move(move)

        def bishop_moves():
            pass

        if isinstance(piece, Pawn):
            pawn_moves()

        elif isinstance(piece, Knight):
            knight_moves()

        elif isinstance(piece, Bishop):
            bishop_moves()

        elif isinstance(piece, Rook):
            pass

        elif isinstance(piece, Queen):
            pass

        elif isinstance(piece, King):
            pass

    def _create(self):
        for row in range(ROWS):
            for col in range(COLS):
                self.squares[row][col] = Square(row, col)

    def _add_piece(self, colour):
        row_pawn, row_pieces = (6, 7) if colour == 'white' else (1, 0)
        # pawns
        for col in range(COLS):
            self.squares[row_pawn][col] = Square(row_pawn, col, Pawn(colour))

        # knights
        self.squares[row_pieces][1] = Square(row_pieces, 1, Knight(colour))
        self.squares[row_pieces][6] = Square(row_pieces, 6, Knight(colour))

        # bishops
        self.squares[row_pieces][2] = Square(row_pieces, 2, Bishop(colour))
        self.squares[row_pieces][5] = Square(row_pieces, 5, Bishop(colour))

        # rooks
        self.squares[row_pieces][0] = Square(row_pieces, 0, Rook(colour))
        self.squares[row_pieces][7] = Square(row_pieces, 7, Rook(colour))

        # queen
        self.squares[row_pieces][3] = Square(row_pieces, 3, Queen(colour))

        # king
        self.squares[row_pieces][4] = Square(row_pieces, 4, King(colour))
