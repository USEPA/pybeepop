##
# BeePop+ Wrapper Tools for Python - linux version
# code by Jeff Minucci
# 5/2022
##

import os
import io
import ctypes
import pandas as pd

colnames = ["Date","Colony Size","Adult Drones","Adult Workers","Foragers", "Active Foragers", "Capped Drone Brood", "Capped Worker Brood",
             "Drone Larvae", "Worker Larvae", "Drone Eggs", "Worker Eggs", "Total Eggs", "DD", "L", "N", "P", "dd", "l", "n", "Free Mites", "Drone Brood Mites",
             "Worker Brood Mites", "Mites/Drone Cell", "Mites/Worker Cell", "Mites Dying", "Proportion Mites Dying",
             "Colony Pollen (g)", "Pollen Pesticide Concentration", "Colony Nectar", "Nectar Pesticide Concentration",
             "Dead Drone Larvae", "Dead Worker Larvae", "Dead Drone Adults", "Dead Worker Adults", "Dead Foragers",
             "Queen Strength", "Average Temperature (celsius)", "Rain", "Min Temp", "Max Temp", "Daylight hours", "Forage Inc", "Forage Day"]

# Utility function to convert a list of strings to bytes readble by the C++ library
def  StringList2CPA(theList):
    theListBytes = []
    for i in range(len(theList)):
        theListBytes.append(bytes(theList[i], 'utf-8'))
    return theListBytes

