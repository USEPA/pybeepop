"""
Tests for engine adapters.

This module tests the PythonEngineAdapter class to ensure it properly implements
the BeepopEngineInterface protocol.
"""

import pytest


# Test helper function
def validate_adapter_interface(adapter) -> bool:
    """
    Validate that an adapter implements the BeepopEngineInterface protocol.

    Args:
        adapter: Adapter instance to validate

    Returns:
        bool: True if adapter has all required methods
    """
    required_methods = [
        "set_parameters",
        "get_parameters",
        "load_parameter_file",
        "load_weather_file",
        "load_residue_file",
        "set_latitude",
        "run_simulation",
        "get_error_log",
        "get_info_log",
        "get_version",
        "cleanup",
    ]

    required_attrs = ["engine_type"]

    for method in required_methods:
        if not hasattr(adapter, method) or not callable(getattr(adapter, method)):
            return False

    for attr in required_attrs:
        if not hasattr(adapter, attr):
            return False

    return True


def test_python_adapter_initialization():
    """Test Python adapter can be initialized."""
    from pybeepop.adapters import PythonEngineAdapter

    adapter = PythonEngineAdapter()
    assert adapter.engine_type == "python"
    assert hasattr(adapter, "model")


def test_python_adapter_interface_compliance():
    """Test Python adapter implements required interface."""
    from pybeepop.adapters import PythonEngineAdapter

    adapter = PythonEngineAdapter()
    assert validate_adapter_interface(adapter)


def test_python_adapter_has_all_methods():
    """Test Python adapter has all required methods."""
    from pybeepop.adapters import PythonEngineAdapter

    adapter = PythonEngineAdapter()

    required_methods = [
        "set_parameters",
        "get_parameters",
        "load_parameter_file",
        "load_weather_file",
        "load_residue_file",
        "set_latitude",
        "run_simulation",
        "get_error_log",
        "get_info_log",
        "get_version",
        "cleanup",
    ]

    for method in required_methods:
        assert hasattr(adapter, method), f"Adapter missing method: {method}"
        assert callable(getattr(adapter, method)), f"{method} is not callable"


def test_python_adapter_parameter_format_conversion():
    """Test Python adapter converts dict to list format and returns lowercase keys."""
    from pybeepop.adapters import PythonEngineAdapter

    adapter = PythonEngineAdapter()  # Initialization happens in __init__

    params = {"ICWorkerAdults": "10000", "SimStart": "04/01/2023"}
    result = adapter.set_parameters(params)

    assert result == params  # Should return what was set

    expected_lowercase = {"icworkeradults": "10000", "simstart": "04/01/2023"}
    assert adapter.get_parameters() == expected_lowercase


def test_python_adapter_error_log_format_conversion():
    """Test Python adapter converts error tuple to string."""
    from pybeepop.adapters import PythonEngineAdapter

    adapter = PythonEngineAdapter()
    error_log = adapter.get_error_log()

    assert isinstance(error_log, str)  # Should be string, not tuple


def test_python_adapter_info_log_format_conversion():
    """Test Python adapter converts info tuple to string."""
    from pybeepop.adapters import PythonEngineAdapter

    adapter = PythonEngineAdapter()
    info_log = adapter.get_info_log()

    assert isinstance(info_log, str)  # Should be string, not tuple


def test_python_adapter_version():
    """Test Python adapter returns version string."""
    from pybeepop.adapters import PythonEngineAdapter

    adapter = PythonEngineAdapter()
    version = adapter.get_version()

    assert isinstance(version, str)
    assert version != "Unknown"


def test_python_adapter_set_latitude():
    """Test Python adapter can set latitude."""
    from pybeepop.adapters import PythonEngineAdapter

    adapter = PythonEngineAdapter()
    result = adapter.set_latitude(40.0)

    assert result is True


def test_python_adapter_cleanup():
    """Test Python adapter cleanup method."""
    from pybeepop.adapters import PythonEngineAdapter

    adapter = PythonEngineAdapter()
    # Should not raise error
    adapter.cleanup()


def test_validate_adapter_interface_function():
    """Test validate_adapter_interface utility function."""
    from pybeepop.adapters import PythonEngineAdapter

    # Valid adapter should pass
    valid_adapter = PythonEngineAdapter()
    assert validate_adapter_interface(valid_adapter) is True

    # Invalid adapter (missing methods) should fail
    class InvalidAdapter:
        engine_type = "invalid"

    invalid_adapter = InvalidAdapter()
    assert validate_adapter_interface(invalid_adapter) is False


def test_python_adapter_verbose_mode():
    """Test Python adapter verbose mode."""
    from pybeepop.adapters import PythonEngineAdapter

    adapter = PythonEngineAdapter(verbose=True)
    assert adapter.verbose is True
    assert adapter.engine_type == "python"


def test_python_adapter_get_parameters_empty():
    """Test get_parameters returns empty dict initially."""
    from pybeepop.adapters import PythonEngineAdapter

    adapter = PythonEngineAdapter()
    params = adapter.get_parameters()

    assert isinstance(params, dict)
    assert len(params) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
