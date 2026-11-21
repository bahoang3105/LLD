# Design a Library Hold and Loan Manager

**Difficulty:** Hard

## Problem

Design an in-memory library system where members borrow books and reserve copies through holds. Each book title in the catalog has a fixed number of interchangeable physical copies.

The system must support adding books, registering members, borrowing and returning books, placing and cancelling holds, and advancing a simulated clock. Users should be able to inspect availability, a member's current loans and holds, waiting order, and historical activity.

Choose your own classes, methods, data structures, and error-reporting conventions.

## Expected behavior

- Books and members have stable, unique identities. Matching titles or names do not make two records the same. Historical records remain associated with the correct book and member.
- A member can have at most two active loans and cannot borrow two copies of the same book at once. Loans remain active until returned; there are no due dates or fines.
- A member can have only one active hold per book and cannot place a hold for a book they currently have on loan.
- Holds are served in first-come, first-served order for each book. Whenever a copy is available, it is immediately reserved for the earliest waiting hold, including a newly placed hold when no one is ahead.
- A reserved copy is protected for its holder for three days. It cannot be borrowed by another member. Members without a reservation may borrow only unreserved copies and cannot bypass waiting holds.
- Members at their loan limit may still place holds and receive reservations. They must return a book before collecting a reserved copy; an unsuccessful collection leaves the reservation unchanged.
- Collecting a reserved copy fulfills the hold and starts a loan without releasing the copy to someone else.
- Returning a book, cancelling a reservation, or letting a reservation expire immediately makes that copy available to the next waiting member.
- Cancelling a waiting hold preserves everyone else's relative position. A finished hold cannot be reused, but the member may place a new hold at the back of the queue if otherwise eligible.
- Retain loan and hold history, including their outcomes and any assigned reservation expiry, after return, fulfillment, cancellation, or expiry. Show current loans and holds in their original creation order.
- Invalid operations must not partially change state. Unknown records, duplicate returns or cancellations, and attempts to exceed limits must be handled consistently.
- Inspecting or modifying returned collections must not let callers change the system's internal membership or ordering.

### Simulated time

Time starts at day 0 and changes only when explicitly advanced. It cannot move backward. Advancing to the current day is valid and changes nothing.

A reservation allocated on day 2 expires exactly on day 5. A large time jump must account for successive reservations and expiries as if time had advanced gradually.

For example, with one available copy and three holds placed on day 0, the first reservation expires on day 3, the second on day 6, and the third on day 9 if nobody collects or cancels. On day 7, only the third member has a reservation.

## Constraints

- At most 2,000 catalog books, 2,000 members, and 20,000 loan and hold records combined.
- Each book has 1 to 100 copies; reject nonpositive copy counts.
- Names and titles are case-sensitive, may be empty, and need not be unique.
- Time is an integer from 0 to 1,000,000,000. Reject requests to move backward.
- Every copy is always either available, on loan, or reserved; never double-allocate or lose a copy.
- Large time jumps must not require iterating over every elapsed day. Linear scans of stored records are otherwise acceptable.
- No persistence, networking, concurrency, real clock, renewals, fines, or tracking of individual physical copies is required.
