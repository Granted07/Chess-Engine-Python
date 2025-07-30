import copy
import math
import time
from const import *


def static_eval(board, verbose=False):
    """Improved evaluation function with positional considerations"""
    evaluation = 0
    piece_count = {'white': {}, 'black': {}}

    if verbose:
        print("\n--- POSITION EVALUATION ---")

    for row in range(ROWS):
        for col in range(COLS):
            if board.squares[row][col].has_piece():
                piece = board.squares[row][col].piece
                evaluation += piece.value

                # Count pieces for verbose output
                if piece.name not in piece_count[piece.colour]:
                    piece_count[piece.colour][piece.name] = 0
                piece_count[piece.colour][piece.name] += 1

                if verbose:
                    print(f"  {piece.colour.capitalize()} {piece.name} at ({row},{col}): {piece.value:+d}")

    if verbose:
        print(f"\nPiece Count:")
        for color in ['white', 'black']:
            print(f"  {color.capitalize()}: {piece_count[color]}")
        print(f"Total Evaluation: {evaluation:+d}")
        print("--- END EVALUATION ---\n")

    return evaluation


def is_game_over(board, color, verbose=False):
    """Check if the game is over for the given color"""
    if verbose:
        print(f"\n--- CHECKING GAME OVER FOR {color.upper()} ---")

    # Check if king exists
    king_pos = find_king(board, color)
    if king_pos is None:
        if verbose:
            print(f"  GAME OVER: {color} king not found!")
        return True

    if verbose:
        print(f"  {color} king found at {king_pos}")

    # Generate all legal moves for the color
    legal_moves = get_all_legal_moves(board, color, verbose=verbose)
    is_over = len(legal_moves) == 0

    if verbose:
        if is_over:
            print(f"  GAME OVER: No legal moves for {color}")
        else:
            print(f"  Game continues: {len(legal_moves)} legal moves available")
        print("--- END GAME OVER CHECK ---\n")

    return is_over


def find_king(board, color):
    """Find the king position for the given color"""
    for row in range(ROWS):
        for col in range(COLS):
            if board.squares[row][col].has_piece():
                piece = board.squares[row][col].piece
                if piece.name == 'king' and piece.colour == color:
                    return (row, col)
    return None


def get_all_legal_moves(board, color, verbose=False):
    """Get all legal moves for a given color"""
    legal_moves = []

    if verbose:
        print(f"\n--- GENERATING LEGAL MOVES FOR {color.upper()} ---")

    for row in range(ROWS):
        for col in range(COLS):
            if board.squares[row][col].has_piece():
                piece = board.squares[row][col].piece
                if piece.colour == color:
                    piece.clear_moves()
                    board.calc_moves(piece, row, col)

                    if verbose and len(piece.moves) > 0:
                        print(f"  {piece.name.capitalize()} at ({row},{col}):")

                    for move in piece.moves:
                        legal_moves.append((piece, (row, col), move))
                        if verbose:
                            captured = "captures" if board.squares[move.final.row][
                                move.final.col].has_piece() else "moves to"
                            print(f"    -> {captured} ({move.final.row},{move.final.col})")

    if verbose:
        print(f"Total legal moves for {color}: {len(legal_moves)}")
        print("--- END MOVE GENERATION ---\n")

    return legal_moves


