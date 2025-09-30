# drug-surfactant

Automated drug-surfactant formulation screening using the Opentrons Flex robot with UV-Vis absorbance measurements.

## Features

- Automated drug-surfactant mixture preparation
- Multi-wavelength UV-Vis absorbance measurements using the Opentrons Absorbance Plate Reader Module
- Bayesian optimization for formulation optimization
- Integration with Ax platform for experiment design

## Files

- `drug_surfactant_otflex.py` - Main protocol for drug-surfactant preparation
- `test_absorbance_reader.py` - Test protocol for UV-Vis absorbance measurements
- `drug_surfactant_with_absorbance.py` - Integrated workflow with absorbance measurements
- `helper_functions.py` - Utility functions for optimization and calculations
- `ABSORBANCE_READER_GUIDE.md` - Comprehensive guide for using the Absorbance Plate Reader

## Quick Start

### Basic UV-Vis Absorbance Measurement

See `test_absorbance_reader.py` for a complete example:

```python
# Load the Absorbance Plate Reader module
absorbance_reader = protocol.load_module(
    module_name="absorbanceReaderV1",
    location="D3"
)

# Initialize for multi-wavelength measurement
absorbance_reader.initialize(mode="multi", wavelengths=[450, 562, 600])

# Load plate and read
absorbance_reader.open_lid()
protocol.move_labware(plate, absorbance_reader, use_gripper=True)
absorbance_reader.close_lid()
data = absorbance_reader.read(export_filename="results")
```

### Integrated Drug-Surfactant Workflow

See `drug_surfactant_with_absorbance.py` for an example that combines sample preparation with absorbance measurements.

## Documentation

- See [ABSORBANCE_READER_GUIDE.md](ABSORBANCE_READER_GUIDE.md) for detailed usage instructions
- See [CHANGELOG.md](CHANGELOG.md) for version history

## Requirements

- Opentrons Flex robot with API level 2.19+
- Absorbance Plate Reader Module
- Required labware and pipettes as specified in protocol files

## References

- [Opentrons Absorbance Plate Reader Documentation](https://docs.opentrons.com/v2/modules/absorbance_plate_reader.html)
- [Opentrons Python API v2](https://docs.opentrons.com/v2/)