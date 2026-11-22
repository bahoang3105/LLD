from enum import Enum
from typing import List
from dataclasses import dataclass 

class GameStatus(Enum):
    PLAYING = 1
    DRAW = 2
    HAS_WINNER = 3

@dataclass(frozen=True)
class Move:
    _row: int
    _col: int
    _player: str

class Board:
    MAX_CONSECUTIVE_CELLS_WIN = 5
    def __init__(self, game_id: int, size: int):
        self.game_id = game_id
        self.size = size
        self.board = [[""] * size for _ in range(size)]
        self.moves = []

    def move(self, player: str, row: int, col: int):
        if row < 0 \
            or row >= self.size \
            or col < 0 \
            or col >= self.size \
            or self.board[row][col] != "":
            return False
        self.board[row][col] = player
        move = Move(row, col, player)
        self.moves.append(move)
        return True
        
    def inspect(self) -> List[List[str]]:
        return [row[:] for row in self.board]

    def review_history(self) -> List[Move]:
        return self.moves[:]

    def check_status(self) -> GameStatus:
        # Check row
        for row in self.board:
            if self._has_winner(row):
                return GameStatus.HAS_WINNER

        # Check col
        for i in range(self.size):
            col = [row[i] for row in self.board]
            if self._has_winner(col):
                return GameStatus.HAS_WINNER

        # Check left diagonal
        starting_row, starting_col = self.size - 1, 0
        while starting_col < self.size:
            line = []
            cur_row, cur_col = starting_row, starting_col
            while cur_col < self.size and cur_row < self.size:
                line.append(self.board[cur_row][cur_col])
                cur_row += 1
                cur_col += 1
            if self._has_winner(line):
                return GameStatus.HAS_WINNER
            if starting_row > 0:
                starting_row -= 1
            else:
                starting_col += 1

        # Check right diagonal
        starting_row, starting_col = 0, 0
        while starting_row < self.size:
            line = []
            cur_row, cur_col = starting_row, starting_col
            while cur_row < self.size and cur_col >= 0:
                line.append(self.board[cur_row][cur_col])
                cur_row += 1
                cur_col -= 1
            if self._has_winner(line):
                return GameStatus.HAS_WINNER
            if starting_col < self.size - 1:
                starting_col += 1
            else:
                starting_row += 1

        if len(self.moves) == self.size ** 2:
            return GameStatus.DRAW
        return GameStatus.PLAYING

    def _has_winner(self, line: List[str]) -> bool:
        cur = ""
        count = 0
        for cell in line:
            if cell == "":
                count = 0
            else:
                count = count + 1 if cell == cur else 1
            cur = cell
            if count >= min(self.size, self.MAX_CONSECUTIVE_CELLS_WIN):
                return True
        return False
                
class Game:
    def __init__(self, id: int, size: int):
        self.id = id
        self.cur_player = "X"
        self.board = Board(id, size)
        self.status = GameStatus.PLAYING
        self.winner = None

    def move(self, player: str, row: int, col: int):
        if player != self.cur_player or self.status != GameStatus.PLAYING:
            return False
        if not self.board.move(player, row, col):
            return False
        self.cur_player = "X" if self.cur_player == "O" else "O"
        self.status = self.board.check_status()
        if self.status != GameStatus.PLAYING:
            self.cur_player = None
        if self.status == GameStatus.HAS_WINNER:
            self.winner = player
        return True 

    def inspect_board(self) -> List[List[str]]:
        return self.board.inspect()

    def inspect_status(self) -> GameStatus:
        return (self.status, self.winner)

    def review_history(self) -> List[Move]:
        return self.board.review_history()


class GameSystem:
    MIN_BOARD_SIZE = 3
    MAX_BOARD_SIZE = 100

    def __init__(self):
        self.games: List[Game] = []

    def create_game(self, size: int) -> int:
        if not self.MIN_BOARD_SIZE <= size <= self.MAX_BOARD_SIZE:
            return -1
        game = Game(len(self.games), size)
        self.games.append(game)
        return game.id

    def move(self, game_id: int, player: str, row: int, col: int) -> bool:
        game = self._get_game(game_id)
        if game is None:
            return False
        return game.move(player, row, col)

    def inspect_board(self, game_id: int) -> List[List[str]]:
        game = self._get_game(game_id)
        if game is None:
            return []
        return game.inspect_board()
    
    def inspect_status(self, game_id: int) -> tuple[GameStatus, str]:
        game = self._get_game(game_id)
        if game is None:
            return []
        return game.inspect_status()

    def review_history(self, game_id: int) -> List[Move]:
        game = self._get_game(game_id)
        if game is None:
            return []
        return game.review_history()

    def _get_game(self, game_id: int) -> Game | None:
        if game_id < 0 or game_id >= len(self.games):
            return None
        return self.games[game_id]


# gs = GameSystem()
# print(gs.create_game(3))
# print(gs.move(0, "X", 0, 0))
# print(gs.move(0, "O", 1, 1))
# print(gs.move(0, "X", 1, 0))
# print(gs.inspect_board(0))
# print(gs.inspect_status(0))
# print(gs.review_history(0))
# print(gs.move(0, "X", 2, 0))
# print(gs.move(0, "O", 1, 0))
# print(gs.move(0, "O", 1, 2))
# print(gs.move(0, "X", 2, 0))
# print(gs.inspect_board(0))
# print(gs.inspect_status(0))
# print(gs.review_history(0))
# print(gs.move(0, "X", 2, 0))