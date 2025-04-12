from generator import Generator
from dataclasses import dataclass
import heapq
from enum import Enum

# Static Constants
TOTAL_ROAD_LENGTH = 40 * 1000 # meters
TOTAL_CHANNELS = 10
NUMBER_OF_BASE_STATIONS = 20
CELL_DAIMETER = TOTAL_ROAD_LENGTH / NUMBER_OF_BASE_STATIONS # meters

EPSILON = 1e-6
# Small value to avoid floating point errors
# This value is used to ensure that the car is not at the end of the cell when checking for handover


@dataclass
@dataclass(frozen=True)
class Car:
    """
    Class representing a car in the simulation.
    
    Attributes:
        _id: Unique identifier for the car.
        velocity: Velocity of the car (in meters per second).
        position: Current position of the car in the station (in meters).
        station: Current base station the car is connected to.
        call_duration: Duration of the ongoing call (in seconds).
    """
    _id: int  # Unique identifier for the car
    velocity: float  # Velocity of the car (meters per second)
    call_duration: float  # Duration of the ongoing call (seconds)
    root_position: float  # Initial position of the car in the cell (meters)
    root_station: int  # Initial base station of the car
    root_time: float  # Time at which the car was created (seconds)

    def __lt__(self, other: 'Car'):
        """Compare cars based on their ID for ordering."""
        return self._id < other._id

    def get_direction(self) -> int:
        """Determine the direction of the car based on its velocity."""
        return int(self.velocity / abs(self.velocity)) if self.velocity != 0 else 0
    
    def get_abs_position(self, current_time: float = None) -> float:
        """
        Get the absolute position of the car in the road based on its current position and velocity.
        """
        if current_time is None:
            return self.root_station * CELL_DAIMETER  + self.root_position
        else:
            return self.get_abs_position() + self.velocity * (current_time - self.root_time)

    def get_current_station(self, current_time: float) -> int:
        """Get the current station of the car based on its position."""
        abs_position = self.get_abs_position(current_time)
        # Handle edge case when car is exactly at the end of the road
        if abs_position >= TOTAL_ROAD_LENGTH:
            return NUMBER_OF_BASE_STATIONS - 1
        if abs_position < 0:
            return 0
        return int(abs_position // CELL_DAIMETER)

    def get_next_station(self, current_time: float) -> int:
        """Get the next station based on the car's direction."""
        return self.get_current_station(current_time) + self.get_direction()
    
    def next_station_is_valid(self, current_time: float) -> bool:
        """Check if the next station is valid."""
        next_station = self.get_next_station(current_time)
        return 0 <= next_station < NUMBER_OF_BASE_STATIONS
    
    def get_time_to_next_station(self, current_time: float) -> float:
        """Calculate the time to reach the next station."""
        abs_position = self.get_abs_position(current_time)
        current_station = self.get_current_station(current_time)
        station_abs_end = current_station * CELL_DAIMETER + CELL_DAIMETER / 2 + self.get_direction() * CELL_DAIMETER / 2
        if station_abs_end == abs_position:
            return CELL_DAIMETER / abs(self.velocity)
        return (station_abs_end - abs_position) / self.velocity

    def get_end_time(self) -> float:
        """Get the end time of the call."""
        return self.root_time + self.call_duration
    
    def is_still_active(self, current_time: float) -> bool:
        """Check if the car is still active or out of the simulation."""

        is_active = self.root_time <= current_time <= self.get_end_time()
        is_in_bounds = 0 <= self.get_abs_position(current_time) < TOTAL_ROAD_LENGTH
        return is_active and is_in_bounds

class EventType(Enum):
    CALL_INITIATION = 'call_initiation'
    CALL_TERMINATION = 'call_termination'
    CALL_HANDOVER = 'call_handover'

class EventResult(Enum):
    INITIATION_SUCCESS = 'initiation_success'
    INITIATION_BLOCKED = 'initiation_blocked'
    HANDOVER_SUCCESS = 'handover_success'
    HANDOVER_DROPPED = 'handover_dropped'
    TERMINATION = 'termination'

class Simulator:
    def __init__(self, 
                 generator:Generator, 
                 channel_reserved_for_handover=0,
                 _no_initial_event=False,
                 _no_new_initialisation=False,
                 logging=False
                 ):
        self.clock = 0 # Simulation clock in seconds
        self.event_list: list[tuple[float, EventType, Car]] = []
        self.base_stations = [0] * NUMBER_OF_BASE_STATIONS
        self.blocked_calls = 0
        self.dropped_calls = 0
        self.completed_calls = 0
        self.channel_reserved_for_handover = channel_reserved_for_handover
        self.gen = generator
        self._id_counter = 0

        self.logging = logging
        self.log:list[tuple[float, EventType, EventResult, Car]] = []

        self._no_new_initialisation = _no_new_initialisation

        # Add initial event to the event list
        if not _no_initial_event:
            self.add_event(
                self.clock + self.gen.generate_inter_arrival_time(),
                EventType.CALL_INITIATION,
                self._gen_car()
            )

    def _gen_car_id(self):
        self._id_counter += 1
        return self._id_counter - 1
    
    def _gen_car(self):
        """Generate a new car object with random attributes."""
        return Car(
            _id=self._gen_car_id(),  # Generate unique car ID
            velocity=self.gen.generate_velocity()*self.gen.generate_direction() * 1000 / 3600,  # Convert km/h to m/s
            call_duration=self.gen.generate_call_duration(),  # Generate random call duration
            root_position=self.gen.generate_position()*1000,  # Generate random position
            root_station=self.gen.generate_base_station(),  # Generate random base station
            root_time=self.gen.generate_inter_arrival_time() + self.clock  # Generate random time of creation
        )
    
    def _base_station_have_free_channel_for_initialisation(self, station):
        """Check if the base station has a free channel."""
        return self.base_stations[station] < TOTAL_CHANNELS - self.channel_reserved_for_handover

    def _base_station_have_free_channel_for_handover(self, station):
        """Check if the base station has a free channel for handover."""
        return self.base_stations[station] < TOTAL_CHANNELS

    def add_event(self, time, event_type, car_data):
        """Add an event to the event list, maintaining the order of events."""
        heapq.heappush(self.event_list, (time, event_type, car_data))

    def run(self, max_steps=1000):
        """Run the simulation for a specified number of steps."""
        for _ in range(max_steps):
            self.step()
            
    def step(self):
        """Run one step of the simulation."""
        if not self.event_list:
            raise ValueError("No events in the event list.")
        
        time, event_type, car_data = heapq.heappop(self.event_list)

        assert time >= self.clock, f"Event time {time} is less than current clock {self.clock}."
        self.clock = time
        if event_type == EventType.CALL_INITIATION:
            event_result = self.handle_call_initiation(car_data)
        elif event_type == EventType.CALL_TERMINATION:
            event_result = self.handle_call_termination(car_data)
        elif event_type == EventType.CALL_HANDOVER:
            event_result = self.handle_call_handover(car_data)
        else:
            raise ValueError(f"Unknown event type: {event_type}")
        
        if self.logging:
            self.log.append((time, event_type, event_result, car_data, self.blocked_calls, self.dropped_calls, self.completed_calls))
        
    def handle_call_initiation(self, car: Car) -> EventResult:
        # Initialise next call
        if not self._no_new_initialisation:
            new_car = self._gen_car()
            self.add_event(
                new_car.root_time,
                EventType.CALL_INITIATION,
                new_car
            )

        # Check if the car leave the highway
        if not car.next_station_is_valid(self.clock):
            self.add_event(
                self.clock + car.get_time_to_next_station(self.clock),
                EventType.CALL_TERMINATION,
                car
            )
            return EventResult.INITIATION_SUCCESS

        # Check if the call can be initiated
        if not self._base_station_have_free_channel_for_initialisation(car.get_current_station(self.clock)):
            self.blocked_calls += 1
            return EventResult.INITIATION_BLOCKED

        self.base_stations[car.root_station] += 1

        self._scedule_termination_and_handover(car)
        return EventResult.INITIATION_SUCCESS

    def handle_call_handover(self, car: Car) -> EventResult:
        # NOTE: As all handover events are at boundary conditions, we need to subtract EPSILON from the clock to get the correct station
        
        self.base_stations[car.get_current_station(self.clock-EPSILON)] -=1

        if self.clock > 123.3876225028:
            1+1

        # Check if the car leave the highway
        if not car.next_station_is_valid(self.clock - EPSILON):
            self.add_event(
                self.clock + car.get_time_to_next_station(self.clock - EPSILON), # not sure if EPSILON is needed here
                EventType.CALL_TERMINATION,
                car
            )
            return EventResult.HANDOVER_SUCCESS

        if not self._base_station_have_free_channel_for_handover(car.get_next_station(self.clock - EPSILON)):
            # No free channel in the next station
            self.dropped_calls += 1
            return EventResult.HANDOVER_DROPPED
            
        
        self.base_stations[car.get_next_station(self.clock - EPSILON)] += 1

        self._scedule_termination_and_handover(car)
        return EventResult.HANDOVER_SUCCESS

    def handle_call_termination(self, car: Car) -> EventResult:
        # Release the channel for the base station

        # if self.clock> 108.0896747967:
        #     1+1

        # NOTE: As some termination events are at boundary conditions, we need to subtract EPSILON from the clock to get the correct station
        self.base_stations[car.get_current_station(self.clock-EPSILON)] -= 1
        self.completed_calls += 1
        return EventResult.TERMINATION

    def _scedule_termination_and_handover(self, car: Car):
        """
        Schedule the termination and handover events for a car.
        This methods is garenteed to scedule either a termination or a handover event.
        """

        # Check if the call ends before reaching the end of the cell
        # EPSILON is used to find the next station
        time_of_next_station = car.get_time_to_next_station(self.clock) + self.clock
        if time_of_next_station > car.get_end_time():
            self.add_event(car.get_end_time(), EventType.CALL_TERMINATION, car)
        else:
            # Schedule another handover event
            handover_time = time_of_next_station
            self.add_event(handover_time, EventType.CALL_HANDOVER, car)