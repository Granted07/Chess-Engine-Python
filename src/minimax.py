import math
import random
import time

from const import ROWS, COLS
from move import Move
from square import Square
from piece import Pawn, Knight, Bishop, Rook, Queen, King

# ---------------------------------------------------------------------------
# Fast constants and tables
# ---------------------------------------------------------------------------
INF = 10**9
EXACT, LOWERBOUND, UPPERBOUND = 0, 1, 2

PIECE_VALUES = {
    'pawn': 100,
    'knight': 320,
    'bishop': 330,
    'rook': 500,
    'queen': 900,
    'king': 20000,
}

# Piece-square tables (white perspective). Black is mirrored.
PST = {
    'pawn': [
        [0, 0, 0, 0, 0, 0, 0, 0],
        [50, 50, 50, 50, 50, 50, 50, 50],
        [10, 10, 20, 30, 30, 20, 10, 10],
        [5, 5, 10, 25, 25, 10, 5, 5],
        [0, 0, 0, 20, 20, 0, 0, 0],
        [5, -5, -10, 0, 0, -10, -5, 5],
        [5, 10, 10, -20, -20, 10, 10, 5],
        [0, 0, 0, 0, 0, 0, 0, 0],
    ],
    'knight': [
        [-50, -40, -30, -30, -30, -30, -40, -50],
        [-40, -20, 0, 0, 0, 0, -20, -40],
        [-30, 0, 10, 15, 15, 10, 0, -30],
        [-30, 5, 15, 20, 20, 15, 5, -30],
        [-30, 0, 15, 20, 20, 15, 0, -30],
        [-30, 5, 10, 15, 15, 10, 5, -30],
        [-40, -20, 0, 5, 5, 0, -20, -40],
        [-50, -40, -30, -30, -30, -30, -40, -50],
    ],
    'bishop': [
        [-20, -10, -10, -10, -10, -10, -10, -20],
        [-10, 5, 0, 0, 0, 0, 5, -10],
        [-10, 10, 10, 10, 10, 10, 10, -10],
        [-10, 0, 10, 10, 10, 10, 0, -10],
        [-10, 5, 5, 10, 10, 5, 5, -10],
        [-10, 0, 5, 10, 10, 5, 0, -10],
        [-10, 0, 0, 0, 0, 0, 0, -10],
        [-20, -10, -10, -10, -10, -10, -10, -20],
    ],
    'rook': [
        [0, 0, 0, 5, 5, 0, 0, 0],
        [-5, 0, 0, 0, 0, 0, 0, -5],
        [-5, 0, 0, 0, 0, 0, 0, -5],
        [-5, 0, 0, 0, 0, 0, 0, -5],
        [-5, 0, 0, 0, 0, 0, 0, -5],
        [-5, 0, 0, 0, 0, 0, 0, -5],
        [5, 10, 10, 10, 10, 10, 10, 5],
        [0, 0, 0, 0, 0, 0, 0, 0],
    ],
    'queen': [
        [-20, -10, -10, -5, -5, -10, -10, -20],
        [-10, 0, 0, 0, 0, 0, 0, -10],
        [-10, 0, 5, 5, 5, 5, 0, -10],
        [-5, 0, 5, 5, 5, 5, 0, -5],
        [0, 0, 5, 5, 5, 5, 0, -5],
        [-10, 5, 5, 5, 5, 5, 0, -10],
        [-10, 0, 5, 0, 0, 0, 0, -10],
        [-20, -10, -10, -5, -5, -10, -10, -20],
    ],
    'king': [
        [-30, -40, -40, -50, -50, -40, -40, -30],
        [-30, -40, -40, -50, -50, -40, -40, -30],
        [-30, -40, -40, -50, -50, -40, -40, -30],
        [-30, -40, -40, -50, -50, -40, -40, -30],
        [-20, -30, -30, -40, -40, -30, -30, -20],
        [-10, -20, -20, -20, -20, -20, -20, -10],
        [20, 20, 0, 0, 0, 0, 20, 20],
        [20, 30, 10, 0, 0, 10, 30, 20],
    ],
}

