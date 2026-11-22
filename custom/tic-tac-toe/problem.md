# Design a Tic-Tac-Toe Game

**Difficulty:** Medium

## Problem

Design an in-memory Tic-Tac-Toe game for two human players sharing an N x N board. One player uses X, the other uses O, and X always moves first.

The system must support creating a game, making moves, inspecting the board and game status, and reviewing move history. Multiple games must be able to exist independently.

Choose your own classes, methods, data structures, and error-reporting conventions.

## Expected behavior

- Each game starts with an empty board and alternates turns between X and O.
- A move identifies the player, row, and column. Coordinates are zero-based.
- A move is valid only when the game is in progress, the player owns the current turn, the coordinates are within the board, and the selected cell is empty.
- A player wins by occupying at least min(5, N) consecutive cells in a horizontal, vertical, or diagonal line. Both diagonal directions count, including lines that do not pass through a board corner. Gaps or the opponent's cells break a line; lines cannot wrap around board edges.
- Check for a win after every successful move. If the board becomes full without a winner, the game ends in a draw. A winning move on the final empty cell is a win, not a draw.
- Once a game ends, no further moves are allowed.
- Expose whether a game is in progress, won, or drawn. A won game identifies its winner; other states have no winner.
- Expose the next player only while the game is in progress. Finished games have no next player.
- Record every successful move in order, including its player and coordinates. Rejected moves must not appear in history.
- Invalid operations must not partially change state. A rejected move must leave the board, turn, status, winner, and history unchanged.
- Inspecting or modifying returned boards or history collections must not let callers change the game's internal state.
- Moves and queries on one game must not affect any other game.

## Example

For a 3 x 3 game:

| Move | Player | Row | Column | Result |
| --- | --- | --- | --- | --- |
| 1 | X | 0 | 0 | In progress; O moves next |
| 2 | O | 1 | 0 | In progress; X moves next |
| 3 | X | 0 | 1 | In progress; O moves next |
| 4 | O | 1 | 1 | In progress; X moves next |
| 5 | X | 0 | 2 | X wins |

Final board:

```text
X X X
O O .
. . .
```

An attempt by O to move after move 5 must be rejected without changing the game.

### Draw example

The following sequence fills a 3 x 3 board without a winner:

```text
X(0,0), O(0,1), X(0,2),
O(1,1), X(1,0), O(1,2),
X(2,1), O(2,0), X(2,2)
```

Final board:

```text
X O X
X O O
O X X
```

## Constraints

- The board size N is an integer from 3 to 100, chosen when creating a game and fixed afterward. Reject unsupported sizes.
- The only valid players are X and O.
- A game contains at most N squared successful moves.
- Reject out-of-range coordinates rather than wrapping or clipping them.
- An O(N) win check per move is acceptable. No particular internal representation is required.
- No AI opponent, user interface, networking, persistence, concurrency, undo, or restart is required.

## Suggested scenarios to verify

- X wins horizontally, O wins vertically, and wins in both diagonal directions are detected, including diagonals away from the board corners.
- A full board with no winner is a draw, while a last-cell winning move is still a win.
- An out-of-turn move, occupied cell, unknown player, or invalid coordinate is rejected without consuming a turn.
- A move after a win or draw is rejected.
- Boards of size 3 and 4 require respectively 3 and 4 consecutive matching cells; boards of size 5 or greater require 5, not a full row, column, or diagonal.
- A line shorter than min(5, N), or matching cells separated by gaps or the opponent's cells, does not win.
- Editing a returned board or history does not affect the game, and separate games remain independent.
