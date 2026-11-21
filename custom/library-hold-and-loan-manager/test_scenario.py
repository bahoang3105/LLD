import unittest

from solution import ActivityType, LibrarySystem


class LibraryScenarioTests(unittest.TestCase):
    def test_register_and_find_member(self):
        library = LibrarySystem()
        member_id = library.register_member("Alice")

        self.assertEqual(member_id, 0)
        self.assertIsNotNone(library.get_member(member_id))
        self.assertIsNone(library.get_member(-1))

    def test_borrow_and_return(self):
        library = LibrarySystem()
        book = library.add_book("Python", 1)
        alice = library.register_member("Alice")

        self.assertEqual(library.get_available_copies(book), 1)
        self.assertIs(library.borrow_book(alice, book), True)
        self.assertEqual(library.get_available_copies(book), 0)
        self.assertEqual(
            library.get_current_loans(alice), [library.get_book(book)]
        )

        self.assertIs(library.return_book(alice, book), True)
        self.assertEqual(library.get_available_copies(book), 1)
        self.assertEqual(library.get_current_loans(alice), [])
        self.assertIs(library.return_book(alice, book), False)

    def test_return_reserves_copy_for_waiting_member(self):
        library = LibrarySystem()
        book = library.add_book("Python", 1)
        alice = library.register_member("Alice")
        bob = library.register_member("Bob")

        self.assertIs(library.borrow_book(alice, book), True)
        self.assertIs(library.borrow_book(bob, book), False)
        self.assertIs(library.place_book(bob, book), True)
        self.assertEqual(
            library.get_waiting_order(book), [library.get_member(bob)]
        )

        self.assertIs(library.return_book(alice, book), True)
        self.assertEqual(library.get_waiting_order(book), [])
        self.assertEqual(library.get_available_copies(book), 0)
        self.assertIs(library.borrow_book(bob, book), True)

    def test_cancel_reservation_releases_copy(self):
        library = LibrarySystem()
        book = library.add_book("Python", 1)
        alice = library.register_member("Alice")

        self.assertIs(library.place_book(alice, book), True)
        self.assertEqual(library.get_available_copies(book), 0)
        self.assertIs(library.cancel_book(alice, book), True)
        self.assertEqual(library.get_available_copies(book), 1)
        self.assertIs(library.cancel_book(alice, book), False)

    def test_reservation_expires_three_days_after_allocation(self):
        library = LibrarySystem()
        book = library.add_book("Python", 1)
        alice = library.register_member("Alice")

        self.assertIs(library.advance_to(2), True)
        self.assertIs(library.place_book(alice, book), True)
        self.assertIs(library.advance_to(4), True)
        self.assertEqual(library.get_available_copies(book), 0)
        self.assertIs(library.advance_to(5), True)
        self.assertEqual(library.get_available_copies(book), 1)

    def test_cancelled_reservation_does_not_expire_replacement(self):
        library = LibrarySystem()
        book = library.add_book("Python", 1)
        member = library.register_member("Alice")
        library.place_book(member, book)
        library.advance_to(1)
        library.cancel_book(member, book)
        library.place_book(member, book)

        self.assertIs(library.advance_to(3), True)
        self.assertEqual(library.get_available_copies(book), 0)
        self.assertEqual(
            library.get_current_holds(member), [library.get_book(book)]
        )
        self.assertIs(library.advance_to(4), True)
        self.assertEqual(library.get_available_copies(book), 1)
        expiries = [
            activity._timestamp for activity in library.get_history(member)
            if activity._type == ActivityType.EXPIRE
        ]
        self.assertEqual(expiries, [4])

    def test_collected_reservation_does_not_expire_active_loan(self):
        library = LibrarySystem()
        book = library.add_book("Python", 1)
        member = library.register_member("Alice")
        library.place_book(member, book)
        library.borrow_book(member, book)

        self.assertIs(library.advance_to(10), True)
        self.assertEqual(library.get_available_copies(book), 0)
        self.assertEqual(
            library.get_current_loans(member), [library.get_book(book)]
        )
        self.assertFalse(any(
            activity._type == ActivityType.EXPIRE
            for activity in library.get_history(member)
        ))

    def test_expiries_across_books_follow_event_time(self):
        library = LibrarySystem()
        owner = library.register_member("Owner")
        member = library.register_member("Reader")
        first = library.add_book("First", 1)
        second = library.add_book("Second", 1)
        library.borrow_book(owner, first)
        library.place_book(member, first)
        library.place_book(member, second)
        library.advance_to(2)
        library.return_book(owner, first)

        self.assertIs(library.advance_to(6), True)
        expiries = [
            activity._timestamp for activity in library.get_history(member)
            if activity._type == ActivityType.EXPIRE
        ]
        self.assertEqual(expiries, [3, 5])
        self.assertEqual(library.get_available_copies(first), 1)
        self.assertEqual(library.get_available_copies(second), 1)

    def test_chained_simultaneous_expiries_preserve_history(self):
        library = LibrarySystem()
        book = library.add_book("Python", 2)
        members = [library.register_member(str(i)) for i in range(5)]
        for member in members:
            library.place_book(member, book)

        self.assertIs(library.advance_to(7), True)
        self.assertEqual(library.get_available_copies(book), 1)
        self.assertEqual(
            library.get_current_holds(members[-1]), [library.get_book(book)]
        )
        history = sorted(
            [activity for member in members
             for activity in library.get_history(member)],
            key=lambda activity: activity._id,
        )
        self.assertEqual(
            [activity._id for activity in history], list(range(len(history)))
        )
        self.assertEqual(
            [(activity._type, activity._timestamp) for activity in history
             if activity._timestamp > 0],
            [
                (ActivityType.EXPIRE, 3), (ActivityType.EXPIRE, 3),
                (ActivityType.RESERVE, 3), (ActivityType.RESERVE, 3),
                (ActivityType.EXPIRE, 6), (ActivityType.EXPIRE, 6),
                (ActivityType.RESERVE, 6),
            ],
        )
        self.assertIs(library.advance_to(10**9), True)
        self.assertEqual(library.get_available_copies(book), 2)
        self.assertIs(library.advance_to(10**9), True)
        self.assertIs(library.advance_to(0), False)


if __name__ == "__main__":
    unittest.main()
