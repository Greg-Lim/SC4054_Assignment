

from generator import Generator
from dataclasses import dataclass
import heapq
from enum import Enum

# Static Constants
TOTAL_ROAD_LENGTH = 40 # km
TOTAL_CHANNELS = 10
NUMBER_OF_BASE_STATIONS = 20
CELL_DAIMETER = TOTAL_ROAD_LENGTH / NUMBER_OF_BASE_STATIONS # km

@dataclass
class Car:
    _id: int  # Unique identifier for the car # useful for debugging and logging
    velocity: float  # Velocity of the car
    position: float  # Current position of the car in the station
    station: int  # Current base station the car is connected to
    call_duration: float  # Duration of the ongoing call

class EventType(Enum):
    CALL_INITIATION = 'call_initiation'
    CALL_TERMINATION = 'call_termination'
    CALL_HANDOVER = 'call_handover'

class Simulation:
    def __init__(self, 
                 generator:Generator, 
                 channel_reserved_for_handover=0,
                 ):
        self.clock = 0
        self.event_list = []
        self.base_stations = [0] * NUMBER_OF_BASE_STATIONS
        self.blocked_calls = 0
        self.dropped_calls = 0
        self.completed_calls = 0
        self.channel_reserved_for_handover = channel_reserved_for_handover
        self.gen = generator
        self._id_counter = 0

        self.log = []

        # Add initial event to the event list
        self.add_event(
            self.clock + self.gen.generate_inter_arrival_time(),
            EventType.CALL_INITIATION,
            Car(
                _id=next(self._gen_car_id()),  # Generate unique car ID
                velocity=self.gen.generate_velocity()*self.gen.generate_direction,  # Generate random velocity*direction
                position=self.gen.generate_position(),  # Generate random position
                station=self.gen.generate_base_station(),  # Generate random base station
                call_duration=self.gen.generate_call_duration()  # Generate random call duration
            )
        )

    def _gen_car_id(self):
        yield self._id_counter
        self._id_counter += 1

    def add_event(self, time, event_type, event_data):
        """Add an event to the event list, maintaining the order of events."""
        heapq.heappush(self.event_list, (time, event_type, event_data))

    def run(self, end_time):
        while self.clock < end_time and self.event_list:
            time, event_type, event_data = heapq.heappop(self.event_list)

            self.clock = time
            if event_type == EventType.CALL_INITIATION:
                pass
            elif event_type == EventType.CALL_TERMINATION:
                pass
            elif event_type == EventType.CALL_HANDOVER:
                pass
            else:
                raise ValueError(f"Unknown event type: {event_type}")

    def handle_call_initiation(self, time, car: Car):
        # Check if the call can be initiated
        if self.base_stations[car.station] < TOTAL_CHANNELS - self.channel_reserved_for_handover:
            self.base_stations[car.station] += 1

            # Determine the end time of the call
            end_time = time + car.call_duration

            # Check if the call ends before reaching the end of the cell
            if car.position + car.velocity * car.call_duration < CELL_DAIMETER:
                self.add_event(end_time, EventType.CALL_TERMINATION, car)
            else:
                # Schedule a handover event
                handover_time = time + (CELL_DAIMETER - car.position) / car.velocity
                car.position = 0  # Reset position for the next cell
                car.station += car.direction  # Update to the next station
                self.add_event(handover_time, EventType.CALL_HANDOVER, car)
        else:
            self.blocked_calls += 1

    def handle_call_termination(self, time, car: Car):
        # Release the channel for the base station
        self.base_stations[car.station] -= 1
        self.completed_calls += 1

    def handle_call_handover(self, time, car: Car):
        # Check if the call can be handed over
        if 0 <= car.station < NUMBER_OF_BASE_STATIONS and self.base_stations[car.station] < TOTAL_CHANNELS:
            self.base_stations[car.station] += 1
            self.base_stations[car.station - car.direction] -= 1  # Release the channel of the old station

            # Determine the end time of the call
            end_time = time + car.call_duration

            # Check if the call ends before reaching the end of the cell
            if car.position + car.velocity * car.call_duration < CELL_DAIMETER:
                self.add_event(end_time, EventType.CALL_TERMINATION, car)
            else:
                # Schedule another handover event
                handover_time = time + (CELL_DAIMETER - car.position) / car.velocity
                car.position = 0  # Reset position for the next cell
                car.station += car.direction  # Update to the next station
                self.add_event(handover_time, EventType.CALL_HANDOVER, car)
        else:
            self.dropped_calls += 1

            