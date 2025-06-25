# pybeepop+ :honeybee:

[![Tests (Windows)](https://github.com/USEPA/pybeepop/actions/workflows/run-tests-windows.yml/badge.svg)](https://github.com/USEPA/pybeepop/actions/workflows/run-tests-windows.yml)
[![Tests (Linux)](https://github.com/USEPA/pybeepop/actions/workflows/run-tests-ubuntu.yml/badge.svg)](https://github.com/USEPA/pybeepop/actions/workflows/run-tests-ubuntu.yml)
[![PyPI version](https://badge.fury.io/py/pybeepop-plus.svg)](https://badge.fury.io/py/pybeepop-plus)

Python-based interface for the USDA/EPA's honey bee colony model **BeePop+**.

For more information about **BeePop+** see [Garber *et al.* 2022](https://doi.org/10.3390/ecologies3030022).

Developed by: Jeffrey Minucci 

## Table of Contents

- [Requirements](#requirements)
- [Quick Start Guide](#quick-start-guide)
- [Minimal Working Example](#minimal-working-example)
- [Example Notebook](#example-notebook)
- [API Documentation](#api-documentation)
- [Compiling BeePop+ on Linux](#compiling-beepop-on-linux)
- [Contributing to pybeepop+](#contributing-to-pybeepop)

## Requirements

* Supported platforms: 
    * Windows 64-bit
    * Linux 64-bit
* For **Windows**: [Microsoft Visual C++ Redistributable 2015-2022](https://www.microsoft.com/en-us/download/details.aspx?id=48145)
* For **Linux**, the bundled BeePop+ library was compiled for the **manylinux/musllinux** standards (musllinux via wheel only). 
If you encounter errors loading the library, you can try compiling BeePop+ yourself from source. Instructions for compiling BeePop+
for Linux are [below](#compiling-beepop-on-linux). Source code is available on [the project's GitHub page](https://github.com/quanted/vpoplib).
* Python version 3.8 or above.
* pandas > 2.0.0
* matplotlib > 3.1.0


## Quick Start Guide

1. **Install the package** into your Python environment using pip:

    ```sh
    pip install pybeepop-plus
    ```
    
2.  **Import the PyBeePop class** in your python code, e.g.:
    
    ```python
    from pybeepop import PyBeePop
    ```
  
3. **Create a BeePop+ object**:

    ```python
    beepop = PyBeePop()
    ```
    
4. **Set parameters, weather and pesticide exposure levels (optional)**.

    ```python
    # define a dictionary of BeePop+ parameters (parameter_name: value)
    params = {"ICWorkerAdults": 10000, "ICWorkerBrood": 8000, 
        "SimStart": "04/13/2015", "SimEnd": "09/15/2015",
        "AIAdultLD50": 0.04}
    beepop.set_parameters(params)
    
    # load your weather file by giving its path
    weather = '/home/example/test_weather.txt'
    beepop.load_weather(weather)
    
    # load your pesticide residue file by giving its path (optional)
    pesticide_file = '/home/example/pesticide_residues.txt'
    beepop.load_contamination_file(pesticide_file)
    ```
    
    <br>Parameters that are not set by the user will take on the BeePop+ default values. For more information see [the BeePop+ publication](https://doi.org/10.3390/ecologies3030022).
    
    For a list of exposed BeePop+ parameters, see [the documentation page](https://usepa.github.io/pybeepop/pybeepop.html).
    
    For an explanation of the **weather file format**, see [docs/weather_readme.txt](https://github.com/USEPA/pybeepop/blob/main/docs/weather_readme.txt).

    For an explanation of the **residue file format**, see [docs/residue_file_readme.txt](https://github.com/USEPA/pybeepop/blob/main/docs/residue_file_readme.txt).

    **Example files** to run the model can be found at [example_files/](https://github.com/USEPA/pybeepop/tree/main/example_data).
    
5. **Run the Model** and get the results as a pandas DataFrame
    ```python
    results = beepop.run_model()
    print(results)
    ```

6. **Results from last simulation** can also be returned using the get_output function, with options to return a DataFrame or a json string.
    ```python
    output = beepop.get_output()  # pandas dataframe
    output_json = beepop.get_output(json_str=True)  # json string
    ```

7. You can pass new parameters and/or update previously set ones (and optionally set a new weather file), and then run the model again. Parameters that were previously defined will remain set

    ```python
    # update value for ICWorkerAdults, InitColPollen, other values set previously remain
    params_new = {"ICWorkerAdults": 22200, "InitColPollen": 4000}
    beepop.set_parameters(parameters = params_new)
    new_results = beepop.run_model()
    ```

8. You can also set parameters using a .txt file where each line gives a parameter in the format "Parameter=Value". 

    Example my_parameters.txt:
    
    ```
    RQEggLayDelay=10
    RQReQueenDate=06/25/2015
    RQEnableReQueen=False
    ```

    In Python:

    ```python
    parameter_file = 'home/example/my_parameters.txt'
    my_parameters = beepop.load_input_file()
    print(my_parameters)
    ```

9. To get a list of the user-defined parameters:

    ```python
    my_parameters = beepop.get_parameters()
    print(my_parameters)
    ```

10. To plot the last output as a time series:

    ```python
    ax = beepop.plot_output()  # default columns

    cols_to_plot = ["Dead Worker Adults", "Dead Foragers"]
    ax = beepop.plot_output(cols_to_plot)  # custom columns
    ```


## Minimal Working Example

```python
from pybeepop import PyBeePop
import tempfile
import os

# Create minimal synthetic weather data
weather_data = """04/01/2023, 20.0, 10.0, 15.0, 3.0, 0.0, 12.0
04/02/2023, 22.0, 12.0, 17.0, 2.5, 0.0, 12.1
04/03/2023, 21.0, 11.0, 16.0, 3.2, 2.0, 12.2
04/04/2023, 19.0, 9.0, 14.0, 2.8, 0.0, 12.3
04/05/2023, 23.0, 13.0, 18.0, 2.1, 0.0, 12.4"""

# Write to temporary file
with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
    f.write(weather_data)
    temp_weather_file = f.name

try:
    # Create BeePop+ instance and run simulation
    beepop = PyBeePop()
    beepop.set_parameters(
        {"ICWorkerAdults": 10000, "ICWorkerBrood": 5000, "SimStart": "04/01/2023", "SimEnd": "04/05/2023"}
    )
    beepop.load_weather(temp_weather_file)

    # Run model and display results
    results = beepop.run_model()
    print(results[["Date", "Colony Size", "Adult Workers"]].head())

finally:
    # Clean up temporary file
    os.unlink(temp_weather_file)
```


## Example notebook

A Jupyter notebook with a working example of using `pybeepop+` is available [here](https://github.com/USEPA/pybeepop/blob/main/pybeepop_example.ipynb).


## API Documentation

Documentation of the pybeepop+ API can be found at: https://usepa.github.io/pybeepop/.


## Compiling BeePop+ on Linux


### Requirements for compilation
* cmake > 3.2
* gcc or g++ 

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


## Contributing to pybeepop+

For those in the user community wishing to contribute to this project:

- Code updates or enhancements can be made by forking and submitting pull requests that will be reviewed by repository admins.
- Software, code, or algorithm related bugs and issues can be submitted directly as issues on the GitHub repository.
- Support can be requested through GitHub issues.