import pytest
import ctypes
import pandas as pd
from pybeepop.tools import StringList2CPA, BeePopModel, colnames


class DummyLib:
    """A dummy shared library to mock C++ functions for BeePopModel."""

    def __init__(self):
        self.init_called = False
        self.buffers_cleared = False
        self.icvars_set = False
        self.weather_set = False
        self.contam_set = False
        self.latitude_set = False
        self.simulation_run = False
        self.results_cleared = False
        self.error_list = [b"Error1", b"Error2"]
        self.info_list = [b"Info1", b"Info2"]
        self.version = b"1.2.3"
        self._handle = 123

    def InitializeModel(self):
        self.init_called = True
        return True

    def ClearResultsBuffer(self):
        self.results_cleared = True
        return True

    def ClearErrorList(self):
        return True

    def ClearInfoList(self):
        return True

    def SetICVariablesCPA(self, CPA, n):
        self.icvars_set = True
        return True

    def SetWeatherCPA(self, CPA, n):
        self.weather_set = True
        return True

    def SetContaminationTableCPA(self, CPA, n):
        self.contam_set = True
        return True

    def SetLatitude(self, lat):
        self.latitude_set = True
        return True

    def RunSimulation(self):
        self.simulation_run = True
        return True

    def GetResultsCPA(self, p_Results, theCount):
        lines = [
            b"Header1",
            b"Header2",
            b"Header3",
            b"2023-01-01 1000 10 990 500 400 20 30 5 10 2 8 10 1 2 3 4 5 6 7 8 9 0.1 0.2 0.3 0.4 100 0.5 200 0.6 1 2 3 4 5 1 20.0 0.0 10.0 30.0 12.0 1 1",
        ]
        arr = (ctypes.c_char_p * len(lines))()
        for i, l in enumerate(lines):
            arr[i] = l
        self._last_results = arr
        self._last_count = len(lines)
        return True

    def GetErrorListCPA(self, p_Errors, count):
        arr = (ctypes.c_char_p * len(self.error_list))()
        for i, l in enumerate(self.error_list):
            arr[i] = l
        self._last_errors = arr
        self._last_error_count = len(self.error_list)
        return True

    def GetInfoListCPA(self, p_Info, count):
        arr = (ctypes.c_char_p * len(self.info_list))()
        for i, l in enumerate(self.info_list):
            arr[i] = l
        self._last_info = arr
        self._last_info_count = len(self.info_list)
        return True

    def GetLibVersionCP(self, version_buffer, buffsize):
        version_buffer.value = self.version
        return True


@pytest.fixture
def monkeypatch_beepop(monkeypatch, tmp_path):
    # Patch pd.read_csv to return a dummy valid_parameters list
    valid_params = pd.DataFrame(
        {"Exposed Variable Name": ["param1", "NecPolFileEnable"]}
    )
    monkeypatch.setattr(pd, "read_csv", lambda *a, **k: valid_params)
    # Patch ctypes.CDLL to return DummyLib
    monkeypatch.setattr("ctypes.CDLL", lambda *a, **k: DummyLib())
    # Patch os.path.join to just join with "/"
    monkeypatch.setattr("os.path.join", lambda *a: "/".join(a))
    # Patch os.path.abspath to identity
    monkeypatch.setattr("os.path.abspath", lambda x: x)
    # Patch os.path.dirname to parent dir
    monkeypatch.setattr("os.path.dirname", lambda x: "/".join(x.split("/")[:-1]))
    return tmp_path


def test_StringList2CPA():
    input_list = ["abc", "def"]
    result = StringList2CPA(input_list)
    assert result == [b"abc", b"def"]


def test_BeePopModel_init(monkeypatch_beepop):
    model = BeePopModel("dummy.so")
    assert isinstance(model, BeePopModel)
    assert hasattr(model, "parameters")
    assert model.lib.init_called


def test_BeePopModel_set_parameters(monkeypatch_beepop):
    model = BeePopModel("dummy.so")
    model.valid_parameters.append("param1")
    params = {"param1": "value1"}
    model.set_parameters(params)
    assert "param1" in model.parameters
    assert model.lib.icvars_set


def test_BeePopModel_send_pars_to_beepop_valid(monkeypatch_beepop):
    model = BeePopModel("dummy.so")
    model.valid_parameters.append("param1")
    model.send_pars_to_beepop(["param1=value1"])
    assert model.lib.icvars_set


def test_BeePopModel_send_pars_to_beepop_invalid(monkeypatch_beepop):
    model = BeePopModel("dummy.so")
    with pytest.raises(ValueError):
        model.send_pars_to_beepop(["notaparam=value"])


