"""
pybeepop - BeePop+ interface for Python
"""

import os
import platform
import pandas as pd
from typing import Optional
from .tools import BeePopModel
from .plots import plot_timeseries
from .engine_interface import BeepopEngineInterface
import json


class PyBeePop:
    """
    Python interface for the BeePop+ honey bee colony simulation model.

    BeePop+ is a mechanistic model for simulating honey bee colony dynamics, designed for ecological risk assessment and research applications.
    This interface enables programmatic access to BeePop+ from Python, supporting batch simulations, sensitivity analysis, and integration with
    data analysis workflows.

    For scientific background, model structure, and example applications, see:
    Garber et al. (2022), "Simulating the Effects of Pesticides on Honey Bee (Apis mellifera L.) Colonies with BeePop+", Ecologies.
    Minucci et al. (2025), "pybeepop: A Python interface for the BeePop+ honey bee colony model," Journal of Open Research Software.

    Example usage:
        >>> from pybeepop.pybeepop import PyBeePop
        >>> model = PyBeePop(parameter_file='params.txt', weather_file='weather.csv', residue_file='residues.csv')
        >>> model.run_model()
        >>> results = model.get_output()
        >>> model.plot_output()
    """

    def __init__(
        self,
        engine="auto",
        lib_file=None,
        parameter_file=None,
        weather_file=None,
        residue_file=None,
        latitude=30.0,
        verbose=False,
    ):
        """
        Initialize a PyBeePop object with choice of simulation engine.

        Args:
            engine (str, optional): Simulation engine to use. Options:
                - 'auto' (default): Automatically select engine. Tries C++ first,
                  falls back to Python if C++ unavailable or initialization fails.
                - 'cpp': Force C++ engine. Raises error if unavailable.
                - 'python': Force pure Python engine.

            lib_file (str, optional): Path to BeePop+ shared library (.dll or .so).
                Only relevant when engine='cpp' or engine='auto'. If None, attempts
                to auto-detect based on OS and architecture.

            parameter_file (str, optional): Path to a text file of BeePop+ parameters (one per line, parameter=value). See https://doi.org/10.3390/ecologies3030022
                or the documentation for valid parameters.
            weather_file (str, optional): Path to a .csv or comma-separated .txt file containing weather data, where each row denotes:
                Date (MM/DD/YY), Max Temp (C), Min Temp (C), Avg Temp (C), Windspeed (m/s), Rainfall (mm), Hours of daylight (optional).
            residue_file (str, optional): Path to a .csv or comma-separated .txt file containing pesticide residue data. Each row should specify Date (MM/DD/YYYY),
                Concentration in nectar (g A.I. / g), Concentration in pollen (g A.I. / g). Values can be in scientific notation (e.g., "9.00E-08").
            latitude (float, optional): Latitude in decimal degrees for daylight hour calculations (-90 to 90). Defaults to 30.0.
            verbose (bool, optional): If True, print additional debugging statements. Defaults to False.

        Raises:
            FileNotFoundError: If a provided file does not exist at the specified path.
            NotImplementedError: If run on a platform that is not 64-bit Windows or Linux.
            ValueError: If engine parameter is invalid or latitude is outside the valid range.

        Examples:
            >>> # Auto-select engine (backward compatible)
            >>> model = PyBeePop(weather_file='weather.csv')
            >>> results = model.run_model()

            >>> # Force Python engine
            >>> model = PyBeePop(engine='python')
            >>> model.load_weather('weather.csv')
            >>> results = model.run_model()

            >>> # Force C++ engine with custom library
            >>> model = PyBeePop(engine='cpp', lib_file='/path/to/custom_beepop.so')
            >>> model.load_weather('weather.csv')
            >>> results = model.run_model()
        """
        self.verbose = verbose
        self.engine_type: Optional[str] = None
        self.engine: Optional[BeepopEngineInterface] = None
        self.lib_file: Optional[str] = None  # For backward compatibility

        # Engine selection logic
        if engine == "python":
            self.engine = self._initialize_python_engine()
            self.engine_type = "python"
        elif engine == "cpp":
            self.engine = self._initialize_cpp_engine(lib_file)
            self.engine_type = "cpp"
            # Store lib_file for backward compatibility
            if hasattr(self.engine, "lib_file"):
                self.lib_file = self.engine.lib_file
        elif engine == "auto":
            # Try C++ first (backward compatible), fall back to Python
            try:
                self.engine = self._initialize_cpp_engine(lib_file)
                self.engine_type = "cpp"
                # Store lib_file for backward compatibility
                if hasattr(self.engine, "lib_file"):
                    self.lib_file = self.engine.lib_file
                if verbose:
                    print("Using C++ engine")
            except Exception as e:
                if verbose:
                    print(f"C++ engine initialization failed: {e}")
                    print("Falling back to Python engine...")
                self.engine = self._initialize_python_engine()
                self.engine_type = "python"
                if verbose:
                    print("Using Python engine")
        else:
            raise ValueError(
                f"Invalid engine type: '{engine}'. "
                f"Must be 'auto', 'cpp', or 'python'."
            )

        # Validate and set latitude
        if not -90 <= latitude <= 90:
            raise ValueError("Latitude must be between -90 and 90 degrees")
        self.current_latitude = latitude
        self.engine.set_latitude(self.current_latitude)

        # Initialize file paths and parameters
        self.parameter_file = None
        self.weather_file = None
        self.residue_file = None
        self.parameters = {}
        self.output = None

        # Add backward compatibility alias
        self.beepop = self.engine

        # Load files if provided
        if parameter_file is not None:
            self.load_parameter_file(parameter_file)

        if weather_file is not None:
            self.load_weather(weather_file)

        if residue_file is not None:
            self.load_residue_file(residue_file)

    def _initialize_cpp_engine(self, lib_file) -> BeepopEngineInterface:
        """
        Initialize C++ engine.

        Args:
            lib_file: Path to shared library, or None for auto-detection

        Returns:
            CppEngineAdapter: Initialized C++ engine adapter

        Raises:
            FileNotFoundError: If library file not found
            RuntimeError: If initialization fails
        """
        from .adapters import (
            CppEngineAdapter,
        )  # Auto-detect lib_file if not provided (existing logic)

        if lib_file is None:
            parent = os.path.dirname(os.path.abspath(__file__))
            platform_name = platform.system()

            if platform_name == "Windows":
                if platform.architecture()[0] == "32bit":
                    raise NotImplementedError(
                        "Windows x86 (32-bit) is not supported by BeePop+. "
                        "Please run on an x64 platform."
                    )
                lib_file = os.path.join(parent, "lib/beepop_win64.dll")
            elif platform_name == "Linux":
                lib_file = os.path.join(parent, "lib/beepop_linux.so")
                if self.verbose:
                    print(
                        "Running in Linux mode. Trying manylinux/musllinux version.\\n"
                        "If you encounter errors, you may need to compile your own version of BeePop+ from source and pass the path to your\\n"
                        ".so file with the lib_file option. Currently, only 64-bit architecture is supported.\\n"
                        "See the pybeepop README for instructions."
                    )
            elif platform_name == "Darwin":
                lib_file = os.path.join(parent, "lib/beepop_macos.dylib")
                if self.verbose:
                    print(
                        "Running in macOS mode. Using universal binary (Intel + Apple Silicon).\\n"
                        "If you encounter errors, you may need to compile your own version of BeePop+ from source and pass the path to your\\n"
                        ".dylib file with the lib_file option.\\n"
                        "See the pybeepop README for instructions."
                    )
            else:
                raise NotImplementedError("BeePop+ only supports Windows, Linux, and macOS.")

        if not os.path.isfile(lib_file):
            raise FileNotFoundError(
                f"BeePop+ shared library not found at: {lib_file}\\n"
                f"You may need to compile BeePop+ from source or use engine='python'\\n"
                f"See https://github.com/USEPA/pybeepop/blob/main/README.md for more info."
            )

        return CppEngineAdapter(lib_file, verbose=self.verbose)

    def _initialize_python_engine(self) -> BeepopEngineInterface:
        """
        Initialize Python engine.

        Returns:
            PythonEngineAdapter: Initialized Python engine adapter
        """
        from .adapters import PythonEngineAdapter

        return PythonEngineAdapter(verbose=self.verbose)

    def set_parameters(self, parameters):
        """
        Set BeePop+ parameters based on a dictionary {parameter: value}.

        Args:
            parameters (dict): Dictionary of BeePop+ parameters {parameter: value}. See https://doi.org/10.3390/ecologies3030022 or the documentation for valid parameters.

        Raises:
            TypeError: If parameters is not a dict.
            ValueError: If a parameter is not a valid BeePop+ parameter.
        """
        if (parameters is not None) and (not isinstance(parameters, dict)):
            raise TypeError(
                "parameters must be a named dictionary of BeePop+ parameters"
            )
        self.parameters = self.engine.set_parameters(parameters)

    def get_parameters(self):
        """
        Return all parameters that have been set by the user.

        Returns:
            dict: Dictionary of current BeePop+ parameters.
        """
        return self.engine.get_parameters()

    def set_latitude(self, latitude):
        """
        Set the latitude for daylight hour calculations.

        Args:
            latitude (float): Latitude in decimal degrees (-90 to 90). Positive values are North, negative are South.

        Raises:
            ValueError: If latitude is outside the valid range.
        """
        if not -90 <= latitude <= 90:
            raise ValueError("Latitude must be between -90 and 90 degrees")
        self.current_latitude = latitude
        self.engine.set_latitude(latitude)

    def get_latitude(self):
        """
        Get the currently set latitude.

        Returns:
            float: Current latitude in decimal degrees.
        """
        return self.current_latitude

    def set_simulation_dates(self, start_date, end_date):
        """
        Convenience method to set simulation start and end dates. The dates can
        also be set directly as SimStart/SimEnd using the set_parameters() or
        load_parameters() methods.

        Args:
            start_date (str): Simulation start date in MM/DD/YYYY format.
            end_date (str): Simulation end date in MM/DD/YYYY format.
        """
        date_params = {"SimStart": start_date, "SimEnd": end_date}
        self.set_parameters(date_params)

        if self.verbose:
            print(f"Set simulation dates: {start_date} to {end_date}")

    def load_weather(self, weather_file):
        """
        Load a weather file. The file should be a .csv or comma-delimited .txt file where each row denotes:
        Date (MM/DD/YYYY), Max Temp (C), Min Temp (C), Avg Temp (C), Windspeed (m/s), Rainfall (mm), Hours of daylight (optional).

        Note: Loading weather may reset simulation dates (SimStart/SimEnd) to the weather file's date range.
        Any previously set parameters will be automatically re-applied after weather loading.

        Args:
            weather_file (str): Path to the weather file (csv or txt). See docs/weather_readme.txt and manuscript for format details.

        Raises:
            TypeError: If weather_file is None.
            FileNotFoundError: If the provided file does not exist at the specified path.
            OSError: If the file cannot be opened or read.
            RuntimeError: If weather file cannot be loaded.
        """
        if weather_file is None:
            raise TypeError("Cannot set weather file to None")
        if not os.path.isfile(weather_file):
            raise FileNotFoundError(
                "Weather file does not exist at path: {}!".format(weather_file)
            )
        self.weather_file = weather_file

        # Load weather via adapter
        success = self.engine.load_weather_file(self.weather_file)
        if not success:
            raise RuntimeError("Failed to load weather file")

    def load_parameter_file(self, parameter_file):
        """
        Load a .txt file of parameter values to set. Each row of the file is a string with the format 'parameter=value'.

        Args:
            parameter_file (str): Path to a txt file of BeePop+ parameters. See https://doi.org/10.3390/ecologies3030022 or the documentation for valid parameters.

        Raises:
            FileNotFoundError: If the provided file does not exist at the specified path.
            ValueError: If a listed parameter is not a valid BeePop+ parameter.
        """
        if not os.path.isfile(parameter_file):
            raise FileNotFoundError(
                "Paramter file does not exist at path: {}!".format(parameter_file)
            )
        self.parameter_file = parameter_file

        # Load parameter file via adapter
        # Note: adapter will raise ValueError for invalid parameters
        success = self.engine.load_parameter_file(self.parameter_file)
        if not success:
            raise RuntimeError("Failed to load parameter file")

    def load_residue_file(self, residue_file):
        """
        Load a .csv or comma-delimited .txt file of pesticide residues in pollen/nectar. Each row should specify Date (MM/DD/YYYY),
        Concentration in nectar (g A.I. / g), Concentration in pollen (g A.I. / g). Values can be in scientific notation (e.g., "9.00E-08").

        Args:
            residue_file (str): Path to the residue .csv or .txt file. See docs/residue_file_readme.txt and manuscript for format details.

        Raises:
            FileNotFoundError: If the provided file does not exist at the specified path.
        """
        if not os.path.isfile(residue_file):
            raise FileNotFoundError(
                "Residue file does not exist at path: {}!".format(residue_file)
            )
        self.residue_file = residue_file

        # Load residue file via adapter
        success = self.engine.load_residue_file(self.residue_file)
        if not success:
            raise RuntimeError("Failed to load residue file")

    def run_model(self):
        """
        Run the BeePop+ model simulation.

        Raises:
            RuntimeError: If the weather file has not yet been set.

        Returns:
            pandas.DataFrame: DataFrame of daily time series results for the BeePop+ run, including colony size, adult workers, brood, eggs, and other metrics.
        """
        # check to see if parameters have been supplied
        if (self.parameter_file is None) and (not self.parameters):
            print("No parameters have been set. Running with default settings.")
        if self.weather_file is None:
            raise RuntimeError("Weather must be set before running BeePop+!")

        # Run via adapter
        self.output = self.engine.run_simulation()

        if self.output is None:
            raise RuntimeError("Simulation failed to produce results")

        return self.output

    def get_output(self, format="DataFrame"):
        """
        Get the output from the last BeePop+ run.

        Args:
            format (str, optional): Return results as DataFrame ('DataFrame') or JSON string ('json'). Defaults to 'DataFrame'.

        Raises:
            RuntimeError: If there is no output because run_model has not yet been called.

        Returns:
            pandas.DataFrame or str: DataFrame or JSON string of the model results. JSON output is a dictionary of lists keyed by column name.
        """
        if self.output is None:
            raise RuntimeError(
                "There are no results to plot. Please run the model first."
            )
        if format == "json":
            result = json.dumps(self.output.to_dict(orient="list"))
        else:
            result = self.output
        return result

    def plot_output(
        self,
        columns=[
            "Colony Size",
            "Adult Workers",
            "Capped Worker Brood",
            "Worker Larvae",
            "Worker Eggs",
        ],
    ):
        """
        Plot the output as a time series.

        Args:
            columns (list, optional): List of column names to plot (as strings). Defaults to key colony metrics.

        Raises:
            RuntimeError: If there is no output because run_model has not yet been called.
            IndexError: If any column name is not a valid output column.

        Returns:
            matplotlib.axes.Axes: Matplotlib Axes object for further customization.
        """
        if self.output is None:
            raise RuntimeError(
                "There are no results to plot. Please run the model first."
            )
        invalid_cols = [col not in self.output.columns for col in columns]
        if any(invalid_cols):
            raise IndexError(
                "The column name {} is not a valid output column.".format(
                    [i for (i, v) in zip(columns, invalid_cols) if v]
                )
            )
        plot = plot_timeseries(output=self.output, columns=columns)
        return plot

    def get_error_log(self):
        """
        Return the BeePop+ session error log as a string for debugging. Useful for troubleshooting.

        Returns:
            str: Error log from the BeePop+ session.
        """
        return self.engine.get_error_log()

    def get_info_log(self):
        """
        Return the BeePop+ session info log as a string for debugging..

        Returns:
            str: Info log from the BeePop+ session.
        """
        return self.engine.get_info_log()

    def version(self):
        """
        Return the BeePop+ version as a string.

        Returns:
            str: BeePop+ version string.
        """
        return self.engine.get_version()

    def exit(self):
        """
        Close the connection to the BeePop+ simulation engine and clean up resources.
        """
        if hasattr(self, "engine") and self.engine is not None:
            try:
                self.engine.cleanup()
            except Exception as e:
                if self.verbose:
                    print(f"Warning during cleanup: {e}")
            self.engine = None

    def __del__(self):
        """Destructor to ensure cleanup when object is garbage collected."""
        self.exit()
