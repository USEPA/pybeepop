from pybeepop import PyBeePop
import pytest
import numpy as np
import os
import pandas as pd

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(TEST_DIR, os.pardir))


def test_integration_set_parameters():
    """Test setting parameters in the BeePop+ model."""
    beepop = PyBeePop(verbose=True)
    print(beepop.lib_file)
    test_parameters = {
        "ICWorkerAdults": 9999,
        "SimStart": "01/01/2020",
        "SimEnd": "10/31/2020",
    }
    beepop.set_parameters(test_parameters)
    params = beepop.get_parameters()
    assert "icworkeradults" in params
    assert "simstart" in params
    assert "simend" in params
    assert params["icworkeradults"] == 9999
    assert params["simstart"] == "01/01/2020"
    assert params["simend"] == "10/31/2020"


def test_integration_set_weather():
    """Test loading weather data into the BeePop+ model."""
    test_weather = os.path.join(PROJECT_DIR, "example_data/cedar_grove_NC_weather.txt")
    beepop = PyBeePop()
    beepop.load_weather(test_weather)


def test_integration_invalid_parameter():
    """Test setting an invalid parameter in the BeePop+ model."""
    beepop = PyBeePop()
    invalid_parameters = {"Invalid_parameter": 1234}
    with pytest.raises(ValueError):
        beepop.set_parameters(invalid_parameters)


def test_integration_invalid_parameter_in_file():
    """Test loading an invalid parameter from a file into the BeePop+ model."""
    beepop = PyBeePop()
    parameter_file = os.path.join(
        PROJECT_DIR, "example_data/test_parameters_invalid.txt"
    )
    with pytest.raises(ValueError):
        beepop.load_parameter_file(parameter_file)


def test_regression_run_model():
    """Run a regression test on the BeePop+ model with example data.
    This test checks if the model runs correctly with a set of predefined parameters and files.
    """
    beepop = PyBeePop(verbose=True)
    print(beepop.lib_file)

    # Define inputs and file paths
    START_DATE = "06/16/2014"
    END_DATE = "10/10/2014"
    run_parameters = {
        "ICWorkerAdults": 23000,
        "ICWorkerBrood": 8000,
        "SimStart": START_DATE,
        "SimEnd": END_DATE,
        "IPollenTrips": 8,
        "INectarTrips": 17,
        "AIAdultLD50": 0.05,  # ug/bee
    }
    weather = os.path.join(PROJECT_DIR, "example_data/cedar_grove_NC_weather.txt")
    parameter_file = os.path.join(PROJECT_DIR, "example_data/example_parameters.txt")
    residue_file = os.path.join(PROJECT_DIR, "example_data/example_residue_file.txt")

    # Load inputs into BeePop+
    beepop.set_latitude(30.0)
    beepop.load_weather(weather)
    beepop.load_parameter_file(parameter_file)
    beepop.set_parameters(run_parameters)
    beepop.load_residue_file(residue_file)

    # run model
    results = beepop.run_model()
    print(results)
    print(len(results))
    results_initial = results.iloc[0, :]
    results_last = results.iloc[len(results) - 1, :]
    results_exposure = results.iloc[20, :]

    # check results
    assert results_initial["Date"] == "Initial"
    assert results_initial["Colony Size"] == 23000
    assert results_initial["Capped Worker Brood"] == 8000
    assert results_exposure["Colony Size"] == 17913
    assert results_exposure["Capped Drone Brood"] == 219
    assert (
        round(results_exposure["Daylight hours"], 1) == 13.7
    )  # linux daylight hour issue
    assert results_exposure["Dead Foragers"] == 155
    assert results_last["Date"] == "10/10/2014"
    assert results_last["Colony Size"] in [43442, 43614]  # linux daylight hour issue
    assert results_last["Adult Drones"] in [500, 507]  # linux daylight hour issue
    assert results_last["Average Temperature (C)"] == 18.93
    assert results_last["Rain (mm)"] == 0.0


