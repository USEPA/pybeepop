"""BeePop+ Brood Module.

This module contains the Brood class that represents capped honey bee brood
(pupae) in the colony simulation. Brood represents the pupal stage where
developing bees undergo metamorphosis from larvae to adults within sealed
wax cells.

The Brood stage is critical for varroa mite reproduction, as mites enter
cells before capping and reproduce during the pupal development period.
This makes brood cells the primary site of mite population growth within
the colony.
"""

from pybeepop.beepop.bee import Bee
from pybeepop.beepop.mite import Mite


class Brood(Bee):
    """Capped brood (pupal) stage honey bee class representing developing pupae.

    This class models capped honey bee brood during the pupal development stage.
    Brood cells are sealed with wax caps and contain developing bees undergoing
    metamorphosis from larvae to adults. This stage is critical for varroa mite
    reproduction as mites breed within the sealed cells.

    Brood development takes a fixed number of days (species and caste dependent)
    before emerging as adult bees. The presence of mites in brood cells affects
    the health and longevity of emerging adults.

    Attributes:
        number (int): Population count for this brood cohort (inherited from Bee)
        age (float): Development age in days (inherited from Bee)
        alive (bool): Whether this cohort is alive (inherited from Bee)
        mites (Mite): Varroa mites reproducing within these brood cells
        prop_virgins (float): Proportion of virgin mites in this brood (0.0-1.0)
    """

    def __init__(self, number=0):
        """Initialize a new Brood cohort.

        Creates a capped brood population with specified initial size and
        default attributes for mite infestation and reproductive status.

        Args:
            number (int, optional): Initial population size for this brood
                cohort. Defaults to 0.
        """
        super().__init__(number)
        self.mites = Mite()  # Initialize with empty Mite object
        self.prop_virgins = 0.0

    def reset(self):
        super().reset()
        self.mites = Mite()  # Initialize with empty Mite object
        self.prop_virgins = 0.0

    def get_mites(self):
        return self.mites

    def set_mites(self, the_mites):
        if isinstance(the_mites, Mite):
            self.mites = the_mites
        elif isinstance(the_mites, (int, float)):
            self.mites = Mite(0, the_mites)  # Assume non-resistant
        else:
            self.mites = Mite()

    def set_prop_virgins(self, prop):
        if prop < 0:
            self.prop_virgins = 0
        elif prop > 1:
            self.prop_virgins = 1
        else:
            self.prop_virgins = prop

    def get_prop_virgins(self):
        return self.prop_virgins

    def __str__(self):
        return (
            f"Brood(number={self.number}, mites={self.mites}, "
            f"prop_virgins={self.prop_virgins}, alive={self.alive})"
        )
