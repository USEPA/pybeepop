"""BeePop+ Adult Bee Module.

This module contains the Adult class that represents mature honey bees (workers,
drones, and foragers) in the colony simulation. Adult bees are the final life
stage that can perform colony functions including foraging, nursing, and reproduction.

The Adult class extends the base Bee class with additional attributes specific
to adult bee behavior including lifespan tracking, mite infestations, foraging
capacity, and age-dependent mortality.

Adult bees in the simulation represent discrete cohorts that age daily and
eventually die based on their maximum lifespan and environmental factors.
Workers can transition to foraging roles based on colony needs and population
dynamics.
"""

from pybeepop.beepop.bee import Bee
from pybeepop.beepop.mite import Mite


class Adult(Bee):
    """Adult honey bee class representing mature workers, drones, or foragers.

    This class models adult honey bees that have completed metamorphosis and
    are capable of performing colony functions. Adult bees track their age,
    lifespan, mite load, and foraging contribution within the colony simulation.

    Adult bees age daily and die when they exceed their maximum lifespan.
    Workers may transition to foraging roles based on colony needs. All adults
    can carry varroa mites that affect their longevity and colony health.

    Attributes:
        number (int): Population count for this age cohort (inherited from Bee)
        age (float): Bee age in simulation time units (inherited from Bee)
        alive (bool): Whether this cohort is alive (inherited from Bee)
        lifespan (float): Maximum lifespan for this adult cohort
        current_age (float): Current age of this adult cohort
        mites (Mite): Varroa mites carried by this adult population
        prop_virgins (float): Proportion of virgin mites (0.0-1.0)
        forage_inc (float): Foraging increment/contribution value
        mites_counted (bool): Whether mites have been counted this period
    """

    def __init__(self, number=0):
        """Initialize a new Adult bee cohort.

        Creates an adult bee population with specified initial size and
        default attributes for lifespan, age, mite load, and behavioral
        characteristics.

        Args:
            number (int, optional): Initial population size for this adult
                cohort. Defaults to 0.
        """
        super().__init__(number)
        self.lifespan = 0.0
        self.current_age = 0.0
        self.mites = Mite()  # Initialize with empty Mite object
        self.prop_virgins = 0.0
        self.forage_inc = 0.0
        self.mites_counted = False

    def set_lifespan(self, span):
        self.lifespan = float(span)

    def set_current_age(self, age):
        self.current_age = age

    def set_prop_virgins(self, prop):
        if prop < 0.0:
            self.prop_virgins = 0.0
        elif prop > 1.0:
            self.prop_virgins = 1.0
        else:
            self.prop_virgins = prop

    def get_prop_virgins(self):
        return self.prop_virgins

    def increment_age(self, increment):
        self.current_age += increment

    def get_current_age(self):
        return self.current_age

    def get_lifespan(self):
        return int(self.lifespan)

    def set_forage_inc(self, inc):
        self.forage_inc = inc

    def get_forage_inc(self):
        return self.forage_inc

    def set_mites(self, the_mites):
        self.mites = the_mites

    def get_mites(self):
        return self.mites

    def have_mites_been_counted(self):
        return self.mites_counted

    def set_mites_counted(self, value):
        self.mites_counted = value

    def reset(self):
        super().reset()
        self.lifespan = 0.0
        self.current_age = 0.0
        self.mites = Mite()  # Initialize with empty Mite object
        self.prop_virgins = 0.0
        self.forage_inc = 0.0
        self.mites_counted = False

    def copy_from(self, other):
        """Copy all attributes from another Adult object."""
        if isinstance(other, Adult):
            self.number = int(other.number)
            self.age = other.age
            self.alive = other.alive
            # Copy Adult-specific attributes
            self.lifespan = other.lifespan
            self.current_age = other.current_age
            self.mites = other.mites
            self.prop_virgins = other.prop_virgins
            self.forage_inc = other.forage_inc
            self.mites_counted = other.mites_counted

    def __eq__(self, other):
        if not isinstance(other, Adult):
            return False
        return (
            self.lifespan == other.lifespan
            and self.current_age == other.current_age
            and self.mites == other.mites
            and self.prop_virgins == other.prop_virgins
            and self.forage_inc == other.forage_inc
            and self.number == other.number
            and self.alive == other.alive
            and self.mites_counted == other.mites_counted
        )

    def __str__(self):
        return (
            f"Adult(number={self.number}, lifespan={self.lifespan}, "
            f"current_age={self.current_age}, mites={self.mites}, "
            f"prop_virgins={self.prop_virgins}, forage_inc={self.forage_inc}, "
            f"mites_counted={self.mites_counted}, alive={self.alive})"
        )
