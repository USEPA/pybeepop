# pybeepop+ 🐝

<div align="center">

[![Tests](https://github.com/USEPA/pybeepop/actions/workflows/run-tests.yml/badge.svg)](https://github.com/USEPA/pybeepop/actions/workflows/run-tests.yml)
[![PyPI version](https://badge.fury.io/py/pybeepop-plus.svg)](https://badge.fury.io/py/pybeepop-plus)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

**A Python interface for the USDA/EPA BeePop+ honey bee colony simulation model**

[Installation](#quick-start-guide) •
[Documentation](https://usepa.github.io/pybeepop/) •
[Examples](#example-notebook) •
[Contributing](#contributing)

</div>

## About

**pybeepop+** provides a Python interface to BeePop+, an agent-based model for simulating honey bee (*Apis mellifera* L.) colony dynamics. The model is designed for ecological risk assessment and research applications.

> **References**: 
> 
> Minucci, J. (2025). "pybeepop+: A Python Interface for the BeePop+ Honey Bee Colony Model." *Journal of Open Research Software*, 13(1). [https://doi.org/10.5334/jors.550](https://doi.org/10.5334/jors.550)
>
> Garber, K., et al. (2022). "Simulating the Effects of Pesticides on Honey Bee (Apis mellifera L.) Colonies with BeePop+." *Ecologies*, 3(3), 22. [https://doi.org/10.3390/ecologies3030022](https://doi.org/10.3390/ecologies3030022)

**Package author**: Jeffrey Minucci, U.S. Environmental Protection Agency 

## Table of Contents

- [Requirements](#requirements)
- [Choosing a Simulation Engine](#choosing-a-simulation-engine)
- [Quick Start Guide](#quick-start-guide)
- [Minimal Working Example](#minimal-working-example)
- [Example Notebook](#example-notebook)
- [API Documentation](#api-documentation)
- [Compiling BeePop+ on Linux](#compiling-beepop-on-linux)
- [Contributing to pybeepop+](#contributing)

## Requirements

### Core Dependencies (All Engines)

| Package | Version | Purpose |
|---------|---------|----------|
| Python | ≥ 3.8 | Runtime environment |
| pandas | > 2.0.0 | Data handling |
| matplotlib | > 3.1.0 | Visualization |

### C++ Engine Requirements (Optional)

> **Tip**: If you can't meet these requirements,  use the Python engine instead.

#### Supported Platforms
- Windows 64-bit
- Linux 64-bit
- macOS (Python engine only)

#### Platform-Specific Dependencies

**Windows**  
- [Microsoft Visual C++ Redistributable 2015-2022](https://www.microsoft.com/en-us/download/details.aspx?id=48145)

**Linux**  
- The bundled library supports **manylinux/musllinux** standards (musllinux via wheel only)
- If you encounter loading errors, see [Compiling BeePop+ on Linux](#compiling-beepop-on-linux)
- Source code: [github.com/quanted/vpoplib](https://github.com/quanted/vpoplib)

**macOS**
- Only the Python engine is supported (C++ engine unavailable due to architecture compatibility issues)


## Choosing a Simulation Engine

**pybeepop+** supports two simulation engines:
- **C++ engine** (default on Windows/Linux): The original published C++ implementation, requires compiled binaries
- **Python engine** (default on macOS): A pure Python port for improved portability and easier code inspection, with no binary dependencies

Both engines produce nearly identical results, with only negligible differences in some floating-point calculations.

> **Note**: On macOS, only the Python engine is available. The C++ engine is not supported due to architecture-specific compatibility issues.

### Selecting an Engine

Specify the engine when creating a `PyBeePop` instance using the `engine` parameter:

```python
from pybeepop import PyBeePop

# Automatic selection (default) - tries C++ first, falls back to Python
beepop = PyBeePop(engine='auto')

# Explicitly use C++ engine
beepop = PyBeePop(engine='cpp')

# Explicitly use Python engine  
beepop = PyBeePop(engine='python')
```


## Quick Start Guide

### Installation

```bash
pip install pybeepop-plus
```

### Basic Usage

```python
from pybeepop import PyBeePop

# 1. Create a BeePop+ instance (auto-selects best available engine)
beepop = PyBeePop()

# 2. Configure simulation parameters
params = {
    "ICWorkerAdults": 10000,
    "ICWorkerBrood": 8000,
    "SimStart": "04/13/2015",
    "SimEnd": "09/15/2015",
    "AIAdultLD50": 0.04
}
beepop.set_parameters(params)

# 3. Load weather data
beepop.load_weather('path/to/weather.txt')

# 4. (Optional) Load pesticide exposure data
beepop.load_residue_file('path/to/residues.txt')

# 5. Run simulation
results = beepop.run_model()
print(results)
```



### Working with Results

```python
# Get results as DataFrame
results_df = beepop.get_output()

# Get results as JSON
results_json = beepop.get_output(json_str=True)

# Visualize time series
beepop.plot_output()  # default columns
beepop.plot_output(["Colony Size", "Adult Workers"])  # custom columns
```

### Updating Parameters Between Runs

```python
# Update specific parameters (others remain unchanged)
beepop.set_parameters({"ICWorkerAdults": 22200, "InitColPollen": 4000})
results_updated = beepop.run_model()
```

### Loading Parameters from File

```python
# Parameters file format (key=value per line)
# Example: my_parameters.txt
#   RQEggLayDelay=10
#   RQReQueenDate=06/25/2015
#   RQEnableReQueen=False

beepop.load_parameter_file('my_parameters.txt')
params = beepop.get_parameters()
```

---

### Additional Resources

- **Parameter Reference**: [Exposed BeePop+ Parameters](https://usepa.github.io/pybeepop/pybeepop.html)
- **Weather File Format**: [docs/weather_readme.txt](https://github.com/USEPA/pybeepop/blob/main/docs/weather_readme.txt)
- **Residue File Format**: [docs/residue_file_readme.txt](https://github.com/USEPA/pybeepop/blob/main/docs/residue_file_readme.txt)
- **Example Files**: [example_data/](https://github.com/USEPA/pybeepop/tree/main/example_data)

> **Note**: Parameters not explicitly set will use BeePop+ default values. See the [publication](https://doi.org/10.3390/ecologies3030022) for details.


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


## Example Notebook

A  Jupyter notebook demonstrating `pybeepop+` usage is available here:

**→** [pybeepop_example.ipynb](https://github.com/USEPA/pybeepop/blob/main/pybeepop_example.ipynb)


## API Documentation

Complete API reference and usage guide:

**→** [https://usepa.github.io/pybeepop/](https://usepa.github.io/pybeepop/)


## Compiling BeePop+ on Linux


### Build Requirements
- `cmake` ≥ 3.2
- `gcc` or `g++`

### Compilation Steps

```bash
# 1. Clone the BeePop+ repository
git clone https://github.com/quanted/VPopLib.git
cd VPopLib

# 2. Create and enter build directory
mkdir build
cd build

# 3. Build the shared library
cmake -DCMAKE_POSITION_INDEPENDENT_CODE=ON ..
cmake --build . --config Release
```

### Using Your Custom Build

The compiled library (`liblibvpop.so`) will be in the `build/` directory. Use it with pybeepop:

```python
from pybeepop import PyBeePop

# Pass the path to your compiled library
beepop = PyBeePop(lib_file='/home/example/liblibvpop.so')
```


## Contributing

We welcome community contributions. Here's how you can help:

### Code Contributions
Fork the repository and submit pull requests. All submissions will be reviewed by maintainers.

### Bug Reports
Found a bug? Please [open an issue](https://github.com/USEPA/pybeepop/issues) with:
- Description of the problem
- Steps to reproduce
- Expected vs. actual behavior
- System information (OS, Python version, etc.)

### Support & Questions
Need help? [Open an issue](https://github.com/USEPA/pybeepop/issues) on GitHub.

## Disclaimer

This software is provided "as is" without warranty of any kind. The views expressed in this package are those of the authors and do not necessarily represent the views or policies of the U.S. Environmental Protection Agency.