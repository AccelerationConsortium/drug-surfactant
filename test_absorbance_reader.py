"""
Test protocol for Opentrons Absorbance Plate Reader Module.

This protocol demonstrates how to use the Absorbance Plate Reader module
on the Opentrons Flex robot to measure UV-Vis absorbance of samples.

References:
- https://docs.opentrons.com/flex/modules/absorbance-plate-reader/
- https://docs.opentrons.com/v2/modules/absorbance_plate_reader.html
"""

from opentrons import protocol_api

metadata = {
    "protocolName": "Absorbance Plate Reader Test",
    "author": "Opentrons Testing",
    "description": "Test protocol for UV-Vis absorbance measurements",
}

requirements = {"robotType": "Flex", "apiLevel": "2.19"}


def run(protocol: protocol_api.ProtocolContext):
    """
    Test the Absorbance Plate Reader module with different measurement modes.
    """

    # Load the Absorbance Plate Reader module
    # Valid locations for Flex: A3, B3, C3, or D3
    absorbance_reader = protocol.load_module(
        module_name="absorbanceReaderV1",
        location="D3"
    )

    # Load a 96-well plate for absorbance readings
    # The plate will be moved onto the reader module
    test_plate = protocol.load_labware(
        load_name="corning_96_wellplate_360ul_flat",
        location="D1"
    )

    # Load tip racks for pipetting
    tiprack_50 = protocol.load_labware(
        load_name="opentrons_flex_96_filtertiprack_50ul",
        location="A1"
    )

    # Load pipette for sample preparation
    pipette = protocol.load_instrument(
        instrument_name="flex_1channel_50",
        mount="right",
        tip_racks=[tiprack_50]
    )

    # Test 1: Single wavelength measurement at 450 nm
    protocol.comment("=== Test 1: Single Wavelength Measurement ===")
    absorbance_reader.initialize(mode="single", wavelengths=[450])

    # Open lid to place plate
    absorbance_reader.open_lid()
    protocol.comment("Lid opened. Moving plate to reader...")

    # Move plate to the absorbance reader using gripper
    protocol.move_labware(test_plate, absorbance_reader, use_gripper=True)

    # Close lid before reading
    absorbance_reader.close_lid()
    protocol.comment("Lid closed. Starting measurement...")

    # Perform absorbance reading and export to CSV
    absorbance_data_single = absorbance_reader.read(export_filename="single_wavelength_test")
    protocol.comment(f"Single wavelength measurement complete. Sample data: A1={absorbance_data_single[450]['A1']}")

    # Open lid to remove plate
    absorbance_reader.open_lid()
    protocol.move_labware(test_plate, "D1", use_gripper=True)

    # Test 2: Single wavelength with reference wavelength
    protocol.comment("=== Test 2: Single Wavelength with Reference ===")
    absorbance_reader.initialize(
        mode="single",
        wavelengths=[450],
        reference_wavelength=562
    )

    absorbance_reader.open_lid()
    protocol.move_labware(test_plate, absorbance_reader, use_gripper=True)
    absorbance_reader.close_lid()

    absorbance_data_ref = absorbance_reader.read(export_filename="single_with_reference_test")
    protocol.comment(f"Measurement with reference complete. Sample data: A1={absorbance_data_ref[450]['A1']}")

    absorbance_reader.open_lid()
    protocol.move_labware(test_plate, "D1", use_gripper=True)

    # Test 3: Multiple wavelength measurement
    protocol.comment("=== Test 3: Multiple Wavelength Measurement ===")
    absorbance_reader.initialize(
        mode="multi",
        wavelengths=[450, 562, 600]
    )

    absorbance_reader.open_lid()
    protocol.move_labware(test_plate, absorbance_reader, use_gripper=True)
    absorbance_reader.close_lid()

    absorbance_data_multi = absorbance_reader.read(export_filename="multi_wavelength_test")
    protocol.comment("Multiple wavelength measurement complete.")
    protocol.comment(f"450nm, A1: {absorbance_data_multi[450]['A1']}")
    protocol.comment(f"562nm, A1: {absorbance_data_multi[562]['A1']}")
    protocol.comment(f"600nm, A1: {absorbance_data_multi[600]['A1']}")

    # Demonstrate accessing data for an entire column
    column_1_data_450nm = [absorbance_data_multi[450][well.well_name] for well in test_plate.columns()[0]]
    protocol.comment(f"Column 1 data at 450nm: {column_1_data_450nm}")

    # Final cleanup
    absorbance_reader.open_lid()
    protocol.move_labware(test_plate, "D1", use_gripper=True)

    protocol.comment("=== All absorbance reader tests complete ===")
