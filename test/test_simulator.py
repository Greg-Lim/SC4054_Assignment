import unittest
from unittest.mock import MagicMock, patch
import sys
import os
from io import StringIO
import numpy as np

# Add parent directory to path to import simulator and generator
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulator import Simulator, Car, EventType, TOTAL_CHANNELS, NUMBER_OF_BASE_STATIONS, CELL_DAIMETER
from generator import Generator

class TestCar(unittest.TestCase):
    def test_car_copy(self):
        """Test the _copy method of Car class"""
        car = Car(_id=1, velocity=60, position=1000.0, station=5, call_duration=120.0)
        car_copy = car._copy()
        
        # Check if the copy has the same attributes
        self.assertEqual(car._id, car_copy._id)
        self.assertEqual(car.velocity, car_copy.velocity)
        self.assertEqual(car.position, car_copy.position)
        self.assertEqual(car.station, car_copy.station)
        self.assertEqual(car.call_duration, car_copy.call_duration)
        
        # Check if it's a different object
        self.assertIsNot(car, car_copy)
    
    def test_car_direction_positive(self):
        """Test get_direction with positive velocity"""
        car = Car(_id=1, velocity=60, position=1000.0, station=5, call_duration=120.0)
        self.assertEqual(car.get_direction(), 1)
    
    def test_car_direction_negative(self):
        """Test get_direction with negative velocity"""
        car = Car(_id=1, velocity=-60, position=1000.0, station=5, call_duration=120.0)
        self.assertEqual(car.get_direction(), -1)
    
    def test_car_direction_zero(self):
        """Test get_direction with zero velocity"""
        car = Car(_id=1, velocity=0, position=1000.0, station=5, call_duration=120.0)
        self.assertEqual(car.get_direction(), 0)
    
    def test_get_next_station(self):
        """Test get_next_station method"""
        # Test moving forward
        car_forward = Car(_id=1, velocity=60, position=1000.0, station=5, call_duration=120.0)
        self.assertEqual(car_forward.get_next_station(), 6)
        
        # Test moving backward
        car_backward = Car(_id=2, velocity=-60, position=1000.0, station=5, call_duration=120.0)
        self.assertEqual(car_backward.get_next_station(), 4)
        
        # Test stationary
        car_stationary = Car(_id=3, velocity=0, position=1000.0, station=5, call_duration=120.0)
        self.assertEqual(car_stationary.get_next_station(), 5)
    
    def test_next_station_is_valid(self):
        """Test next_station_is_valid method"""
        # Test valid next station (middle of the road)
        car_middle = Car(_id=1, velocity=60, position=1000.0, station=5, call_duration=120.0)
        self.assertTrue(car_middle.next_station_is_valid())
        
        # Test invalid next station (edge cases)
        car_edge_forward = Car(_id=2, velocity=60, position=1000.0, station=NUMBER_OF_BASE_STATIONS-1, call_duration=120.0)
        self.assertFalse(car_edge_forward.next_station_is_valid())
        
        car_edge_backward = Car(_id=3, velocity=-60, position=1000.0, station=0, call_duration=120.0)
        self.assertFalse(car_edge_backward.next_station_is_valid())
    
    def test_get_time_to_next_station(self):
        """Test get_time_to_next_station method"""
        # Cell diameter is TOTAL_ROAD_LENGTH / NUMBER_OF_BASE_STATIONS
        # For a car moving forward
        car_forward = Car(_id=1, velocity=10, position=1000.0, station=5, call_duration=120.0)
        expected_time_forward = (CELL_DAIMETER - 1000.0) / 10
        self.assertAlmostEqual(car_forward.get_time_to_next_station(), expected_time_forward)
        
        # For a car moving backward
        car_backward = Car(_id=2, velocity=-10, position=1000.0, station=5, call_duration=120.0)
        expected_time_backward = (1000.0 + CELL_DAIMETER) / 10
        self.assertAlmostEqual(car_backward.get_time_to_next_station(), expected_time_backward)
        
        # For a car with zero velocity (should raise ValueError)
        car_stationary = Car(_id=3, velocity=0, position=1000.0, station=5, call_duration=120.0)
        with self.assertRaises(ValueError):
            car_stationary.get_time_to_next_station()
    
    def test_car_comparison(self):
        """Test car comparison (__lt__ method)"""
        car1 = Car(_id=1, velocity=60, position=1000.0, station=5, call_duration=120.0)
        car2 = Car(_id=2, velocity=60, position=1000.0, station=5, call_duration=120.0)
        car3 = Car(_id=3, velocity=60, position=1000.0, station=5, call_duration=120.0)
        
        self.assertTrue(car1 < car2)
        self.assertTrue(car2 < car3)
        self.assertFalse(car2 < car1)

