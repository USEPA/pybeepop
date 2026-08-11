"""
Integration tests for PyBeePop.

This module verifies that PyBeePop works correctly end to end, including:
- Initialization and rejection of the removed C++ engine options
- Parameter handling and file loading
- Simulation execution
- Exception behavior
- Backward compatibility with legacy code patterns
"""

import pytest
import os
import platform
import tempfile
from datetime import datetime, timedelta
import random


# ============================================================================
# Test Fixtures
# ============================================================================


@pytest.fixture
def sample_weather_file(tmp_path):
    """Create a sample weather file for testing."""
    weather_file = tmp_path / "test_weather.csv"

    # Generate 30 days of weather data
    lines = []
    start_date = datetime(2023, 4, 1)
    for day in range(30):
        current_date = start_date + timedelta(days=day)
        max_temp = 20 + random.uniform(-5, 5)
        min_temp = 10 + random.uniform(-5, 5)
        avg_temp = (max_temp + min_temp) / 2
        windspeed = 2.0
        rain = 0.0
        daylight = 12.0

        line = f"{current_date.strftime('%m/%d/%Y')},{max_temp:.1f},{min_temp:.1f},{avg_temp:.1f},{windspeed:.1f},{rain:.1f},{daylight:.1f}"
        lines.append(line)

    weather_file.write_text("\n".join(lines))
    return str(weather_file)


@pytest.fixture
def sample_parameters():
    """Sample parameters for testing."""
    return {
        "ICWorkerAdults": "10000",
        "ICWorkerBrood": "5000",
        "SimStart": "04/01/2023",
        "SimEnd": "04/30/2023",
    }


@pytest.fixture
def sample_parameter_file(tmp_path):
    """Create a sample parameter file for testing."""
    param_file = tmp_path / "test_params.txt"
    param_file.write_text(
        "ICWorkerAdults=10000\n"
        "ICWorkerBrood=5000\n"
        "SimStart=04/01/2023\n"
        "SimEnd=04/30/2023\n"
    )
    return str(param_file)


# ============================================================================
# Engine Initialization Tests
# ============================================================================


class TestEngineInitialization:
    """Test engine initialization and selection."""

    def test_removed_auto_engine_selection(self):
        """Test that the legacy auto engine option is no longer supported."""
        from pybeepop import PyBeePop

        with pytest.raises(ValueError, match="'python' is the only option"):
            PyBeePop(engine="auto")

    def test_python_engine_selection(self):
        """Test that engine='python' is still accepted."""
        from pybeepop import PyBeePop

        model = PyBeePop(engine="python")
        assert model.engine_type == "python"
        assert model.engine is not None

    def test_cpp_engine_raises_migration_error(self):
        """Test that engine='cpp' explains the 0.3.0 removal."""
        from pybeepop import PyBeePop

        with pytest.raises(ValueError, match="engine was removed in pybeepop"):
            PyBeePop(engine="cpp")

    def test_lib_file_raises_migration_error(self):
        """Test that lib_file explains the 0.3.0 removal."""
        from pybeepop import PyBeePop

        with pytest.raises(ValueError, match="lib_file argument is no longer supported"):
            PyBeePop(lib_file="/path/to/beepop.so")

    def test_invalid_engine_selection(self):
        """Test that invalid engine raises ValueError."""
        from pybeepop import PyBeePop

        with pytest.raises(ValueError, match="Invalid engine type"):
            PyBeePop(engine="invalid")

    def test_backward_compatibility_default(self):
        """Test that the default constructor uses the Python engine."""
        from pybeepop import PyBeePop

        model = PyBeePop()
        assert model.engine is not None
        assert model.engine_type == "python"


# ============================================================================
# Parameter Handling Tests
# ============================================================================


class TestParameterHandling:
    """Test parameter handling."""

    def test_set_parameters(self, sample_parameters):
        """Test setting parameters."""
        from pybeepop import PyBeePop

        model = PyBeePop()
        model.set_parameters(sample_parameters)

        retrieved = model.get_parameters()
        # Check that key parameters were set
        assert "ICWorkerAdults" in retrieved or len(retrieved) > 0

    def test_load_parameter_file(self, sample_parameter_file):
        """Test loading a parameter file."""
        from pybeepop import PyBeePop

        model = PyBeePop()
        model.load_parameter_file(sample_parameter_file)

        # Verify parameters were loaded
        params = model.get_parameters()
        assert len(params) > 0  # Should have some parameters

    def test_parameter_file_in_constructor_python(self, sample_parameter_file):
        """Test loading a parameter file via the constructor."""
        from pybeepop import PyBeePop

        model = PyBeePop(engine="python", parameter_file=sample_parameter_file)
        params = model.get_parameters()
        assert len(params) > 0