# ---------------------------------------------------------------------------
# Zobrist hashing
# ---------------------------------------------------------------------------
random.seed(20241229)
PIECE_INDEX = {
    ('white', 'pawn'): 0,
    ('white', 'knight'): 1,
    ('white', 'bishop'): 2,
    ('white', 'rook'): 3,
    ('white', 'queen'): 4,
    ('white', 'king'): 5,
    ('black', 'pawn'): 6,
    ('black', 'knight'): 7,
    ('black', 'bishop'): 8,
    ('black', 'rook'): 9,
    ('black', 'queen'): 10,
    ('black', 'king'): 11,
}
ZOBRIST_PIECES = [[random.getrandbits(64) for _ in range(64)] for _ in range(12)]
ZOBRIST_SIDE = random.getrandbits(64)
ZOBRIST_CASTLING = [random.getrandbits(64) for _ in range(16)]
ZOBRIST_EP = [random.getrandbits(64) for _ in range(8)]
Q_DEPTH_LIMIT = 8

# ---------------------------------------------------------------------------
# Engine state container
# ---------------------------------------------------------------------------
class EngineState:
    def __init__(self):
        self.tt = {}
        self.killers = [[None, None] for _ in range(128)]
        self.history = {}
        self.nodes = 0
        self.tt_hits = 0
        self.cutoffs = 0
        self.start_time = 0.0
        self.time_limit = None
        self.current_hash = 0
        self.castling_rights = 0
        self.ep_file = None
        self.king_pos = {'white': (0, 4), 'black': (7, 4)}

    def reset(self, start_hash, time_limit=None):
        self.nodes = 0
        self.tt_hits = 0
        self.cutoffs = 0
        self.start_time = time.time()
        self.time_limit = time_limit
        self.current_hash = start_hash
        self.castling_rights = 0
        self.ep_file = None

engine = EngineState()

# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def mirror_index(row):
    return 7 - row


def pst_value(piece, row, col):
    table = PST.get(piece.name)
    if table is None:
        return 0
    return table[row][col] if piece.colour == 'white' else table[mirror_index(row)][col]


def evaluate(board):
    score = 0
    for row in range(ROWS):
        row_squares = board.squares[row]
        for col in range(COLS):
            p = row_squares[col].piece
            if p:
                base = PIECE_VALUES[p.name]
                sign = 1 if p.colour == 'white' else -1
                score += sign * base
                score += sign * pst_value(p, row, col)
    return score


def detect_castling_rights(board):
    rights = 0
    wk = board.squares[7][4].piece
    wkr = board.squares[7][7].piece
    wqr = board.squares[7][0].piece
    bk = board.squares[0][4].piece
    bkr = board.squares[0][7].piece
    bqr = board.squares[0][0].piece
    if isinstance(wk, King) and not wk.moved:
        if isinstance(wkr, Rook) and not wkr.moved:
            rights |= 1
        if isinstance(wqr, Rook) and not wqr.moved:
            rights |= 2
    if isinstance(bk, King) and not bk.moved:
        if isinstance(bkr, Rook) and not bkr.moved:
            rights |= 4
        if isinstance(bqr, Rook) and not bqr.moved:
            rights |= 8
    return rights


def initial_hash(board):
    h = 0
    for row in range(ROWS):
        row_squares = board.squares[row]
        for col in range(COLS):
            sqp = row_squares[col].piece
            if sqp:
                idx = PIECE_INDEX[(sqp.colour, sqp.name)]
                h ^= ZOBRIST_PIECES[idx][row * 8 + col]
                if isinstance(sqp, King):
                    engine.king_pos[sqp.colour] = (row, col)

    rights = detect_castling_rights(board)
    engine.castling_rights = rights
    h ^= ZOBRIST_CASTLING[rights]
    engine.ep_file = None
    return h

