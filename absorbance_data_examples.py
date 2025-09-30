"""
Example data structures and access patterns for Absorbance Plate Reader results.

This file demonstrates how to work with the data returned from the absorbance reader.
It's meant as a reference, not an executable protocol.
"""

# Example 1: Single Wavelength Data Structure
# ==============================================
# When reading at a single wavelength (e.g., 450 nm):
single_wavelength_data = {
    450: {
        'A1': 0.234,
        'A2': 0.456,
        'A3': 0.789,
        'B1': 0.123,
        # ... up to H12
    }
}

# Accessing specific wells:
well_a1 = single_wavelength_data[450]['A1']  # Returns: 0.234
well_b1 = single_wavelength_data[450]['B1']  # Returns: 0.123


# Example 2: Multiple Wavelength Data Structure
# ==============================================
# When reading at multiple wavelengths (e.g., 450, 562, 600 nm):
multi_wavelength_data = {
    450: {
        'A1': 0.234,
        'A2': 0.456,
        'A3': 0.789,
        # ... all wells
    },
    562: {
        'A1': 0.345,
        'A2': 0.567,
        'A3': 0.890,
        # ... all wells
    },
    600: {
        'A1': 0.123,
        'A2': 0.234,
        'A3': 0.456,
        # ... all wells
    }
}

# Accessing data:
a1_at_450 = multi_wavelength_data[450]['A1']  # Returns: 0.234
a1_at_562 = multi_wavelength_data[562]['A1']  # Returns: 0.345
a1_at_600 = multi_wavelength_data[600]['A1']  # Returns: 0.123


# Example 3: Processing Entire Rows or Columns
# =============================================

# Get all values in row A at wavelength 450 nm:
row_a_values = [multi_wavelength_data[450][f'A{col}'] for col in range(1, 13)]

# Get all values in column 1 at wavelength 450 nm:
rows = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
column_1_values = [multi_wavelength_data[450][f'{row}1'] for row in rows]


# Example 4: Using with Opentrons Plate Object
# =============================================
# In an actual protocol with a plate object:
"""
# Assuming 'plate' is a loaded labware object
# and 'data' is from absorbance_reader.read()

# Get all values from the first column:
column_values = [data[450][well.well_name] for well in plate.columns()[0]]

# Get all values from the first row:
row_values = [data[450][well.well_name] for well in plate.rows()[0]]

# Process all wells:
for well in plate.wells():
    absorbance = data[450][well.well_name]
    protocol.comment(f"{well.well_name}: {absorbance}")
"""


# Example 5: Finding Wells Above/Below Threshold
# ================================================

# Find all wells at 450 nm with absorbance > 0.5:
threshold = 0.5
high_absorbance_wells = [
    well_name 
    for well_name, value in multi_wavelength_data[450].items() 
    if value > threshold
]
# Result: ['A2', 'A3'] (based on example data)


# Example 6: Calculating Ratios Between Wavelengths
# ==================================================

# Calculate ratio of 450nm / 600nm for each well:
ratios = {
    well_name: multi_wavelength_data[450][well_name] / multi_wavelength_data[600][well_name]
    for well_name in multi_wavelength_data[450].keys()
}

# Example 7: Comparing Samples to Blank
# ======================================

# Subtract blank (e.g., well H12) from all samples at 450 nm:
blank_value = multi_wavelength_data[450]['H12']
corrected_values = {
    well_name: value - blank_value
    for well_name, value in multi_wavelength_data[450].items()
}


# Example 8: CSV Export Structure
# ================================
# When using export_filename="my_results", the CSV file will have this structure:
# (Accessible through the Opentrons App after protocol completion)
"""
Well,450,562,600
A1,0.234,0.345,0.123
A2,0.456,0.567,0.234
A3,0.789,0.890,0.456
...
H12,0.100,0.200,0.300
"""


# Example 9: Integration with Pandas (Post-Processing)
# ====================================================
# After exporting data and downloading the CSV, you can use pandas:
"""
import pandas as pd

# Load the exported CSV
df = pd.read_csv('my_results.csv', index_col='Well')

# Access data
print(df.loc['A1', '450'])  # Absorbance at 450nm for well A1

# Calculate statistics
mean_450 = df['450'].mean()
std_450 = df['450'].std()

# Filter wells
high_abs = df[df['450'] > 0.5]

# Plot data
import matplotlib.pyplot as plt
df['450'].plot(kind='bar')
plt.xlabel('Well')
plt.ylabel('Absorbance (450nm)')
plt.show()
"""


# Example 10: Protocol Comments for Logging
# =========================================
# Best practices for logging results during protocol execution:
"""
def log_absorbance_summary(protocol, data, wavelengths):
    '''Log a summary of absorbance readings.'''
    for wavelength in wavelengths:
        values = list(data[wavelength].values())
        mean_abs = sum(values) / len(values)
        max_abs = max(values)
        min_abs = min(values)
        
        protocol.comment(f"Wavelength {wavelength}nm:")
        protocol.comment(f"  Mean: {mean_abs:.3f}")
        protocol.comment(f"  Range: {min_abs:.3f} - {max_abs:.3f}")

# Usage in protocol:
# log_absorbance_summary(protocol, absorbance_data, [450, 562, 600])
"""
