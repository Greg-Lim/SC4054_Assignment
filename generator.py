import numpy as np
import yaml
from typing import Dict, Any, Optional


class Generator:
    """
    Generator class that yields values based on different probability distributions
    using parameters from a YAML file.
    """

    def __init__(self, params_file: str = 'params.yaml', seed: Optional[int] = None):
        """
        Initialize the generator with parameters from a YAML file and optional seed.
        
        Args:
            params_file: Path to the YAML file containing distribution parameters
            seed: Random seed for reproducibility
        """
        self.params = self._load_params(params_file)
        self.rng = np.random.RandomState(seed)

        # Extract and store parameters for faster access
        self.call_duration_x0 = self.params['call_duration']['x0']
        self.call_duration_lambda = self.params['call_duration']['lambda']

        self.inter_arrival_time_lambda = self.params['inter_arrival_time']['lambda']

        self.velocity_mu = self.params['velocity']['mu']
        self.velocity_variance = self.params['velocity']['variance']

        self.base_station_min = self.params['base_station']['min']
        self.base_station_max = self.params['base_station']['max']

        self.position_min = self.params['position']['min']
        self.position_max = self.params['position']['max']

    def _load_params(self, params_file: str) -> Dict[str, Any]:
        """Load parameters from YAML file."""
        with open(params_file, 'r') as file:
            return yaml.safe_load(file)

    def generate_call_duration(self) -> float:
        """Generate call duration based on shifted exponential distribution. (Seconds)"""
        return self.call_duration_x0 + self.rng.exponential(1.0 / self.call_duration_lambda)

    def generate_inter_arrival_time(self) -> float:
        """Generate inter-arrival time based on exponential distribution. (Seconds)"""
        return self.rng.exponential(1.0 / self.inter_arrival_time_lambda)

    def generate_velocity(self) -> float:
        """Generate velocity based on normal distribution. (Km/h)"""
        return self.rng.normal(self.velocity_mu, np.sqrt(self.velocity_variance))

    def generate_base_station(self) -> int:
        """Generate base station based on uniform discrete distribution."""
        return self.rng.randint(self.base_station_min, self.base_station_max + 1)
    
    def generate_position(self) -> float:
        """Generate position based on uniform continuous distribution. (Km)"""
        return self.rng.uniform(self.position_min, self.position_max)

    def generate_direction(self) -> int:
        """Generate direction as either -1 or 1."""
        return self.rng.choice([-1, 1])

if __name__ == "__main__":
    # Example usage
    gen = Generator(seed=42)
    
    print("Sample values:")
    print(f"Call Duration: {gen.generate_call_duration():.2f} seconds")
    print(f"Inter-arrival Time: {gen.generate_inter_arrival_time():.2f} seconds")
    print(f"Velocity: {gen.generate_velocity():.2f} km/h")
    print(f"Base Station: {gen.generate_base_station()}")
    print(f"Position: {gen.generate_position():.2f} km")
    print(f"Direction: {gen.generate_direction()}")
    
    # Generate multiple samples
    print("\nMultiple samples:")
    for i in range(5):
        print(f"Sample {i+1}:")
        print(f"  Call Duration: {gen.generate_call_duration():.2f} seconds")
        print(f"  Inter-arrival Time: {gen.generate_inter_arrival_time():.2f} seconds")
        print(f"  Velocity: {gen.generate_velocity():.2f} km/h")
        print(f"  Base Station: {gen.generate_base_station()}")
        print(f"  Position: {gen.generate_position():.2f} km")
        print(f"  Direction: {gen.generate_direction()}")
