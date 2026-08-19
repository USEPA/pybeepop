"""
Engine interface protocol for PyBeePop.

This module defines the BeepopEngineInterface protocol that a BeePop+ simulation
engine must implement to be compatible with the PyBeePop wrapper.
"""

from typing import Protocol, Dict, Optional
import pandas as pd


class BeepopEngineInterface(Protocol):
    """
    Protocol defining the interface that a BeePop simulation engine must implement.

    Implemented by PythonEngineAdapter, which wraps the pure Python engine
    (beepop.BeePop).

    Note: Initialization happens in __init__(), not via a separate initialize_model() method.
    """

    engine_type: str

    def set_parameters(self, parameters: Dict[str, str]) -> Dict[str, str]:
        """
        Set simulation parameters from a dictionary.

        Args:
            parameters: Dictionary of parameter name -> value pairs.
                       Example: {"ICWorkerAdults": "10000", "SimStart": "04/01/2023"}

        Returns:
            Dict[str, str]: Dictionary of parameters that were successfully set.
        """
        ...

    def get_parameters(self) -> Dict[str, str]:
        """
        Get currently set parameters.

        Returns:
            Dict[str, str]: Dictionary of current parameter values.
        """
        ...

    def load_parameter_file(self, file_path: str) -> bool:
        """
        Load parameters from a text file.

        Args:
            file_path: Path to parameter file (format: parameter=value per line).

        Returns:
            bool: True if file loaded successfully, False otherwise.
        """
        ...

    def load_weather_file(self, file_path: str) -> bool:
        """
        Load weather data from a CSV or text file.

        Args:
            file_path: Path to weather file.

        Returns:
            bool: True if file loaded successfully, False otherwise.
        """
        ...

    def load_residue_file(self, file_path: str) -> bool:
        """
        Load pesticide residue/contamination data from a file.

        Args:
            file_path: Path to residue file.

        Returns:
            bool: True if file loaded successfully, False otherwise.
        """
        ...

    def set_latitude(self, latitude: float) -> bool:
        """
        Set geographic latitude for daylight calculations.

        Args:
            latitude: Latitude in decimal degrees (-90 to 90).

        Returns:
            bool: True if latitude set successfully, False otherwise.
        """
        ...

    def run_simulation(self) -> Optional[pd.DataFrame]:
        """
        Execute the simulation and return results.

        Returns:
            pd.DataFrame: DataFrame with simulation results (44 columns), or None if failed.
        """
        ...

    def get_error_log(self) -> str:
        """
        Get error messages from the simulation session.

        Returns:
            str: Error log as newline-separated string.
        """
        ...

    def get_info_log(self) -> str:
        """
        Get informational messages from the simulation session.

        Returns:
            str: Info log as newline-separated string.
        """
        ...

    def get_version(self) -> str:
        """
        Get the engine version string.

        Returns:
            str: Version string (e.g., "1.15.25").
        """
        ...

    def cleanup(self) -> None:
        """
        Clean up resources and close connections.

        This method should be idempotent and safe to call multiple times.
        """
        ...
