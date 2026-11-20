# Design a Meeting Room Booking System

**Difficulty:** Medium  
**Language:** Python 3  
**Focus:** Object references, encapsulation, interval conflicts, defensive collections, and atomic updates.

## Problem

An office has meeting rooms with different capacities. Employees can book rooms, cancel their bookings, and move an existing booking to a different room or time.

Implement `Employee`, `Room`, `Booking`, and `BookingSystem` using the contract below.

This is an in-memory design exercise. You do not need a database, real clock, networking, threads, recurring meetings, or notifications. No starter or solution implementation is provided.

## Core rules

### Identity and references

- Employee, room, and booking IDs are independent sequences starting at `0`.
- Allocate an ID only when creation succeeds. Never reuse IDs.
- Different employees may have the same name. Different rooms may have the same name.
- Every booking stores references to the original employee and room objects, not reconstructed copies or names used as identity.
- Employee names, room names, and room capacities are immutable-style: expose getters but no public setters.
- Entity constructor signatures are your choice. Callers create entities through `BookingSystem`.
- Callers will not mutate underscore-prefixed attributes or invoke internal mutation methods.

### Time intervals

- Times are integer offsets within one abstract scheduling timeline. There is no current time.
- A valid interval satisfies `0 <= start < end`.
- A booking occupies the half-open interval `[start, end)`: the start is included and the end is excluded.
- Two intervals overlap exactly when `firstStart < secondEnd` and `secondStart < firstEnd`.
- Adjacent intervals such as `[10, 20)` and `[20, 30)` do not overlap.

### Booking rules

- Every booking has exactly one organizer, one room, one interval, and a positive attendee count.
- The attendee count includes the organizer. Individual attendees are not modeled.
- A booking's attendee count must not exceed its room's capacity.
- A room cannot have overlapping active bookings.
- An employee cannot organize overlapping active bookings, even in different rooms.
- Different employees may book different rooms at overlapping times.
- A successful new booking has status `"ACTIVE"`.
- Cancellation changes the status to `"CANCELLED"` and releases both the room and the organizer's occupied interval.
- Cancelled bookings remain accessible as history, but no longer block anything.

### Rescheduling

- An active booking can move to another room, another interval, or both, and can change its attendee count.
- Its ID, organizer, object identity, and position in creation order must not change.
- Its room reference, interval, and attendee count update only if every validation succeeds.
- Exclude the booking itself from room-conflict and organizer-conflict checks.
- Rescheduling to exactly the current values succeeds.
- A cancelled booking cannot be rescheduled.

### Atomicity and collections

- A failed operation must leave all observable state unchanged, including IDs, entity fields, statuses, and collection order.
- Queries never modify state.
- Every collection getter returns a new list containing the original entity references.
- Mutating a returned list must not affect the system.
- Previously returned entity references must reflect later legitimate changes.
- All booking lists use **booking-creation order**, not start-time order. Rescheduling must not reorder them.

## Entity API

Use the exact method names below.

| Class | Method | Result |
|---|---|---|
| `Employee` | `get_id() -> int` | Employee ID |
| `Employee` | `get_name() -> str` | Original name |
| `Room` | `get_id() -> int` | Room ID |
| `Room` | `get_name() -> str` | Original name |
| `Room` | `get_capacity() -> int` | Fixed room capacity |
| `Booking` | `get_id() -> int` | Booking ID |
| `Booking` | `get_organizer() -> Employee` | Original organizer reference |
| `Booking` | `get_room() -> Room` | Current room reference |
| `Booking` | `get_start() -> int` | Current start |
| `Booking` | `get_end() -> int` | Current end |
| `Booking` | `get_attendee_count() -> int` | Current attendee count |
| `Booking` | `get_status() -> str` | `"ACTIVE"` or `"CANCELLED"` |

Cancellation preserves the booking's last room, interval, and attendee count for historical inspection.

## BookingSystem API

### Creation and lookup

| Method | Behavior |
|---|---|
| `BookingSystem()` | Create an empty system. |
| `register_employee(name: str) -> int` | Add an employee and return their ID. |
| `add_room(name: str, capacity: int) -> int` | Add a room and return its ID, or `-1` if `capacity <= 0`. |
| `get_employee(employeeId: int) -> Employee \| None` | Return the stored object, or `None` for an unknown ID. |
| `get_room(roomId: int) -> Room \| None` | Same lookup rule. |
| `get_booking(bookingId: int) -> Booking \| None` | Same lookup rule, including cancelled bookings. |

Negative IDs are unknown IDs, not Python indexing shortcuts. Names are case-sensitive, may be empty, and must not be normalized. Inputs have the declared types.