# ---------------------------------------------------------------------------
# Move encoding for heuristics/TT
# ---------------------------------------------------------------------------

def encode_move(move, promotion=None):
    return (move.initial.row, move.initial.col, move.final.row, move.final.col, promotion)


def same_move(a, b):
    return a and b and encode_move(a) == encode_move(b)

# ---------------------------------------------------------------------------
# Attack detection
# ---------------------------------------------------------------------------
KNIGHT_OFFSETS = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
KING_OFFSETS = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def square_attacked(board, row, col, attacker_colour):
    pawn_dir = -1 if attacker_colour == 'white' else 1
    pawn_rows = row + pawn_dir
    for dc in (-1, 1):
        c = col + dc
        if 0 <= pawn_rows < 8 and 0 <= c < 8:
            p = board.squares[pawn_rows][c].piece
            if isinstance(p, Pawn) and p.colour == attacker_colour:
                return True

    for dr, dc in KNIGHT_OFFSETS:
        r, c = row + dr, col + dc
        if 0 <= r < 8 and 0 <= c < 8:
            p = board.squares[r][c].piece
            if isinstance(p, Knight) and p.colour == attacker_colour:
                return True

    # Bishops / Queens (diagonals)
    for dr, dc in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
        r, c = row + dr, col + dc
        while 0 <= r < 8 and 0 <= c < 8:
            p = board.squares[r][c].piece
            if p:
                if p.colour == attacker_colour and (isinstance(p, Bishop) or isinstance(p, Queen)):
                    return True
                break
            r += dr
            c += dc

    # Rooks / Queens (orthogonal)
    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        r, c = row + dr, col + dc
        while 0 <= r < 8 and 0 <= c < 8:
            p = board.squares[r][c].piece
            if p:
                if p.colour == attacker_colour and (isinstance(p, Rook) or isinstance(p, Queen)):
                    return True
                break
            r += dr
            c += dc

    for dr, dc in KING_OFFSETS:
        r, c = row + dr, col + dc
        if 0 <= r < 8 and 0 <= c < 8:
            p = board.squares[r][c].piece
            if isinstance(p, King) and p.colour == attacker_colour:
                return True

    return False


def king_in_check(board, colour):
    kr, kc = engine.king_pos[colour]
    return square_attacked(board, kr, kc, 'black' if colour == 'white' else 'white')

# ---------------------------------------------------------------------------
# Move generation (pseudo legal + legality test via make/unmake)
# ---------------------------------------------------------------------------

