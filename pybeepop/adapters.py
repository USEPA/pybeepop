"""
Engine adapter for PyBeePop.

Wraps the Python BeePop+ engine (beepop.BeePop) to provide an interface conforming
to the BeepopEngineInterface protocol.
"""

import os
from typing import Dict, Optional, Type
import pandas as pd

from .beepop.parameters import validate_parameter
from .exceptions import (
    BeepopException,
    BeepopParameterError,
    BeepopRuntimeError,
    BeepopFileError,
)

# Parameters removed from pybeepop+, mapped to migration guidance. Keys are lowercase.
_VTDATA_GUIDANCE = (
    "Varroa treatments are now scheduled with VTData, which takes "
    "start_date,duration_weeks,mortality% (e.g. VTData=6/2/2015,6,75). Pass one VTData "
    "entry per treatment, or VTData=Clear to reset. Mite resistance is set on the "
    "population with InitMitePctResistant and PctImmMitesResistant."
)

RETIRED_PARAMETERS = {
    "eseedconcentration": (
        "ESeedConcentration was removed in pybeepop+ 0.3.0. Use ESeedAppRate instead, "
        "the seed treatment application rate in mg a.i./seed. Nectar and pollen residues "
        "are now derived separately from that rate rather than sharing one concentration."
    ),
    "vttreatmentstart": f"VTTreatmentStart was removed in pybeepop+ 0.3.0. {_VTDATA_GUIDANCE}",
    "vttreatmentduration": (
        f"VTTreatmentDuration was removed in pybeepop+ 0.3.0. {_VTDATA_GUIDANCE}"
    ),
    "vtmortality": f"VTMortality was removed in pybeepop+ 0.3.0. {_VTDATA_GUIDANCE}",
}


def invalid_parameter_message(par_name: str) -> str:
    """Return the error message for an unrecognized parameter name."""
    retired = RETIRED_PARAMETERS.get(par_name.strip().lower())
    if retired is not None:
        return retired
    return f"{par_name} is not a valid parameter."


