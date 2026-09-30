"""Heuristic evaluation for non-terminal positions.

The board has 69 possible "windows": lines of four cells that could become a
win (24 horizontal, 21 vertical, 24 diagonal). Each window is scored on its
own, and the position's total score is just the sum over all 69 windows, plus
a small bonus for discs in the centre column.

A window scores 0 if it contains discs of both colours (dead: nobody can
complete it anymore) or if it's entirely empty. Otherwise it scores in favour
of whichever player has discs in it, and MORE STRONGLY for more discs, since
a live three-in-a-row is far more dangerous than a live one (see
WINDOW_VALUE below).

The result is ZERO-SUM and SYMMETRIC: evaluate_p1(b) == -evaluate_p1(b with
colours swapped). Both search algorithms rely on this — minimax always scores
from a fixed Player 1 viewpoint, while negamax alpha-beta scores from
whichever player is to move, and the two conventions only agree because of
this symmetry (see tests/test_board.py::test_evaluation_is_zero_sum_symmetric).
"""

from __future__ import annotations

from .board import CENTER, HEIGHT, P1, P2, WIDTH, Board

# WINDOW_VALUE[k] = how much a window is worth when it holds k discs of one
# player and is otherwise empty. Deliberately non-linear: a live three (25)
# is worth far more than five live ones (5 x 1), because a three is one move
# from winning.
WINDOW_VALUE = (0, 1, 5, 25)

# Flat bonus per disc in the centre column, on top of the window score.
# Centre cells already score higher just from being part of more windows
# (see WINDOWS below); this reinforces that effect rather than creating it.
CENTER_BONUS = 3

# The four directions a line of four can run in: right, up, and the two
# diagonals. Each is walked once from every starting cell; a line running the
# opposite way (e.g. left, or down) is the same window found from its other end.
_LINE_DIRECTIONS = (
    (1, 0),   # horizontal
    (0, 1),   # vertical
    (1, 1),   # diagonal, bottom-left to top-right
    (1, -1),  # diagonal, top-left to bottom-right
)


def _all_windows() -> list[tuple[int, int, int, int]]:
    """Every possible 4-in-a-row window, as 4-tuples of flat cell indices.

    Walks every (row, col) starting cell and every direction, keeping the
    ones that stay on the board. There are 69 of these in total on a
    standard 7x6 board.
    """
    windows = []
    for start_row in range(HEIGHT):
        for start_col in range(WIDTH):
            for d_col, d_row in _LINE_DIRECTIONS:
                end_col = start_col + 3 * d_col
                end_row = start_row + 3 * d_row
                if not (0 <= end_col < WIDTH and 0 <= end_row < HEIGHT):
                    continue  # this line would run off the board
                windows.append(tuple(
                    (start_row + step * d_row) * WIDTH + (start_col + step * d_col)
                    for step in range(4)
                ))
    return windows


WINDOWS = _all_windows()


def _score_window(cells: list[int], window: tuple[int, int, int, int]) -> int:
    """Score one window: positive favours P1, negative favours P2, 0 if dead."""
    p1_discs = sum(1 for i in window if cells[i] == P1)
    p2_discs = sum(1 for i in window if cells[i] == P2)
    if p1_discs and p2_discs:
        return 0  # both colours present: nobody can complete this line
    return WINDOW_VALUE[p1_discs] - WINDOW_VALUE[p2_discs]


def _center_column_bonus(cells: list[int]) -> int:
    """Flat bonus for each disc sitting in the centre column."""
    bonus = 0
    for row in range(HEIGHT):
        disc = cells[row * WIDTH + CENTER]
        if disc == P1:
            bonus += CENTER_BONUS
        elif disc == P2:
            bonus -= CENTER_BONUS
    return bonus


def evaluate_p1(board: Board) -> int:
    """Score a position from Player 1's point of view (positive = good for P1).

    Raises ValueError if called on a won position. Terminal states are
    search.py's responsibility, not this function's: a won board contains a
    window with 4 discs of one colour, which WINDOW_VALUE has no entry for,
    so this fails loudly rather than silently returning a meaningless number.
    """
    if board.last_move_won():
        raise ValueError(
            "evaluate() called on a won position; terminal states belong to search"
        )
    window_score = sum(_score_window(board.cells, w) for w in WINDOWS)
    return window_score + _center_column_bonus(board.cells)


def evaluate(board: Board, player: int) -> int:
    """Score a position from `player`'s point of view."""
    score_for_p1 = evaluate_p1(board)
    return score_for_p1 if player == P1 else -score_for_p1
