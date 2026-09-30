"""Connect Four board: state, legal moves, play/undo, win detection.

Representation (deliberately simple; a bitboard version comes later):

    cells[row * WIDTH + col]   with row 0 = BOTTOM row, col 0 = leftmost column
    heights[col]               number of discs currently in that column
    moves                      stack of columns played (0-indexed), used for undo

Players are P1 (plays first, drawn as X) and P2 (drawn as O).
"""

from __future__ import annotations

WIDTH = 7
HEIGHT = 6
CENTER = WIDTH // 2

EMPTY, P1, P2 = 0, 1, 2

# (d_col, d_row) for the four line directions; each is checked both ways.
_DIRECTIONS = ((1, 0), (0, 1), (1, 1), (1, -1))


class Board:
    def __init__(self) -> None:
        self.cells = [EMPTY] * (WIDTH * HEIGHT)
        self.heights = [0] * WIDTH
        self.moves: list[int] = []
        # _won[i] is True iff move i completed four in a row. Computed once in
        # play() so the search can ask "did the last move win?" in O(1).
        self._won: list[bool] = []

    # ---- construction helpers -------------------------------------------

    @classmethod
    def from_moves(cls, move_string: str) -> "Board":
        """Build a position from a string of 1-indexed columns, e.g. '4453'."""
        board = cls()
        for ch in move_string.strip():
            if not ch.isdigit() or not 1 <= int(ch) <= WIDTH:
                raise ValueError(f"bad move character {ch!r}; use digits 1-{WIDTH}")
            board.play(int(ch) - 1)
        return board

    # ---- queries ---------------------------------------------------------

    @property
    def to_move(self) -> int:
        return P1 if len(self.moves) % 2 == 0 else P2

    def can_play(self, col: int) -> bool:
        return 0 <= col < WIDTH and self.heights[col] < HEIGHT

    def legal_moves(self) -> list[int]:
        return [c for c in range(WIDTH) if self.heights[c] < HEIGHT]

    def last_move_won(self) -> bool:
        """True iff the player who just moved has four in a row."""
        return bool(self._won) and self._won[-1]

    def is_full(self) -> bool:
        return len(self.moves) == WIDTH * HEIGHT

    def is_over(self) -> bool:
        return self.last_move_won() or self.is_full()

    # ---- mutation --------------------------------------------------------

    def play(self, col: int) -> None:
        if self.last_move_won():
            raise ValueError("game is already over")
        if not self.can_play(col):
            raise ValueError(f"column {col + 1} is not playable")
        player = self.to_move
        row = self.heights[col]
        self.cells[row * WIDTH + col] = player
        self.heights[col] += 1
        self.moves.append(col)
        self._won.append(self._makes_four(col, row, player))

    def undo(self) -> None:
        col = self.moves.pop()
        self.heights[col] -= 1
        self.cells[self.heights[col] * WIDTH + col] = EMPTY
        self._won.pop()

    # ---- win detection ---------------------------------------------------

    def _makes_four(self, col: int, row: int, player: int) -> bool:
        """Does the disc just placed at (col, row) complete a line of 4+?

        Only lines through the new disc can be newly completed, so we count
        outward from it in both directions along each axis.
        """
        cells = self.cells
        for dc, dr in _DIRECTIONS:
            count = 1
            for sign in (1, -1):
                c, r = col + sign * dc, row + sign * dr
                while 0 <= c < WIDTH and 0 <= r < HEIGHT and cells[r * WIDTH + c] == player:
                    count += 1
                    c += sign * dc
                    r += sign * dr
            if count >= 4:
                return True
        return False

    # ---- display ---------------------------------------------------------

    def render(self, color: bool = False) -> str:
        def sym(v: int) -> str:
            if v == EMPTY:
                return "."
            ch = "X" if v == P1 else "O"
            if color:
                return f"\033[{31 if v == P1 else 33}m{ch}\033[0m"
            return ch

        lines = []
        for row in range(HEIGHT - 1, -1, -1):
            lines.append("| " + " ".join(sym(self.cells[row * WIDTH + c]) for c in range(WIDTH)) + " |")
        lines.append("+" + "-" * (2 * WIDTH + 1) + "+")
        lines.append("  " + " ".join(str(c + 1) for c in range(WIDTH)))
        return "\n".join(lines)

    def __str__(self) -> str:
        return self.render()
