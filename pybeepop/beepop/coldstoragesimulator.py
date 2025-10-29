"""
ColdStorageSimulator class:
- Simulates cold storage conditions for a bee colony.
- Can be activated manually or by specifying start/end dates.
- When active, overrides temperature and disables foraging.
- Tracks active, starting, and ending phases.
- All logic and comments from the C++ version are preserved.
"""

from datetime import datetime


class ColdStorageSimulator:
    DEFAULT_TEMPERATURE = (40.0 - 32.0) / 1.8  # Celsius
    _instance = None

    def __init__(self):
        self.enabled = False
        self.start_date = None
        self.end_date = None
        self.on = False
        self.temperature = self.DEFAULT_TEMPERATURE
        self.start_date_str = ""
        self.end_date_str = ""
        self.is_active = False
        self.is_starting = False
        self.is_ending = False

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = ColdStorageSimulator()
        return cls._instance

    def set_enabled(self, enabled):
        self.enabled = enabled

    def is_enabled(self):
        return self.enabled

    def activate(self):
        self.on = True

    def deactivate(self):
        self.on = False

    def is_on(self):
        return self.on

    def is_automatic(self):
        return not self.start_date_str and not self.end_date_str

    def get_temp(self, event):
        temperature = getattr(event, "temp", None)
        if self.is_active:
            temperature = self.temperature
        return temperature

    def get_max_temp(self, event):
        temperature = getattr(event, "max_temp", None)
        if self.is_active:
            temperature = self.temperature
        return temperature

    def get_min_temp(self, event):
        temperature = getattr(event, "min_temp", None)
        if self.is_active:
            temperature = self.temperature
        return temperature

    def get_forage_inc(self, event):
        forage_inc = getattr(event, "forage_inc", None)
        if self.is_active:
            forage_inc = 0.0
        return forage_inc

    def is_forage_day(self, event):
        forage_day = getattr(event, "forage_day", None)
        if self.is_active:
            forage_day = False
        return forage_day

    def set_start_date(self, start_date):
        self.start_date = start_date
        self.start_date_str = start_date.strftime("%m%d") if start_date else ""

    def set_end_date(self, end_date):
        self.end_date = end_date
        self.end_date_str = end_date.strftime("%m%d") if end_date else ""

    def update(self, event, colony):
        """
        Updates the state of the cold storage, call once per simulation day.
        Tracks starting/ending phases based on colony and event state.
        """
        is_active = self.enabled and (self.on or self.is_cold_storage_period(event))
        if not self.is_active and is_active:
            self.is_starting = True
        # Starting phase: bees placed in cold storage, brood still present
        if self.is_starting:
            starting = (
                getattr(colony.queen, "teggs", 0) > 0
                or getattr(colony, "cap_drn", None)
                and getattr(colony.cap_drn, "quantity", 0) > 0
                or getattr(colony, "cap_wkr", None)
                and getattr(colony.cap_wkr, "quantity", 0) > 0
            )
            self.is_starting = starting
        # Ending phase: queen starts to lay eggs again while in cold storage
        if is_active and not self.is_starting and getattr(colony.queen, "teggs", 0) > 0:
            self.is_ending = True
        if not is_active:
            self.is_starting = False
            self.is_ending = False
        self.is_active = is_active

    def reset(self):
        self.enabled = False
        self.start_date = None
        self.end_date = None
        self.on = False
        self.temperature = self.DEFAULT_TEMPERATURE
        self.start_date_str = ""
        self.end_date_str = ""
        self.is_active = False
        self.is_starting = False
        self.is_ending = False

    def is_active_now(self):
        return self.is_active

    def is_starting_now(self):
        return self.is_active and self.is_starting

    def is_ending_now(self):
        return self.is_active and self.is_ending

    def is_cold_storage_period(self, event):
        """
        Returns True if the current event is within the cold storage period.
        """
        if not self.start_date_str or not self.end_date_str:
            return False
        current_date_str = event.time.strftime("%m%d") if hasattr(event, "time") else ""
        if self.start_date_str >= self.end_date_str:
            return (
                current_date_str >= self.start_date_str
                or current_date_str <= self.end_date_str
            )
        else:
            return self.start_date_str <= current_date_str <= self.end_date_str
