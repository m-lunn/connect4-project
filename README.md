# Connect Four with Alpha-Beta Pruning

A terminal Connect Four game against a minimax / alpha-beta engine, built to
make the effect of pruning and move ordering visible.

## Run

```bash
python -m connect4                              # defaults to play as X against alpha-beta, depth 6
python -m connect4 --depth 8 --first computer   # play with computer to make first move
python -m connect4 --algo minimax --depth 4     # play against plain minimax
python -m connect4 --position 4453              # start from a position (cols 1-7)
python -m connect4 --compare --depth 6          # node counts and runtimes: minimax vs alpha-beta variants
```

Options: `--depth N`, `--algo {minimax,alphabeta}`, `--order {left,center,random}`,
`--first {human,computer}`, `--position MOVES`, `--seed N`, `--compare`, `--no-color`.

## Tests

The key test is `tests/test_search_equivalence.py`: alpha-beta must return the
same root value as plain minimax on hundreds of random positions.

## Layout

| File | Contents |
| `connect4/board.py` | Board state, play/undo, win detection |
| `connect4/eval.py` | Window-based heuristic evaluation |
| `connect4/search.py` | Minimax (reference), negamax alpha-beta, move ordering, stats |
| `connect4/cli.py` | Game loop, `--compare`, argument parsing |
| `tests/` | Board rule tests and search-equivalence tests |

