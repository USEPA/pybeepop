# BeePop+ Python Interface

This directory contains the Python port of the BeePop+ library for bee colony simulation.

## Overview

BeePop+ provides a comprehensive interface for simulating honeybee colony dynamics, including:
- Colony population modeling (eggs, larvae, pupae, adults, foragers)
- Varroa mite population dynamics
- Weather-driven behavioral responses
- Pesticide exposure and mortality modeling
- Supplemental feeding and resource management
- Immigration and migration effects
- Results export as pandas DataFrames for data analysis

## Files

### Core Classes
- `colony.py` - Main Colony class with complete bee population simulation
- `session.py` - Session class for simulation management
- `weatherevents.py` - Weather event handling and forage day calculations
- `epadata.py` - EPA pesticide data and dose-response modeling
- `queen.py` - Queen bee egg-laying behavior
- `bee.py`, `adult.py`, `larva.py`, `egg.py`, `brood.py` - Individual bee life stages
- `mite.py` - Varroa mite modeling
- `colonyresource.py` - Colony resource (pollen/nectar) management

### Interface
- `beepop.py` - Main BeePop+ Python interface (refactored from vpoplib.cpp)
- `test_vpoplib.py` - Test script demonstrating BeePop+ usage

### Supporting Classes
- `beelist.py` - Base bee list management
- `daterangevalues.py` - Date range value handling
- `globaloptions.py` - Global simulation options
- `nutrientcontaminationtable.py` - Contamination table management
- `mitetreatments.py` - Mite treatment scheduling

## Usage

### Basic Usage

```python
from beepop import BeePop

# Create BeePop+ instance
beepop = BeePop()

# Set simulation parameters
beepop.set_latitude(40.0)
beepop.enable_error_reporting(True)
beepop.enable_info_reporting(True)

# Initialize the model
beepop.initialize_model()

# Load parameters from file (new feature)
beepop.load_parameter_file("example_parameters.txt")

# Set additional initial conditions
initial_conditions = [
    "ICWorkerAdults=10000",
    "ICWorkerBrood=5000",
    "SimStart=04/01/2023",
    "SimEnd=05/30/2023"
]
beepop.set_ic_variables_v(initial_conditions)

# Load weather data from file (new feature)
beepop.set_weather_from_file("weather_data.csv")

# Or set weather data manually
weather_data = [
    "01/01/2023,15.0,5.0,10.0,2.0,0.0,10.5",
    "01/02/2023,16.0,6.0,11.0,1.8,2.5,10.6",
    # ... more weather data
]
beepop.set_weather_v(weather_data)

# Run simulation
success = beepop.run_simulation()

if success:
    # Get results as pandas DataFrame (new feature)
    success, df = beepop.get_results_dataframe()
    if success and df is not None:
        print(f"Simulation completed with {len(df)} days of data")
        print(f"Columns: {list(df.columns)}")
        print(df[['Date', 'Colony Size', 'Adult Workers']].head())
    
    # Or get results as raw text (original method)
    success, results = beepop.get_results()
    if success:
        for line in results[:5]:  # Show first 5 lines
            print(line)
else:
    # Check for errors
    success, errors = beepop.get_error_list()
    if success:
        for error in errors:
            print(f"Error: {error}")
```

### Advanced Usage with DataFrames

```python
import pandas as pd
import matplotlib.pyplot as plt
from beepop import BeePop

# Set up and run simulation
beepop = BeePop()
beepop.set_latitude(35.0)
beepop.initialize_model()
beepop.load_parameter_file("parameters.txt")
beepop.set_weather_from_file("weather.csv")

if beepop.run_simulation():
    # Get results as DataFrame for analysis
    success, df = beepop.get_results_dataframe()
    
    if success and df is not None:
        # Basic statistics
        print(f"Average colony size: {df['Colony Size'].mean():.0f}")
        print(f"Peak colony size: {df['Colony Size'].max():.0f}")
        
        # Plot colony growth over time
        df['Date'] = pd.to_datetime(df['Date'])
        plt.figure(figsize=(12, 6))
        plt.plot(df['Date'], df['Colony Size'])
        plt.title('Colony Size Over Time')
        plt.xlabel('Date')
        plt.ylabel('Colony Size')
        plt.show()
        
        # Export to CSV
        df.to_csv('simulation_results.csv', index=False)
```

