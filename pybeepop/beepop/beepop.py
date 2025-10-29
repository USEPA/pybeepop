"""BeePop+ Python Interface Module.

This module provides the main Python interface to the BeePop+ bee colony simulation system.
It serves as a port of the C++ VPopLib library, offering equivalent functionality for
modeling honey bee colony dynamics, population growth, and environmental interactions.

The module is designed to mirror the C++ API while leveraging Python's strengths for
data analysis and scientific computing.

Architecture Overview:
    The BeePop+ system follows a hierarchical architecture:

    BeePop (Main Interface)
    └── VarroaPopSession (Simulation Manager)
        ├── Colony (Core Colony Simulation)
        │   ├── Queen (Egg laying and colony leadership)
        │   ├── Adult Bees (Workers, Drones, Foragers)
        │   ├── Brood (Developing bees)
        │   ├── Larvae (Larval stage bees)
        │   └── Eggs (Egg stage)
        ├── WeatherEvents (Environmental conditions)
        ├── MiteTreatments (Varroa mite management)
        └── NutrientContaminationTable (Pesticide/toxin tracking)

Main Classes:
    BeePop: Primary interface class for simulation management
    SNCElement: Nutrient contamination data element

Key Features:
    - Complete bee lifecycle simulation (egg → larva → pupa → adult)
    - Varroa mite population dynamics and treatment modeling
    - Weather-driven foraging and development
    - Pesticide exposure and mortality tracking
    - Resource management (pollen, nectar)
    - Queen replacement events

Example:
    Basic simulation setup and execution:

    >>> beepop = BeePop()
    >>> beepop.set_latitude(40.0)  # Set location
    >>> beepop.initialize_model()  # Initialize colony
    >>> beepop.set_weather_from_file("weather.txt")  # Load weather
    >>> beepop.run_simulation()  # Execute simulation
    >>> success, results = beepop.get_results()  # Get output

Version:
    1/15/2025 - Python port of BeePop+ C++ library

Notes:
    This Python implementation maintains compatibility with the original C++
    VPopLib API while adding Python-specific enhancements for data handling
    and analysis integration.
"""

from datetime import datetime
import re
import io
import pandas as pd
from typing import List, Tuple, Optional, Any
from pybeepop.beepop.session import VarroaPopSession
from pybeepop.beepop.colony import Colony
from pybeepop.beepop.weatherevents import Event, WeatherEvents
from pybeepop.beepop.nutrientcontaminationtable import (
    SNCElement,
    NutrientContaminationTable,
)

BEEPOP_VERSION = "1/15/2025"


