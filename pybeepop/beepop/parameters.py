"""Type and range specifications for numeric BeePop+ parameters.

Every numeric parameter accepted by VarroaPopSession.update_colony_parameters() is
listed in PARAMETER_SPECS with the range it accepts. Values outside that range are
rejected with an error rather than being passed on to the model.

Bounds are written the way they appear in the Min and Max columns of
BeePop_exposed_parameters.csv: a bare number is inclusive, a number prefixed with
'>' or '<' is exclusive, and an empty string means unbounded on that side. The two
must agree; tests/test_parameter_validation.py compares them row by row.
"""

import math
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

INTEGER = "Integer"
FLOAT = "Float"


@dataclass(frozen=True)
class ParameterSpec:
    """The accepted type and range for one parameter."""

    kind: str
    minimum: str = ""
    maximum: str = ""


def _parse_bound(text: str) -> Optional[Tuple[float, bool]]:
    """Return ``(value, exclusive)`` for a bound string, or None if unbounded."""
    text = text.strip()
    if not text or text == "N/A":
        return None
    if text[0] in "<>":
        return float(text[1:]), True
    return float(text), False


PARAMETER_SPECS: Dict[str, ParameterSpec] = {
    # Colony initial conditions
    "icdroneadults": ParameterSpec(INTEGER, "0"),
    "icworkeradults": ParameterSpec(INTEGER, "0"),
    "icdronebrood": ParameterSpec(INTEGER, "0"),
    "icworkerbrood": ParameterSpec(INTEGER, "0"),
    "icdronelarvae": ParameterSpec(INTEGER, "0"),
    "icworkerlarvae": ParameterSpec(INTEGER, "0"),
    "icdroneeggs": ParameterSpec(INTEGER, "0"),
    "icworkereggs": ParameterSpec(INTEGER, "0"),
    "icqueenstrength": ParameterSpec(FLOAT, "1", "5"),
    # Biological range from the published model; the code itself imposes no limit.
    "icforagerlifespan": ParameterSpec(INTEGER, "4", "16"),
    # Varroa initial infestation
    "icdroneadultinfest": ParameterSpec(FLOAT, "0", "100"),
    "icdronebroodinfest": ParameterSpec(FLOAT, "0", "100"),
    "icdronemiteoffspring": ParameterSpec(FLOAT, "0"),
    "icdronemitesurvivorship": ParameterSpec(FLOAT, "0", "100"),
    "icworkeradultinfest": ParameterSpec(FLOAT, "0", "100"),
    "icworkerbroodinfest": ParameterSpec(FLOAT, "0", "100"),
    "icworkermiteoffspring": ParameterSpec(FLOAT, "0"),
    "icworkermitesurvivorship": ParameterSpec(FLOAT, "0", "100"),
    # Varroa immigration
    "pctimmmitesresistant": ParameterSpec(FLOAT, "0", "100"),
    "totalimmmites": ParameterSpec(INTEGER, "0"),
    # Varroa treatment
    "initmitepctresistant": ParameterSpec(FLOAT, "0", "100"),
    # Re-queening
    "rqegglaydelay": ParameterSpec(INTEGER, "0"),
    "rqqueenstrength": ParameterSpec(FLOAT, "1", "5"),
    # Toxicity. dose_response() returns zero mortality outside these bounds.
    "aiadultslope": ParameterSpec(FLOAT, "0", "<20"),
    "aiadultld50": ParameterSpec(FLOAT, ">0"),
    "aiadultslopecontact": ParameterSpec(FLOAT, "0", "<20"),
    "aiadultld50contact": ParameterSpec(FLOAT, ">0"),
    "ailarvaslope": ParameterSpec(FLOAT, "0", "<20"),
    "ailarvald50": ParameterSpec(FLOAT, ">0"),
    # log10(AIKOW) is taken directly, and AIHalfLife divides into log(2).
    "aikow": ParameterSpec(FLOAT, ">0"),
    "aikoc": ParameterSpec(FLOAT, ">0"),
    "aihalflife": ParameterSpec(FLOAT, ">0"),
    "aicontactfactor": ParameterSpec(FLOAT, "0"),
    # Daily consumption
    "cl4pollen": ParameterSpec(FLOAT, "0"),
    "cl4nectar": ParameterSpec(FLOAT, "0"),
    "cl5pollen": ParameterSpec(FLOAT, "0"),
    "cl5nectar": ParameterSpec(FLOAT, "0"),
    "cldpollen": ParameterSpec(FLOAT, "0"),
    "cldnectar": ParameterSpec(FLOAT, "0"),
    "ca13pollen": ParameterSpec(FLOAT, "0"),
    "ca13nectar": ParameterSpec(FLOAT, "0"),
    "ca410pollen": ParameterSpec(FLOAT, "0"),
    "ca410nectar": ParameterSpec(FLOAT, "0"),
    "ca1120pollen": ParameterSpec(FLOAT, "0"),
    "ca1120nectar": ParameterSpec(FLOAT, "0"),
    "cadpollen": ParameterSpec(FLOAT, "0"),
    "cadnectar": ParameterSpec(FLOAT, "0"),
    "cforagerpollen": ParameterSpec(FLOAT, "0"),
    "cforagernectar": ParameterSpec(FLOAT, "0"),
    # Foraging
    "ipollentrips": ParameterSpec(INTEGER, "0"),
    "inectartrips": ParameterSpec(INTEGER, "0"),
    "ipercentnectarforagers": ParameterSpec(FLOAT, "0", "100"),
    "ipollenload": ParameterSpec(FLOAT, "0"),
    "inectarload": ParameterSpec(FLOAT, "0"),
    # Pesticide application
    "eapprate": ParameterSpec(FLOAT, "0"),
    "esoiltheta": ParameterSpec(FLOAT, "0", "1"),
    # ESoilP, AIKOC and ESoilFoc share the soil-water partition denominator with
    # ESoilTheta, which may be zero, so none of them may reach zero.
    "esoilp": ParameterSpec(FLOAT, ">0"),
    "esoilfoc": ParameterSpec(FLOAT, ">0"),
    "esoilconcentration": ParameterSpec(FLOAT, "0"),
    "eseedapprate": ParameterSpec(FLOAT, "0"),
    # Colony resources
    "initcolnectar": ParameterSpec(FLOAT, "0"),
    "initcolpollen": ParameterSpec(FLOAT, "0"),
    "maxcolnectar": ParameterSpec(FLOAT, "0"),
    "maxcolpollen": ParameterSpec(FLOAT, "0"),
    "suppollenamount": ParameterSpec(FLOAT, "0"),
    "supnectaramount": ParameterSpec(FLOAT, "0"),
    # Other
    "foragermaxprop": ParameterSpec(FLOAT, "0", "1"),
    # Day length is computed as at +/-65 degrees beyond that latitude.
    "latitude": ParameterSpec(FLOAT, "-90", "90"),
}


