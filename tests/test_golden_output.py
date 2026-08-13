"""Regression tests comparing full model output against committed golden fixtures.

These pin every value of every output column, so any change to model behavior fails here.
The fixtures live in tests/fixtures/golden/ as data, not as literals in test code: an
unintended behavior change therefore shows up as a diff in a file whose only purpose is
to be a baseline.

If a failure is expected because a model change is intended, regenerate with
`python tests/regenerate_golden.py` and review the resulting diff as part of the change.
Do not adjust tolerances to make a failure disappear.
"""

import pytest

from golden_scenarios import SCENARIOS, build_model, golden_path

pd = pytest.importorskip("pandas")

# Tolerance absorbs last-bit floating point differences from
# platform libm implementations of exp/log. It is far too tight to hide a behavioral
# change: a 0.006% shift in a single model constant fails these tests.
RTOL = 1e-9
ATOL = 1e-12


def _load_golden(scenario_name):
    path = golden_path(scenario_name)
    if not path.exists():
        pytest.fail(
            f"Missing golden fixture {path}. Generate it with "
            "`python tests/regenerate_golden.py`."
        )
    return pd.read_csv(path, keep_default_na=False)


@pytest.mark.parametrize("scenario_name", sorted(SCENARIOS))
def test_output_matches_golden_fixture(scenario_name):
    expected = _load_golden(scenario_name)
    actual = build_model(scenario_name)

    assert list(actual.columns) == list(expected.columns), (
        "Output columns changed.\n"
        f"  added:   {sorted(set(actual.columns) - set(expected.columns))}\n"
        f"  removed: {sorted(set(expected.columns) - set(actual.columns))}"
    )
    assert len(actual) == len(expected), (
        f"Row count changed: expected {len(expected)}, got {len(actual)}"
    )

    mismatches = []
    for column in expected.columns:
        exp_col, act_col = expected[column], actual[column].reset_index(drop=True)
        numeric = pd.to_numeric(exp_col, errors="coerce")
        if numeric.notna().all():
            act_numeric = pd.to_numeric(act_col, errors="coerce")
            close = pd.Series(
                [
                    (a is not None and e is not None)
                    and abs(a - e) <= ATOL + RTOL * abs(e)
                    for a, e in zip(act_numeric, numeric)
                ]
            )
            if not close.all():
                first = int(close.idxmin())
                mismatches.append(
                    f"  {column!r}: {int((~close).sum())}/{len(close)} rows differ; "
                    f"first at row {first} "
                    f"(expected {numeric.iloc[first]!r}, got {act_numeric.iloc[first]!r})"
                )
        else:
            differing = exp_col.astype(str) != act_col.astype(str)
            if differing.any():
                first = int(differing.idxmax())
                mismatches.append(
                    f"  {column!r}: {int(differing.sum())}/{len(differing)} rows differ; "
                    f"first at row {first} "
                    f"(expected {exp_col.iloc[first]!r}, got {act_col.iloc[first]!r})"
                )

    assert not mismatches, (
        f"Model output changed for scenario {scenario_name!r} in "
        f"{len(mismatches)} of {len(expected.columns)} columns:\n"
        + "\n".join(mismatches)
        + "\n\nIf this change is intended, run `python tests/regenerate_golden.py` "
        "and review the diff."
    )


@pytest.mark.parametrize("scenario_name", sorted(SCENARIOS))
def test_golden_scenario_stays_alive_and_exposed(scenario_name):
    """Guard the fixtures themselves against becoming uninformative.

    A scenario whose colony dies partway, or whose pesticide concentrations are all zero,
    would still match its fixture while pinning far less behavior than intended.
    """
    results = _load_golden(scenario_name)

    colony_size = pd.to_numeric(results["Colony Size"].iloc[1:])
    assert (colony_size > 0).all(), (
        f"{scenario_name}: colony dies during the run, so later rows pin nothing"
    )

    pollen = pd.to_numeric(results["Pollen Pesticide Concentration (ug/g)"])
    nectar = pd.to_numeric(results["Nectar Pesticide Concentration (ug/g)"])
    assert pollen.abs().sum() > 0, f"{scenario_name}: no pollen exposure recorded"
    assert nectar.abs().sum() > 0, f"{scenario_name}: no nectar exposure recorded"

    mites_dying = pd.to_numeric(results["Mites Dying"])
    assert mites_dying.sum() > 0, f"{scenario_name}: no mite mortality recorded"