def generate_pseudo_moves(board, colour):
    moves = []
    forward = -1 if colour == 'white' else 1
    start_row = 6 if colour == 'white' else 1
    promo_row = 0 if colour == 'white' else 7

    for row in range(ROWS):
        row_squares = board.squares[row]
        for col in range(COLS):
            piece = row_squares[col].piece
            if not piece or piece.colour != colour:
                continue

            if isinstance(piece, Pawn):
                one = row + forward
                if 0 <= one < 8 and board.squares[one][col].piece is None:
                    mv = Move(Square(row, col), Square(one, col))
                    if one == promo_row:
                        moves.append((mv, 'queen'))
                    else:
                        moves.append((mv, None))
                    if row == start_row:
                        two = row + 2 * forward
                        if board.squares[two][col].piece is None:
                            moves.append((Move(Square(row, col), Square(two, col)), None))

                for dc in (-1, 1):
                    c = col + dc
                    r = row + forward
                    if 0 <= r < 8 and 0 <= c < 8:
                        target = board.squares[r][c].piece
                        if target and target.colour != colour:
                            mv = Move(Square(row, col), Square(r, c))
                            if r == promo_row:
                                moves.append((mv, 'queen'))
                            else:
                                moves.append((mv, None))
                        # en passant
                        side_piece = board.squares[row][c].piece if 0 <= c < 8 else None
                        if side_piece and isinstance(side_piece, Pawn) and side_piece.colour != colour and side_piece.en_passant:
                            moves.append((Move(Square(row, col), Square(r, c)), None))

            elif isinstance(piece, Knight):
                for dr, dc in KNIGHT_OFFSETS:
                    r, c = row + dr, col + dc
                    if 0 <= r < 8 and 0 <= c < 8:
                        target = board.squares[r][c].piece
                        if target is None or target.colour != colour:
                            moves.append((Move(Square(row, col), Square(r, c)), None))

            elif isinstance(piece, Bishop):
                for dr, dc in ((1, 1), (1, -1), (-1, 1), (-1, -1)):
                    r, c = row + dr, col + dc
                    while 0 <= r < 8 and 0 <= c < 8:
                        target = board.squares[r][c].piece
                        if target is None or target.colour != colour:
                            moves.append((Move(Square(row, col), Square(r, c)), None))
                        if target:
                            break
                        r += dr
                        c += dc

            elif isinstance(piece, Rook):
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    r, c = row + dr, col + dc
                    while 0 <= r < 8 and 0 <= c < 8:
                        target = board.squares[r][c].piece
                        if target is None or target.colour != colour:
                            moves.append((Move(Square(row, col), Square(r, c)), None))
                        if target:
                            break
                        r += dr
                        c += dc

            elif isinstance(piece, Queen):
                for dr, dc in ((1, 1), (1, -1), (-1, 1), (-1, -1), (1, 0), (-1, 0), (0, 1), (0, -1)):
                    r, c = row + dr, col + dc
                    while 0 <= r < 8 and 0 <= c < 8:
                        target = board.squares[r][c].piece
                        if target is None or target.colour != colour:
                            moves.append((Move(Square(row, col), Square(r, c)), None))
                        if target:
                            break
                        r += dr
                        c += dc

            elif isinstance(piece, King):
                for dr, dc in KING_OFFSETS:
                    r, c = row + dr, col + dc
                    if 0 <= r < 8 and 0 <= c < 8:
                        target = board.squares[r][c].piece
                        if target is None or target.colour != colour:
                            moves.append((Move(Square(row, col), Square(r, c)), None))
                # castling
                if not piece.moved and not king_in_check(board, colour):
                    # king side
                    if board.squares[row][col + 1].piece is None and board.squares[row][col + 2].piece is None:
                        rook = board.squares[row][7].piece
                        if isinstance(rook, Rook) and not rook.moved:
                            if not square_attacked(board, row, col + 1, 'black' if colour == 'white' else 'white') and not square_attacked(board, row, col + 2, 'black' if colour == 'white' else 'white'):
                                moves.append((Move(Square(row, col), Square(row, col + 2)), None))
                    # queen side
                    if board.squares[row][col - 1].piece is None and board.squares[row][col - 2].piece is None and board.squares[row][col - 3].piece is None:
                        rook = board.squares[row][0].piece
                        if isinstance(rook, Rook) and not rook.moved:
                            if not square_attacked(board, row, col - 1, 'black' if colour == 'white' else 'white') and not square_attacked(board, row, col - 2, 'black' if colour == 'white' else 'white'):
                                moves.append((Move(Square(row, col), Square(row, col - 2)), None))
    return moves


def generate_legal_moves(board, colour):
    legal = []
    for move, promo in generate_pseudo_moves(board, colour):
        undo, new_hash = make_move(board, move, promo, colour)
        engine.current_hash = new_hash
        if not king_in_check(board, colour):
            legal.append((move, promo))
        undo_move(board, move, undo)
        engine.current_hash = undo['prev_hash']
    return legal

# ---------------------------------------------------------------------------
# Make / unmake with incremental hash
# ---------------------------------------------------------------------------

def clear_en_passant(board):
    for r in range(ROWS):
        for c in range(COLS):
            p = board.squares[r][c].piece
            if isinstance(p, Pawn):
                p.en_passant = False