def minimax(board, depth, alpha=-math.inf, beta=math.inf, maximizing_player=True, verbose=False, indent_level=0):
    """
    Verbose minimax implementation with alpha-beta pruning
    """
    indent = "  " * indent_level
    color = 'black' if maximizing_player else 'white'
    player_type = "MAXIMIZING" if maximizing_player else "MINIMIZING"

    if verbose:
        print(f"{indent}--- MINIMAX DEPTH {depth} ({player_type} - {color.upper()}) ---")
        print(f"{indent}Alpha: {alpha:.1f}, Beta: {beta:.1f}")

    # Base case: terminal node
    if depth == 0 or is_game_over(board, color, verbose=verbose and depth <= 2):
        eval_result = static_eval(board, verbose=verbose and depth <= 1)
        if verbose:
            print(f"{indent}LEAF NODE: Evaluation = {eval_result:+d}")
        return eval_result

    # Get all legal moves for current player
    legal_moves = get_all_legal_moves(board, color, verbose=verbose and depth <= 2)

    if not legal_moves:
        if verbose:
            print(f"{indent}NO LEGAL MOVES - TERMINAL STATE")
        return static_eval(board)

    moves_evaluated = 0
    pruned_moves = 0

    if maximizing_player:
        max_eval = -math.inf
        if verbose:
            print(f"{indent}Evaluating {len(legal_moves)} moves for {color}...")

        for i, (piece, (start_row, start_col), move) in enumerate(legal_moves):
            moves_evaluated += 1

            if verbose and depth <= 2:
                captured = board.squares[move.final.row][move.final.col].has_piece()
                action = "captures" if captured else "moves to"
                print(
                    f"{indent}  [{i + 1}/{len(legal_moves)}] {piece.name} ({start_row},{start_col}) {action} ({move.final.row},{move.final.col})")

            # Make move
            temp_board = copy.deepcopy(board)
            temp_piece = temp_board.squares[start_row][start_col].piece
            temp_board.move(temp_piece, move)

            # Recursive call
            eval_score = minimax(temp_board, depth - 1, alpha, beta, False, verbose, indent_level + 1)

            if verbose and depth <= 2:
                print(f"{indent}    Score: {eval_score:+d}")

            if eval_score > max_eval:
                max_eval = eval_score
                if verbose and depth <= 2:
                    print(f"{indent}    NEW BEST for {color}: {max_eval:+d}")

            alpha = max(alpha, eval_score)

            # Alpha-beta pruning
            if beta <= alpha:
                pruned_moves = len(legal_moves) - moves_evaluated
                if verbose and depth <= 2:
                    print(
                        f"{indent}    PRUNING: Beta({beta:.1f}) <= Alpha({alpha:.1f}) - Skipping {pruned_moves} moves")
                break

        if verbose:
            print(
                f"{indent}MAX RESULT: {max_eval:+d} (evaluated {moves_evaluated}/{len(legal_moves)} moves, pruned {pruned_moves})")
        return max_eval

    else:  # Minimizing player
        min_eval = math.inf
        if verbose:
            print(f"{indent}Evaluating {len(legal_moves)} moves for {color}...")

        for i, (piece, (start_row, start_col), move) in enumerate(legal_moves):
            moves_evaluated += 1

            if verbose and depth <= 2:
                captured = board.squares[move.final.row][move.final.col].has_piece()
                action = "captures" if captured else "moves to"
                print(
                    f"{indent}  [{i + 1}/{len(legal_moves)}] {piece.name} ({start_row},{start_col}) {action} ({move.final.row},{move.final.col})")

            # Make move
            temp_board = copy.deepcopy(board)
            temp_piece = temp_board.squares[start_row][start_col].piece
            temp_board.move(temp_piece, move)

            # Recursive call
            eval_score = minimax(temp_board, depth - 1, alpha, beta, True, verbose, indent_level + 1)

            if verbose and depth <= 2:
                print(f"{indent}    Score: {eval_score:+d}")

            if eval_score < min_eval:
                min_eval = eval_score
                if verbose and depth <= 2:
                    print(f"{indent}    NEW BEST for {color}: {min_eval:+d}")

            beta = min(beta, eval_score)

            # Alpha-beta pruning
            if beta <= alpha:
                pruned_moves = len(legal_moves) - moves_evaluated
                if verbose and depth <= 2:
                    print(
                        f"{indent}    PRUNING: Beta({beta:.1f}) <= Alpha({alpha:.1f}) - Skipping {pruned_moves} moves")
                break

        if verbose:
            print(
                f"{indent}MIN RESULT: {min_eval:+d} (evaluated {moves_evaluated}/{len(legal_moves)} moves, pruned {pruned_moves})")
        return min_eval


