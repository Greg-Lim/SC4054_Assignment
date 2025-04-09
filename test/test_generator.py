import unittest
import sys
import os
import numpy as np
from collections import Counter

# Add parent directory to path to import Generator class
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from generator import Generator


class TestGenerator(unittest.TestCase):
    """Test cases for the Generator class"""
    
    def setUp(self):
        """Set up test fixtures before each test method"""
        # Using a fixed seed for deterministic tests
        self.generator = Generator(seed=42)
        
    def test_call_duration(self):
        """Test call duration generation"""
        # Generate multiple call durations
        durations = [self.generator.generate_call_duration() for _ in range(1000)]
        
        # Test that all values are greater than or equal to x0
        self.assertTrue(all(duration >= self.generator.call_duration_x0 for duration in durations))
        
        # Test statistical properties (approximately)
        self.assertGreater(np.mean(durations), self.generator.call_duration_x0)
        
    def test_inter_arrival_time(self):
        """Test inter-arrival time generation"""
        # Generate multiple inter-arrival times
        times = [self.generator.generate_inter_arrival_time() for _ in range(1000)]
        
        # Test that all values are positive
        self.assertTrue(all(time > 0 for time in times))
        
        # Test statistical properties (approximately)
        mean_time = np.mean(times)
        expected_mean = 1.0 / self.generator.inter_arrival_time_lambda
        # Allow for some deviation due to random sampling
        self.assertAlmostEqual(mean_time, expected_mean, delta=expected_mean*0.2)
        
    def test_velocity(self):
        """Test velocity generation"""
        # Generate multiple velocities
        velocities = [self.generator.generate_velocity() for _ in range(1000)]
        
        # Test statistical properties (approximately)
        mean_velocity = np.mean(velocities)
        std_velocity = np.std(velocities)
        self.assertAlmostEqual(mean_velocity, self.generator.velocity_mu, delta=1.0)
        self.assertAlmostEqual(std_velocity**2, self.generator.velocity_variance, delta=1.0)
        
    def test_base_station(self):
        """Test base station generation"""
        # Generate multiple base stations
        stations = [self.generator.generate_base_station() for _ in range(1000)]
        
        # Test that all values are within the specified range
        self.assertTrue(all(self.generator.base_station_min <= station <= self.generator.base_station_max 
                           for station in stations))
        
        # Test that all values are integers
        self.assertTrue(all(isinstance(station, (int, np.integer)) for station in stations))
    
    def test_position(self):
        """Test position generation"""
        # Generate multiple positions
        positions = [self.generator.generate_position() for _ in range(100000)]
        
        # Test that all values are within the specified range
        self.assertTrue(all(self.generator.position_min <= position <= self.generator.position_max 
                           for position in positions))
        
        # Test statistical properties of uniform distribution
        mean_position = np.mean(positions)
        expected_mean = (self.generator.position_min + self.generator.position_max) / 2
        # Allow for some deviation due to random sampling
        self.assertAlmostEqual(mean_position, expected_mean, delta=(self.generator.position_max - self.generator.position_min)*0.01)
        
        # Test uniformity by checking that values span the entire range
        self.assertLess(min(positions), self.generator.position_min + (self.generator.position_max - self.generator.position_min) * 0.1)
        self.assertGreater(max(positions), self.generator.position_max - (self.generator.position_max - self.generator.position_min) * 0.1)
    
    def test_direction(self):
        """Test direction generation"""
        # Generate multiple directions
        directions = [self.generator.generate_direction() for _ in range(1000)]
        
        # Test that all values are either -1 or 1
        self.assertTrue(all(direction in [-1, 1] for direction in directions))
        self.assertAlmostEqual(np.mean(directions), 0, delta=0.1)

    def test_cell_distribution_extremes(self):
        """Test that cells 0 and 19 can be generated"""
        # Generate a large number of cells to ensure extremes are covered
        cells = [self.generator.generate_base_station() for _ in range(1000)]
        
        # Count occurrences of each cell
        cell_counts = Counter(cells)
        
        # Check that both cell 0 and cell 19 have been generated
        self.assertIn(0, cell_counts)
        self.assertIn(19, cell_counts)
            
    def test_reproducibility(self):
        """Test that generator is reproducible with the same seed"""
        gen1 = Generator(seed=123)
        gen2 = Generator(seed=123)
        
        # Generate values from both generators and compare
        for _ in range(10):
            self.assertEqual(gen1.generate_call_duration(), gen2.generate_call_duration())
            self.assertEqual(gen1.generate_inter_arrival_time(), gen2.generate_inter_arrival_time())
            self.assertEqual(gen1.generate_velocity(), gen2.generate_velocity())
            self.assertEqual(gen1.generate_base_station(), gen2.generate_base_station())
            self.assertEqual(gen1.generate_position(), gen2.generate_position())


if __name__ == "__main__":
    unittest.main()