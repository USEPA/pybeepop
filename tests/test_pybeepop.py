from pybeepop import PyBeePop
import pytest
import numpy as np
import os
import pandas as pd

TEST_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.abspath(os.path.join(TEST_DIR, os.pardir))


def test_set_parameters():
    beepop = PyBeePop()
    test_parameters = {"ICWorkerAdults": 9999, "SimStart": "01/01/2020", "SimEnd": "10/31/2020"}
    beepop.set_parameters(test_parameters)
    params = beepop.get_parameters()
    assert "icworkeradults" in params
    assert "simstart" in params
    assert "simend" in params
    assert params["icworkeradults"] == 9999
    assert params["simstart"] == "01/01/2020"
    assert params["simend"] == "10/31/2020"


def test_set_weather():
    test_weather = os.path.join(PROJECT_DIR, "example_data/cedar_grove_NC_weather.txt")
    beepop = PyBeePop()
    beepop.load_weather(test_weather)


def test_invalid_parameter():
    beepop = PyBeePop()
    invalid_parameters = {"Invalid_parameter": 1234}
    with pytest.raises(ValueError):
        beepop.set_parameters(invalid_parameters)


def test_invalid_parameter_in_file():
    beepop = PyBeePop()
    parameter_file = os.path.join(PROJECT_DIR, "example_data/test_parameters_invalid.txt")
    with pytest.raises(ValueError):
        beepop.load_parameter_file(parameter_file)


def test_run_model():
    beepop = PyBeePop()

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
    results_initial = results.iloc[0, :]
    results_last = results.iloc[len(results) - 1, :]
    results_exposure = results.iloc[20, :]

    # check results
    assert results_initial["Date"] == "Initial"
    assert results_initial["Colony Size"] == 23000
    assert results_initial["Capped Worker Brood"] == 8000
    assert results_exposure["Colony Size"] == 17913
    assert results_exposure["Capped Drone Brood"] == 219
    assert results_exposure["Daylight hours"] == 13.7
    assert results_exposure["Dead Foragers"] == 155
    assert results_last["Date"] == "10/9/2014"
    assert results_last["Colony Size"] == 43932
    assert results_last["Adult Drones"] == 512
    assert results_last["Average Temperature (C)"] == 16.66
    assert results_last["Rain (mm)"] == 0.0
