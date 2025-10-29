"""BeePop+ Larva Module.

This module contains the Larva class that represents the larval stage of honey bee
development. Larvae are the feeding and growing stage between eggs and pupae in
the bee lifecycle, requiring care from nurse bees and being vulnerable to mite
infestation during this critical development period.

Larvae in the simulation represent cohorts that develop over multiple days before
pupating into capped brood. They consume resources and can become infested with
varroa mites that will affect their development and future adult longevity.
"""

from datetime import datetime
from pybeepop.beepop.bee import Bee


class Larva(Bee):
    """Larval stage honey bee class representing developing immature bees.

    This class models larval honey bees during their growth and development phase.
    Larvae require feeding from nurse bees and are susceptible to varroa mite
    infestation. They develop over several days before transitioning to the
    capped brood (pupal) stage.

    Larvae consume colony resources and their survival affects future adult
    populations. Mite infestation during the larval stage can reduce adult
    longevity and overall colony health.

    Attributes:
        number (int): Population count for this larval cohort (inherited from Bee)
        age (float): Development age in days (inherited from Bee)
        alive (bool): Whether this cohort is alive (inherited from Bee)
        infested (bool): Whether this larval cohort is infested with mites
        fertilized (bool): Whether associated mites are fertilized
        mites (int): Number of mites infesting this larval population
        infest_probability (float): Probability of mite infestation (0.0-1.0)
    """

    def __init__(self, number=0):
        """Initialize a new Larva cohort.

        Creates a larval bee population with specified initial size and
        default attributes for mite infestation status and development
        characteristics.

        Args:
            number (int, optional): Initial population size for this larval
                cohort. Defaults to 0.
        """
        super().__init__(number)
        self.infested = False
        self.fertilized = False
        self.mites = 0
        self.infest_probability = 0.0

    def reset(self):
        super().reset()
        self.infested = False
        self.fertilized = False
        self.mites = 0
        self.infest_probability = 0.0

    def __str__(self):
        return (
            f"Larva(number={self.number}, age={self.age}, alive={self.alive}, "
            f"infested={self.infested}, fertilized={self.fertilized}, "
            f"mites={self.mites}, infest_probability={self.infest_probability})"
        )
