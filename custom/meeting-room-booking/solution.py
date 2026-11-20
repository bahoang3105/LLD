from dataclasses import dataclass
from enum import Enum
from typing import List

@dataclass
class Employee:
    _id: int
    _name: str

    def get_id(self) -> int:
        return self._id

    def get_name(self) -> str:
        return self._name


@dataclass
class Room:
    _id: int
    _name: str
    _capacity: int

    def get_id(self) -> int:
        return self._id

    def get_name(self) -> str:
        return self._name

    def get_capacity(self) -> int:
        return self._capacity


@dataclass
class Booking:
    _id: int
    _organizer: Employee
    _room: Room
    _start: int
    _end: int
    _attendee_count: int
    _status: str

    def get_id(self) -> int:
        return self._id

    def get_organizer(self) -> Employee:
        return self._organizer

    def get_room(self) -> Room:
        return self._room

    def get_start(self) -> int:
        return self._start

    def get_end(self) -> int:
        return self._end

    def get_attendee_count(self) -> int:
        return self._attendee_count

    def get_status(self) -> str:
        return self._status

    def cancel(self) -> bool:
        if self._status == "CANCELLED":
            return False
        self._status = "CANCELLED"
        return True

    def reschedule(self, room: Room, start: int, end: int, attendees: int):
        self._room = room
        self._start = start
        self._end = end
        self._attendee_count = attendees


class BookingSystem:
    def __init__(self):
        self._employees: List[Employee] = []
        self._rooms: List[Room] = []
        self._bookings: List[Booking] = []

    def register_employee(self, name: str) -> int:
        employee = Employee(len(self._employees), name)
        self._employees.append(employee)
        return employee.get_id()

    def add_room(self, name: str, capacity: int) -> int:
        if capacity <= 0:
            return -1
        room = Room(len(self._rooms), name, capacity)
        self._rooms.append(room)
        return room.get_id()

    def get_employee(self, employee_id: int) -> Employee | None:
        if -1 < employee_id < len(self._employees):
            return self._employees[employee_id]
        return None

    def get_room(self, room_id: int) -> Room | None:
        if -1 < room_id < len(self._rooms):
            return self._rooms[room_id]
        return None

    def get_booking(self, booking_id: int) -> Booking | None:
        if -1 < booking_id < len(self._bookings):
            return self._bookings[booking_id]
        return None

    def book(self, employee_id: int, room_id: int, start: int, end: int, attendees: int) -> int:
        employee = self.get_employee(employee_id)
        room = self.get_room(room_id)

        if employee is None or room is None or room.get_capacity() < attendees or attendees <= 0 or start >= end or start < 0:
            return -1

        for booking in self._bookings:
            if (booking.get_room() is room or booking.get_organizer() is employee) \
                and booking.get_status() == "ACTIVE" \
                and booking.get_start() < end and start < booking.get_end():
                return -1

        new_booking = Booking(len(self._bookings), employee, room, start, end, attendees, "ACTIVE")
        self._bookings.append(new_booking)
        return new_booking.get_id()

    def cancel(self, booking_id: int) -> bool:
        booking = self.get_booking(booking_id)
        if booking is None:
            return False
        return booking.cancel()

    def reschedule(self, booking_id: int, room_id: int, start: int, end: int, attendees: int) -> bool:
        booking = self.get_booking(booking_id)
        room = self.get_room(room_id)
        if booking is None or booking.get_status() == "CANCELLED" \
            or room is None or room.get_capacity() < attendees or attendees <= 0 \
            or start >= end or start < 0:
            return False
        employee = booking.get_organizer()
        for _booking in self._bookings:
            if _booking is booking:
                continue
            if (_booking.get_room() is room or _booking.get_organizer() is employee) \
                and _booking.get_status() == "ACTIVE" \
                and _booking.get_start() < end and start < _booking.get_end():
                return False
        booking.reschedule(room, start, end, attendees)
        return True

    def room_bookings(self, room_id: int) -> List[Booking]:
        room = self.get_room(room_id)
        if room is None:
            return []
        return [booking for booking in self._bookings if booking.get_room() is room and booking.get_status() == "ACTIVE"]

    def employee_bookings(self, employee_id: int) -> List[Booking]:
        employee = self.get_employee(employee_id)
        if employee is None:
            return []
        return [booking for booking in self._bookings if booking.get_organizer() is employee and booking.get_status() == "ACTIVE"]

    def available_rooms(self, start: int, end: int, attendees: int) -> List[Room]:
        if start >= end or start < 0 or attendees <= 0:
            return []
        
        candidates = set([i for i in range(len(self._rooms)) if self._rooms[i].get_capacity() >= attendees])
        for booking in self._bookings:
            room = booking.get_room()
            if room.get_id() not in candidates or booking.get_status() == "CANCELLED":
                continue
            if room.get_capacity() < attendees or (booking.get_start() < end and start < booking.get_end()):
                candidates.remove(room.get_id())
        return list(self.get_room(room_id) for room_id in candidates)
