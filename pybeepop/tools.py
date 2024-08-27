##
# BeePop+ Wrapper Tools for Python - linux version
# code by Jeff Minucci
# 5/2022
##

import os
import io
import ctypes
import pandas as pd

colnames = [  # DataFrame column names for the BeePop+ output
    "Date",
    "Colony Size",
    "Adult Drones",
    "Adult Workers",
    "Foragers",
    "Active Foragers",
    "Capped Drone Brood",
    "Capped Worker Brood",
    "Drone Larvae",
    "Worker Larvae",
    "Drone Eggs",
    "Worker Eggs",
    "Total Eggs",
    "DD",
    "L",
    "N",
    "P",
    "dd",
    "l",
    "n",
    "Free Mites",
    "Drone Brood Mites",
    "Worker Brood Mites",
    "Mites/Drone Cell",
    "Mites/Worker Cell",
    "Mites Dying",
    "Proportion Mites Dying",
    "Colony Pollen (g)",
    "Pollen Pesticide Concentration (ug/g)",
    "Colony Nectar (g)",
    "Nectar Pesticide Concentration (ug/g)",
    "Dead Drone Larvae",
    "Dead Worker Larvae",
    "Dead Drone Adults",
    "Dead Worker Adults",
    "Dead Foragers",
    "Queen Strength",
    "Average Temperature (C)",
    "Rain (mm)",
    "Min Temp (C)",
    "Max Temp (C)",
    "Daylight hours",
    "Forage Inc",
    "Forage Day",
]


def StringList2CPA(theList):
    """Utility function to convert a list of strings to bytes readble by the C++ library"""
    theListBytes = []
    for i in range(len(theList)):
        theListBytes.append(bytes(theList[i], "utf-8"))
    return theListBytes