def make_move(board, move, promotion, colour):
    initial = move.initial
    final = move.final
    piece = board.squares[initial.row][initial.col].piece

    prev_hash = engine.current_hash
    prev_last = getattr(board, 'last_move', None)
    prev_castling = engine.castling_rights
    prev_ep = engine.ep_file

    captured_piece = None
    captured_pos = (final.row, final.col)
    is_en_passant = False
    is_castle = False
    promotion_piece = None
    piece_moved_prev = piece.moved
    rook_state = None

    piece_idx = PIECE_INDEX[(piece.colour, piece.name)]
    engine.current_hash ^= ZOBRIST_PIECES[piece_idx][initial.row * 8 + initial.col]

    target = board.squares[final.row][final.col].piece
    if isinstance(piece, Pawn) and target is None and final.col != initial.col:
        is_en_passant = True
        ep_row = initial.row
        captured_piece = board.squares[ep_row][final.col].piece
        captured_pos = (ep_row, final.col)
        board.squares[ep_row][final.col].piece = None
    elif target:
        captured_piece = target

    if captured_piece:
        cap_idx = PIECE_INDEX[(captured_piece.colour, captured_piece.name)]
        engine.current_hash ^= ZOBRIST_PIECES[cap_idx][captured_pos[0] * 8 + captured_pos[1]]
        if isinstance(captured_piece, Rook):
            if captured_piece.colour == 'white':
                if captured_pos == (7, 0):
                    engine.castling_rights &= ~2
                elif captured_pos == (7, 7):
                    engine.castling_rights &= ~1
            else:
                if captured_pos == (0, 0):
                    engine.castling_rights &= ~8
                elif captured_pos == (0, 7):
                    engine.castling_rights &= ~4

    board.squares[initial.row][initial.col].piece = None
    board.squares[final.row][final.col].piece = piece

    if isinstance(piece, King) and abs(final.col - initial.col) == 2:
        is_castle = True
        if final.col > initial.col:
            rook_from_col, rook_to_col = 7, 5
        else:
            rook_from_col, rook_to_col = 0, 3
        rook_piece = board.squares[initial.row][rook_from_col].piece
        rook_state = (rook_piece, rook_from_col, rook_to_col, rook_piece.moved)
        board.squares[initial.row][rook_from_col].piece = None
        board.squares[initial.row][rook_to_col].piece = rook_piece
        rook_piece.moved = True
        rook_idx = PIECE_INDEX[(rook_piece.colour, rook_piece.name)]
        engine.current_hash ^= ZOBRIST_PIECES[rook_idx][initial.row * 8 + rook_from_col]
        engine.current_hash ^= ZOBRIST_PIECES[rook_idx][initial.row * 8 + rook_to_col]
        if piece.colour == 'white':
            engine.castling_rights &= ~(1 | 2)
        else:
            engine.castling_rights &= ~(4 | 8)

    if promotion and isinstance(piece, Pawn) and (final.row == 0 or final.row == 7):
        promotion_piece = Queen(piece.colour)
        board.squares[final.row][final.col].piece = promotion_piece
        promo_idx = PIECE_INDEX[(promotion_piece.colour, promotion_piece.name)]
        engine.current_hash ^= ZOBRIST_PIECES[piece_idx][final.row * 8 + final.col]
        engine.current_hash ^= ZOBRIST_PIECES[promo_idx][final.row * 8 + final.col]
    else:
        engine.current_hash ^= ZOBRIST_PIECES[piece_idx][final.row * 8 + final.col]

    prev_ep_flags = []
    for r in range(ROWS):
        for c in range(COLS):
            p = board.squares[r][c].piece
            if isinstance(p, Pawn) and p.en_passant:
                prev_ep_flags.append((r, c))
    clear_en_passant(board)
    if prev_ep is not None:
        engine.current_hash ^= ZOBRIST_EP[prev_ep]
    engine.ep_file = None
    if isinstance(piece, Pawn) and abs(final.row - initial.row) == 2:
        piece.en_passant = True
        engine.ep_file = final.col
        engine.current_hash ^= ZOBRIST_EP[engine.ep_file]

    piece.moved = True
    if isinstance(piece, King):
        engine.king_pos[piece.colour] = (final.row, final.col)
        if piece.colour == 'white':
            engine.castling_rights &= ~(1 | 2)
        else:
            engine.castling_rights &= ~(4 | 8)
    if isinstance(piece, Rook):
        if piece.colour == 'white':
            if initial.row == 7 and initial.col == 0:
                engine.castling_rights &= ~2
            elif initial.row == 7 and initial.col == 7:
                engine.castling_rights &= ~1
        else:
            if initial.row == 0 and initial.col == 0:
                engine.castling_rights &= ~8
            elif initial.row == 0 and initial.col == 7:
                engine.castling_rights &= ~4

    engine.current_hash ^= ZOBRIST_CASTLING[prev_castling]
    engine.current_hash ^= ZOBRIST_CASTLING[engine.castling_rights]

    board.last_move = move
    engine.current_hash ^= ZOBRIST_SIDE

    undo = {
        'captured': captured_piece,
        'captured_pos': captured_pos,
        'is_en_passant': is_en_passant,
        'is_castle': is_castle,
        'rook_state': rook_state,
        'promotion_piece': promotion_piece,
        'piece': piece,
        'piece_moved_prev': piece_moved_prev,
        'prev_ep': prev_ep_flags,
        'prev_ep_file': prev_ep,
        'prev_castling': prev_castling,
        'prev_last': prev_last,
        'prev_hash': prev_hash,
    }
    return undo, engine.current_hash


