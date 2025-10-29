"""BeePop+ Bee List Management Module.

This module contains the BeeList base class and its derived classes that manage
age-structured populations of honey bees at different life stages. These classes
implement the "boxcar" model where bees are grouped into age cohorts that advance
through discrete time steps.

The bee list system provides the core data structure for tracking population
dynamics, aging, transitions between life stages, and mortality events within
the colony simulation. Each life stage (eggs, larvae, brood, adults, foragers)
has its own specialized list class with stage-specific behaviors.

Key Classes:
    BeeList: Base class for all bee population management
    EggList: Manages egg populations and hatching
    LarvaList: Manages larval development and feeding
    BroodList: Manages capped brood and mite reproduction
    AdultList: Manages adult worker and drone populations
    ForagerListA: Manages foraging worker populations with enhanced tracking

Architecture:
    The bee list system uses a "boxcar" or cohort model where:
    - Each list element represents a daily age cohort
    - Bees age by advancing through list positions
    - Transitions occur when bees move between life stages
    - The "caboose" captures overflow from the oldest cohorts

List Management:
    - Daily aging advances all cohorts by one position
    - New bees are added to the head (youngest position)
    - Old bees exit from the tail or transition to next life stage
    - Population counts are maintained for each age cohort
    - Mite loads and other attributes track with bee cohorts
"""

from pybeepop.beepop.adult import Adult
from pybeepop.beepop.brood import Brood
from pybeepop.beepop.larva import Larva
from pybeepop.beepop.egg import Egg
from pybeepop.beepop.globaloptions import GlobalOptions


