"""Command-line interface: play against the engine, or compare search variants."""

from __future__ import annotations

import argparse
import os
import sys

from .board import HEIGHT, P1, P2, WIDTH, Board
from .search import ALGORITHMS, ORDERINGS, Searcher, describe_value


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="python -m connect4",
        description="Play Connect Four against a minimax / alpha-beta engine.",
    )
    p.add_argument("-d", "--depth", type=int, default=6,
                   help="search depth in plies (default: 6)")
    p.add_argument("--algo", choices=ALGORITHMS, default="alphabeta",
                   help="search algorithm (default: alphabeta)")
    p.add_argument("--order", choices=ORDERINGS, default="center",
                   help="move ordering used by alpha-beta (default: center)")
    p.add_argument("--first", choices=("human", "computer"), default="human",
                   help="who plays X and moves first (default: human)")
    p.add_argument("--position", default="", metavar="MOVES",
                   help="start from a move string of columns 1-7, e.g. 4453")
    p.add_argument("--seed", type=int, default=0,
                   help="seed for --order random (default: 0)")
    p.add_argument("--compare", action="store_true",
                   help="don't play: search the starting position with several "
                        "variants and print node counts")
    p.add_argument("--no-color", action="store_true", help="disable ANSI colours")
    return p


# --------------------------------------------------------------------- compare

def compare(board: Board, depth: int, seed: int) -> None:
    configs = [("minimax", "left"), ("alphabeta", "left"),
               ("alphabeta", "random"), ("alphabeta", "center")]
    print(board)
    print(f"\nSearching to depth {depth} ({board.to_move == P1 and 'X' or 'O'} to move)\n")
    print(f"{'algorithm':<10} {'order':<7} {'value':>14} {'nodes':>12} {'cutoffs':>10} {'time (s)':>9} {'vs minimax':>11}")
    baseline = None
    values = set()
    for algo, order in configs:
        result = Searcher(algo, order, seed).search(board, depth)
        s = result.stats
        if baseline is None:
            baseline = s.nodes
        values.add(result.value)
        print(f"{algo:<10} {order:<7} {describe_value(result.value):>14} {s.nodes:>12,} "
              f"{s.cutoffs:>10,} {s.elapsed:>9.2f} {baseline / s.nodes:>10.1f}x")
    print("\nAll variants agree on the root value." if len(values) == 1
          else "\n!! Variants DISAGREE on the root value: there is a bug.")


# ------------------------------------------------------------------ game loop

def _prompt_human(board: Board, human: int) -> str | int:
    """Returns a 0-indexed column, or 'q' / 'u'."""
    while True:
        try:
            raw = input(f"Your move (1-{WIDTH}, u = undo, q = quit): ").strip().lower()
        except EOFError:
            return "q"
        if raw in ("q", "u"):
            return raw
        if raw.isdigit() and board.can_play(int(raw) - 1):
            return int(raw) - 1
        print("  Not a playable column, try again.")


def play_game(board: Board, human: int, searcher: Searcher, depth: int, color: bool) -> None:
    while not board.is_over():
        print()
        print(board.render(color))
        if board.to_move == human:
            choice = _prompt_human(board, human)
            if choice == "q":
                print("Goodbye.")
                return
            if choice == "u":
                if len(board.moves) >= 2:
                    board.undo()
                    board.undo()
                else:
                    print("  Nothing to undo.")
                continue
            board.play(choice)
        else:
            result = searcher.search(board, depth)
            s = result.stats
            board.play(result.move)
            print(f"\nComputer plays column {result.move + 1}  "
                  f"[eval {describe_value(result.value)}; {s.nodes:,} nodes, "
                  f"{s.cutoffs:,} cutoffs, {s.elapsed:.2f}s]")

    print()
    print(board.render(color))
    if board.last_move_won():
        just_moved = P2 if board.to_move == P1 else P1
        print("\nYou win!" if just_moved == human else "\nComputer wins.")
    else:
        print("\nDraw.")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.depth < 1:
        print("error: --depth must be at least 1", file=sys.stderr)
        return 2
    try:
        board = Board.from_moves(args.position)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2

    if args.compare:
        if board.is_over():
            print("error: that position is already finished", file=sys.stderr)
            return 2
        compare(board, args.depth, args.seed)
        return 0

    color = sys.stdout.isatty() and not args.no_color and "NO_COLOR" not in os.environ
    human = P1 if args.first == "human" else P2
    searcher = Searcher(args.algo, args.order, args.seed)
    print(f"You are {'X' if human == P1 else 'O'}. Engine: {args.algo}, "
          f"order={args.order}, depth={args.depth}.")
    play_game(board, human, searcher, args.depth, color)
    return 0
