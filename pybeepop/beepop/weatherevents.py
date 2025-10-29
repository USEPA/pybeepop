"""BeePop+ Weather Events Module.

This module contains classes for managing weather data and environmental conditions
that drive bee colony dynamics. Temperature, wind and rainfall thresholds determine
foraging conditions, while daylight hours affect egg laying and foraging patterns.

Classes:
    Event: Individual weather record with temperature, precipitation, and daylight data
    WeatherEvents: Collection manager for weather data with interpolation and analysis
"""

from datetime import datetime
import math
from pybeepop.beepop.globaloptions import GlobalOptions
from pybeepop.beepop.coldstoragesimulator import ColdStorageSimulator


def count_chars(in_str, test_char):
    """
    Port of free function CountChars(CString instg, TCHAR testchar).
    Returns the number of occurrences of test_char in in_str.
    """
    return in_str.count(test_char)


class Event:
    """Individual weather event representing daily environmental conditions.

    Represents a single day's weather data including temperature, precipitation,
    wind conditions.

    Attributes:
        time (datetime): Date and time for this weather event
        temp (float): Average daily temperature in Celsius
        max_temp (float): Maximum daily temperature in Celsius
        min_temp (float): Minimum daily temperature in Celsius
        windspeed (float): Wind speed in m/s
        rainfall (float): Precipitation amount in mm
        daylight_hours (float): Calculated daylight duration for this date/location
        forage_day (bool): Whether conditions allow foraging activity
        forage_inc (float): Foraging increment factor based on conditions
    """

    def __init__(
        self,
        time=None,
        temp=0.0,
        max_temp=0.0,
        min_temp=0.0,
        windspeed=0.0,
        rainfall=0.0,
        daylight_hours=0.0,
    ):
        self.time = time or datetime.now()
        self.temp = temp
        self.max_temp = max_temp
        self.min_temp = min_temp
        self.windspeed = windspeed
        self.rainfall = rainfall
        self.daylight_hours = daylight_hours
        self.forage_day = True
        self.forage_inc = 0.0

    @classmethod
    def copy_from(cls, other_event):
        """
        Port of CEvent copy constructor CEvent(CEvent& event).
        Creates a new Event as a copy of another Event.
        """
        new_event = cls()
        new_event.time = other_event.time
        new_event.temp = other_event.temp
        new_event.max_temp = other_event.max_temp
        new_event.min_temp = other_event.min_temp
        new_event.windspeed = other_event.windspeed
        new_event.rainfall = other_event.rainfall
        new_event.daylight_hours = other_event.daylight_hours
        new_event.forage_day = other_event.forage_day
        new_event.forage_inc = other_event.forage_inc
        return new_event

    def to_string(self):
        return (
            f"Date: {self.time.strftime('%m/%d/%Y')}\n Temp: {self.temp:.2f}\n MaxTemp: {self.max_temp:.2f}\n "
            f"MinTemp: {self.min_temp:.2f}\n Rainfall: {self.rainfall:.2f}\n DaylightHours: {self.daylight_hours:.2f}\n"
        )

    def update_forage_attribute_for_event(self, latitude, windspeed=None):
        """
        Port of CEvent::UpdateForageAttributeForEvent(double Latitude, double windSpeed).
        Compute the Forage and ForageInc attributes for this event.
        Forage day logic uses temperature, windspeed, and rainfall thresholds from global options.
        """
        windspeed = windspeed if windspeed is not None else self.get_windspeed()
        global_options = GlobalOptions.get()

        if global_options.should_forage_day_election_based_on_temperatures:
            self.forage_day = (
                self.get_max_temp() > 12.0
                and windspeed <= global_options.windspeed_threshold
                and self.get_max_temp() <= 43.33
                and self.get_rainfall() <= global_options.rainfall_threshold
            )
        else:
            self.forage_day = (
                windspeed <= global_options.windspeed_threshold
                and self.get_rainfall() <= global_options.rainfall_threshold
            )
        self.set_hourly_forage_inc(latitude)

    # Keep the old method name for backward compatibility
    def update_forage_attribute(self, latitude, windspeed=None, global_options=None):
        """Legacy method name for backward compatibility."""
        return self.update_forage_attribute_for_event(latitude, windspeed)

    def set_forage(self, forage):
        self.forage_day = forage

    def is_forage_day(self):
        """
        Check if this is a forage day (with cold storage override support if needed).
        Port of CEvent::IsForageDay().
        """
        forage_day = self.forage_day
        cold_storage = ColdStorageSimulator.get()
        if cold_storage.is_enabled():
            forage_day = cold_storage.is_forage_day(self)
        return forage_day

    def get_daylight_hours(self):
        return self.daylight_hours

    def get_forage_inc(self):
        """
        Get forage increment (with cold storage override support if needed).
        Port of CEvent::GetForageInc().
        """
        forage_inc = self.forage_inc
        cold_storage = ColdStorageSimulator.get()
        if cold_storage.is_enabled():
            forage_inc = cold_storage.get_forage_inc(self)
        return forage_inc

    def set_hourly_forage_inc(self, latitude):
        """
        Calculate the daylight hours for the longest day of the year at this latitude (solstice).
        Set forage_inc as a proportion of flying daylight hours to solstice daylight hours.
        """
        solstice = self.calc_daylight_from_latitude_doy(latitude, 182) + 1
        if solstice <= 0:
            self.set_forage_inc(0)
            return
        # Note: C++ tm_yday is 0-based, Python tm_yday is 1-based. Subtract 1 to match C++.
        todaylength = self.calc_daylight_from_latitude_doy(
            latitude, self.time.timetuple().tm_yday - 1
        )
        flightdaylength = self.calc_flight_daylight(todaylength)
        f_inc = min(flightdaylength / solstice, 1.0)
        self.set_forage_inc(f_inc)

    def set_forage_inc(self, value):
        self.forage_inc = value

    def calc_flight_daylight(
        self, daylength, min_temp_threshold=12.0, max_temp_threshold=43.0
    ):
        """
        Returns the number of hours this day that are in daylight and within the temperature thresholds.
        """
        sunrise = int(12 - (daylength / 2))
        sunset = int(sunrise + daylength)
        time_tmin = sunrise - 1
        time_tmax = 14
        tmax = self.get_max_temp()  # Use cold storage-aware getter
        tmin = self.get_min_temp()  # Use cold storage-aware getter
        flighthours = 0
        for i in range(time_tmin, sunset + 1):
            hr_temp = (tmax + tmin) / 2 - (
                (tmax - tmin)
                / 2
                * math.cos(math.pi * (i - time_tmin) / (time_tmax - time_tmin))
            )
            if min_temp_threshold < hr_temp < max_temp_threshold:
                flighthours += 1
        return float(flighthours)

    def calc_daylight_from_latitude_doy(self, lat, day_of_year):
        """
        Reference: CBM model in Ecological Modeling, volume 80 (1995) pp. 87-95.
        Lat is in degrees, limited to +/-65. Beyond that, day is either 24 or 0 hours.

        NOTE: Fixed to match C++ order of operations - the C++ code has:
        acos(numerator / cos(lat) * cos(psi)) not acos(numerator / (cos(lat) * cos(psi)))
        """
        if day_of_year > 366 or day_of_year < 1:
            return 0.0
        if lat < 0.0:
            lat = -lat
            day_of_year = (day_of_year + 182) % 365
        if lat > 65.0:
            lat = 65.0
        dl_coeff = 0.8333
        PI = 3.14159265358979  # Use C++ precision value
        theta = 0.2163108 + 2 * math.atan(
            0.9671396 * math.tan(0.0086 * (day_of_year - 186))
        )
        psi = math.asin(0.39795 * math.cos(theta))
        numerator = math.sin(
            (dl_coeff * PI / 180) + math.sin(lat * PI / 180) * math.sin(psi)
        )
        # Calculate daylight hours using C++ order of operations
        daylight_hours = 24 - (24 / PI) * math.acos(
            numerator / math.cos(lat * PI / 180) * math.cos(psi)
        )
        return daylight_hours

    def is_winter_day(self):
        """
        Port of CEvent::IsWinterDay().
        Uses cold storage-aware temperature getter.
        """
        return self.get_temp() < 18.0

    # Missing getters from C++ version
    def get_time(self):
        return self.time

    def get_temp(self):
        """
        Get temperature (with cold storage override support if needed).
        Port of CEvent::GetTemp().
        """
        event_temp = self.temp
        cold_storage = ColdStorageSimulator.get()
        if cold_storage.is_enabled():
            event_temp = cold_storage.get_temp(self)
        return event_temp

    def get_max_temp(self):
        """
        Get maximum temperature (with cold storage override support if needed).
        Port of CEvent::GetMaxTemp().
        """
        event_temp = self.max_temp
        cold_storage = ColdStorageSimulator.get()
        if cold_storage.is_enabled():
            event_temp = cold_storage.get_max_temp(self)
        return event_temp

    def get_min_temp(self):
        """
        Get minimum temperature (with cold storage override support if needed).
        Port of CEvent::GetMinTemp().
        """
        event_temp = self.min_temp
        cold_storage = ColdStorageSimulator.get()
        if cold_storage.is_enabled():
            event_temp = cold_storage.get_min_temp(self)
        return event_temp

    def get_rainfall(self):
        return self.rainfall

    def get_windspeed(self):
        return self.windspeed

    # Missing setters from C++ version
    def set_time(self, time):
        self.time = time

    def set_temp(self, temp):
        self.temp = temp

    def set_max_temp(self, max_temp):
        self.max_temp = max_temp

    def set_min_temp(self, min_temp):
        self.min_temp = min_temp

    def set_rainfall(self, rainfall):
        self.rainfall = rainfall

    def set_windspeed(self, windspeed):
        self.windspeed = windspeed

    def set_daylight_hours(self, hrs):
        self.daylight_hours = hrs

    def get_date_stg(self, format_str="%m/%d/%Y"):
        """
        Port of CEvent::GetDateStg(CString formatstg).
        Returns formatted date string.
        """
        return self.time.strftime(format_str)

    def parse_date(self, date_str):
        """
        Helper method to parse date string back to datetime.
        Not in C++ but useful for Python implementation.
        """
        try:
            return datetime.strptime(date_str, "%m/%d/%Y")
        except ValueError:
            return None

    def calc_today_daylight_from_latitude(self, lat):
        """
        Port of CEvent::CalcTodayDaylightFromLatitude(double Lat).
        Calculate daylight hours for this event's date.

        Note: C++ tm_yday is 0-based (0-365), Python tm_yday is 1-based (1-366).
        We subtract 1 to match C++ behavior. But note that this introduces a bug
        in the calc_daylight_from_latitude_doy method on January 1st. The bug is
        maintained for backward compatibility with the original C++ code, but a fix
        would be to remove the -1 and set Jan 1st as day 1. May also need leap year
        handling.
        """
        day_num = self.time.timetuple().tm_yday - 1
        return self.calc_daylight_from_latitude_doy(lat, day_num)

    def set_forage_inc_with_thresholds(self, t_thresh, t_max, t_ave):
        """
        Port of CEvent::SetForageInc(double TThresh, double TMax, double TAve).
        Calculates a measure of the amount of foraging for days having
        maximum temperatures close to the foraging threshold.
        """
        daytime_range = t_max - t_ave

        if daytime_range == 0:
            prop_threshold = 0
        else:
            prop_threshold = (t_thresh - t_ave) / daytime_range

        if t_max < t_thresh:
            self.forage_inc = 0.0
        elif 0.968 <= prop_threshold < 1:
            self.forage_inc = 0.25
        elif 0.866 <= prop_threshold < 0.968:
            self.forage_inc = 0.5
        elif 0.660 <= prop_threshold < 0.866:
            self.forage_inc = 0.75
        else:
            self.forage_inc = 1.0

    # Overloaded operators (Python equivalents)
    def __add__(self, other):
        """
        Port of CEvent::operator + (CEvent event).
        When adding events, increment rainfall, daylight hours; reset min and
        max temp if necessary; If either event is not a forage day, the sum is not a
        forage day.
        """
        result = Event()
        result.time = self.time  # Keep time as beginning of event
        result.rainfall = self.rainfall + other.rainfall
        result.daylight_hours = self.daylight_hours + other.daylight_hours
        result.max_temp = max(self.max_temp, other.max_temp)
        result.min_temp = min(self.min_temp, other.min_temp)
        result.forage_day = self.forage_day and other.forage_day
        result.forage_inc = self.forage_inc + other.forage_inc
        # Average the other fields
        result.temp = (self.temp + other.temp) / 2
        result.windspeed = (self.windspeed + other.windspeed) / 2
        return result

    def __iadd__(self, other):
        """
        Port of CEvent::operator += (CEvent event).
        """
        self.rainfall += other.rainfall
        self.daylight_hours += other.daylight_hours
        self.max_temp = max(self.max_temp, other.max_temp)
        self.min_temp = min(self.min_temp, other.min_temp)
        self.forage_day = self.forage_day and other.forage_day
        self.forage_inc += other.forage_inc
        return self


