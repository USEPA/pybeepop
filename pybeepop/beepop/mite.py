"""
Mite Population Module for BeePop+ Varroa Mite Simulation

This module models Varroa destructor mite populations with resistance genetics
for BeePop+ honey bee colony simulation. It tracks resistant and non-resistant
mite subpopulations, supporting treatment efficacy modeling and resistance
evolution studies.

Classes:
    Mite: Varroa mite population with resistance genetics tracking
"""


class Mite:
    """
    Varroa destructor mite population model with resistance genetics for BeePop+ simulation.

    Attributes:
        resistant (float): Number of treatment-resistant mites in population
        non_resistant (float): Number of treatment-susceptible mites in population

    Note:
        Arithmetic operations include C++ compatibility features like integer
        truncation in addition operations to maintain exact simulation reproducibility.
    """

    def __init__(self, resistant=0.0, non_resistant=0.0):
        self.resistant = resistant
        self.non_resistant = non_resistant

    def zero(self):
        self.resistant = 0.0
        self.non_resistant = 0.0

    def get_resistant(self):
        return self.resistant

    def get_non_resistant(self):
        return self.non_resistant

    def set_resistant(self, num):
        self.resistant = num

    def set_non_resistant(self, num):
        self.non_resistant = num

    def get_total(self):
        return self.resistant + self.non_resistant

    def get_pct_resistant(self):
        total = self.get_total()
        return (100.0 * self.resistant / total) if total > 0 else 0.0

    def set_pct_resistant(self, pct):
        total = self.get_total()
        self.resistant = total * pct / 100.0
        self.non_resistant = total - self.resistant

    def __iadd__(self, other):
        if isinstance(other, Mite):
            self.resistant += other.resistant
            self.non_resistant += other.non_resistant
        elif isinstance(other, (int, float)):
            total = self.get_total()
            pctres = self.resistant / total if total > 0 else 0.0
            addtores = other * pctres
            self.resistant += addtores
            self.non_resistant += other - addtores
        return self

    def __isub__(self, other):
        if isinstance(other, Mite):
            self.resistant -= other.resistant
            self.non_resistant -= other.non_resistant
        elif isinstance(other, (int, float)):
            total = self.get_total()
            pctres = self.resistant * 100 / total if total > 0 else 0.0
            subfromres = other * pctres / 100.0
            self.resistant -= subfromres
            self.non_resistant -= other - subfromres
            self.resistant = max(0.0, self.resistant)
            self.non_resistant = max(0.0, self.non_resistant)
        return self

    def __add__(self, other):
        if isinstance(other, Mite):
            # Match C++ behavior: truncate to int like CMite::operator+(CMite theMite)
            res = self.resistant + other.resistant
            nres = self.non_resistant + other.non_resistant
            return Mite(int(res), int(nres))
        elif isinstance(other, (int, float)):
            return Mite(self.resistant, self.non_resistant + other)
        return NotImplemented

    def __radd__(self, other):
        # Handle cases like 0 + Mite or int + Mite
        if isinstance(other, (int, float)):
            return Mite(self.resistant, self.non_resistant + other)
        return NotImplemented

    def __sub__(self, other):
        if isinstance(other, Mite):
            res = self.resistant - other.resistant
            nres = self.non_resistant - other.non_resistant
            return Mite(max(0.0, res), max(0.0, nres))
        elif isinstance(other, (int, float)):
            return Mite(self.resistant, max(0.0, self.non_resistant - other))
        return NotImplemented

    def __mul__(self, value):
        if isinstance(value, (int, float)):
            return Mite(self.resistant * value, self.non_resistant * value)
        return NotImplemented

    def __int__(self):
        return int(self.get_total())

    def __eq__(self, other):
        if not isinstance(other, Mite):
            return False
        return (
            self.resistant == other.resistant
            and self.non_resistant == other.non_resistant
        )

    def assign_value(self, value):
        """
        Matches C++ CMite::operator=(double value) behavior.
        Sets resistant = 0 and non_resistant = value.
        """
        self.resistant = 0.0
        self.non_resistant = float(value)
        return self

    def __str__(self):
        return f"Mite(resistant={self.resistant}, non_resistant={self.non_resistant})"
