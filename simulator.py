

from generator import Generator
from dataclasses import dataclass
import heapq
from enum import Enum

# Static Constants
TOTAL_ROAD_LENGTH = 40 * 1000 # meters
TOTAL_CHANNELS = 10
NUMBER_OF_BASE_STATIONS = 20
CELL_DAIMETER = TOTAL_ROAD_LENGTH / NUMBER_OF_BASE_STATIONS # meters


@dataclass
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
    _id: int  # Unique identifier for the car # useful for debugging and logging
    velocity: float  # Velocity of the car (meters per second)
    position: float  # Current position of the car in the station (meters)
    station: int  # Current base station the car is connected to
    call_duration: float  # Duration of the ongoing call (seconds)

    def __lt__(self, other):
        """Compare cars based on their ID for ordering."""
        return self._id < other._id

    def _copy(self):
        """Create a copy of the car object."""
        return Car(
            _id=self._id,
            velocity=self.velocity,
            position=self.position,
            station=self.station,
            call_duration=self.call_duration
        )

    def get_direction(self):
        """Determine the direction of the car based on its velocity."""
        return int(self.velocity / abs(self.velocity)) if self.velocity != 0 else 0
    
    def get_next_station(self):
        """Get the next station based on the car's direction."""
        return self.station + self.get_direction()
    
    def next_station_is_valid(self):
        """Check if the next station is valid."""
        return 0 <= self.get_next_station() < NUMBER_OF_BASE_STATIONS
    
    def get_time_to_next_station(self):
        """Calculate the time to reach the next station."""
        if self.get_direction() == -1:
            return (self.position + CELL_DAIMETER) / abs(self.velocity)
        elif self.get_direction() == 1:
            return (CELL_DAIMETER - self.position) / abs(self.velocity)
        else:
            raise ValueError("Car is dircetion Error")

class EventType(Enum):
    CALL_INITIATION = 'call_initiation'
    CALL_TERMINATION = 'call_termination'
    CALL_HANDOVER = 'call_handover'

class Simulator:
    def __init__(self, 
                 generator:Generator, 
                 channel_reserved_for_handover=0,
                 _no_initial_event=False,
                 _no_new_initialisation=False,
                 logging=False
                 ):
        self.clock = 0 # Simulation clock in seconds
        self.event_list = []
        self.base_stations = [0] * NUMBER_OF_BASE_STATIONS
        self.blocked_calls = 0
        self.dropped_calls = 0
        self.completed_calls = 0
        self.channel_reserved_for_handover = channel_reserved_for_handover
        self.gen = generator
        self._id_counter = 0

        self.logging = logging
        self.log = []

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
            position=self.gen.generate_position()*1000,  # Generate random position
            station=self.gen.generate_base_station(),  # Generate random base station
            call_duration=self.gen.generate_call_duration()  # Generate random call duration
        )
    
    def _base_station_have_free_channel_for_initialisation(self, station):
        """Check if the base station has a free channel."""
        return self.base_stations[station] < TOTAL_CHANNELS - self.channel_reserved_for_handover

    def _base_station_have_free_channel_for_handover(self, station):
        """Check if the base station has a free channel for handover."""
        return self.base_stations[station] < TOTAL_CHANNELS

    def add_event(self, time, event_type, car_data):
        """Add an event to the event list, maintaining the order of events."""
        if self.logging:
            self.log.append((self.clock, event_type, car_data._copy()))
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
        self.clock = time
        if event_type == EventType.CALL_INITIATION:
            self.handle_call_initiation(car_data)
        elif event_type == EventType.CALL_TERMINATION:
            self.handle_call_termination(car_data)
        elif event_type == EventType.CALL_HANDOVER:
            self.handle_call_handover(car_data)
        else:
            raise ValueError(f"Unknown event type: {event_type}")
        
    def handle_call_initiation(self, car: Car):
        # Initialise next call
        if not self._no_new_initialisation:
            self.add_event(
                self.clock + self.gen.generate_inter_arrival_time(),
                EventType.CALL_INITIATION,
                self._gen_car()
            )

        # Check if the call can be initiated
        if not self._base_station_have_free_channel_for_initialisation(car.station):
            self.blocked_calls += 1
            return

        self.base_stations[car.station] += 1

        self._scedule_termination_and_handover(car)

    def handle_call_handover(self, car: Car):
        # Check if the call can be handed over
        self.base_stations[car.station] -=1

        if not car.next_station_is_valid():
            self.dropped_calls += 1
            return # Car is out of range
        if not self._base_station_have_free_channel_for_handover(car.get_next_station()):
            self.dropped_calls += 1
            return # No free channel in the next station
        
        self.base_stations[car.get_next_station()] += 1

        new_car_position = -2000 * car.get_direction()
        new_call_duration = car.call_duration - car.get_time_to_next_station()
        new_car_base_station = car.get_next_station()

        # Update the car's attributes
        car.position = new_car_position
        car.call_duration = new_call_duration
        car.station = new_car_base_station

        self._scedule_termination_and_handover(car)

    def handle_call_termination(self, car: Car):
        # Release the channel for the base station
        self.base_stations[car.station] -= 1
        self.completed_calls += 1

    def _scedule_termination_and_handover(self, car: Car):
        """
        Schedule the termination and handover events for a car.
        This methods is garenteed to scedule either a termination or a handover event.
        """

        end_time = self.clock + car.call_duration

        # Check if the call ends before reaching the end of the cell
        if car.get_time_to_next_station() >= car.call_duration:
            self.add_event(end_time, EventType.CALL_TERMINATION, car)
        else:
            # Schedule another handover event
            handover_time = self.clock + (CELL_DAIMETER - car.position) / car.velocity
            self.add_event(handover_time, EventType.CALL_HANDOVER, car)