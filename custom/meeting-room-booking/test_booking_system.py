import unittest

from solution import Booking, BookingSystem, Employee, Room


class BookingSystemTests(unittest.TestCase):
    def setUp(self):
        self.system = BookingSystem()
        self.alice = self.system.register_employee("Alice")
        self.bob = self.system.register_employee("Bob")
        self.north = self.system.add_room("North", 4)
        self.south = self.system.add_room("South", 8)

    def ids(self, objects):
        return [obj.get_id() for obj in objects]

    def booking_state(self, booking):
        return (
            booking.get_id(),
            booking.get_organizer(),
            booking.get_room(),
            booking.get_start(),
            booking.get_end(),
            booking.get_attendee_count(),
            booking.get_status(),
        )

    def test_creation_independent_ids_duplicate_and_empty_names(self):
        self.assertEqual((self.alice, self.bob), (0, 1))
        self.assertEqual((self.north, self.south), (0, 1))
        self.assertEqual(self.system.add_room("Invalid", 0), -1)
        self.assertEqual(self.system.add_room("Invalid", -2), -1)
        duplicate_room = self.system.add_room("North", 4)
        duplicate_employee = self.system.register_employee("Alice")
        self.assertEqual(duplicate_room, 2)
        self.assertEqual(duplicate_employee, 2)
        self.assertIsNot(
            self.system.get_room(duplicate_room), self.system.get_room(self.north)
        )
        self.assertIsNot(
            self.system.get_employee(duplicate_employee),
            self.system.get_employee(self.alice),
        )
        empty_room = self.system.add_room("", 1)
        empty_employee = self.system.register_employee("")
        room = self.system.get_room(self.north)
        employee = self.system.get_employee(self.alice)
        self.assertIsInstance(room, Room)
        self.assertIsInstance(employee, Employee)
        self.assertEqual(room.get_name(), "North")
        self.assertEqual(room.get_capacity(), 4)
        self.assertEqual(employee.get_name(), "Alice")
        self.assertEqual(self.system.get_room(empty_room).get_name(), "")
        self.assertEqual(self.system.get_employee(empty_employee).get_name(), "")

    def test_booking_getters_and_canonical_references(self):
        booking_id = self.system.book(self.alice, self.north, 10, 20, 4)
        self.assertEqual(booking_id, 0)
        booking = self.system.get_booking(booking_id)
        self.assertIsInstance(booking, Booking)
        self.assertEqual(booking.get_id(), 0)
        self.assertIs(booking.get_organizer(), self.system.get_employee(self.alice))
        self.assertIs(booking.get_room(), self.system.get_room(self.north))
        self.assertEqual(
            (booking.get_start(), booking.get_end(), booking.get_attendee_count()),
            (10, 20, 4),
        )
        self.assertEqual(booking.get_status(), "ACTIVE")
        self.assertIs(self.system.room_bookings(self.north)[0], booking)
        self.assertIs(self.system.employee_bookings(self.alice)[0], booking)

    def test_invalid_bookings_do_not_consume_ids(self):
        cases = [
            (-1, self.north, 10, 20, 1),
            (999, self.north, 10, 20, 1),
            (self.alice, -1, 10, 20, 1),
            (self.alice, 999, 10, 20, 1),
            (self.alice, self.north, -1, 20, 1),
            (self.alice, self.north, 10, 10, 1),
            (self.alice, self.north, 20, 10, 1),
            (self.alice, self.north, 10, 20, 0),
            (self.alice, self.north, 10, 20, -1),
            (self.alice, self.north, 10, 20, 5),
        ]
        for args in cases:
            with self.subTest(args=args):
                self.assertEqual(self.system.book(*args), -1)
                self.assertEqual(self.system.room_bookings(self.north), [])
                self.assertEqual(self.system.employee_bookings(self.alice), [])
                self.assertIsNone(self.system.get_booking(0))
        self.assertEqual(self.system.book(self.alice, self.north, 0, 1, 4), 0)

    def test_room_overlap_including_containment_and_equal_intervals(self):
        self.assertEqual(self.system.book(self.alice, self.north, 10, 20, 1), 0)
        for start, end in ((10, 20), (12, 18), (5, 25), (5, 15), (15, 25)):
            with self.subTest(start=start, end=end):
                self.assertEqual(
                    self.system.book(self.bob, self.north, start, end, 1), -1
                )
        self.assertEqual(self.system.book(self.bob, self.north, 0, 10, 1), 1)
        self.assertEqual(self.system.book(self.bob, self.north, 20, 30, 1), 2)

    def test_organizer_overlap_across_rooms_and_adjacent_bookings(self):
        self.system.book(self.alice, self.north, 10, 20, 1)
        self.assertEqual(self.system.book(self.alice, self.south, 15, 25, 1), -1)
        self.assertEqual(self.system.book(self.bob, self.south, 10, 20, 1), 1)
        self.assertEqual(self.system.book(self.alice, self.south, 20, 30, 1), 2)

    def test_cancel_retains_history_and_releases_both_constraints(self):
        booking_id = self.system.book(self.alice, self.north, 10, 20, 3)
        booking = self.system.get_booking(booking_id)
        before = self.booking_state(booking)
        self.assertIs(self.system.cancel(booking_id), True)
        self.assertEqual(booking.get_status(), "CANCELLED")
        self.assertEqual(self.booking_state(booking)[:-1], before[:-1])
        self.assertIs(self.system.get_booking(booking_id), booking)
        self.assertIs(self.system.cancel(booking_id), False)
        self.assertEqual(self.system.room_bookings(self.north), [])
        self.assertEqual(self.system.employee_bookings(self.alice), [])
        self.assertEqual(self.system.book(self.bob, self.north, 10, 20, 1), 1)
        self.assertEqual(self.system.book(self.alice, self.south, 10, 20, 1), 2)

    def test_reschedule_preserves_identity_organizer_and_id_sequence(self):
        booking_id = self.system.book(self.alice, self.north, 10, 20, 2)
        booking = self.system.get_booking(booking_id)
        self.assertIs(
            self.system.reschedule(booking_id, self.south, 15, 25, 6), True
        )
        self.assertIs(self.system.get_booking(booking_id), booking)
        self.assertEqual(booking.get_id(), booking_id)
        self.assertIs(booking.get_organizer(), self.system.get_employee(self.alice))
        self.assertIs(booking.get_room(), self.system.get_room(self.south))
        self.assertEqual(
            (booking.get_start(), booking.get_end(), booking.get_attendee_count()),
            (15, 25, 6),
        )
        self.assertEqual(booking.get_status(), "ACTIVE")
        self.assertEqual(self.system.room_bookings(self.north), [])
        self.assertIs(self.system.room_bookings(self.south)[0], booking)
        self.assertEqual(self.system.book(self.bob, self.north, 10, 20, 1), 1)

    def test_reschedule_excludes_self_for_both_conflict_checks(self):
        booking = self.system.book(self.alice, self.north, 10, 20, 2)
        self.assertIs(
            self.system.reschedule(booking, self.north, 10, 20, 2), True
        )
        self.assertIs(
            self.system.reschedule(booking, self.north, 12, 25, 4), True
        )
        self.assertEqual(self.system.get_booking(booking).get_start(), 12)

    def test_failed_reschedules_preserve_every_field_and_membership(self):
        booking_id = self.system.book(self.alice, self.north, 10, 20, 2)
        self.system.book(self.bob, self.south, 30, 40, 2)
        self.system.book(self.alice, self.north, 50, 60, 2)
        booking = self.system.get_booking(booking_id)
        before = self.booking_state(booking)
        cases = [
            (-1, 10, 20, 2),
            (999, 10, 20, 2),
            (self.south, -1, 20, 2),
            (self.south, 20, 20, 2),
            (self.south, 21, 20, 2),
            (self.south, 10, 20, 0),
            (self.south, 10, 20, -1),
            (self.north, 10, 20, 5),
            (self.south, 35, 45, 2),
            (self.south, 55, 65, 2),
        ]
        for args in cases:
            with self.subTest(args=args):
                self.assertIs(self.system.reschedule(booking_id, *args), False)
                self.assertEqual(self.booking_state(booking), before)
                self.assertEqual(self.ids(self.system.room_bookings(self.north)), [0, 2])
                self.assertEqual(self.ids(self.system.room_bookings(self.south)), [1])
                self.assertEqual(
                    self.ids(self.system.employee_bookings(self.alice)), [0, 2]
                )
        self.assertEqual(self.system.book(self.bob, self.south, 70, 80, 1), 3)

    def test_cancelled_booking_cannot_be_rescheduled(self):
        booking_id = self.system.book(self.alice, self.north, 10, 20, 2)
        self.system.cancel(booking_id)
        booking = self.system.get_booking(booking_id)
        before = self.booking_state(booking)
        self.assertIs(
            self.system.reschedule(booking_id, self.south, 30, 40, 3), False
        )
        self.assertEqual(self.booking_state(booking), before)
        self.assertEqual(self.system.room_bookings(self.south), [])

    def test_available_rooms_capacity_order_endpoints_and_cancellation(self):
        third = self.system.add_room("Tiny", 2)
        booking = self.system.book(self.alice, self.north, 10, 20, 2)
        self.assertEqual(
            self.ids(self.system.available_rooms(15, 18, 2)), [self.south, third]
        )
        self.assertEqual(
            self.ids(self.system.available_rooms(20, 30, 4)),
            [self.north, self.south],
        )
        self.assertEqual(
            self.ids(self.system.available_rooms(15, 18, 8)), [self.south]
        )
        self.assertEqual(self.system.available_rooms(15, 18, 9), [])
        self.system.cancel(booking)
        self.assertEqual(
            self.ids(self.system.available_rooms(15, 18, 2)),
            [self.north, self.south, third],
        )
        for start, end, attendees in ((-1, 2, 1), (2, 2, 1), (3, 2, 1),
                                      (1, 2, 0), (1, 2, -1)):
            with self.subTest(start=start, end=end, attendees=attendees):
                self.assertEqual(
                    self.system.available_rooms(start, end, attendees), []
                )

    def test_creation_order_survives_moves_into_and_out_of_rooms(self):
        first = self.system.book(self.alice, self.south, 50, 60, 2)
        second = self.system.book(self.bob, self.north, 10, 20, 2)
        third = self.system.book(self.alice, self.north, 70, 80, 2)
        self.assertIs(
            self.system.reschedule(first, self.north, 30, 40, 2), True
        )
        self.assertEqual(
            self.ids(self.system.room_bookings(self.north)), [first, second, third]
        )
        self.assertEqual(
            self.ids(self.system.employee_bookings(self.alice)), [first, third]
        )
        self.system.cancel(second)
        self.assertEqual(
            self.ids(self.system.room_bookings(self.north)), [first, third]
        )

    def test_collection_results_are_defensive_and_entities_remain_live(self):
        booking_id = self.system.book(self.alice, self.north, 10, 20, 2)
        booking = self.system.get_booking(booking_id)
        for getter in (
            lambda: self.system.room_bookings(self.north),
            lambda: self.system.employee_bookings(self.alice),
        ):
            snapshot = getter()
            self.assertIsInstance(snapshot, list)
            self.assertIsNot(snapshot, getter())
            self.assertIs(snapshot[0], booking)
            snapshot.clear()
            self.assertEqual(self.ids(getter()), [booking_id])
        rooms = self.system.available_rooms(30, 40, 1)
        self.assertIsInstance(rooms, list)
        self.assertIsNot(rooms, self.system.available_rooms(30, 40, 1))
        self.assertIs(rooms[0], self.system.get_room(self.north))
        rooms.clear()
        self.assertEqual(
            self.ids(self.system.available_rooms(30, 40, 1)),
            [self.north, self.south],
        )
        snapshot = self.system.employee_bookings(self.alice)
        self.system.cancel(booking_id)
        self.assertEqual(snapshot[0].get_status(), "CANCELLED")
        self.assertEqual(self.system.employee_bookings(self.alice), [])

    def test_duplicate_names_do_not_merge_identity(self):
        other_employee = self.system.register_employee("Alice")
        other_room = self.system.add_room("North", 4)
        first = self.system.book(self.alice, self.north, 10, 20, 2)
        second = self.system.book(other_employee, other_room, 10, 20, 2)
        self.assertEqual((first, second), (0, 1))
        self.assertIs(
            self.system.get_booking(second).get_organizer(),
            self.system.get_employee(other_employee),
        )
        self.assertIs(
            self.system.get_booking(second).get_room(), self.system.get_room(other_room)
        )
        self.assertEqual(self.ids(self.system.room_bookings(self.north)), [first])

    def test_unknown_ids_in_empty_and_populated_systems(self):
        for system in (BookingSystem(), self.system):
            for invalid in (-1, 999):
                with self.subTest(system=system, invalid=invalid):
                    self.assertIsNone(system.get_employee(invalid))
                    self.assertIsNone(system.get_room(invalid))
                    self.assertIsNone(system.get_booking(invalid))
                    self.assertEqual(system.employee_bookings(invalid), [])
                    self.assertEqual(system.room_bookings(invalid), [])
                    self.assertIs(system.cancel(invalid), False)
                    self.assertIs(
                        system.reschedule(invalid, self.north, 10, 20, 1), False
                    )

    def test_negative_booking_id_does_not_target_latest_booking(self):
        booking_id = self.system.book(self.alice, self.north, 10, 20, 2)
        booking = self.system.get_booking(booking_id)
        before = self.booking_state(booking)
        self.assertIsNone(self.system.get_booking(-1))
        self.assertIs(self.system.cancel(-1), False)
        self.assertIs(self.system.reschedule(-1, self.south, 30, 40, 2), False)
        self.assertEqual(self.booking_state(booking), before)

    def test_large_intervals_require_no_per_time_unit_storage(self):
        booking = self.system.book(self.alice, self.north, 0, 10**9, 4)
        self.assertEqual(booking, 0)
        self.assertEqual(self.system.book(self.bob, self.north, 50, 51, 1), -1)
        self.assertEqual(
            self.ids(self.system.available_rooms(0, 10**9, 1)), [self.south]
        )


if __name__ == "__main__":
    unittest.main()