### `book(employeeId: int, roomId: int, start: int, end: int, attendees: int) -> int`

Create a booking and return its ID.

Return `-1` if either ID is unknown, the interval is invalid, the attendee count is not positive, the room is too small, or the booking would conflict with an active booking for that room or organizer.

### `cancel(bookingId: int) -> bool`

Return `False` for an unknown or already cancelled booking. Otherwise cancel the booking and return `True`.

### `reschedule(bookingId: int, roomId: int, start: int, end: int, attendees: int) -> bool`

Apply the rescheduling rules above. Return `False` if the booking is unknown or cancelled, the destination room is unknown, or any of the same interval, capacity, or conflict checks used by `book()` fail.

On success, update the existing booking and return `True`. Do not cancel it and create a replacement.

### `room_bookings(roomId: int) -> list[Booking]`

Return that room's active bookings in booking-creation order, or an empty list for an unknown room.

### `employee_bookings(employeeId: int) -> list[Booking]`

Return that employee's active bookings in booking-creation order, or an empty list for an unknown employee.

### `available_rooms(start: int, end: int, attendees: int) -> list[Room]`

Return rooms that can accommodate the attendee count and have no overlapping active booking for the interval. Use room-creation order.

Return an empty list for an invalid interval or a nonpositive attendee count.

This query has no organizer argument, so it checks room availability only, not an employee's schedule.

## Worked examples

The examples below describe expected behavior, not an implementation.

### 1. Adjacent meetings and organizer conflicts

1. Register Alice as employee `0` and Bob as employee `1`.
2. Add room North with capacity `4` as room `0`, and South with capacity `8` as room `1`.
3. Alice books North for `[10, 20)` with `4` attendees. Return booking ID `0`.
4. Bob books North for `[20, 30)` with `2` attendees. Return booking ID `1`: touching endpoints do not conflict.
5. Bob tries to book North for `[15, 18)` with `2` attendees. Return `-1`: North is occupied.
6. Alice tries to book South for `[15, 18)` with `2` attendees. Return `-1`: Alice already organizes an overlapping meeting.
7. Query available rooms for `[15, 18)` with `2` attendees. Return only South's original room object; this query does not check organizers.

### 2. Failed rescheduling changes nothing

1. Alice has booking `0` in North for `[10, 20)` with `4` attendees.
2. Bob has booking `1` in South for `[15, 25)` with `3` attendees.
3. Reschedule booking `0` to South for `[12, 18)` with `4` attendees. Return `False` because of Bob's booking.
4. Booking `0` still refers to North and still has interval `[10, 20)` and attendee count `4`.
5. Cancel booking `1`. Return `True`.
6. Repeat the reschedule. Return `True`.
7. A previously retained reference to booking `0` now reports South and `[12, 18)`. It is still the exact same object.

### 3. Creation order is not chronological order

1. Create booking `0` in North for `[50, 60)`.
2. Create booking `1` in North for `[10, 20)` with another organizer.
3. `room_bookings(North)` returns booking references in order `[0, 1]`.
4. Move booking `0` to `[30, 40)`.
5. The order is still `[0, 1]`.
6. Cancel booking `0`. The active list is now `[1]`, but `get_booking(0)` still returns its cancelled historical object.

## Constraints

- At most 500 employees, 100 rooms, and 5,000 successful booking creations.
- Valid times are at most `10**9`.
- Successful room capacities and attendee counts are at most 1,000.
- ID lookup should be O(1) on average.
- Linear scans of stored bookings are acceptable for conflict checks and queries.
- Do not iterate over every individual time unit in an interval.

## Design review rubric

| Dimension | Points | What a strong submission demonstrates |
|---|---|---|
| Identity and relationships | 20 | Canonical employee and room references; stable booking identity; independent IDs and retained history. |
| Encapsulation | 25 | Entities protect their data and meaningful invariants; no mutable collections leak. |
| Correctness and atomicity | 35 | Correct half-open overlap checks, room and organizer constraints, cancellation, and all-or-nothing rescheduling. |
| Simplicity and clarity | 20 | Shared rules are expressed consistently without unnecessary patterns or duplicated validation. |

Additional internal helpers are allowed. Inheritance, design patterns, and extra layers are not required.

## Unit tests

Write your implementation in `solution.py` beside this file. Export `Employee`, `Room`, `Booking`, and `BookingSystem`.

The supplied `test_booking_system.py` uses Python's standard-library `unittest`. Run from this problem's folder:

```powershell
python -m unittest -v test_booking_system
```

Until you create `solution.py`, the suite will report an import error. Tests cover public behavior, not the internal architecture; use the rubric to review your design separately.