class BeePopModel:
    """
    BeePopModel

    Class to interact with the BeePop+ linux library.

    """

    def __init__(self, library_file, new_features=False, verbose = False):
        self.parameters = dict()
        self.weather_file = None
        self.contam_file = None
        #self.new_features = new_features
        self.verbose = verbose
        self.results = None
        self.lib = ctypes.CDLL(library_file)
        self.parent_dir = os.path.dirname(os.path.abspath(__file__))
        self.lib_status = None
        weather_dir = os.path.join(self.parent_dir,"files/weather")
        if self.lib.InitializeModel():  # Initialize model
            lib_status = self.lib.InitializeModel()
            if self.verbose:
                #print(lib_status)
                print('Model initialized')
        else:
            raise RuntimeError('BeePop+ could not be initialized.')
        self.clear_buffers()
    
    # clear C++ buffers
    def clear_buffers(self):  
        if not self.lib.ClearResultsBuffer():  # Clear Results and weather lists
            raise RuntimeError('Error clearing results buffer.')
        if not self.lib.ClearErrorList():
            raise RuntimeError('Error clearing error list')
        if not self.lib.ClearInfoList():
            raise RuntimeError('Error clearing info')
     
    #Load parameters from a file
    def load_input_file(self, in_file):   
        self.input_file = in_file
        icf = open(self.input_file)
        inputs = icf.readlines()
        icf.close()
        input_d = dict(x.replace(" ","").replace("\n","").split("=") for x in inputs)
        self.parameter_list_update(input_d) # update parameter dictionary
        inputlist = []
        for k, v in self.parameters.items():
            inputlist.append('{}={}'.format(k, v))
        self.send_pars_to_beepop(inputlist)
        return self.parameters
    
    # update the dictionary of parameters
    def parameter_list_update(self,parameters):
        to_add = dict((k.lower(), v) for k, v in parameters.items())
        self.parameters.update(to_add)
    
    # set parameters based on a python dictionary
    def set_parameters(self, parameters=None):
        refresh = False
        if parameters is not None:
            self.parameter_list_update(parameters)
        else:
            refresh = True # is this refresh variable needed?
            if len(self.parameters) < 1:
                return
        inputlist = []
        for k, v in self.parameters.items():
            inputlist.append('{}={}'.format(k, v))
        self.send_pars_to_beepop(inputlist, refresh=refresh)
        return self.parameters
    
    # interact with the BeePop+ library to set parameters from a list
    def send_pars_to_beepop(self, parameter_list, refresh=False):
        CPA = (ctypes.c_char_p * len(parameter_list))()
        inputlist_bytes = StringList2CPA(parameter_list)
        CPA[:] = inputlist_bytes
        if self.lib.SetICVariablesCPA(CPA, len(parameter_list)):
            if self.verbose and not refresh:
                print('Updated parameters')
        else:
            raise RuntimeError("Error setting parameters")
        #del CPA  # shouldn't be needed 
        #del inputlist_bytes
    
    # access the current list of parameters defined by the user
    def get_parameters(self):
        return self.parameters

    # load weather file .txt into BeePop+
    def load_weather(self, weather_file='durham'):
        self.weather_file = weather_file
        weather_dir = os.path.join(self.parent_dir,"files/weather")
        self.weather_locs = {'columbus': os.path.join(weather_dir,'18815_grid_39.875_lat.wea'),
                             'sacramento': os.path.join(weather_dir,'17482_grid_38.375_lat.wea'),
                             'phoenix': os.path.join(weather_dir, '12564_grid_33.375_lat.wea'),
                             'yakima': os.path.join(weather_dir, '25038_grid_46.375_lat.wea'),
                             'eau claire': os.path.join(weather_dir, '23503_grid_44.875_lat.wea'),
                             'jackson': os.path.join(weather_dir, '11708_grid_32.375_lat.wea'),
                             'durham': os.path.join(weather_dir, '15057_grid_35.875_lat.wea')}
        if self.weather_file.lower() in self.weather_locs.keys():
            self.weather_file = self.weather_locs[self.weather_file.lower()]
        if self.weather_file is not None:
            try:
                wf = open(self.weather_file)
                weatherlines = wf.readlines()
                wf.close()
            except:
                raise OSError("Weather file is invalid.")
            CPA = (ctypes.c_char_p * len(weatherlines))()
            weatherline_bytes = StringList2CPA(weatherlines) 
            CPA[:] = weatherline_bytes
            if self.lib.SetWeatherCPA(CPA, len(weatherlines)):
                if self.verbose:
                    print('Loaded Weather')
            else:
                raise RuntimeError("Error Loading Weather")
            #del CPA  # shouldn't be needed
            #del weatherline_bytes
        else:
            raise TypeError("Cannot set weather file to None")
    
    def load_contam_file(self, contam_file):
        self.contam_file = contam_file
        try:
            ct = open(contam_file)
            contamlines = ct.readlines()
            ct.close()
        except:
            raise OSError("Contamination file is invalid.")
        CPA = (ctypes.c_char_p * len(contamlines))()
        contamlines_bytes = StringList2CPA(contamlines)
        CPA[:] = contamlines_bytes
        if self.lib.SetContaminationTableCPA(CPA, len(contamlines)):
            if self.verbose:
                print('Loaded contamination file')
        else:
            raise RuntimeError("Error loading contamination file")
        #del CPA  # shouldn't be needed
        #del contamlines_bytes
        
    def set_latitude(self, latitude):
        c_double_lat = ctypes.c_double(latitude)
        if(self.lib.SetLatitude(c_double_lat)):
            if self.verbose:
                print('Set Latitude to: {}'.format(latitude))
        else:
                print('Error setting latitude')
       

    def run_beepop(self):
        if self.lib.RunSimulation():
            self.lib_status = 1
        else :
            self.lib_status = 2
            if self.verbose:
                print('Error in sumulation')
        # fetch results
        theCount = ctypes.c_int(0)
        p_Results = ctypes.POINTER(ctypes.c_char_p)()
        if self.lib.GetResultsCPA(ctypes.byref(p_Results),ctypes.byref(theCount)):
            # Store Reaults
            n_result_lines = int(theCount.value)
            self.lib.ClearResultsBuffer()
            out_lines = []
            for j in range(0, n_result_lines-1): 
                out_lines.append(p_Results[j].decode('utf-8', errors='replace'))
                #out_lines.append(str(p_Results[j]))
            out_str = io.StringIO('\n'.join(out_lines))
            out_df = pd.read_csv(out_str, delim_whitespace=True, skiprows=3, names = colnames, dtype={'Date': str})
            self.results = out_df
        else:
            print('Error getting results')
        self.clear_buffers()
        #del theCount  # shouldn't be needed but trying to fix progressive slowdown issue
        #del p_Results
        return self.results
        
    def write_results(self, file_path):
        results_file = file_path
        if self.results is None:
            raise RuntimeError("There are no results to write. Please run the model first")
        self.results.to_csv(results_file, index=False)
        if self.verbose():
            print('Wrote results to file')
            
    def get_errors(self):
        p_Errors = ctypes.POINTER(ctypes.c_char_p)()
        NumErrors = ctypes.c_int(0)
        error_str = ""
        if self.lib.GetErrorListCPA(ctypes.byref(p_Errors), ctypes.byref(NumErrors)):
            print("inside error list function")
            n_error_lines = int(NumErrors.value)
            error_lines = []
            for j in range(0, n_error_lines-1): 
                error_lines.append(p_Errors[j])#.decode('ISO-8859-1', errors='replace'))
            #error_str = io.StringIO('\n'.join(error_lines)).getvalue()
            #outfile = open(errorpath, "w")
            #for j in range(0,max-1):
            #    outfile.write(p_Errors[j].decode("utf-8"))
            #outfile.close()
            #if self.verbose and (max > 0):
            #    print('Wrote errors to {}'.format(errorpath))
            self.lib.ClearErrorList()
        return error_lines
    
    def get_info(self):
        p_Info = ctypes.POINTER(ctypes.c_char_p)()
        NumInfo = ctypes.c_int(0)
        info_str = ""
        if self.lib.GetInfoListCPA(ctypes.byref(p_Info), ctypes.byref(NumInfo)):
            print("inside info list function")
            n_info_lines = int(NumInfo.value)
            info_lines = []
            for j in range(0, n_info_lines-1): 
                info_lines.append(p_Info[j].decode('utf-8', errors='replace'))
            into_str = io.StringIO('\n'.join(info_lines)).getvalue()
            self.lib.ClearInfoList()
        return info_str
    
    def get_version(self):
        p_version= ctypes.POINTER(ctypes.c_char_p)()
        buffsize = ctypes.c_int(0)
        print("getting version")
        version = []
        if self.lib.GetLibVersionCP(ctypes.byref(p_version), ctypes.byref(buffsize)):
            n_version_lines = int(buffsize.value)
            for j in range(0, n_version_lines-1): 
                version.append(p_version[j].decode('utf-8', errors='replace'))
        return version
            
    def close_library(self):
        dlclose_func = ctypes.CDLL(None).dlclose
        dlclose_func.argtypes = [ctypes.c_void_p]
        handle = self.lib._handle
        self.lib = None
        del self.lib