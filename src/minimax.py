import copy
import math
import time
import threading
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
import hashlib
import pickle
from const import *

try:
    import cupy as cp
    import numba
    from numba import cuda, jit

    GPU_AVAILABLE = True
except ImportError:
    GPU_AVAILABLE = False

try:
    import intel_npu_acceleration_library as npu_lib

    NPU_AVAILABLE = True
except ImportError:
    NPU_AVAILABLE = False

transposition_table = {}
table_lock = threading.Lock()

class PerformanceTracker:
    def __init__(self):
        self.nodes_searched = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.pruned_branches = 0
        self.start_time = 0
        self.lock = threading.Lock()

    def reset(self):
        with self.lock:
            self.nodes_searched = 0
            self.cache_hits = 0
            self.cache_misses = 0
            self.pruned_branches = 0
            self.start_time = time.time()

    def add_node(self):
        with self.lock:
            self.nodes_searched += 1

    def add_cache_hit(self):
        with self.lock:
            self.cache_hits += 1

    def add_cache_miss(self):
        with self.lock:
            self.cache_misses += 1

    def add_pruning(self):
        with self.lock:
            self.pruned_branches += 1

    def get_stats(self):
        elapsed = time.time() - self.start_time
        with self.lock:
            return {
                'nodes': self.nodes_searched,
                'nps': self.nodes_searched / max(elapsed, 0.001),
                'cache_hit_rate': self.cache_hits / max(self.cache_hits + self.cache_misses, 1),
                'pruning_rate': self.pruned_branches / max(self.nodes_searched, 1),
                'time': elapsed
            }


perf_tracker = PerformanceTracker()


def get_board_hash(board):
    """Create a hash of the board state for transposition table"""
    board_str = ""
    for row in range(ROWS):
        for col in range(COLS):
            if board.squares[row][col].has_piece():
                piece = board.squares[row][col].piece
                board_str += f"{piece.colour[0]}{piece.name[0]}{row}{col}"
            else:
                board_str += "empty"
    return hashlib.md5(board_str.encode()).hexdigest()


@jit(nopython=True) if GPU_AVAILABLE else lambda x: x
def fast_piece_square_tables():
    """Numba-optimized piece-square tables for position evaluation"""
    pawn_table = [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [50, 50, 50, 50, 50, 50, 50, 50],
        [10, 10, 20, 30, 30, 20, 10, 10],
        [5, 5, 10, 25, 25, 10, 5, 5],
        [0, 0, 0, 20, 20, 0, 0, 0],
        [5, -5, -10, 0, 0, -10, -5, 5],
        [5, 10, 10, -20, -20, 10, 10, 5],
        [0, 0, 0, 0, 0, 0, 0, 0]
    ]
    return pawn_table


