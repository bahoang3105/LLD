# Design a Library Hold and Loan Manager

**Difficulty:** Hard  
**Language:** Python 3  
**Focus:** Object references, encapsulation, state transitions, FIFO allocation, logical time, and atomic operations.

This is an original exercise inspired by the contract-driven low-level-design practice format. It is not a reproduction of an AlgoMaster problem.

## Problem

A library owns several physical copies of each book. Members borrow copies and place holds when none are immediately available.

Implement `Book`, `Member`, `Loan`, `Hold`, and `Library`. Unlike a basic catalog, this system must coordinate ownership, limited inventory, fair waiting queues, and time-dependent hold expiry.

No database, networking, persistence, real clock, threads, or external dependencies are required.

## Core rules

### Identity and references

- Book, member, loan, and hold IDs are independent sequences starting at `0`.
- Allocate an ID only when the corresponding creation operation succeeds. Never reuse IDs.
- Different books may share a title. Different members may share a name.
- Every loan and hold refers to the exact existing `Book` and `Member` objects; do not reconstruct those objects or associate them by name.
- Names and titles are immutable-style: expose getters but no public setters.
- Loans and holds are retained as history after becoming inactive.

### Inventory

Each book has a positive, fixed total number of interchangeable copies. Individual copies do not need their own objects or IDs.

At every externally observable point:

```text
total copies = available copies + active loans + READY holds
```

`WAITING` holds do not consume copies.

### Borrowing

- A member may have at most **two active loans across all books**.
- A member may have at most one active loan for a particular book.
- A successful borrow creates a new loan with status `ACTIVE`.
- Returning a loan changes its status to `RETURNED`; it cannot be returned again.
- Loans do not expire and have no due dates.

### Holds and FIFO allocation

- A member may have at most one active hold for a particular book. `WAITING` and `READY` are active hold states.
- A member cannot place a hold for a book they currently have on loan.
- A member may place holds even when they already have two active loans.
- Every successful hold enters that book's waiting queue in creation order, then allocation runs immediately.
- Allocation repeatedly gives an available copy to the oldest `WAITING` hold for that book.
- An allocated hold becomes `READY`, consumes one copy, and receives an expiry time of `current time + 3`.
- A ready hold does not count toward the member's active-loan limit.
- Do not skip a waiting member because they currently have two loans. Their hold becomes ready normally, and they must free a loan slot before collecting it.
- A `READY` hold protects its copy from everyone except its owner.
- Removing a waiting hold must preserve the relative order of the remaining waiting holds.

### Hold transitions

```text
WAITING -> READY -> FULFILLED
WAITING -> CANCELLED
READY   -> CANCELLED
READY   -> EXPIRED
```

No other transitions are allowed. Terminal holds cannot be reactivated.

Borrowing with a ready hold atomically changes it to `FULFILLED` and converts its reserved copy into an active loan. It must not temporarily offer that copy to another hold.

### Logical time

- The library starts at time `0`. Time is an integer; one unit represents one day.
- Only `advanceTo()` changes time. Other methods never advance time implicitly.
- A ready hold with `expiresAt == t` expires at time `t`, not after it.
- `advanceTo(target)` must process expiry events **chronologically**, including newly allocated holds that also expire before or at `target`.
- At an event time, expire all ready holds due at that time, release their copies, and run allocation for the affected books using that event time.
- Finish at `target` only after processing all events through `target`.
- Consequently, advancing directly from `0` to `9` must have the same final state as advancing through every integer time from `1` to `9`, with no intervening operations.
- Advancing to the current time succeeds without changing anything.
- Advancing backward fails without changing anything.

## Required object API

Use the exact method names below. Type annotations are recommended.

| Class | Method | Result |
|---|---|---|
| `Book` | `getId() -> int` | Book ID |
| `Book` | `getTitle() -> str` | Original title |
| `Book` | `getTotalCopies() -> int` | Fixed total copies |
| `Book` | `getAvailableCopies() -> int` | Copies neither loaned nor reserved |
| `Member` | `getId() -> int` | Member ID |
| `Member` | `getName() -> str` | Original name |
| `Member` | `getActiveLoans() -> list[Loan]` | Active loans in loan-creation order |
| `Member` | `getActiveHolds() -> list[Hold]` | Waiting and ready holds in hold-creation order |
| `Loan` | `getId() -> int` | Loan ID |
| `Loan` | `getBook() -> Book` | Original book reference |
| `Loan` | `getMember() -> Member` | Original member reference |
| `Loan` | `getStatus() -> str` | `"ACTIVE"` or `"RETURNED"` |
| `Hold` | `getId() -> int` | Hold ID |
| `Hold` | `getBook() -> Book` | Original book reference |
| `Hold` | `getMember() -> Member` | Original member reference |
| `Hold` | `getStatus() -> str` | One of the five hold statuses |
| `Hold` | `getExpiresAt() -> int \| None` | Expiry assigned when first made ready |

