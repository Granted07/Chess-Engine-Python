import copy

import math

from const import *


def static_eval(board):
    evaluation = 0
    for row in range(ROWS):
        for col in range(COLS):
            if board.squares[row][col].has_piece():
                piece = board.squares[row][col].piece
                evaluation += piece.value
    return evaluation


def game_over(board, maximizingPlayer):
    for row in range(ROWS):
        for col in range(COLS):
            colour = 'white' if maximizingPlayer else 'black'
            if board.squares[row][col].has_enemy_piece(colour):
                piece = board.squares[row][col].piece
                piece.clear_moves()
                board.calc_moves(piece, row, col)
                move_list = [str(m) for m in piece.moves]
                if len(move_list) != 0:
                    return False
    return True


def minimax(board, alpha=-math.inf, beta=math.inf, depth=2, maximizingPlayer=True):
    x: bool = depth == 0 or game_over(board, maximizingPlayer)
    if x:
        return static_eval(board)

    # maximizing
    if maximizingPlayer:
        maxEval = -math.inf
        for row in range(ROWS):
            for col in range(COLS):
                # calculate child node
                if board.squares[row][col].has_team_piece('black'):
                    piece = board.squares[row][col].piece
                    # piece.clear_moves()
                    board.calc_moves(piece, row, col)
                    if len(piece.moves) > 0:
                        for move in piece.moves:
                            temp_piece = copy.deepcopy(piece)
                            temp_board = copy.deepcopy(board)
                            temp_board.move(temp_piece, move)
                            evaluation = minimax(temp_board, alpha, beta, depth - 1, True)
                            maxEval = max(maxEval, evaluation)
                            alpha = max(alpha, maxEval)
                            if maxEval >= beta:
                                break
                            if depth == 2:
                                print(f'Black: {str(move)}, Depth: {depth}, Evaluation: {maxEval}')

        return maxEval

    # minimising
    else:
        minEval = math.inf
        for row in range(ROWS):
            for col in range(COLS):
                # calculate child node
                if board.squares[row][col].has_team_piece('white'):
                    piece = board.squares[row][col].piece
                    piece.clear_moves()
                    board.calc_moves(piece, row, col)
                    if len(piece.moves) > 0:
                        for move in piece.moves:
                            # if depth == 3:
                            # print(f'White: {str(move)}, Depth: {depth}')
                            temp_piece = copy.deepcopy(piece)
                            temp_board = copy.deepcopy(board)
                            temp_board.move(temp_piece, move)
                            # passing child through recursion
                            evaluation = minimax(temp_board, alpha, beta, depth - 1, False)
                            minEval = min(minEval, evaluation)
                            beta = min(beta, minEval)
                            if minEval <= alpha:
                                break

        return minEval
