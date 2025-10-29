"""
Date Range Values Module for BeePop+ Environmental Simulation

This module provides temporal parameter management for the BeePop+ bee colony simulation.
It manages parameter values that vary over specific date ranges, supporting
time-dependent environmental conditions and management interventions.

The DateRangeValues system enables dynamic parameter changes throughout simulations,
allowing for seasonal variations, treatment schedules, and environmental events
that affect colony development over time.

Classes:
    DateRangeItem: Represents a single parameter value valid within a date range
    DateRangeValues: Collection manager for time-dependent parameter values
"""

from datetime import datetime
from typing import List, Optional


class DateRangeItem:
    """
    Single time-dependent parameter value for BeePop+ environmental simulation.

    Represents a parameter value that is valid within a specific date range,
    enabling temporal variations in environmental conditions, management
    practices, or other simulation parameters that change over time.

    Attributes:
        start_time (datetime): Beginning of the valid date range (inclusive)
        end_time (datetime): End of the valid date range (inclusive)
        value (float): Parameter value to apply during this date range
    """

    def __init__(self, start_time: datetime, end_time: datetime, value: float):
        self.start_time = start_time
        self.end_time = end_time
        self.value = value


class DateRangeValues:
    """
    Temporal parameter collection manager for BeePop+ environmental simulation.

    Manages collections of time-dependent parameter values that can change over
    specific date ranges during colony simulation. Supports environmental
    variations, treatment schedules, seasonal effects, and other temporal
    changes that affect bee colony development.

    The system implements exact C++ compatibility for date range calculations.

    Attributes:
        items (List[DateRangeItem]): Collection of date-ranged parameter values
        enabled (bool): Whether this parameter collection is active in simulation
        file_format_version (int): Deprecated
    """

    def __init__(self):
        self.items: List[DateRangeItem] = []
        self.enabled: bool = True
        self.file_format_version: int = 1

    def add_item(self, start_time: datetime, end_time: datetime, value: float):
        self.items.append(DateRangeItem(start_time, end_time, value))

    def get_item(self, index: int) -> Optional[DateRangeItem]:
        if 0 <= index < len(self.items):
            return self.items[index]
        return None

    def get_active_item(self, the_date: datetime) -> Optional[DateRangeItem]:
        """
        Find the first item where the_date falls within the date range.
        Implements the exact C++ logic from daterangevalues.cpp lines 67-98.
        """
        for item in self.items:
            # Normalize dates to midnight (matching C++ VAR_DATEVALUEONLY behavior)
            start_normalized = item.start_time.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            end_normalized = item.end_time.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            date_normalized = the_date.replace(
                hour=0, minute=0, second=0, microsecond=0
            )

            # Calculate time spans exactly like C++ COleDateTimeSpan
            time_since_start = date_normalized - start_normalized
            time_till_end = end_normalized - date_normalized

            # Convert to days (matching C++ GetDays() method)
            time_since_start_days = time_since_start.days
            time_till_end_days = time_till_end.days

            # Apply exact C++ logic: (TimeSinceStart.GetDays() > 0) && (TimeTillEnd.GetDays() > 0)
            if time_since_start_days > 0 and time_till_end_days > 0:
                return item

        return None

    def get_active_value(self, the_date: datetime) -> Optional[float]:
        item = self.get_active_item(the_date)
        return item.value if item else None

    def delete_item(self, index: int):
        if 0 <= index < len(self.items):
            del self.items[index]

    def get_count(self) -> int:
        return len(self.items)

    def clear_all(self):
        self.items.clear()

    def is_enabled(self) -> bool:
        return self.enabled

    def set_enabled(self, enable_val: bool):
        self.enabled = enable_val

    def set_file_format_version(self, version: int):
        self.file_format_version = version

    def copy(self, destination: "DateRangeValues"):
        destination.items = [
            DateRangeItem(item.start_time, item.end_time, item.value)
            for item in self.items
        ]
        destination.enabled = self.enabled
        destination.file_format_version = self.file_format_version