def test_BeePopModel_get_parameters(monkeypatch_beepop):
    model = BeePopModel("dummy.so")
    model.parameters = {"param1": "value1"}
    assert model.get_parameters() == {"param1": "value1"}


def test_BeePopModel_run_beepop(monkeypatch_beepop):
    model = BeePopModel("dummy.so")
    import pybeepop.tools

    pybeepop.tools.colnames = colnames
    df = model.run_beepop()
    # Check DummyLib's stored results, cannot simulate C+ library behavior
    assert hasattr(model.lib, "_last_results")
    assert hasattr(model.lib, "_last_count")
    assert model.lib._last_count == 4  # 4 lines in dummy data


def test_BeePopModel_get_errors(monkeypatch_beepop):
    model = BeePopModel("dummy.so")
    errors = model.get_errors()
    # Check DummyLib's stored results, cannot simulate C+ library behavior
    assert hasattr(model.lib, "_last_errors")
    assert hasattr(model.lib, "_last_error_count")
    assert model.lib._last_error_count == 2


def test_BeePopModel_get_info(monkeypatch_beepop):
    model = BeePopModel("dummy.so")
    info = model.get_info()
    # Check DummyLib's stored results, cannot simulate C+ library behavior
    assert hasattr(model.lib, "_last_info")
    assert hasattr(model.lib, "_last_info_count")
    assert model.lib._last_info_count == 2


def test_BeePopModel_get_version(monkeypatch_beepop):
    model = BeePopModel("dummy.so")
    version = model.get_version()
    assert version == "1.2.3"


def test_BeePopModel_set_latitude(monkeypatch_beepop):
    """Test setting latitude in the BeePopModel."""
    model = BeePopModel("dummy.so")

    # Test setting latitude
    model.set_latitude(45.0)
    assert model.lib.latitude_set == True

    # Test that it accepts different latitude values
    test_latitudes = [0, 30, 60, 90, -45]
    for lat in test_latitudes:
        model.lib.latitude_set = False  # Reset flag
        model.set_latitude(lat)
        assert model.lib.latitude_set == True


def test_BeePopModel_load_weather_parameter_reapplication(
    monkeypatch_beepop, monkeypatch, tmp_path
):
    """Test that parameters are re-applied after loading weather."""
    model = BeePopModel("dummy.so")

    # Create a dummy weather file
    weather_file = tmp_path / "test_weather.txt"
    weather_file.write_text(
        "Date,MaxTemp,MinTemp,AvgTemp,Windspeed,Rain\n2014-06-16,25,15,20,5,0\n"
    )

    # Mock file opening and reading
    import builtins

    original_open = builtins.open

    def mock_open(file, *args, **kwargs):
        if str(weather_file) in str(file):
            from io import StringIO

            return StringIO(
                "Date,MaxTemp,MinTemp,AvgTemp,Windspeed,Rain\n2014-06-16,25,15,20,5,0\n"
            )
        return original_open(file, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", mock_open)

    # Set some parameters first
    model.valid_parameters.extend(["simstart", "simend", "icworkeradults"])
    model.set_parameters(
        {"simstart": "06/01/2014", "simend": "08/01/2014", "icworkeradults": 15000}
    )

    # Reset the flag to check if parameters are re-applied
    model.lib.icvars_set = False

    # Load weather - should trigger parameter re-application
    model.load_weather(str(weather_file))

    assert model.lib.weather_set == True
    assert model.lib.icvars_set == True  # Parameters should be re-applied


def test_BeePopModel_close_library(monkeypatch_beepop, monkeypatch):
    """Test the close_library functionality."""
    model = BeePopModel("dummy.so")

    # Test Windows path
    monkeypatch.setattr("platform.system", lambda: "Windows")
    monkeypatch.setattr("ctypes.windll.kernel32.FreeLibrary", lambda x: None)

    model.close_library()
    assert model.lib is None

    # Test Linux path
    model = BeePopModel("dummy.so")  # Create new instance
    monkeypatch.setattr("platform.system", lambda: "Linux")

    # Mock dlclose function
    def mock_dlclose(handle):
        pass

    mock_dlclose.argtypes = [ctypes.c_void_p]

    class MockCDLL:
        def __init__(self):
            self.dlclose = mock_dlclose

    mock_cdll = MockCDLL()
    monkeypatch.setattr("ctypes.CDLL", lambda x: mock_cdll)

    model.close_library()
    assert model.lib is None