`getExpiresAt()` returns `None` for a hold that has never been ready. Once assigned, retain the expiry even after fulfillment, cancellation, or expiry.

All collection getters return **new lists containing the original object references**. Mutating a returned list must not affect internal membership or ordering. Previously returned entity references must reflect later legitimate status changes.

Constructor signatures for the four entity classes and any internal methods are your design choice. Callers create them through `Library`. Callers will not mutate underscore-prefixed attributes or invoke internal mutation methods.

## Required Library API

### Creation and lookup

| Method | Behavior |
|---|---|
| `Library()` | Create an empty library at time `0`. |
| `addBook(title: str, copies: int) -> int` | Create a book and return its ID; return `-1` if `copies <= 0`. |
| `registerMember(name: str) -> int` | Create a member and return its ID. |
| `getBook(bookId: int) -> Book \| None` | Return the stored object, or `None` for an unknown ID. |
| `getMember(memberId: int) -> Member \| None` | Same lookup rule. |
| `getLoan(loanId: int) -> Loan \| None` | Same lookup rule, including returned loans. |
| `getHold(holdId: int) -> Hold \| None` | Same lookup rule, including terminal holds. |
| `getTime() -> int` | Return current logical time. |

Negative IDs are unknown IDs, not Python indexing shortcuts. Names and titles are case-sensitive and may be empty; do not normalize or reject them. Inputs have the declared types.

### `borrow(memberId: int, bookId: int) -> int`

Return a new loan ID on success, or `-1` on failure.

Fail if either ID is unknown, the member already has two active loans, or they already have an active loan for that book.

After those checks:

- If the member has a `READY` hold for this book, fulfill it and create the loan using its reserved copy.
- If the member has a `WAITING` hold for this book, fail; do not cancel the hold or jump the queue.
- Otherwise, borrow only if an unreserved copy is available.

A failed borrow must leave a ready hold ready, with its original expiry.

### `returnLoan(loanId: int) -> bool`

Return `False` for an unknown or already returned loan. Otherwise mark the loan returned, remove it from its member's active loans, release its copy, immediately allocate that book's available copies to waiting holds, and return `True`.

### `placeHold(memberId: int, bookId: int) -> int`

Return `-1` if either ID is unknown, the member already has an active loan for this book, or they already have an active hold for it.

Otherwise create and enqueue a hold, immediately run allocation for that book, and return its ID. It may already be `READY` when the method returns.

A member whose previous hold became terminal may place a new hold for the same book, provided the other rules allow it. The new hold receives a new ID and a new position at the back of the queue.

### `cancelHold(holdId: int) -> bool`

Return `False` for an unknown or terminal hold.

Otherwise mark the hold cancelled and remove it from its member's active holds. If it was ready, release its copy. Run allocation for its book before returning `True`.

### `advanceTo(time: int) -> bool`

Apply the logical-time rules above. Return `False` only when `time` is less than the current time.

### `getWaitingHolds(bookId: int) -> list[Hold]`

Return only that book's `WAITING` holds in FIFO order, or an empty list for an unknown book. Return a defensive list containing the original hold references.

### Atomicity

Every operation that fails must leave **all** observable state unchanged: IDs, clock, inventory, statuses, expiry times, active collections, and queue positions.

Queries must not modify state.

## Worked examples

Each example starts with a fresh library. Assertions illustrate the expected behavior; they are not an exhaustive test suite.

### 1. FIFO reservation, identity, and fulfillment

```python
lib = Library()
book = lib.addBook("Designing Systems", 1)  # 0
alice = lib.registerMember("Alice")        # 0
bob = lib.registerMember("Bob")            # 1
cara = lib.registerMember("Cara")          # 2

loan = lib.borrow(alice, book)             # 0
hb = lib.placeHold(bob, book)              # 0, WAITING
hc = lib.placeHold(cara, book)             # 1, WAITING

assert lib.returnLoan(loan) is True
assert lib.getHold(hb).getStatus() == "READY"
assert lib.getHold(hb).getExpiresAt() == 3
assert lib.getHold(hc).getStatus() == "WAITING"
assert lib.borrow(cara, book) == -1

bob_loan = lib.borrow(bob, book)            # 1
assert lib.getHold(hb).getStatus() == "FULFILLED"
assert lib.getLoan(bob_loan).getBook() is lib.getBook(book)
assert lib.getLoan(bob_loan).getMember() is lib.getMember(bob)
assert lib.getBook(book).getAvailableCopies() == 0
assert lib.getMember(bob).getActiveHolds() == []
assert lib.getWaitingHolds(book)[0] is lib.getHold(hc)
```

### 2. A time jump can expire several generations of holds

