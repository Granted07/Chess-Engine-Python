from const import *
from move import Move
from square import Square
from piece import *


class Board:
    def __init__(self):
        self.squares = [[0 for _ in range(ROWS)] for _ in range(COLS)]
        self.last_move = None
        self._create()
        self._add_piece('white')
        self._add_piece('black')

    def move(self, piece, move):
        initial = move.initial
        final = move.final
        # board move update
        self.squares[initial.row][initial.col].piece = None
        self.squares[final.row][final.col].piece = piece
        # promotion
        if isinstance(piece, Pawn):
            self.check_promotion(piece, final)

        # castling
        if isinstance(piece, King):
            if self.castle(initial, final):
                diff = final.col - initial.col
                rook = piece.left_rook if (diff < 0) else piece.right_rook
                self.move(rook, rook.moves[-1])

        piece.moved = True
        piece.clear_moves()
        self.last_move = move

    @staticmethod
    def valid_move(piece, move):
        return move in piece.moves

    @staticmethod
    def castle(initial, final):
        return abs(initial.col - final.col) == 2

    def calc_moves(self, piece, row: int, col: int):

        """
        Calculates all possible moves for a piece
        :param piece:
        :param row:
        :param col:
        :return:
        """

        def straight_line_moves(incs):
            for inc in incs:
                row_inc, col_inc = inc
                possible_move_row = row + row_inc
                possible_move_col = col + col_inc

                while True:
                    if Square.in_range(possible_move_row, possible_move_col):
                        initial = Square(row, col)
                        final = Square(possible_move_row, possible_move_col)
                        move = Move(initial, final)
                        if self.squares[possible_move_row][possible_move_col].isempty():
                            piece.add_move(move)
                        if self.squares[possible_move_row][possible_move_col].has_enemy_piece(piece.colour):
                            piece.add_move(move)
                            break
                        if self.squares[possible_move_row][possible_move_col].has_team_piece(piece.colour):
                            break
                    else:
                        break
                    possible_move_row += row_inc
                    possible_move_col += col_inc

        def pawn_moves():
            # steps
            steps = 1 if piece.moved else 2
            # vertical
            start = row + piece.dir
            end = row + (piece.dir * (1 + steps))
            for possible_move_row in range(start, end, piece.dir):
                if Square.in_range(possible_move_row):
                    if self.squares[possible_move_row][col].isempty():
                        initial = Square(row, col)
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
            possible_move_cols = [col - 1, col + 1]
            for possible_move_col in possible_move_cols:
                if Square.in_range(possible_move_row, possible_move_col):
                    if self.squares[possible_move_row][possible_move_col].has_enemy_piece(piece.colour):
                        initial = Square(row, col)
                        final = Square(possible_move_row, possible_move_col)
                        move = Move(initial, final)
                        piece.add_move(move)

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

        def king_moves():
            possible_moves = [
                (row, col + 1),
                (row, col - 1),
                (row + 1, col),
                (row - 1, col),
                (row + 1, col - 1),
                (row - 1, col - 1),
                (row + 1, col + 1),
                (row - 1, col + 1),
            ]
            for possible_move in possible_moves:
                possible_move_row, possible_move_col = possible_move
                if Square.in_range(possible_move_row, possible_move_col):
                    if self.squares[possible_move_row][possible_move_col].isempty_or_enemy(piece.colour):
                        initial = Square(row, col)
                        final = Square(possible_move_row, possible_move_col)  # piece = piece
                        move = Move(initial, final)
                        piece.add_move(move)
            # castling
            if not piece.moved:
                left_rook, right_rook = self.squares[row][0].piece, self.squares[row][7].piece
                if isinstance(left_rook, Rook):
                    if not left_rook.moved:
                        for c in range(1, 4):
                            if self.squares[row][c].has_piece():
                                break
                            if c == 3:
                                piece.left_rook = left_rook
                                initial = Square(row, 0)
                                final = Square(row, 3)
                                move = Move(initial, final)
                                left_rook.add_move(move)
                                initial = Square(row, col)
                                final = Square(row, 2)
                                move = Move(initial, final)
                                piece.add_move(move)

                if isinstance(right_rook, Rook):
                    if not right_rook.moved:
                        for c in range(5, 7):
                            if self.squares[row][c].has_piece():
                                break
                            if c == 6:
                                piece.right_rook = right_rook
                                initial = Square(row, 7)
                                final = Square(row, 5)
                                move = Move(initial, final)
                                right_rook.add_move(move)
                                initial = Square(row, col)
                                final = Square(row, 6)
                                move = Move(initial, final)
                                piece.add_move(move)

        if isinstance(piece, Pawn):
            pawn_moves()

        elif isinstance(piece, Knight):
            knight_moves()

        elif isinstance(piece, Bishop):
            straight_line_moves([
                (1, 1), (1, -1), (-1, 1), (-1, -1)
            ])

        elif isinstance(piece, Rook):
            straight_line_moves([
                (1, 0), (-1, 0), (0, 1), (0, -1)
            ])

        elif isinstance(piece, Queen):
            straight_line_moves([
                (1, 1), (1, -1), (-1, 1), (-1, -1),
                (1, 0), (-1, 0), (0, 1), (0, -1)
            ])

        elif isinstance(piece, King):
            king_moves()

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

    def check_promotion(self, piece, final):
        if final.row == 0 or final.row == 7:
            self.squares[final.row][final.col].piece = Queen(piece.colour)
