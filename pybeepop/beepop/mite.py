"""
Mite Population Module for BeePop+ Varroa Mite Simulation

This module models Varroa destructor mite populations for BeePop+ honey bee colony
simulation, tracking resistant and non-resistant subpopulations.

Resistance to Varroa treatment is a property of the mite population, not of an individual
treatment. Resistant mites enter the population two ways: InitMitePctResistant sets the
proportion of the initial infestation, and PctImmMitesResistant sets the proportion of
each batch of immigrating mites, which arrive with their own split rather than adopting
the resident population's. Mites produced by reproduction scale the parent population's
split, so offspring inherit the parents' resistant proportion.

Treatments kill only the non-resistant subpopulation, so a schedule of repeated treatments
selects for resistance: the resistant share rises as susceptible mites are removed.

Classes:
    Mite: Varroa mite population with resistant/non-resistant tracking
"""


class Mite:
    """
    Varroa destructor mite population model for BeePop+ simulation.

    Attributes:
        resistant (float): Number of treatment-resistant mites, which survive Varroa
            treatments.
        non_resistant (float): Number of treatment-susceptible mites, which die at the
            treatment's pct_mortality while a treatment is active.

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
        # Truncates to whole mites, matching C++ CMite::operator+(CMite). This differs
        # from __iadd__ above, which does not truncate — also matching C++, where
        # operator+= is defined separately. `a + b` and `a += b` are therefore NOT
        # interchangeable here; swapping one for the other changes results.
        # C++ defines no operator+(double), so scalars are unsupported.
        if isinstance(other, Mite):
            res = self.resistant + other.resistant
            nres = self.non_resistant + other.non_resistant
            return Mite(int(res), int(nres))
        return NotImplemented

    def __sub__(self, other):
        # C++ defines no operator-(double), so scalars are unsupported.
        if isinstance(other, Mite):
            res = self.resistant - other.resistant
            nres = self.non_resistant - other.non_resistant
            return Mite(max(0.0, res), max(0.0, nres))
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