class PythonEngineAdapter:
    """
    Adapter for pure Python BeePop+ engine.

    Wraps the Python port (beepop.BeePop) to conform to the BeepopEngineInterface
    protocol, handling format conversions between PyBeePop's dict-based API and
    the Python engine's list-based parameter format.

    Attributes:
        engine_type (str): Always 'python'
        model (BeePop): The underlying Python engine
    """

    def __init__(self, verbose: bool = False):
        """
        Initialize Python engine adapter.

        Args:
            verbose: Enable verbose output
        """
        from pybeepop.beepop import BeePop

        self.model = BeePop()
        self.engine_type = "python"
        self.verbose = verbose
        self._parameters = {}  # Track parameters set

        # Load valid parameters for validation
        parent = os.path.dirname(os.path.abspath(__file__))
        self.valid_parameters = pd.read_csv(
            os.path.join(parent, "data/BeePop_exposed_parameters.csv"), skiprows=1
        )["Exposed Variable Name"].tolist()
        self._valid_parameters_lower = {x.lower() for x in self.valid_parameters}

        # Initialize model during adapter construction
        self.model.initialize_model()

        if verbose:
            self.model.enable_error_reporting(True)
            self.model.enable_info_reporting(True)

    def _raise_with_log(
        self, exception_class: Type[BeepopException], message: str
    ) -> None:
        """
        Raise exception with BeePop+ error log included.

        Args:
            exception_class: The exception class to raise (BeepopParameterError, etc.)
            message: The error message

        Raises:
            exception_class: Raised with error log and info log included
        """
        error_log = self.get_error_log()
        info_log = self.get_info_log()
        raise exception_class(
            message=message,
            error_log=error_log,
            info_log=None,  # info_log,
            engine_type=self.engine_type,
        )

    def set_parameters(self, parameters: Dict[str, str]) -> Dict[str, str]:
        """
        Set parameters, converting from dict to list format.

        Python engine expects: ["ParamName=value", ...]
        PyBeePop provides: {"ParamName": "value", ...}

        Raises:
            BeepopParameterError: If parameter name is not valid
            BeepopRuntimeError: If parameters cannot be set
        """
        try:
            # Validate parameter names and values
            for par_name, par_value in parameters.items():
                if par_name.lower() not in self._valid_parameters_lower:
                    self._raise_with_log(
                        BeepopParameterError, invalid_parameter_message(par_name)
                    )
                ok, _, error = validate_parameter(
                    par_name.lower(), str(par_value).strip(), par_name
                )
                if not ok:
                    self._raise_with_log(BeepopParameterError, error)

            # Convert dict to list format
            param_list = [f"{k}={v}" for k, v in parameters.items()]

            # Set parameters (don't reset ICs to preserve previous settings)
            success = self.model.set_ic_variables_v(param_list, reset_ics=False)

            if success:
                self._parameters.update(parameters)
                return parameters
            else:
                self._raise_with_log(BeepopRuntimeError, "Error setting parameters")
        except BeepopException:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            if self.verbose:
                print(f"Error setting parameters: {e}")
            self._raise_with_log(BeepopRuntimeError, f"Error setting parameters: {e}")

    def get_parameters(self) -> Dict[str, str]:
        """Get currently set parameters with lowercase keys."""
        return {k.lower(): v for k, v in self._parameters.items()}

    def load_parameter_file(self, file_path: str) -> bool:
        """
        Load parameter file via Python engine.

        Raises:
            BeepopFileError: If file cannot be opened or read
            BeepopParameterError: If parameter is invalid
            BeepopRuntimeError: If parameters cannot be loaded
        """
        try:
            # Try to open and read file to catch OSError early
            with open(file_path, "r") as f:
                lines = f.readlines()

            # Validate parameter names and values before loading
            for line in lines:
                clean_line = line.strip()
                if clean_line and not clean_line.startswith("#") and "=" in clean_line:
                    raw_name, raw_value = clean_line.split("=", 1)
                    param_name = raw_name.strip().lower()
                    if param_name not in self._valid_parameters_lower:
                        self._raise_with_log(
                            BeepopParameterError,
                            invalid_parameter_message(raw_name.strip()),
                        )
                    ok, _, error = validate_parameter(
                        param_name, raw_value.strip(), raw_name.strip()
                    )
                    if not ok:
                        self._raise_with_log(BeepopParameterError, error)

            success = self.model.load_parameter_file(file_path)

            # If successful, parse file to track parameters
            if success:
                for line in lines:
                    clean_line = line.strip()
                    if (
                        clean_line
                        and not clean_line.startswith("#")
                        and "=" in clean_line
                    ):
                        key, value = clean_line.split("=", 1)
                        self._parameters[key.strip()] = value.strip()
                return True
            else:
                self._raise_with_log(BeepopRuntimeError, "Error loading parameter file")
        except BeepopException:
            # Re-raise our custom exceptions
            raise
        except OSError as e:
            # Re-raise as BeepopFileError with error logs
            self._raise_with_log(BeepopFileError, str(e))
        except Exception as e:
            if self.verbose:
                print(f"Error loading parameter file: {e}")
            self._raise_with_log(
                BeepopRuntimeError, f"Error loading parameter file: {e}"
            )

    def load_weather_file(self, file_path: str) -> bool:
        """
        Load weather file via Python engine.

        Raises:
            BeepopFileError: If file cannot be opened or read
            BeepopRuntimeError: If weather cannot be loaded
        """
        try:
            # Try to open file to catch OSError early
            with open(file_path, "r") as f:
                f.read()

            success = self.model.set_weather_from_file(file_path)
            if success:
                return True
            else:
                self._raise_with_log(BeepopRuntimeError, "Error Loading Weather")
        except BeepopException:
            # Re-raise our custom exceptions
            raise
        except OSError:
            # Re-raise as BeepopFileError with error logs
            self._raise_with_log(BeepopFileError, "Weather file is invalid.")
        except Exception as e:
            if self.verbose:
                print(f"Error loading weather file: {e}")
            self._raise_with_log(BeepopRuntimeError, f"Error loading weather file: {e}")

    def load_residue_file(self, file_path: str) -> bool:
        """
        Load residue file, converting to list format.

        Python engine expects list of strings, not a file path.
        We need to parse the file ourselves.

        Raises:
            BeepopFileError: If file cannot be opened or read
            BeepopRuntimeError: If residue file cannot be loaded
        """
        try:
            with open(file_path, "r") as f:
                lines = [
                    line.strip()
                    for line in f
                    if line.strip() and not line.startswith("#")
                ]
        except Exception:
            self._raise_with_log(BeepopFileError, "Residue file is invalid.")

        try:
            # Load the contamination table
            success = self.model.set_contamination_table(lines)
            if success:
                self.set_parameters(
                    {"NecPolFileEnable": "true"}
                )  # Enable residue file mode
                return True
            else:
                self._raise_with_log(BeepopRuntimeError, "Error loading residue file")
        except BeepopException:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            if self.verbose:
                print(f"Error loading residue file: {e}")
            self._raise_with_log(BeepopRuntimeError, f"Error loading residue file: {e}")

    def set_latitude(self, latitude: float) -> bool:
        """Set latitude via Python engine."""
        try:
            return self.model.set_latitude(latitude)
        except Exception as e:
            if self.verbose:
                print(f"Error setting latitude: {e}")
            return False

    def run_simulation(self) -> Optional[pd.DataFrame]:
        """
        Run simulation via Python engine.

        Raises:
            BeepopRuntimeError: If simulation fails to run
        """
        try:
            success = self.model.run_simulation()
            if success:
                success, df = self.model.get_results_dataframe()
                if success:
                    return df
                else:
                    self._raise_with_log(
                        BeepopRuntimeError, "Error running BeePop+ simulation."
                    )
            else:
                self._raise_with_log(
                    BeepopRuntimeError, "Error running BeePop+ simulation."
                )
        except BeepopException:
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            if self.verbose:
                print(f"Error running simulation: {e}")
            self._raise_with_log(
                BeepopRuntimeError, f"Error running BeePop+ simulation: {e}"
            )

    def get_error_log(self) -> str:
        """
        Get error log, converting from tuple format to string.

        Python engine returns: (success: bool, errors: List[str])
        We need: string (newline-separated)
        """
        try:
            success, errors = self.model.get_error_list()
            if success and errors:
                return "\n".join(errors)
            return ""
        except Exception:
            return ""

    def get_info_log(self) -> str:
        """
        Get info log, converting from tuple format to string.

        Python engine returns: (success: bool, info: List[str])
        We need: string (newline-separated)
        """
        try:
            success, info = self.model.get_info_list()
            if success and info:
                return "\n".join(info)
            return ""
        except Exception:
            return ""

    def get_version(self) -> str:
        """Get version from Python engine."""
        try:
            success, version = self.model.get_lib_version()
            return version if success else "Unknown"
        except Exception:
            return "Unknown"

    def cleanup(self) -> None:
        """Python engine handles cleanup automatically via garbage collection."""
        pass  # No explicit cleanup needed
