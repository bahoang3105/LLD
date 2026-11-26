from dataclasses import dataclass
from enum import Enum


class DiscColor(Enum):
    RED = "R"
    YELLOW = "Y"


class GameState(Enum):
    DRAW = 1
    PLAYING = 2
    HAS_WINNER = 3


@dataclass(frozen=True)
class Player:
    discColor: DiscColor


class Board:
    ROWS = 6
    COLS = 7

    def __init__(self):
        self.grid = [[""] * self.COLS for _ in range(self.ROWS)]

    def place_disc(self, column: int, disc_color: DiscColor):
        if type(column) is not int or not 0 <= column < self.COLS:
            return None

        for row in range(self.ROWS - 1, -1, -1):
            if self.grid[row][column] == "":
                self.grid[row][column] = disc_color.value
                return row

        return None

    def is_full(self) -> bool:
        return all(cell != "" for cell in self.grid[0])

    def check(self, row: int, col: int) -> bool:
        disc = self.grid[row][col]
        if disc == "":
            return False

        for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
            count = 1

            for direction in (1, -1):
                i = row + dr * direction
                j = col + dc * direction

                while (
                    0 <= i < self.ROWS
                    and 0 <= j < self.COLS
                    and self.grid[i][j] == disc
                ):
                    count += 1
                    i += dr * direction
                    j += dc * direction

            if count >= 4:
                return True

        return False

    def get_grid(self):
        # Return a copy so callers cannot change the board through this result.
        return [row[:] for row in self.grid]


class Game:
    def __init__(self, player1: Player, player2: Player):
        if player1.discColor == player2.discColor:
            raise ValueError("Players must have different disc colors.")

        self.player1 = player1
        self.player2 = player2
        self.currentPlayer = player1
        self.board = Board()
        self.state = GameState.PLAYING
        self.winner = None

    def move(self, player: Player, column: int) -> bool:
        if self.state != GameState.PLAYING:
            return False

        if player is not self.currentPlayer:
            return False

        row = self.board.place_disc(column, player.discColor)
        if row is None:
            return False

        if self.board.check(row, column):
            self.state = GameState.HAS_WINNER
            self.winner = player
        elif self.board.is_full():
            self.state = GameState.DRAW
        else:
            self.currentPlayer = (
                self.player2 if player is self.player1 else self.player1
            )

        return True

    def get_state(self) -> GameState:
        return self.state

    def get_board(self):
        return self.board.get_grid()