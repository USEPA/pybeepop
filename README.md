[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3461089.svg)](https://doi.org/10.5281/zenodo.3461089)


# pybeepop
Python-based wrapper for the USDA/EPA's honey bee colony model **BeePop+**.

For more information about **BeePop+** see the [publication in Ecologies](https://doi.org/10.3390/ecologies3030022).

Developed by: Jeffrey Minucci
<br><br>

### Requirements

* You must have **BeePop+ (aka VPopLib) version 0.1.0-beta or greater** installed locally. 
* Currently, BeePop+ is only available on **Linux**. Instructions for compiling the model's shared library are below. Source code is available on [the project's GitHub page](https://github.com/quanted/vpoplib]).
* You must also have the **pandas** package installed in your python environment.

---

### Quick Start guide:

1. **Clone this repo**, ideally into the directory where your python code or project will be.

        git clone https://github.com/USEPA/pybeepop.git
        
2.  **Import the PyBeePop class** in your python code, e.g.:
    
        from pybeepop import PyBeePop
    
    (if pybeepop is cloned to the same directory that your python script is in.)
  
  
3. **Create a BeePop+ object**, by giving the path to your BeePop+ shared library object (e.g., liblibvpop.so). using a dictionary of parameters (parameter_name: value), and the path to a valid weather file.


        lib_file = os.path.abspath('/home/example/liblibvpop_rhel8.so')  # path to your shared library object
        beepop = PyBeePop(lib_file)
        

4. **Set parameters, weather and pesticide exposure levels (optional)**.

        params = {"ICWorkerAdults": 10000, "ICWorkerBrood": 8000, "SimStart": "04/13/2015", "SimEnd": "09/15/2015"}
        beepop.set_parameters(params)
        weather = os.path.abspath('/home/example/test_weather.txt')  # path to your weather file
        beepop.load_weather(weather)
        pesticide_file = os.path.abspath('/home/example/pesticide_residues.txt')  # path to your pesticide residue file (optional)
        beepop.load_contamination_file(pesticide_file)
     
    <br>Parameters that are not set by the user will take on the BeePop+ default values. For more information see [the BeePop+ publication](https://doi.org/10.3390/ecologies3030022).
    
    For a list of exposed BeePop+ parameters, see docs/BeePop_exposed_parameters.xlsx
    
    For an explanation of the required weather file formet, see docs/weather_readme.txt
    
5. **Run the Model** 
    ```
    results = beepop.run_model()
    ```
    This will return the simulation results as a pandas DataFrame object. 

6. Results from last simulation can also be returned using the get_output function, with options to return a DataFrame or a json string.
    ```
    output = beepop.get_output()  # pandas dataframe
    output_json = beepop.get_output(json_str=True)  # json string
    ```

7. You can pass new parameters and/or update previously set ones (and optionally set a new weather file), and then run the model again. Parameters that were previously defined will remain set

    ```
    params_new = {"ICWorkerAdults": 22200, "InitColPollen": 4000}
    # Updates value for ICWorkerAdults, new value for InitColPollen, other values set previously remain the same.
    beepop.set_parameters(parameters = params_new)
    new_results = beepop.run_model()
    ```
---

### How to compile BeePop+ on Linux

#### Prerequesites
* cmake > 3.2
* python > 3.6
* gcc and g++ compilers

#### Compiling

1. Clone the BeePop+ repo:

    git clone https://github.com/quanted/VPopLib.git
    
2. Create a build directory

    cd VPopLib
    mkdir build
    cd build
    
3. Build the shared library 

    cmake -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ -DCMAKE_CXX_FLAGS="-fPIC" -DCMAKE_C_FLAGS="-fPIC" ..  	
    make
 
4. Now the .so file liblibvpop.so should have been created inside the /build directory. This shared library can be moved or renamed, and it is the object that pybeepop must connect to via a valid path.