# ============================================================================
# Simulation Execution Tests
# ============================================================================


class TestSimulationExecution:
    """Test running simulations."""

    def test_run_simulation(self, sample_weather_file, sample_parameters):
        """Test running a simulation."""
        from pybeepop import PyBeePop

        model = PyBeePop()
        model.set_parameters(sample_parameters)
        model.load_weather(sample_weather_file)

        results = model.run_model()

        # Verify results structure
        assert results is not None
        assert len(results) > 0
        assert "Date" in results.columns
        # Should produce colony size data
        assert any("Colony" in col or "Adult" in col for col in results.columns)

    def test_simulation_without_weather_raises_error(self):
        """Test that simulation without weather raises error."""
        from pybeepop import PyBeePop

        model = PyBeePop(engine="python")

        with pytest.raises(RuntimeError, match="Weather must be set"):
            model.run_model()

    def test_weather_file_in_constructor_python(
        self, sample_weather_file, sample_parameters
    ):
        """Test loading a weather file via the constructor."""
        from pybeepop import PyBeePop

        model = PyBeePop(engine="python", weather_file=sample_weather_file)
        model.set_parameters(sample_parameters)
        results = model.run_model()

        assert results is not None
        assert len(results) > 0


# ============================================================================
# Exception Behavior Tests
# ============================================================================


class TestExceptionParity:
    """Test exceptions raised for error conditions."""

    def test_invalid_parameter_raises_valueerror(self):
        """Should raise ValueError for invalid parameter names."""
        from pybeepop import PyBeePop

        model = PyBeePop()
        with pytest.raises(ValueError, match="is not a valid parameter"):
            model.set_parameters({"Invalid_Parameter_Name": "123"})

    def test_wrong_parameter_type_raises_typeerror(self):
        """Should raise TypeError for non-dict parameters."""
        from pybeepop import PyBeePop

        model = PyBeePop()
        with pytest.raises(TypeError, match="must be a named dictionary"):
            model.set_parameters(["not", "a", "dict"])

    def test_none_weather_file_raises_typeerror(self):
        """Should raise TypeError when weather_file is None."""
        from pybeepop import PyBeePop

        model = PyBeePop()
        with pytest.raises(TypeError, match="Cannot set weather file to None"):
            model.load_weather(None)

    def test_missing_weather_file_raises_filenotfounderror(self):
        """Should raise FileNotFoundError for missing weather file."""
        from pybeepop import PyBeePop

        model = PyBeePop()
        with pytest.raises(FileNotFoundError):
            model.load_weather("nonexistent_weather.txt")

    def test_missing_parameter_file_raises_filenotfounderror(self):
        """Should raise FileNotFoundError for missing parameter file."""
        from pybeepop import PyBeePop

        model = PyBeePop()
        with pytest.raises(FileNotFoundError):
            model.load_parameter_file("nonexistent_params.txt")

    def test_missing_residue_file_raises_filenotfounderror(self):
        """Should raise FileNotFoundError for missing residue file."""
        from pybeepop import PyBeePop

        model = PyBeePop()
        with pytest.raises(FileNotFoundError):
            model.load_residue_file("nonexistent_residue.txt")

    def test_invalid_parameter_in_file_raises_valueerror(self, tmp_path):
        """Should raise ValueError for invalid parameters in file."""
        from pybeepop import PyBeePop

        # Create a parameter file with invalid parameter
        param_file = tmp_path / "invalid_params.txt"
        param_file.write_text("InvalidParameterName=12345\n")

        model = PyBeePop()
        with pytest.raises(ValueError, match="is not a valid parameter"):
            model.load_parameter_file(str(param_file))

    def test_run_without_weather_raises_runtimeerror(self):
        """Should raise RuntimeError when running without weather."""
        from pybeepop import PyBeePop

        model = PyBeePop()
        model.set_parameters({"ICWorkerAdults": "10000"})
        with pytest.raises(RuntimeError, match="Weather must be set"):
            model.run_model()

    def test_invalid_weather_file_format_raises_oserror(self, tmp_path):
        """Should raise OSError for invalid weather file format."""
        from pybeepop import PyBeePop

        # Create a weather file with invalid content
        weather_file = tmp_path / "invalid_weather.txt"
        weather_file.write_text("This is not valid weather data\n")

        model = PyBeePop()
        # This should raise OSError or RuntimeError depending on how badly formatted
        with pytest.raises((OSError, RuntimeError)):
            model.load_weather(str(weather_file))


