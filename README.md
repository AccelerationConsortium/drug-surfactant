# Drug-Surfactant Optimization

This repository contains code for drug-surfactant optimization using Opentrons robots and the Ax optimization platform.

## Quick Start

### 1. Test Repository Health
```bash
python3 test_basic.py
```

### 2. Check Dependencies
```bash
python3 test_advanced.py
```

### 3. Install Dependencies
```bash
# Option A: Use pip with requirements file
pip install -r requirements.txt

# Option B: Use the installation helper
python3 install_deps.py

# Option C: Install manually
pip install numpy pandas matplotlib ax-platform
```

### 4. Test Functionality
```bash
# Test helper functions
python3 -c "import helper_functions; print(helper_functions.virtual_exp(1,2,3,4,5,6,7,8,9,10,11,12))"

# For minimal functionality without ax-platform
python3 -c "import helper_functions_minimal; print(helper_functions_minimal.virtual_exp(1,2,3,4,5,6,7,8,9,10,11,12))"
```

## Files

- `helper_functions.py` - Core optimization functions (requires ax-platform)
- `helper_functions_minimal.py` - Basic functions without heavy dependencies  
- `drug_surfactant_otflex.py` - Opentrons protocol for robot execution
- `test_basic.py` - Basic repository health checks
- `test_advanced.py` - Advanced dependency testing
- `install_deps.py` - Dependency installation helper

## Usage

The main workflow involves:
1. Using helper functions to set up optimization
2. Running experiments (virtual or real robot)
3. Analyzing results

See `workflow_test.ipynb` for detailed examples.

## Troubleshooting

- **Import errors**: Run `python3 test_advanced.py` to identify missing dependencies
- **Network timeouts**: Try `python3 install_deps.py` for safer installation
- **Robot connection**: Check network settings in helper functions

## Dependencies

- Python 3.7+
- numpy, pandas, matplotlib (data handling)
- ax-platform (optimization)
- opentrons (robot control, optional)