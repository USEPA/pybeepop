"""BeePop+ Mite Treatment Management Module.

This module contains classes for managing Varroa mite treatment schedules and
efficacy parameters. Mite treatments are critical interventions that reduce
mite populations to prevent colony collapse from mite-induced mortality.

Classes:
    MiteTreatmentItem: Individual treatment schedule with efficacy parameters
    MiteTreatments: Collection manager for treatment schedules and active treatment lookup
"""

from dataclasses import dataclass
from datetime import datetime
from datetime import timedelta
from typing import List, Optional


@dataclass
class MiteTreatmentItem:
    """Individual mite treatment schedule with timing and efficacy.

    Represents a single miticide application with specified timing, duration, and
    efficacy. The treatment kills susceptible (non-resistant) mites at pct_mortality;
    resistant mites survive it. What share of the population is resistant is a property
    of the mite population, set by InitMitePctResistant and PctImmMitesResistant, not of
    the treatment.

    Attributes:
        start_time (datetime): Treatment application start date
        duration (int): Treatment duration in weeks
        pct_mortality (float): Mortality rate for susceptible mites (0-100%)
    """

    start_time: datetime
    duration: int  # in weeks
    pct_mortality: float  # percent mortality (0-100)
    # TODO: Need to change logic in rest of program to treat pct_mortality like a float (percentage)

    def is_valid(self) -> bool:
        return isinstance(self.start_time, datetime)


class MiteTreatments:
    """Collection manager for mite treatment schedules and active treatment lookup.

    Manages multiple mite treatment schedules and provides functionality to
    determine active treatments for any given date.

    Attributes:
        items (List[MiteTreatmentItem]): Collection of scheduled mite treatments
    """

    def __init__(self):
        self.items: List[MiteTreatmentItem] = []

    def add_item(self, item: MiteTreatmentItem):
        self.items.append(item)

    def add_item_by_values(
        self,
        start_time: datetime,
        duration: int,
        pct_mortality: float,
    ):
        item = MiteTreatmentItem(start_time, duration, pct_mortality)
        self.add_item(item)

    def get_item(self, index: int) -> Optional[MiteTreatmentItem]:
        if 0 <= index < len(self.items):
            return self.items[index]
        return None

    def get_item_by_date(self, date: datetime) -> Optional[MiteTreatmentItem]:
        for item in self.items:
            if item.start_time.date() == date.date():
                return item
        return None

    def get_active_item(self, date: datetime) -> Optional[MiteTreatmentItem]:
        for item in self.items:
            if (
                item.start_time
                <= date
                < item.start_time + timedelta(days=item.duration * 7)
            ):
                return item
        return None

    def is_new_treatment_starting(self, date: datetime) -> bool:
        return any(item.start_time.date() == date.date() for item in self.items)

    def delete_item(self, index: int):
        if 0 <= index < len(self.items):
            del self.items[index]

    def get_count(self) -> int:
        return len(self.items)

    def clear_all(self):
        self.items.clear()