def test_init_default_lib(monkeypatch):
    # Patch os.path.isfile to always return True for library file
    monkeypatch.setattr(os.path, "isfile", lambda x: True)
    # Patch BeePopModel to a dummy class to avoid loading actual library
    import pybeepop.pybeepop as pbp
    import pybeepop.tools as tools

    class DummyBeePopModel:
        def __init__(self, *a, **k):
            self.latitude = 30.0

        def set_parameters(self, p):
            return p

        def get_parameters(self):
            return {"icworkeradults": 1000}

        def set_latitude(self, lat):
            self.latitude = lat

        def get_latitude(self):
            return self.latitude

        def load_weather(self, f):
            pass

        def load_input_file(self, f):
            pass

        def load_contam_file(self, f):
            pass

        def run_beepop(self):
            import pandas as pd

            return pd.DataFrame({"Colony Size": [1], "Date": ["Initial"]})

        def get_errors(self):
            return "No errors"

        def get_info(self):
            return "Info"

        def get_version(self):
            return "1.0"

        def close_library(self):
            pass

    monkeypatch.setattr(tools, "BeePopModel", DummyBeePopModel)
    beepop = PyBeePop()
    assert hasattr(beepop, "beepop")
    assert beepop.lib_file.endswith(".dll") or beepop.lib_file.endswith(".so")


def test_set_parameters_type_error(monkeypatch):
    import pybeepop.pybeepop as pbp
    import pybeepop.tools as tools
    import pybeepop.tools as tools

    class DummyBeePopModel:
        def __init__(self, *a, **k):
            self.latitude = 30.0

        def set_parameters(self, p):
            return p

        def get_parameters(self):
            return {}

        def set_latitude(self, lat):
            self.latitude = lat

        def get_latitude(self):
            return self.latitude

    monkeypatch.setattr(os.path, "isfile", lambda x: True)
    monkeypatch.setattr(tools, "BeePopModel", DummyBeePopModel)
    beepop = PyBeePop()
    with pytest.raises(TypeError):
        beepop.set_parameters(["not", "a", "dict"])


def test_set_parameters_and_get(monkeypatch):
    import pybeepop.pybeepop as pbp
    import pybeepop.tools as tools

    class DummyBeePopModel:
        def __init__(self, *a, **k):
            self.latitude = 30.0

        def set_parameters(self, p):
            return p

        def get_parameters(self):
            return {"icworkeradults": 123}

        def set_latitude(self, lat):
            self.latitude = lat

        def get_latitude(self):
            return self.latitude

    monkeypatch.setattr(os.path, "isfile", lambda x: True)
    monkeypatch.setattr(tools, "BeePopModel", DummyBeePopModel)
    beepop = PyBeePop()
    beepop.set_parameters({"ICWorkerAdults": 123})
    params = beepop.get_parameters()
    assert "icworkeradults" in params
    assert params["icworkeradults"] == 123


def test_load_weather_file_not_found(monkeypatch):
    import pybeepop.pybeepop as pbp
    import pybeepop.tools as tools

    class DummyBeePopModel:
        def __init__(self, *a, **k):
            self.latitude = 30.0

        def set_parameters(self, p):
            return p

        def get_parameters(self):
            return {}

        def set_latitude(self, lat):
            self.latitude = lat

        def get_latitude(self):
            return self.latitude

        def load_weather(self, f):
            pass

    beepop = PyBeePop()
    monkeypatch.setattr(os.path, "isfile", lambda x: False)
    monkeypatch.setattr(tools, "BeePopModel", DummyBeePopModel)
    with pytest.raises(FileNotFoundError):
        beepop.load_weather("nonexistent_file.txt")