def undo_move(board, move, undo):
    initial = move.initial
    final = move.final
    piece = undo['piece']

    engine.current_hash = undo['prev_hash']

    board.squares[initial.row][initial.col].piece = piece
    board.squares[final.row][final.col].piece = None

    piece.moved = undo['piece_moved_prev']

    if undo['promotion_piece']:
        board.squares[initial.row][initial.col].piece = Pawn(piece.colour)
        board.squares[initial.row][initial.col].piece.moved = undo['piece_moved_prev']

    if undo['captured']:
        r, c = undo['captured_pos']
        board.squares[r][c].piece = undo['captured']

    if undo['is_castle'] and undo['rook_state']:
        rook_piece, rook_from_col, rook_to_col, rook_moved_prev = undo['rook_state']
        board.squares[initial.row][rook_from_col].piece = rook_piece
        board.squares[initial.row][rook_to_col].piece = None
        rook_piece.moved = rook_moved_prev

    if isinstance(piece, King):
        engine.king_pos[piece.colour] = (initial.row, initial.col)

    clear_en_passant(board)
    engine.ep_file = undo['prev_ep_file']

    for r, c in undo['prev_ep']:
        p = board.squares[r][c].piece
        if isinstance(p, Pawn):
            p.en_passant = True

    engine.castling_rights = undo['prev_castling']

    board.last_move = undo['prev_last']

# ---------------------------------------------------------------------------
# Move ordering helpers
# ---------------------------------------------------------------------------

def mvv_lva(board, move):
    target = board.squares[move.final.row][move.final.col].piece
    if target is None:
        return 0
    victim = PIECE_VALUES[target.name]
    attacker_piece = board.squares[move.initial.row][move.initial.col].piece
    attacker = PIECE_VALUES[attacker_piece.name]
    return victim * 10 - attacker


def static_exchange_ok(board, move):
    target = board.squares[move.final.row][move.final.col].piece
    if target is None:
        return True
    attacker_piece = board.squares[move.initial.row][move.initial.col].piece
    attacker = PIECE_VALUES[attacker_piece.name]
    victim = PIECE_VALUES[target.name]
    return victim >= attacker - 50


