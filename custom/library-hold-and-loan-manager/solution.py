from dataclasses import dataclass
from enum import Enum
from typing import List

class BorrowStatus(Enum):
    WAITING = 1
    CANCELED = 2
    RESERVED = 3
    EXPIRED = 4
    BORROWING = 5
    RETURNED = 6

class ActivityType(Enum):
    PLACE = 1
    CANCEL = 2
    RESERVE = 3
    EXPIRE = 4
    BORROW = 5
    RETURN = 6


@dataclass
class Book:
    _id: int
    _name: str
    _total_copies: int
    _available_copies: int

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def total_copies(self) -> int:
        return self._total_copies

    @property
    def available_copies(self) -> int:
        return self._available_copies

    def increase_available_copies(self):
        self._available_copies += 1

    def decrease_available_copies(self):
        self._available_copies -= 1

@dataclass
class Member:
    _id: int
    _name: str

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        return self._name
    

@dataclass
class Borrow:
    _id: int
    _book: Book
    _member: Member
    _status: BorrowStatus
    _reserved_at: int

    @property
    def id(self) -> int:
        return self._id

    @property
    def book(self) -> Book:
        return self._book

    @property
    def member(self) -> Member:
        return self._member

    @property
    def status(self) -> BorrowStatus:
        return self._status

    @property
    def reserved_at(self) -> int:
        return self._reserved_at

    def set_status(self, status: BorrowStatus):
        self._status = status

    def set_reserved_at(self, reserved_at: int):
        self._reserved_at = reserved_at

@dataclass
class Activity:
    _id: int
    _timestamp: int
    _type: ActivityType
    _book: Book
    _member: Member

    @property
    def member(self) -> Member:
        return self._member