def test_load_parameter_file_not_found(monkeypatch):
    import pybeepop.pybeepop as pbp
    import pybeepop.tools as tools

    class DummyBeePopModel:
        def __init__(self, *a, **k):
            self.latitude = 30.0

        def set_parameters(self, p):
            return p

        def get_parameters(self):
            return {}

        def set_latitude(self, lat):
            self.latitude = lat

        def get_latitude(self):
            return self.latitude

        def load_input_file(self, f):
            pass

    beepop = PyBeePop()
    monkeypatch.setattr(os.path, "isfile", lambda x: False)
    monkeypatch.setattr(tools, "BeePopModel", DummyBeePopModel)
    with pytest.raises(FileNotFoundError):
        beepop.load_parameter_file("nonexistent_param.txt")


def test_load_residue_file_not_found(monkeypatch):
    import pybeepop.pybeepop as pbp
    import pybeepop.tools as tools

    class DummyBeePopModel:
        def __init__(self, *a, **k):
            self.latitude = 30.0

        def set_parameters(self, p):
            return p

        def get_parameters(self):
            return {}

        def set_latitude(self, lat):
            self.latitude = lat

        def get_latitude(self):
            return self.latitude

        def load_contam_file(self, f):
            pass

    beepop = PyBeePop()
    monkeypatch.setattr(os.path, "isfile", lambda x: False)
    monkeypatch.setattr(tools, "BeePopModel", DummyBeePopModel)
    with pytest.raises(FileNotFoundError):
        beepop.load_residue_file("nonexistent_residue.txt")


def test_run_model_no_weather(monkeypatch):
    import pybeepop.pybeepop as pbp
    import pybeepop.tools as tools

    class DummyBeePopModel:
        def __init__(self, *a, **k):
            self.latitude = 30.0

        def set_parameters(self, p):
            return p

        def get_parameters(self):
            return {}

        def set_latitude(self, lat):
            self.latitude = lat

        def get_latitude(self):
            return self.latitude

        def run_beepop(self):
            return None

    monkeypatch.setattr(os.path, "isfile", lambda x: True)
    monkeypatch.setattr(tools, "BeePopModel", DummyBeePopModel)
    beepop = PyBeePop()
    beepop.weather_file = None
    with pytest.raises(RuntimeError):
        beepop.run_model()


def test_get_output_json(monkeypatch):
    import pybeepop.pybeepop as pbp
    import pybeepop.tools as tools

    class DummyBeePopModel:
        def __init__(self, *a, **k):
            self.latitude = 30.0

        def set_parameters(self, p):
            return p

        def get_parameters(self):
            return {}

        def set_latitude(self, lat):
            self.latitude = lat

        def get_latitude(self):
            return self.latitude

        def run_beepop(self):
            return pd.DataFrame({"Colony Size": [1], "Date": ["Initial"]})

    monkeypatch.setattr(os.path, "isfile", lambda x: True)
    monkeypatch.setattr(tools, "BeePopModel", DummyBeePopModel)
    beepop = PyBeePop()
    beepop.output = pd.DataFrame({"Colony Size": [1], "Date": ["Initial"]})
    result = beepop.get_output(format="json")
    assert isinstance(result, str)
    assert '"Colony Size": [1]' in result


def test_get_output_no_output(monkeypatch):
    import pybeepop.pybeepop as pbp
    import pybeepop.tools as tools

    class DummyBeePopModel:
        def __init__(self, *a, **k):
            self.latitude = 30.0

        def set_parameters(self, p):
            return p

        def get_parameters(self):
            return {}

        def set_latitude(self, lat):
            self.latitude = lat

        def get_latitude(self):
            return self.latitude

    monkeypatch.setattr(os.path, "isfile", lambda x: True)
    monkeypatch.setattr(tools, "BeePopModel", DummyBeePopModel)
    beepop = PyBeePop()
    beepop.output = None
    with pytest.raises(RuntimeError):
        beepop.get_output()