def order_moves(board, moves, tt_move, ply):
    ordered = []
    k1, k2 = engine.killers[ply]
    for move, promo in moves:
        key = encode_move(move, promo)
        score = 0
        if tt_move and key == tt_move:
            score = 1_000_000_000
        else:
            if board.squares[move.final.row][move.final.col].piece:
                score = 500_000 + mvv_lva(board, move)
            elif key == k1:
                score = 300_000
            elif key == k2:
                score = 250_000
            else:
                score = engine.history.get(key, 0)
        ordered.append((score, move, promo))
    ordered.sort(key=lambda x: x[0], reverse=True)
    return [(m, p) for _, m, p in ordered]

# ---------------------------------------------------------------------------
# Quiescence search
# ---------------------------------------------------------------------------

def quiescence(board, alpha, beta, colour, ply):
    if engine.time_limit and (time.time() - engine.start_time) >= engine.time_limit:
        raise TimeoutError
    if ply >= Q_DEPTH_LIMIT:
        return alpha

    engine.nodes += 1
    stand_pat = evaluate(board) * (1 if colour == 'white' else -1)
    if stand_pat >= beta:
        engine.cutoffs += 1
        return beta
    if alpha < stand_pat:
        alpha = stand_pat

    captures = []
    enemy = 'black' if colour == 'white' else 'white'
    for move, promo in generate_pseudo_moves(board, colour):
        target = board.squares[move.final.row][move.final.col].piece
        is_capture = target is not None
        if not is_capture:
            if isinstance(board.squares[move.initial.row][move.initial.col].piece, Pawn) and move.initial.col != move.final.col:
                side_piece = board.squares[move.initial.row][move.final.col].piece
                if side_piece and isinstance(side_piece, Pawn) and side_piece.colour != colour and side_piece.en_passant:
                    is_capture = True
        if is_capture:
            if not static_exchange_ok(board, move):
                continue
            captures.append((move, promo))
        else:
            undo_chk, new_hash_chk = make_move(board, move, promo, colour)
            engine.current_hash = new_hash_chk
            gives_check = king_in_check(board, enemy)
            undo_move(board, move, undo_chk)
            engine.current_hash = undo_chk['prev_hash']
            if gives_check:
                captures.append((move, promo))

    for move, promo in captures:
        undo, new_hash = make_move(board, move, promo, colour)
        engine.current_hash = new_hash
        if engine.time_limit and (time.time() - engine.start_time) >= engine.time_limit:
            undo_move(board, move, undo)
            engine.current_hash = undo['prev_hash']
            raise TimeoutError
        score = -quiescence(board, -beta, -alpha, enemy, ply + 1)
        undo_move(board, move, undo)
        engine.current_hash = undo['prev_hash']

        if score >= beta:
            engine.cutoffs += 1
            return beta
        if score > alpha:
            alpha = score
    return alpha

# ---------------------------------------------------------------------------
# Negamax with alpha-beta and TT
# ---------------------------------------------------------------------------