```python
lib = Library()
book = lib.addBook("Queues", 1)
members = [lib.registerMember(str(i)) for i in range(3)]
holds = [lib.placeHold(member, book) for member in members]

assert [lib.getHold(h).getStatus() for h in holds] == [
    "READY", "WAITING", "WAITING"
]

assert lib.advanceTo(7) is True
assert [lib.getHold(h).getStatus() for h in holds] == [
    "EXPIRED", "EXPIRED", "READY"
]
assert [lib.getHold(h).getExpiresAt() for h in holds] == [3, 6, 9]
assert lib.getTime() == 7

assert lib.advanceTo(9) is True
assert lib.getHold(holds[2]).getStatus() == "EXPIRED"
assert lib.getBook(book).getAvailableCopies() == 1
assert lib.advanceTo(8) is False
assert lib.getTime() == 9
```

### 3. Loan limits must not destroy a ready hold

```python
lib = Library()
member = lib.registerMember("Reader")
books = [lib.addBook(title, 1) for title in ("A", "B", "C")]

first = lib.borrow(member, books[0])        # 0
assert lib.borrow(member, books[1]) == 1
hold = lib.placeHold(member, books[2])      # 0, READY

assert lib.borrow(member, books[2]) == -1
assert lib.getHold(hold).getStatus() == "READY"
assert lib.getHold(hold).getExpiresAt() == 3
assert lib.getBook(books[2]).getAvailableCopies() == 0

assert lib.returnLoan(first) is True
assert lib.borrow(member, books[2]) == 2    # Failure consumed no ID.
assert lib.getHold(hold).getStatus() == "FULFILLED"
```

### 4. Defensive collections and duplicate names

```python
lib = Library()
a = lib.registerMember("Same Name")
b = lib.registerMember("Same Name")
book = lib.addBook("References", 2)

ha = lib.placeHold(a, book)
hb = lib.placeHold(b, book)
snapshot = lib.getMember(a).getActiveHolds()
snapshot.clear()
assert len(lib.getMember(a).getActiveHolds()) == 1

original_hold = lib.getHold(ha)
assert lib.cancelHold(ha) is True
assert original_hold.getStatus() == "CANCELLED"
assert lib.getHold(hb).getStatus() == "READY"
assert lib.getBook(book).getAvailableCopies() == 1
assert lib.cancelHold(ha) is False
```

## Constraints and performance expectations

- At most 2,000 books, 2,000 members, and 20,000 successful loan or hold creations combined.
- Copy counts range from 1 to 100 for successful book creation.
- Valid logical times range from 0 to `10**9`; backward requests may be negative.
- ID lookup should be O(1) on average.
- `advanceTo()` must not iterate through every elapsed day. Work should depend on stored records or actual expiry/allocation events, not the numerical size of the time jump.
- Linear scans of stored records and simple ordered collections are otherwise acceptable. A heap or specialized queue is optional, not required.
- Returning a collection necessarily costs at least O(k) for its k returned references.

## Design review rubric

Correct output is necessary, but it is not the whole exercise.

| Dimension | Points | What a strong submission demonstrates |
|---|---|---|
| Identity and relationships | 20 | Loans and holds retain canonical object references; names are not used as identity; history is retained. |
| Encapsulation and ownership | 25 | Entities own meaningful behavior and protect their invariants. `Library` coordinates workflows rather than directly editing every entity's internal fields. Public collection results are defensive. |
| State and inventory correctness | 25 | Legal transitions, FIFO fairness, copy conservation, loan limits, and atomic failures hold across all operations. |
| Time model | 20 | Expiry is inclusive, chronological, and correct across chained allocations and large jumps. |
| Simplicity and clarity | 10 | Responsibilities are explicit; shared allocation logic is not duplicated; abstractions serve a real need. |

Do not introduce inheritance, factories, repositories, or design patterns solely to increase the class count. Private helpers and additional small types are allowed when they make invariants easier to enforce.

## Submission

Write your implementation in `solution.py` beside this file. No starter or solution implementation is supplied. Entity constructor signatures are your choice.

The supplied `test_library.py` uses only Python's standard-library `unittest` and the public API. From this problem's folder, run:

```powershell
python -m unittest -v test_library
```

The tests require `solution.py` to export `Book`, `Member`, `Loan`, `Hold`, and `Library`. Until you create that module, running the suite will report an import error.

Tests cover the worked examples and important boundary cases, especially:

- Multiple copies and simultaneous expiries.
- Cancelling a waiting hold in the middle of a queue.
- Cancelling a ready hold and immediately allocating its copy.
- Returning a loan when the oldest waiting member is already at their loan limit.
- Re-placing a hold after cancellation or expiry.
- Borrowing exactly at expiry after `advanceTo()` has processed that time.
- Independent queues for different books.
- Invalid operations that consume no IDs and change no state.
- Large time jumps with repeated expiry and reallocation.

Do not include an implementation in `problem.md`; keep your solution and tests separate.
