"""BeePop+ Colony Simulation Module.

This module contains the core Colony class that manages all aspects of honey bee
colony dynamics and simulation. It serves as a Python port of the C++ CColony
class from the original BeePop+ system.

The Colony class is the heart of the simulation system, coordinating all bee life
stages, mite populations, resource management, environmental responses, and
pesticide effects within a single honey bee colony.

Architecture:
    The Colony class manages multiple interconnected subsystems:

    Colony (Main Controller)
    ├── Queen (Egg laying and reproduction)
    ├── Bee Life Stages
    │   ├── EggList (Developing eggs)
    │   ├── LarvaList (Larval development)
    │   ├── BroodList (Pupal development)
    │   ├── AdultList (Adult workers and drones)
    │   └── ForagerListA (Foraging workers)
    ├── Mite Management
    │   ├── Running Mites (Free-living mites)
    │   ├── Brood Mites (Mites in cells)
    │   └── MiteTreatments (Treatment protocols)
    ├── Resource Management
    │   ├── ColonyResource (Pollen/nectar stores)
    │   └── Supplemental Feeding
    ├── Environmental Interaction
    │   ├── WeatherEvents (Daily conditions)
    │   ├── Daylight responses
    │   └── Seasonal patterns
    └── Toxicology
        ├── EPAData (Pesticide tracking)
        ├── NutrientContaminationTable (Exposure records)
        └── Mortality calculations

Key Constants:
    EGGLIFE (int): Duration of egg stage (3 days)
    WLARVLIFE (int): Worker larva development time (5 days)
    DLARVLIFE (int): Drone larva development time (7 days)
    WBROODLIFE (int): Worker brood development time (13 days)
    DBROODLIFE (int): Drone brood development time (14 days)
    WADLLIFE (int): Worker adult lifespan (21 days)
    DADLLIFE (int): Drone adult lifespan (21 days)
    PROPINFSTW (float): Proportion of worker cells that get infested (0.08)
    PROPINFSTD (float): Proportion of drone cells that get infested (0.92)
    MAXMITES_PER_WORKER_CELL (int): Maximum mites per worker cell (4)
    MAXMITES_PER_DRONE_CELL (int): Maximum mites per drone cell (7)

Notes:
    - This class is ported from C++ and maintains C++ naming conventions
      where necessary for compatibility
    - All bee populations are tracked in discrete age cohorts
    - Time progression is handled through daily update cycles
    - The class is designed to be deterministic for reproducible results
"""

# Imports for referenced objects
from pybeepop.beepop.epadata import EPAData
from pybeepop.beepop.colonyresource import ColonyResource, ResourceItem
from pybeepop.beepop.queen import Queen
from pybeepop.beepop.nutrientcontaminationtable import NutrientContaminationTable
from pybeepop.beepop.beelist import (
    ForagerListA,
    AdultList,
    BroodList,
    LarvaList,
    EggList,
)
from pybeepop.beepop.mite import Mite
from pybeepop.beepop.brood import Brood
from pybeepop.beepop.mitetreatments import MiteTreatments
from pybeepop.beepop.daterangevalues import DateRangeValues
from pybeepop.beepop.egg import Egg
from pybeepop.beepop.coldstoragesimulator import ColdStorageSimulator
import math
from pybeepop.beepop.globaloptions import GlobalOptions
from pybeepop.beepop.spores import Spores
from types import SimpleNamespace
from datetime import datetime, timedelta


# Life stage durations (from colony.h)
EGGLIFE = 3
DLARVLIFE = 7
WLARVLIFE = 5
DBROODLIFE = 14
WBROODLIFE = 13
DADLLIFE = 21
WADLLIFE = 21

# Mite attributes
PROPINFSTW = 0.08
PROPINFSTD = 0.92
MAXMITES_PER_DRONE_CELL = 7
MAXMITES_PER_WORKER_CELL = 4

# Discrete event codes
DE_NONE = 1
DE_SWARM = 2
DE_CHALKBROOD = 3
DE_RESOURCEDEP = 4
DE_SUPERCEDURE = 5
DE_PESTICIDE = 6


class InOutEvent:
    """Additional statistics container for detailed colony simulation output.

    This class tracks transition events between bee life stages and mortality
    events for detailed analysis. These statistics are appended to normal
    simulation output when GlobalOptions.ShouldOutputInOutCounts() is activated.

    Note:
        All counts are initialized to -1 to indicate unset values.
        Call reset() to reinitialize all values to -1.
    """

    def __init__(self):
        self.m_NewWEggs = -1  # new worker eggs
        self.m_NewDEggs = -1  # new drone eggs
        self.m_WEggsToLarv = -1  # worker eggs moving to larvae
        self.m_DEggsToLarv = -1  # drone eggs moving to larvae
        self.m_WLarvToBrood = -1  # worker larvae moving to brood
        self.m_DLarvToBrood = -1  # drone larvae moving to brood
        self.m_WBroodToAdult = -1  # worker drone moving to adult
        self.m_DBroodToAdult = -1  # drone drone moving to adult
        self.m_DeadDAdults = -1  # drone adult dying
        self.m_ForagersKilledByPesticide = -1  # forager killed by pesticide
        self.m_WAdultToForagers = -1  # worker adult moving to forager
        self.m_WinterMortalityForagersLoss = -1  # forager dying due to winter mortality
        self.m_DeadForagers = -1  # forager dying
        self.m_PropRedux = -1.0  # Debug for a double

    def reset(self):
        """Reset all event counters to uninitialized state (-1).

        This method reinitializes all tracking counters to -1, indicating
        that no events have been recorded for the current simulation day.
        Should be called at the beginning of each simulation day.
        """
        self.m_NewWEggs = -1
        self.m_NewDEggs = -1
        self.m_WEggsToLarv = -1
        self.m_DEggsToLarv = -1
        self.m_WLarvToBrood = -1
        self.m_DLarvToBrood = -1
        self.m_WBroodToAdult = -1
        self.m_DBroodToAdult = -1
        self.m_DeadDAdults = -1
        self.m_ForagersKilledByPesticide = -1
        self.m_WAdultToForagers = -1
        self.m_WinterMortalityForagersLoss = -1
        self.m_DeadForagers = -1
        self.m_PropRedux = -1.0