class OptimizedEvaluator:
    def __init__(self):
        self.piece_values = {
            'pawn': 100, 'knight': 320, 'bishop': 330,
            'rook': 500, 'queen': 900, 'king': 20000
        }
        self.position_tables = self._init_position_tables()

    def _init_position_tables(self):
        """Initialize piece-square tables for positional evaluation"""
        return {
            'pawn': [
                [0, 0, 0, 0, 0, 0, 0, 0],
                [50, 50, 50, 50, 50, 50, 50, 50],
                [10, 10, 20, 30, 30, 20, 10, 10],
                [5, 5, 10, 25, 25, 10, 5, 5],
                [0, 0, 0, 20, 20, 0, 0, 0],
                [5, -5, -10, 0, 0, -10, -5, 5],
                [5, 10, 10, -20, -20, 10, 10, 5],
                [0, 0, 0, 0, 0, 0, 0, 0]
            ],
            'knight': [
                [-50, -40, -30, -30, -30, -30, -40, -50],
                [-40, -20, 0, 0, 0, 0, -20, -40],
                [-30, 0, 10, 15, 15, 10, 0, -30],
                [-30, 5, 15, 20, 20, 15, 5, -30],
                [-30, 0, 15, 20, 20, 15, 0, -30],
                [-30, 5, 10, 15, 15, 10, 5, -30],
                [-40, -20, 0, 5, 5, 0, -20, -40],
                [-50, -40, -30, -30, -30, -30, -40, -50]
            ],
            'king': [
                [-30, -40, -40, -50, -50, -40, -40, -30],
                [-30, -40, -40, -50, -50, -40, -40, -30],
                [-30, -40, -40, -50, -50, -40, -40, -30],
                [-30, -40, -40, -50, -50, -40, -40, -30],
                [-20, -30, -30, -40, -40, -30, -30, -20],
                [-10, -20, -20, -20, -20, -20, -20, -10],
                [20, 20, 0, 0, 0, 0, 20, 20],
                [20, 30, 10, 0, 0, 10, 30, 20]
            ]
        }

    def advanced_eval(self, board):
        """Advanced position evaluation with multiple factors"""
        material_score = 0
        positional_score = 0

        white_pieces = []
        black_pieces = []

        for row in range(ROWS):
            for col in range(COLS):
                if board.squares[row][col].has_piece():
                    piece = board.squares[row][col].piece

                    base_value = self.piece_values.get(piece.name, 0)
                    if piece.colour == 'white':
                        material_score += base_value
                        white_pieces.append((piece, row, col))
                    else:
                        material_score -= base_value
                        black_pieces.append((piece, row, col))

                    if piece.name in self.position_tables:
                        pos_value = self.position_tables[piece.name][row][col]
                        if piece.colour == 'white':
                            positional_score += pos_value
                        else:
                            positional_score -= pos_value

        white_mobility = len(get_all_legal_moves_fast(board, 'white'))
        black_mobility = len(get_all_legal_moves_fast(board, 'black'))
        mobility_score = (white_mobility - black_mobility) * 10

        total_score = material_score + positional_score + mobility_score
        return total_score


evaluator = OptimizedEvaluator()


def get_all_legal_moves_fast(board, color):
    """Optimized move generation"""
    legal_moves = []
    for row in range(ROWS):
        for col in range(COLS):
            if board.squares[row][col].has_piece():
                piece = board.squares[row][col].piece
                if piece.colour == color:
                    piece.clear_moves()
                    board.calc_moves(piece, row, col)
                    for move in piece.moves:
                        legal_moves.append((piece, (row, col), move))
    return legal_moves


def order_moves(board, legal_moves):
    """Advanced move ordering for better alpha-beta pruning"""

    def move_priority(move_data):
        piece, (start_row, start_col), move = move_data
        score = 0

        target_square = board.squares[move.final.row][move.final.col]
        if target_square.has_piece():
            captured_piece = target_square.piece
            score += evaluator.piece_values.get(captured_piece.name, 0) * 10
            score -= evaluator.piece_values.get(piece.name, 0)

        center_bonus = 0
        if 2 <= move.final.row <= 5 and 2 <= move.final.col <= 5:
            center_bonus = 20
        score += center_bonus

        if piece.name in ['knight', 'bishop'] and not piece.moved:
            score += 15

        return -score

    return sorted(legal_moves, key=move_priority)


class ParallelMinimax:
    def __init__(self, max_workers=None):
        self.max_workers = max_workers or min(mp.cpu_count(), 8)

    def evaluate_move_parallel(self, args):
        """Evaluate a single move - designed for multiprocessing"""
        board_data, move_data, depth, alpha, beta, maximizing_player = args

        board = pickle.loads(board_data)
        piece, (start_row, start_col), move = move_data

        temp_board = copy.deepcopy(board)
        temp_piece = temp_board.squares[start_row][start_col].piece
        temp_board.move(temp_piece, move)

        score = optimized_minimax(temp_board, depth - 1, alpha, beta,
                                  not maximizing_player, use_parallel=False)

        return score, move_data


