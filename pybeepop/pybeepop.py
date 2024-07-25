"""
pybeepop - BeePop+ Wrapper for Python
code by Jeff Minucci
7/10/24
"""

import os
import pandas as pd
from .tools import BeePopModel
import json


class PyBeePop:
    """Wrapper for the BeePop+ honey bee colony simulation model"""

    def __init__(
        self, lib_file, parameter_file=None, weather_file=None, residue_file=None, verbose=False
    ):
        """Create a PyBeePop object connected to a BeePop+ shared library.

        Args:
            lib_file (str): Path to the BeePop+ shared library.
            parameters_file (str, optional): Path to a txt file of BeePop+ parameters where each line specifies
                parameter=value. Defaults to None.
            weather_file (str, optional): Path to a txt file containing weather data. For formatting info see
                docs/weather_readme.txt. Defaults to None.
            residue_file (str, optional): Path to a txt file containing pesticide residue data. Defaults to None.
            verbose (bool, optional): Print additional debugging statements? Defaults to False.

        Raises:
            FileNotFoundError: If a provided file does not exist at the specified path.
        """

        # check file paths
        self.parent = os.path.dirname(os.path.abspath(__file__))
        # if lib_file is None:
        #    lib_file = os.path.join(self.parent, "files/exe/liblibvpop.so")
        if not os.path.isfile(lib_file):
            raise FileNotFoundError(
                "BeePop+ shared object library does not exist at path: {}!".format(lib_file)
            )
        self.lib_file = lib_file
        self.parameters = None
        if parameter_file is not None:
            self.load_parameter_file(self.parameter_file)
        else:
            self.parameter_file = None
        if weather_file is not None:
            self.load_weather(weather_file)
        else:
            self.weather_file = None
        if residue_file is not None:
            self.load_residue_file(self.residue_file)
        else:
            self.residue_file = None
        # self.new_features = new_features # not being used?
        self.verbose = verbose
        self.output = None
        self.beepop = BeePopModel(self.lib_file, verbose=self.verbose)

    def set_parameters(self, parameters):
        """Set BeePop+ parameters based on a dictionary {parameter: value}.

        Args:
            parameters (dict): dictionary of parameteres {parameter: value}.

        Raises:
            TypeError: If parameters is not a dict.
        """
        if (parameters is not None) and (not isinstance(parameters, dict)):
            raise TypeError("parameters must be a named dictionary of BeePop+ parameters")
        self.parameters = self.beepop.set_parameters(parameters)

    def get_parameters(self):
        """Return all parameters that have been set by the user."""
        return self.beepop.get_parameters()

    def load_weather(self, weather_file):
        """Load a weather txt file. This should be a tab delimited txt file where each line denotes:
        Date(MM/DD/YY), Max Temp (C), Min Temp (C), Avg Temp (C), Windspeed (m/s), Rainfall (mm),
        Hours of daylight (optional).

        Args:
            weather_file (_type_): Path to the weather file .txt.

        Raises:
            FileNotFoundError: If the provided file does not exist at the specified path.
        """
        if not os.path.isfile(weather_file):
            raise FileNotFoundError("Weather file does not exist at path: {}!".format(weather_file))
        self.weather_file = weather_file
        self.beepop.load_weather(self.weather_file)

    def load_parameter_file(self, parameter_file):
        """Load a .txt file of parameter values to set. Each line of the file is a string with the
        format 'paramter=value'.

        Args:
            parameter_file (_type_): Path to a txt file of BeePop+ parameters.


        Raises:
            FileNotFoundError: If the provided file does not exist at the specified path.
        """
        if not os.path.isfile(parameter_file):
            raise FileNotFoundError(
                "Paramter file does not exist at path: {}!".format(parameter_file)
            )
        self.parameter_file = parameter_file
        self.beepop.load_input_file(self.parameter_file)

    def load_residue_file(self, residue_file):
        """Load a .txt file of pesticide residues in pollen/nectar. File should be comma separated
            with each line giving Date(MM/DD/YY), Concentration in nectar (g A.I. / g),
            Concentration in pollen (g A.I. / g)

        Args:
            residue_file (_type_): Path to the residue .txt file.

        Raises:
            FileNotFoundError: If the provided file does not exist at the specified path.
        """
        if not os.path.isfile(residue_file):
            raise FileNotFoundError("Residue file does not exist at path: {}!".format(residue_file))
        self.residue_file = residue_file
        self.beepop.load_contam_file(self.residue_file)

    def run_model(self):
        """_summary_

        Raises:
            RuntimeError: If the weather file has not yet been set.

        Returns:
            DataFrame: A DataFrame of the model results for the BeePop+ run.
        """
        # check to see if parameters have been supplied
        if (self.parameter_file is None) and (self.parameters is None):
            print("No parameters have been set. Running with defualt settings.")
        if self.weather_file is None:
            raise RuntimeError("Weather must be set before running BeePop+!")
        self.output = self.beepop.run_beepop()
        return self.output

    def get_output(self, format="DataFrame"):
        """Get the output from the last BeePop+ run.

        Args:
            format (str, optional): Return results as DataFrame ('DataFrame') or
                JSON string ('json')? Defaults to "DataFrame".

        Returns:
            DataFrame or json str: A DataFrame or JSON string of the model results for the BeePop+ run.
        """
        if format == "json":
            result = json.dumps(self.output.to_dict(orient="list"))
        else:
            result = self.output
        return result

    def get_error_log(self):
        """Return the BeePop+ session error log as a string for debugging."""
        return self.beepop.get_errors()

    def get_info_log(self):
        """Return the BeePop+ session info log as a string for debugging."""
        return self.beepop.get_info()

    def version(self):
        """Return the BeePop+ version as a string."""
        version = self.beepop.get_version()
        return version

    def exit(self):
        """Close the connection to the BeePop+ shared library."""
        self.beepop.close_library()
        del self.beepop
        return
