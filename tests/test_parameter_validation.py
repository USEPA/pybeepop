"""Tests for numeric parameter range and type validation."""

import csv
import os

import pytest

from pybeepop import PyBeePop
from pybeepop.beepop.parameters import INTEGER, PARAMETER_SPECS, _parse_bound
from pybeepop.beepop.session import VarroaPopSession
from pybeepop.exceptions import BeepopParameterError

CSV_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "pybeepop",
    "data",
    "BeePop_exposed_parameters.csv",
)


@pytest.fixture(scope="module")
def csv_rows():
    """Parameter rows keyed by lowercased name. The column header is the second line."""
    with open(CSV_PATH, newline="", encoding="utf-8-sig") as handle:
        next(handle)  # note row precedes the column header
        return {
            row["Exposed Variable Name"].strip().lower(): row
            for row in csv.DictReader(handle)
        }


def test_every_spec_matches_the_documented_row(csv_rows):
    """The shipped CSV and the enforced ranges must agree, so docs cannot drift."""
    mismatches = []
    for name, spec in PARAMETER_SPECS.items():
        row = csv_rows.get(name)
        if row is None:
            mismatches.append(f"{name}: no row in {os.path.basename(CSV_PATH)}")
            continue
        documented = (
            row["Type"].strip(),
            row["Min"].strip(),
            row["Max"].strip(),
        )
        enforced = (spec.kind, spec.minimum, spec.maximum)
        if documented != enforced:
            mismatches.append(f"{name}: CSV says {documented}, code enforces {enforced}")

    assert not mismatches, "Parameter documentation disagrees with validation:\n" + "\n".join(
        mismatches
    )


def test_every_numeric_row_has_a_spec(csv_rows):
    """Any Integer or Float parameter without a spec is silently unvalidated."""
    unspecified = [
        name
        for name, row in csv_rows.items()
        if row["Type"].strip() in ("Integer", "Float")
        and name not in PARAMETER_SPECS
        and row["Description"].strip() != "Unused"
    ]
    assert not unspecified, f"Numeric parameters with no range validation: {unspecified}"


def test_documented_defaults_are_within_their_own_range(csv_rows):
    """A default that its own Min/Max would reject means one of the two is wrong."""
    rejected = []
    for name in PARAMETER_SPECS:
        row = csv_rows[name]
        default = row["Default"].strip()
        if not default:
            continue
        try:
            PyBeePop().set_parameters({row["Exposed Variable Name"].strip(): default})
        except BeepopParameterError as error:
            rejected.append(str(error).splitlines()[0])

    assert not rejected, "Documented defaults rejected by their own range:\n" + "\n".join(
        rejected
    )


def test_csv_defaults_match_the_packaged_default_parameter_file(csv_rows):
    """Every entry in default_parameters.txt must match the Default column it documents."""
    default_file = os.path.join(os.path.dirname(CSV_PATH), "default_parameters.txt")
    with open(default_file) as handle:
        packaged = {}
        for line in handle:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                name, value = line.split("=", 1)
                packaged[name.strip().lower()] = value.strip()

    assert packaged, "default_parameters.txt is empty"

    mismatches = []
    for name, value in packaged.items():
        row = csv_rows.get(name)
        if row is None:
            mismatches.append(f"{name}: in default_parameters.txt but not in the CSV")
            continue
        documented = row["Default"].strip()
        if documented != value:
            mismatches.append(f"{name}: CSV Default {documented!r}, file has {value!r}")

    assert not mismatches, "Documented defaults disagree with the packaged file:\n" + "\n".join(
        mismatches
    )


def test_defaults_not_in_the_file_match_the_values_the_model_initializes(csv_rows):
    """Parameters absent from default_parameters.txt take their default from the model."""
    model = PyBeePop()
    session = model.engine.model.session
    colony = session.get_colony()

    initialized = {
        "eapprate": colony.m_epadata.m_E_AppRate,
        "initmitepctresistant": session.init_mite_pct_resistant,
        "necpolfileenable": colony.m_epadata.m_NecPolFileEnabled,
        "pctimmmitesresistant": session.imm_mite_pct_resistant,
        "rqqueenstrength": session.rq_queen_strength,
        "supnectaramount": colony.m_SuppNectar.m_StartingAmount,
        "suppollenamount": colony.m_SuppPollen.m_StartingAmount,
        "totalimmmites": session.tot_immigrating_mites,
    }

    mismatches = []
    for name, live in initialized.items():
        documented = csv_rows[name]["Default"].strip()
        matches = (
            str(live) == documented
            if isinstance(live, bool)
            else float(live) == float(documented)
        )
        if not matches:
            mismatches.append(f"{name}: CSV Default {documented!r}, model has {live!r}")

    assert not mismatches, "Documented defaults disagree with the model:\n" + "\n".join(
        mismatches
    )