class BeeList:
    """Base class for age-structured bee population management.

    This class provides the foundation for managing bee populations using a
    "boxcar" or cohort model where bees are grouped by age and advance through
    discrete time steps. Each list element represents a daily age cohort with
    specific population counts and characteristics.

    The BeeList class handles common operations for all bee life stages including
    aging, mortality, transitions, and population tracking. Derived classes
    extend this functionality with stage-specific behaviors and attributes.

    Class Attributes:
        DroneCount (int): Global counter for drone populations
        ForagerCount (int): Global counter for forager populations
        WorkerCount (int): Global counter for worker populations

    Attributes:
        bees (List[Bee]): List of bee cohorts ordered by age (youngest first)
        _list_length (int): Maximum length of the bee list (life stage duration)
        _colony (Colony): Reference to parent colony object
        _prop_transition (float): Base proportion of bees transitioning out (0.0-1.0)
        _drv_list (DateRangeValues): Date-dependent transition proportions
    """

    # Class-level counters (shared across all instances)
    DroneCount = 0
    ForagerCount = 0
    WorkerCount = 0

    def __init__(self):
        """Initialize a new BeeList with empty populations.

        Creates an empty bee list with default settings for managing
        age-structured bee populations. The list starts with no bees
        and default transition parameters.
        """
        self.bees = []
        self._list_length = 0
        self._colony = None
        self._prop_transition = 1.0
        self._drv_list = None  # DateRangeValues object for dynamic transition control

    def set_length(self, length):
        """Set the list length (life stage duration)."""
        self._list_length = length

    def get_length(self):
        """Get the list length (life stage duration)."""
        return self._list_length

    def set_colony(self, colony):
        """Set reference to parent colony object."""
        self._colony = colony

    def get_colony(self):
        """Get reference to parent colony object."""
        return self._colony

    def set_prop_transition(self, prop):
        """Set proportion of bees transitioning from this list."""
        self._prop_transition = prop

    def get_prop_transition(self):
        """Get proportion of bees transitioning from this list."""
        return self._prop_transition

    def set_drv_list(self, drv_list):
        """Set the DateRangeValues object for this bee list."""
        self._drv_list = drv_list

    def get_drv_list(self):
        """Get the DateRangeValues object for this bee list."""
        return self._drv_list

    def get_effective_prop_transition(self, current_date=None):
        """
        Get the effective proportion transition for the current date.
        If a DateRangeValues object is set and enabled, it will override the base proportion.
        Following C++ logic from colony.cpp lines 1392-1434.
        """
        # If no date range values are set, use the base proportion
        if self._drv_list is None or not self._drv_list.is_enabled():
            return self._prop_transition

        # If no date is provided, use the base proportion
        if current_date is None:
            return self._prop_transition

        # Try to get the active value from the date range values
        drv_value = self._drv_list.get_active_value(current_date)
        if drv_value is not None:
            # Convert from percentage to proportion (following C++ logic: PropTransition / 100)
            return drv_value / 100.0
        else:
            # No active date range value found, use base proportion
            return self._prop_transition

    def clear(self):
        """Clears the bee list."""
        self.bees = []

    def get_count(self):
        """Get the number of bees in the list (alias for get_quantity)."""
        return self.get_quantity()

    def add_head(self, bee):
        """Add a bee to the head (beginning) of the list."""
        self.bees.insert(0, bee)

    def get_bee_class(self):
        """Get the bee class for this list type. Override in derived classes."""
        return Egg

    def get_quantity(self):
        """Returns the total number of alive bees in the list."""
        total = 0
        for bee in self.bees:
            if bee.is_alive():
                total += bee.get_number()
        return int(total)

    def kill_all(self):
        """Kills all bees in the list."""
        for bee in self.bees:
            bee.kill()

    def remove_list_elements(self):
        """Removes all bees from the list and deletes them."""
        self.bees.clear()

    def get_quantity_at(self, index):
        """Returns the quantity of bees at the specified index (boxcar). Single index version."""
        if 0 <= index < len(self.bees) and self.bees[index] is not None:
            number = self.bees[index].get_number()
            return int(number) if number is not None else 0
        return 0

    def set_quantity_at(self, index, quan):
        """Sets the quantity of bees at the specified index (boxcar). Single index version."""
        if 0 <= index < len(self.bees):
            self.bees[index].set_number(quan)

    def get_quantity_at_range(self, from_idx, to_idx):
        """Returns the sum of quantities from 'from_idx' to 'to_idx' inclusive. Range version."""
        count = 0
        list_length = len(self.bees)

        if from_idx >= 0 and from_idx < list_length:
            for i in range(from_idx, min(to_idx + 1, list_length)):
                count += self.get_quantity_at(i)  # Calls single-index version
        return int(count)

    def set_quantity_at_range(self, from_idx, to_idx, quan):
        """Evenly divides 'quan' bees between boxcars from 'from_idx' to 'to_idx' inclusive. Range version."""
        if from_idx > to_idx:
            return

        list_length = len(self.bees)
        if to_idx > list_length - 1:
            to_idx = list_length - 1

        if from_idx >= 0 and from_idx <= to_idx:
            num_boxcars = 1 + (to_idx - from_idx)
            quan_per_boxcar = int(quan / num_boxcars) if num_boxcars > 0 else 0
            for i in range(from_idx, to_idx + 1):
                self.set_quantity_at(i, quan_per_boxcar)  # Calls single-index version

    def set_quantity_at_proportional(self, from_idx, to_idx, proportion):
        """Sets the quantity of bees in boxcars between from_idx and to_idx = Number*Proportion."""
        list_length = len(self.bees)
        if to_idx > list_length - 1:
            to_idx = list_length - 1

        if from_idx >= 0 and from_idx <= to_idx:
            for i in range(from_idx, to_idx + 1):
                boxcar_quant = self.get_quantity_at(i)
                self.set_quantity_at(i, int(boxcar_quant * proportion))

    def factor_quantity(self, factor):
        """Factor quantity increases or decreases the number of bees in each age group."""
        for bee in self.bees:
            bee.set_number(int(bee.get_number() * factor))

    def status(self):
        """Returns a string status of the bee list."""
        stat = f"Tot BC: {len(self.bees)}, "
        stat += ", ".join(
            f"BC{i+1}: {bee.get_number()}" for i, bee in enumerate(self.bees)
        )
        return stat


