import unittest

from solution import GameStatus, GameSystem


class GameSystemTests(unittest.TestCase):
    def setUp(self):
        self.system = GameSystem()
        self.game_id = self.system.create_game(3)

    def history(self, game_id):
        return [
            (move._player, move._row, move._col)
            for move in self.system.review_history(game_id)
        ]

    def snapshot(self, game_id):
        return (
            self.system.inspect_board(game_id),
            self.system.inspect_status(game_id),
            self.history(game_id),
            self.system.games[game_id].cur_player,
        )

    def play(self, game_id, coordinates):
        for index, (row, col) in enumerate(coordinates):
            player = "X" if index % 2 == 0 else "O"
            self.assertTrue(
                self.system.move(game_id, player, row, col),
                (index, player, row, col),
            )

    def play_x_line(self, size, line):
        game_id = self.system.create_game(size)
        fillers = [
            (row, col)
            for row in range(size)
            for col in range(size)
            if (row, col) not in line
        ]
        for index, (row, col) in enumerate(line):
            self.assertTrue(self.system.move(game_id, "X", row, col))
            if index < len(line) - 1:
                self.assertEqual(
                    self.system.inspect_status(game_id), (GameStatus.PLAYING, None)
                )
                self.assertTrue(self.system.move(game_id, "O", *fillers[index]))
        self.assertEqual(
            self.system.inspect_status(game_id), (GameStatus.HAS_WINNER, "X")
        )

    def test_new_game_and_size_boundaries(self):
        for size in (3, 4, 5, 100):
            with self.subTest(size=size):
                game_id = self.system.create_game(size)
                self.assertEqual(
                    self.system.inspect_board(game_id),
                    [[""] * size for _ in range(size)],
                )
                self.assertEqual(
                    self.system.inspect_status(game_id), (GameStatus.PLAYING, None)
                )
                self.assertEqual(self.history(game_id), [])
                self.assertEqual(self.system.games[game_id].cur_player, "X")

    def test_invalid_sizes_do_not_create_games(self):
        count = len(self.system.games)
        for size in (-10, 0, 1, 2, 101):
            with self.subTest(size=size):
                self.assertEqual(self.system.create_game(size), -1)
                self.assertEqual(len(self.system.games), count)
        self.assertEqual(self.system.create_game(3), count)

    def test_turns_board_and_ordered_history(self):
        moves = [(2, 1), (0, 2), (1, 0)]
        self.play(self.game_id, moves)
        self.assertEqual(
            self.system.inspect_board(self.game_id),
            [["", "", "O"], ["X", "", ""], ["", "X", ""]],
        )
        self.assertEqual(
            self.history(self.game_id),
            [("X", 2, 1), ("O", 0, 2), ("X", 1, 0)],
        )
        self.assertEqual(self.system.games[self.game_id].cur_player, "O")

    def test_invalid_moves_are_atomic(self):
        self.assertTrue(self.system.move(self.game_id, "X", 1, 1))
        before = self.snapshot(self.game_id)
        for player, row, col in (
            ("X", 0, 0),
            ("Z", 0, 0),
            ("", 0, 0),
            ("x", 0, 0),
            ("O", 1, 1),
            ("O", -1, 0),
            ("O", 0, -1),
            ("O", 3, 0),
            ("O", 0, 3),
        ):
            with self.subTest(player=player, row=row, col=col):
                self.assertFalse(self.system.move(self.game_id, player, row, col))
                self.assertEqual(self.snapshot(self.game_id), before)
        self.assertTrue(self.system.move(self.game_id, "O", 0, 0))

    def test_unknown_game_ids_do_not_affect_existing_game(self):
        before = self.snapshot(self.game_id)
        for game_id in (-1, 1, 999):
            with self.subTest(game_id=game_id):
                self.assertFalse(self.system.move(game_id, "X", 0, 0))
                self.assertEqual(self.system.inspect_board(game_id), [])
                self.assertEqual(self.system.inspect_status(game_id), [])
                self.assertEqual(self.system.review_history(game_id), [])
                self.assertEqual(self.snapshot(self.game_id), before)

    def test_winning_length_in_all_four_directions(self):
        for size in (3, 4, 5, 7):
            length = min(5, size)
            start = size - length
            lines = {
                "horizontal": [(size - 1, start + i) for i in range(length)],
                "vertical": [(start + i, size - 1) for i in range(length)],
                "descending": [(start + i, i) for i in range(length)],
                "ascending": [(start + i, size - 1 - i) for i in range(length)],
            }
            for direction, line in lines.items():
                with self.subTest(size=size, direction=direction):
                    self.play_x_line(size, line)

    def test_offset_diagonals_not_touching_corners(self):
        for line in (
            [(1 + i, 2 + i) for i in range(5)],
            [(1 + i, 5 - i) for i in range(5)],
        ):
            with self.subTest(line=line):
                self.play_x_line(8, line)

    def test_o_can_win(self):
        self.play(self.game_id, [(0, 0), (0, 1), (2, 0), (1, 1), (2, 2), (2, 1)])
        self.assertEqual(
            self.system.inspect_status(self.game_id), (GameStatus.HAS_WINNER, "O")
        )

    def test_gap_and_opponent_break_lines(self):
        for opponent_blocks_gap in (False, True):
            with self.subTest(opponent_blocks_gap=opponent_blocks_gap):
                game_id = self.system.create_game(7)
                fillers = [(0, 0), (0, 2), (0, 4), (0, 6), (1, 1)]
                if opponent_blocks_gap:
                    fillers[0] = (3, 2)
                for index, col in enumerate((0, 1, 3, 4, 5)):
                    self.assertTrue(self.system.move(game_id, "X", 3, col))
                    self.assertTrue(self.system.move(game_id, "O", *fillers[index]))
                self.assertEqual(
                    self.system.inspect_status(game_id), (GameStatus.PLAYING, None)
                )

    def test_line_cannot_wrap_across_board_edges(self):
        game_id = self.system.create_game(6)
        self.play(
            game_id,
            [(2, 4), (0, 0), (2, 5), (0, 2), (3, 0), (0, 4),
             (3, 1), (5, 0), (3, 2)],
        )
        self.assertEqual(
            self.system.inspect_status(game_id), (GameStatus.PLAYING, None)
        )

    def test_bridging_two_runs_can_make_more_than_five(self):
        game_id = self.system.create_game(8)
        self.play(
            game_id,
            [(3, 0), (0, 0), (3, 1), (0, 2), (3, 2), (0, 4),
             (3, 4), (0, 6), (3, 5), (1, 0)],
        )
        self.assertEqual(
            self.system.inspect_status(game_id), (GameStatus.PLAYING, None)
        )
        self.assertTrue(self.system.move(game_id, "X", 3, 3))
        self.assertEqual(
            self.system.inspect_status(game_id), (GameStatus.HAS_WINNER, "X")
        )

    def test_draw(self):
        self.play(
            self.game_id,
            [(0, 0), (0, 1), (0, 2), (1, 1), (1, 0),
             (1, 2), (2, 1), (2, 0), (2, 2)],
        )
        self.assertEqual(
            self.system.inspect_status(self.game_id), (GameStatus.DRAW, None)
        )
        self.assertEqual(len(self.history(self.game_id)), 9)

    def test_last_empty_cell_win_takes_precedence_over_draw(self):
        self.play(
            self.game_id,
            [(0, 0), (0, 1), (1, 1), (0, 2), (1, 2),
             (1, 0), (2, 0), (2, 1), (2, 2)],
        )
        self.assertEqual(
            self.system.inspect_status(self.game_id), (GameStatus.HAS_WINNER, "X")
        )
        self.assertEqual(len(self.history(self.game_id)), 9)

    def test_moves_after_win_or_draw_are_atomic(self):
        for coordinates in (
            [(0, 0), (1, 0), (0, 1), (1, 1), (0, 2)],
            [(0, 0), (0, 1), (0, 2), (1, 1), (1, 0),
             (1, 2), (2, 1), (2, 0), (2, 2)],
        ):
            with self.subTest(coordinates=coordinates):
                game_id = self.system.create_game(3)
                self.play(game_id, coordinates)
                before = self.snapshot(game_id)
                for player in ("X", "O"):
                    self.assertFalse(self.system.move(game_id, player, 2, 0))
                    self.assertEqual(self.snapshot(game_id), before)

    def test_finished_game_has_no_next_player(self):
        # There is no next-player query, so inspect the existing turn attribute.
        for coordinates in (
            [(0, 0), (1, 0), (0, 1), (1, 1), (0, 2)],
            [(0, 0), (0, 1), (0, 2), (1, 1), (1, 0),
             (1, 2), (2, 1), (2, 0), (2, 2)],
        ):
            with self.subTest(coordinates=coordinates):
                game_id = self.system.create_game(3)
                self.play(game_id, coordinates)
                self.assertIsNone(self.system.games[game_id].cur_player)

    def test_board_snapshot_is_detached(self):
        self.assertTrue(self.system.move(self.game_id, "X", 0, 0))
        before = self.snapshot(self.game_id)
        board = self.system.inspect_board(self.game_id)
        board[0][0] = "O"
        board[1].append("X")
        board.clear()
        self.assertEqual(self.snapshot(self.game_id), before)

    def test_history_collection_is_detached(self):
        self.play(self.game_id, [(0, 0), (1, 1)])
        before = self.snapshot(self.game_id)
        history = self.system.review_history(self.game_id)
        history.reverse()
        history.pop()
        history.clear()
        self.assertEqual(self.snapshot(self.game_id), before)

    def test_history_records_cannot_mutate_internal_history(self):
        self.assertTrue(self.system.move(self.game_id, "X", 0, 0))
        before = self.snapshot(self.game_id)
        move = self.system.review_history(self.game_id)[0]
        try:
            move._player = "O"
            move._row = 2
            move._col = 2
        except (AttributeError, TypeError):
            pass
        self.assertEqual(self.snapshot(self.game_id), before)

    def test_games_are_independent(self):
        other = self.system.create_game(4)
        other_before = self.snapshot(other)
        self.play(self.game_id, [(0, 0), (1, 0), (0, 1), (1, 1), (0, 2)])
        self.assertEqual(self.snapshot(other), other_before)
        first_before = self.snapshot(self.game_id)
        self.assertTrue(self.system.move(other, "X", 3, 3))
        self.assertEqual(self.snapshot(self.game_id), first_before)


if __name__ == "__main__":
    unittest.main()
