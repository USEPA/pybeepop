"""Scenario definitions shared by the golden-output test and its regenerator.

Each scenario enables as many model features as can validly coexist, so a small number
of fixtures pins a large share of model behavior.
"""

from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
EXAMPLE_DATA = PROJECT_DIR / "example_data"
WEATHER_FILE = EXAMPLE_DATA / "cedar_grove_NC_weather.txt"
RESIDUE_FILE = Path(__file__).resolve().parent / "fixtures" / "golden_residue.txt"
GOLDEN_DIR = Path(__file__).resolve().parent / "fixtures" / "golden"

SIM_START = "06/16/2014"
SIM_END = "10/10/2014"

# Application rates are chosen so each scenario produces a clear dose response while the
# colony survives all 118 days. The rates are not intended to be rooted in realism.

# Colony initial conditions, Varroa infestation (resident and immigrating), Varroa
# treatment, and adult/larval toxicity. Shared by every scenario.
_COMMON = {
    # Colony
    "ICWorkerAdults": 23000,
    "ICWorkerBrood": 8000,
    "ICWorkerLarvae": 5000,
    "ICWorkerEggs": 2000,
    "ICDroneAdults": 200,
    "ICDroneBrood": 100,
    "SimStart": SIM_START,
    "SimEnd": SIM_END,
    "Latitude": 35.9,
    # Foraging
    "IPollenTrips": 8,
    "INectarTrips": 17,
    # Varroa: resident infestation, partly treatment-resistant
    "ICWorkerAdultInfest": 15,
    "ICWorkerBroodInfest": 15,
    "ICDroneAdultInfest": 10,
    "ICDroneBroodInfest": 10,
    "InitMitePctResistant": 20,
    # Varroa: immigration, more resistant than the resident population
    "ImmEnabled": True,
    "ImmType": "Sine",
    "TotalImmMites": 800,
    "PctImmMitesResistant": 60,
    "ImmStart": "07/01/2014",
    "ImmEnd": "09/01/2014",
    # Varroa: treatment enabled (entries added separately, see VTDATA_ENTRIES)
    "VTEnable": True,
    # Toxicity
    "AIAdultLD50": 0.05,
    "AIAdultSlope": 4,
    "AILarvaLD50": 0.08,
    "AILarvaSlope": 3,
    "AIAdultLD50Contact": 0.04,
    "AIAdultSlopeContact": 4,
    "AIHalfLife": 25,
    "AIKOW": 100,
    "AIKOC": 25,
}

# Two treatments, so selection against the susceptible subpopulation happens more than once.
VTDATA_ENTRIES = ["07/10/2014,2,70", "08/20/2014,2,85"]

SCENARIOS = {
    "foliar": {
        "parameters": {
            **_COMMON,
            "FoliarEnabled": True,
            "EAppRate": 0.01,
            "FoliarAppDate": "07/05/2014",
            "FoliarForageBegin": "07/05/2014",
            "FoliarForageEnd": "08/05/2014",
        },
        "residue_file": None,
    },
    "soil": {
        "parameters": {
            **_COMMON,
            "SoilEnabled": True,
            "ESoilConcentration": 0.4,
            "ESoilTheta": 0.25,
            "ESoilP": 1.4,
            "ESoilFoc": 0.02,
            "SoilForageBegin": "07/15/2014",
            "SoilForageEnd": "08/15/2014",
        },
        "residue_file": None,
    },
    "seed": {
        "parameters": {
            **_COMMON,
            "SeedEnabled": True,
            "ESeedAppRate": 50,
            "SeedForageBegin": "06/20/2014",
            "SeedForageEnd": "07/20/2014",
        },
        "residue_file": None,
    },
    "direct_eec": {
        "parameters": {
            **_COMMON,
            "NecPolFileEnable": True,
        },
        "residue_file": str(RESIDUE_FILE),
    },
}


def build_model(scenario_name):
    """Construct and run one scenario, returning its output DataFrame."""
    from pybeepop import PyBeePop

    scenario = SCENARIOS[scenario_name]
    model = PyBeePop()
    model.load_weather(str(WEATHER_FILE))
    model.set_parameters(dict(scenario["parameters"]))
    for entry in VTDATA_ENTRIES:
        model.set_parameters({"VTData": entry})
    if scenario["residue_file"] is not None:
        model.load_residue_file(scenario["residue_file"])
    return model.run_model()


def golden_path(scenario_name):
    return GOLDEN_DIR / f"{scenario_name}.csv"