# ============================================================================
# Exception Message Tests
# ============================================================================


class TestExceptionMessages:
    """Test that exception messages are helpful."""

    def test_invalid_parameter_message_format(self):
        """Invalid parameter errors should name the offending parameter."""
        from pybeepop import PyBeePop

        model = PyBeePop()
        with pytest.raises(ValueError) as exc_info:
            model.set_parameters({"BadParam": "123"})

        error_msg = str(exc_info.value).lower()
        assert "badparam" in error_msg or "not a valid parameter" in error_msg


# ============================================================================
# Backward Compatibility Tests
# ============================================================================


class TestBackwardCompatibility:
    """Test that existing code patterns still work."""

    def test_old_initialization_pattern(self, sample_weather_file):
        """Test that old initialization pattern still works."""
        from pybeepop import PyBeePop

        # Old pattern (no engine parameter)
        model = PyBeePop(weather_file=sample_weather_file, latitude=35.0, verbose=False)

        assert model.engine is not None
        assert model.weather_file is not None
        assert model.current_latitude == 35.0

    def test_old_workflow_pattern(self, sample_weather_file, sample_parameters):
        """Test that old workflow pattern still works."""
        from pybeepop import PyBeePop

        # Old workflow
        model = PyBeePop()
        model.set_parameters(sample_parameters)
        model.load_weather(sample_weather_file)
        results = model.run_model()

        assert results is not None
        assert len(results) > 0

    def test_latitude_setting(self):
        """Test latitude setting works with both old and new patterns."""
        from pybeepop import PyBeePop

        # New pattern with Python engine
        model = PyBeePop(engine="python", latitude=40.0)
        assert model.get_latitude() == 40.0

        # Change latitude
        model.set_latitude(45.0)
        assert model.get_latitude() == 45.0


# ============================================================================
# Engine-Specific Feature Tests
# ============================================================================


class TestEngineSpecificFeatures:
    """Test engine-specific features and differences."""

    def test_python_engine_attributes(self):
        """Test that Python engine has expected attributes."""
        from pybeepop import PyBeePop

        model = PyBeePop(engine="python")
        assert model.engine_type == "python"
        assert hasattr(model.engine, "model")
        assert model.engine.engine_type == "python"

    def test_engine_version(self):
        """Test that version info is accessible."""
        from pybeepop import PyBeePop

        model = PyBeePop(engine="python")
        version = model.version()

        assert isinstance(version, str)
        assert len(version) > 0

    def test_error_and_info_logs(self, sample_weather_file, sample_parameters):
        """Test that error and info logs are accessible."""
        from pybeepop import PyBeePop

        model = PyBeePop(engine="python")
        model.set_parameters(sample_parameters)
        model.load_weather(sample_weather_file)
        model.run_model()

        error_log = model.get_error_log()
        info_log = model.get_info_log()

        # Should return strings (empty or with content)
        assert isinstance(error_log, str)
        assert isinstance(info_log, str)

    def test_cleanup_is_safe(self, sample_weather_file):
        """Test that cleanup/exit doesn't raise errors."""
        from pybeepop import PyBeePop

        model = PyBeePop(engine="python", weather_file=sample_weather_file)

        # Should not raise any errors
        model.exit()

        # Can call multiple times
        model.exit()


# ============================================================================
# Edge Cases and Error Handling Tests
# ============================================================================


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_invalid_latitude_raises_error(self):
        """Test that invalid latitude raises ValueError."""
        from pybeepop import PyBeePop

        with pytest.raises(ValueError, match="Latitude must be between"):
            PyBeePop(engine="python", latitude=100.0)

        with pytest.raises(ValueError, match="Latitude must be between"):
            PyBeePop(engine="python", latitude=-100.0)

    def test_nonexistent_weather_file_raises_error(self):
        """Test that nonexistent weather file raises FileNotFoundError."""
        from pybeepop import PyBeePop

        model = PyBeePop(engine="python")

        with pytest.raises(FileNotFoundError):
            model.load_weather("/nonexistent/path/to/weather.csv")

    def test_nonexistent_parameter_file_raises_error(self):
        """Test that nonexistent parameter file raises FileNotFoundError."""
        from pybeepop import PyBeePop

        model = PyBeePop(engine="python")

        with pytest.raises(FileNotFoundError):
            model.load_parameter_file("/nonexistent/path/to/params.txt")

    def test_get_output_before_run_raises_error(self):
        """Test that getting output before running raises error."""
        from pybeepop import PyBeePop

        model = PyBeePop(engine="python")

        with pytest.raises(RuntimeError, match="no results"):
            model.get_output()
