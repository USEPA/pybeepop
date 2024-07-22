[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3461089.svg)](https://doi.org/10.5281/zenodo.3461089)


# pybeepop
Python-based wrapper for the USDA/EPA's honey bee colony model BeePop+.

For more information about BeePop+ see the [publication in Ecologies](https://doi.org/10.3390/ecologies3030022).

Developed by: Jeffrey Minucci
<br><br>

#### Quick Start guide: 

1. **Requirements:** 
    * You must have **BeePop+ (aka VPopLib) version 0.1.0-beta or greater** installed locally. 
    * Currently, BeePop+ is only available on **Linux**. Source code and compliation instructions are available on [GitHub](https://github.com/quanted/vpoplib]).
    * You must also have the **pandas** package installed in your python environment.

2. **Clone this repo**, ideally into the directory where your python code or project will be.

3.  **Import the PyBeePop class** from  VarroaPy/VarroaPy/RunVarroaPop in python,
    e.g.:
    
        from pybeepop import PyBeePop
    
    
    if pybeepop is cloned to the same directory that your python script is in.
    
4. **Instantiate a BeePop+ object**, using a dictionary of parameters (parameter_name: value), and the path to a valid weather file.


        params = {"ICWorkerAdults": 10000, "ICWorkerBrood": 8000, "SimStart": "04/13/2015", "SimEnd": "09/15/2015"}
        weather = "Columbus"
        beepop = PyBeePop(parameters = params, weather_file = weather)
     
    Note that weather can be a path to a valid .wea or .wth file, or one of the included base weather locations, which are:    "Columbus" (OH; default), "Sacramento", "Phoenix", "Yakima", "Eau Claire", "Jackson" (MS), or "Durham (NC)"
    
    Parameters that are not set by the user will take on the BeePop+ default values. For more information see 
    
    For a list of exposed BeePop+ parameters, see docs/BeePop_exposed_parameters.xlsx


5. **Run the Model** 
    ```
    results = beepop.run_model()
    ```
    This will return the simulation results as a pandas DataFrame object. 

6. The last simulation can also be returned using the get_output function, with options to return a DataFrame or a json string.
    ```
    output = beepop.get_output()  # pandas dataframe
    output_json = beepop.get_output(json_str=True)  # json string
    ```
    
7. You can pass new parameters and/or update previously set ones (and optionally set a new weather file), and then run the model again. Parameters that were previously defined will remain set

    ```
    params_new = {"ICWorkerAdults": 22200, "InitColPollen": 4000}
    # Updates value for ICWorkerAdults, new value for InitColPollen, other values set previously remain the same.
    beepop.set_parameters(parameters = params_new)
    vp.run_model()
    ```