class Colony:
    """Main simulation class for honey bee colony dynamics.

    This class represents a single honey bee colony and manages all aspects of
    its simulation including bee populations across all life stages, mite
    infestations, resource management, environmental responses, and pesticide
    effects. It serves as a Python port of the C++ CColony class.

    The Colony class operates on a daily time step, updating all bee populations,
    mite dynamics, resource consumption, and environmental interactions each
    simulation day.

    """

    def __init__(self, session=None):
        """Initialize a new Colony instance.

        Creates a new honey bee colony with default initial conditions,
        empty bee populations, and initialized subsystems for mites,
        resources, and environmental tracking.

        Args:
            session (VarroaPopSession, optional): The simulation session that
                manages this colony. If None, the colony will operate
                independently. Defaults to None.

        """
        # Attributes from CColony constructor
        self.name = ""
        self.has_been_initialized = False
        self.prop_rm_virgins = 1.0
        self.long_redux = [0.0, 0.1, 0.2, 0.6, 0.9, 0.9, 0.9, 0.9]
        self.m_vt_treatment_active = False
        self.m_vt_enable = False

        self.m_ColonyNecMaxAmount = 0
        self.m_ColonyPolMaxAmount = 0
        self.m_ColonyNecInitAmount = 0
        self.m_ColonyPolInitAmount = 0
        self.m_NoResourceKillsColony = False
        self.m_epadata = EPAData()
        self.resources = ColonyResource()  # Changed from m_resources for consistency
        self.m_colony_event_list = []
        self.m_nutrient_ct = NutrientContaminationTable()
        self.m_dead_worker_larvae_pesticide = 0
        self.m_dead_drone_larvae_pesticide = 0
        self.m_dead_worker_adults_pesticide = 0
        self.m_dead_drone_adults_pesticide = 0
        self.m_dead_foragers_pesticide = 0

        self.m_event_map = {}
        self.queen = Queen()
        self.m_p_session = (
            session  # Accept session reference instead of creating new one
        )
        # Add bee lists and other simulation objects as needed
        # Bee lists (port from CColony)
        self.foragers = ForagerListA()
        self.foragers.set_colony(self)  # Set colony reference for C++ compatibility
        self.dadl = AdultList()  # Drone adults
        self.wadl = AdultList()  # Worker adults
        self.capwkr = BroodList()  # Worker capped brood
        self.capdrn = BroodList()  # Drone capped brood
        self.wlarv = LarvaList()  # Worker larvae
        self.dlarv = LarvaList()  # Drone larvae
        self.weggs = EggList()  # Worker eggs
        self.deggs = EggList()  # Drone eggs

        # Lifespan constants (accessible as instance attributes for BeeList classes)
        self.egglife = EGGLIFE
        self.dlarvlife = DLARVLIFE
        self.wlarvlife = WLARVLIFE
        self.dbroodlife = DBROODLIFE
        self.wbroodlife = WBROODLIFE
        self.dadllife = DADLLIFE
        self.wadllife = WADLLIFE

        # Mite state
        self.run_mite = Mite()  # Free running mites
        self.prop_rm_virgins = 1.0
        self.emerging_mites_w = Mite()  # Worker emerging mites
        self.prop_emerging_virgins_w = 0.0
        self.num_emerging_brood_w = 0
        self.emerging_mites_d = Mite()  # Drone emerging mites
        self.prop_emerging_virgins_d = 0.0
        self.num_emerging_brood_d = 0

        # Spore population
        self.m_spores = Spores()

        # Mite treatment info
        self.m_mite_treatment_info = MiteTreatments()

        # Initial conditions container (port from ColonyInitCond)
        self.m_init_cond = SimpleNamespace()
        self.m_init_cond.m_droneAdultInfestField = 0.0
        self.m_init_cond.m_droneBroodInfestField = 0.0
        self.m_init_cond.m_droneMiteOffspringField = 2.7
        self.m_init_cond.m_droneMiteSurvivorshipField = 100.0
        self.m_init_cond.m_workerAdultInfestField = 0.0
        self.m_init_cond.m_workerBroodInfestField = 0.0
        self.m_init_cond.m_workerMiteOffspring = 1.5
        self.m_init_cond.m_workerMiteSurvivorship = 100.0
        self.m_init_cond.m_droneAdultsField = 0
        self.m_init_cond.m_droneBroodField = 0
        self.m_init_cond.m_droneEggsField = 0
        self.m_init_cond.m_droneLarvaeField = 0
        self.m_init_cond.m_workerAdultsField = 5000
        self.m_init_cond.m_workerBroodField = 5000
        self.m_init_cond.m_workerEggsField = 5000
        self.m_init_cond.m_workerLarvaeField = 5000
        self.m_init_cond.m_totalEggsField = 0
        self.m_init_cond.m_QueenStrength = 4.0
        self.m_init_cond.m_ForagerLifespan = 12

        # Initialize Date Range Value objects
        self.m_init_cond.m_AdultLifespanDRV = DateRangeValues()
        self.m_init_cond.m_ForagerLifespanDRV = DateRangeValues()
        self.m_init_cond.m_EggTransitionDRV = DateRangeValues()
        self.m_init_cond.m_BroodTransitionDRV = DateRangeValues()
        self.m_init_cond.m_LarvaeTransitionDRV = DateRangeValues()
        self.m_init_cond.m_AdultTransitionDRV = DateRangeValues()

        # Adult aging delay parameters
        self.adult_aging_delay_armed = False
        self.m_days_since_egg_laying_began = 0
        self.m_adult_age_delay_limit = 24  # Default from CColony
        self.m_adult_aging_delay_egg_threshold = 50  # Default from CColony

        # Feeding day flags
        self.m_pollen_feeding_day = False
        self.m_nectar_feeding_day = False

        # Sample period and mite death tracking
        self.m_mites_dying_today = 0.0
        self.m_mites_dying_this_period = 0.0

        # Additional attributes from colony.h
        self.m_VTStart = 0
        self.m_SPStart = 0
        self.m_VTDuration = 0
        self.m_VTMortality = 0
        self.m_SPEnable = False
        self.m_SPTreatmentActive = False
        self.m_InitMitePctResistant = 0.0
        self.m_CurrentForagerLifespan = 0
        self.m_RQQueenStrengthArray = []
        self.m_NutrientContEnabled = False
        self.m_SuppPollenEnabled = False
        self.m_SuppNectarEnabled = False
        self.m_SuppPollenAnnual = False
        self.m_SuppNectarAnnual = False

        # Supplemental feeding resource objects (match C++ structure)
        self.m_SuppPollen = SimpleNamespace()
        self.m_SuppPollen.m_BeginDate = datetime.now()
        self.m_SuppPollen.m_EndDate = datetime.now()
        self.m_SuppPollen.m_CurrentAmount = 0.0
        self.m_SuppPollen.m_StartingAmount = 0.0

        self.m_SuppNectar = SimpleNamespace()
        self.m_SuppNectar.m_BeginDate = datetime.now()
        self.m_SuppNectar.m_EndDate = datetime.now()
        self.m_SuppNectar.m_CurrentAmount = 0.0
        self.m_SuppNectar.m_StartingAmount = 0.0

        self.m_InOutEvent = InOutEvent()

    # Property aliases for consistent naming in consume_food methods
    @property
    def epa_data(self):
        return self.m_epadata

    @property
    def nutrient_ct(self):
        return self.m_nutrient_ct

    # Methods from colony.h not yet implemented
    def get_adult_aging_delay(self):
        return self.m_adult_age_delay_limit

    def set_adult_aging_delay(self, delay):
        self.m_adult_age_delay_limit = delay

    def get_adult_aging_delay_egg_threshold(self):
        return self.m_adult_aging_delay_egg_threshold

    def set_adult_aging_delay_egg_threshold(self, threshold):
        self.m_adult_aging_delay_egg_threshold = threshold

    def is_adult_aging_delay_armed(self):
        return self.adult_aging_delay_armed

    def set_adult_aging_delay_armed(self, armed_state):
        self.adult_aging_delay_armed = armed_state

    def set_initialized(self, val):
        self.has_been_initialized = val

    def is_initialized(self):
        return self.has_been_initialized

    def get_forager_lifespan(self):
        return self.m_init_cond.m_ForagerLifespan

    def get_cold_storage_simulator(self):
        """Return the singleton instance of the cold storage simulator."""
        return ColdStorageSimulator.get()

    def get_adult_drones(self):
        """Get the total number of adult drones."""
        return self.dadl.get_quantity()

    def get_adult_workers(self):
        """Get the total number of adult workers."""
        return self.wadl.get_quantity()

    def get_foragers(self):
        """Get the total number of foragers."""
        return self.foragers.get_quantity()

    def get_active_foragers(self):
        """Get the number of active foragers following C++ logic."""
        # Following C++ CForagerlistA::GetActiveQuantity() logic:
        # Limits active foragers to a proportion of total colony size
        return self.foragers.get_active_quantity()

    def get_drone_brood(self):
        """Get the total number of drone brood."""
        return self.capdrn.get_quantity()

    def get_worker_brood(self):
        """Get the total number of worker brood."""
        return self.capwkr.get_quantity()

    def get_drone_larvae(self):
        """Get the total number of drone larvae."""
        return self.dlarv.get_quantity()

    def get_worker_larvae(self):
        """Get the total number of worker larvae."""
        return self.wlarv.get_quantity()

    def get_drone_eggs(self):
        """Get the total number of drone eggs."""
        return self.deggs.get_quantity()

    def get_worker_eggs(self):
        """Get the total number of worker eggs."""
        return self.weggs.get_quantity()

    def get_total_eggs_laid_today(self):
        """Get the total number of all eggs laid today."""
        return self.queen.get_teggs()

    def get_free_mites(self):
        """Get the number of free mites."""
        return self.run_mite.get_total()

    def get_drone_brood_mites(self):
        """Get the number of mites in drone brood."""
        return self.capdrn.get_mite_count()

    def get_worker_brood_mites(self):
        """Get the number of mites in worker brood."""
        return self.capwkr.get_mite_count()

    def get_mites_per_drone_brood(self):
        """Get the mites per drone brood ratio."""
        return self.capdrn.get_mites_per_cell()

    def get_mites_per_worker_brood(self):
        """Get the mites per worker brood ratio."""
        return self.capwkr.get_mites_per_cell()

    def get_prop_mites_dying(self):
        """Get the proportion of mites dying."""
        if (self.get_mites_dying_this_period() + self.get_total_mite_count()) > 0:
            proportion_dying = self.get_mites_dying_this_period() / (
                self.get_mites_dying_this_period() + self.get_total_mite_count()
            )
            return proportion_dying
        else:
            return 0.0

    def get_col_pollen(self):
        """Get colony pollen amount in grams."""
        return self.resources.get_pollen_quantity()

    def get_pollen_pest_conc(self):
        """Get pollen pesticide concentration in ug/g."""
        return self.resources.get_pollen_pesticide_concentration() * 1000000.0

    def get_col_nectar(self):
        """Get colony nectar amount in grams."""
        return self.resources.get_nectar_quantity()

    def get_nectar_pest_conc(self):
        """Get nectar pesticide concentration in ug/g."""
        return self.resources.get_nectar_pesticide_concentration() * 1000000.0

    # Pesticide-specific death getters (to match C++ output behavior)
    def get_dead_drone_larvae_pesticide(self):
        """Get number of drone larvae killed by pesticide."""
        return getattr(self, "m_dead_drone_larvae_pesticide", 0)

    def get_dead_worker_larvae_pesticide(self):
        """Get number of worker larvae killed by pesticide."""
        return getattr(self, "m_dead_worker_larvae_pesticide", 0)

    def get_dead_drone_adults_pesticide(self):
        """Get number of drone adults killed by pesticide."""
        return getattr(self, "m_dead_drone_adults_pesticide", 0)

    def get_dead_worker_adults_pesticide(self):
        """Get number of worker adults killed by pesticide."""
        return getattr(self, "m_dead_worker_adults_pesticide", 0)

    def get_dead_foragers_pesticide(self):
        """Get number of foragers killed by pesticide."""
        return getattr(self, "m_dead_foragers_pesticide", 0)

    def get_queen_strength(self):
        """Get the queen strength."""
        return self.queen.get_strength() if self.queen else 0.0

    def get_dd_lower(self):
        """Get the lower degree day value."""
        return self.get_dd_today_lower()

    def get_l_lower(self):
        """Get the lower L value."""
        return self.get_l_today_lower()

    def get_n_lower(self):
        """Get the lower N value."""
        return self.get_n_today_lower()

    def set_mite_pct_resistance(self, pct):
        self.m_InitMitePctResistant = pct

    def set_vt_enable(self, value):
        self.m_vt_enable = value

    def initialize_colony(self):
        # CRITICAL FIX: Set lengths of the various lists before initializing bees
        # This matches the C++ CColony::InitializeColony() logic
        self.deggs.set_length(EGGLIFE)
        self.deggs.set_prop_transition(1.0)
        self.weggs.set_length(EGGLIFE)
        self.weggs.set_prop_transition(1.0)
        self.dlarv.set_length(DLARVLIFE)
        self.dlarv.set_prop_transition(1.0)
        self.wlarv.set_length(WLARVLIFE)
        self.wlarv.set_prop_transition(1.0)
        self.capdrn.set_length(DBROODLIFE)
        self.capdrn.set_prop_transition(1.0)
        self.capwkr.set_length(WBROODLIFE)
        self.capwkr.set_prop_transition(1.0)
        self.dadl.set_length(DADLLIFE)
        self.dadl.set_prop_transition(1.0)
        self.wadl.set_length(WADLLIFE)
        self.wadl.set_prop_transition(1.0)
        self.wadl.set_colony(self)
        self.foragers.set_length(self.m_CurrentForagerLifespan)
        self.foragers.set_colony(self)

        self.initialize_bees()
        self.initialize_mites()
        # Set pesticide Dose rate to 0
        if self.m_epadata:
            for attr in [
                "m_D_L4",
                "m_D_L5",
                "m_D_LD",
                "m_D_A13",
                "m_D_A410",
                "m_D_A1120",
                "m_D_AD",
                "m_D_C_Foragers",
                "m_D_D_Foragers",
                "m_D_L4_Max",
                "m_D_L5_Max",
                "m_D_LD_Max",
                "m_D_A13_Max",
                "m_D_A410_Max",
                "m_D_A1120_Max",
                "m_D_AD_Max",
                "m_D_C_Foragers_Max",
                "m_D_D_Foragers_Max",
            ]:
                setattr(self.m_epadata, attr, 0)
        # Set resources
        if self.resources:
            self.resources.initialize(
                self.m_ColonyPolInitAmount, self.m_ColonyNecInitAmount
            )
        if self.m_SuppPollen:
            self.m_SuppPollen.m_CurrentAmount = self.m_SuppPollen.m_StartingAmount
        if self.m_SuppNectar:
            self.m_SuppNectar.m_CurrentAmount = self.m_SuppNectar.m_StartingAmount
        # Set pesticide mortality trackers to zero
        self.m_dead_worker_larvae_pesticide = 0
        self.m_dead_drone_larvae_pesticide = 0
        self.m_dead_worker_adults_pesticide = 0
        self.m_dead_drone_adults_pesticide = 0
        self.m_dead_foragers_pesticide = 0
        self.m_colony_event_list.clear()
        # Nutrient contamination table logic (if enabled)
        # Note: In Python version, contamination table is loaded via set_contamination_table method
        # rather than loading from file during initialization
        if (
            self.m_nutrient_ct
            and getattr(self.m_nutrient_ct, "is_enabled", lambda: False)()
        ):
            # Contamination table is already loaded via set_contamination_table
            pass
        # Set initial state of AdultAgingDelayArming
        if self.m_p_session:
            monthnum = self.m_p_session.get_sim_start().month
            # Ported logic for arming AdultAgingDelay
            # Set armed if the first date is January or February (C++: if ((monthnum >= 1) && (monthnum < 3)))
            if 1 <= monthnum < 3:
                self.adult_aging_delay_armed = True
            else:
                self.adult_aging_delay_armed = False
        self.has_been_initialized = True

    def add_event_notification(self, date_stg, msg):
        event_string = f"{date_stg}: {msg}"
        if self.m_p_session and self.m_p_session.is_info_reporting_enabled():
            self.m_colony_event_list.append(event_string)

    def get_day_num_date(self, day_num):
        # Returns a date object for the given simulation day number
        if not self.m_p_session:
            return None
        sim_start = self.m_p_session.get_sim_start()
        # Use timedelta to add days to datetime object
        return sim_start + timedelta(days=day_num - 1)

    def kill_colony(self):
        # Set queen strength to 1 (minimum)
        if self.queen:
            self.queen.set_strength(1)
        # Kill all bee lists (attributes must be set elsewhere)
        for attr in [
            "deggs",
            "weggs",
            "dlarv",
            "wlarv",
            "capdrn",
            "capwkr",
            "dadl",
            "wadl",
            "foragers",
        ]:
            bee_list = getattr(self, attr, None)
            if bee_list:
                bee_list.kill_all()
        if hasattr(self, "foragers"):
            self.foragers.clear_pending_foragers()

    def create(self):
        self.clear()  # Clear all lists in case they have been built already

        # Set lengths and prop transitions for all bee lists
        self.deggs.set_length(EGGLIFE)
        self.deggs.set_prop_transition(1.0)
        self.weggs.set_length(EGGLIFE)
        self.weggs.set_prop_transition(1.0)
        self.dlarv.set_length(DLARVLIFE)
        self.dlarv.set_prop_transition(1.0)
        self.wlarv.set_length(WLARVLIFE)
        self.wlarv.set_prop_transition(1.0)
        self.capdrn.set_length(DBROODLIFE)
        self.capdrn.set_prop_transition(1.0)
        self.capwkr.set_length(WBROODLIFE)
        self.capwkr.set_prop_transition(1.0)
        self.dadl.set_length(DADLLIFE)
        self.dadl.set_prop_transition(1.0)
        self.wadl.set_length(WADLLIFE)
        self.wadl.set_prop_transition(1.0)

        # Set colony reference for lists that need it
        if hasattr(self.wadl, "set_colony"):
            self.wadl.set_colony(self)
        if hasattr(self.foragers, "set_length"):
            self.foragers.set_length(
                getattr(self, "m_init_cond", None).m_ForagerLifespan
                if hasattr(self, "m_init_cond")
                else 12
            )
        if hasattr(self.foragers, "set_colony"):
            self.foragers.set_colony(self)

        # Remove any current list boxcars in preparation for new initialization
        self.set_default_init_conditions()

    def clear(self):
        # Clear all lists and simulation state
        for attr in [
            "deggs",
            "weggs",
            "dlarv",
            "wlarv",
            "capdrn",
            "capwkr",
            "dadl",
            "wadl",
            "foragers",
        ]:
            bee_list = getattr(self, attr, None)
            if bee_list:
                bee_list.kill_all()
        self.m_colony_event_list.clear()

    def is_adult_aging_delay_active(self):
        """
        Returns True if adult aging delay is active (CColony::IsAdultAgingDelayActive).
        Logic matches C++ implementation exactly.
        """
        # C++ logic: First check if armed and handle disarming
        egg_quant_threshold = self.get_adult_aging_delay_egg_threshold()

        if self.is_adult_aging_delay_armed():
            if self.queen.get_teggs() > egg_quant_threshold:
                self.set_adult_aging_delay_armed(
                    False
                )  # Disarm when eggs exceed threshold
                self.m_days_since_egg_laying_began = 0  # Reset counter

        # C++ logic: active = ((m_DaysSinceEggLayingBegan++ < m_AdultAgeDelayLimit) && !IsAdultAgingDelayArmed());
        active = (
            self.m_days_since_egg_laying_began < self.m_adult_age_delay_limit
        ) and not self.is_adult_aging_delay_armed()
        self.m_days_since_egg_laying_began += 1  # Increment counter (C++ does ++)

        return active

    def set_default_init_conditions(self):
        """
        Sets default initial conditions for the colony (CColony::SetDefaultInitConditions).
        Resets bee lists and initial state variables.
        """
        # Reset bee lists
        for bee_list in [
            self.deggs,
            self.weggs,
            self.dlarv,
            self.wlarv,
            self.capdrn,
            self.capwkr,
            self.dadl,
            self.wadl,
            self.foragers,
        ]:
            if hasattr(bee_list, "clear"):
                bee_list.clear()
        # Reset initial conditions
        self.m_days_since_egg_laying_began = self.m_adult_age_delay_limit
        self.adult_aging_delay_armed = False
        self.m_dead_worker_larvae_pesticide = 0
        self.m_dead_drone_larvae_pesticide = 0
        self.m_dead_worker_adults_pesticide = 0
        self.m_dead_drone_adults_pesticide = 0
        self.m_dead_foragers_pesticide = 0
        self.m_colony_event_list.clear()
        # Optionally reset other state variables as needed

    def initialize_bees(self):
        """
        Ported from CColony::InitializeBees.
        Distributes bees from initial conditions into age groupings (boxcars) for each type.
        """
        # Set current forager lifespan and adult aging delay
        self.m_CurrentForagerLifespan = self.m_init_cond.m_ForagerLifespan
        self.m_days_since_egg_laying_began = self.m_adult_age_delay_limit

        # Initialize Queen
        self.queen.set_strength(self.m_init_cond.m_QueenStrength)

        # CRITICAL: Set forager length again to match C++ InitializeBees() exactly
        # This is needed because m_CurrentForagerLifespan may have changed from initial conditions
        self.foragers.set_length(self.m_CurrentForagerLifespan)
        self.foragers.set_colony(self)

        # Helper to distribute bees into boxcars
        def distribute_bees(init_count, bee_list, bee_class):
            boxcar_len = bee_list.get_length()
            if boxcar_len == 0:
                return
            avg = init_count // boxcar_len
            remainder = init_count - avg * boxcar_len
            for i in range(boxcar_len):
                count = avg if i < (boxcar_len - 1) else avg + remainder
                bee = bee_class(count)
                bee_list.add_head(bee)

        # Eggs
        distribute_bees(
            self.m_init_cond.m_droneEggsField, self.deggs, self.deggs.get_bee_class()
        )
        distribute_bees(
            self.m_init_cond.m_workerEggsField, self.weggs, self.weggs.get_bee_class()
        )

        # Larvae
        distribute_bees(
            self.m_init_cond.m_droneLarvaeField, self.dlarv, self.dlarv.get_bee_class()
        )
        distribute_bees(
            self.m_init_cond.m_workerLarvaeField, self.wlarv, self.wlarv.get_bee_class()
        )

        # Capped Brood
        distribute_bees(
            self.m_init_cond.m_droneBroodField, self.capdrn, self.capdrn.get_bee_class()
        )
        distribute_bees(
            self.m_init_cond.m_workerBroodField,
            self.capwkr,
            self.capwkr.get_bee_class(),
        )

        # Drone Adults
        boxcar_len = self.dadl.get_length()
        avg = self.m_init_cond.m_droneAdultsField // boxcar_len if boxcar_len else 0
        remainder = (
            self.m_init_cond.m_droneAdultsField - avg * boxcar_len if boxcar_len else 0
        )
        for i in range(boxcar_len):
            count = avg if i < (boxcar_len - 1) else avg + remainder
            drone = self.dadl.get_bee_class()(count)
            drone.set_lifespan(DADLLIFE)
            self.dadl.add_head(drone)

        # Worker Adults and Foragers
        total_boxcars = self.wadl.get_length() + self.foragers.get_length()
        avg = (
            self.m_init_cond.m_workerAdultsField // total_boxcars
            if total_boxcars
            else 0
        )
        remainder = (
            self.m_init_cond.m_workerAdultsField - avg * total_boxcars
            if total_boxcars
            else 0
        )
        for i in range(self.wadl.get_length()):
            worker = self.wadl.get_bee_class()(avg)
            worker.set_lifespan(WADLLIFE)
            self.wadl.add_head(worker)
        for i in range(self.foragers.get_length()):
            count = avg if i < (self.foragers.get_length() - 1) else avg + remainder
            forager = self.foragers.get_bee_class()(count)
            forager.set_lifespan(self.foragers.get_length())
            self.foragers.add_head(forager)

        # Set queen day one and egg laying delay
        self.queen.set_day_one(1)
        self.queen.set_egg_laying_delay(0)

    def get_colony_size(self):
        """
        Returns the total colony size (CColony::GetColonySize).
        Sum of drone adults, worker adults, and foragers.
        """
        return int(
            self.dadl.get_quantity()
            + self.wadl.get_quantity()
            + self.foragers.get_quantity()
        )

    def update_bees(self, event, day_num):
        """
        Ported from CColony::UpdateBees.
        Updates bee lists and colony state for the current day.
        """
        # Calculate larvae per bee
        total_larvae = self.wlarv.get_quantity() + self.dlarv.get_quantity()
        total_adults = (
            self.wadl.get_quantity()
            + self.dadl.get_quantity()
            + self.foragers.get_quantity()
        )
        # Match C++ behavior - division by zero produces large value that triggers larv_per_bee > 2
        if total_adults == 0:
            larv_per_bee = float("inf")  # Match C++ division by zero behavior
        else:
            larv_per_bee = float(total_larvae) / total_adults

        # Arm Adult Aging Delay on Jan 1
        if event.get_time().month == 1 and event.get_time().day == 1:
            self.set_adult_aging_delay_armed(True)

        # Apply date range values
        date_stg = event.get_date_stg("%m/%d/%Y")
        the_date = event.parse_date(date_stg)
        if the_date:
            # Eggs Transition Rate
            prop_transition = self.m_init_cond.m_EggTransitionDRV.get_active_value(
                the_date
            )
            if (
                prop_transition is not None
                and self.m_init_cond.m_EggTransitionDRV.is_enabled()
            ):
                self.deggs.set_prop_transition(prop_transition / 100)
                self.weggs.set_prop_transition(prop_transition / 100)
            else:
                self.deggs.set_prop_transition(1.0)
                self.weggs.set_prop_transition(1.0)
            # Larvae Transition Rate
            prop_transition = self.m_init_cond.m_LarvaeTransitionDRV.get_active_value(
                the_date
            )
            if (
                prop_transition is not None
                and self.m_init_cond.m_LarvaeTransitionDRV.is_enabled()
            ):
                self.dlarv.set_prop_transition(prop_transition / 100)
                self.wlarv.set_prop_transition(prop_transition / 100)
            else:
                self.dlarv.set_prop_transition(1.0)
                self.wlarv.set_prop_transition(1.0)
            # Brood Transition Rate
            prop_transition = self.m_init_cond.m_BroodTransitionDRV.get_active_value(
                the_date
            )
            if (
                prop_transition is not None
                and self.m_init_cond.m_BroodTransitionDRV.is_enabled()
            ):
                self.capdrn.set_prop_transition(prop_transition / 100)
                self.capwkr.set_prop_transition(prop_transition / 100)
            else:
                self.capdrn.set_prop_transition(1.0)
                self.capwkr.set_prop_transition(1.0)
            # Adults Transition Rate
            prop_transition = self.m_init_cond.m_AdultTransitionDRV.get_active_value(
                the_date
            )
            if (
                prop_transition is not None
                and self.m_init_cond.m_AdultTransitionDRV.is_enabled()
            ):
                self.dadl.set_prop_transition(prop_transition / 100)
                self.wadl.set_prop_transition(prop_transition / 100)
            else:
                self.dadl.set_prop_transition(1.0)
                self.wadl.set_prop_transition(1.0)
            # Adults Lifespan Change
            adult_age_limit = self.m_init_cond.m_AdultLifespanDRV.get_active_value(
                the_date
            )
            if (
                adult_age_limit is not None
                and self.m_init_cond.m_AdultLifespanDRV.is_enabled()
            ):
                if self.wadl.get_length() != int(adult_age_limit):
                    self.wadl.update_length(int(adult_age_limit))
            else:
                if self.wadl.get_length() != WADLLIFE:
                    self.wadl.update_length(WADLLIFE)
            # Foragers Lifespan Change
            forager_lifespan = self.m_init_cond.m_ForagerLifespanDRV.get_active_value(
                the_date
            )
            if (
                forager_lifespan is not None
                and self.m_init_cond.m_ForagerLifespanDRV.is_enabled()
            ):
                self.m_CurrentForagerLifespan = int(forager_lifespan)
            else:
                self.m_CurrentForagerLifespan = self.m_init_cond.m_ForagerLifespan
            self.foragers.set_length(self.m_CurrentForagerLifespan)
        else:
            self.deggs.set_prop_transition(1.0)
            self.weggs.set_prop_transition(1.0)
            self.dlarv.set_prop_transition(1.0)
            self.wlarv.set_prop_transition(1.0)
            self.capdrn.set_prop_transition(1.0)
            self.capwkr.set_prop_transition(1.0)
            self.dadl.set_prop_transition(1.0)
            self.wadl.set_prop_transition(1.0)

        # Reset output data struct for algorithm intermediate results
        self.m_InOutEvent.reset()

        # Queen lays eggs
        self.queen.lay_eggs(
            day_num,
            event.get_temp(),
            event.get_daylight_hours(),
            self.foragers.get_quantity(),
            larv_per_bee,
        )

        # Simulate cold storage
        cold_storage = self.get_cold_storage_simulator()
        today = event.get_date_stg()
        if cold_storage.is_enabled():
            cs_state_stg = f"On {today} Cold Storage is ENABLED"
            cold_storage.update(event, self)
            if cold_storage.is_active_now():
                cs_state_stg += " and ACTIVE"
            if cold_storage.is_starting_now():
                cs_state_stg += " and STARTING"
            if cold_storage.is_ending_now():
                cs_state_stg += "and ENDING"
            if cold_storage.is_on():
                cs_state_stg += " and ON"
            if self.m_p_session.is_info_reporting_enabled():
                self.m_p_session.add_to_info_list(cs_state_stg)

        l_DEggs = Egg(self.queen.get_deggs())
        l_WEggs = Egg(self.queen.get_weggs())

        # At the beginning of cold storage all eggs are lost
        if cold_storage.is_starting_now():
            if self.m_p_session.is_info_reporting_enabled():
                self.m_p_session.add_to_info_list(
                    f"On {today} Cold Storage is STARTING"
                )
            l_DEggs.set_number(0)
            l_WEggs.set_number(0)
            self.deggs.kill_all()
            self.weggs.kill_all()

        # Update stats for new eggs
        self.m_InOutEvent.m_NewWEggs = l_WEggs.get_number()
        self.m_InOutEvent.m_NewDEggs = l_DEggs.get_number()

        self.deggs.update(l_DEggs)
        self.weggs.update(l_WEggs)

        # At the beginning of cold storage no eggs become larvae
        if cold_storage.is_starting_now():
            self.weggs.get_caboose().reset()
            self.deggs.get_caboose().reset()

        # Update stats for new larvae
        self.m_InOutEvent.m_WEggsToLarv = self.weggs.get_caboose().get_number()
        self.m_InOutEvent.m_DEggsToLarv = self.deggs.get_caboose().get_number()

        self.dlarv.update(self.deggs.get_caboose())
        self.wlarv.update(self.weggs.get_caboose())

        # At the beginning of cold storage no larvae become brood
        if cold_storage.is_starting_now():
            self.wlarv.get_caboose().reset()
            self.dlarv.get_caboose().reset()
            self.wlarv.kill_all()
            self.dlarv.kill_all()

        # Update stats for new brood
        self.m_InOutEvent.m_WLarvToBrood = self.wlarv.get_caboose().get_number()
        self.m_InOutEvent.m_DLarvToBrood = self.dlarv.get_caboose().get_number()

        self.capdrn.update(self.dlarv.get_caboose())
        self.capwkr.update(self.wlarv.get_caboose())

        # Update stats for new adults
        self.m_InOutEvent.m_WBroodToAdult = self.capwkr.get_caboose().get_number()
        self.m_InOutEvent.m_DBroodToAdult = self.capdrn.get_caboose().get_number()

        number_of_non_adults = (
            self.wlarv.get_quantity()
            + self.dlarv.get_quantity()
            + self.capdrn.get_quantity()
            + self.capwkr.get_quantity()
        )

        # ForageInc validity
        global_options = GlobalOptions.get()
        forage_inc_is_valid = (
            global_options.should_forage_day_election_based_on_temperatures
            or event.get_forage_inc() > 0.0
        )

        if (number_of_non_adults > 0) or (
            event.is_forage_day() and forage_inc_is_valid
        ):
            # Foragers killed due to pesticide
            foragers_to_be_killed = self.quantity_pesticide_to_kill(
                self.foragers,
                self.m_epadata.m_D_C_Foragers,
                0,
                self.m_epadata.m_AI_AdultLD50_Contact,
                self.m_epadata.m_AI_AdultSlope_Contact,
            )
            foragers_to_be_killed += self.quantity_pesticide_to_kill(
                self.foragers,
                self.m_epadata.m_D_D_Foragers,
                0,
                self.m_epadata.m_AI_AdultLD50,
                self.m_epadata.m_AI_AdultSlope,
            )
            min_age_to_forager = 14
            self.wadl.move_to_end(foragers_to_be_killed, min_age_to_forager)
            if foragers_to_be_killed > 0:
                notification = f"{foragers_to_be_killed} Foragers killed by pesticide - recruiting workers"
                self.add_event_notification(
                    event.get_date_stg("%m/%d/%Y"), notification
                )
            self.m_InOutEvent.m_ForagersKilledByPesticide = foragers_to_be_killed

            # Aging adults
            aging_adults = not cold_storage.is_active_now() and (
                not global_options.should_adults_age_based_laid_eggs
                or self.queen.compute_L(event.get_daylight_hours()) > 0
            )
            if self.is_adult_aging_delay_active():
                pass  # Corresponds to C++: CString stgDate = pEvent->GetDateStg();
            aging_adults = (
                aging_adults
                and not self.is_adult_aging_delay_active()
                and not self.is_adult_aging_delay_armed()
            )
            if aging_adults:
                self.dadl.update(self.capdrn.get_caboose(), self, event, False)
                wkr_adl_caboose_number = self.wadl.get_caboose().get_number()
                self.wadl.update(self.capwkr.get_caboose(), self, event, True)
                drn_number_from_caboose = self.capwkr.get_caboose().get_number()
                wkr_adl_caboose_number = self.wadl.get_caboose().get_number()
                self.m_InOutEvent.m_WAdultToForagers = (
                    self.wadl.get_caboose().get_number()
                )
                self.foragers.update(self.wadl.get_caboose(), self, event)
            else:
                if (
                    number_of_non_adults > 0
                    and global_options.should_adults_age_based_laid_eggs
                ):
                    self.dadl.add(self.capdrn.get_caboose(), self, event, False)
                    self.wadl.add(self.capwkr.get_caboose(), self, event, True)
                self.m_InOutEvent.m_WAdultToForagers = 0
                reset_adult = self.dadl.get_bee_class()()  # CAdult reset
                reset_adult.reset()
                self.foragers.update(reset_adult, self, event)
            self.m_InOutEvent.m_DeadForagers = (
                self.foragers.get_caboose().get_number()
                if self.foragers.get_caboose().get_number() > 0
                else 0
            )

        # Apply pesticide mortality impacts
        self.consume_food(event, day_num)
        self.determine_foliar_dose(day_num)
        self.apply_pesticide_mortality()

    def get_eggs_today(self):
        # Returns the total eggs today (worker + drone) from Queen
        return self.queen.get_teggs()

    def get_dd_today(self):
        # Returns DD value for today from Queen
        return self.queen.get_DD()

    def get_daylight_hrs_today(self, event=None):
        # Returns daylight hours for today from Queen
        return self.queen.get_L()

    def get_l_today(self):
        # Returns L value for today from Queen
        return self.queen.get_L()

    def get_n_today(self):
        # Returns N value for today from Queen
        return self.queen.get_N()

    def get_p_today(self):
        # Returns P value for today from Queen
        return self.queen.get_P()

    def get_dd_today_lower(self):
        # Returns dd value for today (lowercase) from Queen
        return self.queen.get_dd()

    def get_l_today_lower(self):
        # Returns l value for today (lowercase) from Queen
        return self.queen.get_l()

    def get_n_today_lower(self):
        # Returns n value for today (lowercase) from Queen
        return self.queen.get_n()

    def add_mites(self, new_mites):
        # Assume new mites are "virgins" (port of CColony::AddMites)
        virgins = self.run_mite * self.prop_rm_virgins + new_mites
        self.run_mite += new_mites
        if self.run_mite.get_total() <= 0:
            self.prop_rm_virgins = 1.0
        else:
            total_run = self.run_mite.get_total()
            # avoid division by zero though handled above
            self.prop_rm_virgins = (
                virgins.get_total() / total_run if total_run > 0 else 1.0
            )
        # Constrain proportion to be [0..1]
        if self.prop_rm_virgins > 1.0:
            self.prop_rm_virgins = 1.0
        if self.prop_rm_virgins < 0.0:
            self.prop_rm_virgins = 0.0

    def initialize_mites(self):
        # Initial condition infestation of capped brood (port of CColony::InitializeMites)
        w_count = int(
            (self.capwkr.get_quantity() * self.m_init_cond.m_workerBroodInfestField)
            / 100.0
        )
        d_count = int(
            (self.capdrn.get_quantity() * self.m_init_cond.m_droneBroodInfestField)
            / 100.0
        )
        w_mites = Mite(0, w_count)
        d_mites = Mite(0, d_count)
        # Distribute mites into capped brood
        self.capwkr.distribute_mites(w_mites)
        self.capdrn.distribute_mites(d_mites)

        # Initial condition mites on adult bees i.e. Running Mites
        run_w_count = int(
            (
                self.wadl.get_quantity() * self.m_init_cond.m_workerAdultInfestField
                + self.foragers.get_quantity()
                * self.m_init_cond.m_workerAdultInfestField
            )
            / 100.0
        )
        run_d_count = int(
            (self.dadl.get_quantity() * self.m_init_cond.m_droneAdultInfestField)
            / 100.0
        )
        run_mite_w = Mite(0, run_w_count)
        run_mite_d = Mite(0, run_d_count)

        self.run_mite = run_mite_d + run_mite_w

        self.prop_rm_virgins = 1.0

        self.m_mites_dying_today = 0.0
        self.m_mites_dying_this_period = 0.0

    def update_mites(self, event, day_num):
        # Port of CColony::UpdateMites
        #
        # Assume UpdateMites is called after UpdateBees.  This means the
        # last Larva boxcar has been moved to the first Brood boxcar and the last
        # Brood boxcar has been moved to the first Adult boxcar.  Therefore, we infest
        # the first Brood boxcar with mites and we have mites emerging from the
        # first boxcar in the appropriate Adult list.
        #
        # The proportion of running mites that have not infested before (prop_rm_virgins)
        # is maintained and updated each day. Mites with that proportion infest each day
        # and the proportion is updated at the end of this function.

        # Reset today's mite death counter
        self.m_mites_dying_today = 0.0

        # The cells being infested this cycle are the head (index 0) of capped brood lists
        WkrBrood = (
            self.capwkr.bees[0]
            if getattr(self.capwkr, "bees", None) and len(self.capwkr.bees) > 0
            else None
        )
        DrnBrood = (
            self.capdrn.bees[0]
            if getattr(self.capdrn, "bees", None) and len(self.capdrn.bees) > 0
            else None
        )

        if WkrBrood is None:
            # Nothing to do without brood
            return
        if DrnBrood is None:
            # create an empty brood-like object for math, fallback
            class _EmptyBrood:
                def get_number(self):
                    return 0

            DrnBrood = _EmptyBrood()

        # Calculate proportion of RunMites that can invade cells (per Calis)
        B = self.get_colony_size() * 0.125  # Weight in grams of colony
        if B > 0.0:
            rD = 6.49 * (DrnBrood.get_number() / B)
            rW = 0.56 * (WkrBrood.get_number() / B)
            I = 1 - math.exp(-(rD + rW))
            if I < 0.0:
                I = 0.0
        else:
            I = 0.0

        # WMites = RunMite * (I * PROPINFSTW)
        WMites = self.run_mite * (I * PROPINFSTW)

        # Likelihood of finding drone cell
        if WkrBrood.get_number() > 0:
            Likelihood = float(DrnBrood.get_number()) / float(WkrBrood.get_number())
            if Likelihood > 1.0:
                Likelihood = 1.0
        else:
            Likelihood = 1.0

        # DMites = RunMite * (I * PROPINFSTD * Likelihood)
        DMites = self.run_mite * (I * PROPINFSTD * Likelihood)

        # If no worker targets, send WMites to drone candidates
        if WkrBrood.get_number() == 0:
            DMites += WMites
            WMites.set_resistant(0)
            WMites.set_non_resistant(0)

        # OverflowLikelihood = RunMite * (I * PROPINFSTD * (1.0 - Likelihood));
        OverflowLikelihood = self.run_mite * (I * PROPINFSTD * (1.0 - Likelihood))
        # Preserve pct resistant of DMites
        try:
            OverflowLikelihood.set_pct_resistant(DMites.get_pct_resistant())
        except Exception:
            pass

        # Determine if too many mites/drone cell. If so send excess to worker cells
        OverflowMax = Mite(0, 0)
        max_allowed = MAXMITES_PER_DRONE_CELL * DrnBrood.get_number()
        if DMites.get_total() > max_allowed:
            # Don't truncate to int - preserve floating point precision like C++
            overflow_count = DMites.get_total() - max_allowed
            OverflowMax = Mite(0, overflow_count)
            try:
                OverflowMax.set_pct_resistant(DMites.get_pct_resistant())
            except Exception:
                pass
            # DMites -= OverflowMax
            DMites = DMites - OverflowMax

        # Add overflow mites to those available to infest worker brood
        WMites = WMites + OverflowMax + OverflowLikelihood

        # Limit worker mites per cell
        max_w = MAXMITES_PER_WORKER_CELL * WkrBrood.get_number()
        if WMites.get_total() > max_w:
            pr = WMites.get_pct_resistant()
            # Don't truncate to int - preserve floating point precision like C++
            WMites = Mite(0, max_w)
            try:
                WMites.set_pct_resistant(pr)
            except Exception:
                pass

        # Remove the mites used to infest from running mites
        self.run_mite = self.run_mite - WMites - DMites
        if self.run_mite.get_total() < 0:
            self.run_mite = Mite(0, 0)

        # Assign mites to the brood head and set prop virgins
        WkrBrood.set_mites(WMites)
        if hasattr(WkrBrood, "set_prop_virgins"):
            WkrBrood.set_prop_virgins(self.prop_rm_virgins)
        DrnBrood.set_mites(DMites)
        if hasattr(DrnBrood, "set_prop_virgins"):
            DrnBrood.set_prop_virgins(self.prop_rm_virgins)

        # Emerging mites from first adult boxcar
        # Prepare emerge records - USE BROOD OBJECTS LIKE C++
        WkrHead = (
            self.wadl.bees[0]
            if getattr(self.wadl, "bees", None) and len(self.wadl.bees) > 0
            else None
        )
        DrnHead = (
            self.dadl.bees[0]
            if getattr(self.dadl, "bees", None) and len(self.dadl.bees) > 0
            else None
        )

        # Use actual Brood objects like C++ CBrood WkrEmerge; CBrood DrnEmerge;
        WkrEmerge = Brood()
        DrnEmerge = Brood()

        if WkrHead:
            WkrEmerge.number = int(WkrHead.get_number())  # Ensure integer type
            WkrEmerge.set_prop_virgins(
                WkrHead.get_prop_virgins()
                if hasattr(WkrHead, "get_prop_virgins")
                else 0.0
            )
            if WkrHead.have_mites_been_counted():
                WkrEmerge.mites = Mite(0, 0)
            else:
                m = WkrHead.get_mites() if hasattr(WkrHead, "get_mites") else 0
                if isinstance(m, Mite):
                    WkrEmerge.mites = m
                else:
                    # Don't truncate to int - preserve floating point precision like C++
                    WkrEmerge.mites = Mite(0, m)
                WkrHead.set_mites_counted(True)

        if DrnHead:
            DrnEmerge.number = int(DrnHead.get_number())  # Ensure integer type
            DrnEmerge.set_prop_virgins(
                DrnHead.get_prop_virgins()
                if hasattr(DrnHead, "get_prop_virgins")
                else 0.0
            )
            if DrnHead.have_mites_been_counted():
                DrnEmerge.mites = Mite(0, 0)
            else:
                m = DrnHead.get_mites() if hasattr(DrnHead, "get_mites") else 0
                if isinstance(m, Mite):
                    DrnEmerge.mites = m
                else:
                    # Don't truncate to int - preserve floating point precision like C++
                    DrnEmerge.mites = Mite(0, m)
                DrnHead.set_mites_counted(True)

        # Mites per cell - USE DIRECT ACCESS LIKE C++
        MitesPerCellW = (
            WkrEmerge.mites.get_total() / WkrEmerge.number
            if WkrEmerge.number > 0
            else 0.0
        )
        MitesPerCellD = (
            DrnEmerge.mites.get_total() / DrnEmerge.number
            if DrnEmerge.number > 0
            else 0.0
        )

        # Survivorship
        PropSurviveMiteW = self.m_init_cond.m_workerMiteSurvivorship / 100.0
        PropSurviveMiteD = self.m_init_cond.m_droneMiteSurvivorshipField / 100.0

        # Reproduction rates per mite per cell
        if MitesPerCellW <= 1.0:
            ReproMitePerCellW = self.m_init_cond.m_workerMiteOffspring
        else:
            ReproMitePerCellW = (1.15 * MitesPerCellW) - (
                0.233 * MitesPerCellW * MitesPerCellW
            )
        if ReproMitePerCellW < 0:
            ReproMitePerCellW = 0.0

        if MitesPerCellD <= 2.0:
            ReproMitePerCellD = self.m_init_cond.m_droneMiteOffspringField
        else:
            ReproMitePerCellD = (
                1.734
                - (0.0755 * MitesPerCellD)
                - (0.0069 * MitesPerCellD * MitesPerCellD)
            )
        if ReproMitePerCellD < 0:
            ReproMitePerCellD = 0.0

        PROPRUNMITE2 = 0.6

        SurviveMitesW = WkrEmerge.mites * PropSurviveMiteW
        SurviveMitesD = DrnEmerge.mites * PropSurviveMiteD

        NumEmergingMites = SurviveMitesW.get_total() + SurviveMitesD.get_total()

        NewMitesW = SurviveMitesW * ReproMitePerCellW
        NewMitesD = SurviveMitesD * ReproMitePerCellD

        # Only mites which hadn't previously infested can survive to infest again.
        SurviveMitesW = SurviveMitesW * WkrEmerge.get_prop_virgins()
        SurviveMitesD = SurviveMitesD * DrnEmerge.get_prop_virgins()

        NumVirgins = SurviveMitesW.get_total() + SurviveMitesD.get_total()

        RunMiteVirgins = self.run_mite * self.prop_rm_virgins
        RunMiteW = NewMitesW + (SurviveMitesW * PROPRUNMITE2)
        RunMiteD = NewMitesD + (SurviveMitesD * PROPRUNMITE2)

        # Mites dying today are the number which originally emerged from brood minus the ones that eventually became running mites
        self.m_mites_dying_today = (
            WkrEmerge.mites.get_total() + DrnEmerge.mites.get_total()
        )
        self.m_mites_dying_today = max(0.0, self.m_mites_dying_today)

        # Add new running mites
        self.run_mite = self.run_mite + RunMiteD + RunMiteW

        # Update proportion of virgins
        if self.run_mite.get_total() <= 0:
            self.prop_rm_virgins = 1.0
        else:
            numerator = (
                RunMiteVirgins.get_total()
                + NewMitesW.get_total()
                + NewMitesD.get_total()
            )
            self.prop_rm_virgins = (
                numerator / self.run_mite.get_total()
                if self.run_mite.get_total() > 0
                else 1.0
            )
            # Clamp
            if self.prop_rm_virgins > 1.0:
                self.prop_rm_virgins = 1.0
            if self.prop_rm_virgins < 0.0:
                self.prop_rm_virgins = 0.0

        # Kill NonResistant Running Mites if Treatment Enabled
        if self.m_vt_enable and hasattr(self.m_mite_treatment_info, "get_active_item"):
            the_date = self.get_day_num_date(day_num)
            the_item = None
            the_item = self.m_mite_treatment_info.get_active_item(the_date)
            has_item = the_item is not None
            if has_item and the_item:
                Quan = self.run_mite.get_total()
                # Reduce non-resistant proportion
                if hasattr(self.run_mite, "get_non_resistant") and hasattr(
                    self.run_mite, "set_non_resistant"
                ):
                    new_nonres = (
                        self.run_mite.get_non_resistant()
                        * (100.0 - the_item.pct_mortality)
                        / 100.0
                    )
                    self.run_mite.set_non_resistant(new_nonres)
                    self.m_mites_dying_today += Quan - self.run_mite.get_total()

        self.m_mites_dying_this_period += self.m_mites_dying_today

    def requeen_if_needed(
        self,
        sim_day_num,
        event,
        egg_laying_delay,
        wkr_drn_ratio,
        enable_requeen,
        scheduled,
        queen_strength,
        rq_once,
        requeen_date,
    ):
        """
        Port of CColony::ReQueenIfNeeded

        Two modes:
         - Scheduled: trigger on ReQueenDate (initial exact year match, subsequent annual matches)
         - Automatic: trigger when proportion of unfertilized (drone) eggs > 0.15 during Apr-Sep (months 4..9)

        When requeening occurs, a strength may be popped from m_RQQueenStrengthArray (if present).
        After requeening, egg laying is delayed by egg_laying_delay days (queen.requeen handles this).
        """
        applied_strength = queen_strength

        if not enable_requeen:
            return

        try:
            if scheduled == 0:
                # Scheduled re-queening:
                # initial: year, month, day must match
                # subsequent annual: year < current year and month/day match and rq_once != 0
                ev_time = event.get_time()
                try:
                    rd_year = requeen_date.year
                    rd_month = requeen_date.month
                    rd_day = requeen_date.day
                except Exception:
                    # If requeen_date doesn't expose year/month/day, bail out (no scheduled requeen)
                    return

                if (
                    rd_year == ev_time.year
                    and rd_month == ev_time.month
                    and rd_day == ev_time.day
                ) or (
                    (rd_year < ev_time.year)
                    and (rd_month == ev_time.month)
                    and (rd_day == ev_time.day)
                    and (rq_once != 0)
                ):
                    if self.m_RQQueenStrengthArray:
                        applied_strength = self.m_RQQueenStrengthArray.pop(0)
                    notification = f"Scheduled Requeening Occurred, Strength {applied_strength:5.1f}"
                    self.add_event_notification(
                        event.get_date_stg("%m/%d/%Y"), notification
                    )
                    self.queen.requeen(egg_laying_delay, applied_strength, sim_day_num)
            else:
                # Automatic re-queening
                month = event.get_time().month
                if (
                    (self.queen.get_prop_drone_eggs() > 0.15)
                    and (month > 3)
                    and (month < 10)
                ):
                    if self.m_RQQueenStrengthArray:
                        applied_strength = self.m_RQQueenStrengthArray.pop(0)
                    notification = f"Automatic Requeening Occurred, Strength {applied_strength:5.1f}"
                    self.add_event_notification(
                        event.get_date_stg("%m/%d/%Y"), notification
                    )
                    self.queen.requeen(egg_laying_delay, applied_strength, sim_day_num)
        except Exception:
            # On unexpected errors, do not requeen
            return

    # def set_miticide_treatment(self, start_day_num, duration, mortality, enable):
    #     pass

    # def set_miticide_treatment_from_treatments(self, treatments, enable):
    #     pass

    def set_spore_treatment(self, start_day_num, enable):
        # Port of CColony::SetSporeTreatment
        if enable:
            self.m_SPStart = start_day_num
            self.m_SPEnable = True
        else:
            self.m_SPEnable = False
        self.m_SPTreatmentActive = False

    def remove_drone_comb(self, pct):
        # Port of CColony::RemoveDroneComb
        # Simulates the removal of drone comb. The variable pct is the amount to be removed
        # possible bug: when multiplying by the percentages, likely need to divide by 100 to convert to fraction
        if pct > 100:
            pct = 100.0
        if pct < 0:
            pct = 0.0

        # Apply to drone eggs
        for egg in getattr(self.deggs, "bees", []):
            if hasattr(egg, "number"):
                egg.number *= int(
                    100.0 - pct
                )  # should this be *= (100.0 - pct) / 100.0 ?

        # Apply to drone larvae
        for larva in getattr(self.dlarv, "bees", []):
            if hasattr(larva, "number"):
                larva.number *= int(
                    100.0 - pct
                )  # should this be *= (100.0 - pct) / 100.0 ?

        # Apply to drone capped brood
        for brood in getattr(self.capdrn, "bees", []):
            if hasattr(brood, "number"):
                brood.number *= int(
                    100.0 - pct
                )  # should this be *= (100.0 - pct) / 100.0 ?
            if hasattr(brood, "mites"):
                # brood.m_Mites = brood.m_Mites * (100.0 - pct);
                if hasattr(brood.mites, "__mul__"):
                    # Follow C++ logic: mites multiplied by floating point, not int
                    brood.mites *= 100.0 - pct  # should this be (100.0 - pct) / 100 ??
            if hasattr(brood, "set_prop_virgins"):
                brood.set_prop_virgins(0.0)

    def add_discrete_event(self, date_stg, event_id):
        # Port of CColony::AddDiscreteEvent
        if date_stg in self.m_event_map:
            # Date already exists, add a new event to the array
            self.m_event_map[date_stg].append(event_id)
        else:
            # Create new map element
            self.m_event_map[date_stg] = [event_id]

    def remove_discrete_event(self, date_stg, event_id):
        # Port of CColony::RemoveDiscreteEvent
        if date_stg in self.m_event_map:
            # Date exists
            event_array = self.m_event_map[date_stg]
            # Remove all occurrences of event_id
            self.m_event_map[date_stg] = [x for x in event_array if x != event_id]

            if len(self.m_event_map[date_stg]) == 0:
                del self.m_event_map[date_stg]

    def get_discrete_events(self, key):
        # Port of CColony::GetDiscreteEvents
        # Returns the event array for the given key, or None if not found
        return self.m_event_map.get(key, None)

    def do_pending_events(self, weather_event, current_sim_day):
        # Port of CColony::DoPendingEvents
        # DoPendingEvents is used when running WebBeePop. The predefined events from a legacy program are
        # mapped into VarroaPop parameters and this is executed as part of the main simulation loop. A much
        # simplified set of features for use by elementary school students.

        event_array = self.get_discrete_events(weather_event.get_date_stg("%m/%d/%Y"))
        if not event_array:
            return

        for event_id in event_array:
            # TRACE("A Discrete Event on %s\n",pWeatherEvent->GetDateStg("%m/%d/%Y"));
            EggLayDelay = 17
            Strength = 5

            if event_id == DE_SWARM:  # Swarm
                self.add_event_notification(
                    weather_event.get_date_stg("%m/%d/%Y"),
                    "Detected SWARM Discrete Event",
                )
                if hasattr(self.foragers, "factor_quantity"):
                    self.foragers.factor_quantity(0.75)
                if hasattr(self.wadl, "factor_quantity"):
                    self.wadl.factor_quantity(0.75)
                if hasattr(self.dadl, "factor_quantity"):
                    self.dadl.factor_quantity(0.75)

            elif event_id == DE_CHALKBROOD:  # Chalk Brood
                # All Larvae Die
                self.add_event_notification(
                    weather_event.get_date_stg("%m/%d/%Y"),
                    "Detected CHALKBROOD Discrete Event",
                )
                if hasattr(self.dlarv, "factor_quantity"):
                    self.dlarv.factor_quantity(0.0)
                if hasattr(self.wlarv, "factor_quantity"):
                    self.wlarv.factor_quantity(0.0)

            elif event_id == DE_RESOURCEDEP:  # Resource Depletion
                # Forager Lifespan = minimum
                self.add_event_notification(
                    weather_event.get_date_stg("%m/%d/%Y"),
                    "Detected RESOURCEDEPLETION Discrete Event",
                )
                self.m_init_cond.m_ForagerLifespan = 4

            elif event_id == DE_SUPERCEDURE:  # Supercedure of Queen
                # New queen = 17 days before egg laying starts
                self.add_event_notification(
                    weather_event.get_date_stg("%m/%d/%Y"),
                    "Detected SUPERCEDURE Discrete Event",
                )
                if hasattr(self.queen, "requeen"):
                    self.queen.requeen(EggLayDelay, Strength, current_sim_day)

            elif event_id == DE_PESTICIDE:  # Death of foragers by pesticide
                # 25% of foragers die
                self.add_event_notification(
                    weather_event.get_date_stg("%m/%d/%Y"),
                    "Detected PESTICIDE Discrete Event",
                )
                if hasattr(self.foragers, "factor_quantity"):
                    self.foragers.factor_quantity(0.75)

    def get_mites_dying_today(self):
        # Port of CColony::GetMitesDyingToday
        return self.m_mites_dying_today

    def get_nurse_bees(self):
        # Port of CColony::GetNurseBees
        # Number of nurse bees is defined as # larvae/2. Implication is that a nurse bee is needed for each two larvae
        total_larvae = self.wlarv.get_quantity() + self.dlarv.get_quantity()
        return total_larvae // 2

    def get_total_mite_count(self):
        # Port of CColony::GetTotalMiteCount
        # return ( RunMite.GetTotal() + CapDrn.GetMiteCount() + CapWkr.GetMiteCount() );
        run_mite_total = (
            self.run_mite.get_total() if hasattr(self.run_mite, "get_total") else 0
        )
        capdrn_mites = (
            self.capdrn.get_mite_count()
            if hasattr(self.capdrn, "get_mite_count")
            else 0
        )
        capwkr_mites = (
            self.capwkr.get_mite_count()
            if hasattr(self.capwkr, "get_mite_count")
            else 0
        )
        return run_mite_total + capdrn_mites + capwkr_mites

    def set_start_sample_period(self):
        # Port of CColony::SetStartSamplePeriod
        # Notifies CColony that it is the beginning of a sample period. Since we gather either weekly or
        # daily data this is used to reset accumulators.
        self.m_mites_dying_this_period = 0.0

    def get_mites_dying_this_period(self):
        # Port of CColony::GetMitesDyingThisPeriod
        return self.m_mites_dying_this_period

    def apply_pesticide_mortality(self):
        """
        Port of CColony::ApplyPesticideMortality

        Applies pesticide mortality to different bee populations based on their current doses
        compared to previously seen maximum doses. Updates mortality tracking variables.

        Constraint:  Bee quantities are not reduced unless the current pesticide dose is > previous maximum dose.  But,
              for bees just getting into Larva4 or Adult1, this is the first time they have had a dose.

        """
        # Worker Larvae 4
        # if (m_EPAData.m_D_L4 > m_EPAData.m_D_L4_Max) // IED - only reduce if current dose greater than previous maximum dose
        # {
        self.m_dead_worker_larvae_pesticide = self.apply_pesticide_to_bees(
            self.wlarv,
            3,
            3,
            self.m_epadata.m_D_L4,
            0,
            self.m_epadata.m_AI_LarvaLD50,
            self.m_epadata.m_AI_LarvaSlope,
        )
        if self.m_epadata.m_D_L4 > self.m_epadata.m_D_L4_Max:
            self.m_epadata.m_D_L4_Max = self.m_epadata.m_D_L4
        # }

        # Worker Larvae 5
        if self.m_epadata.m_D_L5 > self.m_epadata.m_D_L5_Max:
            self.m_dead_worker_larvae_pesticide += self.apply_pesticide_to_bees(
                self.wlarv,
                4,
                4,
                self.m_epadata.m_D_L5,
                self.m_epadata.m_D_L5_Max,
                self.m_epadata.m_AI_LarvaLD50,
                self.m_epadata.m_AI_LarvaSlope,
            )
            self.m_epadata.m_D_L5_Max = self.m_epadata.m_D_L5

        # Drone Larvae
        self.m_dead_drone_larvae_pesticide = self.apply_pesticide_to_bees(
            self.dlarv,
            3,
            3,
            self.m_epadata.m_D_LD,
            0,
            self.m_epadata.m_AI_LarvaLD50,
            self.m_epadata.m_AI_LarvaSlope,
        )  # New L4 drones
        if self.m_epadata.m_D_LD > self.m_epadata.m_D_LD_Max:
            self.m_dead_drone_larvae_pesticide += self.apply_pesticide_to_bees(
                self.dlarv,
                4,
                DLARVLIFE - 1,
                self.m_epadata.m_D_LD,
                self.m_epadata.m_D_LD_Max,
                self.m_epadata.m_AI_LarvaLD50,
                self.m_epadata.m_AI_LarvaSlope,
            )
            self.m_epadata.m_D_LD_Max = self.m_epadata.m_D_LD

        # Worker Adults 1-3
        self.m_dead_worker_adults_pesticide = self.apply_pesticide_to_bees(
            self.wadl,
            0,
            0,
            self.m_epadata.m_D_A13,
            0,
            self.m_epadata.m_AI_AdultLD50,
            self.m_epadata.m_AI_AdultSlope,
        )  # New adults
        if self.m_epadata.m_D_A13 > self.m_epadata.m_D_A13_Max:
            self.m_dead_worker_adults_pesticide += self.apply_pesticide_to_bees(
                self.wadl,
                1,
                2,
                self.m_epadata.m_D_A13,
                self.m_epadata.m_D_A13_Max,
                self.m_epadata.m_AI_AdultLD50,
                self.m_epadata.m_AI_AdultSlope,
            )
            self.m_epadata.m_D_A13_Max = self.m_epadata.m_D_A13

        # Worker Adults 4-10
        if self.m_epadata.m_D_A410 > self.m_epadata.m_D_A410_Max:
            self.m_dead_worker_adults_pesticide += self.apply_pesticide_to_bees(
                self.wadl,
                3,
                9,
                self.m_epadata.m_D_A410,
                self.m_epadata.m_D_A410_Max,
                self.m_epadata.m_AI_AdultLD50,
                self.m_epadata.m_AI_AdultSlope,
            )
            self.m_epadata.m_D_A410_Max = self.m_epadata.m_D_A410

        # Worker Adults 11-20
        if self.m_epadata.m_D_A1120 > self.m_epadata.m_D_A1120_Max:
            self.m_dead_worker_adults_pesticide += self.apply_pesticide_to_bees(
                self.wadl,
                10,
                WADLLIFE - 1,
                self.m_epadata.m_D_A1120,
                self.m_epadata.m_D_A1120_Max,
                self.m_epadata.m_AI_AdultLD50,
                self.m_epadata.m_AI_AdultSlope,
            )
            self.m_epadata.m_D_A1120_Max = self.m_epadata.m_D_A1120

        # Worker Drones
        self.m_dead_drone_adults_pesticide = self.apply_pesticide_to_bees(
            self.dadl,
            0,
            0,
            self.m_epadata.m_D_AD,
            0,
            self.m_epadata.m_AI_AdultLD50,
            self.m_epadata.m_AI_AdultSlope,
        )
        if self.m_epadata.m_D_AD > self.m_epadata.m_D_AD_Max:
            self.m_dead_drone_adults_pesticide += self.apply_pesticide_to_bees(
                self.dadl,
                1,
                DADLLIFE - 1,
                self.m_epadata.m_D_AD,
                self.m_epadata.m_D_AD_Max,
                self.m_epadata.m_AI_AdultLD50,
                self.m_epadata.m_AI_AdultSlope,
            )
            self.m_epadata.m_D_AD_Max = self.m_epadata.m_D_AD

        # Foragers - Contact Mortality
        self.m_dead_foragers_pesticide = self.apply_pesticide_to_bees(
            self.foragers,
            0,
            0,
            self.m_epadata.m_D_C_Foragers,
            0,
            self.m_epadata.m_AI_AdultLD50_Contact,
            self.m_epadata.m_AI_AdultSlope_Contact,
        )
        if self.m_epadata.m_D_C_Foragers > self.m_epadata.m_D_C_Foragers_Max:
            # Use get_length() method if available, otherwise assume reasonable default
            forager_length = getattr(self.foragers, "get_length", lambda: 21)() - 1
            self.m_dead_foragers_pesticide += self.apply_pesticide_to_bees(
                self.foragers,
                1,
                forager_length,
                self.m_epadata.m_D_C_Foragers,
                self.m_epadata.m_D_C_Foragers_Max,
                self.m_epadata.m_AI_AdultLD50_Contact,
                self.m_epadata.m_AI_AdultSlope_Contact,
            )
            self.m_epadata.m_D_C_Foragers_Max = self.m_epadata.m_D_C_Foragers

        # Foragers - Diet Mortality
        self.m_dead_foragers_pesticide += self.apply_pesticide_to_bees(
            self.foragers,
            0,
            0,
            self.m_epadata.m_D_D_Foragers,
            0,
            self.m_epadata.m_AI_AdultLD50,
            self.m_epadata.m_AI_AdultSlope,
        )
        if self.m_epadata.m_D_D_Foragers > self.m_epadata.m_D_D_Foragers_Max:
            # Use get_length() method if available, otherwise assume reasonable default
            forager_length = getattr(self.foragers, "get_length", lambda: 21)() - 1
            self.m_dead_foragers_pesticide += self.apply_pesticide_to_bees(
                self.foragers,
                1,
                forager_length,
                self.m_epadata.m_D_D_Foragers,
                self.m_epadata.m_D_D_Foragers_Max,
                self.m_epadata.m_AI_AdultLD50,
                self.m_epadata.m_AI_AdultSlope,
            )
            self.m_epadata.m_D_D_Foragers_Max = self.m_epadata.m_D_D_Foragers

        if self.m_dead_foragers_pesticide > 0:
            # Debug breakpoint placeholder (equivalent to int i = 0; in C++)
            pass

        # Reset the current doses to zero after mortality is applied.
        self.m_epadata.m_D_L4 = 0
        self.m_epadata.m_D_L5 = 0
        self.m_epadata.m_D_LD = 0
        self.m_epadata.m_D_A13 = 0
        self.m_epadata.m_D_A410 = 0
        self.m_epadata.m_D_A1120 = 0
        self.m_epadata.m_D_AD = 0
        self.m_epadata.m_D_C_Foragers = 0
        self.m_epadata.m_D_D_Foragers = 0

    def quantity_pesticide_to_kill(self, bee_list, current_dose, max_dose, ld50, slope):
        """
        Port of CColony::QuantityPesticideToKill

        This just calculates the number of bees in the list that would be killed by the pesticide and dose.

        Args:
            bee_list: The bee list to calculate mortality for
            current_dose: Current pesticide dose
            max_dose: Previously seen maximum dose
            ld50: Lethal dose 50 value
            slope: Dose-response slope parameter

        Returns:
            Number of bees that would be killed by pesticide
        """
        bee_quant = bee_list.get_quantity()

        # Calculate dose response for current and maximum doses
        redux_current = self.m_epadata.dose_response(current_dose, ld50, slope)
        redux_max = self.m_epadata.dose_response(max_dose, ld50, slope)

        # Less than max already seen - no additional mortality
        if redux_current <= redux_max:
            return 0

        # Calculate new bee quantity after mortality
        new_bee_quant = int(bee_quant * (1 - (redux_current - redux_max)))

        # Return the number killed by pesticide
        return bee_quant - new_bee_quant

    def apply_pesticide_to_bees(
        self, bee_list, from_idx, to_idx, current_dose, max_dose, ld50, slope
    ):
        """
        Port of CColony::ApplyPesticideToBees

        This calculates the number of bees to kill then reduces that number from all age groups
        between "from_idx" and "to_idx" in the list.

        Args:
            bee_list: The bee list to apply mortality to
            from_idx: Starting age index
            to_idx: Ending age index
            current_dose: Current pesticide dose
            max_dose: Previously seen maximum dose
            ld50: Lethal dose 50 value
            slope: Dose-response slope parameter

        Returns:
            Number of bees killed by pesticide
        """
        # Get bee quantity in the specified age range
        bee_quant = int(bee_list.get_quantity_at_range(from_idx, to_idx))
        if bee_quant <= 0:
            return 0

        # Calculate dose response for current and maximum doses
        redux_current = self.m_epadata.dose_response(current_dose, ld50, slope)
        redux_max = self.m_epadata.dose_response(max_dose, ld50, slope)

        # Less than max already seen - no additional mortality
        if redux_current <= redux_max:
            return 0

        # Calculate new bee quantity after mortality
        new_bee_quant = int(bee_quant * (1 - (redux_current - redux_max)))
        prop_redux = new_bee_quant / bee_quant if bee_quant > 0 else 0

        # Apply proportional reduction to the specified age range
        bee_list.set_quantity_at_proportional(from_idx, to_idx, prop_redux)

        # Return the number killed by pesticide
        return int(bee_quant - new_bee_quant)

    def determine_foliar_dose(self, day_num):
        """
        Port of CColony::DetermineFoliarDose

        If we are in a date range with Dose, this routine adds to the Dose rate variables.

        Args:
            day_num: The simulation day number
        """
        # Jump out if Foliar is not enabled
        if not self.m_epadata.m_FoliarEnabled:
            return

        # Get the current date (matches C++ COleDateTime* pDate = GetDayNumDate(DayNum))
        current_date = self.get_day_num_date(day_num)

        # In order to expose, must be after the application date and inside the forage window
        if (
            current_date >= self.m_epadata.m_FoliarAppDate
            and current_date >= self.m_epadata.m_FoliarForageBegin
            and current_date < self.m_epadata.m_FoliarForageEnd
        ):

            # Calculate days since application (matches C++ LONG DaysSinceApplication)
            days_since_application = (
                current_date - self.m_epadata.m_FoliarAppDate
            ).days

            # Foliar Dose is related to AI application rate and Contact Exposure factor
            # (See Kris Garber's EFED Training Insect Exposure.pptx for a summary)
            dose = (
                self.m_epadata.m_E_AppRate
                * self.m_epadata.m_AI_ContactFactor
                / 1000000.0
            )  # convert to Grams AI/bee

            # Dose reduced due to active ingredient half-life
            if self.m_epadata.m_AI_HalfLife > 0:
                import math

                k = math.log(2.0) / self.m_epadata.m_AI_HalfLife
                dose *= math.exp(-k * days_since_application)

            # Adds to any diet-based exposure. Only foragers impacted.
            self.m_epadata.m_D_C_Foragers += dose

    def consume_food(self, event, day_num):
        """
        Calculate colony food consumption and pesticide exposure.

        Args:
            event: Current event with date and forage information
            day_num: Current day number in simulation
        """
        # Skip food consumption on day 1
        if day_num == 1:
            return

        # Calculate colony needs for pollen and nectar
        pollen_need = self.get_pollen_needs(event)  # grams
        nectar_need = self.get_nectar_needs(event)  # grams

        # Get incoming resources from foraging
        incoming_pollen = 0.0
        incoming_nectar = 0.0

        # Get incoming pesticide concentrations
        c_ai_p = 0.0  # Pesticide concentration in incoming pollen
        c_ai_n = 0.0  # Pesticide concentration in incoming nectar

        if event.is_forage_day():
            incoming_pollen = self.get_incoming_pollen_quant()
            incoming_nectar = self.get_incoming_nectar_quant()
            c_ai_p = self.get_incoming_pollen_pesticide_concentration(day_num)
            c_ai_n = self.get_incoming_nectar_pesticide_concentration(day_num)

        # Process pollen consumption
        c_actual_p = 0.0

        # First check if supplemental pollen feeding is available
        in_p = incoming_pollen
        if self.is_pollen_feeding_day(event):
            # C++ logic: All pollen needs are met by supplemental feeding
            if self.m_SuppPollen.m_CurrentAmount >= pollen_need:
                self.m_SuppPollen.m_CurrentAmount -= pollen_need
                pollen_need = 0  # All needs met by supplemental feeding
                c_ai_p = 0  # No pesticide in supplemental feed

        if in_p >= pollen_need:
            # Sufficient incoming pollen
            c_actual_p = c_ai_p
            # Add remaining pollen to resources
            remaining_pollen = in_p - pollen_need
            if remaining_pollen > 0:
                pollen_resource = ResourceItem(
                    resource_quantity=remaining_pollen,
                    pesticide_quantity=remaining_pollen * c_ai_p,
                )
                self.add_pollen_to_resources(pollen_resource)
        else:
            # Need to use stored pollen
            shortfall = pollen_need - in_p

            # Calculate resultant concentration [C1*Q1 + C2*Q2]/[Q1 + Q2]
            stored_conc = self.resources.get_pollen_pesticide_concentration()
            c_actual_p = ((c_ai_p * in_p) + (stored_conc * shortfall)) / (
                in_p + shortfall
            )

            # Check if we have enough stored pollen
            if self.resources.get_pollen_quantity() < shortfall:
                if self.m_NoResourceKillsColony:
                    self.kill_colony()
                    date_str = event.get_date_stg()
                    self.add_event_notification(
                        date_str, "Colony Died - Lack of Pollen Stores"
                    )

            # Remove pollen from stores
            self.resources.remove_pollen(shortfall)

        # Process nectar consumption
        c_actual_n = 0.0

        # First check if supplemental nectar feeding is available
        in_n = incoming_nectar
        if self.is_nectar_feeding_day(event):
            # C++ logic: Add daily nectar amount to resources
            if (
                hasattr(self.m_SuppNectar, "m_StartingAmount")
                and hasattr(self.m_SuppNectar, "m_BeginDate")
                and hasattr(self.m_SuppNectar, "m_EndDate")
                and self.m_SuppNectar.m_BeginDate is not None
                and self.m_SuppNectar.m_EndDate is not None
            ):
                days_in_period = (
                    self.m_SuppNectar.m_EndDate - self.m_SuppNectar.m_BeginDate
                ).days
                if days_in_period > 0:
                    daily_nectar_amount = (
                        self.m_SuppNectar.m_StartingAmount / days_in_period
                    )
                    if self.m_SuppNectar.m_CurrentAmount >= daily_nectar_amount:
                        nectar_resource = ResourceItem(
                            resource_quantity=daily_nectar_amount,
                            pesticide_quantity=0.0,  # No pesticide in supplemental feed
                        )
                        self.add_nectar_to_resources(nectar_resource)
                        self.m_SuppNectar.m_CurrentAmount -= daily_nectar_amount
            c_ai_n = 0  # No pesticide in supplemental nectar

        if in_n >= nectar_need:
            # Sufficient incoming nectar
            c_actual_n = c_ai_n
            # Add remaining nectar to resources
            remaining_nectar = in_n - nectar_need
            if remaining_nectar > 0:
                nectar_resource = ResourceItem(
                    resource_quantity=remaining_nectar,
                    pesticide_quantity=remaining_nectar * c_ai_n,
                )
                self.add_nectar_to_resources(nectar_resource)
        else:
            # Need to use stored nectar
            shortfall = nectar_need - in_n

            # Calculate resultant concentration [C1*Q1 + C2*Q2]/[Q1 + Q2]
            stored_conc = self.resources.get_nectar_pesticide_concentration()
            c_actual_n = ((c_ai_n * in_n) + (stored_conc * shortfall)) / (
                in_n + shortfall
            )

            # Check if we have enough stored nectar
            if self.resources.get_nectar_quantity() < shortfall:
                if self.m_NoResourceKillsColony:
                    self.kill_colony()
                    date_str = event.get_date_stg()
                    self.add_event_notification(
                        date_str, "Colony Died - Lack of Nectar Stores"
                    )

            # Remove nectar from stores
            self.resources.remove_nectar(shortfall)

        # Calculate diet doses for each life stage based on actual consumed concentrations
        # Diet dose = concentration * consumption rate / 1000 (convert mg to g)
        self.m_epadata.m_D_L4 = (
            c_actual_p * self.m_epadata.m_C_L4_Pollen / 1000.0
            + c_actual_n * self.m_epadata.m_C_L4_Nectar / 1000.0
        )
        self.m_epadata.m_D_L5 = (
            c_actual_p * self.m_epadata.m_C_L5_Pollen / 1000.0
            + c_actual_n * self.m_epadata.m_C_L5_Nectar / 1000.0
        )
        self.m_epadata.m_D_LD = (
            c_actual_p * self.m_epadata.m_C_LD_Pollen / 1000.0
            + c_actual_n * self.m_epadata.m_C_LD_Nectar / 1000.0
        )
        self.m_epadata.m_D_A13 = (
            c_actual_p * self.m_epadata.m_C_A13_Pollen / 1000.0
            + c_actual_n * self.m_epadata.m_C_A13_Nectar / 1000.0
        )
        self.m_epadata.m_D_A410 = (
            c_actual_p * self.m_epadata.m_C_A410_Pollen / 1000.0
            + c_actual_n * self.m_epadata.m_C_A410_Nectar / 1000.0
        )
        self.m_epadata.m_D_A1120 = (
            c_actual_p * self.m_epadata.m_C_A1120_Pollen / 1000.0
            + c_actual_n * self.m_epadata.m_C_A1120_Nectar / 1000.0
        )
        self.m_epadata.m_D_AD = (
            c_actual_p * self.m_epadata.m_C_AD_Pollen / 1000.0
            + c_actual_n * self.m_epadata.m_C_AD_Nectar / 1000.0
        )
        self.m_epadata.m_D_D_Foragers = (
            c_actual_p * self.m_epadata.m_C_Forager_Pollen / 1000.0
            + c_actual_n * self.m_epadata.m_C_Forager_Nectar / 1000.0
        )

    def get_pollen_needs(self, event):
        """
        Calculate pollen needs in grams based on colony composition and season.

        Args:
            event: Current event with date and temperature information

        Returns:
            float: Pollen needs in grams
        """
        need = 0.0

        if event.is_winter_day():
            # Winter consumption - nurse bees have different rates
            wadl_ag = [
                self.wadl.get_quantity_at_range(0, 2),  # Ages 0-2
                self.wadl.get_quantity_at_range(3, 9),  # Ages 3-9
                self.wadl.get_quantity_at_range(10, 19),  # Ages 10-19
            ]

            consumption = [
                self.m_epadata.m_C_A13_Pollen / 1000.0,
                self.m_epadata.m_C_A410_Pollen / 1000.0,
                self.m_epadata.m_C_A1120_Pollen / 1000.0,
            ]

            nurse_bee_quantity = self.get_nurse_bees()
            moved_nurse_bees = 0

            # Allocate nurse bees from youngest age groups first
            for i in range(3):
                if wadl_ag[i] <= nurse_bee_quantity - moved_nurse_bees:
                    moved_nurse_bees += wadl_ag[i]
                    need += wadl_ag[i] * consumption[i]
                else:
                    # Match C++ bug: update moved_nurse_bees first, then calculate need
                    # This causes (nurse_bee_quantity - moved_nurse_bees) to be 0
                    moved_nurse_bees += nurse_bee_quantity - moved_nurse_bees
                    need += (nurse_bee_quantity - moved_nurse_bees) * consumption[i]

                if moved_nurse_bees >= nurse_bee_quantity:
                    break

            # Non-nurse bees consume 2 mg per day
            non_nurse_bees = self.get_colony_size() - moved_nurse_bees
            need += non_nurse_bees * 0.002

            # Add forager need
            forager_need = 0.0
            if event.is_forage_day():
                forager_need = (
                    self.foragers.get_active_quantity()
                    * self.m_epadata.m_C_Forager_Pollen
                    / 1000.0
                )
                forager_need += (
                    (self.foragers.get_quantity() - self.foragers.get_active_quantity())
                    * self.m_epadata.m_C_A1120_Pollen
                    / 1000.0
                )
            else:
                forager_need = self.foragers.get_quantity() * 0.002

            need += forager_need  # Already in grams
        else:
            # Non-winter day - calculate based on larvae and adult needs
            # Larvae needs
            l_needs = (
                self.wlarv.get_quantity_at(3) * self.m_epadata.m_C_L4_Pollen
                + self.wlarv.get_quantity_at(4) * self.m_epadata.m_C_L5_Pollen
                + self.dlarv.get_quantity() * self.m_epadata.m_C_LD_Pollen
            )

            # Adult needs
            if event.is_forage_day():
                a_needs = (
                    self.wadl.get_quantity_at_range(0, 2)
                    * self.m_epadata.m_C_A13_Pollen
                    + self.wadl.get_quantity_at_range(3, 9)
                    * self.m_epadata.m_C_A410_Pollen
                    + self.wadl.get_quantity_at_range(10, 19)
                    * self.m_epadata.m_C_A1120_Pollen
                    + self.dadl.get_quantity() * self.m_epadata.m_C_AD_Pollen
                    + self.foragers.get_active_quantity()
                    * self.m_epadata.m_C_Forager_Pollen
                    + self.foragers.get_unemployed_quantity()
                    * self.m_epadata.m_C_A1120_Pollen
                )
            else:
                # All foragers consume like mature adults on non-forage days
                a_needs = (
                    self.wadl.get_quantity_at_range(0, 2)
                    * self.m_epadata.m_C_A13_Pollen
                    + self.wadl.get_quantity_at_range(3, 9)
                    * self.m_epadata.m_C_A410_Pollen
                    + (
                        self.wadl.get_quantity_at_range(10, 19)
                        + self.foragers.get_quantity()
                    )
                    * self.m_epadata.m_C_A1120_Pollen
                    + self.dadl.get_quantity() * self.m_epadata.m_C_AD_Pollen
                )

            need = (l_needs + a_needs) / 1000.0  # Convert to grams

        return need

    def get_nectar_needs(self, event):
        """
        Calculate nectar needs in grams based on colony composition and season.

        Args:
            event: Current event with date and temperature information

        Returns:
            float: Nectar needs in grams
        """
        need = 0.0

        if event.is_winter_day():
            colony_size = self.get_colony_size()
            if colony_size > 0:
                if event.get_temp() <= 8.5:
                    # See K. Garber's Winter Failure logic
                    need = 0.3121 * colony_size * pow(0.128 * colony_size, -0.48)
                else:
                    # 8.5 < AveTemp < 18.0
                    if event.is_forage_day():
                        # Foragers need normal forager nutrition
                        non_foragers = colony_size - self.foragers.get_active_quantity()
                        need = (
                            self.foragers.get_active_quantity()
                            * self.m_epadata.m_C_Forager_Nectar
                        ) / 1000.0 + 0.05419 * non_foragers * pow(
                            0.128 * non_foragers, -0.27
                        )
                    else:
                        # All bees consume at winter rates
                        need = 0.05419 * colony_size * pow(0.128 * colony_size, -0.27)
        else:
            # Summer day
            # Larvae needs
            l_needs = (
                self.wlarv.get_quantity_at(3) * self.m_epadata.m_C_L4_Nectar
                + self.wlarv.get_quantity_at(4) * self.m_epadata.m_C_L5_Nectar
                + self.dlarv.get_quantity() * self.m_epadata.m_C_LD_Nectar
            )

            # Adult needs
            if event.is_forage_day():
                a_needs = (
                    self.wadl.get_quantity_at_range(0, 2)
                    * self.m_epadata.m_C_A13_Nectar
                    + self.wadl.get_quantity_at_range(3, 9)
                    * self.m_epadata.m_C_A410_Nectar
                    + self.wadl.get_quantity_at_range(10, 19)
                    * self.m_epadata.m_C_A1120_Nectar
                    + self.foragers.get_unemployed_quantity()
                    * self.m_epadata.m_C_A1120_Nectar
                    + self.foragers.get_active_quantity()
                    * self.m_epadata.m_C_Forager_Nectar
                    + self.dadl.get_quantity() * self.m_epadata.m_C_AD_Nectar
                )
            else:
                # Foragers consume like mature adults
                a_needs = (
                    self.wadl.get_quantity_at_range(0, 2)
                    * self.m_epadata.m_C_A13_Nectar
                    + self.wadl.get_quantity_at_range(3, 9)
                    * self.m_epadata.m_C_A410_Nectar
                    + (
                        self.wadl.get_quantity_at_range(10, 19)
                        + self.foragers.get_quantity()
                    )
                    * self.m_epadata.m_C_A1120_Nectar
                    + self.dadl.get_quantity() * self.m_epadata.m_C_AD_Nectar
                )

            need = (l_needs + a_needs) / 1000.0  # Convert to grams

        return need

    def get_incoming_pollen_quant(self):
        """
        Calculate incoming pollen quantity in grams from foraging.

        Returns:
            float: Incoming pollen in grams
        """
        pollen = 0.0
        # Only bring in pollen if there are larvae
        if (self.wlarv.get_quantity() + self.dlarv.get_quantity()) > 0:
            pollen = (
                self.foragers.get_active_quantity()
                * self.m_epadata.m_I_PollenTrips
                * self.m_epadata.m_I_PollenLoad
                / 1000.0
            )
        return pollen

    def get_incoming_nectar_quant(self):
        """
        Calculate incoming nectar quantity in grams from foraging.

        Returns:
            float: Incoming nectar in grams
        """
        nectar = (
            self.foragers.get_active_quantity()
            * self.m_epadata.m_I_NectarTrips
            * self.m_epadata.m_I_NectarLoad
            / 1000.0
        )

        # If there are no larvae, all pollen foraging trips become nectar trips
        if (self.wlarv.get_quantity() + self.dlarv.get_quantity()) <= 0:
            nectar += (
                self.foragers.get_active_quantity()
                * self.m_epadata.m_I_PollenTrips
                * self.m_epadata.m_I_NectarLoad
                / 1000.0
            )

        return nectar

    def get_incoming_pollen_pesticide_concentration(self, day_num):
        """
        Calculate incoming pollen pesticide concentration accounting for decay.

        Args:
            day_num: Current day number in simulation

        Returns:
            float: Pesticide concentration in grams AI per gram pollen
        """
        incoming_concentration = 0.0
        cur_date = self.get_day_num_date(day_num)

        # Check if using nutrient contamination table
        if self.nutrient_ct.is_enabled():
            nectar_conc, pollen_conc = self.nutrient_ct.get_contaminant_conc(cur_date)
            incoming_concentration = pollen_conc
        else:
            # Normal foliar spray process
            if (
                self.m_epadata.m_FoliarEnabled
                and cur_date >= self.m_epadata.m_FoliarAppDate
                and cur_date >= self.m_epadata.m_FoliarForageBegin
                and cur_date < self.m_epadata.m_FoliarForageEnd
            ):

                # Base concentration from foliar spray
                incoming_concentration = 110.0 * self.m_epadata.m_E_AppRate / 1000000.0
                # Apply decay due to active ingredient half-life
                days_since_application = (
                    cur_date - self.m_epadata.m_FoliarAppDate
                ).days
                if self.m_epadata.m_AI_HalfLife > 0:
                    k = math.log(2.0) / self.m_epadata.m_AI_HalfLife
                    incoming_concentration *= math.exp(-k * days_since_application)

                self.add_event_notification(
                    cur_date.strftime("%m/%d/%Y"),
                    "Incoming Foliar Spray Pollen Pesticide",
                )

            # Seed treatment exposure
            if (
                cur_date >= self.m_epadata.m_SeedForageBegin
                and cur_date < self.m_epadata.m_SeedForageEnd
                and self.m_epadata.m_SeedEnabled
            ):
                incoming_concentration += (
                    self.m_epadata.m_E_SeedConcentration / 1000000.0
                )
                self.add_event_notification(
                    cur_date.strftime("%m/%d/%Y"), "Incoming Seed Pollen Pesticide"
                )

            # Soil contamination exposure
            if (
                cur_date >= self.m_epadata.m_SoilForageBegin
                and cur_date < self.m_epadata.m_SoilForageEnd
                and self.m_epadata.m_SoilEnabled
            ):
                if self.m_epadata.m_AI_KOW > 0 or self.m_epadata.m_E_SoilTheta != 0:
                    log_kow = math.log10(self.m_epadata.m_AI_KOW)
                    tscf = -0.0648 * (log_kow * log_kow) + 0.241 * log_kow + 0.5822
                    soil_conc = (
                        tscf
                        * (pow(10, (0.95 * log_kow - 2.05)) + 0.82)
                        * self.m_epadata.m_E_SoilConcentration
                        * (
                            self.m_epadata.m_E_SoilP
                            / (
                                self.m_epadata.m_E_SoilTheta
                                + self.m_epadata.m_E_SoilP
                                * self.m_epadata.m_AI_KOC
                                * self.m_epadata.m_E_SoilFoc
                            )
                        )
                    )
                    incoming_concentration += soil_conc / 1000000.0
                    self.add_event_notification(
                        cur_date.strftime("%m/%d/%Y"), "Incoming Soil Pollen Pesticide"
                    )

        return incoming_concentration

    def get_incoming_nectar_pesticide_concentration(self, day_num):
        """
        Calculate incoming nectar pesticide concentration accounting for decay.

        Args:
            day_num: Current day number in simulation

        Returns:
            float: Pesticide concentration in grams AI per gram nectar
        """
        incoming_concentration = 0.0
        cur_date = self.get_day_num_date(day_num)

        # Check if using nutrient contamination table
        if self.nutrient_ct.is_enabled():
            nectar_conc, pollen_conc = self.nutrient_ct.get_contaminant_conc(cur_date)
            incoming_concentration = nectar_conc
        else:
            # Normal foliar spray process
            if (
                self.m_epadata.m_FoliarEnabled
                and cur_date >= self.m_epadata.m_FoliarAppDate
                and cur_date >= self.m_epadata.m_FoliarForageBegin
                and cur_date < self.m_epadata.m_FoliarForageEnd
            ):

                # Base concentration from foliar spray
                incoming_concentration = 110.0 * self.m_epadata.m_E_AppRate / 1000000.0

                # Apply decay due to active ingredient half-life
                days_since_application = (
                    cur_date - self.m_epadata.m_FoliarAppDate
                ).days
                if self.m_epadata.m_AI_HalfLife > 0:
                    k = math.log(2.0) / self.m_epadata.m_AI_HalfLife
                    incoming_concentration *= math.exp(-k * days_since_application)

                self.add_event_notification(
                    cur_date.strftime("%m/%d/%Y"),
                    "Incoming Foliar Spray Nectar Pesticide",
                )

            # Seed treatment exposure
            if (
                cur_date >= self.m_epadata.m_SeedForageBegin
                and cur_date < self.m_epadata.m_SeedForageEnd
                and self.m_epadata.m_SeedEnabled
            ):
                incoming_concentration += (
                    self.m_epadata.m_E_SeedConcentration / 1000000.0
                )
                self.add_event_notification(
                    cur_date.strftime("%m/%d/%Y"), "Incoming Seed Nectar Pesticide"
                )

            # Soil contamination exposure
            if (
                cur_date >= self.m_epadata.m_SoilForageBegin
                and cur_date < self.m_epadata.m_SoilForageEnd
                and self.m_epadata.m_SoilEnabled
            ):
                if self.m_epadata.m_AI_KOW > 0 or self.m_epadata.m_E_SoilTheta != 0:
                    log_kow = math.log10(self.m_epadata.m_AI_KOW)
                    tscf = -0.0648 * (log_kow * log_kow) + 0.241 * log_kow + 0.5822
                    soil_conc = (
                        tscf
                        * (pow(10, (0.95 * log_kow - 2.05)) + 0.82)
                        * self.m_epadata.m_E_SoilConcentration
                        * (
                            self.m_epadata.m_E_SoilP
                            / (
                                self.m_epadata.m_E_SoilTheta
                                + self.m_epadata.m_E_SoilP
                                * self.m_epadata.m_AI_KOC
                                * self.m_epadata.m_E_SoilFoc
                            )
                        )
                    )
                    incoming_concentration += soil_conc / 1000000.0
                    self.add_event_notification(
                        cur_date.strftime("%m/%d/%Y"), "Incoming Soil Nectar Pesticide"
                    )

        return incoming_concentration

    def is_pollen_feeding_day(self, event):
        """
        Check if supplemental pollen feeding should occur.

        Args:
            event: Current event with date information

        Returns:
            bool: True if pollen feeding should occur
        """
        feeding_day = False

        if self.m_SuppPollenEnabled and self.get_colony_size() > 100:
            if self.m_SuppPollenAnnual:
                # Annual feeding - check within year
                test_begin = event.get_time().replace(
                    month=self.m_SuppPollen.m_BeginDate.month,
                    day=self.m_SuppPollen.m_BeginDate.day,
                )
                test_end = event.get_time().replace(
                    month=self.m_SuppPollen.m_EndDate.month,
                    day=self.m_SuppPollen.m_EndDate.day,
                )

                feeding_day = (
                    self.m_SuppPollen.m_CurrentAmount > 0.0
                    and test_begin < event.get_time()
                    and test_end >= event.get_time()
                )
            else:
                # Specific date range
                feeding_day = (
                    self.m_SuppPollen.m_CurrentAmount > 0.0
                    and self.m_SuppPollen.m_BeginDate < event.get_time()
                    and self.m_SuppPollen.m_EndDate >= event.get_time()
                )

        return feeding_day

    def is_nectar_feeding_day(self, event):
        """
        Check if supplemental nectar feeding should occur.

        Args:
            event: Current event with date information

        Returns:
            bool: True if nectar feeding should occur
        """
        feeding_day = False

        if self.m_SuppNectarEnabled and self.get_colony_size() > 100:
            if self.m_SuppNectarAnnual:
                # Annual feeding - check within year
                test_begin = event.get_time().replace(
                    month=self.m_SuppNectar.m_BeginDate.month,
                    day=self.m_SuppNectar.m_BeginDate.day,
                )
                test_end = event.get_time().replace(
                    month=self.m_SuppNectar.m_EndDate.month,
                    day=self.m_SuppNectar.m_EndDate.day,
                )
                feeding_day = (
                    self.m_SuppNectar.m_CurrentAmount > 0.0
                    and test_begin < event.get_time()
                    and test_end >= event.get_time()
                )
            else:
                # Specific date range
                feeding_day = (
                    self.m_SuppNectar.m_CurrentAmount > 0.0
                    and self.m_SuppNectar.m_BeginDate < event.get_time()
                    and self.m_SuppNectar.m_EndDate >= event.get_time()
                )

        return feeding_day

    def add_pollen_to_resources(self, resource):
        """
        Add pollen to colony resources with storage limits.

        Args:
            resource: ResourceItem object with resource_quantity and pesticide_quantity
        """
        if self.m_ColonyPolMaxAmount <= 0:
            self.m_ColonyPolMaxAmount = 5000  # Default max

        prop_full = self.resources.get_pollen_quantity() / self.m_ColonyPolMaxAmount
        reduction = 1 - prop_full

        if prop_full > 0.9:
            resource.resource_quantity *= reduction
            resource.pesticide_quantity *= reduction

        self.resources.add_pollen(resource)

    def add_nectar_to_resources(self, resource):
        """
        Add nectar to colony resources with storage limits.

        Args:
            resource: ResourceItem object with resource_quantity and pesticide_quantity
        """
        if self.m_ColonyNecMaxAmount <= 0:
            self.m_ColonyNecMaxAmount = 5000  # Default max

        prop_full = self.resources.get_nectar_quantity() / self.m_ColonyNecMaxAmount
        reduction = 1 - prop_full

        if reduction < 0:
            reduction = 0  # Don't exceed max value

        if prop_full > 0.9:
            resource.resource_quantity *= reduction
            resource.pesticide_quantity *= reduction

        self.resources.add_nectar(resource)

    def initialize_colony_resources(self):
        """
        Port of CColony::InitializeColonyResources

        Initialize colony resources to zero values.
        TODO: This should ultimately be pre-settable at the beginning of a simulation.
        For now, initialize everything to 0.0.
        """
        self.resources.set_pollen_quantity(0)
        self.resources.set_nectar_quantity(0)
        self.resources.set_pollen_pesticide_quantity(0)
        self.resources.set_nectar_pesticide_quantity(0)
