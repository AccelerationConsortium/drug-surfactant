# Opentrons Absorbance Plate Reader Usage Guide

This directory contains test protocols and examples for using the Opentrons Absorbance Plate Reader Module with the Flex robot.

## Files

- `test_absorbance_reader.py` - Comprehensive test protocol demonstrating all absorbance reader features
- `drug_surfactant_with_absorbance.py` - Integrated workflow combining drug-surfactant preparation with UV-Vis measurements

## Absorbance Plate Reader Overview

The Opentrons Absorbance Plate Reader Module enables automated UV-Vis spectrophotometry measurements on 96-well plates.

### Key Features

- **Single wavelength mode**: Measure at one specific wavelength (e.g., 450 nm)
- **Single wavelength with reference**: Measure at a sample wavelength with reference wavelength correction
- **Multi-wavelength mode**: Measure at up to 6 wavelengths simultaneously (e.g., 450, 562, 600 nm)
- **Data export**: Automatically export measurements to CSV files
- **Programmatic access**: Access individual well measurements via nested dictionaries

## Hardware Setup

### Module Placement

The Absorbance Plate Reader can be placed in slots **A3, B3, C3, or D3** on the Flex deck.

Example:
```python
absorbance_reader = protocol.load_module(
    module_name="absorbanceReaderV1",
    location="D3"
)
```

### Compatible Labware

The module works with standard 96-well plates such as:
- `corning_96_wellplate_360ul_flat`
- `nest_96_wellplate_200ul_flat`
- Other standard 96-well microplates

## Usage Examples

### 1. Single Wavelength Measurement

```python
# Initialize for single wavelength at 450 nm
absorbance_reader.initialize(mode="single", wavelengths=[450])

# Open lid and load plate
absorbance_reader.open_lid()
protocol.move_labware(plate, absorbance_reader, use_gripper=True)
absorbance_reader.close_lid()

# Read and export data
data = absorbance_reader.read(export_filename="my_results")

# Access specific well
a1_value = data[450]["A1"]
```

### 2. Single Wavelength with Reference

Reference wavelength readings are subtracted from sample readings for better accuracy.

```python
absorbance_reader.initialize(
    mode="single",
    wavelengths=[450],
    reference_wavelength=562
)

# ... load plate and read as above
data = absorbance_reader.read(export_filename="ref_corrected")
```

### 3. Multiple Wavelengths

Measure at multiple wavelengths in a single read (up to 6 wavelengths).

```python
absorbance_reader.initialize(
    mode="multi",
    wavelengths=[450, 562, 600]
)

# ... load plate and read as above
data = absorbance_reader.read(export_filename="multi_wavelength")

# Access data for each wavelength
value_450 = data[450]["A1"]
value_562 = data[562]["A1"]
value_600 = data[600]["A1"]
```

### 4. Processing Entire Columns

```python
# Get all values in column 1 at 450 nm
column_1_values = [data[450][well.well_name] for well in plate.columns()[0]]
```

## Workflow Integration

The `drug_surfactant_with_absorbance.py` protocol shows how to integrate absorbance measurements into an existing workflow:

1. Load all modules and labware
2. Prepare samples (drug-surfactant mixtures)
3. Initialize absorbance reader
4. Move plate to reader using gripper
5. Perform measurements
6. Export data to CSV
7. Return plate to deck

## Common Wavelengths for Drug-Surfactant Studies

- **280 nm**: Protein and aromatic compound detection
- **340 nm**: NADH/NADPH detection
- **405 nm**: Common ELISA wavelength
- **450 nm**: Many chromophores and dyes
- **562 nm**: BCA protein assay
- **600 nm**: Turbidity and aggregation measurements

## Data Output

When `export_filename` is specified, the module creates a CSV file accessible via the Opentrons App:
- Filename: `<export_filename>.csv`
- Format: Wells as rows, wavelengths as columns
- Location: Accessible through the Opentrons App after protocol completion

## Important Notes

1. **Gripper Required**: Moving labware to/from the absorbance reader requires the Flex gripper
2. **Lid Management**: Always open the lid before moving plates onto/off the module
3. **Initialization**: Call `initialize()` before each read to set measurement parameters
4. **Reference Wavelengths**: Only available in "single" mode, not "multi" mode
5. **API Level**: Requires API level 2.15 or higher

## Troubleshooting

- **"Module not found" error**: Ensure the module is correctly loaded in a valid slot (A3-D3)
- **Plate transfer errors**: Verify the gripper is properly configured
- **No data returned**: Check that `close_lid()` was called before `read()`
- **Invalid wavelength**: Ensure wavelengths are within the module's supported range

## References

- [Opentrons Absorbance Plate Reader Documentation](https://docs.opentrons.com/v2/modules/absorbance_plate_reader.html)
- [Absorbance Plate Reader Instruction Manual](https://insights.opentrons.com/hubfs/Absorbance%20Plate%20Reader%20Instruction%20Manual.pdf)
- [Opentrons Python API v2](https://docs.opentrons.com/v2/)
- [Flex Modules Overview](https://docs.opentrons.com/flex/modules/absorbance-plate-reader/)

## Testing

To test these protocols in simulation mode:

```bash
# Using Opentrons Protocol Designer or App
# Import the .py file and run in simulation mode

# Or use the opentrons_simulate command if installed:
opentrons_simulate test_absorbance_reader.py
```

## Contributing

When modifying these protocols:
1. Ensure syntax validation: `python3 -m py_compile <filename>.py`
2. Test in simulation mode before hardware deployment
3. Update CHANGELOG.md with any changes
4. Document any new features or modifications