def _describe_range(spec: ParameterSpec) -> str:
    low, high = _parse_bound(spec.minimum), _parse_bound(spec.maximum)
    if low is not None and high is not None:
        lo_op = ">" if low[1] else ">="
        hi_op = "<" if high[1] else "<="
        return f"{lo_op} {low[0]:g} and {hi_op} {high[0]:g}"
    if low is not None:
        return f"{'>' if low[1] else '>='} {low[0]:g}"
    if high is not None:
        return f"{'<' if high[1] else '<='} {high[0]:g}"
    return ""


def validate_parameter(
    name: str, value: str, display_name: Optional[str] = None
) -> Tuple[bool, str, Optional[str]]:
    """Check one parameter value against its spec.

    Args:
        name: Parameter name, lowercased.
        value: Raw parameter value as a string.
        display_name: Name to use in error messages. Defaults to ``name``.

    Returns:
        ``(ok, normalized_value, error)``. When ``ok`` is False, ``error`` explains why
        the value was rejected. Integer parameters are normalized to a whole-number
        string so downstream parsing accepts them.
    """
    spec = PARAMETER_SPECS.get(name)
    if spec is None:
        return True, value, None

    label = display_name if display_name is not None else name

    try:
        number = float(value)
    except (TypeError, ValueError):
        return False, value, f"{label} must be a number, got '{value}'."

    if math.isnan(number) or math.isinf(number):
        return False, value, f"{label} must be a finite number, got '{value}'."

    low = _parse_bound(spec.minimum)
    high = _parse_bound(spec.maximum)
    below = low is not None and (number < low[0] or (low[1] and number == low[0]))
    above = high is not None and (number > high[0] or (high[1] and number == high[0]))
    if below or above:
        return (
            False,
            value,
            f"{label} is out of range: {value}. Must be {_describe_range(spec)}.",
        )

    if spec.kind == INTEGER:
        if number != int(number):
            return False, value, f"{label} must be a whole number, got '{value}'."
        return True, str(int(number)), None

    return True, value, None
