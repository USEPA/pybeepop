"""BeePop+ In-Hive Exposure Dose (IED) Module.

IMPORTANT NOTE: This module is currently NOT IMPLEMENTED or USED in the
BeePop+ Python simulation. The IEDItem class exists as a placeholder from the
C++ port but is not integrated into the simulation engine. The IED functionality
is disabled (ied_enable = False in session.py) and would require additional
development to become functional.

Classes:
    IEDItem: Individual in-hive exposure event with life-stage-specific mortality
            (NOT CURRENTLY USED IN SIMULATION)
"""

from datetime import datetime


class IEDItem:
    """In-hive exposure dose event causing life-stage-specific mortality.

    IMPORTANT: This class is currently NOT IMPLEMENTED or USED in the BeePop+
    Python simulation. It exists as a placeholder from the C++ port but is not
    integrated into the simulation engine. To use this functionality, additional
    development would be required to connect it to the colony mortality systems
    and enable the IED processing in the session manager.

    Represents an acute pesticide exposure event occurring within the hive
    that affects bees across multiple life stages. IED events model scenarios
    such as contaminated stored resources, residue buildup in wax comb, or
    other in-hive exposure pathways.

    Attributes:
        ied_date (datetime): Date when exposure event occurs
        mort_eggs (float): Mortality rate for eggs (proportion 0.0-1.0)
        mort_larvae (float): Mortality rate for larvae (proportion 0.0-1.0)
        mort_brood (float): Mortality rate for capped brood (proportion 0.0-1.0)
        mort_adults (float): Mortality rate for adult workers (proportion 0.0-1.0)
        mort_foragers (float): Mortality rate for foragers (proportion 0.0-1.0)
    """

    def __init__(
        self,
        ied_date=None,
        mort_eggs=0.0,
        mort_larvae=0.0,
        mort_brood=0.0,
        mort_adults=0.0,
        mort_foragers=0.0,
    ):
        self.ied_date = ied_date or datetime.now()
        self.mort_eggs = mort_eggs
        self.mort_larvae = mort_larvae
        self.mort_brood = mort_brood
        self.mort_adults = mort_adults
        self.mort_foragers = mort_foragers

    def __str__(self):
        return (
            f"IEDItem(date={self.ied_date}, mort_eggs={self.mort_eggs}, "
            f"mort_larvae={self.mort_larvae}, mort_brood={self.mort_brood}, "
            f"mort_adults={self.mort_adults}, mort_foragers={self.mort_foragers})"
        )
