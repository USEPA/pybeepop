from datetime import datetime

import pytest

from pybeepop import PyBeePop
from pybeepop.beepop.session import VarroaPopSession

POLLEN_FACTOR = 18e-9
NECTAR_FACTOR = 45e-9


def _seed_exposed_colony(app_rate):
    """Build a colony with the seed forage window open on simulation day 1."""
    session = VarroaPopSession()
    session.set_sim_start(datetime(2023, 4, 1))
    session.set_sim_end(datetime(2023, 4, 30))

    colony = session.colony
    colony.create()
    colony.initialize_colony()

    epadata = colony.m_epadata
    epadata.m_SeedEnabled = True
    epadata.m_SeedForageBegin = datetime(2023, 4, 1)
    epadata.m_SeedForageEnd = datetime(2023, 4, 30)
    epadata.m_E_SeedAppRate = app_rate
    return colony


def test_eseedapprate_is_parsed_into_epadata():
    session = VarroaPopSession()

    assert session.update_colony_parameters("eseedapprate", "0.1") is True
    assert session.colony.m_epadata.m_E_SeedAppRate == pytest.approx(0.1)


def test_invalid_eseedapprate_adds_error():
    session = VarroaPopSession()

    success = session.update_colony_parameters("eseedapprate", "not_a_number")

    assert success is False
    assert any("eseedapprate must be a number" in error for error in session.get_error_list())


def test_pollen_residue_scales_at_18_ng_per_mg_per_seed():
    colony = _seed_exposed_colony(0.1)

    assert colony.get_incoming_pollen_pesticide_concentration(1) == pytest.approx(
        0.1 * POLLEN_FACTOR
    )


def test_nectar_residue_scales_at_45_ng_per_mg_per_seed():
    colony = _seed_exposed_colony(0.1)

    assert colony.get_incoming_nectar_pesticide_concentration(1) == pytest.approx(
        0.1 * NECTAR_FACTOR
    )


def test_pollen_and_nectar_residues_differ():
    """Guard against a regression to a single shared seed concentration."""
    colony = _seed_exposed_colony(0.1)

    pollen = colony.get_incoming_pollen_pesticide_concentration(1)
    nectar = colony.get_incoming_nectar_pesticide_concentration(1)

    assert pollen != nectar
    assert nectar == pytest.approx(pollen * 2.5)


def test_zero_app_rate_gives_zero_residue():
    colony = _seed_exposed_colony(0.0)

    assert colony.get_incoming_pollen_pesticide_concentration(1) == 0.0
    assert colony.get_incoming_nectar_pesticide_concentration(1) == 0.0


def test_residue_is_zero_outside_seed_forage_window():
    colony = _seed_exposed_colony(0.1)
    colony.m_epadata.m_SeedForageBegin = datetime(2023, 4, 10)
    colony.m_epadata.m_SeedForageEnd = datetime(2023, 4, 20)

    assert colony.get_incoming_pollen_pesticide_concentration(1) == 0.0
    assert colony.get_incoming_nectar_pesticide_concentration(1) == 0.0


def test_residue_is_zero_when_seed_exposure_disabled():
    colony = _seed_exposed_colony(0.1)
    colony.m_epadata.m_SeedEnabled = False

    assert colony.get_incoming_pollen_pesticide_concentration(1) == 0.0
    assert colony.get_incoming_nectar_pesticide_concentration(1) == 0.0


def test_eseedconcentration_is_rejected_with_migration_message():
    model = PyBeePop()

    with pytest.raises(ValueError, match="ESeedConcentration was removed"):
        model.set_parameters({"ESeedConcentration": "0.5"})


def test_eseedconcentration_migration_message_names_replacement():
    model = PyBeePop()

    with pytest.raises(ValueError) as exc_info:
        model.set_parameters({"eseedconcentration": "0.5"})

    assert "ESeedAppRate" in str(exc_info.value)


def test_eseedapprate_accepted_through_public_api():
    model = PyBeePop()

    model.set_parameters({"ESeedAppRate": "0.1"})

    assert "eseedapprate" in model.get_parameters()
