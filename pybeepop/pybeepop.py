'''
pybeepop - BeePop+ Wrapper for Python
code by Jeff Minucci
7/10/24
'''

import os
import pandas as pd
from .tools import BeePopModel
import json

class PyBeePop():

    def __init__(self, lib_file, parameters = None, input_file = None, weather_file = 'Columbus',
                 verbose = False):
        '''
        Initialize a pybeepop model object

        :param parameters: named dictionary of BeePop+ input parameters and their values
        :param weather_file: Full path to the weather file e.g. C:/VarroaPop/weather.wea (must be .wea/.dvf/.wth) OR
            one of either 'Columbus' (default), 'Sacramento', 'Phoenix', 'Yakima', 'Eau Claire', 'Jackson', or 'Durham'
        :param verbose: True or false, print messages?

        :return: Nothing
        '''
        #check file paths
        self.parent = os.path.dirname(os.path.abspath(__file__))
        if lib_file is None:
            lib_file = os.path.join(self.parent, 'files/exe/liblibvpop.so')
        if not os.path.isfile(lib_file):
            raise FileNotFoundError('BeePop+ shared object library does not exist at path: {}!'.format(lib_file))
        self.lib_file = lib_file
        #self.new_features = new_features # not being used?
        self.verbose = verbose
        if parameters is not None:
            if not isinstance(parameters, dict):
                raise TypeError('parameters must be a named dictionary of BeePop+ parameters')
        self.weather_file = None
        self.contam_file = None
        self.output = None
        self.input_file = None
        self.beepop = BeePopModel(self.lib_file, verbose=self.verbose)
        self.parameters = self.beepop.set_parameters(parameters)


    def set_parameters(self, parameters=None):
        '''
        Set or update the parameters 

        :param parameters: named dictionary of BeePop+ input parameters and their values

        :return: Nothing
        '''
        if (parameters is not None) and (not isinstance(parameters, dict)):
            raise TypeError('parameters must be a named dictionary of BeePop+ parameters')
        self.parameters = self.beepop.set_parameters(parameters)
    
    def get_parameters(self):
        return self.beepop.get_parameters()


    def load_weather(self, weather_file):
        '''
        Set the weather option

        :param weather_file: Full path to the weather file e.g. C:/VarroaPop/weather.wea (must be .wea/.dvf/.wth) OR
            one of either 'Columbus' (default), 'Sacramento', 'Phoenix', 'Yakima', 'Eau Claire', 'Jackson', or 'Durham'
        :return: Nothing
        '''
        self.weather_file = weather_file
        self.beepop.load_weather(self.weather_file)
    
    def load_input_file(self, input_file):
        self.input_file = input_file
        self.beepop.load_input_file(self.input_file)
    
    def load_contamination_file(self,file):
        self.contam_file = file
        self.beepop.load_contam_file(self.contam_file)
    
    def run_model(self):
        '''
        Run the BeePop+ model.

        :return: output as a pandas DataFrame
        '''

        #check to see if parameters have been supplied
        if (self.input_file is None) and (self.parameters is None):
            pass
            #raise Exception('Parameters must be set before running BeePop+!')
        if self.weather_file is None:
            raise Exception('Weather must be set before running BeePop+!')
        self.output = self.beepop.run_beepop()
        return self.output

    def get_output(self,format='dataframe'):
        '''
        Return the output from a BeePop+ run
        
        :param format: if 'dataframe', return pandas DataFrame object. If 'json', return json string.
        :return: If format equals 'dataframe' (default), returns results as a pandas DataFrame. If format 
        equals "json", returns results as a json string.
        '''
        if format == 'json':
            result = json.dumps(self.output.to_dict(orient='list'))
        else:
            result = self.output
        return result
    
    def get_error_log(self):
        return self.beepop.get_errors()
    
    def get_info_log(self):
        return self.beepop.get_info()
    
    def version(self):
        version = self.beepop.get_version()
        #print(version)
        return version
    
    def exit(self):
        self.beepop.close_library()
        del self.beepop
        return