@pytest.mark.parametrize(
    "parameters, expected",
    [
        ({"AIAdultSlope": 20}, "out of range"),
        ({"AIAdultSlope": -1}, "out of range"),
        ({"AILarvaSlope": 25}, "out of range"),
        ({"AIAdultLD50": 0}, "out of range"),
        ({"AILarvaLD50": -0.5}, "out of range"),
        ({"ICWorkerAdultInfest": 101}, "out of range"),
        ({"ForagerMaxProp": 1.5}, "out of range"),
        ({"Latitude": 91}, "out of range"),
        ({"Latitude": -91}, "out of range"),
        ({"ESoilP": 0}, "out of range"),
        ({"ESoilFoc": 0}, "out of range"),
        ({"AIKOC": 0}, "out of range"),
        ({"AIKOW": 0}, "out of range"),
        ({"AIHalfLife": 0}, "out of range"),
        ({"ESoilTheta": 1.5}, "out of range"),
        ({"ICForagerLifespan": 3}, "out of range"),
        ({"ICForagerLifespan": 17}, "out of range"),
        ({"AIHalfLife": "not_a_number"}, "must be a number"),
        ({"IPollenTrips": 2.677}, "must be a whole number"),
        ({"ICWorkerAdults": 100.5}, "must be a whole number"),
    ],
)
def test_out_of_range_values_are_rejected(parameters, expected):
    model = PyBeePop()
    with pytest.raises(BeepopParameterError, match=expected):
        model.set_parameters(parameters)


@pytest.mark.parametrize(
    "parameters",
    [
        {"AIAdultSlope": 19.999},
        {"AIAdultSlope": 0},
        {"AIAdultLD50": 0.0001},
        {"AIAdultLD50": 999},
        {"ICWorkerAdultInfest": 100},
        {"ForagerMaxProp": 1},
        {"Latitude": -90},
        {"Latitude": 90},
        {"Latitude": 71},
        {"ESoilP": 1.8},
        {"ESoilTheta": 1},
        {"ESoilTheta": 0},
        # Outside the recommended range but within the limits the model enforces.
        {"ESoilP": 2.5},
        {"ESoilFoc": 0.5},
        {"AIKOC": 20000},
        {"AIHalfLife": 60},
        {"ICForagerLifespan": 4},
        {"ICForagerLifespan": 16},
        {"ESoilTheta": 0.8},
    ],
)
def test_values_on_the_boundary_are_accepted(parameters):
    model = PyBeePop()
    model.set_parameters(parameters)

    name = next(iter(parameters))
    assert model.get_parameters()[name.lower()] == parameters[name]


def test_error_message_uses_the_name_the_caller_passed():
    model = PyBeePop()
    with pytest.raises(BeepopParameterError, match="AIAdultSlope is out of range"):
        model.set_parameters({"AIAdultSlope": 25})


def test_slope_at_20_is_rejected_rather_than_silently_zeroing_mortality():
    """dose_response() returns zero mortality at slope >= 20, so it must not be settable."""
    from pybeepop.beepop.epadata import EPAData

    assert EPAData().dose_response(1.0, 0.05, 20) == 0.0
    with pytest.raises(BeepopParameterError):
        PyBeePop().set_parameters({"AIAdultSlope": 20})


def test_zero_ld50_is_rejected_rather_than_silently_zeroing_mortality():
    from pybeepop.beepop.epadata import EPAData

    assert EPAData().dose_response(1.0, 0.0, 4) == 0.0
    with pytest.raises(BeepopParameterError):
        PyBeePop().set_parameters({"AIAdultLD50": 0})


def test_integer_parameters_all_behave_the_same_way():
    """Every Integer parameter accepts a whole-number float and rejects a fractional one."""
    integer_names = [
        name for name, spec in PARAMETER_SPECS.items() if spec.kind == INTEGER
    ]
    assert len(integer_names) == 13

    accepted, rejected = [], []
    for name in integer_names:
        if VarroaPopSession().update_colony_parameters(name, "10.0"):
            accepted.append(name)
        if not VarroaPopSession().update_colony_parameters(name, "10.677"):
            rejected.append(name)

    assert sorted(accepted) == sorted(integer_names)
    assert sorted(rejected) == sorted(integer_names)


def test_soil_partition_denominator_cannot_be_driven_to_zero():
    """The soil-water partition term divides by theta + rho * Koc * foc.

    ESoilTheta is allowed to be zero, so ESoilP, AIKOC and ESoilFoc must each be barred
    from reaching zero no matter what the rest of their range allows.
    """
    for name in ("esoilp", "aikoc", "esoilfoc"):
        spec = PARAMETER_SPECS[name]
        assert _parse_bound(spec.minimum) is not None, f"{name} has no lower bound"
        value, exclusive = _parse_bound(spec.minimum)
        assert value > 0 or exclusive, f"{name} allows zero, which zeroes the denominator"


def test_latitude_beyond_65_degrees_still_runs():
    """Day length is computed as at 65 degrees, so high latitudes remain simulatable."""
    weather = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "example_data",
        "cedar_grove_NC_weather.txt",
    )
    model = PyBeePop()
    model.load_weather(weather)
    model.set_parameters(
        {
            "Latitude": 71,
            "SimStart": "06/16/2014",
            "SimEnd": "07/16/2014",
            "ICWorkerAdults": 15000,
            "ICWorkerBrood": 8000,
        }
    )
    results = model.run_model()

    assert len(results) > 0
    assert results["Colony Size"].iloc[-1] > 0


def test_out_of_range_value_in_parameter_file_is_rejected(tmp_path):
    param_file = tmp_path / "params.txt"
    param_file.write_text("ICWorkerAdults=10000\nAIAdultSlope=25\n")

    model = PyBeePop()
    with pytest.raises(BeepopParameterError, match="AIAdultSlope is out of range"):
        model.load_parameter_file(str(param_file))


def test_rejected_parameter_does_not_block_later_valid_parameters():
    model = PyBeePop()
    with pytest.raises(BeepopParameterError):
        model.set_parameters({"AIAdultSlope": 25})

    model.set_parameters({"AIAdultSlope": 4})
    assert model.get_parameters()["aiadultslope"] == 4