def negamax(board, depth, alpha, beta, colour, ply):
    if engine.time_limit and (time.time() - engine.start_time) >= engine.time_limit:
        raise TimeoutError

    engine.nodes += 1
    orig_alpha = alpha

    tt_entry = engine.tt.get(engine.current_hash)
    tt_move_key = None
    if tt_entry and tt_entry['depth'] >= depth:
        engine.tt_hits += 1
        tt_move_key = tt_entry['move']
        flag = tt_entry['flag']
        tt_score = tt_entry['score']
        if flag == EXACT:
            return tt_score, tt_move_key
        elif flag == LOWERBOUND:
            alpha = max(alpha, tt_score)
        elif flag == UPPERBOUND:
            beta = min(beta, tt_score)
        if alpha >= beta:
            engine.cutoffs += 1
            return tt_score, tt_move_key
    elif tt_entry:
        tt_move_key = tt_entry['move']

    if depth == 0:
        return quiescence(board, alpha, beta, colour, ply), None

    legal_moves = generate_legal_moves(board, colour)
    if not legal_moves:
        if king_in_check(board, colour):
            return -INF + ply, None
        return 0, None

    ordered_moves = order_moves(board, legal_moves, tt_move_key, ply)

    best_move_key = None
    best_score = -INF

    for move, promo in ordered_moves:
        undo, new_hash = make_move(board, move, promo, colour)
        engine.current_hash = new_hash
        try:
            score, _ = negamax(board, depth - 1, -beta, -alpha, 'black' if colour == 'white' else 'white', ply + 1)
            score = -score
        except TimeoutError:
            undo_move(board, move, undo)
            engine.current_hash = undo['prev_hash']
            raise
        undo_move(board, move, undo)
        engine.current_hash = undo['prev_hash']

        if score > best_score:
            best_score = score
            best_move_key = encode_move(move, promo)
        if score > alpha:
            alpha = score
        if alpha >= beta:
            engine.cutoffs += 1
            if board.squares[move.final.row][move.final.col].piece is None:
                k1, k2 = engine.killers[ply]
                key = encode_move(move, promo)
                if k1 != key:
                    engine.killers[ply][1] = k1
                    engine.killers[ply][0] = key
                engine.history[key] = engine.history.get(key, 0) + depth * depth
            break

    flag = EXACT
    if best_score <= orig_alpha:
        flag = UPPERBOUND
    elif best_score >= beta:
        flag = LOWERBOUND

    engine.tt[engine.current_hash] = {
        'depth': depth,
        'score': best_score,
        'flag': flag,
        'move': best_move_key,
    }

    return best_score, best_move_key

# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

def decode_move(board, key):
    if key is None:
        return None
    r1, c1, r2, c2, promo = key
    move = Move(Square(r1, c1), Square(r2, c2))
    return move, promo


def get_best_move_optimized(board, depth=5, maximizing_player=True, time_limit=None, verbose=False):
    colour = 'black' if maximizing_player else 'white'
    start_hash = initial_hash(board)
    engine.reset(start_hash, time_limit=time_limit)
    engine.current_hash = start_hash
    if colour == 'black':
        engine.current_hash ^= ZOBRIST_SIDE

    best_move_key = None
    best_score = -INF
    prev_score = 0

    try:
        for d in range(1, depth + 1):
            window = 50
            alpha_w = prev_score - window if d > 1 else -INF
            beta_w = prev_score + window if d > 1 else INF
            widened = False
            while True:
                try:
                    score, mv_key = negamax(board, d, alpha_w, beta_w, colour, 0)
                except TimeoutError:
                    raise
                if score <= alpha_w and not widened:
                    alpha_w = -INF
                    beta_w = INF
                    widened = True
                    continue
                if score >= beta_w and not widened:
                    alpha_w = -INF
                    beta_w = INF
                    widened = True
                    continue
                break

            if mv_key:
                best_move_key = mv_key
                best_score = score
                prev_score = score
            if verbose:
                elapsed = time.time() - engine.start_time
                nps = engine.nodes / max(elapsed, 1e-3)
                hit_rate = engine.tt_hits / max(engine.nodes, 1) * 100
                print(f"Depth {d}: score {score:+} | nodes {engine.nodes} | nps {nps:,.0f} | tt {hit_rate:.1f}% | cut {engine.cutoffs}")
    except TimeoutError:
        if verbose:
            print("Search stopped on time limit")

    move = decode_move(board, best_move_key)
    if move is None:
        return None
    move_obj, promo = move
    piece = board.squares[move_obj.initial.row][move_obj.initial.col].piece
    return (piece, (move_obj.initial.row, move_obj.initial.col), move_obj)


def clear_transposition_table():
    engine.tt.clear()


def get_stats():
    elapsed = time.time() - engine.start_time if engine.start_time else 0
    return {
        'nodes': engine.nodes,
        'nps': engine.nodes / max(elapsed, 1e-3),
        'tt_hit_rate': engine.tt_hits / max(engine.nodes, 1),
        'cutoffs': engine.cutoffs,
        'time': elapsed,
    }