def optimized_minimax(board, depth, alpha=-math.inf, beta=math.inf,
                      maximizing_player=True, use_cache=True, use_parallel=True,
                      move_ordering=True, verbose=False):
    """
    Highly optimized minimax with multiple acceleration techniques
    """
    perf_tracker.add_node()
    if use_cache:
        board_hash = get_board_hash(board)
        with table_lock:
            if board_hash in transposition_table:
                cached_depth, cached_score, cached_flag = transposition_table[board_hash]
                if cached_depth >= depth:
                    perf_tracker.add_cache_hit()
                    return cached_score
        perf_tracker.add_cache_miss()

    color = 'black' if maximizing_player else 'white'
    if depth == 0:
        score = evaluator.advanced_eval(board)
        if use_cache:
            with table_lock:
                transposition_table[board_hash] = (depth, score, 'exact')
        return score


    legal_moves = get_all_legal_moves_fast(board, color)
    if not legal_moves:
        score = evaluator.advanced_eval(board)
        return score

    if move_ordering:
        legal_moves = order_moves(board, legal_moves)

    if use_parallel and depth >= 4 and len(legal_moves) > 4:
        return parallel_minimax_root(board, legal_moves, depth, alpha, beta, maximizing_player)

    best_score = -math.inf if maximizing_player else math.inf

    for move_data in legal_moves:
        piece, (start_row, start_col), move = move_data

        temp_board = copy.deepcopy(board)
        temp_piece = temp_board.squares[start_row][start_col].piece
        temp_board.move(temp_piece, move)

        score = optimized_minimax(temp_board, depth - 1, alpha, beta,
                                  not maximizing_player, use_cache, False, move_ordering)

        if maximizing_player:
            if score > best_score:
                best_score = score
            alpha = max(alpha, score)
            if beta <= alpha:
                perf_tracker.add_pruning()
                break
        else:
            if score < best_score:
                best_score = score
            beta = min(beta, score)
            if beta <= alpha:
                perf_tracker.add_pruning()
                break

    if use_cache:
        with table_lock:
            transposition_table[board_hash] = (depth, best_score, 'exact')

    return best_score


def parallel_minimax_root(board, legal_moves, depth, alpha, beta, maximizing_player):
    """Parallel evaluation of root moves"""
    parallel_minimax = ParallelMinimax()

    board_data = pickle.dumps(board)
    args_list = []

    for move_data in legal_moves:
        args = (board_data, move_data, depth, alpha, beta, maximizing_player)
        args_list.append(args)

    best_score = -math.inf if maximizing_player else math.inf

    with ProcessPoolExecutor(max_workers=parallel_minimax.max_workers) as executor:
        future_to_move = {executor.submit(parallel_minimax.evaluate_move_parallel, args): args[1]
                          for args in args_list}

        for future in as_completed(future_to_move):
            try:
                score, move_data = future.result(timeout=30)

                if maximizing_player and score > best_score:
                    best_score = score
                elif not maximizing_player and score < best_score:
                    best_score = score

            except Exception as e:
                print(f"Parallel evaluation error: {e}")

    return best_score


