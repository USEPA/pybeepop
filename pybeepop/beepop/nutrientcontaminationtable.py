"""
Nutrient Contamination Module for BeePop+ Pesticide Exposure Simulation

This module manages time-dependent contamination levels in honey bee nutrient
sources (pollen and nectar). It tracks daily contamination concentrations
for modeling exposure to pesticides.

Classes:
    SNCElement: Single day's contamination data for pollen and nectar sources
    NutrientContaminationTable: Time-series contamination concentration manager
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple


@dataclass
class SNCElement:
    """
    Daily nutrient source contamination data for BeePop+ exposure simulation.

    Represents contamination levels in honey bee nutrient sources (pollen and
    nectar) for a specific date. Enables modeling of time-varying exposure
    to environmental contaminants through foraging activities.

    Attributes:
        nc_date (datetime): Date for this contamination measurement
        nc_pollen_cont (float): Pollen contamination concentration (default: 0.0)
        nc_nectar_cont (float): Nectar contamination concentration (default: 0.0)
    """

    nc_date: datetime
    nc_pollen_cont: float = 0.0
    nc_nectar_cont: float = 0.0


class NutrientContaminationTable:
    """
    Time-series contamination concentration manager for BeePop+ exposure simulation.

    Attributes:
        cont_date_array (List[SNCElement]): Time-series of daily contamination measurements
        nutrient_cont_enabled (bool): Whether contamination effects are active in simulation
        contaminant_file_name (str): Source filename for contamination data (default: "No File Loaded")
    """

    def __init__(self):
        self.cont_date_array: List[SNCElement] = []
        self.nutrient_cont_enabled: bool = False
        self.contaminant_file_name: str = "No File Loaded"

    def remove_all(self):
        self.cont_date_array.clear()

    def add_contaminant_conc(self, element: SNCElement):
        self.cont_date_array.append(element)

    def get_contaminant_conc(self, date: datetime) -> Tuple[float, float]:
        """
        Returns (nectar_conc, pollen_conc) for the given date. If not found, returns (0.0, 0.0).
        """
        for element in self.cont_date_array:
            if element.nc_date.date() == date.date():
                return element.nc_nectar_cont, element.nc_pollen_cont
        return 0.0, 0.0

    def copy_from(self, other: "NutrientContaminationTable"):
        self.remove_all()
        self.cont_date_array = [
            SNCElement(e.nc_date, e.nc_pollen_cont, e.nc_nectar_cont)
            for e in other.cont_date_array
        ]
        self.nutrient_cont_enabled = other.nutrient_cont_enabled
        self.contaminant_file_name = other.contaminant_file_name

    def get_file_name(self) -> str:
        return self.contaminant_file_name

    def is_enabled(self) -> bool:
        return self.nutrient_cont_enabled
