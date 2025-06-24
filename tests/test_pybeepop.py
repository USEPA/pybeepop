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
    assert results_last["Date"] == "10/09/2014"
    assert results_last["Colony Size"] in [43932, 44087]  # linux daylight hour issue
    assert results_last["Adult Drones"] == 512
    assert results_last["Average Temperature (C)"] == 16.66
    assert results_last["Rain (mm)"] == 0.0


def test_init_default_lib(monkeypatch):
    # Patch os.path.isfile to always return True for library file
    monkeypatch.setattr(os.path, "isfile", lambda x: True)
    # Patch BeePopModel to a dummy class to avoid loading actual library
    import pybeepop.pybeepop as pbp

    class DummyBeePopModel:
        def __init__(self, *a, **k):
            pass

        def set_parameters(self, p):
            return p

        def get_parameters(self):
            return {"icworkeradults": 1000}

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

    monkeypatch.setattr(pbp, "BeePopModel", DummyBeePopModel)
    beepop = PyBeePop()
    assert hasattr(beepop, "beepop")
    assert beepop.lib_file.endswith(".dll") or beepop.lib_file.endswith(".so")


def test_set_parameters_type_error(monkeypatch):
    import pybeepop.pybeepop as pbp

    class DummyBeePopModel:
        def __init__(self, *a, **k):
            pass

        def set_parameters(self, p):
            return p

        def get_parameters(self):
            return {}

    monkeypatch.setattr(os.path, "isfile", lambda x: True)
    monkeypatch.setattr(pbp, "BeePopModel", DummyBeePopModel)
    beepop = PyBeePop()
    with pytest.raises(TypeError):
        beepop.set_parameters(["not", "a", "dict"])


def test_set_parameters_and_get(monkeypatch):
    import pybeepop.pybeepop as pbp

    class DummyBeePopModel:
        def __init__(self, *a, **k):
            pass

        def set_parameters(self, p):
            return p

        def get_parameters(self):
            return {"icworkeradults": 123}

    monkeypatch.setattr(os.path, "isfile", lambda x: True)
    monkeypatch.setattr(pbp, "BeePopModel", DummyBeePopModel)
    beepop = PyBeePop()
    beepop.set_parameters({"ICWorkerAdults": 123})
    params = beepop.get_parameters()
    assert "icworkeradults" in params
    assert params["icworkeradults"] == 123


def test_load_weather_file_not_found(monkeypatch):
    import pybeepop.pybeepop as pbp

    class DummyBeePopModel:
        def __init__(self, *a, **k):
            pass

        def set_parameters(self, p):
            return p

        def get_parameters(self):
            return {}

        def load_weather(self, f):
            pass

    beepop = PyBeePop()
    monkeypatch.setattr(os.path, "isfile", lambda x: False)
    monkeypatch.setattr(pbp, "BeePopModel", DummyBeePopModel)
    with pytest.raises(FileNotFoundError):
        beepop.load_weather("nonexistent_file.txt")


def test_load_parameter_file_not_found(monkeypatch):
    import pybeepop.pybeepop as pbp

    class DummyBeePopModel:
        def __init__(self, *a, **k):
            pass

        def set_parameters(self, p):
            return p

        def get_parameters(self):
            return {}

        def load_input_file(self, f):
            pass

    beepop = PyBeePop()
    monkeypatch.setattr(os.path, "isfile", lambda x: False)
    monkeypatch.setattr(pbp, "BeePopModel", DummyBeePopModel)
    with pytest.raises(FileNotFoundError):
        beepop.load_parameter_file("nonexistent_param.txt")


def test_load_residue_file_not_found(monkeypatch):
    import pybeepop.pybeepop as pbp

    class DummyBeePopModel:
        def __init__(self, *a, **k):
            pass

        def set_parameters(self, p):
            return p

        def get_parameters(self):
            return {}

        def load_contam_file(self, f):
            pass

    beepop = PyBeePop()
    monkeypatch.setattr(os.path, "isfile", lambda x: False)
    monkeypatch.setattr(pbp, "BeePopModel", DummyBeePopModel)
    with pytest.raises(FileNotFoundError):
        beepop.load_residue_file("nonexistent_residue.txt")