def get_best_move_optimized(board, depth=5, maximizing_player=True,
                            time_limit=None, verbose=False):
    """
    Get best move with all optimizations enabled
    """
    start_time = time.time()
    perf_tracker.reset()

    color = 'black' if maximizing_player else 'white'

    if verbose:
        print(f"\n{'=' * 80}")
        print(f"Chess Engine Move Search for {color.upper()}")
        print(f"Hardware detected: GPU [{'Yes' if GPU_AVAILABLE else 'No'}], NPU [{'Yes' if NPU_AVAILABLE else 'No'}]")
        print(f"Search depth: {depth} | Time limit: {time_limit if time_limit else 'None'}s")
        print(f"CPU cores available: {mp.cpu_count()}")
        print(f"{'=' * 80}")

    best_move = None
    best_score = -math.inf if maximizing_player else math.inf

    legal_moves = get_all_legal_moves_fast(board, color)
    ordered_moves = order_moves(board, legal_moves)

    if not legal_moves:
        return None

    for current_depth in range(1, depth + 1):
        if time_limit and (time.time() - start_time) > time_limit * 0.8:
            break

        depth_start = time.time()
        current_best = None
        current_best_score = -math.inf if maximizing_player else math.inf

        for i, move_data in enumerate(ordered_moves):
            piece, (start_row, start_col), move = move_data

            if time_limit and (time.time() - start_time) > time_limit * 0.9:
                break

            temp_board = copy.deepcopy(board)
            temp_piece = temp_board.squares[start_row][start_col].piece
            temp_board.move(temp_piece, move)

            score = optimized_minimax(temp_board, current_depth - 1,
                                      -math.inf, math.inf, not maximizing_player,
                                      use_cache=True, use_parallel=current_depth >= 4)

            is_better = (maximizing_player and score > current_best_score) or \
                        (not maximizing_player and score < current_best_score)

            if is_better:
                current_best_score = score
                current_best = move_data

        if current_best:
            best_move = current_best
            best_score = current_best_score

        depth_time = time.time() - depth_start
        stats = perf_tracker.get_stats()

        if verbose:
            print(f"Depth {current_depth}: Score {current_best_score:+d} | Time: {depth_time:.3f}s | Nodes/sec: {stats['nps']:.0f}")

    total_time = time.time() - start_time
    final_stats = perf_tracker.get_stats()

    if verbose:
        print(f"\n--- Search Complete ---")
        print(f"Best move found: {best_move[0].name if best_move else 'None'}")
        print(f"Score: {best_score:+d}")
        print(f"Total time: {total_time:.3f}s")
        print(f"Nodes searched: {final_stats['nodes']:,}")
        print(f"Speed: {final_stats['nps']:,.0f} nodes/sec")
        print(f"Cache hits: {final_stats['cache_hit_rate']:.1%} | Pruning: {final_stats['pruning_rate']:.1%}")
        print(f"Transposition table entries: {len(transposition_table):,}")
        print(f"{'=' * 80}\n")

    return best_move


def clear_transposition_table():
    """Clear the transposition table to free memory"""
    global transposition_table
    with table_lock:
        transposition_table.clear()


# GPU-accelerated evaluation (if available)
if GPU_AVAILABLE:
    @cuda.jit
    def gpu_evaluate_positions(board_arrays, results):
        """GPU kernel for batch position evaluation"""
        idx = cuda.grid(1)
        if idx < board_arrays.shape[0]:
            # Simple material count on GPU
            score = 0
            for i in range(64):
                piece_value = board_arrays[idx, i]
                score += piece_value
            results[idx] = score


    def batch_evaluate_gpu(boards):
        """Evaluate multiple positions on GPU"""
        if not boards:
            return []

        # Convert boards to GPU arrays
        board_arrays = cp.array([[get_piece_value(board, i // 8, i % 8)
                                  for i in range(64)] for board in boards])
        results = cp.zeros(len(boards))

        # Launch GPU kernel
        threads_per_block = 256
        blocks_per_grid = (len(boards) + threads_per_block - 1) // threads_per_block
        gpu_evaluate_positions[blocks_per_grid, threads_per_block](board_arrays, results)

        return results.get().tolist()


def get_piece_value(board, row, col):
    """Helper function to get piece value for GPU processing"""
    if board.squares[row][col].has_piece():
        piece = board.squares[row][col].piece
        value = evaluator.piece_values.get(piece.name, 0)
        return value if piece.colour == 'white' else -value
    return 0


# Usage example for your main.py:
def integrate_with_main():
    """
    Integration example for main.py
    Replace your existing minimax call with:

    if game.next_player == 'white':
        best_move = get_best_move_optimized(
            board,
            depth=6,  # Increased depth due to optimizations
            maximizing_player=False,
            time_limit=5.0,  # 5 second time limit
            verbose=True
        )
        if best_move:
            piece, (start_row, start_col), move = best_move
            # Apply the move or show to user
    """
    pass