class BeePop:
    """Main interface class for BeePop+ bee colony simulation.

    This class provides the primary Python interface to the BeePop+ simulation system,
    equivalent to the C++ VPopLib interface. It manages the underlying simulation
    session, colony dynamics, weather conditions, and provides methods for
    configuration, execution, and results retrieval.

    The BeePop class acts as an interface for high-level interaction with the complex
    underlying bee colony simulation system, handling session management,
    parameter validation, and data formatting.

    Attributes:
        session (VarroaPopSession): The underlying simulation session that manages
            all colony dynamics, weather events, and simulation state.

    Example:
        Basic simulation workflow:

        >>> # Initialize simulation
        >>> beepop = BeePop()
        >>> beepop.set_latitude(39.5)  # Set geographic location
        >>> beepop.initialize_model()  # Initialize colony model

        >>> # Configure simulation parameters
        >>> params = ["ICWorkerAdults=25000", "SimStart=06/01/2024"]
        >>> beepop.set_ic_variables_v(params)

        >>> # Load environmental data
        >>> beepop.set_weather_from_file("weather_data.txt")

        >>> # Execute simulation
        >>> success = beepop.run_simulation()
        >>> if success:
        ...     success, results = beepop.get_results()
        ...     print(f"Simulation completed with {len(results)} data points")

    Note:
        This class is designed to be thread-safe for individual instances,
        but multiple BeePop instances should not share session data.
    """

    def __init__(self):
        """Initialize a new BeePop+ simulation session.

        Creates a new simulation session with default settings, initializing
        the underlying VarroaPopSession and setting up the colony and weather
        management systems.

        Raises:
            RuntimeError: If session initialization fails due to system constraints
                or missing dependencies.
        """
        self.session = VarroaPopSession()
        self._initialize_session()

    def _initialize_session(self):
        """Set up the session with default colony and weather objects.

        Internal method that ensures the session has properly initialized
        Colony and WeatherEvents objects. This method is called automatically
        during BeePop initialization.

        Note:
            This is an internal method and should not be called directly by users.
        """
        # Create colony if not present
        if not hasattr(self.session, "colony") or self.session.colony is None:
            self.session.colony = Colony()

        # Create weather if not present
        if not hasattr(self.session, "weather") or self.session.weather is None:
            self.session.weather = WeatherEvents()

    # Helper methods for session access
    def _get_colony(self):
        """Get the colony object."""
        return getattr(self.session, "colony", None)

    def _get_weather(self):
        """Get the weather object."""
        return getattr(self.session, "weather", None)

    def _clear_error_list(self):
        """Clear the error list."""
        if hasattr(self.session, "clear_error_list"):
            self.session.clear_error_list()

    def _clear_info_list(self):
        """Clear the info list."""
        if hasattr(self.session, "clear_info_list"):
            self.session.clear_info_list()

    def _add_to_error_list(self, msg: str):
        """Add message to error list."""
        if hasattr(self.session, "add_to_error_list"):
            self.session.add_to_error_list(msg)

    def _add_to_info_list(self, msg: str):
        """Add message to info list."""
        if hasattr(self.session, "add_to_info_list"):
            self.session.add_to_info_list(msg)

    def _is_error_reporting_enabled(self) -> bool:
        """Check if error reporting is enabled."""
        if hasattr(self.session, "is_error_reporting_enabled"):
            return self.session.is_error_reporting_enabled()
        return True

    def _is_info_reporting_enabled(self) -> bool:
        """Check if info reporting is enabled."""
        if hasattr(self.session, "is_info_reporting_enabled"):
            return self.session.is_info_reporting_enabled()
        return True

    # Core Interface Methods

    def initialize_model(self) -> bool:
        """Initialize the colony simulation model.

        Port of the C++ InitializeModel() function. This method sets up the
        colony for simulation by calling the colony's create() method and
        clearing any existing error or info messages.

        This must be called before running a simulation to ensure the colony
        is properly initialized with default or previously set parameters.

        Returns:
            bool: True if initialization successful, False if any errors occurred.

        Example:
            >>> beepop = BeePop()
            >>> if beepop.initialize_model():
            ...     print("Model initialized successfully")
            ... else:
            ...     print("Model initialization failed")

        Note:
            After calling this method, the colony will be reset to initial
            conditions. Any previous simulation state will be lost.
        """
        try:
            colony = self._get_colony()
            if colony and hasattr(colony, "create"):
                colony.create()
            self._clear_error_list()
            self._clear_info_list()
            return True
        except Exception as e:
            self._add_to_error_list(f"Failed to initialize model: {str(e)}")
            return False

    def clear_results_buffer(self) -> bool:
        """
        Port of ClearResultsBuffer().
        Clear the results text buffer.

        Returns:
            bool: True if successful
        """
        try:
            if hasattr(self.session, "clear_results"):
                self.session.clear_results()
            elif hasattr(self.session, "results_text"):
                if hasattr(self.session.results_text, "clear"):
                    self.session.results_text.clear()
                elif hasattr(self.session.results_text, "RemoveAll"):
                    self.session.results_text.RemoveAll()
            return True
        except Exception:
            return False

    def set_latitude(self, lat: float) -> bool:
        """Set the geographic latitude for the simulation.

        Port of the C++ SetLatitude() function. The latitude affects daylight
        hours calculation, which influences bee foraging behavior, brood
        development rates, and overall colony dynamics.

        Args:
            lat (float): Latitude in decimal degrees. Positive values for
                northern hemisphere, negative for southern hemisphere.
                Valid range: -90.0 to +90.0 degrees.

        Returns:
            bool: True if latitude was set successfully, False otherwise.

        Example:
            >>> beepop = BeePop()
            >>> beepop.set_latitude(40.7)  # New York City latitude
            >>> beepop.set_latitude(-33.9)  # Sydney, Australia latitude

        Note:
            If weather data is already loaded, daylight hours will be
            automatically recalculated for the new latitude. This ensures
            consistency between geographic location and environmental conditions.
        """
        try:
            if hasattr(self.session, "set_latitude"):
                self.session.set_latitude(lat)
            else:
                self.session.latitude = lat

            # Update daylight hours for existing weather events if weather is loaded
            if (
                hasattr(self.session, "is_weather_loaded")
                and self.session.is_weather_loaded()
            ):
                weather = self._get_weather()
                if weather and hasattr(weather, "update_daylight_for_latitude"):
                    weather.update_daylight_for_latitude(lat)
            return True
        except Exception:
            return False

    def get_latitude(self) -> Tuple[bool, float]:
        """
        Port of GetLatitude().
        Get the current simulation latitude.

        Returns:
            Tuple[bool, float]: (success, latitude)
        """
        try:
            if hasattr(self.session, "get_latitude"):
                lat = self.session.get_latitude()
            else:
                lat = getattr(self.session, "latitude", 0.0)
            return True, lat
        except Exception:
            return False, 0.0

    # Parameter File Loading Methods

    def load_parameter_file(self, file_path: str) -> bool:
        """
        Load parameters from a text file containing key=value pairs.

        This functionality is not present in the C++ library - it's added
        for compatibility with PyBeePop's parameter file loading capability.

        The file should contain lines in the format:
        ParameterName=ParameterValue

        Args:
            file_path: Path to the parameter file

        Returns:
            bool: True if file was loaded and parameters set successfully
        """
        try:
            with open(file_path, "r") as f:
                lines = f.readlines()

            # Parse lines into key=value pairs (matching PyBeePop implementation)
            parameter_pairs = []
            for line in lines:
                # Remove whitespace and newlines, skip empty lines and comments
                clean_line = line.replace(" ", "").replace("\n", "").strip()
                if clean_line and not clean_line.startswith("#") and "=" in clean_line:
                    parameter_pairs.append(clean_line)

            if not parameter_pairs:
                if self._is_error_reporting_enabled():
                    self._add_to_error_list(
                        f"No valid parameters found in file: {file_path}"
                    )
                return False

            # Use existing set_ic_variables_v method to set all parameters
            success = self.set_ic_variables_v(parameter_pairs, reset_ics=False)

            if success:
                if self._is_info_reporting_enabled():
                    self._add_to_info_list(
                        f"Loaded {len(parameter_pairs)} parameters from {file_path}"
                    )
            else:
                if self._is_error_reporting_enabled():
                    self._add_to_error_list(
                        f"Failed to load parameters from {file_path}"
                    )

            return success

        except FileNotFoundError:
            if self._is_error_reporting_enabled():
                self._add_to_error_list(f"Parameter file not found: {file_path}")
            return False
        except Exception as e:
            if self._is_error_reporting_enabled():
                self._add_to_error_list(
                    f"Error loading parameter file {file_path}: {str(e)}"
                )
            return False

    # Initial Conditions Methods

    def set_ic_variables_s(self, name: str, value: str) -> bool:
        """
        Port of SetICVariablesS().
        Set initial condition variable by name and value strings.

        Args:
            name: Parameter name
            value: Parameter value as string

        Returns:
            bool: True if successful
        """
        try:
            success = False
            if hasattr(self.session, "update_colony_parameters"):
                success = self.session.update_colony_parameters(name, value)
            else:
                # Fallback: try to set attribute directly on colony
                colony = self._get_colony()
                if colony and hasattr(colony, name):
                    setattr(colony, name, value)
                    success = True

            if success:
                if self._is_info_reporting_enabled():
                    self._add_to_info_list(
                        f"Setting Variables. Name = {name} Value = {value}"
                    )
                return True
            else:
                if self._is_error_reporting_enabled():
                    self._add_to_error_list(f"Failed to set {name} to {value}")
                return False
        except Exception as e:
            if self._is_error_reporting_enabled():
                self._add_to_error_list(
                    f"Exception setting {name} to {value}: {str(e)}"
                )
            return False

    def set_ic_variables_v(self, nv_pairs: List[str], reset_ics: bool = True) -> bool:
        """
        Port of SetICVariablesV().
        Set initial condition variables from list of name=value pairs.

        Args:
            nv_pairs: List of "name=value" strings
            reset_ics: Whether to reset initial conditions first

        Returns:
            bool: True if successful
        """
        try:
            if reset_ics:
                # Clear date range value lists before loading new ICs
                colony = self.session.get_colony()
                if colony and hasattr(colony, "m_init_cond"):
                    # Clear DRVs if they exist
                    for drv_name in [
                        "m_AdultLifespanDRV",
                        "m_ForagerLifespanDRV",
                        "m_EggTransitionDRV",
                        "m_BroodTransitionDRV",
                        "m_LarvaeTransitionDRV",
                        "m_AdultTransitionDRV",
                    ]:
                        if hasattr(colony.m_init_cond, drv_name):
                            drv = getattr(colony.m_init_cond, drv_name)
                            if hasattr(drv, "clear_all"):
                                drv.clear_all()

                    # Clear mite treatment info
                    if hasattr(colony, "m_mite_treatment_info"):
                        if hasattr(colony.m_mite_treatment_info, "clear_all"):
                            colony.m_mite_treatment_info.clear_all()

            success = True
            for pair in nv_pairs:
                eq_pos = pair.find("=")
                if (
                    eq_pos > 0
                ):  # Equals sign must be present with at least one character before it
                    name = pair[:eq_pos].strip()
                    value = pair[eq_pos + 1 :].strip()
                    if not self.set_ic_variables_s(name, value):
                        success = False
                else:
                    if self.session.is_error_reporting_enabled():
                        self.session.add_to_error_list(
                            f"Invalid name=value pair: {pair}"
                        )
                    success = False

            return success
        except Exception as e:
            if self.session.is_error_reporting_enabled():
                self.session.add_to_error_list(
                    f"Exception in set_ic_variables_v: {str(e)}"
                )
            return False

    # Weather Methods

    def set_weather_s(self, weather_event_string: str) -> bool:
        """
        Port of SetWeatherS().
        Set weather from a single weather event string.

        Args:
            weather_event_string: Weather string in format: "Date,MaxTemp,MinTemp,AvgTemp,Windspeed,Rainfall,DaylightHours"

        Returns:
            bool: True if successful
        """
        try:
            weather_events = self._get_weather()
            event = self._weather_string_to_event(weather_event_string)

            if event and weather_events:
                if hasattr(event, "update_forage_attribute_for_event") and hasattr(
                    self.session, "get_latitude"
                ):
                    event.update_forage_attribute_for_event(
                        self.session.get_latitude(), getattr(event, "windspeed", 0.0)
                    )
                if hasattr(weather_events, "add_event"):
                    weather_events.add_event(event)
                return True
            else:
                if self._is_error_reporting_enabled():
                    self._add_to_error_list(
                        f"Bad Weather String Format: {weather_event_string}"
                    )
                return False
        except Exception as e:
            if self._is_error_reporting_enabled():
                self._add_to_error_list(f"Exception in set_weather_s: {str(e)}")
            return False

    def set_weather_v(self, weather_event_string_list: List[str]) -> bool:
        """
        Port of SetWeatherV().
        Set weather from a list of weather event strings.

        Args:
            weather_event_string_list: List of weather strings

        Returns:
            bool: True if all successful
        """
        try:
            success = True
            for weather_str in weather_event_string_list:
                if not self.set_weather_s(weather_str):
                    success = False
                    break

            weather = self.session.get_weather()
            if weather and weather.get_total_events() > 0:
                # Only set simulation dates from weather if they haven't been explicitly set
                # This preserves user-defined SimStart/SimEnd parameters
                if (
                    not hasattr(self.session, "_sim_dates_explicitly_set")
                    or not self.session._sim_dates_explicitly_set
                ):
                    self.session.set_sim_start(weather.get_beginning_time())
                    self.session.set_sim_end(weather.get_ending_time())
                weather.set_initialized(True)
            else:
                success = False

            return success
        except Exception as e:
            if self.session.is_error_reporting_enabled():
                self.session.add_to_error_list(f"Exception in set_weather_v: {str(e)}")
            return False

    def clear_weather(self) -> bool:
        """
        Port of ClearWeather().
        Clear all weather events.

        Returns:
            bool: True if successful
        """
        try:
            weather = self.session.get_weather()
            if weather:
                weather.clear_all_events()
            return True
        except Exception:
            return False

    def set_weather_from_file(self, file_path: str, delimiter: str = None) -> bool:
        """
        Helper method to load weather data from a CSV or tab-separated file.

        Args:
            file_path: Path to the weather file
            delimiter: Field delimiter (auto-detected if None). Common values: ',' or '\t'

        Returns:
            bool: True if successful

        The file should contain weather data in the format:
        Date,MaxTemp,MinTemp,AvgTemp,Windspeed,Rainfall,DaylightHours

        Date can be in MM/DD/YYYY or MM-DD-YYYY format.
        Temperatures should be in Celsius.
        Windspeed in km/h, Rainfall in mm, DaylightHours as decimal hours.
        """
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                lines = file.readlines()

            if not lines:
                if self._is_error_reporting_enabled():
                    self._add_to_error_list(f"Weather file is empty: {file_path}")
                return False

            # Auto-detect delimiter if not specified
            if delimiter is None:
                first_line = lines[0].strip()
                if "\t" in first_line:
                    delimiter = "\t"
                elif "," in first_line:
                    delimiter = ","
                else:
                    if self._is_error_reporting_enabled():
                        self._add_to_error_list(
                            f"Cannot auto-detect delimiter in weather file: {file_path}"
                        )
                    return False

            # Process each line and convert to weather event strings
            weather_strings = []
            for line_num, line in enumerate(lines, 1):
                line = line.strip()
                if not line:  # Skip empty lines
                    continue

                try:
                    # Split by delimiter and clean up whitespace
                    fields = [field.strip() for field in line.split(delimiter)]

                    if len(fields) < 6:
                        if self._is_error_reporting_enabled():
                            self._add_to_error_list(
                                f"Insufficient fields in line {line_num}: {line} (expected at least 6 fields)"
                            )
                        return False

                    # Take first 7 fields (Date, MaxTemp, MinTemp, AvgTemp, Windspeed, Rainfall, DaylightHours)
                    # If only 6 fields, we'll let the weather parsing handle the missing daylight hours
                    weather_fields = fields[:7] if len(fields) >= 7 else fields[:6]

                    # Rejoin with commas for the weather string format expected by set_weather_s
                    weather_string = ",".join(weather_fields)
                    weather_strings.append(weather_string)

                except Exception as e:
                    if self._is_error_reporting_enabled():
                        self._add_to_error_list(
                            f"Error parsing line {line_num}: {line} - {str(e)}"
                        )
                    return False

            # Use set_weather_v to process all weather strings
            return self.set_weather_v(weather_strings)

        except FileNotFoundError:
            if self._is_error_reporting_enabled():
                self._add_to_error_list(f"Weather file not found: {file_path}")
            return False
        except Exception as e:
            if self._is_error_reporting_enabled():
                self._add_to_error_list(f"Exception in set_weather_from_file: {str(e)}")
            return False

    # Contamination Table Methods

    def set_contamination_table(self, contamination_table_list: List[str]) -> bool:
        """
        Port of SetContaminationTable().
        Set contamination table from list of strings.

        Args:
            contamination_table_list: List of "Date,NectarConc,PollenConc" strings

        Returns:
            bool: True if any items were added successfully
        """
        try:
            success = False
            if len(contamination_table_list) > 0:
                colony = self.session.get_colony()
                if colony and hasattr(colony, "m_nutrient_ct"):
                    colony.m_nutrient_ct.remove_all()

                    for ct_record in contamination_table_list:
                        element = self._string_to_nutrient_element(ct_record)
                        if element:
                            colony.m_nutrient_ct.add_contaminant_conc(element)
                            success = True  # Set true if any items are added

                    # Enable contamination table if any items were added successfully
                    if success:
                        colony.m_nutrient_ct.nutrient_cont_enabled = True

            return success
        except Exception as e:
            if self.session.is_error_reporting_enabled():
                self.session.add_to_error_list(
                    f"Exception in set_contamination_table: {str(e)}"
                )
            return False

    def clear_contamination_table(self) -> bool:
        """
        Port of ClearContaminationTable().
        Clear the contamination table.

        Returns:
            bool: True if successful
        """
        try:
            colony = self.session.get_colony()
            if colony and hasattr(colony, "m_nutrient_ct"):
                colony.m_nutrient_ct.remove_all()
            return True
        except Exception:
            return False

    # Error and Info Reporting Methods

    def enable_error_reporting(self, enable: bool) -> bool:
        """
        Port of EnableErrorReporting().
        Enable or disable error reporting.

        Args:
            enable: True to enable, False to disable

        Returns:
            bool: True if successful
        """
        try:
            self.session.enable_error_reporting(enable)
            return True
        except Exception as e:
            raise e
            # return False

    def enable_info_reporting(self, enable: bool) -> bool:
        """
        Port of EnableInfoReporting().
        Enable or disable info reporting.

        Args:
            enable: True to enable, False to disable

        Returns:
            bool: True if successful
        """
        try:
            self.session.enable_info_reporting(enable)
            return True
        except Exception:
            return False

    def get_error_list(self) -> Tuple[bool, List[str]]:
        """
        Port of GetErrorList().
        Get the list of error messages.

        Returns:
            Tuple[bool, List[str]]: (success, error_list)
        """
        try:
            error_list = []
            errors = self.session.get_error_list()
            if errors:
                error_list = list(errors)  # Convert to Python list
            return True, error_list
        except Exception:
            return False, []

    def clear_error_list(self) -> bool:
        """
        Port of ClearErrorList().
        Clear the error list.

        Returns:
            bool: True if successful
        """
        try:
            self.session.clear_error_list()
            return True
        except Exception:
            return False

    def get_info_list(self) -> Tuple[bool, List[str]]:
        """
        Port of GetInfoList().
        Get the list of info messages.

        Returns:
            Tuple[bool, List[str]]: (success, info_list)
        """
        try:
            info_list = []
            infos = self.session.get_info_list()
            if infos:
                info_list = list(infos)  # Convert to Python list
            return True, info_list
        except Exception:
            return False, []

    def clear_info_list(self) -> bool:
        """
        Port of ClearInfoList().
        Clear the info list.

        Returns:
            bool: True if successful
        """
        try:
            self.session.clear_info_list()
            return True
        except Exception:
            return False

    # Simulation Methods

    def run_simulation(self) -> bool:
        """
        Port of RunSimulation().
        Initialize and run the simulation.

        Returns:
            bool: True if successful
        """
        try:
            self.session.initialize_simulation()
            self.session.simulate()
            return True
        except Exception as e:
            if self.session.is_error_reporting_enabled():
                self.session.add_to_error_list(f"Exception in run_simulation: {str(e)}")
            raise e
            # return False

    def get_results(self) -> Tuple[bool, List[str]]:
        """
        Port of GetResults().
        Get the simulation results.

        Returns:
            Tuple[bool, List[str]]: (success, results_list)
        """
        try:
            # Access results_text directly from session
            if hasattr(self.session, "results_text") and self.session.results_text:
                results_list = list(self.session.results_text)  # Convert to Python list
                return True, results_list
            return False, []
        except Exception:
            return False, []

    def get_results_dataframe(self) -> Tuple[bool, Optional[pd.DataFrame]]:
        """
        Get simulation results as a pandas DataFrame with PyBeePop-compatible formatting.

        This method mimics the PyBeePop package's result formatting, providing
        the same 44 columns with proper column names and data types.

        Returns:
            Tuple[bool, Optional[pd.DataFrame]]: (success, dataframe)
                                               Returns (True, DataFrame) on success,
                                               (False, None) on failure
        """
        try:
            # Get raw results
            success, results_list = self.get_results()
            if not success or not results_list:
                return False, None

            # PyBeePop-compatible column names (44 columns total)
            colnames = [
                "Date",
                "Colony Size",
                "Adult Drones",
                "Adult Workers",
                "Foragers",
                "Active Foragers",
                "Capped Drone Brood",
                "Capped Worker Brood",
                "Drone Larvae",
                "Worker Larvae",
                "Drone Eggs",
                "Worker Eggs",
                "Daily Eggs Laid",
                "DD",
                "L",
                "N",
                "P",
                "dd",
                "l",
                "n",
                "Free Mites",
                "Drone Brood Mites",
                "Worker Brood Mites",
                "Mites/Drone Cell",
                "Mites/Worker Cell",
                "Mites Dying",
                "Proportion Mites Dying",
                "Colony Pollen (g)",
                "Pollen Pesticide Concentration (ug/g)",
                "Colony Nectar (g)",
                "Nectar Pesticide Concentration (ug/g)",
                "Dead Drone Larvae",
                "Dead Worker Larvae",
                "Dead Drone Adults",
                "Dead Worker Adults",
                "Dead Foragers",
                "Queen Strength",
                "Average Temperature (C)",
                "Rain (mm)",
                "Min Temp (C)",
                "Max Temp (C)",
                "Daylight hours",
                "Forage Inc",
                "Forage Day",
            ]

            # Join results into a single string (mimicking PyBeePop approach)
            out_lines = results_list[1:]  # Skip header line
            if not out_lines:
                return False, None

            out_str = io.StringIO("\n".join(out_lines))

            # Read with pandas using whitespace separator and expected column names
            # Skip first 3 rows if they contain headers/metadata (like PyBeePop)
            try:
                # Try to determine if we need to skip rows by checking first few lines
                if len(results_list) >= 4:
                    # Check if first line looks like a header
                    first_line = results_list[0].strip()
                    if any(
                        word in first_line.lower()
                        for word in ["date", "colony", "adult", "version"]
                    ):
                        # Has header, might need to skip more rows
                        skip_rows = 0
                        # Look for the actual data start
                        for i, line in enumerate(results_list):
                            if line.strip():
                                first_word = line.split()[0] if line.split() else ""
                                # Data line starts with either "Initial" or a date (numbers/slashes)
                                if first_word == "Initial" or not any(
                                    char.isalpha() for char in first_word
                                ):
                                    # Found line starting with "Initial" or numbers (date), this is data
                                    skip_rows = i
                                    break
                        out_str = io.StringIO("\n".join(results_list[skip_rows:]))
                    else:
                        # No header, use all data
                        out_str = io.StringIO("\n".join(results_list))
                else:
                    out_str = io.StringIO("\n".join(out_lines))

                # Read CSV with whitespace separator
                out_df = pd.read_csv(
                    out_str,
                    sep=r"\s+",  # Whitespace separator
                    names=colnames,  # Use our column names
                    dtype={"Date": str},  # Keep dates as strings
                    engine="python",  # Use python engine for regex separator
                )

                # Ensure we have the right number of columns
                if len(out_df.columns) > len(colnames):
                    # Too many columns, take first 44
                    out_df = out_df.iloc[:, : len(colnames)]
                    out_df.columns = colnames
                elif len(out_df.columns) < len(colnames):
                    # Too few columns, pad with NaN
                    for i in range(len(out_df.columns), len(colnames)):
                        out_df[colnames[i]] = float("nan")

                return True, out_df

            except Exception as parse_error:
                # If parsing fails, try simpler approach
                if self._is_error_reporting_enabled():
                    self._add_to_error_list(
                        f"DataFrame parsing error: {str(parse_error)}"
                    )

                # Fallback: create DataFrame manually
                data_rows = []
                for line in out_lines:
                    if line.strip():
                        values = line.split()
                        if values:
                            # Pad or truncate to match expected column count
                            if len(values) < len(colnames):
                                values.extend(
                                    [float("nan")] * (len(colnames) - len(values))
                                )
                            elif len(values) > len(colnames):
                                values = values[: len(colnames)]
                            data_rows.append(values)

                if data_rows:
                    out_df = pd.DataFrame(data_rows, columns=colnames)
                    # Ensure Date column is string
                    out_df["Date"] = out_df["Date"].astype(str)
                    return True, out_df
                else:
                    return False, None

        except Exception as e:
            if self._is_error_reporting_enabled():
                self._add_to_error_list(f"Exception in get_results_dataframe: {str(e)}")
            return False, None

    # Version Methods

    def get_lib_version(self) -> Tuple[bool, str]:
        """
        Port of GetLibVersion().
        Get the library version string.

        Returns:
            Tuple[bool, str]: (success, version)
        """
        try:
            return True, BEEPOP_VERSION
        except Exception:
            return False, ""

    # Helper Methods

    def _weather_string_to_event(
        self, weather_string: str, calc_daylight_by_lat: bool = True
    ) -> Optional[Any]:
        """
        Port of WeatherStringToEvent().
        Convert a weather string to an Event object.

        The string format is: Date,MaxTemp,MinTemp,AvgTemp,Windspeed,Rainfall,DaylightHours
        Space or comma delimited.

        Args:
            weather_string: Weather data string
            calc_daylight_by_lat: Whether to calculate daylight by latitude

        Returns:
            Event object or None if parsing failed
        """
        try:
            # Split by comma or space
            tokens = re.split(r"[,\s]+", weather_string.strip())

            if len(tokens) < 6:
                return None

            # Parse date
            try:
                event_date = datetime.strptime(tokens[0], "%m/%d/%Y")
            except ValueError:
                try:
                    event_date = datetime.strptime(tokens[0], "%m/%d/%y")
                except ValueError:
                    return None

            # Parse numeric values
            try:
                max_temp = float(tokens[1])
                min_temp = float(tokens[2])
                avg_temp = float(tokens[3])
                windspeed = float(tokens[4])
                rainfall = float(tokens[5])
            except (ValueError, IndexError):
                return None

            # Create event
            if Event is not None:
                event = Event(
                    time=event_date,
                    temp=avg_temp,
                    max_temp=max_temp,
                    min_temp=min_temp,
                    windspeed=windspeed,
                    rainfall=rainfall,
                )
            else:
                # Create a minimal event object if Event class is not available
                event = type(
                    "Event",
                    (),
                    {
                        "time": event_date,
                        "temp": avg_temp,
                        "max_temp": max_temp,
                        "min_temp": min_temp,
                        "windspeed": windspeed,
                        "rainfall": rainfall,
                        "daylight_hours": 0.0,
                        "set_daylight_hours": lambda self, dh: setattr(
                            self, "daylight_hours", dh
                        ),
                        "calc_today_daylight_from_latitude": lambda self, lat: 12.0,  # Default daylight
                        "update_forage_attribute_for_event": lambda self, lat, ws: None,
                    },
                )()

            # Set daylight hours
            if calc_daylight_by_lat:
                daylight = event.calc_today_daylight_from_latitude(
                    self.session.get_latitude()
                )
                event.set_daylight_hours(daylight)
            else:
                if len(tokens) >= 7:
                    try:
                        daylight = float(tokens[6])
                        event.set_daylight_hours(daylight)
                    except ValueError:
                        return None
                else:
                    return None

            return event

        except Exception:
            return None

    def _string_to_nutrient_element(self, element_string: str) -> Optional[Any]:
        """
        Port of String2NutrientElement().
        Convert a nutrient string into an SNCElement.

        Nutrient String Format is: Date,Nectar,Pollen

        Args:
            element_string: Nutrient contamination string

        Returns:
            SNCElement object or None if parsing failed
        """
        try:
            tokens = re.split(r"[,\s]+", element_string.strip())

            if len(tokens) < 3:
                return None

            # Parse date
            try:
                nc_date = datetime.strptime(tokens[0], "%m/%d/%Y")
            except ValueError:
                try:
                    nc_date = datetime.strptime(tokens[0], "%m/%d/%y")
                except ValueError:
                    return None

            # Parse concentrations
            try:
                nectar_conc = float(tokens[1])
                pollen_conc = float(tokens[2])
            except (ValueError, IndexError):
                return None

            # Create element
            if SNCElement is not None:
                element = SNCElement(
                    nc_date=nc_date,
                    nc_nectar_cont=nectar_conc,
                    nc_pollen_cont=pollen_conc,
                )
            else:
                # Create a minimal element object if SNCElement class is not available
                element = type(
                    "SNCElement",
                    (),
                    {
                        "nc_date": nc_date,
                        "nc_nectar_cont": nectar_conc,
                        "nc_pollen_cont": pollen_conc,
                    },
                )()

            return element

        except Exception:
            return None
