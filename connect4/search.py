"""Game-tree search: plain minimax (reference) and alpha-beta (negamax form).

Two deliberately DIFFERENT code paths so that one can act as a correctness
check on the other:

_minimax    classic max/min, always scores from PLAYER 1's viewpoint.
_alphabeta  negamax + alpha-beta, always scores from the SIDE TO MOVE's
                viewpoint.

If both agree on the root value across many random positions, a sign error or
a bad cutoff in either is very unlikely (tested in tests/test_search_equivalence.py).

depth   number of plies still to look ahead. depth == 0 -> use the heuristic.
ply     plies from the root; used so that faster wins score higher than slower
        wins (WIN_SCORE - ply) and slower losses score higher than faster ones.
"""

import random
from dataclasses import dataclass, field
from time import perf_counter

from .board import CENTER, HEIGHT, P1, P2, WIDTH, Board
from .eval import evaluate

WIN_SCORE = 100000          # must exceed any heuristic score + max ply
INF = 10**9

ALGORITHMS = ("minimax", "alphabeta")
ORDERINGS = ("left", "center", "random")

# Columns sorted by distance from the centre: 3, 2, 4, 1, 5, 0, 6
CENTER_ORDER = sorted(range(WIDTH), key=lambda c: abs(c - CENTER))


@dataclass
class Stats:
    nodes: int = 0       # positions visited (including the root)
    cutoffs: int = 0     # times alpha >= beta caused a loop to stop early
    elapsed: float = 0.0 # seconds


@dataclass
class SearchResult:
    move: int            # 0-indexed column
    value: int           # from the point of view of the player to move at the root
    depth: int
    stats: Stats = field(default_factory=Stats)


def describe_value(value: int) -> str:
    """Human-readable version of a root value."""
    if abs(value) > WIN_SCORE - 100:
        plies = WIN_SCORE - abs(value)
        moves = (plies + 1) // 2
        who = "win" if value > 0 else "loss"
        return f"forced {who} in {moves}"
    return f"{value:+d}"


class Searcher:
    def __init__(self, algorithm: str = "alphabeta", ordering: str = "center", seed: int = 0):
        if algorithm not in ALGORITHMS:
            raise ValueError(f"algorithm must be one of {ALGORITHMS}")
        if ordering not in ORDERINGS:
            raise ValueError(f"ordering must be one of {ORDERINGS}")
        self.algorithm = algorithm
        self.ordering = ordering
        self.rng = random.Random(seed)
        self.stats = Stats()

    # ------------------------------------------------------------------ root

    def search(self, board: Board, depth: int) -> SearchResult:
        if depth < 1:
            raise ValueError("depth must be at least 1")
        if board.is_over():
            raise ValueError("cannot search a finished game")

        self.stats = Stats(nodes=1)  # count the root
        start = perf_counter()

        best_move, best_value = -1, -INF
        for col in self._ordered_moves(board):
            board.play(col)
            value = self._child_value(board, depth - 1, alpha=best_value)
            board.undo()
            if value > best_value:
                best_move, best_value = col, value

        self.stats.elapsed = perf_counter() - start
        return SearchResult(best_move, best_value, depth, self.stats)

    def _child_value(self, board: Board, depth: int, alpha: int) -> int:
        if self.algorithm == "alphabeta":
            # Root window is (alpha, +INF); the child sees it negated and swapped.
            return -self._alphabeta(board, depth, -INF, -alpha, ply=1)
        # Minimax returns a P1-viewpoint value; convert to the mover's viewpoint.
        v = self._minimax(board, depth, ply=1)
        just_moved = P2 if board.to_move == P1 else P1
        return v if just_moved == P1 else -v

    # --------------------------------------------------------- move ordering

    def _ordered_moves(self, board: Board) -> list[int]:
        if self.ordering == "center":
            return [c for c in CENTER_ORDER if board.heights[c] < HEIGHT]
        moves = board.legal_moves()  # left-to-right
        if self.ordering == "random":
            self.rng.shuffle(moves)
        return moves

    # --------------------------------------------------- plain minimax

    def _minimax(self, board: Board, depth: int, ply: int) -> int:
        """Classic minimax. Returns the value from PLAYER 1's viewpoint."""
        self.stats.nodes += 1

        if board.last_move_won():
            just_moved = P2 if board.to_move == P1 else P1
            return (WIN_SCORE - ply) if just_moved == P1 else -(WIN_SCORE - ply)
        if board.is_full():
            return 0
        if depth == 0:
            return evaluate(board, P1)

        maximizing = board.to_move == P1
        best = -INF if maximizing else INF
        for col in board.legal_moves():
            board.play(col)
            v = self._minimax(board, depth - 1, ply + 1)
            board.undo()
            best = max(best, v) if maximizing else min(best, v)
        return best

    # --------------------------------------------------- negamax alpha-beta

    def _alphabeta(self, board: Board, depth: int, alpha: int, beta: int, ply: int) -> int:
        """Negamax with alpha-beta pruning (fail-soft).
        
        Returns the value from the viewpoint of the SIDE TO MOVE at `board`.
        * if alpha < v < beta   -> the return value is exactly v
        * if v <= alpha         -> the return value is an upper bound on v (<= alpha)
        * if v >= beta          -> the return value is a lower bound on v (>= beta)
        """
        self.stats.nodes += 1

        if board.last_move_won():
            # The player who just moved has won, so the side to move has lost.
            return -(WIN_SCORE - ply)
        if board.is_full():
            return 0
        if depth == 0:
            return evaluate(board, board.to_move)

        best = -INF
        for col in self._ordered_moves(board):
            board.play(col)
            # The child's window is ours negated and swapped.
            score = -self._alphabeta(board, depth - 1, -beta, -alpha, ply + 1)
            board.undo()

            if score > best:
                best = score
            if best > alpha:
                alpha = best
            if alpha >= beta:
                self.stats.cutoffs += 1
                break
        return best
