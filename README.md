# pybeepop :honeybee:
Python-based wrapper for the USDA/EPA's honey bee colony model **BeePop+**.

For more information about **BeePop+** see [Garber *et al.* 2022](https://doi.org/10.3390/ecologies3030022).

Developed by: Jeffrey Minucci 

## Table of Contents

- [Requirements](#requirements)
- [Quick Start Guide](#quick-start-guide)
- [API Documentation](#api-documentation)
- [Compiling BeePop+ on Linux](#compiling-beepop-on-linux)
- [Contributing to pybeepop](#contributing-to-pybeepop)

## Requirements

* Supported platforms: 
    * Windows 64-bit (x64)
    * Linux
* For **Windows**: [Microsoft Visual C++ Redistributable 2015-2022](https://www.microsoft.com/en-us/download/details.aspx?id=48145)
* For **Linux**, the bundled BeePop+ library was compiled on **Red Hat Enterprise Linux 8 (RHEL8)**. If you encounter errors loading the library, you can try compiling BeePop+ yourself from source. Instructions for compiling BeePop+ for Linux are [below](#compiling-beepop-on-linux). Source code is available on [the project's GitHub page](https://github.com/quanted/vpoplib]).
* Python version 3.6 or above.
* pandas installed in your Python environment.


## Quick Start Guide

1. **Clone this repo**, ideally into the directory where your python code or project will be.

        git clone https://github.com/USEPA/pybeepop.git
        
2.  **Import the PyBeePop class** in your python code, e.g.:
    
        from pybeepop import PyBeePop
    
    (if pybeepop is cloned to the same directory that your python script is in.)
  
  
3. **Create a BeePop+ object**:

        beepop = PyBeePop()
        

4. **Set parameters, weather and pesticide exposure levels (optional)**.

        # define a dictionary of BeePop+ parameters (parameter_name: value)
        params = {"ICWorkerAdults": 10000, "ICWorkerBrood": 8000, 
            "SimStart": "04/13/2015", "SimEnd": "09/15/2015",
            "AIAdultLD50: 0.04"}
        beepop.set_parameters(params)
        
        # load your weather file by giving its path
        weather = '/home/example/test_weather.txt'
        beepop.load_weather(weather)
        
        # load your pesticide residue file by giving its path (optional)
        pesticide_file = '/home/example/pesticide_residues.txt'
        beepop.load_contamination_file(pesticide_file)
     
    <br>Parameters that are not set by the user will take on the BeePop+ default values. For more information see [the BeePop+ publication](https://doi.org/10.3390/ecologies3030022).
    
    For a list of exposed BeePop+ parameters, see [docs/BeePop_exposed_parameters.csv](https://github.com/USEPA/pybeepop/blob/main/docs/BeePop_exposed_parameters.csv).
    
    For an explanation of the required weather file formet, see docs/weather_readme.txt.
    
    
5. **Run the Model** and get the results as a pandas DataFrame
    ```
    results = beepop.run_model()
    print(results)
    ```


6. **Results from last simulation** can also be returned using the get_output function, with options to return a DataFrame or a json string.
    ```
    output = beepop.get_output()  # pandas dataframe
    output_json = beepop.get_output(json_str=True)  # json string
    ```


7. You can pass new parameters and/or update previously set ones (and optionally set a new weather file), and then run the model again. Parameters that were previously defined will remain set

    ```
    # update value for ICWorkerAdults, InitColPollen, other values set previously remain
    params_new = {"ICWorkerAdults": 22200, "InitColPollen": 4000}
    beepop.set_parameters(parameters = params_new)
    new_results = beepop.run_model()
    ```


8. You can also set parameters using a .txt file where each line gives a parameter in the format "Parameter=Value". 

    Example my_parameters.txt:
        
        RQEggLayDelay=10
        RQReQueenDate=06/25/2015
        RQEnableReQueen=False

    In Python:

        parameter_file = 'home/example/my_parameters.txt'
        my_parameters = beepop.load_input_file()
        print(my_parameters)


9. To get a list of the user-defined parameters:

        my_parameters = beepop.get_parameters()
        print(my_parameters)


## API Documentation

Documentation of the pybeepop API can be found at: https://usepa.github.io/pybeepop/.


## Compiling BeePop+ on Linux


### Requirements for compilation
* cmake > 3.2
* gcc and g++ compilers

### Compiling BeePop+ from source on Linux

1. Clone the BeePop+ repo:

        git clone https://github.com/quanted/VPopLib.git
    
2. Create a build directory:

        cd VPopLib
        mkdir build
        cd build
    
3. Build the shared library:

        cmake -DCMAKE_POSITION_INDEPENDENT_CODE=ON ..  	
        cmake --build . --config Release
 
4. Now the .so file liblibvpop.so should have been created inside the /build directory. This shared library can be moved or renamed. You can pass the path to this .so file as lib_path when creating a PyBeePop object:
        
        # pass the path to your previously compiled shared library file
        lib_file = '/home/example/liblibvpop.so'
        beepop = PyBeePop(lib_file)


## Contributing to pybeepop

For those in the user community wishing to contribute to this project:

- Code updates or enhancements can be made by forking and submitting pull requests that will be reviewed by repository admins.
- Software, code, or algorithm related bugs and issues can be submitted directly as issues on the GitHub repository.
- Support can be requested through GitHub issues.