"""
PyBeePop - A Python wrapper for the BeePop+ colony simulation model.

PyBeePop provides a pure Python implementation of the BeePop+ honey bee colony
dynamics model for colony simulation and pesticide risk estimation.
"""

from .pybeepop import PyBeePop
from .exceptions import (
    BeepopException,
    BeepopParameterError,
    BeepopRuntimeError,
    BeepopFileError,
)

__version__ = "0.3.0"

__all__ = [
    "PyBeePop",
    "BeepopException",
    "BeepopParameterError",
    "BeepopRuntimeError",
    "BeepopFileError",
    "__version__",
]