def get_best_move(board, depth=3, maximizing_player=True, verbose=False):
    """
    Get the best move using minimax algorithm with detailed logging
    """
    start_time = time.time()
    color = 'black' if maximizing_player else 'white'
    player_type = "MAXIMIZING" if maximizing_player else "MINIMIZING"

    if verbose:
        print(f"\n{'=' * 60}")
        print(f"STARTING AI ANALYSIS FOR {color.upper()} ({player_type})")
        print(f"Search Depth: {depth}")
        print(f"{'=' * 60}")

    legal_moves = get_all_legal_moves(board, color, verbose=verbose)

    if not legal_moves:
        if verbose:
            print("NO LEGAL MOVES AVAILABLE!")
        return None

    best_move = None
    best_eval = -math.inf if maximizing_player else math.inf
    moves_analyzed = 0

    if verbose:
        print(f"\n--- ANALYZING {len(legal_moves)} ROOT MOVES ---")

    for i, (piece, (start_row, start_col), move) in enumerate(legal_moves):
        moves_analyzed += 1

        if verbose:
            captured_piece = board.squares[move.final.row][move.final.col].piece
            capture_info = f" (captures {captured_piece.colour} {captured_piece.name})" if captured_piece else ""
            print(
                f"\n[{i + 1}/{len(legal_moves)}] Analyzing: {piece.name} ({start_row},{start_col}) -> ({move.final.row},{move.final.col}){capture_info}")

        # Make move
        temp_board = copy.deepcopy(board)
        temp_piece = temp_board.squares[start_row][start_col].piece
        temp_board.move(temp_piece, move)

        # Evaluate position
        move_start_time = time.time()
        eval_score = minimax(temp_board, depth - 1, -math.inf, math.inf, not maximizing_player, verbose, 1)
        move_time = time.time() - move_start_time

        if verbose:
            print(f"  Final Score: {eval_score:+d} (analyzed in {move_time:.3f}s)")

        # Update best move
        is_better = (maximizing_player and eval_score > best_eval) or (not maximizing_player and eval_score < best_eval)

        if is_better:
            best_eval = eval_score
            best_move = (piece, (start_row, start_col), move)
            if verbose:
                print(f"  *** NEW BEST MOVE! Score: {best_eval:+d} ***")

    total_time = time.time() - start_time

    if verbose:
        print(f"\n{'=' * 60}")
        print(f"AI ANALYSIS COMPLETE")
        print(f"Total Time: {total_time:.3f}s")
        print(f"Moves Analyzed: {moves_analyzed}")
        print(f"Average Time per Move: {total_time / moves_analyzed:.3f}s")

        if best_move:
            piece, (start_row, start_col), move = best_move
            captured_piece = board.squares[move.final.row][move.final.col].piece
            capture_info = f" (captures {captured_piece.colour} {captured_piece.name})" if captured_piece else ""
            print(
                f"BEST MOVE: {piece.name} ({start_row},{start_col}) -> ({move.final.row},{move.final.col}){capture_info}")
            print(f"BEST SCORE: {best_eval:+d}")
        else:
            print("NO BEST MOVE FOUND!")
        print(f"{'=' * 60}\n")

    return best_move


def analyze_position(board, depth=3, verbose=True):
    """
    Analyze current position for both colors
    """
    print(f"\n{'=' * 80}")
    print(f"FULL POSITION ANALYSIS")
    print(f"{'=' * 80}")

    # Analyze for white
    print(f"\n--- WHITE'S PERSPECTIVE ---")
    white_move = get_best_move(board, depth, maximizing_player=False, verbose=verbose)

    # Analyze for black
    print(f"\n--- BLACK'S PERSPECTIVE ---")
    black_move = get_best_move(board, depth, maximizing_player=True, verbose=verbose)

    return white_move, black_move