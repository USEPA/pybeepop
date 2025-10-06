"""
Custom exceptions for PyBeePop with enhanced error reporting.

This module provides custom exception classes that automatically include BeePop+
internal error logs in exception messages, providing better diagnostic information
without requiring manual log retrieval.
"""


class BeepopException(Exception):
    """
    Base exception for PyBeePop errors with enhanced error reporting.

    Automatically includes BeePop+ error log and info log for better diagnostics.
    This exception captures engine-specific error information and formats it
    into a comprehensive error message.

    Attributes:
        message (str): The primary error message
        error_log (str): BeePop+ error log content
        info_log (str): BeePop+ info log content
        engine_type (str): Engine that raised the error ('cpp' or 'python')

    Example:
        >>> raise BeepopException(
        ...     "Simulation failed",
        ...     error_log="Invalid parameter: SimStart",
        ...     engine_type="python"
        ... )
        BeepopException: Simulation failed

        BeePop+ Error Log (python engine):
        Invalid parameter: SimStart
    """

    def __init__(
        self,
        message: str,
        error_log: str = "",
        info_log: str = "",
        engine_type: str = "",
    ):
        """
        Initialize BeepopException with message and optional logs.

        Args:
            message: Primary error message
            error_log: BeePop+ error log content (optional)
            info_log: BeePop+ info log content (optional)
            engine_type: Engine that raised the error (optional)
        """
        self.message = message
        self.error_log = error_log
        self.info_log = info_log
        self.engine_type = engine_type

        # Build comprehensive error message
        full_message = message

        # Add error log if available and non-empty
        if error_log and error_log.strip():
            engine_label = f" ({engine_type} engine)" if engine_type else ""
            full_message += f"\n\nBeePop+ Error Log{engine_label}:\n{error_log.strip()}"

        # Add info log if available and non-empty (usually less critical)
        if info_log and info_log.strip():
            full_message += f"\n\nBeePop+ Info Log:\n{info_log.strip()}"

        super().__init__(full_message)


class BeepopParameterError(BeepopException, ValueError):
    """
    Invalid parameter name or value.

    Raised when a parameter name is not recognized or a parameter value
    is invalid. Inherits from both BeepopException (for enhanced logging)
    and ValueError (for standard exception compatibility).

    This dual inheritance ensures:
    - isinstance(e, ValueError) returns True (backward compatible)
    - isinstance(e, BeepopException) returns True (can catch all BeePop errors)
    - Error logs are automatically included in the message

    Example:
        >>> model = PyBeePop(engine='python')
        >>> model.set_parameters({"InvalidParam": "123"})
        BeepopParameterError: InvalidParam is not a valid parameter.

        BeePop+ Error Log (python engine):
        Parameter 'InvalidParam' not found in valid parameter list.
        Expected one of: ICWorkerAdults, SimStart, SimEnd, ...
    """

    pass


class BeepopRuntimeError(BeepopException, RuntimeError):
    """
    Error during BeePop+ operation.

    Raised when a BeePop+ operation fails at runtime (e.g., simulation fails,
    file loading fails, parameter setting fails). Inherits from both
    BeepopException (for enhanced logging) and RuntimeError (for standard
    exception compatibility).

    This dual inheritance ensures:
    - isinstance(e, RuntimeError) returns True (backward compatible)
    - isinstance(e, BeepopException) returns True (can catch all BeePop errors)
    - Error logs are automatically included in the message

    Example:
        >>> model = PyBeePop(engine='python')
        >>> model.run_model()  # No weather loaded
        BeepopRuntimeError: Weather must be set before running simulation

        BeePop+ Error Log (python engine):
        Attempted to run simulation without weather data.
        Call load_weather() or pass weather_file to constructor.
    """

    pass


class BeepopFileError(BeepopException, OSError):
    """
    Error reading or parsing input file.

    Raised when a file cannot be opened, read, or parsed correctly.
    Inherits from both BeepopException (for enhanced logging) and OSError
    (for standard exception compatibility).

    This dual inheritance ensures:
    - isinstance(e, OSError) returns True (backward compatible)
    - isinstance(e, BeepopException) returns True (can catch all BeePop errors)
    - Error logs are automatically included in the message

    Example:
        >>> model = PyBeePop(engine='python')
        >>> model.load_weather("corrupted_weather.txt")
        BeepopFileError: Weather file is invalid.

        BeePop+ Error Log (python engine):
        Failed to parse weather file at line 15.
        Expected format: Date,MaxTemp,MinTemp,AvgTemp,Windspeed,Rain,Daylight
        Got: 06/15/2020,invalid_data
    """

    pass
