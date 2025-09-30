# Absorbance Plate Reader Quick Reference

## Module Loading

```python
absorbance_reader = protocol.load_module(
    module_name="absorbanceReaderV1",
    location="D3"  # Valid: A3, B3, C3, or D3
)
```

## Measurement Modes

### Single Wavelength
```python
absorbance_reader.initialize(mode="single", wavelengths=[450])
```

### Single Wavelength with Reference
```python
absorbance_reader.initialize(
    mode="single",
    wavelengths=[450],
    reference_wavelength=562
)
```

### Multiple Wavelengths (up to 6)
```python
absorbance_reader.initialize(
    mode="multi",
    wavelengths=[450, 562, 600]
)
```

## Plate Handling

```python
# Open lid
absorbance_reader.open_lid()

# Move plate to reader (requires gripper)
protocol.move_labware(plate, absorbance_reader, use_gripper=True)

# Close lid
absorbance_reader.close_lid()

# Perform reading
data = absorbance_reader.read(export_filename="results")

# Return plate
absorbance_reader.open_lid()
protocol.move_labware(plate, "D1", use_gripper=True)
```

## Data Access

```python
# Single wavelength
value = data[450]["A1"]

# Multiple wavelengths
value_450 = data[450]["A1"]
value_562 = data[562]["A1"]
value_600 = data[600]["A1"]

# Entire column at 450nm
column_data = [data[450][well.well_name] for well in plate.columns()[0]]

# All wells at 450nm
all_wells = {well: value for well, value in data[450].items()}
```

## Common Wavelengths

| Wavelength | Application |
|------------|-------------|
| 280 nm | Protein/aromatic compounds |
| 340 nm | NADH/NADPH |
| 405 nm | ELISA |
| 450 nm | Many chromophores |
| 562 nm | BCA protein assay |
| 600 nm | Turbidity/aggregation |

## Important Notes

✓ Requires API level 2.15+
✓ Gripper required for plate movement
✓ Always open lid before moving plate
✓ Close lid before reading
✓ Reference wavelength only in "single" mode
✓ Max 6 wavelengths in "multi" mode

## File Structure

- `test_absorbance_reader.py` - Complete test protocol
- `drug_surfactant_with_absorbance.py` - Integrated workflow
- `absorbance_data_examples.py` - Data processing examples
- `ABSORBANCE_READER_GUIDE.md` - Full documentation