## API Reference

### Core Methods

#### Model Management
- `initialize_model()` → bool - Initialize the colony model
- `clear_results_buffer()` → bool - Clear results buffer
- `run_simulation()` → bool - Run the simulation
- `get_results()` → (bool, List[str]) - Get simulation results as text lines
- `get_results_dataframe()` → (bool, Optional[pd.DataFrame]) - **NEW**: Get results as pandas DataFrame

#### Parameters and Configuration  
- `set_latitude(lat: float)` → bool - Set simulation latitude
- `get_latitude()` → (bool, float) - Get simulation latitude
- `load_parameter_file(file_path: str)` → bool - **NEW**: Load parameters from file
- `set_ic_variables_s(name: str, value: str)` → bool - Set single initial condition
- `set_ic_variables_v(pairs: List[str], reset_ics: bool = True)` → bool - Set multiple initial conditions

#### Weather Data
- `set_weather_s(weather_string: str)` → bool - Set single weather event
- `set_weather_v(weather_list: List[str])` → bool - Set multiple weather events
- `set_weather_from_file(file_path: str, delimiter: str = None)` → bool - **NEW**: Load weather from file
- `clear_weather()` → bool - Clear weather data

#### Contamination
- `set_contamination_table(data: List[str])` → bool - Set contamination table
- `clear_contamination_table()` → bool - Clear contamination table

#### Error/Info Reporting
- `enable_error_reporting(enable: bool)` → bool - Enable/disable error reporting
- `enable_info_reporting(enable: bool)` → bool - Enable/disable info reporting
- `get_error_list()` → (bool, List[str]) - Get error messages
- `get_info_list()` → (bool, List[str]) - Get info messages
- `clear_error_list()` → bool - Clear error list
- `clear_info_list()` → bool - Clear info list

#### Version
- `get_lib_version()` → (bool, str) - Get library version

## Data Formats

### Weather Data Format
Weather strings should be comma or space delimited with fields:
```
Date, MaxTemp(°C), MinTemp(°C), AvgTemp(°C), Windspeed(m/s), Rainfall(mm), DaylightHours
```

Example: `"01/15/2023,12.5,2.1,7.3,3.2,0.0,9.5"`

**Weather File Format:** CSV or tab-separated files are supported. The `set_weather_from_file()` method auto-detects delimiters and handles headers.

### Initial Conditions Format
Initial condition pairs should be in "name=value" format:
```
"ParameterName=Value"
```

Examples:
- `"ICWorkerAdults=10000"`
- `"ICWorkerBrood=5000"`
- `"SimStart=04/01/2023"`
- `"SimEnd=05/30/2023"`

**Parameter File Format:** Text files with one parameter per line in `name=value` format. Comments (lines starting with #) are ignored.

### Contamination Data Format
Contamination table entries should be comma delimited:
```
Date, NectarConcentration(g_AI/g), PollenConcentration(g_AI/g)
```

Example: `"01/15/2023,0.000001,0.000002"`

### Results DataFrame Format
The `get_results_dataframe()` method returns a pandas DataFrame with 44 columns matching PyBeePop output:

| Column Name | Description | Units |
|-------------|-------------|-------|
| Date | Simulation date | MM/DD/YYYY |
| Colony Size | Total colony population | bees |
| Adult Drones | Adult drone population | bees |
| Adult Workers | Adult worker population | bees |
| Foragers | Total forager population | bees |
| Active Foragers | Currently active foragers | bees |
| Capped Worker Brood | Capped worker brood cells | cells |
| Worker Larvae | Worker larvae count | larvae |
| Worker Eggs | Worker egg count | eggs |
| Colony Nectar (g) | Colony nectar stores | grams |
| Colony Pollen (g) | Colony pollen stores | grams |
| Queen Strength | Queen laying strength | unitless 1 to 5 |
| Average Temperature (C) | Daily average temperature | °C |
| Daylight hours | Daily daylight duration | hours |
| ... | *[Plus 30 additional columns]* | various |

This format ensures compatibility with existing PyBeePop analysis workflows.


## Dependencies

Required:
- Python 3.6+
- pandas (for DataFrame functionality)
- datetime module
- typing module (for type hints)
- io module (for string processing)
- re module (for text parsing)

Optional:
- matplotlib (for plotting examples)
- scipy (for statistical analysis)