"""
Pure Python implementation of BeePop+ simulation engine.

This subpackage contains a complete Python port of the BeePop+ honey bee
colony simulation model, originally implemented in C++.

Main interface:
    BeePop: Primary class for running simulations

Example:
    >>> from pybeepop.beepop import BeePop
    >>> model = BeePop()
    >>> model.set_latitude(35.0)
    >>> model.set_weather_from_file('weather.csv')
    >>> model.run_simulation()
"""

from .beepop import BeePop, BEEPOP_VERSION

__all__ = ["BeePop", "BEEPOP_VERSION"]
