from datetime import datetime, timedelta
from pathlib import Path

from pybeepop import PyBeePop
from pybeepop.beepop.mite import Mite
from pybeepop.beepop.mitetreatments import MiteTreatments
from pybeepop.beepop.session import VarroaPopSession


def test_vtdata_parses_single_treatment_item():
    session = VarroaPopSession()

    success = session.update_colony_parameters("vtdata", "04/01/2023,2,75,5")

    assert success is True
    items = session.colony.m_mite_treatment_info.items
    assert len(items) == 1
    assert items[0].start_time == datetime(2023, 4, 1)
    assert items[0].duration == 2
    assert items[0].pct_mortality == 75.0
    assert items[0].pct_resistant == 5.0


def test_vtdata_parses_multiple_lines_and_clear():
    session = VarroaPopSession()

    assert session.update_colony_parameters("vtdata", "04/01/2023,2,75,5") is True
    assert session.update_colony_parameters("vtdata", "04/15/2023,1,60,10") is True
    assert len(session.colony.m_mite_treatment_info.items) == 2

    assert session.update_colony_parameters("vtdata", "Clear") is True
    assert session.colony.m_mite_treatment_info.items == []


def test_mite_treatment_duration_is_interpreted_as_weeks():
    treatments = MiteTreatments()
    start = datetime(2023, 4, 1)
    treatments.add_item_by_values(start, 2, 75.0, 5.0)

    assert treatments.get_active_item(start) is not None
    assert treatments.get_active_item(start + timedelta(days=13)) is not None
    assert treatments.get_active_item(start + timedelta(days=14)) is None


def test_vtdata_invalid_format_adds_error():
    session = VarroaPopSession()

    success = session.update_colony_parameters("vtdata", "04/01/2023,2,75")

    assert success is False
    assert any("Invalid vtdata format" in error for error in session.get_error_list())


def _build_initialized_colony(vt_enable: bool):
    session = VarroaPopSession()
    session.set_sim_start(datetime(2023, 4, 1))
    session.set_sim_end(datetime(2023, 4, 30))

    colony = session.colony
    colony.create()
    colony.initialize_colony()
    colony.run_mite = Mite(10.0, 90.0)
    colony.prop_rm_virgins = 1.0
    colony.m_mite_treatment_info.clear_all()
    colony.m_mite_treatment_info.add_item_by_values(
        datetime(2023, 4, 1),
        2,
        50.0,
        0.0,
    )
    colony.set_vt_enable(vt_enable)
    return colony


def test_vt_enable_controls_treatment_application():
    treated_colony = _build_initialized_colony(vt_enable=True)
    untreated_colony = _build_initialized_colony(vt_enable=False)

    treated_colony.update_mites(None, 1)
    untreated_colony.update_mites(None, 1)

    assert (
        treated_colony.run_mite.get_resistant()
        == untreated_colony.run_mite.get_resistant()
    )
    assert (
        treated_colony.run_mite.get_non_resistant()
        < untreated_colony.run_mite.get_non_resistant()
    )
    assert treated_colony.m_mites_dying_today > untreated_colony.m_mites_dying_today


def test_run_model_applies_multiple_vtdata_entries(tmp_path):
    project_dir = Path(__file__).resolve().parent.parent
    weather_file = project_dir / "example_data" / "cedar_grove_NC_weather.txt"

    def write_parameter_file(vt_enable: bool):
        parameter_file = tmp_path / f"vt_{'on' if vt_enable else 'off'}.txt"
        parameter_file.write_text(
            "\n".join(
                [
                    "ICWorkerAdults=15000",
                    "ICWorkerBrood=10000",
                    "ICWorkerLarvae=5000",
                    "ICWorkerEggs=2000",
                    "ICWorkerAdultInfest=20",
                    "ICWorkerBroodInfest=20",
                    "SimStart=06/16/2014",
                    "SimEnd=07/16/2014",
                    f"VTEnable={'True' if vt_enable else 'False'}",
                    "VTData=06/20/2014,1,60,0",
                    "VTData=07/04/2014,1,60,0",
                    "",
                ]
            ),
            encoding="ascii",
        )
        return parameter_file

    treated_model = PyBeePop(engine="python")
    untreated_model = PyBeePop(engine="python")

    treated_model.load_weather(str(weather_file))
    untreated_model.load_weather(str(weather_file))

    treated_model.load_parameter_file(str(write_parameter_file(vt_enable=True)))
    untreated_model.load_parameter_file(str(write_parameter_file(vt_enable=False)))

    treated_results = treated_model.run_model()
    untreated_results = untreated_model.run_model()

    treated_daily = treated_results.iloc[1:].reset_index(drop=True)
    untreated_daily = untreated_results.iloc[1:].reset_index(drop=True)

    assert len(treated_daily) == len(untreated_daily)
    assert "Free Mites" in treated_daily.columns
    assert "Mites Dying" in treated_daily.columns
    assert treated_daily["Mites Dying"].sum() > untreated_daily["Mites Dying"].sum()
    assert treated_daily["Free Mites"].mean() < untreated_daily["Free Mites"].mean()