class LibrarySystem:
    MAX_ACTIVE_LOANS = 2
    MAX_RESERVED_DAYS = 3

    def __init__(self):
        self._members: List[Member] = []
        self._books: List[Book] = []
        self._borrows: List[Borrow] = []
        self._activities: List[Activity] = []
        self._timestamp: int = 0

    def advance_to(self, timestamp: int) -> bool:
        if timestamp < self._timestamp:
            return False

        while True:
            due = [
                borrow for borrow in self._borrows
                if borrow.status == BorrowStatus.RESERVED
                and borrow.reserved_at + self.MAX_RESERVED_DAYS <= timestamp
            ]
            if not due:
                break

            event_time = min(
                borrow.reserved_at + self.MAX_RESERVED_DAYS
                for borrow in due
            )
            expiring = [
                borrow for borrow in due
                if borrow.reserved_at + self.MAX_RESERVED_DAYS == event_time
            ]

            for borrow in expiring:
                borrow.set_status(BorrowStatus.EXPIRED)
                borrow.book.increase_available_copies()
                self._activities.append(Activity(
                    len(self._activities), event_time, ActivityType.EXPIRE,
                    borrow.book, borrow.member,
                ))

            for borrow in expiring:
                self._reserve_for_next_waiting(borrow.book, -1, event_time)

        self._timestamp = timestamp
        return True

    def add_book(self, name: str, copies: int) -> int:
        if copies <= 0:
            return -1
        book = Book(len(self._books), name, copies, copies)
        self._books.append(book)
        return book.id

    def register_member(self, name: str) -> int:
        member = Member(len(self._members), name)
        self._members.append(member)
        return member.id

    def get_book(self, book_id: int) -> Book | None:
        if book_id >= len(self._books) or book_id < 0:
            return None
        return self._books[book_id]

    def get_member(self, member_id: int) -> Member | None:
        if member_id >= len(self._members) or member_id < 0:
            return None
        return self._members[member_id]

    def place_book(self, member_id: int, book_id: int) -> bool:
        book = self.get_book(book_id)
        member = self.get_member(member_id)
        if book is None or member is None:
            return False
        for borrow in self._borrows:
            if borrow.book is book \
                and borrow.member is member \
                and borrow.status in (BorrowStatus.WAITING, BorrowStatus.RESERVED, BorrowStatus.BORROWING):
                return False
        borrow = Borrow(len(self._borrows), book, member, BorrowStatus.WAITING, -1)
        self._borrows.append(borrow)
        activity = Activity(len(self._activities), self._timestamp, ActivityType.PLACE, book, member)
        self._activities.append(activity)
        if book.available_copies > 0:
            borrow.set_status(BorrowStatus.RESERVED)
            borrow.set_reserved_at(self._timestamp)
            book.decrease_available_copies()
            activity = Activity(len(self._activities), self._timestamp, ActivityType.RESERVE, book, member)
            self._activities.append(activity)
        return True

    def borrow_book(self, member_id: int, book_id: int) -> bool:
        book = self.get_book(book_id)
        member = self.get_member(member_id)
        if book is None or member is None:
            return False
        active_loans = self.get_current_loans(member_id)
        if len(active_loans) >= self.MAX_ACTIVE_LOANS or any(loaned_book is book for loaned_book in active_loans):
            return False
        for borrow in self._borrows:
            if borrow.member is member \
                and borrow.book is book \
                and borrow.status == BorrowStatus.RESERVED:
                borrow.set_status(BorrowStatus.BORROWING)
                activity = Activity(len(self._activities), self._timestamp, ActivityType.BORROW, book, member)
                self._activities.append(activity)
                return True
        if book.available_copies > 0:
            borrow = Borrow(len(self._borrows), book, member, BorrowStatus.BORROWING, -1)
            self._borrows.append(borrow)
            book.decrease_available_copies()
            activity = Activity(len(self._activities), self._timestamp, ActivityType.BORROW, book, member)
            self._activities.append(activity)
            return True
        return False

    def return_book(self, member_id: int, book_id: int) -> bool:
        book = self.get_book(book_id)
        member = self.get_member(member_id)
        if book is None or member is None:
            return False
        for i, borrow in enumerate(self._borrows):
            if borrow.member is member \
                and borrow.book is book \
                and borrow.status == BorrowStatus.BORROWING:
                borrow.set_status(BorrowStatus.RETURNED)
                book.increase_available_copies()
                activity = Activity(len(self._activities), self._timestamp, ActivityType.RETURN, book, member)
                self._activities.append(activity)
                self._reserve_for_next_waiting(book, i)
                return True
        return False

    def cancel_book(self, member_id: int, book_id: int) -> bool:
        book = self.get_book(book_id)
        member = self.get_member(member_id)
        if book is None or member is None:
            return False
        for i, borrow in enumerate(self._borrows):
            if borrow.member is member \
                and borrow.book is book \
                and borrow.status in (BorrowStatus.WAITING, BorrowStatus.RESERVED):
                if borrow.status == BorrowStatus.RESERVED:
                    book.increase_available_copies()
                    self._reserve_for_next_waiting(book, i)
                borrow.set_status(BorrowStatus.CANCELED)
                activity = Activity(len(self._activities), self._timestamp, ActivityType.CANCEL, book, member)
                self._activities.append(activity)
                return True
        return False

    def _reserve_for_next_waiting(self, book: Book, index: int, timestamp: int = -1):
        for i in range(index + 1, len(self._borrows)):
            if self._borrows[i].book is book \
                and self._borrows[i].status == BorrowStatus.WAITING:
                self._borrows[i].set_status(BorrowStatus.RESERVED)
                timestamp = timestamp if timestamp >= 0 else self._timestamp
                self._borrows[i].set_reserved_at(timestamp)
                book.decrease_available_copies()
                activity = Activity(len(self._activities), timestamp, ActivityType.RESERVE, book, self._borrows[i].member)
                self._activities.append(activity)
                return

    def get_available_copies(self, book_id: int):
        book = self.get_book(book_id)
        if book is None: 
            return -1
        return book.available_copies
    
    def get_waiting_order(self, book_id: int):
        book = self.get_book(book_id)
        if book is None:
            return []
        waiting_order = []
        for borrow in self._borrows:
            if borrow.book is book and \
                borrow.status == BorrowStatus.WAITING:
                waiting_order.append(borrow.member)
        return waiting_order

    def get_current_loans(self, member_id: int):
        member = self.get_member(member_id)
        if member is None:
            return []
        current_loans = []
        for borrow in self._borrows:
            if borrow.member is member and \
                borrow.status == BorrowStatus.BORROWING:
                current_loans.append(borrow.book)
        return current_loans

    def get_current_holds(self, member_id: int):
        member = self.get_member(member_id)
        if member is None:
            return []
        current_holds = []
        for borrow in self._borrows:
            if borrow.member is member and \
                borrow.status in (BorrowStatus.WAITING, BorrowStatus.RESERVED):
                current_holds.append(borrow.book)
        return current_holds

    def get_history(self, member_id: int):
        member = self.get_member(member_id)
        return [activity for activity in self._activities if activity.member is member]


