"""
Dual-engine integration and exception parity tests for PyBeePop.

This module verifies that PyBeePop works correctly with both C++ and Python engines,
including:
- Engine selection and initialization
- Parameter handling and file loading
- Simulation execution
- Exception consistency between engines
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

        with pytest.raises(ValueError, match="Must be 'cpp' or 'python'"):
            PyBeePop(engine="auto")

    def test_python_engine_selection(self):
        """Test forcing Python engine."""
        from pybeepop import PyBeePop

        model = PyBeePop(engine="python")
        assert model.engine_type == "python"
        assert model.engine is not None

    def test_cpp_engine_selection_with_lib(self):
        """Test forcing C++ engine (if library available)."""
        from pybeepop import PyBeePop

        try:
            model = PyBeePop(engine="cpp")
            assert model.engine_type == "cpp"
            assert model.engine is not None
        except (FileNotFoundError, NotImplementedError):
            pytest.skip("C++ library not available on this platform")

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
    """Test parameter handling with both engines."""

    @pytest.mark.parametrize("engine_type", ["python", "cpp"])
    def test_set_parameters(self, engine_type, sample_parameters):
        """Test setting parameters with both engines."""
        from pybeepop import PyBeePop

        try:
            model = PyBeePop(engine=engine_type)
            model.set_parameters(sample_parameters)

            retrieved = model.get_parameters()
            # Check that key parameters were set
            assert "ICWorkerAdults" in retrieved or len(retrieved) > 0
        except (FileNotFoundError, NotImplementedError):
            if engine_type == "cpp":
                pytest.skip("C++ engine not available")
            raise

    @pytest.mark.parametrize("engine_type", ["python", "cpp"])
    def test_load_parameter_file(self, engine_type, sample_parameter_file):
        """Test loading parameter file with both engines."""
        from pybeepop import PyBeePop

        try:
            model = PyBeePop(engine=engine_type)
            model.load_parameter_file(sample_parameter_file)

            # Verify parameters were loaded
            params = model.get_parameters()
            assert len(params) > 0  # Should have some parameters
        except (FileNotFoundError, NotImplementedError):
            if engine_type == "cpp":
                pytest.skip("C++ engine not available")
            raise

    def test_parameter_file_in_constructor_python(self, sample_parameter_file):
        """Test loading parameter file via constructor with Python engine."""
        from pybeepop import PyBeePop

        model = PyBeePop(engine="python", parameter_file=sample_parameter_file)
        params = model.get_parameters()
        assert len(params) > 0


# ============================================================================
# Simulation Execution Tests
# ============================================================================


class TestSimulationExecution:
    """Test running simulations with both engines."""

    @pytest.mark.parametrize("engine_type", ["python", "cpp"])
    def test_run_simulation(self, engine_type, sample_weather_file, sample_parameters):
        """Test running simulation with both engines."""
        from pybeepop import PyBeePop

        try:
            model = PyBeePop(engine=engine_type)
            model.set_parameters(sample_parameters)
            model.load_weather(sample_weather_file)

            results = model.run_model()

            # Verify results structure
            assert results is not None
            assert len(results) > 0
            assert "Date" in results.columns
            # Both engines should produce colony size data
            assert any("Colony" in col or "Adult" in col for col in results.columns)
        except (FileNotFoundError, NotImplementedError):
            if engine_type == "cpp":
                pytest.skip("C++ engine not available")
            raise

    def test_simulation_without_weather_raises_error(self):
        """Test that simulation without weather raises error."""
        from pybeepop import PyBeePop

        model = PyBeePop(engine="python")

        with pytest.raises(RuntimeError, match="Weather must be set"):
            model.run_model()

    def test_weather_file_in_constructor_python(
        self, sample_weather_file, sample_parameters
    ):
        """Test loading weather file via constructor with Python engine."""
        from pybeepop import PyBeePop

        model = PyBeePop(engine="python", weather_file=sample_weather_file)
        model.set_parameters(sample_parameters)
        results = model.run_model()

        assert results is not None
        assert len(results) > 0


# ============================================================================
# Exception Parity Tests
# ============================================================================


class TestExceptionParity:
    """Test that both engines raise identical exceptions for error conditions."""

    @pytest.mark.parametrize("engine_type", ["python", "cpp"])
    def test_invalid_parameter_raises_valueerror(self, engine_type):
        """Both engines should raise ValueError for invalid parameter names."""
        from pybeepop import PyBeePop

        try:
            model = PyBeePop(engine=engine_type)
            with pytest.raises(ValueError, match="is not a valid parameter"):
                model.set_parameters({"Invalid_Parameter_Name": "123"})
        except (FileNotFoundError, NotImplementedError):
            if engine_type == "cpp":
                pytest.skip("C++ engine not available")
            raise

    @pytest.mark.parametrize("engine_type", ["python", "cpp"])
    def test_wrong_parameter_type_raises_typeerror(self, engine_type):
        """Both engines should raise TypeError for non-dict parameters."""
        from pybeepop import PyBeePop

        try:
            model = PyBeePop(engine=engine_type)
            with pytest.raises(TypeError, match="must be a named dictionary"):
                model.set_parameters(["not", "a", "dict"])
        except (FileNotFoundError, NotImplementedError):
            if engine_type == "cpp":
                pytest.skip("C++ engine not available")
            raise

    @pytest.mark.parametrize("engine_type", ["python", "cpp"])
    def test_none_weather_file_raises_typeerror(self, engine_type):
        """Both engines should raise TypeError when weather_file is None."""
        from pybeepop import PyBeePop

        try:
            model = PyBeePop(engine=engine_type)
            with pytest.raises(TypeError, match="Cannot set weather file to None"):
                model.load_weather(None)
        except (FileNotFoundError, NotImplementedError):
            if engine_type == "cpp":
                pytest.skip("C++ engine not available")
            raise

    @pytest.mark.parametrize("engine_type", ["python", "cpp"])
    def test_missing_weather_file_raises_filenotfounderror(self, engine_type):
        """Both engines should raise FileNotFoundError for missing weather file."""
        from pybeepop import PyBeePop

        try:
            model = PyBeePop(engine=engine_type)
            with pytest.raises(FileNotFoundError):
                model.load_weather("nonexistent_weather.txt")
        except (FileNotFoundError, NotImplementedError) as e:
            if engine_type == "cpp" and (
                "library" in str(e).lower() or isinstance(e, NotImplementedError)
            ):
                pytest.skip("C++ engine not available")
            raise

    @pytest.mark.parametrize("engine_type", ["python", "cpp"])
    def test_missing_parameter_file_raises_filenotfounderror(self, engine_type):
        """Both engines should raise FileNotFoundError for missing parameter file."""
        from pybeepop import PyBeePop

        try:
            model = PyBeePop(engine=engine_type)
            with pytest.raises(FileNotFoundError):
                model.load_parameter_file("nonexistent_params.txt")
        except (FileNotFoundError, NotImplementedError) as e:
            if engine_type == "cpp" and (
                "library" in str(e).lower() or isinstance(e, NotImplementedError)
            ):
                pytest.skip("C++ engine not available")
            raise

    @pytest.mark.parametrize("engine_type", ["python", "cpp"])
    def test_missing_residue_file_raises_filenotfounderror(self, engine_type):
        """Both engines should raise FileNotFoundError for missing residue file."""
        from pybeepop import PyBeePop

        try:
            model = PyBeePop(engine=engine_type)
            with pytest.raises(FileNotFoundError):
                model.load_residue_file("nonexistent_residue.txt")
        except (FileNotFoundError, NotImplementedError) as e:
            if engine_type == "cpp" and (
                "library" in str(e).lower() or isinstance(e, NotImplementedError)
            ):
                pytest.skip("C++ engine not available")
            raise

    @pytest.mark.parametrize("engine_type", ["python", "cpp"])
    def test_invalid_parameter_in_file_raises_valueerror(self, engine_type, tmp_path):
        """Both engines should raise ValueError for invalid parameters in file."""
        from pybeepop import PyBeePop

        # Create a parameter file with invalid parameter
        param_file = tmp_path / "invalid_params.txt"
        param_file.write_text("InvalidParameterName=12345\n")

        try:
            model = PyBeePop(engine=engine_type)
            with pytest.raises(ValueError, match="is not a valid parameter"):
                model.load_parameter_file(str(param_file))
        except (FileNotFoundError, NotImplementedError):
            if engine_type == "cpp":
                pytest.skip("C++ engine not available")
            raise

    @pytest.mark.parametrize("engine_type", ["python", "cpp"])
    def test_run_without_weather_raises_runtimeerror(self, engine_type):
        """Both engines should raise RuntimeError when running without weather."""
        from pybeepop import PyBeePop

        try:
            model = PyBeePop(engine=engine_type)
            model.set_parameters({"ICWorkerAdults": "10000"})
            with pytest.raises(RuntimeError, match="Weather must be set"):
                model.run_model()
        except (FileNotFoundError, NotImplementedError):
            if engine_type == "cpp":
                pytest.skip("C++ engine not available")
            raise

    @pytest.mark.parametrize("engine_type", ["python", "cpp"])
    def test_invalid_weather_file_format_raises_oserror(self, engine_type, tmp_path):
        """Both engines should raise OSError for invalid weather file format."""
        from pybeepop import PyBeePop

        # Create a weather file with invalid content
        weather_file = tmp_path / "invalid_weather.txt"
        weather_file.write_text("This is not valid weather data\n")

        try:
            model = PyBeePop(engine=engine_type)
            # This should raise OSError or RuntimeError depending on how badly formatted
            with pytest.raises((OSError, RuntimeError)):
                model.load_weather(str(weather_file))
        except (FileNotFoundError, NotImplementedError):
            if engine_type == "cpp":
                pytest.skip("C++ engine not available")
            raise


class TestExceptionMessages:
    """Test that exception messages are consistent between engines."""

    def test_invalid_parameter_message_format_python(self):
        """Python engine should provide helpful parameter error messages."""
        from pybeepop import PyBeePop

        model = PyBeePop(engine="python")
        with pytest.raises(ValueError) as exc_info:
            model.set_parameters({"BadParam": "123"})

        error_msg = str(exc_info.value).lower()
        assert "badparam" in error_msg or "not a valid parameter" in error_msg

    def test_invalid_parameter_message_format_cpp(self):
        """C++ engine should provide helpful parameter error messages."""
        from pybeepop import PyBeePop

        try:
            model = PyBeePop(engine="cpp")
            with pytest.raises(ValueError) as exc_info:
                model.set_parameters({"BadParam": "123"})

            error_msg = str(exc_info.value).lower()
            assert "badparam" in error_msg or "not a valid parameter" in error_msg
        except (FileNotFoundError, NotImplementedError):
            pytest.skip("C++ engine not available")


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
        """Test that logging works with both engines."""
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
