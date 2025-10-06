"""BeePop+ Queen Bee Module.

This module contains the Queen class that models the queen bee's behavior,
egg-laying dynamics, sperm reserves, and overall strength within a honey bee
colony simulation. The implementation is based on the BEEPOP model by
DeGrandi-Hoffman et al. (1988) and serves as a Python port of the C++ CQueen class.

The Queen class manages the reproductive capacity of the colony, determining
daily egg production based on environmental factors, colony conditions, and
the queen's physiological state.

Algorithm Basis:
    The egg-laying algorithm is derived from:
    "BEEPOP: A HONEYBEE POPULATION DYNAMICS SIMULATION MODEL"
    G. DeGrandi-Hoffman et al., 1988

    The model incorporates multiple environmental and biological factors:
    - Queen strength and age (P factor)
    - Degree days/temperature (DD factor)
    - Daylight hours (L factor)
    - Forager population (N factor)
    - Nurse bee availability (larv_per_bee ratio)
    - Sperm reserves (affects drone egg proportion)

Key Features:
    - Dynamic egg laying based on multiple environmental factors
    - Sperm depletion modeling for drone egg production
    - Queen strength system (1-5 scale)
    - Requeening event support with egg laying delays
    - Integration with colony resource and population dynamics

"""

from pybeepop.beepop.bee import Bee
import math
from pybeepop.beepop.globaloptions import GlobalOptions