def test_run_model_no_weather(monkeypatch):
    import pybeepop.pybeepop as pbp

    class DummyBeePopModel:
        def __init__(self, *a, **k):
            pass

        def set_parameters(self, p):
            return p

        def get_parameters(self):
            return {}

        def run_beepop(self):
            return None

    monkeypatch.setattr(os.path, "isfile", lambda x: True)
    monkeypatch.setattr(pbp, "BeePopModel", DummyBeePopModel)
    beepop = PyBeePop()
    beepop.weather_file = None
    with pytest.raises(RuntimeError):
        beepop.run_model()


def test_get_output_json(monkeypatch):
    import pybeepop.pybeepop as pbp

    class DummyBeePopModel:
        def __init__(self, *a, **k):
            pass

        def set_parameters(self, p):
            return p

        def get_parameters(self):
            return {}

        def run_beepop(self):
            return pd.DataFrame({"Colony Size": [1], "Date": ["Initial"]})

    monkeypatch.setattr(os.path, "isfile", lambda x: True)
    monkeypatch.setattr(pbp, "BeePopModel", DummyBeePopModel)
    beepop = PyBeePop()
    beepop.output = pd.DataFrame({"Colony Size": [1], "Date": ["Initial"]})
    result = beepop.get_output(format="json")
    assert isinstance(result, str)
    assert '"Colony Size": [1]' in result


def test_get_output_no_output(monkeypatch):
    import pybeepop.pybeepop as pbp

    class DummyBeePopModel:
        def __init__(self, *a, **k):
            pass

        def set_parameters(self, p):
            return p

        def get_parameters(self):
            return {}

    monkeypatch.setattr(os.path, "isfile", lambda x: True)
    monkeypatch.setattr(pbp, "BeePopModel", DummyBeePopModel)
    beepop = PyBeePop()
    beepop.output = None
    with pytest.raises(RuntimeError):
        beepop.get_output()


def test_plot_output_invalid_column(monkeypatch):
    import pybeepop.pybeepop as pbp

    class DummyBeePopModel:
        def __init__(self, *a, **k):
            pass

        def set_parameters(self, p):
            return p

        def get_parameters(self):
            return {}

    def dummy_plot_timeseries(output, columns):
        return None

    monkeypatch.setattr(os.path, "isfile", lambda x: True)
    monkeypatch.setattr(pbp, "BeePopModel", DummyBeePopModel)
    monkeypatch.setattr(pbp, "plot_timeseries", dummy_plot_timeseries)
    beepop = PyBeePop()
    beepop.output = pd.DataFrame({"Colony Size": [1], "Date": ["Initial"]})
    with pytest.raises(IndexError):
        beepop.plot_output(columns=["NotAColumn"])


def test_get_error_and_info_log(monkeypatch):
    import pybeepop.pybeepop as pbp

    class DummyBeePopModel:
        def __init__(self, *a, **k):
            pass

        def get_errors(self):
            return "error log"

        def get_info(self):
            return "info log"

    monkeypatch.setattr(os.path, "isfile", lambda x: True)
    monkeypatch.setattr(pbp, "BeePopModel", DummyBeePopModel)
    beepop = PyBeePop()
    assert beepop.get_error_log() == "error log"
    assert beepop.get_info_log() == "info log"


def test_version_and_exit(monkeypatch):
    import pybeepop.pybeepop as pbp

    class DummyBeePopModel:
        def __init__(self, *a, **k):
            pass

        def get_version(self):
            return "2.1"

        def close_library(self):
            self.closed = True

    monkeypatch.setattr(os.path, "isfile", lambda x: True)
    monkeypatch.setattr(pbp, "BeePopModel", DummyBeePopModel)
    beepop = PyBeePop()
    assert beepop.version() == "2.1"
    beepop.exit()
