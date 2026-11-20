import unittest

from solution import Book, Hold, Library, Loan, Member


class LibraryTests(unittest.TestCase):
    def setUp(self):
        self.lib = Library()

    def ids(self, objects):
        return [obj.getId() for obj in objects]

    def assert_hold(self, hold_id, status, expires_at):
        hold = self.lib.getHold(hold_id)
        self.assertEqual(hold.getStatus(), status)
        self.assertEqual(hold.getExpiresAt(), expires_at)

    def assert_inventory(self, book_id, loan_ids=(), hold_ids=()):
        book = self.lib.getBook(book_id)
        active = sum(
            self.lib.getLoan(i).getStatus() == "ACTIVE" for i in loan_ids
        )
        ready = sum(
            self.lib.getHold(i).getStatus() == "READY" for i in hold_ids
        )
        self.assertEqual(
            book.getTotalCopies(),
            book.getAvailableCopies() + active + ready,
        )
        self.assertGreaterEqual(book.getAvailableCopies(), 0)

    def test_creation_ids_names_and_invalid_copy_counts(self):
        self.assertEqual(self.lib.getTime(), 0)
        self.assertEqual(self.lib.addBook("Bad", 0), -1)
        self.assertEqual(self.lib.addBook("Bad", -2), -1)
        books = [self.lib.addBook(title, 2) for title in ("Same", "Same", "")]
        members = [self.lib.registerMember(name) for name in ("Same", "Same", "")]
        self.assertEqual(books, [0, 1, 2])
        self.assertEqual(members, [0, 1, 2])
        for i, title in enumerate(("Same", "Same", "")):
            book = self.lib.getBook(i)
            member = self.lib.getMember(i)
            self.assertIsInstance(book, Book)
            self.assertIsInstance(member, Member)
            self.assertEqual(book.getId(), i)
            self.assertEqual(book.getTitle(), title)
            self.assertEqual(book.getTotalCopies(), 2)
            self.assertEqual(book.getAvailableCopies(), 2)
            self.assertEqual(member.getId(), i)
            self.assertEqual(member.getName(), title)
            self.assertEqual(member.getActiveLoans(), [])
            self.assertEqual(member.getActiveHolds(), [])
        self.assertIsNot(self.lib.getBook(0), self.lib.getBook(1))
        self.assertIsNot(self.lib.getMember(0), self.lib.getMember(1))

    def test_unknown_ids_in_empty_and_populated_library(self):
        for populated in (False, True):
            if populated:
                self.lib.addBook("Book", 1)
                self.lib.registerMember("Member")
                self.lib.borrow(0, 0)
                self.lib.registerMember("Waiting")
                self.lib.placeHold(1, 0)
            for invalid in (-1, 999):
                with self.subTest(populated=populated, invalid=invalid):
                    self.assertIsNone(self.lib.getBook(invalid))
                    self.assertIsNone(self.lib.getMember(invalid))
                    self.assertIsNone(self.lib.getLoan(invalid))
                    self.assertIsNone(self.lib.getHold(invalid))
                    self.assertEqual(self.lib.getWaitingHolds(invalid), [])
                    self.assertEqual(self.lib.borrow(invalid, 0), -1)
                    self.assertEqual(self.lib.borrow(0, invalid), -1)
                    self.assertEqual(self.lib.placeHold(invalid, 0), -1)
                    self.assertEqual(self.lib.placeHold(0, invalid), -1)
                    self.assertIs(self.lib.returnLoan(invalid), False)
                    self.assertIs(self.lib.cancelHold(invalid), False)
            self.assertEqual(self.lib.getTime(), 0)
            if populated:
                self.assertEqual(self.lib.getLoan(0).getStatus(), "ACTIVE")
                self.assert_hold(0, "WAITING", None)
                self.assertEqual(self.ids(self.lib.getWaitingHolds(0)), [0])
                self.assert_inventory(0, [0], [0])

    def test_borrow_return_history_and_duplicate_book_loan(self):
        book = self.lib.addBook("Book", 2)
        member = self.lib.registerMember("Member")
        loan_id = self.lib.borrow(member, book)
        self.assertEqual(loan_id, 0)
        loan = self.lib.getLoan(loan_id)
        self.assertIsInstance(loan, Loan)
        self.assertEqual(loan.getId(), loan_id)
        self.assertIs(loan.getBook(), self.lib.getBook(book))
        self.assertIs(loan.getMember(), self.lib.getMember(member))
        self.assertEqual(self.lib.borrow(member, book), -1)
        self.assertEqual(self.lib.placeHold(member, book), -1)
        self.assertIs(self.lib.returnLoan(loan_id), True)
        self.assertIs(self.lib.returnLoan(loan_id), False)
        self.assertIs(self.lib.getLoan(loan_id), loan)
        self.assertEqual(loan.getStatus(), "RETURNED")
        self.assertEqual(self.lib.getMember(member).getActiveLoans(), [])
        self.assertEqual(self.lib.getBook(book).getAvailableCopies(), 2)
        self.assertEqual(self.lib.borrow(member, book), 1)

    def test_fifo_return_reserves_for_oldest_and_fulfillment_is_atomic(self):
        book = self.lib.addBook("Book", 1)
        owner, first, second, outsider = [
            self.lib.registerMember(str(i)) for i in range(4)
        ]
        loan = self.lib.borrow(owner, book)
        h1 = self.lib.placeHold(first, book)
        h2 = self.lib.placeHold(second, book)
        self.assert_hold(h1, "WAITING", None)
        self.assert_hold(h2, "WAITING", None)
        self.assertEqual(self.ids(self.lib.getWaitingHolds(book)), [h1, h2])
        self.assertIs(self.lib.advanceTo(2), True)
        self.assertIs(self.lib.returnLoan(loan), True)
        self.assert_hold(h1, "READY", 5)
        self.assertEqual(self.lib.borrow(second, book), -1)
        self.assertEqual(self.lib.borrow(outsider, book), -1)
        collected = self.lib.borrow(first, book)
        self.assertEqual(collected, 1)
        self.assert_hold(h1, "FULFILLED", 5)
        self.assert_hold(h2, "WAITING", None)
        self.assertEqual(self.lib.getMember(first).getActiveHolds(), [])
        self.assertIs(self.lib.cancelHold(h1), False)
        self.assert_inventory(book, [loan, collected], [h1, h2])
        self.assertIs(self.lib.returnLoan(collected), True)
        self.assert_hold(h2, "READY", 5)

    def test_ready_hold_duplicate_rejection_and_cancellation(self):
        book = self.lib.addBook("Book", 1)
        members = [self.lib.registerMember(str(i)) for i in range(2)]
        ready = self.lib.placeHold(members[0], book)
        hold = self.lib.getHold(ready)
        self.assertIsInstance(hold, Hold)
        self.assertEqual(hold.getId(), ready)
        self.assertIs(hold.getBook(), self.lib.getBook(book))
        self.assertIs(hold.getMember(), self.lib.getMember(members[0]))
        self.assertEqual(self.lib.placeHold(members[0], book), -1)
        waiting = self.lib.placeHold(members[1], book)
        self.assertEqual(waiting, 1)
        self.assertIs(self.lib.advanceTo(1), True)
        self.assertIs(self.lib.cancelHold(ready), True)
        self.assert_hold(ready, "CANCELLED", 3)
        self.assert_hold(waiting, "READY", 4)
        self.assertEqual(self.lib.getMember(members[0]).getActiveHolds(), [])
        self.assertIs(self.lib.cancelHold(ready), False)
        self.assertIs(self.lib.advanceTo(3), True)
        self.assert_hold(waiting, "READY", 4)
        self.assert_inventory(book, hold_ids=[ready, waiting])

    def test_cancel_middle_waiter_preserves_fifo_and_none_expiry(self):
        book = self.lib.addBook("Book", 1)
        members = [self.lib.registerMember(str(i)) for i in range(4)]
        loan = self.lib.borrow(members[0], book)
        holds = [self.lib.placeHold(m, book) for m in members[1:]]
        self.assertEqual(self.lib.placeHold(members[2], book), -1)
        self.assertIs(self.lib.cancelHold(holds[1]), True)
        self.assert_hold(holds[1], "CANCELLED", None)
        self.assertEqual(
            self.ids(self.lib.getWaitingHolds(book)), [holds[0], holds[2]]
        )
        self.assertIs(self.lib.returnLoan(loan), True)
        self.assert_hold(holds[0], "READY", 3)
        self.assert_hold(holds[2], "WAITING", None)

    def test_loan_limit_failure_preserves_ready_hold_and_loan_id(self):
        member = self.lib.registerMember("Reader")
        books = [self.lib.addBook(title, 1) for title in ("A", "B", "C")]
        first = self.lib.borrow(member, books[0])
        self.assertEqual(self.lib.borrow(member, books[1]), 1)
        self.assertEqual(self.lib.borrow(member, books[2]), -1)
        hold = self.lib.placeHold(member, books[2])
        self.assertEqual(self.lib.borrow(member, books[2]), -1)
        self.assert_hold(hold, "READY", 3)
        self.assert_inventory(books[2], hold_ids=[hold])
        self.assertIs(self.lib.returnLoan(first), True)
        self.assertEqual(self.lib.borrow(member, books[2]), 2)
        self.assert_hold(hold, "FULFILLED", 3)
        self.assertEqual(
            self.ids(self.lib.getMember(member).getActiveLoans()), [1, 2]
        )

    def test_allocation_does_not_skip_member_at_loan_limit(self):
        books = [self.lib.addBook(title, 1) for title in ("A", "B", "C")]
        full, owner, other = [
            self.lib.registerMember(str(i)) for i in range(3)
        ]
        self.lib.borrow(full, books[0])
        self.lib.borrow(full, books[1])
        loan = self.lib.borrow(owner, books[2])
        first = self.lib.placeHold(full, books[2])
        second = self.lib.placeHold(other, books[2])
        self.assertIs(self.lib.returnLoan(loan), True)
        self.assert_hold(first, "READY", 3)
        self.assert_hold(second, "WAITING", None)
        self.assertEqual(self.lib.borrow(full, books[2]), -1)
        self.assertIs(self.lib.advanceTo(3), True)
        self.assert_hold(first, "EXPIRED", 3)
        self.assert_hold(second, "READY", 6)

    def test_expiry_boundary_and_backward_clock_atomicity(self):
        book = self.lib.addBook("Book", 1)
        a = self.lib.registerMember("A")
        b = self.lib.registerMember("B")
        first = self.lib.placeHold(a, book)
        second = self.lib.placeHold(b, book)
        self.assertIs(self.lib.advanceTo(-1), False)
        self.assertIs(self.lib.advanceTo(2), True)
        self.assertIs(self.lib.advanceTo(2), True)
        self.assert_hold(first, "READY", 3)
        self.assertIs(self.lib.advanceTo(1), False)
        self.assertEqual(self.lib.getTime(), 2)
        self.assert_hold(first, "READY", 3)
        self.assert_hold(second, "WAITING", None)
        self.assertIs(self.lib.advanceTo(3), True)
        self.assert_hold(first, "EXPIRED", 3)
        self.assert_hold(second, "READY", 6)
        self.assertEqual(self.lib.borrow(a, book), -1)
        self.assertIs(self.lib.cancelHold(first), False)
        self.assertEqual(self.lib.getMember(a).getActiveHolds(), [])
        self.assertEqual(self.lib.borrow(b, book), 0)

    def test_chained_expiries_use_event_time_not_jump_target(self):
        book = self.lib.addBook("Book", 1)
        members = [self.lib.registerMember(str(i)) for i in range(3)]
        holds = [self.lib.placeHold(m, book) for m in members]
        self.assertIs(self.lib.advanceTo(7), True)
        for h, status, expiry in zip(
            holds, ("EXPIRED", "EXPIRED", "READY"), (3, 6, 9)
        ):
            self.assert_hold(h, status, expiry)
        self.assertEqual(self.lib.getTime(), 7)
        self.assertIs(self.lib.advanceTo(9), True)
        self.assert_hold(holds[2], "EXPIRED", 9)
        self.assertEqual(self.lib.getBook(book).getAvailableCopies(), 1)

    def test_simultaneous_expiries_with_multiple_copies(self):
        book = self.lib.addBook("Book", 2)
        members = [self.lib.registerMember(str(i)) for i in range(5)]
        holds = [self.lib.placeHold(m, book) for m in members]
        self.assertIs(self.lib.advanceTo(3), True)
        for i, hold in enumerate(holds):
            status = "EXPIRED" if i < 2 else "READY" if i < 4 else "WAITING"
            expiry = 3 if i < 2 else 6 if i < 4 else None
            self.assert_hold(hold, status, expiry)
        self.assert_inventory(book, hold_ids=holds)
        self.assertIs(self.lib.advanceTo(6), True)
        self.assert_hold(holds[4], "READY", 9)
        self.assertEqual(self.lib.getBook(book).getAvailableCopies(), 1)
        self.assertEqual(self.lib.getWaitingHolds(book), [])
        self.assert_inventory(book, hold_ids=holds)

    def test_jump_matches_incremental_advances_and_handles_large_target(self):
        def scenario(incremental):
            lib = Library()
            book = lib.addBook("Book", 2)
            members = [lib.registerMember(str(i)) for i in range(7)]
            holds = [lib.placeHold(m, book) for m in members]
            targets = range(1, 11) if incremental else (10,)
            for target in targets:
                self.assertIs(lib.advanceTo(target), True)
            state = (
                lib.getTime(),
                lib.getBook(book).getAvailableCopies(),
                [(lib.getHold(h).getStatus(), lib.getHold(h).getExpiresAt())
                 for h in holds],
                [self.ids(lib.getMember(m).getActiveHolds()) for m in members],
                self.ids(lib.getWaitingHolds(book)),
            )
            self.assertIs(lib.advanceTo(10**9), True)
            self.assertEqual(lib.getBook(book).getAvailableCopies(), 2)
            self.assertTrue(
                all(lib.getHold(h).getStatus() == "EXPIRED" for h in holds)
            )
            return state

        self.assertEqual(scenario(False), scenario(True))

    def test_terminal_hold_replacement_joins_back_of_queue(self):
        book = self.lib.addBook("Book", 1)
        a, b = [self.lib.registerMember(name) for name in ("A", "B")]
        old = self.lib.placeHold(a, book)
        other = self.lib.placeHold(b, book)
        self.assertIs(self.lib.cancelHold(old), True)
        replacement = self.lib.placeHold(a, book)
        self.assertEqual(replacement, 2)
        self.assert_hold(other, "READY", 3)
        self.assert_hold(replacement, "WAITING", None)
        self.assertIs(self.lib.advanceTo(3), True)
        newest = self.lib.placeHold(b, book)
        self.assertEqual(newest, 3)
        self.assert_hold(replacement, "READY", 6)
        self.assert_hold(newest, "WAITING", None)
        self.assertEqual(self.ids(self.lib.getWaitingHolds(book)), [newest])
        loan = self.lib.borrow(a, book)
        self.assertEqual(self.lib.placeHold(a, book), -1)
        self.assertIs(self.lib.returnLoan(loan), True)
        final = self.lib.placeHold(a, book)
        self.assertEqual(final, 4)
        self.assert_hold(replacement, "FULFILLED", 6)
        self.assert_hold(final, "WAITING", None)

    def test_collections_are_defensive_but_entities_remain_live(self):
        books = [self.lib.addBook(title, 2) for title in ("A", "B", "C", "D")]
        member = self.lib.registerMember("Reader")
        loans = [self.lib.borrow(member, b) for b in books[:2]]
        holds = [self.lib.placeHold(member, b) for b in books[2:]]
        person = self.lib.getMember(member)
        loan_snapshot = person.getActiveLoans()
        hold_snapshot = person.getActiveHolds()
        self.assertIsNot(loan_snapshot, person.getActiveLoans())
        self.assertIsNot(hold_snapshot, person.getActiveHolds())
        self.assertIs(loan_snapshot[0], self.lib.getLoan(loans[0]))
        self.assertIs(hold_snapshot[0], self.lib.getHold(holds[0]))
        loan_snapshot.clear()
        hold_snapshot.reverse()
        hold_snapshot.pop()
        self.assertEqual(self.ids(person.getActiveLoans()), loans)
        self.assertEqual(self.ids(person.getActiveHolds()), holds)
        live_loan = self.lib.getLoan(loans[0])
        live_hold = self.lib.getHold(holds[0])
        self.assertIs(self.lib.returnLoan(loans[0]), True)
        self.assertIs(self.lib.cancelHold(holds[0]), True)
        self.assertEqual(live_loan.getStatus(), "RETURNED")
        self.assertEqual(live_hold.getStatus(), "CANCELLED")
        self.assertEqual(self.ids(person.getActiveLoans()), loans[1:])
        self.assertEqual(self.ids(person.getActiveHolds()), holds[1:])

    def test_waiting_list_is_defensive_and_preserves_reference_identity(self):
        book = self.lib.addBook("Book", 1)
        members = [self.lib.registerMember(str(i)) for i in range(3)]
        holds = [self.lib.placeHold(m, book) for m in members]
        snapshot = self.lib.getWaitingHolds(book)
        self.assertIsNot(snapshot, self.lib.getWaitingHolds(book))
        self.assertIs(snapshot[0], self.lib.getHold(holds[1]))
        snapshot.clear()
        self.assertEqual(self.ids(self.lib.getWaitingHolds(book)), holds[1:])
        self.assertIs(self.lib.cancelHold(holds[0]), True)
        self.assert_hold(holds[1], "READY", 3)

    def test_same_titles_and_names_do_not_merge_identity_or_queues(self):
        a = self.lib.addBook("Same", 1)
        b = self.lib.addBook("Same", 1)
        first = self.lib.registerMember("Same")
        second = self.lib.registerMember("Same")
        loan = self.lib.borrow(first, a)
        other_loan = self.lib.borrow(first, b)
        ha = self.lib.placeHold(second, a)
        self.assertIs(self.lib.advanceTo(1), True)
        hb = self.lib.placeHold(second, b)
        self.assertIs(self.lib.returnLoan(loan), True)
        self.assert_hold(ha, "READY", 4)
        self.assert_hold(hb, "WAITING", None)
        self.assertEqual(self.lib.getLoan(other_loan).getStatus(), "ACTIVE")
        self.assertIs(self.lib.advanceTo(4), True)
        self.assert_hold(ha, "EXPIRED", 4)
        self.assert_hold(hb, "WAITING", None)
        self.assertIs(self.lib.returnLoan(other_loan), True)
        self.assert_hold(hb, "READY", 7)
        self.assertIs(self.lib.getHold(ha).getBook(), self.lib.getBook(a))
        self.assertIs(self.lib.getHold(hb).getBook(), self.lib.getBook(b))

    def test_loans_never_expire_and_spare_copies_remain_borrowable(self):
        book = self.lib.addBook("Book", 3)
        a, b, c = [self.lib.registerMember(str(i)) for i in range(3)]
        loan = self.lib.borrow(a, book)
        hold = self.lib.placeHold(b, book)
        other = self.lib.borrow(c, book)
        self.assertEqual(other, 1)
        self.assert_inventory(book, [loan, other], [hold])
        self.assertIs(self.lib.advanceTo(10**9), True)
        self.assertEqual(self.lib.getLoan(loan).getStatus(), "ACTIVE")
        self.assertEqual(self.lib.getLoan(other).getStatus(), "ACTIVE")
        self.assert_hold(hold, "EXPIRED", 3)
        self.assert_inventory(book, [loan, other], [hold])
        self.assertEqual(self.lib.getBook(book).getAvailableCopies(), 1)


if __name__ == "__main__":
    unittest.main()
