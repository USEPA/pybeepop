"""BeePop+ Session Management Module.

This module contains the VarroaPopSession class, which serves as the central
coordinator for BeePop+ simulations. It manages the simulation state, coordinates
major objects (colony, weather, treatments), handles results output, and provides
error/information reporting capabilities.

The VarroaPopSession class is a Python port of the C++ CVarroaPopSession class
and maintains compatibility with the original API while adding Python-specific
enhancements.

Architecture:
    VarroaPopSession acts as the main controller that coordinates:

    VarroaPopSession (Central Controller)
    ├── Colony (Bee population dynamics)
    ├── WeatherEvents (Environmental conditions)
    ├── Results Management
    │   ├── Output formatting
    │   ├── Header generation
    │   └── Data collection
    ├── Treatment Protocols
    │   ├── Mite treatments
    │   ├── Spore treatments
    │   └── Comb removal
    ├── Immigration Events
    │   ├── Mite immigration
    │   └── Schedule management
    ├── Requeening Events
    │   ├── Queen replacement
    │   └── Colony recovery
    └── Error/Information Reporting
        ├── Error tracking
        ├── Warning management
        └── Status reporting

Key Features:
    - Centralized simulation state management
    - Results formatting and output coordination
    - Weather event integration
    - Treatment protocol scheduling
    - Error and warning tracking
    - Immigration and requeening event management

"""

import math
from datetime import timedelta
import datetime
from pybeepop.beepop.colony import Colony
from pybeepop.beepop.weatherevents import WeatherEvents
from pybeepop.beepop.mite import Mite


