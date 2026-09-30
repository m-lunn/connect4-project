"""Correctness oracle: alpha-beta must give the same root value as plain minimax.

Minimax and alpha-beta are separate code paths (different viewpoint
conventions), so agreement across many random positions is strong evidence
that both are right. We compare root VALUES. Best moves can legitimately
differ between orderings when several moves tie.
"""

import random

import pytest

from connect4.board import Board
from connect4.search import ORDERINGS, Searcher


def random_position(rng, n_moves):
    """Play up to n_moves random legal moves; stop early if the game ends."""
    b = Board()
    for _ in range(n_moves):
        if b.is_over():
            break
        b.play(rng.choice(b.legal_moves()))
    return b


def positions(n, seed=12345, max_moves=30):
    rng = random.Random(seed)
    out = []
    while len(out) < n:
        b = random_position(rng, rng.randint(0, max_moves))
        if not b.is_over():
            out.append(b)
    return out


@pytest.mark.parametrize("ordering", ORDERINGS)
@pytest.mark.parametrize("depth", [1, 2, 3, 4])
def test_alphabeta_matches_minimax(depth, ordering):
    for b in positions(40):
        ref = Searcher("minimax").search(b, depth)
        ab = Searcher("alphabeta", ordering, seed=7).search(b, depth)
        assert ab.value == ref.value, f"moves={[m + 1 for m in b.moves]}"
        # Alpha-beta may never look at MORE nodes than minimax:
        assert ab.stats.nodes <= ref.stats.nodes


def test_search_leaves_board_untouched():
    for b in positions(10):
        before = (list(b.cells), list(b.heights), list(b.moves))
        Searcher("alphabeta").search(b, 4)
        assert (b.cells, b.heights, b.moves) == before


def test_same_ordering_gives_same_move_as_minimax():
    # Root ties are broken by "first in ordering wins" in both algorithms, so
    # with the SAME ordering the chosen move should match too. (Minimax ignores
    # ordering inside the tree but the root loop uses it.)
    for b in positions(30, seed=99):
        ref = Searcher("minimax", "center").search(b, 3)
        ab = Searcher("alphabeta", "center").search(b, 3)
        assert ab.move == ref.move


@pytest.mark.parametrize("ordering", ORDERINGS)
@pytest.mark.parametrize("depth", [2, 3, 4])
def test_takes_immediate_win(depth, ordering):
    b = Board.from_moves("112233")  # X has 3 on the bottom row; column 4 wins
    assert Searcher("alphabeta", ordering).search(b, depth).move == 3


@pytest.mark.parametrize("ordering", ORDERINGS)
@pytest.mark.parametrize("depth", [2, 3, 4])
def test_blocks_immediate_loss(depth, ordering):
    b = Board.from_moves("11223")  # X threatens column 4; O must block it
    assert Searcher("alphabeta", ordering).search(b, depth).move == 3


def test_prefers_faster_win():
    # X can win at once via column 4; it must report a win in 1 move.
    b = Board.from_moves("112233")
    r = Searcher("alphabeta").search(b, 4)
    from connect4.search import WIN_SCORE
    assert r.value == WIN_SCORE - 1