def test_plot_output_invalid_column(monkeypatch):
    import pybeepop.pybeepop as pbp
    import pybeepop.tools as tools

    class DummyBeePopModel:
        def __init__(self, *a, **k):
            self.latitude = 30.0

        def set_parameters(self, p):
            return p

        def get_parameters(self):
            return {}

        def set_latitude(self, lat):
            self.latitude = lat

        def get_latitude(self):
            return self.latitude

    def dummy_plot_timeseries(output, columns):
        return None

    monkeypatch.setattr(os.path, "isfile", lambda x: True)
    monkeypatch.setattr(tools, "BeePopModel", DummyBeePopModel)
    monkeypatch.setattr(pbp, "plot_timeseries", dummy_plot_timeseries)
    beepop = PyBeePop()
    beepop.output = pd.DataFrame({"Colony Size": [1], "Date": ["Initial"]})
    with pytest.raises(IndexError):
        beepop.plot_output(columns=["NotAColumn"])


def test_get_error_and_info_log(monkeypatch):
    import pybeepop.pybeepop as pbp
    import pybeepop.tools as tools
    import pybeepop.tools as tools

    class DummyBeePopModel:
        def __init__(self, *a, **k):
            self.latitude = 30.0

        def set_latitude(self, lat):
            self.latitude = lat

        def get_latitude(self):
            return self.latitude

        def get_errors(self):
            return "error log"

        def get_info(self):
            return "info log"

    monkeypatch.setattr(os.path, "isfile", lambda x: True)
    monkeypatch.setattr(tools, "BeePopModel", DummyBeePopModel)
    beepop = PyBeePop()
    assert beepop.get_error_log() == "error log"
    assert beepop.get_info_log() == "info log"


def test_version_and_exit(monkeypatch):
    import pybeepop.pybeepop as pbp
    import pybeepop.tools as tools
    import pybeepop.tools as tools

    class DummyBeePopModel:
        def __init__(self, *a, **k):
            self.latitude = 30.0

        def set_latitude(self, lat):
            self.latitude = lat

        def get_latitude(self):
            return self.latitude

        def get_version(self):
            return "2.1"

        def close_library(self):
            self.closed = True

    monkeypatch.setattr(os.path, "isfile", lambda x: True)
    monkeypatch.setattr(tools, "BeePopModel", DummyBeePopModel)
    beepop = PyBeePop()
    assert beepop.version() == "2.1"
    beepop.exit()


def test_set_latitude():
    """Test setting and getting latitude with real model."""
    beepop = PyBeePop(verbose=False)

    # Test default latitude
    default_lat = beepop.get_latitude()
    assert isinstance(default_lat, (int, float))
    assert default_lat == 30.0  # Default latitude set in __init__

    # Test setting different latitudes
    test_latitudes = [0, 30, 45, 60, 90]
    for lat in test_latitudes:
        beepop.set_latitude(lat)
        retrieved_lat = beepop.get_latitude()
        assert retrieved_lat == lat, f"Expected {lat}, got {retrieved_lat}"


def test_latitude_effects_on_daylight():
    """Test that different latitudes produce different daylight hour patterns."""
    weather_file = os.path.join(PROJECT_DIR, "example_data/cedar_grove_NC_weather.txt")

    # Test parameters for a short simulation
    test_params = {
        "ICWorkerAdults": 10000,
        "SimStart": "06/16/2014",
        "SimEnd": "08/16/2014",
    }

    # Test two different latitudes
    latitudes = [0, 60]  # Equator vs high latitude
    daylight_results = {}

    for lat in latitudes:
        beepop = PyBeePop(verbose=False)
        beepop.set_latitude(lat)
        beepop.load_weather(weather_file)
        beepop.set_parameters(test_params)

        results = beepop.run_model()
        daylight_hours = results["Daylight hours"].tolist()[1:]  # Skip 'Initial' row
        daylight_results[lat] = daylight_hours

    # Different latitudes should produce different daylight patterns
    equator_daylight = daylight_results[0]
    high_lat_daylight = daylight_results[60]

    # At least some values should be different
    assert (
        equator_daylight != high_lat_daylight
    ), "Different latitudes should produce different daylight patterns"

    # Equator should have less variation (closer to 12 hours year-round)
    equator_range = max(equator_daylight) - min(equator_daylight)
    high_lat_range = max(high_lat_daylight) - min(high_lat_daylight)

    # High latitude should have more variation in summer
    assert (
        high_lat_range > equator_range
    ), "High latitude should have more daylight variation"


