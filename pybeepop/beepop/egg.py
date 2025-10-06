"""BeePop+ Egg Module.

This module contains the Egg class that represents the earliest stage of honey
bee development. Eggs are laid by the queen and represent the beginning of the
bee lifecycle before hatching into larvae.

Eggs in the simulation develop over a fixed period (typically 3 days) before
transitioning to the larval stage. They require no resources during development.
"""

from pybeepop.beepop.bee import Bee


class Egg(Bee):
    """Egg stage honey bee class representing the earliest development stage.

    This class models honey bee eggs laid by the queen. Eggs represent the
    initial stage of bee development and require no resources while developing
    over a fixed incubation period before hatching into larvae.

    Eggs are not susceptible to mite infestation.
    They transition to larvae after completing their development period.

    Attributes:
        number (int): Population count for this egg cohort (inherited from Bee)
        age (float): Development age in days (inherited from Bee)
        alive (bool): Whether this cohort is alive (inherited from Bee)
    """

    def __init__(self, number=0):
        """Initialize a new Egg cohort.

        Creates an egg population with specified initial size. Eggs have
        no additional attributes beyond the base Bee class as they are
        the simplest life stage.

        Args:
            number (int, optional): Initial population size for this egg
                cohort. Defaults to 0.
        """
        super().__init__(number)

    def __str__(self):
        return f"Egg(number={self.number}, age={self.age}, alive={self.alive})"
