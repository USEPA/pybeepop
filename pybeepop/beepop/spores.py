"""
Spores Module for BeePop+ Biocontrol Simulation

Not yet implemented

Classes:
    Spores: Biocontrol agent spore dynamics and efficacy modeling
"""


class Spores:
    """
    Biocontrol spore dynamics and treatment efficacy model for BeePop+ simulation.

    Models the vitality degradation and treatment efficacy of biological control
    spores over time. Implements William Meikle's research-based spore survival
    data and mortality functions for accurate biocontrol agent modeling in
    honey bee colonies.

    Not yet implemented

    Note:
        Vitality data based on William Meikle's email of May 23, 2005. May transition
        to polynomial functions as additional research data becomes available.
    """

    class IntDoub:
        def __init__(self, int_val=0, doub_val=0.0):
            self.int_val = int_val
            self.doub_val = doub_val

    def __init__(self):
        # The Spore Vitality Data is from William Meikle's email of May 23, 2005.
        # The Vitality is the percentage of live spores left after a number of days
        # The DayPoints are the days after application that the vitality was measured.
        # Most likely will change to a polynomial function
        self.m_InitialSporeCount = 0
        self.m_SporeVitalityMatrix = [self.IntDoub() for _ in range(10)]
        self.m_MortalityFunctionPts = [self.IntDoub() for _ in range(10)]
        self.m_SporeVitalityMatrix[0].doub_val = 1.0  # Sample Values
        self.m_SporeVitalityMatrix[1].doub_val = 0.16
        self.m_SporeVitalityMatrix[2].doub_val = 0.26
        self.m_SporeVitalityMatrix[3].doub_val = 0.13
        self.m_SporeVitalityMatrix[4].doub_val = 0.01
        self.m_SporeVitalityMatrix[5].doub_val = 0.003
        self.m_SporeVitalityMatrix[0].int_val = 1  # Sample Days
        self.m_SporeVitalityMatrix[1].int_val = 3
        self.m_SporeVitalityMatrix[2].int_val = 6
        self.m_SporeVitalityMatrix[3].int_val = 13
        self.m_SporeVitalityMatrix[4].int_val = 20
        self.m_SporeVitalityMatrix[5].int_val = 42
        self.m_SporeVitalityPtCount = 6
        self.m_MortFunctPtCount = 0

    def set_mortality_function(self, percent_mortality, spore_density, index):
        """
        Sets the Varroa mortality rate as a function of spore density.
        For now, this will be set from the CAction dialog and will simply consist
        of pairs of proportion of mortality and spore density (spores per mite).
        This may ultimately become a polynomial function once we have data.
        """
        self.m_MortalityFunctionPts[index].doub_val = percent_mortality
        self.m_MortalityFunctionPts[index].int_val = spore_density
        self.m_MortFunctPtCount += 1

    def get_day_mortality_rate(self, treatment_day_number):
        """
        The mortality rate for a specific day after treatment begins is a function
        of the Mortality Rate vs Spore Density and the Degradation of spores over time.
        """
        current_spores = int(
            self.m_InitialSporeCount
            * self._interpolation(
                self.m_SporeVitalityMatrix,
                self.m_SporeVitalityPtCount,
                treatment_day_number,
            )
        )
        mort_rate = self._interpolation(
            self.m_MortalityFunctionPts, self.m_MortFunctPtCount, current_spores
        )
        return mort_rate

    def _interpolation(self, id_array, array_size, int_var):
        """
        Performs a linear interpolation of an IntDoub array using int_var as the independent variable.
        If the interpolation is not found, returns 0.
        """
        if array_size == 0:
            return 0.0
        if int_var >= id_array[array_size - 1].int_val:
            return id_array[array_size - 1].doub_val
        elif int_var <= id_array[0].int_val:
            return id_array[0].doub_val
        else:
            for index in range(array_size - 1):
                if id_array[index].int_val <= int_var <= id_array[index + 1].int_val:
                    # Linear interpolation
                    return (
                        (int_var - id_array[index].int_val)
                        / (id_array[index + 1].int_val - id_array[index].int_val)
                    ) * (
                        id_array[index + 1].doub_val - id_array[index].doub_val
                    ) + id_array[
                        index
                    ].doub_val
        return 0.0

    def _interpolation_doub(self, id_array, array_size, doub_val):
        """
        Performs a linear interpolation of an IntDoub array using doub_val as the independent variable.
        If the interpolation is not found, returns 0.
        """
        if array_size == 0:
            return 0
        if doub_val >= id_array[array_size - 1].doub_val:
            return id_array[array_size - 1].int_val
        elif doub_val <= id_array[0].doub_val:
            return id_array[0].int_val
        else:
            for index in range(array_size - 1):
                if id_array[index].doub_val <= doub_val <= id_array[index + 1].doub_val:
                    # Linear interpolation
                    return int(
                        (
                            (doub_val - id_array[index].doub_val)
                            / (id_array[index + 1].doub_val - id_array[index].doub_val)
                        )
                        * (id_array[index + 1].int_val - id_array[index].int_val)
                        + id_array[index].int_val
                    )
        return 0