def test_latitude_inheritance_reset():
    """Test that new PyBeePop instances reset latitude to default."""
    # Create first instance and set latitude
    beepop1 = PyBeePop(verbose=False)
    beepop1.set_latitude(65)
    assert beepop1.get_latitude() == 65

    # Create second instance - should have default latitude, not inherit
    beepop2 = PyBeePop(verbose=False)
    default_lat = beepop2.get_latitude()
    assert (
        default_lat == 30.0
    ), f"New instance should have default latitude 30.0, got {default_lat}"


def test_set_simulation_dates():
    """Test the new set_simulation_dates convenience method."""
    beepop = PyBeePop(verbose=False)

    start_date = "01/01/2020"
    end_date = "12/31/2020"

    beepop.set_simulation_dates(start_date, end_date)
    params = beepop.get_parameters()

    assert "simstart" in params
    assert "simend" in params
    assert params["simstart"] == start_date
    assert params["simend"] == end_date


def test_load_weather_preserves_simulation_dates():
    """Test that loading weather doesn't overwrite previously set simulation dates."""
    weather_file = os.path.join(PROJECT_DIR, "example_data/cedar_grove_NC_weather.txt")
    beepop = PyBeePop(verbose=False)

    # Set specific simulation dates
    custom_start = "07/01/2014"
    custom_end = "08/31/2014"
    beepop.set_simulation_dates(custom_start, custom_end)

    # Verify dates are set
    params_before = beepop.get_parameters()
    assert params_before["simstart"] == custom_start
    assert params_before["simend"] == custom_end

    # Load weather (this previously overwrote dates)
    beepop.load_weather(weather_file)

    # Verify dates are preserved
    params_after = beepop.get_parameters()
    assert (
        params_after["simstart"] == custom_start
    ), f"SimStart changed from {custom_start} to {params_after.get('simstart')}"
    assert (
        params_after["simend"] == custom_end
    ), f"SimEnd changed from {custom_end} to {params_after.get('simend')}"


def test_latitude_edge_cases():
    """Test latitude setting with edge cases and invalid values."""
    beepop = PyBeePop(verbose=False)

    # Test extreme but valid latitudes
    valid_latitudes = [-90, -45, 0, 45, 90]
    for lat in valid_latitudes:
        beepop.set_latitude(lat)
        assert beepop.get_latitude() == lat

    with pytest.raises(ValueError):
        beepop.set_latitude(180)  # Invalid


def test_comprehensive_latitude_workflow():
    """Test a complete workflow with latitude changes and model runs."""
    weather_file = os.path.join(PROJECT_DIR, "example_data/cedar_grove_NC_weather.txt")

    beepop = PyBeePop(verbose=False)

    # Set latitude before loading anything
    beepop.set_latitude(55)
    assert beepop.get_latitude() == 55

    # Load weather and parameters
    beepop.load_weather(weather_file)
    beepop.set_parameters(
        {"ICWorkerAdults": 12000, "SimStart": "06/16/2014", "SimEnd": "07/16/2014"}
    )

    # Latitude should still be set
    assert beepop.get_latitude() == 55

    # Run model
    results = beepop.run_model()
    assert len(results) > 1
    assert "Daylight hours" in results.columns

    # Change latitude and run again
    beepop.set_latitude(25)
    results2 = beepop.run_model()

    # Results should be different due to latitude change
    daylight1 = results["Daylight hours"].tolist()[1:]  # Skip 'Initial'
    daylight2 = results2["Daylight hours"].tolist()[1:]

    # At least some daylight values should be different
    assert daylight1 != daylight2, "Changing latitude should affect daylight hours"
