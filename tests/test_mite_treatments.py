from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

from pybeepop import PyBeePop
from pybeepop.beepop.mite import Mite
from pybeepop.beepop.mitetreatments import MiteTreatments
from pybeepop.beepop.session import VarroaPopSession


def test_vtdata_parses_single_treatment_item():
    session = VarroaPopSession()

    success = session.update_colony_parameters("vtdata", "04/01/2023,2,75")

    assert success is True
    items = session.colony.m_mite_treatment_info.items
    assert len(items) == 1
    assert items[0].start_time == datetime(2023, 4, 1)
    assert items[0].duration == 2
    assert items[0].pct_mortality == 75.0


def test_vtdata_parses_multiple_lines_and_clear():
    session = VarroaPopSession()

    assert session.update_colony_parameters("vtdata", "04/01/2023,2,75") is True
    assert session.update_colony_parameters("vtdata", "04/15/2023,1,60") is True
    assert len(session.colony.m_mite_treatment_info.items) == 2

    assert session.update_colony_parameters("vtdata", "Clear") is True
    assert session.colony.m_mite_treatment_info.items == []


def test_mite_treatment_duration_is_interpreted_as_weeks():
    treatments = MiteTreatments()
    start = datetime(2023, 4, 1)
    treatments.add_item_by_values(start, 2, 75.0)

    assert treatments.get_active_item(start) is not None
    assert treatments.get_active_item(start + timedelta(days=13)) is not None
    assert treatments.get_active_item(start + timedelta(days=14)) is None


def test_vtdata_invalid_format_adds_error():
    session = VarroaPopSession()

    success = session.update_colony_parameters("vtdata", "04/01/2023,2")

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
                    "VTData=06/20/2014,1,60",
                    "VTData=07/04/2014,1,60",
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


def test_retired_vt_parameters_point_users_at_vtdata():
    for name in ("VTTreatmentStart", "VTTreatmentDuration", "VTMortality"):
        model = PyBeePop()
        with pytest.raises(ValueError) as exc_info:
            model.set_parameters({name: "1"})
        message = str(exc_info.value)
        assert f"{name} was removed" in message
        assert "VTData" in message


def test_retired_parameters_rejected_from_parameter_file(tmp_path):
    parameter_file = tmp_path / "legacy_params.txt"
    parameter_file.write_text("VTEnable=True\nVTTreatmentStart=06/20/2014\n")

    model = PyBeePop()
    with pytest.raises(ValueError, match="VTData"):
        model.load_parameter_file(str(parameter_file))


def test_dashboard_style_vtdata_string_is_accepted():
    """The dashboard composes VTData from four separate widgets."""
    model = PyBeePop()

    model.set_parameters(
        {"VTEnable": True, "VTData": "06/20/2014,6,75.0"}
    )

    items = model.engine.model.session.colony.m_mite_treatment_info.items
    assert len(items) == 1
    assert items[0].start_time == datetime(2014, 6, 20)
    assert items[0].duration == 6
    assert items[0].pct_mortality == 75.0


def test_vtdata_with_legacy_resistant_field_is_rejected():
    session = VarroaPopSession()

    success = session.update_colony_parameters("vtdata", "04/01/2023,2,75,5")

    assert success is False
    assert any(
        "no longer takes a resistant% field" in error
        for error in session.get_error_list()
    )


def _colony_with_initial_resistance(pct_resistant, vt_enable=True, pct_mortality=100.0):
    """Colony whose initial mite population is pct_resistant% treatment-resistant."""
    session = VarroaPopSession()
    session.set_sim_start(datetime(2023, 4, 1))
    session.set_sim_end(datetime(2023, 4, 30))
    session.update_colony_parameters("icworkeradults", "10000")
    session.update_colony_parameters("icworkerbrood", "5000")
    session.update_colony_parameters("icworkeradultinfest", "20")
    session.update_colony_parameters("initmitepctresistant", str(pct_resistant))
    session.update_colony_parameters("vtdata", f"04/01/2023,2,{pct_mortality}")
    session.update_colony_parameters("vtenable", str(vt_enable))
    session.initialize_simulation()
    return session.colony


def test_init_mite_pct_resistant_creates_resistant_mites():
    colony = _colony_with_initial_resistance(25.0)

    total = colony.run_mite.get_total()
    assert total > 0
    assert colony.run_mite.get_resistant() > 0
    assert colony.run_mite.get_pct_resistant() == pytest.approx(25.0, abs=1.0)


def test_zero_init_mite_pct_resistant_creates_no_resistant_mites():
    colony = _colony_with_initial_resistance(0.0)

    assert colony.run_mite.get_total() > 0
    assert colony.run_mite.get_resistant() == 0


def test_resistant_mites_survive_a_total_treatment():
    """At 100% mortality every susceptible mite dies and no resistant mite does."""
    treated = _colony_with_initial_resistance(25.0, pct_mortality=100.0)
    untreated = _colony_with_initial_resistance(
        25.0, pct_mortality=100.0, vt_enable=False
    )
    assert treated.run_mite.get_resistant() > 0

    treated.update_mites(None, 1)
    untreated.update_mites(None, 1)

    # The treatment wipes out susceptibles...
    assert treated.run_mite.get_non_resistant() == 0
    assert untreated.run_mite.get_non_resistant() > 0
    # ...and leaves the resistant subpopulation exactly as the untreated colony has it.
    assert treated.run_mite.get_resistant() == pytest.approx(
        untreated.run_mite.get_resistant()
    )


def test_treatment_raises_the_resistant_proportion():
    """Killing susceptibles selects for resistance."""
    colony = _colony_with_initial_resistance(25.0, pct_mortality=75.0)
    pct_before = colony.run_mite.get_pct_resistant()

    colony.update_mites(None, 1)

    assert colony.run_mite.get_pct_resistant() > pct_before


def test_immigrating_mites_inherit_pct_imm_mites_resistant():
    session = VarroaPopSession()
    session.set_sim_start(datetime(2023, 4, 1))
    session.set_sim_end(datetime(2023, 4, 30))
    session.immigration_enabled = True
    session.immigration_type = "Sine"
    session.tot_immigrating_mites = 500
    session.immigration_start_date = datetime(2023, 4, 1)
    session.immigration_end_date = datetime(2023, 4, 30)
    session.update_colony_parameters("pctimmmitesresistant", "40")

    mites = session.get_immigration_mites(SimpleNamespace(time=datetime(2023, 4, 15)))

    total = mites["resistant"] + mites["non_resistant"]
    assert total > 0
    assert mites["resistant"] / total == pytest.approx(0.40)