class WeatherEvents:
    """Collection manager for weather data driving colony simulation dynamics.

    Manages chronological weather events and provides environmental data access
    for colony simulation. Handles weather data interpolation, daylight calculations,
    foraging condition assessment, and seasonal pattern analysis.

    Integrates with colony simulation by providing daily environmental drivers
    that influence bee behavior, brood development, resource collection, and
    overwintering survival. Temperature thresholds determine foraging activity
    while daylight patterns drive circadian and seasonal behaviors.

    Attributes:
        filename (str): Source filename for weather data (informational)
        events (list): Chronological collection of Event objects
        has_been_initialized (bool): Whether weather data has been loaded
        latitude (float): Geographic latitude for daylight calculations (degrees)
        current_index (int): Current position for iteration through events
    """

    def __init__(self, latitude=30.0):
        self.filename = ""
        self.events = []
        self.has_been_initialized = False
        self.latitude = latitude
        self.current_index = 0  # For iteration support

    def clear_all_events(self):
        self.events.clear()
        self.has_been_initialized = False
        self.current_index = 0

    def add_event(self, event):
        self.events.append(event)
        self.has_been_initialized = True

    def remove_current_event(self):
        """
        Port of CWeatherEvents::RemoveCurrentEvent().
        Removes the event at current index.
        """
        if 0 <= self.current_index < len(self.events):
            del self.events[self.current_index]
            if self.current_index >= len(self.events) and self.events:
                self.current_index = len(self.events) - 1
            return True
        return False

    def get_total_events(self):
        return len(self.events)

    def set_file_name(self, fname):
        self.filename = fname

    def get_file_name(self):
        return self.filename

    def check_sanity(self):
        """
        Port of CWeatherEvents::CheckSanity().
        Basic validation method (implementation can be expanded as needed).
        """
        return 0  # 0 indicates no errors

    def set_latitude(self, lat):
        if lat != self.latitude:
            self.latitude = lat
            # Update all daylight hours and forage attributes for events based on updated latitude
            if self.events:
                for event in self.events:
                    event.daylight_hours = event.calc_today_daylight_from_latitude(
                        self.latitude
                    )
                    event.update_forage_attribute_for_event(
                        self.latitude, event.windspeed
                    )

    def get_latitude(self):
        return self.latitude

    def is_initialized(self):
        return self.has_been_initialized

    def set_initialized(self, val):
        self.has_been_initialized = val

    def go_to_first_event(self):
        """
        Port of CWeatherEvents::GoToFirstEvent().
        Sets current position to first event.
        """
        self.current_index = 0

    def get_first_event(self):
        """
        Port of CWeatherEvents::GetFirstEvent().
        Returns first event and sets position to iterate from there.
        """
        if self.events:
            self.current_index = 0
            return self.events[0]
        return None

    def get_next_event(self, current_index=None):
        """
        Port of CWeatherEvents::GetNextEvent().
        If current_index is provided, returns the next event after that index.
        If not provided, uses internal current_index and advances it.
        """
        if current_index is not None:
            if 0 <= current_index + 1 < len(self.events):
                return self.events[current_index + 1]
            return None
        else:
            # Use internal index and advance
            self.current_index += 1
            if 0 <= self.current_index < len(self.events):
                return self.events[self.current_index]
            return None

    def get_current_time(self, current_index=None):
        """
        Port of CWeatherEvents::GetCurrentTime().
        Returns the time of the current event.
        """
        index = current_index if current_index is not None else self.current_index
        if 0 <= index < len(self.events):
            return self.events[index].time
        return None

    def get_day_event(self, the_time):
        """
        Port of CWeatherEvents::GetDayEvent(COleDateTime theTime).
        Finds and returns event matching the given date.
        IMPORTANT: This method sets the current_index to the found event's position,
        so subsequent calls to get_next_event() will advance from this position.
        """
        old_position = self.current_index
        self.go_to_first_event()
        for i, event in enumerate(self.events):
            if event.time.date() == the_time.date():
                self.current_index = i
                return event
        # If no match found, restore old position
        self.current_index = old_position
        return None

    def get_beginning_time(self):
        return self.events[0].time if self.events else None

    def get_ending_time(self):
        return self.events[-1].time if self.events else None