class Queen(Bee):
    """Queen bee class for colony reproduction and egg-laying dynamics.

    This class models the queen bee's reproductive behavior, including daily
    egg laying, sperm reserve management, and responses to environmental
    conditions. The queen's egg-laying capacity is determined by multiple
    factors including her strength, environmental conditions, and colony state.

    The Queen class implements the BEEPOP egg-laying algorithm, which uses
    multiplicative factors to determine daily egg production:
    - P: Queen potential based on strength and age
    - DD: Degree-day (temperature) response
    - L: Daylight hours (photoperiod) response
    - N: Forager population response

    The vars table defines queen capabilities for strength levels 1-5:
        - Strength 1: 1000 max eggs, 1.8M sperm
        - Strength 2: 1500 max eggs, 2.7M sperm
        - Strength 3: 2000 max eggs, 3.7M sperm
        - Strength 4: 2500 max eggs, 4.8M sperm
        - Strength 5: 3000 max eggs, 5.5M sperm

    Note:
        Intermediate strength values are interpolated between table entries.
        Sperm depletion over time increases the proportion of drone eggs.
        High larv_per_bee ratios (>2.0) stop egg laying due to insufficient
        nurse bees.
    """

    def __init__(self):
        """Initialize a new Queen with default attributes.

        Creates a queen bee with default strength (1.0), full sperm reserves,
        and empty egg counts. The queen starts with no egg-laying delay and
        is ready to begin laying eggs immediately upon simulation start.

        The queen is initialized with the minimum strength level (1.0) and
        corresponding maximum egg laying capacity and sperm count from the
        lookup table.
        """
        super().__init__(number=1)
        self.age = 0.0
        self.alive = True
        self.cum_weggs = 0
        self.cur_queen_day_1 = 1
        self.egg_laying_delay = 0
        self.weggs = 0
        self.deggs = 0
        self.teggs = 0
        self.max_eggs = 0.0
        self.DD = 0.0
        self.L = 0.0
        self.N = 0.0
        self.P = 0.0
        self.dd = 0.0
        self.l = 0.0
        self.n = 0.0
        self.current_sperm = 0.0
        self.initial_sperm = 5500000.0
        self.strength = 1.0
        # m_Vars: [max_eggs, initial_sperm] for strengths 1-5
        self.vars = [
            [1000, 1800000],
            [1500, 2720000],
            [2000, 3650000],
            [2500, 4750000],
            [3000, 5500000],
        ]

    # Only one version of each method below, preserving docstrings where present
    def get_DD(self):
        return self.DD

    def get_L(self):
        return self.L

    def get_N(self):
        return self.N

    def get_P(self):
        return self.P

    def get_dd(self):
        return self.dd

    def get_l(self):
        return self.l

    def get_n(self):
        return self.n

    def get_weggs(self):
        return self.weggs

    def get_deggs(self):
        return self.deggs

    def get_teggs(self):
        return self.teggs

    def set_initial_sperm(self, sperm):
        self.initial_sperm = sperm

    def set_current_sperm(self, sperm):
        self.current_sperm = sperm

    def get_initial_sperm(self):
        return self.initial_sperm

    def get_current_sperm(self):
        return self.current_sperm

    def set_strength(self, strength):
        """Set the queen's strength and update related attributes.

        Sets the internal values of the Queen object based on the input strength
        by linearly interpolating between the lookup table values. The strength
        is constrained to the range [1.0, 5.0] and determines both maximum egg
        laying capacity and initial sperm count.

        Args:
            strength (float): Queen strength rating between 1.0 and 5.0.
                Higher values indicate stronger queens with greater egg laying
                capacity and larger sperm reserves.

        Note:
            Strength values are interpolated between discrete table entries.
            Values outside [1.0, 5.0] are clamped to the valid range.
            Setting strength also resets current sperm to initial sperm.
        """
        self.strength = strength
        s = max(1.00000001, min(strength, 4.99999999))
        i_strength = int(s)
        max_eggs1, sperm1 = self.vars[i_strength - 1]
        max_eggs2, sperm2 = self.vars[i_strength]
        self.max_eggs = max_eggs1 + (max_eggs2 - max_eggs1) * (s - i_strength)
        self.initial_sperm = sperm1 + (sperm2 - sperm1) * (s - i_strength)
        self.current_sperm = self.initial_sperm

    def get_queen_strength(self):
        return self.strength

    def get_strength(self):
        """Alias for get_queen_strength() to match expected interface."""
        return self.strength

    def set_max_eggs(self, max_eggs):
        self.max_eggs = max_eggs

    def get_max_eggs(self):
        return self.max_eggs

    def set_egg_laying_delay(self, delay):
        self.egg_laying_delay = delay

    def set_day_one(self, day_num):
        self.cur_queen_day_1 = day_num

    def requeen(self, egg_laying_delay, queen_strength, sim_day_num):
        self.egg_laying_delay = egg_laying_delay
        self.cur_queen_day_1 = sim_day_num
        self.set_strength(queen_strength)

    def compute_L(self, daylight_hours):
        """
        Computes the DaylightHours-based component for egg-laying.
        Uses the main algorithm from the original C++ code.
        Gets the threshold from GlobalOptions singleton.
        """
        threshold = GlobalOptions.get().daylight_hours_threshold
        L = 0.0
        if daylight_hours > threshold:
            L = math.log10((daylight_hours + 0.3) * 0.1) * 7.889
        L = max(0, min(L, 1.0))
        return L

    def get_prop_drone_eggs(self):
        """
        Calculates the proportion of drone eggs based on sperm reserves.
        Prevents divide by zero and uses a cubic polynomial fit from the original model.
        """
        if self.initial_sperm == 0:
            return 0.0
        propsperm = (self.initial_sperm - self.current_sperm) / self.initial_sperm
        if propsperm < 0.6:
            pde = 0.0
        else:
            pde = 1 - (
                -6.355 * propsperm**3 + 7.657 * propsperm**2 - 2.3 * propsperm + 1.002
            )
        return max(0.0, pde)

    def lay_eggs(
        self, lay_days, degree_days, daylight_hours, num_foragers, larv_per_bee
    ):
        """
        Main egg-laying algorithm. Sets daily egg counts and updates sperm reserves.
        Implements logic from BEEPOP and the original C++ code.
        """
        if larv_per_bee > 2:
            # Not enough House Bees
            self.weggs = 0  # Set egg count to 0
            self.deggs = 0  # Set egg count to 0
            self.teggs = 0
            self.DD = 0
            self.L = 0
            self.N = 0
            self.P = 0
            self.dd = 0
            self.l = 0
            self.n = 0
            return

        # Pre-decrement egg laying delay to match C++ behavior: --m_EggLayingDelay > 0
        self.egg_laying_delay -= 1
        if self.egg_laying_delay > 0:
            # Still some egg laying delay from re-queening
            self.weggs = 0  # Set egg count to 0
            self.deggs = 0  # Set egg count to 0
            self.teggs = 0
            self.DD = 0
            self.L = 0
            self.N = 0
            self.P = 0
            self.dd = 0
            self.l = 0
            self.n = 0
            return
        lay_days = (
            lay_days - self.cur_queen_day_1
        )  # Correct if there has been a re-queening
        P = self.max_eggs + -0.0027 * lay_days**2 + 0.395 * lay_days
        P = max(0, P)
        DD = -0.0006 * degree_days**2 + 0.05 * degree_days + 0.021
        DD = max(0, min(DD, 1))
        if degree_days == 0:
            DD = 0
        L = self.compute_L(daylight_hours)
        N = math.log10((num_foragers * 0.001) + 1) * 0.672
        N = max(0, min(N, 1))
        E = DD * L * N * P
        self.DD = DD
        self.L = L
        self.N = N
        self.P = P
        self.dd = degree_days
        self.l = daylight_hours
        self.n = num_foragers
        S = self.get_prop_drone_eggs()
        # Alternate L and F calculation (historical, not main algorithm)
        L_alt = math.log10(daylight_hours * 0.1) * 0.284 if daylight_hours > 0 else 0
        L_alt = max(0, L_alt)
        F = math.log10(num_foragers * 0.0006) * 0.797 if num_foragers > 0 else 0
        F = max(0, F)
        B = L_alt * F
        Z = S + B
        Z = min(Z, 1.0)
        self.deggs = int(E * Z)
        self.weggs = int(E - self.deggs)
        self.teggs = int(E)
        self.current_sperm -= 10 * self.weggs
        self.current_sperm = max(0, self.current_sperm)
        # Only 85% of eggs become adults
        self.deggs = int(self.deggs * 0.85)
        self.weggs = int(self.weggs * 0.85)
        self.teggs = int(self.teggs * 0.85)
        self.cum_weggs += self.weggs

    def __str__(self):
        return f"Queen(strength={self.strength}, max_eggs={self.max_eggs}, initial_sperm={self.initial_sperm}, current_sperm={self.current_sperm}, weggs={self.weggs}, deggs={self.deggs}, teggs={self.teggs})"
