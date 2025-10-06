"""BeePop+ Global Configuration Options Module.

This module contains the GlobalOptions singleton class that manages simulation-wide
configuration parameters. These options control various aspects of colony behavior,
environmental responses, and computational algorithms throughout the simulation.

Global options provide centralized control over model parameters such as aging
algorithms, foraging thresholds, weather processing methods, and output formatting.
This allows for consistent behavior across all simulation components and easy
parameter adjustment for sensitivity analysis or model calibration.

The singleton pattern ensures all simulation components access the same configuration
state, preventing inconsistencies in model behavior across different subsystems.

Classes:
    GlobalOptions: Singleton configuration manager for simulation-wide parameters
"""


class GlobalOptions:
    """Singleton configuration manager for simulation-wide behavioral parameters.

    Manages global configuration options that control various aspects of the
    colony simulation including aging algorithms, environmental thresholds,
    foraging behavior, and output formatting. Provides centralized parameter
    control for consistent model behavior.

    Global options influence how bees respond to environmental conditions, when
    aging algorithms are applied, how weather data is processed, and what
    outputs are generated. These parameters allow for model calibration and
    sensitivity analysis across different scenarios.

    Attributes:
        daylight_hours_threshold (float): Minimum daylight hours for egg laying
        should_adults_age_based_laid_eggs (bool): Whether adult aging depends on egg laying
        should_forage_day_election_based_on_temperatures (bool): Temperature-based foraging
        windspeed_threshold (float): Maximum wind speed for foraging activity
        rainfall_threshold (float): Maximum rainfall for foraging activity
        should_compute_hourly_temperature_estimation (bool): Hourly temperature calculations
        should_foragers_always_age_based_on_forage_inc (bool): Forager aging algorithm
        adult_aging_delay_egg_threshold (float): Egg threshold for aging delays
        should_output_in_out_counts (bool): Whether to output detailed transition counts
    """

    # Singleton instance
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GlobalOptions, cls).__new__(cls)
            cls._instance._initialize_defaults()
        return cls._instance

    def _initialize_defaults(self):
        # Egg laying options
        self.daylight_hours_threshold = 9.5

        # Adult aging options
        self.should_adults_age_based_laid_eggs = True

        # Forager aging options
        self.should_forage_day_election_based_on_temperatures = False
        self.windspeed_threshold = 8.94
        self.rainfall_threshold = 0.197
        self.should_compute_hourly_temperature_estimation = True
        self.should_foragers_always_age_based_on_forage_inc = True
        self.adult_aging_delay_egg_threshold = 50.0

        # Weather file options
        self.binary_weather_file_format_identifier = ""

        # Additional Output Data
        self.should_output_in_out_counts = False

    # Example: get the singleton instance
    @staticmethod
    def get():
        return GlobalOptions()


# Usage:
# options = GlobalOptions.get()
# print(options.daylight_hours_threshold)