class BeePopModel:
    """Class of background functions to interface with the BeePop+ shared library using CTypes.

    In most cases users would interact with a PyBeePop object instead of this class.
    """

    def __init__(self, library_file, verbose=False):
        """Initialize the connection to the BeePop+ shared library.

        Args:
            library_file (str): Path to the BeePop+ shared library.
            verbose (bool, optional): Print debugging messages? Defaults to False.

        Raises:
            RuntimeError: If BeePop+ passes an error code on initialization.
        """
        self.parameters = dict()
        self.parent = os.path.dirname(os.path.abspath(__file__))
        self.valid_parameters = pd.read_csv(
            os.path.join(self.parent, "data/BeePop_exposed_parameters.csv"), skiprows=1
        )["Exposed Variable Name"].tolist()
        self.weather_file = None
        self.contam_file = None
        self.verbose = verbose
        self.results = None
        self.lib = ctypes.CDLL(library_file)
        self.parent_dir = os.path.dirname(os.path.abspath(__file__))
        self.lib_status = None
        if self.lib.InitializeModel():  # Initialize model
            if self.verbose:
                print("Model initialized.")
        else:
            raise RuntimeError("BeePop+ could not be initialized.")
        self.clear_buffers()
        self.send_pars_to_beepop(
            ["NecPolFileEnable=false"], silent=True
        )  # disable residue input until given

    def clear_buffers(self):
        """Clear C++ buffers in BeePop+"""
        if not self.lib.ClearResultsBuffer():  # Clear Results and weather lists
            raise RuntimeError("Error clearing results buffer.")
        if not self.lib.ClearErrorList():
            raise RuntimeError("Error clearing error list")
        if not self.lib.ClearInfoList():
            raise RuntimeError("Error clearing info")

    def load_input_file(self, in_file):
        """Load txt file of BeePop+ parameters."""
        self.input_file = in_file
        icf = open(self.input_file)
        inputs = icf.readlines()
        icf.close()
        input_d = dict(x.replace(" ", "").replace("\n", "").split("=") for x in inputs)
        self.parameter_list_update(input_d)  # update parameter dictionary
        inputlist = []
        for k, v in self.parameters.items():
            inputlist.append("{}={}".format(k, v))
        self.send_pars_to_beepop(inputlist)
        return self.parameters

    def parameter_list_update(self, parameters):
        """Update the internal tracking of set parameters with a dict of
        parameters: values."""
        to_add = dict((k.lower(), v) for k, v in parameters.items())
        self.parameters.update(to_add)

    def set_parameters(self, parameters=None):
        """Set BeePop+ parameters based on a dict of parameters: values"""
        if parameters is not None:
            self.parameter_list_update(parameters)
        else:
            if len(self.parameters) < 1:
                return
        inputlist = []
        for k, v in self.parameters.items():
            inputlist.append("{}={}".format(k, v))
        self.send_pars_to_beepop(inputlist)
        return self.parameters

    def send_pars_to_beepop(self, parameter_list, silent=False):
        """Call the BeePop+ interface function to set parameters from a list of
        parameter=value strings"""
        for par in parameter_list:  # check for invalid parameters
            par_name = par.split("=")[0].lower()
            if par_name not in [x.lower() for x in self.valid_parameters]:
                raise ValueError("{} is not a valid parameter.".format(par_name))
        CPA = (ctypes.c_char_p * len(parameter_list))()
        inputlist_bytes = StringList2CPA(parameter_list)
        CPA[:] = inputlist_bytes
        if self.lib.SetICVariablesCPA(CPA, len(parameter_list)):
            if self.verbose and not silent:
                print("Updated parameters")
        else:
            raise RuntimeError("Error setting parameters")

    def get_parameters(self):
        """Return the current dict of user defined parameters"""
        return self.parameters

    def load_weather(self, weather_file=None):
        """Load a csv or comma separated txt weather file into BeePop+ using the library interface."""
        if weather_file is not None:
            try:
                wf = open(weather_file)
                weatherlines = wf.readlines()
                wf.close()
            except:
                raise OSError("Weather file is invalid.")
            self.weather_file = weather_file
            CPA = (ctypes.c_char_p * len(weatherlines))()
            weatherline_bytes = StringList2CPA(weatherlines)
            CPA[:] = weatherline_bytes
            if self.lib.SetWeatherCPA(CPA, len(weatherlines)):
                if self.verbose:
                    print("Loaded Weather")
            else:
                raise RuntimeError("Error Loading Weather")
        else:
            raise TypeError("Cannot set weather file to None")

    def load_contam_file(self, contam_file):
        """Load a csv or comma separated txt of pesticide residues in pollen/nectar using the library interface."""
        try:
            ct = open(contam_file)
            contamlines = ct.readlines()
            ct.close()
            self.contam_file = contam_file
        except:
            raise OSError("Residue file is invalid.")
        CPA = (ctypes.c_char_p * len(contamlines))()
        contamlines_bytes = StringList2CPA(contamlines)
        CPA[:] = contamlines_bytes
        if self.lib.SetContaminationTableCPA(CPA, len(contamlines)):
            if self.verbose:
                print("Loaded residue file")
        else:
            raise RuntimeError("Error loading residue file")
        self.send_pars_to_beepop(["NecPolFileEnable=true"], silent=True)  # enable residue files

    def set_latitude(self, latitude):
        """Set the latitude for calculation of day length using the library interface."""
        c_double_lat = ctypes.c_double(latitude)
        if self.lib.SetLatitude(c_double_lat):
            if self.verbose:
                print("Set Latitude to: {}".format(latitude))
        else:
            print("Error setting latitude")

    def run_beepop(self):
        """Run the BeePop+ model once using the previously set parameters and weather.

        Raises:
            RuntimeError: If BeePop+ passes an error code when running the simulation.

        Returns:
            DataFrame: A pandas DataFrame of daily BeePop+ outputs.
        """
        if self.lib.RunSimulation():
            self.lib_status = 1
        else:
            self.lib_status = 2
            raise RuntimeError("Error running BeePop+ simulation.")
        # fetch results
        theCount = ctypes.c_int(0)
        p_Results = ctypes.POINTER(ctypes.c_char_p)()
        if self.lib.GetResultsCPA(ctypes.byref(p_Results), ctypes.byref(theCount)):
            # store results
            n_result_lines = int(theCount.value)
            self.lib.ClearResultsBuffer()
            out_lines = []
            for j in range(0, n_result_lines - 1):
                out_lines.append(p_Results[j].decode("utf-8", errors="replace"))
            out_str = io.StringIO("\n".join(out_lines))
            out_df = pd.read_csv(
                out_str, sep="\\s+", skiprows=3, names=colnames, dtype={"Date": str}
            )
            self.results = out_df
        else:
            print("Error running BeePop+ and fetching results.")
        self.clear_buffers()
        return self.results

    def write_results(self, file_path):
        """Write previously generated BeePop+ outputs to a csv file."""
        results_file = file_path
        if self.results is None:
            raise RuntimeError("There are no results to write. Please run the model first")
        self.results.to_csv(results_file, index=False)
        if self.verbose():
            print("Wrote results to file")

    def get_errors(self):
        """Return the BeePop+ error log as a string using the library interface."""
        p_Errors = ctypes.POINTER(ctypes.c_char_p)()
        count = ctypes.c_int()
        if self.lib.GetErrorListCPA(ctypes.byref(p_Errors), ctypes.byref(count)):
            error_lines = []
            for j in range(count.value):
                error_lines.append(p_Errors[j].decode("utf-8", errors="replace"))
            # self.lib.ClearErrorList()
        else:
            raise RuntimeError("Failed to get error log")
        return "\n".join(error_lines)

    def get_info(self):
        """Return the BeePop+ info log as a string using the library interface."""
        p_Info = ctypes.POINTER(ctypes.c_char_p)()
        count = ctypes.c_int()
        if self.lib.GetInfoListCPA(ctypes.byref(p_Info), ctypes.byref(count)):
            info_lines = []
            for j in range(count.value):
                info_lines.append(p_Info[j].decode("utf-8", errors="replace"))
            # self.lib.ClearInfoList()
        return "\n".join(info_lines)

    def get_version(self):
        """Return the BeePop+ version as a string using the library interface."""
        buffsize = 16
        version_buffer = ctypes.create_string_buffer(buffsize)
        result = self.lib.GetLibVersionCP(version_buffer, buffsize)
        if result:
            return version_buffer.value.decode("utf-8")
        else:
            raise RuntimeError("Failed to get library version")

    def close_library(self):
        """Close connection to the library using CTypes."""
        dlclose_func = ctypes.CDLL(None).dlclose
        dlclose_func.argtypes = [ctypes.c_void_p]
        handle = self.lib._handle
        self.lib = None
        del self.lib
