import unittest
import sys
import os
import time

# Add parent directory to path to import simulator and generator
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from simulator import Simulator, NUMBER_OF_BASE_STATIONS
from generator import Generator


class TestLongSimulations(unittest.TestCase):
    
    def test_all_channels_return_to_zero_1(self):
        """
        Test that runs the simulator for 100 steps using the real generator,
        then sets _no_new_initialisation to True and verifies that all base station
        channel counts return to 0 after processing all remaining events.
        """
        # Create a simulator with a real generator (not mocked)
        gen = Generator(seed=6)  # Use a fixed seed for reproducibility
        sim = Simulator(gen)
        
        # Run the simulation for 1 steps
        print(f"Running first 1 steps...")
        start_time = time.time()
        for _ in range(1):
            sim.step()
        first_phase_time = time.time() - start_time
        print(f"First 1 steps completed in {first_phase_time:.2f} seconds")
        
        # Report the current state
        busy_stations = sum(1 for count in sim.base_stations if count > 0)
        total_channels_in_use = sum(sim.base_stations)
        print(f"Current state after 1 steps:")
        print(f"- Base stations with active calls: {busy_stations}/{NUMBER_OF_BASE_STATIONS}")
        print(f"- Total channels in use: {total_channels_in_use}")
        print(f"- Events remaining in queue: {len(sim.event_list)}")
        print(f"- Simulation clock: {sim.clock:.2f}")
        
        # Set no_new_initialisation to True to prevent new call initiations
        sim._no_new_initialisation = True
        
        # Run until event list is empty or we hit a maximum step count
        max_steps = 10000  # Safety limit
        step_count = 0
        
        print(f"Running remaining events with no new initiations...")
        start_time = time.time()
        while len(sim.event_list) > 0 and step_count < max_steps:
            sim.step()
            step_count += 1
        second_phase_time = time.time() - start_time
        
        print(f"Processed {step_count} additional steps in {second_phase_time:.2f} seconds")
        print(f"Final simulation clock: {sim.clock:.2f}")
        print(f"Final statistics:")
        print(f"- Blocked calls: {sim.blocked_calls}")
        print(f"- Dropped calls: {sim.dropped_calls}")
        print(f"- Completed calls: {sim.completed_calls}")
        
        # Verify all base stations have 0 channels in use
        for i, channel_count in enumerate(sim.base_stations):
            self.assertEqual(
                channel_count, 0, 
                f"Base station {i} still has {channel_count} channels in use"
            )
        
        # Verify no events are left
        self.assertEqual(len(sim.event_list), 0, "Event list should be empty")

    def test_all_channels_return_to_zero_1000(self):
        """
        Test that runs the simulator for 1000 steps using the real generator,
        then sets _no_new_initialisation to True and verifies that all base station
        channel counts return to 0 after processing all remaining events.
        """
        # Create a simulator with a real generator (not mocked)
        gen = Generator(seed=42)  # Use a fixed seed for reproducibility
        sim = Simulator(gen)
        
        # Run the simulation for 1 steps
        print(f"Running first 1 steps...")
        start_time = time.time()
        for _ in range(1000):
            sim.step()
        first_phase_time = time.time() - start_time
        print(f"First 1000 steps completed in {first_phase_time:.2f} seconds")
        
        # Report the current state
        busy_stations = sum(1 for count in sim.base_stations if count > 0)
        total_channels_in_use = sum(sim.base_stations)
        print(f"Current state after 1000 steps:")
        print(f"- Base stations with active calls: {busy_stations}/{NUMBER_OF_BASE_STATIONS}")
        print(f"- Total channels in use: {total_channels_in_use}")
        print(f"- Events remaining in queue: {len(sim.event_list)}")
        print(f"- Simulation clock: {sim.clock:.2f}")
        
        # Set no_new_initialisation to True to prevent new call initiations
        sim._no_new_initialisation = True
        
        # Run until event list is empty or we hit a maximum step count
        max_steps = 10000  # Safety limit
        step_count = 0
        
        print(f"Running remaining events with no new initiations...")
        start_time = time.time()
        while len(sim.event_list) > 0 and step_count < max_steps:
            sim.step()
            step_count += 1
        second_phase_time = time.time() - start_time
        
        print(f"Processed {step_count} additional steps in {second_phase_time:.2f} seconds")
        print(f"Final simulation clock: {sim.clock:.2f}")
        print(f"Final statistics:")
        print(f"- Blocked calls: {sim.blocked_calls}")
        print(f"- Dropped calls: {sim.dropped_calls}")
        print(f"- Completed calls: {sim.completed_calls}")
        
        # Verify all base stations have 0 channels in use
        for i, channel_count in enumerate(sim.base_stations):
            self.assertEqual(
                channel_count, 0, 
                f"Base station {i} still has {channel_count} channels in use"
            )
        
        # Verify no events are left
        self.assertEqual(len(sim.event_list), 0, "Event list should be empty")

if __name__ == '__main__':
    unittest.main()