class TestSimulator(unittest.TestCase):
    def setUp(self):
        # Create a mock generator to have deterministic behavior
        self.mock_generator = MagicMock(spec=Generator)
        
        # Default mock return values
        self.mock_generator.generate_inter_arrival_time.return_value = 1.0
        self.mock_generator.generate_velocity.return_value = 60.0
        self.mock_generator.generate_direction.return_value = 1  # Property, not method
        self.mock_generator.generate_position.return_value = 1.0
        self.mock_generator.generate_base_station.return_value = 5
        self.mock_generator.generate_call_duration.return_value = 2.0

    def test_add_event(self):
        """Test if events are added to the event list correctly"""
        sim = Simulator(self.mock_generator, _no_initial_event=True, _no_new_initialisation=True)
        
        # Clear event list for testing
        sim.event_list = []
        
        # Create a car for the event
        car = Car(_id=1, velocity=60, position=1.0, station=5, call_duration=2.0)
        
        # Add events with different timestamps to test ordering
        sim.add_event(3.0, EventType.CALL_INITIATION, car)
        sim.add_event(1.0, EventType.CALL_TERMINATION, car)
        sim.add_event(2.0, EventType.CALL_HANDOVER, car)
        
        # Check if events are ordered by time
        self.assertEqual(len(sim.event_list), 3)
        first_event = sim.event_list[0]
        self.assertEqual(first_event[0], 1.0)  # Time
        self.assertEqual(first_event[1], EventType.CALL_TERMINATION)  # Type

    def test_handle_call_initiation_success(self):
        """Test successful call initiation"""
        sim = Simulator(self.mock_generator, _no_initial_event=True, _no_new_initialisation=True)
        sim.event_list = []  # Clear event list
        
        car = Car(_id=1, velocity=2/3.6, position=0.0, station=5, call_duration=1800)
        
        # Base station has no calls initially
        self.assertEqual(sim.base_stations[5], 0)
        
        # Handle call initiation
        sim.clock = 2.0
        sim.handle_call_initiation(car)
        
        # Check if base station channel is allocated
        self.assertEqual(sim.base_stations[5], 1)
        
        # Check if termination event is scheduled
        self.assertEqual(len(sim.event_list), 1)
        event = sim.event_list[0]
        self.assertEqual(event[0], 1802)  # Time = current time + call duration
        self.assertEqual(event[1], EventType.CALL_TERMINATION)

    def test_handle_call_initiation_blocked(self):
        """Test call initiation when all channels are occupied"""
        sim = Simulator(self.mock_generator, _no_initial_event=True, _no_new_initialisation=True)
        sim.event_list = []  # Clear event list
        
        car = Car(_id=1, velocity=20/3.6, position=0.0, station=5, call_duration=3600)
        
        # Fill up all channels
        sim.base_stations[5] = TOTAL_CHANNELS
        
        # Initial blocked calls
        initial_blocked = sim.blocked_calls
        
        # Handle call initiation
        sim.handle_call_initiation(car)
        
        # Check if call was blocked
        self.assertEqual(sim.blocked_calls, initial_blocked + 1)
        
        # Check that no event was scheduled
        self.assertEqual(len(sim.event_list), 0)

    def test_handle_call_termination(self):
        """Test call termination"""
        sim = Simulator(self.mock_generator, _no_initial_event=True, _no_new_initialisation=True)
        sim.event_list = []  # Clear event list
        
        car = Car(_id=1, velocity=20/3.6, position=0.0, station=5, call_duration=3600)
        
        # Allocate a channel
        sim.base_stations[car.station] = 1
        
        # Handle call termination
        sim.clock = 2.0
        sim.handle_call_termination(car)
        
        # Check if channel was released
        self.assertEqual(sim.base_stations[car.station], 0)
        
        # Check if completed calls was incremented
        self.assertEqual(sim.completed_calls, 1)

    def test_handle_call_handover_success(self):
        """Test successful call handover"""
        sim = Simulator(self.mock_generator, _no_initial_event=True, _no_new_initialisation=True)
        sim.event_list = []  # Clear event list
        
        # Create car at station 5 moving to station 6
        car = Car(_id=1, velocity=2/3.6, position=0.0, station=5, call_duration=3600)
        
        # Set initial state (channel occupied at previous station)
        sim.base_stations[5] = 1  # Previous station
        
        # Handle handover
        sim.clock = 5.0
        sim.handle_call_handover(car)
        
        # Check if channel was released from old station
        self.assertEqual(sim.base_stations[5], 0)
        
        # Check if channel was allocated to new station
        self.assertEqual(sim.base_stations[6], 1)
        
        # Check if a new event was scheduled
        self.assertEqual(len(sim.event_list), 1)

    def test_handle_call_handover_dropped(self):
        """Test call handover when destination has no available channels"""
        sim = Simulator(self.mock_generator, _no_initial_event=True, _no_new_initialisation=True)
        sim.event_list = []  # Clear event list
        
        # Create car at station 5 moving to station 6
        car = Car(_id=1, velocity=2/3.6, position=0.0, station=5, call_duration=3600)
        
        # Set initial state (channel occupied at previous station and all channels occupied at new station)
        sim.base_stations[5] = 1  # Previous station
        sim.base_stations[6] = TOTAL_CHANNELS  # New station is full
        
        # Initial dropped calls
        initial_dropped = sim.dropped_calls
        
        # Handle handover
        sim.clock = 5.0
        sim.handle_call_handover(car)
        
        # Check if call was dropped
        self.assertEqual(sim.dropped_calls, initial_dropped + 1)
        
        # Verify no new events were scheduled
        self.assertEqual(len(sim.event_list), 0)

    def test_reserved_channels_for_handover(self):
        """Test reserving 1 channel for handover"""
        # Create sim with 1 channels reserved for handover
        sim = Simulator(self.mock_generator, _no_initial_event=True, channel_reserved_for_handover=1, _no_new_initialisation=True)
                
        # Occupy all but the reserved channels
        sim.base_stations[5] = TOTAL_CHANNELS - 2  # One less than the threshold
        
        # This call should be accepted
        car1 = Car(_id=1, velocity=2/3.6, position=0.0, station=5, call_duration=3600)
        sim.handle_call_initiation(car1)
        self.assertEqual(sim.base_stations[5], TOTAL_CHANNELS - 1)
        
        # This call should be blocked (only reserved channels left)
        car2 = Car(_id=2, velocity=2/3.6, position=0.0, station=5, call_duration=3600)
        sim.handle_call_initiation(car2)
        self.assertEqual(sim.blocked_calls, 1)

    def test_car_id_generation(self):
        """Test that car IDs are generated correctly"""
        sim = Simulator(self.mock_generator, _no_initial_event=True, _no_new_initialisation=True)
        
        # Reset counter
        sim._id_counter = 0
        
        # Generate a few IDs
        ids = [sim._gen_car_id() for _ in range(5)]
        
        # Check if IDs are sequential
        self.assertEqual(ids, [0, 1, 2, 3, 4])

    # Integration test for the entire simulation process
    def test_short_simulation_0_reserve(self):
        """Test a short simulation run"""
        sim = Simulator(self.mock_generator, _no_initial_event=True, _no_new_initialisation=True)
        
        # Add 11 call initiation events
        # first 10 will be accepted, the 11th will be blocked
        for i in range(11):
            sim.add_event(
                i,
                EventType.CALL_INITIATION,
                Car(_id=i, velocity=2/3.6, position=0.0, station=5, call_duration=7200)
            )
            sim.step()

        self.assertEqual(sim.blocked_calls, 1)
        self.assertEqual(len(sim.event_list), 10)
        self.assertEqual(sim.clock, 10) # 0,1,2, ... 10 = 11 events

        # Add a car to base station 6
        sim.add_event(
            11,
            EventType.CALL_INITIATION,
            Car(_id=11, velocity=2/3.6, position=-20, station=6, call_duration=7200)
        )
        sim.step()

        self.assertEqual(sim.base_stations[5], 10)
        self.assertEqual(sim.base_stations[6], 1)

        # Step 10 hand over events
        # The last hadover should be droped
        for i in range(10):
            sim.step()

        self.assertEqual(sim.blocked_calls, 1)
        self.assertEqual(sim.dropped_calls, 1)
        self.assertEqual(sim.completed_calls, 0)
        self.assertEqual(sim.base_stations[6], 10)
        self.assertEqual(sim.base_stations[5], 0)

        for i in range(10):
            sim.step()

        self.assertEqual(sim.blocked_calls, 1)
        self.assertEqual(sim.dropped_calls, 1)
        self.assertEqual(sim.completed_calls, 9)
        self.assertEqual(sim.base_stations[7], 1)
        self.assertEqual(sim.base_stations[6], 0)
        self.assertEqual(sim.base_stations[5], 0)
        self.assertEqual(len(sim.event_list), 1)
        self.assertEqual(sim.clock, 7200+8) # 7209 was blocked and 7210 was dropped

        sim.step()
        self.assertEqual(sim.blocked_calls, 1)
        self.assertEqual(sim.dropped_calls, 1)
        self.assertEqual(sim.completed_calls, 10)
        self.assertEqual(sim.base_stations[7], 0)
        self.assertEqual(len(sim.event_list), 0)
        self.assertEqual(sim.clock, 7211)

    def test_short_simulation_1_reserve(self):
        """Test a short simulation run with 1 reserved channel"""
        sim = Simulator(self.mock_generator, _no_initial_event=True, channel_reserved_for_handover=1, _no_new_initialisation=True)
        
        # Add 11 call initiation events
        # first 9 will be accepted, the 10th and 11th will be blocked
        for i in range(11):
            sim.add_event(
                i,
                EventType.CALL_INITIATION,
                Car(_id=i, velocity=2/3.6, position=0.0, station=5, call_duration=7200)
            )
            sim.step()

        self.assertEqual(sim.blocked_calls, 2)
        self.assertEqual(len(sim.event_list), 9)
        self.assertEqual(sim.clock, 10) # 0,1,2, ... 10 = 11 events

        # Add a car to base station 6
        sim.add_event(
            11,
            EventType.CALL_INITIATION,
            Car(_id=11, velocity=2/3.6, position=-20, station=6, call_duration=7200)
        )
        sim.step()

        self.assertEqual(sim.base_stations[5], 9)
        self.assertEqual(sim.base_stations[6], 1)

        # Step 9 hand over events
        # No hadover should be dropped
        for i in range(9):
            sim.step()

        self.assertEqual(sim.blocked_calls, 2)
        self.assertEqual(sim.dropped_calls, 0)
        self.assertEqual(sim.completed_calls, 0)
        self.assertEqual(sim.base_stations[6], 10)
        self.assertEqual(sim.base_stations[5], 0)

        for i in range(10):
            sim.step()

        self.assertEqual(sim.blocked_calls, 2)
        self.assertEqual(sim.dropped_calls, 0)
        self.assertEqual(sim.completed_calls, 9)
        self.assertEqual(sim.base_stations[7], 1)
        self.assertEqual(sim.base_stations[6], 0)
        self.assertEqual(sim.base_stations[5], 0)
        self.assertEqual(len(sim.event_list), 1)
        self.assertEqual(sim.clock, 7200+8) # 7209 was blocked and 7210 was dropped

        sim.step()
        self.assertEqual(sim.blocked_calls, 2)
        self.assertEqual(sim.dropped_calls, 0)
        self.assertEqual(sim.completed_calls, 10)
        self.assertEqual(sim.base_stations[7], 0)
        self.assertEqual(len(sim.event_list), 0)
        self.assertEqual(sim.clock, 7211)

if __name__ == '__main__':
    unittest.main()