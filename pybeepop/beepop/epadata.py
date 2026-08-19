"""BeePop+ EPA Pesticide Data Management Module.

This module contains classes for managing pesticide active ingredient (AI)
data including toxicity parameters, consumption rates, and environmental fate
characteristics. This data drives pesticide exposure and mortality calculations
throughout the simulation.Different life stages have varying sensitivity
to pesticide exposure based on physiological differences and exposure pathways.

Classes:
    AIItem: Individual active ingredient with toxicity and fate parameters
    EPAData: EPA pesticide database manager with consumption and exposure data
"""

from datetime import datetime
from typing import List, Optional


class AIItem:
    """Not currently being used? Only supported one AI at a time,
    directly setting class variables in EPAData"""

    def __init__(self, name: str = ""):
        self.name = name
        self.adult_slope = 0.0
        self.adult_ld50 = 0.0
        self.adult_slope_contact = 0.0
        self.adult_ld50_contact = 0.0
        self.larva_slope = 0.0
        self.larva_ld50 = 0.0
        self.kow = 0.0
        self.koc = 0.0
        self.half_life = 0.0
        self.contact_factor = 0.0


class EPAData:
    """EPA pesticide database manager with active ingredient and consumption data.

    Manages pesticide data including active ingredient toxicity
    parameters, bee consumption rates by life stage, and foraging behavior data.
    Provides centralized access to pesticide exposure and effects parameters
    used throughout the simulation.

    Integrates toxicity data with consumption patterns to calculate realistic
    pesticide exposure doses for different bee castes and life stages. Supports
    both oral and contact exposure routes (contact for foliar application mode only).

    """

    def __init__(self):
        self.ai_items: List[AIItem] = []
        self.current_ai: Optional[AIItem] = None

        # Currently selected AI attributes (matching C++ m_AI_* naming)
        self.m_AI_Name = ""
        self.m_AI_AdultSlope = 0.0
        self.m_AI_AdultLD50 = 0.0
        self.m_AI_AdultSlope_Contact = 0.0  # foliar application only
        self.m_AI_AdultLD50_Contact = 0.0  # foliar application only
        self.m_AI_LarvaSlope = 0.0
        self.m_AI_LarvaLD50 = 0.0
        self.m_AI_KOW = 0.0  # soil application only
        self.m_AI_KOC = 0.0  # soil application only
        self.m_AI_HalfLife = 0.0
        self.m_AI_ContactFactor = 0.0  # foliar application only

        # Consumption (match C++ m_C_* naming exactly)
        self.m_C_L4_Pollen = 0.0
        self.m_C_L4_Nectar = 0.0
        self.m_C_L5_Pollen = 0.0
        self.m_C_L5_Nectar = 0.0
        self.m_C_LD_Pollen = 0.0
        self.m_C_LD_Nectar = 0.0
        self.m_C_A13_Pollen = 0.0
        self.m_C_A13_Nectar = 0.0
        self.m_C_A410_Pollen = 0.0
        self.m_C_A410_Nectar = 0.0
        self.m_C_A1120_Pollen = 0.0
        self.m_C_A1120_Nectar = 0.0
        self.m_C_AD_Pollen = 0.0
        self.m_C_AD_Nectar = 0.0
        self.m_C_Forager_Pollen = 0.0
        self.m_C_Forager_Nectar = 0.0

        # Incoming (match C++ m_I_* naming exactly)
        self.m_I_PollenTrips = 0
        self.m_I_NectarTrips = 0
        self.m_I_PercentNectarForagers = 0.0
        self.m_I_PollenLoad = 0.0
        self.m_I_NectarLoad = 0.0

        # Current dosages (matching C++ m_D_* naming)
        self.m_D_L4 = 0.0  # Current dosage for larvae 4 days old
        self.m_D_L5 = 0.0  # Current dosage for larvae 5 days old
        self.m_D_LD = 0.0  # Current dosage for larvae drone
        self.m_D_A13 = 0.0  # Current dosage for adult workers 1-3 days old
        self.m_D_A410 = 0.0  # Current dosage for adult workers 4-10 days old
        self.m_D_A1120 = 0.0  # Current dosage for adult workers 11-20 days old
        self.m_D_AD = 0.0  # Current dosage for adult drones
        self.m_D_C_Foragers = 0.0  # Current contact dosage for foragers
        self.m_D_D_Foragers = 0.0  # Current diet dosage for foragers

        # Maximum doses seen so far for each life stage
        self.m_D_L4_Max = 0.0
        self.m_D_L5_Max = 0.0
        self.m_D_LD_Max = 0.0
        self.m_D_A13_Max = 0.0
        self.m_D_A410_Max = 0.0
        self.m_D_A1120_Max = 0.0
        self.m_D_AD_Max = 0.0
        self.m_D_C_Foragers_Max = 0.0
        self.m_D_D_Foragers_Max = 0.0

        # Exposure (match C++ naming exactly)
        self.m_FoliarEnabled = False
        self.m_SoilEnabled = False
        self.m_SeedEnabled = False
        self.m_E_AppRate = 0.0
        self.m_E_SoilTheta = 0.0
        self.m_E_SoilP = 0.0
        self.m_E_SoilFoc = 0.0
        self.m_E_SoilConcentration = 0.0
        self.m_E_SeedAppRate = 0.0
        self.m_FoliarAppDate = datetime.now()
        self.m_FoliarForageBegin = datetime.now()
        self.m_FoliarForageEnd = datetime.now()
        self.m_SoilForageBegin = datetime.now()
        self.m_SoilForageEnd = datetime.now()
        self.m_SeedForageBegin = datetime.now()
        self.m_SeedForageEnd = datetime.now()

        # Nectar/Pollen Bypass File Processing (match C++ naming exactly)
        self.m_NecPolFileEnabled = False
        self.m_NecPolFileName = ""

    def add_ai_item(self, item: AIItem):
        self.ai_items.append(item)

    def remove_ai_item(self, name: str) -> bool:
        for i, item in enumerate(self.ai_items):
            if item.name == name:
                del self.ai_items[i]
                return True
        return False

    def get_ai_item(self, name: str) -> Optional[AIItem]:
        for item in self.ai_items:
            if item.name == name:
                return item
        return None

    def set_current_ai_item(self, item: AIItem):
        self.current_ai = item

    def get_ai_item_count(self) -> int:
        return len(self.ai_items)

    def dose_response(self, dose: float, ld50: float, slope: float) -> float:
        """
        Replicates the C++ DoseResponse logic:
        - Converts dose from grams to micrograms
        - Assumes LD50 is already in micrograms/bee (as per C++ comment)
        - Validates input
        - Returns proportion killed
        """
        dose *= 1_000_000.0  # Convert grams to micrograms
        # LD50 is assumed to already be in micrograms/bee (per C++ comment)
        valid = (dose > ld50 * 0.05) and (ld50 > 0) and (slope >= 0) and (slope < 20)
        if not valid:
            return 0.0
        return 1.0 / (1.0 + (dose / ld50) ** (-slope))