# Derived classes (stubs, ported from colony.cpp)
# ForagerListA will be defined after AdultList since it inherits from it


class AdultList(BeeList):
    """Adult bee list for drones and workers. Ported from CAdultlist."""

    def __init__(self):
        super().__init__()
        self.caboose = Adult(0)  # Initialize with empty adult, not None

    def get_bee_class(self):
        """Get the bee class for adult lists."""
        return Adult

    def get_caboose(self):
        """Returns the caboose (oldest bee group)."""
        return self.caboose

    def clear_caboose(self):
        """Resets the caboose."""
        if self.caboose:
            self.caboose.reset()
        self.caboose = None

    def add(self, brood, colony, event, is_worker=True):
        new_adult = Adult(brood.get_number())
        if is_worker:
            AdultList.WorkerCount += 1
        else:
            AdultList.DroneCount += 1
        new_adult.set_mites(brood.get_mites())
        new_adult.set_prop_virgins(brood.get_prop_virgins())
        new_adult.set_lifespan(colony.wadllife)
        brood.reset()
        if len(self.bees) > 0:
            adult = self.bees[0]
            adult.set_number(adult.get_number() + new_adult.get_number())
            adult.set_mites(adult.get_mites() + new_adult.get_mites())
            adult.set_prop_virgins(
                adult.get_mites().get_total()
                if adult.get_mites().get_total() > 0
                else 0
            )
        else:
            self.bees.insert(0, new_adult)

    def update(self, brood, colony, event, is_worker=True):
        """Updates the adult list with incoming brood and ages existing adults."""
        # Create new adult from brood
        new_adult = self.get_bee_class()(brood.get_number())
        if is_worker:
            AdultList.WorkerCount += 1
        else:
            AdultList.DroneCount += 1

        new_adult.set_mites(brood.get_mites())
        new_adult.set_prop_virgins(brood.get_prop_virgins())
        new_adult.set_lifespan(21)  # WADLLIFE = 21

        # Save emerging mites for colony
        if hasattr(colony, "emerging_mites_w"):
            if is_worker:
                colony.emerging_mites_w = brood.get_mites()
                colony.prop_emerging_virgins_w = brood.get_prop_virgins()
                colony.num_emerging_brood_w = brood.get_number()
            else:
                colony.emerging_mites_d = brood.get_mites()
                colony.prop_emerging_virgins_d = brood.get_prop_virgins()
                colony.num_emerging_brood_d = brood.get_number()

        brood.reset()  # These brood are now gone
        self.add_head(new_adult)

        # Check if list is full - move oldest to caboose
        if len(self.bees) >= (self._list_length + 1):
            adult_to_remove = self.bees.pop()
            # Use effective transition proportion based on date range values
            effective_transition = self.get_effective_prop_transition(
                event.get_time() if event else None
            )
            self.caboose.age = adult_to_remove.age
            self.caboose.alive = adult_to_remove.alive
            self.caboose.number = int(adult_to_remove.number * effective_transition)

            if not is_worker:
                # Drone adults die - update stats
                if hasattr(colony, "m_InOutEvent"):
                    colony.m_InOutEvent.m_DeadDAdults = self.caboose.get_number()
                self.caboose.reset()
                AdultList.DroneCount -= 1
        else:
            self.caboose.reset()

        # Check for age beyond reduced lifespan due to mite infestation (workers only)
        if is_worker:
            day = 1
            for adult in self.bees:
                num_mites = adult.get_mites()
                if (
                    adult.is_alive()
                    and num_mites.get_total() > 0
                    and adult.get_number() > 0
                ):
                    index = min(num_mites.get_total() // adult.get_number(), 7)
                    prop_redux = (
                        colony.long_redux[int(index)]
                        if hasattr(colony, "long_redux")
                        else 0
                    )
                    if day > (1 - prop_redux) * (
                        adult.get_lifespan() + colony.m_CurrentForagerLifespan
                    ):
                        adult.kill()
                day += 1

    def kill_all(self):
        super().kill_all()
        if self.caboose:
            self.caboose.kill()

    def update_length(self, length, is_worker=True):
        """Adjusts the list length, moving excess bees to caboose or adding boxcars."""
        if is_worker:
            if length < len(self.bees):
                adults_to_foragers = 0
                while len(self.bees) > length and len(self.bees) > 0:
                    adult = self.bees.pop()
                    adults_to_foragers += adult.get_number()
                    # Add to caboose instead of deleting
                    if hasattr(self, "caboose"):
                        self.caboose.set_number(
                            self.caboose.get_number() + adult.get_number()
                        )

                # Note: adults_to_foragers will become foragers in next Update call
            else:
                # Add empty boxcars if needed
                while len(self.bees) < length:
                    self.bees.append(self.get_bee_class()())

        self._list_length = length

    def move_to_end(self, quantity_to_move, min_age):
        """Moves the oldest quantity_to_move bees to the last boxcar, not moving any adults younger than min_age."""
        if min_age < 0 or quantity_to_move <= 0:
            return 0
        total_moved = 0
        end_index = len(self.bees) - 1
        index = len(self.bees) - 2
        while total_moved < quantity_to_move and index >= min_age:
            currently_moving = self.get_quantity_at(index)
            if currently_moving > quantity_to_move - total_moved:
                currently_moving = quantity_to_move - total_moved
            # Add currently_moving to the end boxcar
            self.set_quantity_at(
                end_index, currently_moving + self.get_quantity_at(end_index)
            )
            # Remove them from the current boxcar
            self.set_quantity_at(index, self.get_quantity_at(index) - currently_moving)
            total_moved += currently_moving
            index -= 1
        # Optionally, print status for debugging
        # print(f"In move_to_end: {self.status()}")
        return total_moved


# --- ForagerListA class (inherits from AdultList to match C++ CForagerlistA : public CAdultlist) ---
class ForagerListA(AdultList):
    """Specialized adult list managing forager bee populations with unemployment tracking.

    Extends AdultList to handle forager-specific dynamics including active vs. unemployed
    foragers, pending forager pools, and proportional colony size limits on active foraging.
    Implements the BEEPOP algorithm's forager management where only a proportion of potential
    foragers are actively employed based on colony needs.

    Attributes:
        pending_foragers (list): Queue of unemployed forager Adult objects awaiting activation.
        prop_actual_foragers (float): Proportion of colony that can be active foragers (default 0.3).
    """

    def __init__(self):
        super().__init__()
        self.pending_foragers = []
        self.prop_actual_foragers = 0.3

    def get_bee_class(self):
        """Get the bee class for forager lists."""
        return Adult  # Foragers are adult bees

    def clear_pending_foragers(self):
        """Clears all pending foragers."""
        self.pending_foragers.clear()

    def get_quantity(self):
        """Returns total foragers (active + pending)."""
        return int(
            super().get_quantity() + sum(a.get_number() for a in self.pending_foragers)
        )

    def get_active_quantity(self):
        """Returns the number of active foragers, limited by colony size proportion."""
        quan = self.get_quantity()
        if quan > 0:
            colony_size = self._colony.get_colony_size()
            max_active = int(colony_size * self.prop_actual_foragers)
            if quan > max_active:
                quan = max_active
        return quan

    def get_unemployed_quantity(self):
        """Returns the number of unemployed foragers."""
        return self.get_quantity() - self.get_active_quantity()

    def kill_all(self):
        super().kill_all()
        for bee in self.pending_foragers:
            bee.kill()
        self.clear_pending_foragers()

    def set_prop_actual_foragers(self, proportion):
        """Sets the actual foragers proportion."""
        self.prop_actual_foragers = proportion

    def get_prop_actual_foragers(self):
        """Gets the actual foragers proportion."""
        return self.prop_actual_foragers

    def set_length(self, length):
        """Sets the length of the forager list, adding/removing boxcars as needed."""
        self._list_length = length  # Fixed: use _list_length to match base class
        while len(self.bees) > length:
            self.bees.pop()
        while len(self.bees) < length:
            # Fixed: Create Adult objects for foragers, not base Bee objects
            self.bees.append(Adult())

    def update(self, adult, colony, event):
        """Updates the forager list with incoming adults and manages pending foragers."""
        WINTER_MORTALITY_PER_DAY = 0.10 / 152

        # C++ logic: Always process the adult, even if number is 0
        # C++ lines 285-287: Change lifespan from worker to forager
        ForagerListA.WorkerCount -= 1
        ForagerListA.ForagerCount += 1
        adult.set_lifespan(colony.m_CurrentForagerLifespan)
        adult.set_current_age(0.0)

        pending_foragers_first = (
            GlobalOptions.get().should_foragers_always_age_based_on_forage_inc
        )

        if pending_foragers_first:
            # Add adult to pending foragers (even if 0 bees)
            if len(self.pending_foragers) == 0:
                add_adult = Adult()
                add_adult.copy_from(adult)
                self.pending_foragers.insert(0, add_adult)
            else:
                pending_adult = self.pending_foragers[0]
                if pending_adult.get_forage_inc() == 0.0:
                    # Add to existing pending adult with 0 forage increment
                    pending_adult.set_number(
                        pending_adult.get_number() + adult.get_number()
                    )
                    adult.reset()
                    ForagerListA.ForagerCount -= 1
                else:
                    # Create new pending adult
                    add_adult = Adult()
                    add_adult.copy_from(adult)
                    self.pending_foragers.insert(0, add_adult)

        if event.is_forage_day():
            if not pending_foragers_first:
                # Add adult to pending foragers (even if 0 bees)
                add_adult = Adult()
                add_adult.copy_from(adult)
                self.pending_foragers.insert(0, add_adult)

            # Increment forage increment for all pending foragers
            for pending_adult in self.pending_foragers:
                pending_adult.set_forage_inc(
                    pending_adult.get_forage_inc() + event.get_forage_inc()
                )

            # Move pending foragers with >= 1.0 forage increment to main list
            add_head = False
            foragers_head = Adult()
            to_remove = []

            for i in reversed(range(len(self.pending_foragers))):
                pending_adult = self.pending_foragers[i]
                if pending_adult.get_forage_inc() >= 1.0:
                    add_head = True
                    foragers_head.set_number(
                        foragers_head.get_number() + pending_adult.get_number()
                    )
                    to_remove.append(i)

            # Remove processed pending foragers
            for i in to_remove:
                del self.pending_foragers[i]

            # Add new foragers to head of list
            if add_head:
                self.bees.insert(0, foragers_head)
                # C++ logic: IMMEDIATELY remove tail when adding head (line 387-388)
                if len(self.bees) > 1:  # Only remove if there's something to remove
                    removed = self.bees.pop()  # delete (RemoveTail())

                # C++ logic: Additional check if list is still full (lines 390-394)
                if len(self.bees) >= (self._list_length + 1):
                    self.caboose = self.bees.pop()
                    ForagerListA.ForagerCount -= 1
                else:
                    self.caboose.reset()
            else:
                # When not adding head, still check if list is full and remove oldest
                if len(self.bees) >= (self._list_length + 1):
                    self.caboose = self.bees.pop()
                    ForagerListA.ForagerCount -= 1
                else:
                    self.caboose.reset()

        elif not pending_foragers_first:
            # Non-forage day - add adult (even if 0 bees) to first boxcar
            if len(self.bees) == 0:
                if self._list_length > 0:
                    add_adult = Adult()
                    add_adult.copy_from(adult)
                    self.pending_foragers.insert(0, add_adult)
                    self.bees.insert(0, add_adult)
            else:
                # Add to first boxcar (even 0 bees)
                forager_head = self.bees[0]
                forager_head.set_number(forager_head.get_number() + adult.get_number())
                adult.reset()
                ForagerListA.ForagerCount -= 1

        # Age existing foragers and check for mite mortality (ALWAYS runs - this is key!)
        self._age_existing_foragers(colony, event)

    def _age_existing_foragers(self, colony, event):
        """Ages existing foragers and applies mite mortality and winter mortality."""
        WINTER_MORTALITY_PER_DAY = 0.10 / 152

        # Check for lifespan reduction due to mite infestation
        day = 21 + 1  # WADLLIFE + 1
        colony.m_InOutEvent.m_PropRedux = 0

        for list_adult in self.bees:
            if list_adult.is_alive():
                if list_adult.get_number() <= 0:
                    prop_redux = (
                        colony.long_redux[0] if hasattr(colony, "long_redux") else 0
                    )
                else:
                    mite_index = min(
                        int(
                            list_adult.get_mites().get_total() / list_adult.get_number()
                        ),
                        (
                            len(colony.long_redux) - 1
                            if hasattr(colony, "long_redux")
                            else 0
                        ),
                    )
                    prop_redux = (
                        colony.long_redux[mite_index]
                        if hasattr(colony, "long_redux")
                        else 0
                    )

                if prop_redux > 0:
                    colony.m_InOutEvent.m_PropRedux = (
                        list_adult.get_mites().get_total() / list_adult.get_number()
                    )

                if day > (1 - prop_redux) * (
                    21 + colony.m_CurrentForagerLifespan
                ):  # WADLLIFE = 21
                    list_adult.kill()
            day += 1

        # Winter mortality (November through March)
        if event.get_time().month >= 11 or event.get_time().month < 4:
            for the_forager in self.bees:
                number = the_forager.get_number()
                new_number = int(number * (1 - WINTER_MORTALITY_PER_DAY))
                if hasattr(colony, "m_InOutEvent"):
                    colony.m_InOutEvent.m_WinterMortalityForagersLoss += (
                        number - new_number
                    )
                the_forager.set_number(new_number)


class BroodList(BeeList):
    """Age-structured list managing capped brood populations with mite infestation tracking.

    Specialized BeeList for managing capped brood (pupae) using boxcar model dynamics.
    Tracks mite infestation levels, distribution patterns, and provides colony health
    metrics related to brood viability. Handles transitions from larvae to emerging adults
    with proper mite load inheritance.

    Attributes:
        caboose (Brood): Oldest brood cohort ready for emergence as adults.
    """

    def __init__(self):
        super().__init__()
        self.caboose = Brood(0)  # Initialize with empty brood, not None

    def get_bee_class(self):
        """Get the bee class for brood lists."""
        return Brood

    def get_caboose(self):
        """Returns the caboose (oldest bee group)."""
        return self.caboose

    def clear_caboose(self):
        """Resets the caboose."""
        if self.caboose:
            self.caboose.set_number(0)
        self.caboose = None

    def update(self, larva, current_date=None):
        """Updates brood list with incoming larvae."""
        new_brood = self.get_bee_class()(int(larva.get_number()))
        larva.reset()  # These larvae are now gone
        self.add_head(new_brood)

        if len(self.bees) >= (self._list_length + 1):
            tail = self.bees.pop()
            # Move to caboose with proper transition using effective proportion
            effective_transition = self.get_effective_prop_transition(current_date)
            self.caboose.age = tail.age
            self.caboose.alive = tail.alive
            self.caboose.set_mites(tail.get_mites())
            self.caboose.set_prop_virgins(tail.get_prop_virgins())
            self.caboose.number = int(tail.number * effective_transition)
        else:
            self.caboose.reset()

    def get_mite_count(self):
        """Returns total mite count in all brood."""
        total_count = 0.0
        for bee in self.bees:
            if hasattr(bee, "mites"):
                total_count += bee.mites.get_total()
        return total_count

    def get_prop_infest(self):
        """Returns proportion of infested brood cells."""
        total_cells = sum(bee.get_number() for bee in self.bees)
        total_uninfested = 0
        for bee in self.bees:
            mite_count = bee.mites.get_total() if hasattr(bee, "mites") else 0
            total_uninfested += max(bee.get_number() - mite_count, 0)
        if total_cells > 0:
            return 1 - (total_uninfested / total_cells)
        return 0.0

    def get_mites_per_cell(self):
        """Returns average mites per brood cell."""
        total_cells = sum(bee.get_number() for bee in self.bees)
        total_mites = self.get_mite_count()
        return (total_mites / total_cells) if total_cells > 0 else 0.0

    def distribute_mites(self, mites):
        """Distributes mites evenly across all brood."""
        if not self.bees:
            return

        # Use total mite count divided by number of boxcars, like C++ version
        mites_per_boxcar = mites.get_total() / len(self.bees)
        percent_resistant = mites.get_pct_resistant()

        for bee in self.bees:
            # Match C++ behavior exactly:
            # pBrood->m_Mites = MitesPerBoxcar (assignment operator)
            # pBrood->m_Mites.SetPctResistant(PercentRes)
            bee.mites.assign_value(mites_per_boxcar)  # Matches C++ operator=(double)
            bee.mites.set_pct_resistant(percent_resistant)


class LarvaList(BeeList):
    """Age-structured list managing larval bee populations during development phase.

    Specialized BeeList for managing larvae using boxcar model dynamics. Handles
    transitions from eggs to capped brood stage, tracking larval development timing
    and survival rates.

    Attributes:
        caboose (Larva): Oldest larval cohort ready for transition to capped brood.
    """

    def get_bee_class(self):
        """Get the bee class for larva lists."""
        return Larva

    def get_caboose(self):
        """Returns the caboose (oldest bee group)."""
        return self.caboose

    def clear_caboose(self):
        """Resets the caboose."""
        if self.caboose:
            self.caboose.set_number(0)
        self.caboose = None

    def __init__(self):
        super().__init__()
        self.caboose = Larva(0)  # Initialize with empty larva, not None

    def update(self, egg, current_date=None):
        """Updates larva list with incoming eggs."""
        new_larva = self.get_bee_class()(int(egg.get_number()))
        egg.reset()  # These eggs are now gone
        self.add_head(new_larva)

        if len(self.bees) >= (self._list_length + 1):
            tail = self.bees.pop()
            # Move to caboose with proper transition using effective proportion
            effective_transition = self.get_effective_prop_transition(current_date)
            self.caboose.age = tail.age
            self.caboose.alive = tail.alive
            self.caboose.number = int(tail.number * effective_transition)
        else:
            self.caboose.reset()


# --- EggList class (Python port of CEgglist) ---
class EggList(BeeList):
    """Age-structured list managing egg populations from queen laying to larval emergence.

    Specialized BeeList for managing eggs using boxcar model dynamics. Handles
    initial egg placement from queen laying activities and tracks incubation timing
    until eggs transition to larval stage. Forms the foundation of the colony's
    reproductive pipeline.

    Attributes:
        caboose (Egg): Oldest egg cohort ready for transition to larval stage.
    """

    def __init__(self):
        super().__init__()
        self.caboose = Egg(0)  # Initialize with empty egg, not None

    def get_bee_class(self):
        """Get the bee class for egg lists."""
        return Egg

    def get_caboose(self):
        """Returns the caboose (oldest egg group)."""
        return self.caboose

    def update(self, new_egg, current_date=None):
        """Updates egg list with new eggs from queen."""
        new_eggs = self.get_bee_class()(new_egg.get_number())
        self.add_head(new_eggs)

        if len(self.bees) >= (self._list_length + 1):
            tail = self.bees.pop()
            # Move to caboose with proper transition using effective proportion
            effective_transition = self.get_effective_prop_transition(current_date)
            self.caboose.age = tail.age
            self.caboose.alive = tail.alive
            self.caboose.number = int(tail.number * effective_transition)
        else:
            self.caboose.reset()

    def kill_all(self):
        super().kill_all()