class VarroaPopSession:
    """Central session manager for BeePop+ simulations.

    This class serves as the main coordinator for BeePop+ simulations, managing
    the simulation state, coordinating major simulation objects, handling results
    output, and providing comprehensive error and information reporting.

    The VarroaPopSession maintains the simulation timeline, manages colony and
    weather interactions, coordinates treatment protocols, and formats output
    data for analysis. It serves as a Python port of the C++ CVarroaPopSession.

    """

    def set_default_headers(self):
        """
        Sets the default header strings for output/plotting, matching the C++ results header logic.
        """
        self.results_header = [
            "Date",
            "ColSze",
            "AdDrns",
            "AdWkrs",
            "Forgr",
            "DrnBrd",
            "WkrBrd",
            "DrnLrv",
            "WkrLrv",
            "DrnEggs",
            "WkrEggs",
            "TotalEggs",
            "DD",
            "L",
            "N",
            "P",
            "dd",
            "l",
            "n",
            "FreeMts",
            "DBrdMts",
            "WBrdMts",
            "Mts/DBrd",
            "Mts/WBrd",
            "Mts Dying",
            "PropMts Dying",
            "ColPollen(g)",
            "PPestConc(ug/g)",
            "ColNectar(g)",
            "NPestConc(ug/g)",
            "Dead DLarv",
            "Dead WLarv",
            "Dead DAdults",
            "Dead WAdults",
            "Dead Foragers",
            "Queen Strength",
            "Temp (DegC)",
            "Precip",
            "Min Temp (C)",
            "Max Temp (C)",
            "Daylight hours",
            "Forage Inc",
            "Forage Day",
        ]
        self.results_file_header = list(self.results_header)
        # Add additional headers if needed for file output

    def __init__(self):
        """Initialize a new VarroaPopSession.

        Creates a new simulation session with default settings, initializes
        the colony and weather objects, sets up results tracking, and
        configures all treatment and event management systems.

        The session is initialized with conservative default values for all
        parameters and empty data structures for results collection.

        Raises:
            RuntimeError: If colony or weather initialization fails.

        Note:
            After initialization, the session requires additional configuration
            (dates, latitude, initial conditions) before running simulations.
        """
        # Output/Plotting Attributes
        self.results_header = []
        self.results_file_header = []
        self.results_text = []
        self.results_file_text = []
        self.disp_weekly_data = False
        # Options Selection
        self.col_titles = True
        self.init_conds = False
        self.version = True
        self.weather_colony = False
        self.field_delimiter = 0
        self.disp_frequency = 1
        # Error/Status
        self.error_list = []
        self.information_list = []
        self._enable_error_reporting = True
        self._enable_info_reporting = True
        # Simulation Data
        self.sim_start_time = None
        self.sim_end_time = None
        self.simulation_complete = False
        self.results_ready = False
        # Immigration Data
        self.immigration_type = "None"
        self.tot_immigrating_mites = 0
        self.inc_immigrating_mites = 0
        self.cum_immigrating_mites = 0
        self.imm_mite_pct_resistant = 0.0
        # Use sentinel date (1999-01-01) to match C++ behavior when dates are not set
        self.immigration_start_date = datetime.datetime(1999, 1, 1)
        self.immigration_end_date = datetime.datetime(1999, 1, 1)
        self.immigration_enabled = False
        self.imm_enabled = False  # ImmEnabled parameter
        # Re-Queening Data
        self.rq_egg_laying_delay = 10  # RQEggLayDelay parameter
        self.rq_wkr_drn_ratio = 0.0
        self.rq_enable_requeen = False
        self.rq_scheduled = 1
        self.rq_queen_strength = 5.0
        self.rq_once = 0
        self.rq_requeen_date = None
        # Varroa Miticide Treatment Data
        self.init_mite_pct_resistant = 0.0
        self.vt_enable = False
        # Varroa Spore Treatment Data
        self.sp_enable = False
        self.sp_treatment_start = None
        self.sp_initial = 0
        self.mort10 = 0.0
        self.mort25 = 0.0
        self.mort50 = 0.0
        self.mort75 = 0.0
        self.mort90 = 0.0
        # Comb Removal
        self.comb_remove_date = None
        self.comb_remove_enable = False
        self.comb_remove_pct = 0.0
        # EPA Mortality
        self.ied_enable = False
        self.results_file_format_stg = ""

        # Initialize main objects (matching C++ session constructor)
        # Create the colony object (equivalent to CColony theColony)
        self.colony = Colony(session=self)

        # Set session reference in colony (matching theColony.SetSession(this))
        if hasattr(self.colony, "set_session"):
            self.colony.set_session(self)

        # Create the weather events object (equivalent to new CWeatherEvents)
        self.weather = WeatherEvents()
        self.first_result_entry = True
        self.weather_loaded = False
        self.show_warnings = (
            False  # Not appropriate to show warnings for library version
        )

    # Main object accessors (matching C++ GetColony() and GetWeather())
    def get_colony(self):
        """Get the colony object (equivalent to C++ GetColony())."""
        return self.colony

    def get_weather(self):
        """Get the weather events object (equivalent to C++ GetWeather())."""
        return self.weather

    def set_latitude(self, lat):
        """Set the latitude for weather calculations."""
        if self.weather is not None:
            if hasattr(self.weather, "set_latitude"):
                self.weather.set_latitude(lat)

    def get_latitude(self):
        """Get the current latitude setting."""
        if self.weather is not None and hasattr(self.weather, "get_latitude"):
            return self.weather.get_latitude()
        return 30.0  # Default latitude

    def is_weather_loaded(self):
        """Check if weather data has been loaded."""
        return self.weather_loaded

    def set_weather_loaded(self, load_complete):
        """Set the weather loaded status."""
        self.weather_loaded = load_complete

    def is_show_warnings(self):
        """Check if warnings should be shown."""
        return self.show_warnings

    def set_show_warnings(self, warn):
        """Set whether warnings should be shown."""
        self.show_warnings = warn

    # Error/Status list access
    def clear_error_list(self):
        self.error_list.clear()

    def clear_info_list(self):
        self.information_list.clear()

    def add_to_error_list(self, err_stg):
        self.error_list.append(err_stg)

    def add_to_info_list(self, info_stg):
        self.information_list.append(info_stg)

    def get_error_list(self):
        return self.error_list

    def get_info_list(self):
        return self.information_list

    def is_error_reporting_enabled(self):
        return self._enable_error_reporting

    def is_info_reporting_enabled(self):
        return self._enable_info_reporting

    def enable_error_reporting(self, enable):
        self._enable_error_reporting = bool(enable)

    def enable_info_reporting(self, enable):
        self._enable_info_reporting = bool(enable)

    # Simulation Operations
    def get_sim_start(self):
        return self.sim_start_time

    def get_sim_end(self):
        return self.sim_end_time

    def set_sim_start(self, start):
        self.sim_start_time = start
        # Mark that simulation dates were explicitly set
        self._sim_dates_explicitly_set = True

    def set_sim_end(self, end):
        self.sim_end_time = end
        # Mark that simulation dates were explicitly set
        self._sim_dates_explicitly_set = True

    def get_sim_days(self):
        if self.sim_start_time and self.sim_end_time:
            return (self.sim_end_time - self.sim_start_time).days + 1
        return 0

    def get_sim_day_number(self, the_date):
        if self.sim_start_time:
            return (the_date - self.sim_start_time).days + 1
        return 0

    def get_sim_date(self, day_num):
        if self.sim_start_time:
            return self.sim_start_time + timedelta(days=day_num)
        return None

    def ready_to_simulate(self):
        return (
            self.colony
            and self.colony.is_initialized()
            and self.weather
            and self.weather.is_initialized()
        )

    def is_simulation_complete(self):
        return self.simulation_complete

    def are_results_ready(self):
        return self.results_ready

    def get_results_length(self):
        return len(self.results_text)

    def date_in_range(self, start_range, stop_range, the_time):
        """
        Helper function to check if a date falls within a range.
        Matches C++ DateInRange function.
        """
        return (the_time >= start_range) and (the_time <= stop_range)

    def check_date_consistency(self, show_warning=True):
        """
        Checks Dates for Immigration, Varroa Treatment and Re-Queening to verify
        they fall inside the Simulation range. If not, a warning message is displayed
        and the user is given the opportunity to continue or quit the simulation.

        Return value: True if simulation should continue, False otherwise. User can
        override consistency check and continue from warning message box. Otherwise,
        inconsistent times will return false.

        Ported from C++ CheckDateConsistency function.
        """
        consistent = True
        if show_warning:  # we only check if show_warnings is on. Is this intended?
            warn_strings = []

            # Check Re-Queening dates if enabled
            if (
                hasattr(self, "rq_enable_requeen")
                and self.rq_enable_requeen
                and hasattr(self, "rq_requeen_date")
                and self.rq_requeen_date
            ):
                if not self.date_in_range(
                    self.sim_start_time, self.sim_end_time, self.rq_requeen_date
                ):
                    warn_strings.append("     ReQueening")
                    consistent = False

            # Check Immigration dates if enabled
            if self.immigration_enabled:
                # Check immigration start date
                if self.immigration_start_date and not self.date_in_range(
                    self.sim_start_time, self.sim_end_time, self.immigration_start_date
                ):
                    warn_strings.append("     Immigration Start")
                    consistent = False

                # Check immigration end date
                if self.immigration_end_date and not self.date_in_range(
                    self.sim_start_time, self.sim_end_time, self.immigration_end_date
                ):
                    warn_strings.append("     Immigration End")
                    consistent = False

            # Display warnings if enabled and inconsistencies found
            if show_warning and not consistent:
                warn_message = (
                    "Date consistency check failed. The following dates are outside simulation range:\n"
                    + "\n".join(warn_strings)
                )
                self.add_to_error_list(warn_message)
                # In C++, this would show a dialog for user override
                # For Python, we'll just log the error and return False

        return consistent

    def simulate(self):
        """
        Main simulation loop. Coordinates colony, weather, immigration, treatments, and results.
        Ported from C++ Simulate, preserving logic and comments.
        """
        if not self.ready_to_simulate():
            self.add_to_error_list(
                "Simulation not ready: colony or weather not initialized."
            )
            return

        # Check date consistency before starting simulation (matches C++ behavior)
        if not self.check_date_consistency(self.show_warnings):
            return

        # Set results frequency
        res_freq = 7 if self.disp_weekly_data else 1

        # Format string setup (simplified for Python)
        delimiter = " "
        if self.field_delimiter == 1:
            delimiter = ","
        elif self.field_delimiter == 2:
            delimiter = "\t"

        # Initialize results headers
        self.set_default_headers()
        self.results_text.clear()
        self.results_file_text.clear()

        # Add header rows (simplified)
        self.results_text.append(" ".join(self.results_header))

        # Generate Initial row showing exact initial conditions (like C++ version)
        initial_row = self._generate_initial_conditions_row()
        self.results_text.append(initial_row)

        # Get simulation start and end
        sim_start = self.get_sim_start()
        sim_days = self.get_sim_days()
        day_count = 1
        tot_foraging_days = 0

        # Get first event from weather
        event = self.weather.get_day_event(sim_start)

        # Main simulation loop
        while event is not None and day_count <= sim_days:
            # Requeening logic
            self.colony.requeen_if_needed(
                day_count,
                event,
                self.rq_egg_laying_delay,
                self.rq_wkr_drn_ratio,
                self.rq_enable_requeen,
                self.rq_scheduled,
                self.rq_queen_strength,
                self.rq_once,
                self.rq_requeen_date,
            )

            # Update bees
            self.colony.update_bees(event, day_count)

            # Immigration
            if self.is_immigration_enabled() and self.is_immigration_window(event):
                imm_mites_dict = self.get_immigration_mites(event)
                # Convert dict to Mite object for colony.add_mites()
                imm_mites = Mite(
                    imm_mites_dict["resistant"], imm_mites_dict["non_resistant"]
                )
                self.inc_immigrating_mites = imm_mites
                self.colony.add_mites(imm_mites)
            else:
                self.inc_immigrating_mites = 0

            # Update mites
            self.colony.update_mites(event, day_count)

            # Comb removal
            if (
                self.comb_remove_enable
                and event.time.year == self.comb_remove_date.year
                and event.time.month == self.comb_remove_date.month
                and event.time.day == self.comb_remove_date.day
            ):
                self.colony.remove_drone_comb(self.comb_remove_pct)

            # Pending events
            self.colony.do_pending_events(event, day_count)

            # Results output
            if day_count % res_freq == 0:
                # Collect results for the day using C++ compatible formatting
                result_row = [
                    event.time.strftime("%m/%d/%Y"),  # "%s"
                    "%6d" % self.colony.get_colony_size(),  # "%6d"
                    "%8d" % self.colony.get_adult_drones(),  # "%8d"
                    "%8d" % self.colony.get_adult_workers(),  # "%8d"
                    "%8d" % self.colony.get_foragers(),  # "%8d"
                    "%8d" % self.colony.get_active_foragers(),  # "%8d"
                    "%7d" % self.colony.get_drone_brood(),  # "%7d"
                    "%6d" % self.colony.get_worker_brood(),  # "%6d"
                    "%6d" % self.colony.get_drone_larvae(),  # "%6d"
                    "%6d" % self.colony.get_worker_larvae(),  # "%6d"
                    "%6d" % self.colony.get_drone_eggs(),  # "%6d"
                    "%6d" % self.colony.get_worker_eggs(),  # "%6d"
                    "%6d" % self.colony.get_total_eggs_laid_today(),  # "%6d"
                    "%7.2f" % self.colony.get_dd_today(),  # "%7.2f"
                    "%6.2f" % self.colony.get_l_today(),  # "%6.2f"
                    "%6.2f" % self.colony.get_n_today(),  # "%6.2f"
                    "%8.2f" % self.colony.get_p_today(),  # "%8.2f"
                    "%7.2f" % self.colony.get_dd_lower(),  # "%7.2f"
                    "%6.2f" % self.colony.get_l_lower(),  # "%6.2f"
                    "%8.2f" % self.colony.get_n_lower(),  # "%8.2f"
                    "%6.2f" % self.colony.get_free_mites(),  # "%6.2f"
                    "%6.2f" % self.colony.get_drone_brood_mites(),  # "%6.2f"
                    "%6.2f" % self.colony.get_worker_brood_mites(),  # "%6.2f"
                    "%6.2f" % self.colony.get_mites_per_drone_brood(),  # "%6.2f"
                    "%6.2f" % self.colony.get_mites_per_worker_brood(),  # "%6.2f"
                    "%6.0f" % self.colony.get_mites_dying_this_period(),  # "%6.0f"
                    "%6.2f"
                    % self.colony.get_prop_mites_dying(),  # "%6.2f" - changed from c++ code which uses 0 decimal places
                    "%8.1f" % self.colony.get_col_pollen(),  # "%8.1f"
                    "%7.4f" % self.colony.get_pollen_pest_conc(),  # "%7.4f"
                    "%8.1f" % self.colony.get_col_nectar(),  # "%8.1f"
                    "%7.4f" % self.colony.get_nectar_pest_conc(),  # "%7.4f"
                    "%6d"
                    % self.colony.get_dead_drone_larvae_pesticide(),  # "%6d" - FIXED: Use pesticide-specific deaths
                    "%6d"
                    % self.colony.get_dead_worker_larvae_pesticide(),  # "%6d" - FIXED: Use pesticide-specific deaths
                    "%6d"
                    % self.colony.get_dead_drone_adults_pesticide(),  # "%6d" - FIXED: Use pesticide-specific deaths
                    "%6d"
                    % self.colony.get_dead_worker_adults_pesticide(),  # "%6d" - FIXED: Use pesticide-specific deaths
                    "%6d"
                    % self.colony.get_dead_foragers_pesticide(),  # "%6d" - FIXED: Use pesticide-specific deaths
                    "%8.3f" % self.colony.get_queen_strength(),  # "%8.3f"
                    "%8.3f" % event.temp,  # "%8.3f"
                    "%6.3f" % event.rainfall,  # "%6.3f"
                    "%8.3f" % event.min_temp,  # "%8.3f"
                    "%8.3f" % event.max_temp,  # "%8.3f"
                    "%8.2f"
                    % event.daylight_hours,  # "%8.2f" - KEY FORMATTING FOR DAYLIGHT HOURS
                    "%8.2f" % event.forage_inc,  # "%8.2f"
                    "Yes" if event.is_forage_day() else "No",  # "%s"
                ]
                self.results_text.append(delimiter.join(result_row))

            if day_count % res_freq == 0:
                self.colony.set_start_sample_period()

            day_count += 1
            if getattr(event, "is_forage_day", False):
                tot_foraging_days += 1
            event = self.weather.get_next_event()

        self.results_ready = True
        self.simulation_complete = True
        self.colony.clear()
        self.simulation_complete = False

    # Immigration Operations
    def set_immigration_type(self, im_type):
        self.immigration_type = im_type

    def get_immigration_type(self):
        return self.immigration_type

    def set_num_immigration_mites(self, mites):
        # Store total mites (matching C++ logic where m_TotImmigratingMites.GetTotal() returns total)
        self.tot_immigrating_mites = mites

    def get_num_immigration_mites(self):
        return self.tot_immigrating_mites

    def set_immigration_start(self, start):
        self.immigration_start_date = start

    def get_immigration_start(self):
        return self.immigration_start_date

    def set_immigration_end(self, end):
        self.immigration_end_date = end

    def get_immigration_end(self):
        return self.immigration_end_date

    def set_immigration_enabled(self, enabled):
        self.immigration_enabled = enabled

    def is_immigration_enabled(self):
        return self.immigration_enabled

    def is_immigration_window(self, event):
        today = event.time
        # Match C++ logic: (today >= m_ImmigrationStartDate) && (today <= m_ImmigrationEndDate)
        return (
            today >= self.immigration_start_date and today <= self.immigration_end_date
        )

    def get_immigration_mites(self, event):
        """
        Returns the number of immigration mites for a given event (date and colony count), supporting all immigration models.
        Ported from C++ GetImmigrationMites.

        This routine calculates the number of mites to immigrate on the
            specified date.  It also keeps track of the cumulative number of
            mites that have migrated so far.  First calculate the total quantity
            of immigrating mites then return a CMite based on percent resistance to miticide

                The equations of immigration were derived by identifying the desired function,
                e.g. f(x) = A*Cos(x), then calculating the constants by setting the integral of
                the function (over the range 0..1) to 1.  This means that the area under the
                curve is = 1.  This ensures that 100% of m_TotImmigratingMites were added to the
                colony.  With the constants were established, a very simple numerical integration
                is performed using sum(f(x)*DeltaX) for each day of immigration.

                The immigration functions are:

                        Cosine -> f(x) = 1.188395*cos(x)

                        Sine -> f(x) = 1.57078*sin(PI*x)

                        Tangent -> f(x) = 2.648784*tan(1.5*x)

                        Exponential -> f(x) = (1.0/(e-2))*(exp(1 - (x)) - 1.0)

                        Logarithmic -> f(x) = -1.0*log(x)  day #2 and on

                        Polynomial -> f(x) = 3.0*(x) - 1.5*(x*x)

                In the case of Logarithmic, since there is an infinity at x=0, the
                actual value of the integral over the range (0..DeltaX) is used on the first
                day.

                Mites only immigrate on foraging days.

        Args:
            event: An object with 'time' (datetime), 'num_colonies' (int), and 'is_forage_day' (bool) attributes.
        Returns:
            dict: {'resistant': float, 'non_resistant': float} number of immigration mites for the event's day.
        """

        # Immigration only occurs if enabled, on foraging days, and within the window
        if not getattr(self, "immigration_enabled", False):
            return {"resistant": 0, "non_resistant": 0}
        the_date = event.time
        # Check immigration window (matches C++ logic: today >= start AND today <= end)
        if not (
            the_date >= self.immigration_start_date
            and the_date <= self.immigration_end_date
        ):
            return {"resistant": 0, "non_resistant": 0}
        if not getattr(event, "is_forage_day", lambda: True)():
            return {"resistant": 0, "non_resistant": 0}

        sim_day_today = (the_date - self.sim_start_time).days + 1
        sim_day_im_start = (self.immigration_start_date - self.sim_start_time).days + 1
        sim_day_im_stop = (self.immigration_end_date - self.sim_start_time).days + 1

        # Set cumulative immigration to 0 on first day
        if sim_day_today == sim_day_im_start:
            self.cum_immigrating_mites = 0

        # Calculate proportion of days into immigration
        im_prop = float(sim_day_today - sim_day_im_start) / float(
            1 + sim_day_im_stop - sim_day_im_start
        )
        delta_x = 1.0 / (sim_day_im_stop - sim_day_im_start + 1)
        x = im_prop + delta_x / 2

        immigration_type = str(self.immigration_type).upper()
        total_mites = 0.0
        A = self.get_num_immigration_mites()  # Total mites to distribute

        if immigration_type == "NONE":
            total_mites = 0.0
        elif immigration_type == "COSINE":
            total_mites = A * 1.188395 * math.cos(x) * delta_x
        elif immigration_type == "EXPONENTIAL":
            total_mites = (
                A * (1.0 / (math.exp(1.0) - 2)) * (math.exp(1.0 - x) - 1.0) * delta_x
            )
        elif immigration_type == "LOGARITHMIC":
            if im_prop == 0:
                total_mites = A * (-1.0 * delta_x * math.log(delta_x) - delta_x)
            else:
                total_mites = A * (-1.0 * math.log(x) * delta_x)
        elif immigration_type == "POLYNOMIAL":
            total_mites = A * (3.0 * x - 1.5 * (x * x)) * delta_x
        elif immigration_type == "SINE":
            total_mites = A * 1.57078 * math.sin(math.pi * x) * delta_x
        elif immigration_type == "TANGENT":
            total_mites = A * 2.648784 * math.tan(1.5 * x) * delta_x
        else:
            total_mites = 0.0

        if total_mites < 0.0:
            total_mites = 0.0

        resistant = total_mites * self.imm_mite_pct_resistant / 100.0
        non_resistant = total_mites - resistant
        self.cum_immigrating_mites += resistant + non_resistant
        return {"resistant": resistant, "non_resistant": non_resistant}

    # Implementation
    def update_colony_parameters(self, param_name, param_value):
        """
        Updates colony parameters based on the provided name and value.
        Ported from C++ UpdateColonyParameters, with pythonic improvements.
        Args:
            param_name (str): The name of the parameter to update.
            param_value (str): The value to set for the parameter.
        Returns:
            bool: True if the parameter was updated, False otherwise.
        """

        name = param_name.strip().lower()
        value = param_value.strip()

        def parse_bool(val):
            return str(val).lower() in ("1", "true", "yes")

        def parse_date(val):
            try:
                return datetime.datetime.strptime(val, "%m/%d/%Y")
            except Exception:
                return None

        # Session parameters
        if name == "simstart":
            dt = parse_date(value)
            if dt:
                self.set_sim_start(dt)
                return True
            self.add_to_error_list(f"Invalid simstart date: {value}")
            return False
        if name == "simend":
            dt = parse_date(value)
            if dt:
                self.set_sim_end(dt)
                return True
            self.add_to_error_list(f"Invalid simend date: {value}")
            return False
        if name == "latitude":
            try:
                self.latitude = float(value)
                if self.weather and hasattr(self.weather, "set_latitude"):
                    self.weather.set_latitude(self.latitude)
                return True
            except Exception:
                self.add_to_error_list(f"Invalid latitude: {value}")
                return False

        # Initial Conditions parameters (IC) - Store directly in colony.m_init_cond
        if name == "icdroneadults":
            if self.colony and hasattr(self.colony, "m_init_cond"):
                try:
                    self.colony.m_init_cond.m_droneAdultsField = int(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid icdroneadults: {value}")
                    return False
        if name == "icworkeradults":
            if self.colony and hasattr(self.colony, "m_init_cond"):
                try:
                    self.colony.m_init_cond.m_workerAdultsField = int(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid icworkeradults: {value}")
                    return False
        if name == "icdronebrood":
            if self.colony and hasattr(self.colony, "m_init_cond"):
                try:
                    self.colony.m_init_cond.m_droneBroodField = int(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid icdronebrood: {value}")
                    return False
        if name == "icworkerbrood":
            if self.colony and hasattr(self.colony, "m_init_cond"):
                try:
                    self.colony.m_init_cond.m_workerBroodField = int(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid icworkerbrood: {value}")
                    return False
        if name == "icdronelarvae":
            if self.colony and hasattr(self.colony, "m_init_cond"):
                try:
                    self.colony.m_init_cond.m_droneLarvaeField = int(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid icdronelarvae: {value}")
                    return False
        if name == "icworkerlarvae":
            if self.colony and hasattr(self.colony, "m_init_cond"):
                try:
                    self.colony.m_init_cond.m_workerLarvaeField = int(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid icworkerlarvae: {value}")
                    return False
        if name == "icdroneeggs":
            if self.colony and hasattr(self.colony, "m_init_cond"):
                try:
                    self.colony.m_init_cond.m_droneEggsField = int(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid icdroneeggs: {value}")
                    return False
        if name == "icworkereggs":
            if self.colony and hasattr(self.colony, "m_init_cond"):
                try:
                    self.colony.m_init_cond.m_workerEggsField = int(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid icworkereggs: {value}")
                    return False
        if name == "icqueenstrength":
            if self.colony and hasattr(self.colony, "m_init_cond"):
                try:
                    self.colony.m_init_cond.m_QueenStrength = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid icqueenstrength: {value}")
                    return False
        if name == "icforagerlifespan":
            if self.colony and hasattr(self.colony, "m_init_cond"):
                try:
                    self.colony.m_init_cond.m_ForagerLifespan = int(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid icforagerlifespan: {value}")
                    return False

        # Handle common parameter name variations (for user convenience)
        if name == "queenstrength":
            return self.update_colony_parameters("icqueenstrength", value)
        if name == "foragerlifespan":
            return self.update_colony_parameters("icforagerlifespan", value)
        if name == "workeradults":
            return self.update_colony_parameters("icworkeradults", value)
        if name == "workerbrood":
            return self.update_colony_parameters("icworkerbrood", value)
        if name == "workereggs":
            return self.update_colony_parameters("icworkereggs", value)
        if name == "workerlarvae":
            return self.update_colony_parameters("icworkerlarvae", value)
        if name == "droneadults":
            return self.update_colony_parameters("icdroneadults", value)
        if name == "dronebrood":
            return self.update_colony_parameters("icdronebrood", value)
        if name == "droneeggs":
            return self.update_colony_parameters("icdroneeggs", value)
        if name == "dronelarvae":
            return self.update_colony_parameters("icdronelarvae", value)

        # Mite Parameters (ICDroneAdultInfest, etc.) - Following C++ session.cpp pattern
        if name == "icdroneadultinfest":
            if self.colony and hasattr(self.colony, "m_init_cond"):
                try:
                    self.colony.m_init_cond.m_droneAdultInfestField = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid icdroneadultinfest: {value}")
                    return False
        if name == "icdronebroodinfest":
            if self.colony and hasattr(self.colony, "m_init_cond"):
                try:
                    self.colony.m_init_cond.m_droneBroodInfestField = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid icdronebroodinfest: {value}")
                    return False
        if name == "icdronemiteoffspring":
            if self.colony and hasattr(self.colony, "m_init_cond"):
                try:
                    self.colony.m_init_cond.m_droneMiteOffspringField = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid icdronemiteoffspring: {value}")
                    return False
        if name == "icdronemitesurvivorship":
            if self.colony and hasattr(self.colony, "m_init_cond"):
                try:
                    self.colony.m_init_cond.m_droneMiteSurvivorshipField = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid icdronemitesurvivorship: {value}")
                    return False
        if name == "icworkeradultinfest":
            if self.colony and hasattr(self.colony, "m_init_cond"):
                try:
                    self.colony.m_init_cond.m_workerAdultInfestField = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid icworkeradultinfest: {value}")
                    return False
        if name == "icworkerbroodinfest":
            if self.colony and hasattr(self.colony, "m_init_cond"):
                try:
                    self.colony.m_init_cond.m_workerBroodInfestField = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid icworkerbroodinfest: {value}")
                    return False
        if name == "icworkermiteoffspring":
            if self.colony and hasattr(self.colony, "m_init_cond"):
                try:
                    self.colony.m_init_cond.m_workerMiteOffspring = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid icworkermiteoffspring: {value}")
                    return False
        if name == "initmitepctresistant":
            try:
                self.init_mite_pct_resistant = float(value)
                return True
            except Exception:
                self.add_to_error_list(f"Invalid initmitepctresistant: {value}")
                return False
        if name == "icworkermitesurvivorship":
            if self.colony and hasattr(self.colony, "m_init_cond"):
                try:
                    self.colony.m_init_cond.m_workerMiteSurvivorship = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid icworkermitesurvivorship: {value}")
                    return False
        # AI/Pesticide Parameters (following C++ session.cpp pattern)
        if name == "ainame":
            if self.colony and hasattr(self.colony, "m_epadata"):
                self.colony.m_epadata.m_AI_Name = value
                return True
        if name == "aiadultslope":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_AI_AdultSlope = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid aiadultslope: {value}")
                    return False
        if name == "aiadultld50":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_AI_AdultLD50 = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid aiadultld50: {value}")
                    return False
        if name == "aiadultslopecontact":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_AI_AdultSlope_Contact = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid aiadultslopecontact: {value}")
                    return False
        if name == "aiadultld50contact":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_AI_AdultLD50_Contact = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid aiadultld50contact: {value}")
                    return False
        if name == "ailarvaslope":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_AI_LarvaSlope = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid ailarvaslope: {value}")
                    return False
        if name == "ailarvald50":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_AI_LarvaLD50 = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid ailarvald50: {value}")
                    return False
        if name == "aikow":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_AI_KOW = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid aikow: {value}")
                    return False
        if name == "aikoc":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_AI_KOC = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid aikoc: {value}")
                    return False
        if name == "aihalflife":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_AI_HalfLife = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid aihalflife: {value}")
                    return False
        if name == "aicontactfactor":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_AI_ContactFactor = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid aicontactfactor: {value}")
                    return False

        # Consumption Parameters (CL4Pollen, etc.) - following C++ session.cpp pattern
        if name == "cl4pollen":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_C_L4_Pollen = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid cl4pollen: {value}")
                    return False
        if name == "cl4nectar":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_C_L4_Nectar = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid cl4nectar: {value}")
                    return False
        if name == "cl5pollen":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_C_L5_Pollen = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid cl5pollen: {value}")
                    return False
        if name == "cl5nectar":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_C_L5_Nectar = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid cl5nectar: {value}")
                    return False
        if name == "cldpollen":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_C_LD_Pollen = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid cldpollen: {value}")
                    return False
        if name == "cldnectar":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_C_LD_Nectar = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid cldnectar: {value}")
                    return False
        if name == "ca13pollen":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_C_A13_Pollen = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid ca13pollen: {value}")
                    return False
        if name == "ca13nectar":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_C_A13_Nectar = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid ca13nectar: {value}")
                    return False
        if name == "ca410pollen":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_C_A410_Pollen = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid ca410pollen: {value}")
                    return False
        if name == "ca410nectar":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_C_A410_Nectar = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid ca410nectar: {value}")
                    return False
        if name == "ca1120pollen":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_C_A1120_Pollen = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid ca1120pollen: {value}")
                    return False
        if name == "ca1120nectar":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_C_A1120_Nectar = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid ca1120nectar: {value}")
                    return False
        if name == "cadpollen":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_C_AD_Pollen = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid cadpollen: {value}")
                    return False
        if name == "cadnectar":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_C_AD_Nectar = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid cadnectar: {value}")
                    return False
        if name == "cforagerpollen":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_C_Forager_Pollen = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid cforagerpollen: {value}")
                    return False
        if name == "cforagernectar":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_C_Forager_Nectar = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid cforagernectar: {value}")
                    return False

        # Foraging Parameters (IPollenTrips, etc.) - following C++ session.cpp pattern
        if name == "ipollentrips":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_I_PollenTrips = int(
                        float(value)
                    )  # Convert float to int like C++
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid ipollentrips: {value}")
                    return False
        if name == "inectartrips":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_I_NectarTrips = int(
                        float(value)
                    )  # Convert float to int like C++
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid inectartrips: {value}")
                    return False
        if name == "ipercentnectarforagers":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_I_PercentNectarForagers = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid ipercentnectarforagers: {value}")
                    return False
        if name == "ipollenload":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_I_PollenLoad = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid ipollenload: {value}")
                    return False
        if name == "inectarload":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_I_NectarLoad = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid inectarload: {value}")
                    return False

        # Feature Flags (FoliarEnabled, etc.) - following C++ session.cpp pattern
        if name == "foliarenabled":
            if self.colony and hasattr(self.colony, "m_epadata"):
                self.colony.m_epadata.m_FoliarEnabled = parse_bool(value)
                return True
        if name == "soilenabled":
            if self.colony and hasattr(self.colony, "m_epadata"):
                self.colony.m_epadata.m_SoilEnabled = parse_bool(value)
                return True
        if name == "seedenabled":
            if self.colony and hasattr(self.colony, "m_epadata"):
                self.colony.m_epadata.m_SeedEnabled = parse_bool(value)
                return True
        if name == "necpolfileenable":
            if self.colony and hasattr(self.colony, "m_epadata"):
                self.colony.m_epadata.m_NecPolFileEnabled = parse_bool(value)
                return True

        # Exposure Parameters (EAppRate, etc.) - following C++ session.cpp pattern
        if name == "eapprate":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_E_AppRate = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid eapprate: {value}")
                    return False
        if name == "esoiltheta":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_E_SoilTheta = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid esoiltheta: {value}")
                    return False
        if name == "esoilp":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_E_SoilP = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid esoilp: {value}")
                    return False
        if name == "esoilfoc":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_E_SoilFoc = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid esoilfoc: {value}")
                    return False
        if name == "esoilconcentration":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_E_SoilConcentration = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid esoilconcentration: {value}")
                    return False
        if name == "eseedapprate":
            if self.colony and hasattr(self.colony, "m_epadata"):
                try:
                    self.colony.m_epadata.m_E_SeedAppRate = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid eseedapprate: {value}")
                    return False

        # Foliar Date Parameters - following C++ session.cpp pattern
        if name == "foliarappdate":
            if self.colony and hasattr(self.colony, "m_epadata"):
                dt = parse_date(value)
                if dt:
                    self.colony.m_epadata.m_FoliarAppDate = dt
                    return True
                self.add_to_error_list(
                    f"Invalid foliarappdate format (expected MM/DD/YYYY): {value}"
                )
                return False
        if name == "foliarforagebegin":
            if self.colony and hasattr(self.colony, "m_epadata"):
                dt = parse_date(value)
                if dt:
                    self.colony.m_epadata.m_FoliarForageBegin = dt
                    return True
                self.add_to_error_list(
                    f"Invalid foliarforagebegin format (expected MM/DD/YYYY): {value}"
                )
                return False
        if name == "foliarforageend":
            if self.colony and hasattr(self.colony, "m_epadata"):
                dt = parse_date(value)
                if dt:
                    self.colony.m_epadata.m_FoliarForageEnd = dt
                    return True
                self.add_to_error_list(
                    f"Invalid foliarforageend format (expected MM/DD/YYYY): {value}"
                )
                return False
        if name == "soilforagebegin":
            if self.colony and hasattr(self.colony, "m_epadata"):
                dt = parse_date(value)
                if dt:
                    self.colony.m_epadata.m_SoilForageBegin = dt
                    return True
                self.add_to_error_list(
                    f"Invalid soilforagebegin format (expected MM/DD/YYYY): {value}"
                )
                return False
        if name == "soilforageend":
            if self.colony and hasattr(self.colony, "m_epadata"):
                dt = parse_date(value)
                if dt:
                    self.colony.m_epadata.m_SoilForageEnd = dt
                    return True
                self.add_to_error_list(
                    f"Invalid soilforageend format (expected MM/DD/YYYY): {value}"
                )
                return False
        if name == "seedforagebegin":
            if self.colony and hasattr(self.colony, "m_epadata"):
                dt = parse_date(value)
                if dt:
                    self.colony.m_epadata.m_SeedForageBegin = dt
                    return True
                self.add_to_error_list(
                    f"Invalid seedforagebegin format (expected MM/DD/YYYY): {value}"
                )
                return False
        if name == "seedforageend":
            if self.colony and hasattr(self.colony, "m_epadata"):
                dt = parse_date(value)
                if dt:
                    self.colony.m_epadata.m_SeedForageEnd = dt
                    return True
                self.add_to_error_list(
                    f"Invalid seedforageend format (expected MM/DD/YYYY): {value}"
                )
                return False

        # Resource Management Parameters (following C++ session.cpp pattern)
        if name == "initcolnectar":
            if self.colony:
                try:
                    self.colony.m_ColonyNecInitAmount = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid initcolnectar: {value}")
                    return False
        if name == "initcolpollen":
            if self.colony:
                try:
                    self.colony.m_ColonyPolInitAmount = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid initcolpollen: {value}")
                    return False
        if name == "maxcolnectar":
            if self.colony:
                try:
                    self.colony.m_ColonyNecMaxAmount = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid maxcolnectar: {value}")
                    return False
        if name == "maxcolpollen":
            if self.colony:
                try:
                    self.colony.m_ColonyPolMaxAmount = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid maxcolpollen: {value}")
                    return False
        if name == "suppollenenable":
            if self.colony:
                self.colony.m_SuppPollenEnabled = parse_bool(value)
                return True
        if name == "supnectarenable":
            if self.colony:
                self.colony.m_SuppNectarEnabled = parse_bool(value)
                return True
        if name == "suppollenamount":
            if self.colony and hasattr(self.colony, "m_SuppPollen"):
                try:
                    self.colony.m_SuppPollen.m_StartingAmount = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid suppollenamount: {value}")
                    return False
        if name == "suppollenbegin":
            if self.colony and hasattr(self.colony, "m_SuppPollen"):
                try:
                    # Parse date in format MM/DD/YYYY (like C++)
                    date_obj = datetime.datetime.strptime(value, "%m/%d/%Y")
                    self.colony.m_SuppPollen.m_BeginDate = date_obj
                    return True
                except Exception:
                    self.add_to_error_list(
                        f"Invalid suppollenbegin date format (expected MM/DD/YYYY): {value}"
                    )
                    return False
        if name == "suppollenend":
            if self.colony and hasattr(self.colony, "m_SuppPollen"):
                try:
                    # Parse date in format MM/DD/YYYY (like C++)
                    date_obj = datetime.datetime.strptime(value, "%m/%d/%Y")
                    self.colony.m_SuppPollen.m_EndDate = date_obj
                    return True
                except Exception:
                    self.add_to_error_list(
                        f"Invalid suppollenend date format (expected MM/DD/YYYY): {value}"
                    )
                    return False
        if name == "supnectaramount":
            if self.colony and hasattr(self.colony, "m_SuppNectar"):
                try:
                    self.colony.m_SuppNectar.m_StartingAmount = float(value)
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid supnectaramount: {value}")
                    return False
        if name == "supnectarbegin":
            if self.colony and hasattr(self.colony, "m_SuppNectar"):
                try:
                    # Parse date in format MM/DD/YYYY (like C++)
                    date_obj = datetime.datetime.strptime(value, "%m/%d/%Y")
                    self.colony.m_SuppNectar.m_BeginDate = date_obj
                    return True
                except Exception:
                    self.add_to_error_list(
                        f"Invalid supnectarbegin date format (expected MM/DD/YYYY): {value}"
                    )
                    return False
        if name == "supnectarend":
            if self.colony and hasattr(self.colony, "m_SuppNectar"):
                try:
                    # Parse date in format MM/DD/YYYY (like C++)
                    date_obj = datetime.datetime.strptime(value, "%m/%d/%Y")
                    self.colony.m_SuppNectar.m_EndDate = date_obj
                    return True
                except Exception:
                    self.add_to_error_list(
                        f"Invalid supnectarend date format (expected MM/DD/YYYY): {value}"
                    )
                    return False
        if name == "foragermaxprop":
            if self.colony and hasattr(self.colony, "foragers"):
                try:
                    self.colony.foragers.set_prop_actual_foragers(float(value))
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid foragermaxprop: {value}")
                    return False
        if name == "needresourcestolive":
            if self.colony:
                self.colony.m_NoResourceKillsColony = parse_bool(value)
                return True

        # Life Stage Transition Parameters (following C++ session.cpp pattern)
        if name == "etolxitionen":
            # EtoL Transition Enable - theColony.m_InitCond.m_EggTransitionDRV.SetEnabled(Value == "true")
            if self.colony and hasattr(self.colony, "m_init_cond"):
                self.colony.m_init_cond.m_EggTransitionDRV.set_enabled(
                    parse_bool(value)
                )
                return True
            return False
        if name == "ltobxitionen":
            # LtoB Transition Enable - theColony.m_InitCond.m_LarvaeTransitionDRV.SetEnabled(Value == "true")
            if self.colony and hasattr(self.colony, "m_init_cond"):
                self.colony.m_init_cond.m_LarvaeTransitionDRV.set_enabled(
                    parse_bool(value)
                )
                return True
            return False
        if name == "btoaxitionen":
            # BtoA Transition Enable - theColony.m_InitCond.m_BroodTransitionDRV.SetEnabled(Value == "true")
            if self.colony and hasattr(self.colony, "m_init_cond"):
                self.colony.m_init_cond.m_BroodTransitionDRV.set_enabled(
                    parse_bool(value)
                )
                return True
            return False
        if name == "atofxitionen":
            # AtoF Transition Enable - theColony.m_InitCond.m_AdultTransitionDRV.SetEnabled(Value == "true")
            if self.colony and hasattr(self.colony, "m_init_cond"):
                self.colony.m_init_cond.m_AdultTransitionDRV.set_enabled(
                    parse_bool(value)
                )
                return True
            return False

        # Lifespan Control Parameters (following C++ session.cpp pattern)
        if name == "alifespanen":
            # Adult Lifespan Enable - theColony.m_InitCond.m_AdultLifespanDRV.SetEnabled(Value == "true")
            if self.colony and hasattr(self.colony, "m_init_cond"):
                self.colony.m_init_cond.m_AdultLifespanDRV.set_enabled(
                    parse_bool(value)
                )
                return True
            return False
        if name == "flifespanen":
            # Forager Lifespan Enable - theColony.m_InitCond.m_ForagerLifespanDRV.SetEnabled(Value == "true")
            if self.colony and hasattr(self.colony, "m_init_cond"):
                self.colony.m_init_cond.m_ForagerLifespanDRV.set_enabled(
                    parse_bool(value)
                )
                return True
            return False

        # Adult Aging Delay Parameters (following C++ session.cpp pattern)
        if name == "adultagedelay":
            # Adult Age Delay - theColony.SetAdultAgingDelay(atoi(Value))
            if self.colony:
                try:
                    self.colony.set_adult_aging_delay(int(value))
                    return True
                except Exception:
                    self.add_to_error_list(f"Invalid adultagedelay: {value}")
                    return False
            return False
        if name == "adultagedelayeggthreshold":
            # Adult Age Delay Egg Threshold - theColony.SetAdultAgingDelayEggThreshold(atoi(Value))
            if self.colony:
                try:
                    self.colony.set_adult_aging_delay_egg_threshold(int(value))
                    return True
                except Exception:
                    self.add_to_error_list(
                        f"Invalid adultagedelayeggthreshold: {value}"
                    )
                    return False
            return False

        # Life Stage Transition Percentage Parameters (following C++ session.cpp pattern)
        if name == "etolxition":
            # Egg to Larva Transition - theColony.m_InitCond.m_EggTransitionDRV.AddItem() or ClearAll()
            if self.colony and hasattr(self.colony, "m_init_cond"):
                if value.lower() == "clear":
                    self.colony.m_init_cond.m_EggTransitionDRV.clear_all()
                    return True
                else:
                    try:
                        # Parse comma-separated format: StartDate,EndDate,Percentage
                        parts = [part.strip() for part in value.split(",")]
                        if len(parts) >= 3:
                            start_date_str, end_date_str, percentage_str = (
                                parts[0],
                                parts[1],
                                parts[2],
                            )
                            start_date = parse_date(start_date_str)
                            end_date = parse_date(end_date_str)
                            percentage = float(percentage_str)
                            if start_date and end_date:
                                self.colony.m_init_cond.m_EggTransitionDRV.add_item(
                                    start_date, end_date, percentage
                                )
                                return True
                    except Exception:
                        self.add_to_error_list(f"Invalid etolxition format: {value}")
                        return False
            return False
        if name == "ltobxition":
            # Larva to Brood Transition - theColony.m_InitCond.m_LarvaeTransitionDRV.AddItem() or ClearAll()
            if self.colony and hasattr(self.colony, "m_init_cond"):
                if value.lower() == "clear":
                    self.colony.m_init_cond.m_LarvaeTransitionDRV.clear_all()
                    return True
                else:
                    try:
                        # Parse comma-separated format: StartDate,EndDate,Percentage
                        parts = [part.strip() for part in value.split(",")]
                        if len(parts) >= 3:
                            start_date_str, end_date_str, percentage_str = (
                                parts[0],
                                parts[1],
                                parts[2],
                            )
                            start_date = parse_date(start_date_str)
                            end_date = parse_date(end_date_str)
                            percentage = float(percentage_str)
                            if start_date and end_date:
                                self.colony.m_init_cond.m_LarvaeTransitionDRV.add_item(
                                    start_date, end_date, percentage
                                )
                                return True
                    except Exception:
                        self.add_to_error_list(f"Invalid ltobxition format: {value}")
                        return False
            return False
        if name == "btoaxition":
            # Brood to Adult Transition - theColony.m_InitCond.m_BroodTransitionDRV.AddItem() or ClearAll()
            if self.colony and hasattr(self.colony, "m_init_cond"):
                if value.lower() == "clear":
                    self.colony.m_init_cond.m_BroodTransitionDRV.clear_all()
                    return True
                else:
                    try:
                        # Parse comma-separated format: StartDate,EndDate,Percentage
                        parts = [part.strip() for part in value.split(",")]
                        if len(parts) >= 3:
                            start_date_str, end_date_str, percentage_str = (
                                parts[0],
                                parts[1],
                                parts[2],
                            )
                            start_date = parse_date(start_date_str)
                            end_date = parse_date(end_date_str)
                            percentage = float(percentage_str)
                            if start_date and end_date:
                                self.colony.m_init_cond.m_BroodTransitionDRV.add_item(
                                    start_date, end_date, percentage
                                )
                                return True
                    except Exception:
                        self.add_to_error_list(f"Invalid btoaxition format: {value}")
                        return False
            return False
        if name == "atofxition":
            # Adult to Forager Transition - theColony.m_InitCond.m_AdultTransitionDRV.AddItem() or ClearAll()
            if self.colony and hasattr(self.colony, "m_init_cond"):
                if value.lower() == "clear":
                    self.colony.m_init_cond.m_AdultTransitionDRV.clear_all()
                    return True
                else:
                    try:
                        # Parse comma-separated format: StartDate,EndDate,Percentage
                        parts = [part.strip() for part in value.split(",")]
                        if len(parts) >= 3:
                            start_date_str, end_date_str, percentage_str = (
                                parts[0],
                                parts[1],
                                parts[2],
                            )
                            start_date = parse_date(start_date_str)
                            end_date = parse_date(end_date_str)
                            percentage = float(percentage_str)
                            if start_date and end_date:
                                self.colony.m_init_cond.m_AdultTransitionDRV.add_item(
                                    start_date, end_date, percentage
                                )
                                return True
                    except Exception:
                        self.add_to_error_list(f"Invalid atofxition format: {value}")
                        return False
            return False

        # Lifespan Data Parameters (following C++ session.cpp pattern)
        if name == "alifespan":
            # Adult Lifespan - theColony.m_InitCond.m_AdultLifespanDRV.AddItem() or ClearAll()
            if self.colony and hasattr(self.colony, "m_init_cond"):
                if value.lower() == "clear":
                    self.colony.m_init_cond.m_AdultLifespanDRV.clear_all()
                    return True
                else:
                    try:
                        # Parse comma-separated format: StartDate,EndDate,LifespanDays
                        parts = [part.strip() for part in value.split(",")]
                        if len(parts) >= 3:
                            start_date_str, end_date_str, lifespan_str = (
                                parts[0],
                                parts[1],
                                parts[2],
                            )
                            start_date = parse_date(start_date_str)
                            end_date = parse_date(end_date_str)
                            lifespan_days = float(lifespan_str)
                            # Apply C++ constraint: Adult bee age constraint (7-21 days)
                            if start_date and end_date and 7 <= lifespan_days <= 21:
                                self.colony.m_init_cond.m_AdultLifespanDRV.add_item(
                                    start_date, end_date, lifespan_days
                                )
                                return True
                            elif not (7 <= lifespan_days <= 21):
                                self.add_to_error_list(
                                    f"Adult lifespan must be 7-21 days, got: {lifespan_days}"
                                )
                                return False
                    except Exception:
                        self.add_to_error_list(f"Invalid alifespan format: {value}")
                        return False
            return False
        if name == "flifespan":
            # Forager Lifespan - theColony.m_InitCond.m_ForagerLifespanDRV.AddItem() or ClearAll()
            if self.colony and hasattr(self.colony, "m_init_cond"):
                if value.lower() == "clear":
                    self.colony.m_init_cond.m_ForagerLifespanDRV.clear_all()
                    return True
                else:
                    try:
                        # Parse comma-separated format: StartDate,EndDate,LifespanDays
                        parts = [part.strip() for part in value.split(",")]
                        if len(parts) >= 3:
                            start_date_str, end_date_str, lifespan_str = (
                                parts[0],
                                parts[1],
                                parts[2],
                            )
                            start_date = parse_date(start_date_str)
                            end_date = parse_date(end_date_str)
                            lifespan_days = float(lifespan_str)
                            # Apply C++ constraint: Forager lifespan constraint (0-20 days)
                            if start_date and end_date and 0 <= lifespan_days <= 20:
                                self.colony.m_init_cond.m_ForagerLifespanDRV.add_item(
                                    start_date, end_date, lifespan_days
                                )
                                return True
                            elif not (0 <= lifespan_days <= 20):
                                self.add_to_error_list(
                                    f"Forager lifespan must be 0-20 days, got: {lifespan_days}"
                                )
                                return False
                    except Exception:
                        self.add_to_error_list(f"Invalid flifespan format: {value}")
                        return False
            return False

        # Varroa Treatment Parameters (following C++ session.cpp pattern)
        if name == "vtenable":
            self.vt_enable = parse_bool(value)
            return True
        if name == "vtdata":
            if not self.colony or not hasattr(self.colony, "m_mite_treatment_info"):
                self.add_to_error_list("Unable to store vtdata: colony mite treatment info is unavailable")
                return False

            if value.strip().lower() == "clear":
                self.colony.m_mite_treatment_info.clear_all()
                return True

            parts = [part.strip() for part in value.split(",")]
            if len(parts) == 4:
                self.add_to_error_list(
                    f"Invalid vtdata format: {value}. VTData no longer takes a resistant% "
                    "field. Expected start_date,duration_weeks,mortality%. Mite resistance "
                    "is set on the population with InitMitePctResistant and "
                    "PctImmMitesResistant."
                )
                return False
            if len(parts) != 3:
                self.add_to_error_list(
                    f"Invalid vtdata format: {value}. Expected start_date,duration_weeks,mortality%"
                )
                return False

            start_date_str, duration_str, pct_mortality_str = parts
            start_date = parse_date(start_date_str)
            if not start_date:
                self.add_to_error_list(f"Invalid vtdata start date: {start_date_str}")
                return False

            try:
                duration = int(duration_str)
                pct_mortality = float(pct_mortality_str)
            except Exception:
                self.add_to_error_list(f"Invalid vtdata values: {value}")
                return False

            self.colony.m_mite_treatment_info.add_item_by_values(
                start_date,
                duration,
                pct_mortality,
            )
            return True

        # Immigration parameters
        if name == "immenabled":
            self.immigration_enabled = parse_bool(value)
            return True
        if name == "immtype":
            self.immigration_type = value
            return True
        if name == "totalimmmites":
            try:
                self.tot_immigrating_mites = int(value)
                return True
            except Exception:
                self.add_to_error_list(f"Invalid totalimmmites: {value}")
                return False
        if name == "pctimmmitesresistant":
            try:
                self.imm_mite_pct_resistant = float(value)
                return True
            except Exception:
                self.add_to_error_list(f"Invalid pctimmmitesresistant: {value}")
                return False
        if name == "immstart":
            dt = parse_date(value)
            if dt:
                self.immigration_start_date = dt
                return True
            self.add_to_error_list(f"Invalid immstart date: {value}")
            return False
        if name == "immend":
            dt = parse_date(value)
            if dt:
                self.immigration_end_date = dt
                return True
            self.add_to_error_list(f"Invalid immend date: {value}")
            return False
        if name == "immenabled":
            self.immigration_enabled = parse_bool(value)
            return True

        # Requeening parameters
        if name == "rqegglaydelay":
            try:
                self.rq_egg_laying_delay = int(value)
                return True
            except Exception:
                self.add_to_error_list(f"Invalid rqegglaydelay: {value}")
                return False
        if name == "rqwkrdrnratio":
            try:
                self.rq_wkr_drn_ratio = float(value)
                return True
            except Exception:
                self.add_to_error_list(f"Invalid rqwkrdrnratio: {value}")
                return False
        if name == "rqrequeendate":
            dt = parse_date(value)
            if dt:
                self.rq_requeen_date = dt
                return True
            self.add_to_error_list(f"Invalid rqrequeendate: {value}")
            return False
        if name == "rqenablerequeen":
            self.rq_enable_requeen = parse_bool(value)
            return True
        if name == "rqscheduled":
            self.rq_scheduled = 0 if parse_bool(value) else 1
            return True
        if name == "rqqueenstrength":
            try:
                self.rq_queen_strength = float(value)
                if self.colony and hasattr(self.colony, "add_requeen_strength"):
                    self.colony.add_requeen_strength(self.rq_queen_strength)
                return True
            except Exception:
                self.add_to_error_list(f"Invalid rqqueenstrength: {value}")
                return False
        if name == "rqonce":
            self.rq_once = 0 if parse_bool(value) else 1
            return True

        # Add more explicit parameter handling for other classes (nutrient contamination, cold storage, etc.) as needed
        # Example: cold storage
        if name == "coldstoragestart":
            dt = parse_date(value)
            if dt and hasattr(self, "cold_storage_simulator"):
                self.cold_storage_simulator.set_start_date(dt)
                return True
        if name == "coldstorageend":
            dt = parse_date(value)
            if dt and hasattr(self, "cold_storage_simulator"):
                self.cold_storage_simulator.set_end_date(dt)
                return True
        if name == "coldstorageenable":
            if hasattr(self, "cold_storage_simulator"):
                self.cold_storage_simulator.set_enabled(parse_bool(value))
                return True

        # Fallback: unknown parameter
        self.add_to_error_list(f"Unknown parameter: {param_name}")
        return False

    def _generate_initial_conditions_row(self):
        """
        Generate the Initial row that shows exact initial conditions.
        Matches C++ logic from session.cpp lines 418-475.
        This row has date="Initial" and shows the colony state before any simulation days.
        """
        if not self.colony:
            return "Initial 0 0 0 0 0 0 0 0 0 0 0 0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 0 0 0 0.0 0.0 0 0.0 0.0 0.0 0.0 0.0 0 0 0 0 0 0.0 0.0 0.0 0.0 0.0 0.0 0.0 No"

        # Generate Initial row using exact C++ field order and formatting
        initial_data = [
            "Initial   ",  # "%s" - Date field = "Initial" (padded like C++)
            "%6d" % self.colony.get_colony_size(),  # "%6d" - Colony size
            "%8d"
            % self.colony.get_adult_drones(),  # "%8d" - Adult Drones (Dadl.GetQuantity())
            "%8d"
            % self.colony.get_adult_workers(),  # "%8d" - Adult Workers (Wadl.GetQuantity())
            "%8d"
            % self.colony.get_foragers(),  # "%8d" - Foragers (foragers.GetQuantity())
            "%8d"
            % self.colony.get_active_foragers(),  # "%8d" - Active Foragers (foragers.GetActiveQuantity())
            "%7d"
            % self.colony.get_drone_brood(),  # "%7d" - Drone Brood (CapDrn.GetQuantity())
            "%6d"
            % self.colony.get_worker_brood(),  # "%6d" - Worker Brood (CapWkr.GetQuantity())
            "%6d"
            % self.colony.get_drone_larvae(),  # "%6d" - Drone Larvae (Dlarv.GetQuantity())
            "%6d"
            % self.colony.get_worker_larvae(),  # "%6d" - Worker Larvae (Wlarv.GetQuantity())
            "%6d"
            % self.colony.get_drone_eggs(),  # "%6d" - Drone Eggs (Deggs.GetQuantity())
            "%6d"
            % self.colony.get_worker_eggs(),  # "%6d" - Worker Eggs (Weggs.GetQuantity())
            "%6d"
            % self.colony.get_total_eggs_laid_today(),  # "%6d" - Total Eggs (GetEggsToday())
            "%7.2f" % 0.0,  # "%7.2f" - DD (GetDDToday() - 0 for Initial)
            "%6.2f" % 0.0,  # "%6.2f" - L (GetLToday() - 0 for Initial)
            "%6.2f" % 0.0,  # "%6.2f" - N (GetNToday() - 0 for Initial)
            "%8.2f" % 0.0,  # "%8.2f" - P (GetPToday() - 0 for Initial)
            "%7.2f" % 0.0,  # "%7.2f" - dd (GetddToday() - 0 for Initial)
            "%6.2f" % 0.0,  # "%6.2f" - l (GetlToday() - 0 for Initial)
            "%8.2f" % 0.0,  # "%8.2f" - n (GetnToday() - 0 for Initial)
            "%6.2f"
            % self.colony.get_free_mites(),  # "%6.2f" - Free Mites (RunMite.GetTotal())
            "%6.2f"
            % self.colony.get_drone_brood_mites(),  # "%6.2f" - DBrood Mites (CapDrn.GetMiteCount())
            "%6.2f"
            % self.colony.get_worker_brood_mites(),  # "%6.2f" - WBrood Mites (CapWkr.GetMiteCount())
            "%6.2f"
            % self.colony.get_mites_per_drone_brood(),  # "%6.2f" - DMite/Cell (CapDrn.GetMitesPerCell())
            "%6.2f"
            % self.colony.get_mites_per_worker_brood(),  # "%6.2f" - WMite/Cell (CapWkr.GetMitesPerCell())
            "%6.0f" % 0,  # "%6.0f" - Mites Dying (0 for Initial)
            "%6.0f" % 0.0,  # "%6.0f" - Prop Mites Dying (0.0 for Initial)
            "%8.1f"
            % 0.0,  # "%8.1f" - Colony Pollen (0.0 for Initial - matches C++ logic)
            "%7.4f" % 0.0,  # "%7.4f" - Conc Pollen Pest (0.0 for Initial)
            "%8.1f"
            % 0.0,  # "%8.1f" - Colony Nectar (0.0 for Initial - matches C++ logic)
            "%7.4f" % 0.0,  # "%7.4f" - Conc Nectar Pest (0.0 for Initial)
            "%6d" % 0,  # "%6d" - Dead DLarv (0 for Initial)
            "%6d" % 0,  # "%6d" - Dead WLarv (0 for Initial)
            "%6d" % 0,  # "%6d" - Dead DAdlt (0 for Initial)
            "%6d" % 0,  # "%6d" - Dead WAdlt (0 for Initial)
            "%6d" % 0,  # "%6d" - Dead Foragers (0 for Initial)
            "%8.3f"
            % self.colony.get_queen_strength(),  # "%8.3f" - Queen Strength (queen.GetQueenStrength())
            "%8.3f" % 0.0,  # "%8.3f" - Ave Temp (0.0 for Initial - no weather yet)
            "%6.3f" % 0.0,  # "%6.3f" - Rain (0.0 for Initial)
            "%8.3f" % 0.0,  # "%8.3f" - Min Temp (0.0 for Initial)
            "%8.3f" % 0.0,  # "%8.3f" - Max Temp (0.0 for Initial)
            "%8.2f"
            % 0.0,  # "%8.2f" - Daylight Hours (0.0 for Initial) - KEY FORMATTING
            "%8.2f" % 0.0,  # "%8.2f" - Activity Ratio (0.0 for Initial)
            "No",  # "%s" - Forage Day ("No" for Initial)
        ]

        return " ".join(initial_data)

    def initialize_simulation(self):
        self.results_text.clear()
        self.results_header.clear()
        self.results_file_header.clear()
        self.inc_immigrating_mites = 0
        if self.colony:
            # Must precede initialize_colony(), which builds the initial mite
            # population from this proportion.
            self.colony.set_mite_pct_resistance(self.init_mite_pct_resistant)
            self.colony.initialize_colony()

            # Transfer VT enable flag from session to colony
            if hasattr(self, "vt_enable"):
                self.colony.set_vt_enable(self.vt_enable)

        self.cum_immigrating_mites = 0
        self.first_result_entry = True
