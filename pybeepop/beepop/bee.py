"""BeePop+ Base Bee Module.

This module contains the base Bee class that serves as the foundation for all
honey bee life stages in the colony simulation. The Bee class provides common
attributes and methods shared across eggs, larvae, brood, and adult bees.

The Bee class implements the basic properties of bee populations including
population counts, age tracking, and vitality status. All specific life stages
inherit from this base class and extend it with stage-specific attributes
and behaviors.
"""


class Bee:
    """Base class for all honey bee life stages in the colony simulation.

    This class provides the fundamental attributes and methods common to all
    bee life stages. It tracks population counts, age, and survival status
    for cohorts of bees as they progress through their lifecycle.

    The Bee class serves as the foundation for the age-structured population
    model, where bees are grouped into cohorts that age and transition between
    life stages over time.

    Attributes:
        number (int): Population count for this bee cohort
        age (float): Age of this cohort in days since creation
        alive (bool): Whether this cohort is still alive and active
    """

    def __init__(self, number=0):
        """Initialize a new Bee cohort.

        Creates a bee population cohort with specified initial size and
        default attributes for age and survival status.

        Args:
            number (int, optional): Initial population size for this cohort.
                Must be non-negative integer. Defaults to 0.
        """
        # Enforce integer type to match C++ CBee::number (int)
        self.number = int(number)
        self.age = 0.0  # days
        self.alive = True

    def set_number(self, num):
        # Enforce integer type to match C++ CBee::number (int)
        self.number = int(num)

    def get_number(self):
        return self.number

    def kill(self):
        self.alive = False
        self.number = 0

    def is_alive(self):
        return self.alive

    def reset(self):
        self.number = 0
        self.age = 0.0
        self.alive = True

    def __eq__(self, other):
        if not isinstance(other, Bee):
            return False
        return self.alive == other.alive and self.number == other.number

    def __copy__(self):
        new_bee = Bee(self.number)
        new_bee.age = self.age
        new_bee.alive = self.alive
        return new_bee

    def __str__(self):
        return f"Bee(number={self.number}, age={self.age}, alive={self.alive})"
