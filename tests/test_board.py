import pytest

from connect4.board import HEIGHT, P1, P2, WIDTH, Board
from connect4.eval import WINDOWS


def play_string(s):
    b = Board()
    for ch in s:
        b.play(int(ch) - 1)
    return b


def assert_wins_on_last_move(moves):
    """Nobody wins before the last move; the last move wins."""
    b = play_string(moves[:-1])
    assert not b.last_move_won()
    b.play(int(moves[-1]) - 1)
    assert b.last_move_won()


def test_horizontal_win():
    assert_wins_on_last_move("1122334")


def test_vertical_win():
    assert_wins_on_last_move("1212121")


def test_diagonal_up_right_win():
    assert_wins_on_last_move("1223733474644")


def test_diagonal_up_left_win():
    # mirror image of the previous position (column c -> 8 - c)
    assert_wins_on_last_move("7665155414244")


def test_three_in_a_row_is_not_a_win():
    b = play_string("112233")
    assert not b.last_move_won()


def test_no_wraparound_between_rows():
    # P1 gets cols 6,7 (idx 5,6) on row 0 and col 1 (idx 0) on row 1: not a line.
    b = play_string("6" "1" "7" "1" "1")
    assert not b.last_move_won()


def test_win_by_filling_the_middle_of_a_line():
    # P1 has cols 1,2,4 on the bottom row; playing 3 completes the line
    # in the MIDDLE, so the check must count in both directions.
    b = play_string("1" "1" "2" "2" "4" "4")
    assert not b.last_move_won()
    b.play(2)
    assert b.last_move_won()


def test_column_fills_up():
    b = Board()
    for _ in range(HEIGHT):
        b.play(0)
        if b.last_move_won():
            break
    # Alternating players in one column never wins, so it should be full:
    assert b.heights[0] == HEIGHT
    assert not b.can_play(0)
    with pytest.raises(ValueError):
        b.play(0)


def test_undo_restores_everything():
    b = play_string("4453")
    snapshot = (list(b.cells), list(b.heights), list(b.moves), b.to_move)
    b.play(2)
    b.undo()
    assert (b.cells, b.heights, b.moves, b.to_move) == snapshot


def test_cannot_play_after_game_over():
    b = play_string("1122334")
    with pytest.raises(ValueError):
        b.play(4)


def test_to_move_alternates():
    b = Board()
    assert b.to_move == P1
    b.play(3)
    assert b.to_move == P2


def test_from_moves():
    b = Board.from_moves("4453")
    assert b.moves == [3, 3, 4, 2]
    with pytest.raises(ValueError):
        Board.from_moves("48")


def test_window_count():
    # 24 horizontal + 21 vertical + 12 + 12 diagonal
    assert len(WINDOWS) == 69


def test_evaluate_rejects_won_position():
    from connect4.eval import evaluate
    b = play_string("1122334")
    assert b.last_move_won()
    with pytest.raises(ValueError):
        evaluate(b, P1)


def test_evaluation_is_zero_sum_symmetric():
    import random
    from connect4.eval import evaluate
    rng = random.Random(1)
    checked = 0
    while checked < 200:
        b = Board()
        for _ in range(rng.randint(0, 30)):
            if b.is_over():
                break
            b.play(rng.choice(b.legal_moves()))
        if b.last_move_won():
            continue
        assert evaluate(b, P1) == -evaluate(b, P2)
        checked += 1
