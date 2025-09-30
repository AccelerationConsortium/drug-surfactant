"""
Integrated protocol for drug-surfactant experiments with UV-Vis absorbance measurements.

This protocol extends the drug-surfactant workflow by adding absorbance readings
after preparing the samples, using the Opentrons Absorbance Plate Reader module.
"""

from opentrons import protocol_api
import re

metadata = {
    "protocolName": "Drug-Surfactant with Absorbance Reading",
    "author": "Opentrons Testing",
    "description": "Prepare drug-surfactant samples and measure absorbance",
}

requirements = {"robotType": "Flex", "apiLevel": "2.19"}


def run(protocol: protocol_api.ProtocolContext):
    """
    Prepare drug-surfactant samples and measure their absorbance.
    """

    # Load the Absorbance Plate Reader module
    absorbance_reader = protocol.load_module(
        module_name="absorbanceReaderV1",
        location="D3"
    )

    # Load tip racks
    tip1000 = protocol.load_labware(
        load_name="opentrons_flex_96_filtertiprack_1000ul",
        location="B1"
    )
    tip50 = protocol.load_labware(
        load_name="opentrons_flex_96_filtertiprack_50ul",
        location="B2"
    )

    # Attach pipettes
    pipette_low = protocol.load_instrument(
        instrument_name="flex_1channel_50",
        mount="right",
        tip_racks=[tip50]
    )
    pipette_high = protocol.load_instrument(
        instrument_name="flex_1channel_1000",
        mount="left",
        tip_racks=[tip1000]
    )

    # Load surfactant stock plates
    surfactant_stock_1 = protocol.load_labware(
        load_name="allenlab_8_wellplate_20000ul",
        location="C1"
    )

    # Load second stock plate with drug and DMSO
    surfactant_drug_dmso_stock_2 = protocol.load_labware(
        load_name="allenlab_8_wellplate_20000ul",
        location="C2"
    )

    # Load water reservoir
    water_res = protocol.load_labware(
        "nest_1_reservoir_290ml",
        "C3"
    )
    water = water_res["A1"]

    # Load well plate for final samples - this will be read by absorbance reader
    sample_plate = protocol.load_labware(
        load_name="corning_96_wellplate_360ul_flat",
        location="D1"
    )

    # Load deep well plate for intermediate mixing
    deepplate = protocol.load_labware(
        "allenlabresevoir_96_wellplate_2200ul",
        location="D2"
    )

    # Load trash bin
    trash = protocol.load_trash_bin(location="A3")

    # Example: Simple sample preparation
    # In a real experiment, this would be replaced with the actual drug-surfactant
    # preparation workflow from drug_surfactant_otflex.py

    protocol.comment("=== Preparing samples ===")

    # For demonstration, we'll just add water to a few wells
    for well in ["A1", "A2", "A3", "B1", "B2", "B3"]:
        pipette_high.pick_up_tip()
        pipette_high.transfer(
            200,
            water,
            sample_plate[well],
            new_tip="never",
            air_gap=10
        )
        pipette_high.blow_out(sample_plate[well])
        pipette_high.drop_tip()

    protocol.comment("=== Sample preparation complete ===")

    # Initialize the absorbance reader for UV-Vis measurements
    # For drug-surfactant systems, we might measure at multiple wavelengths
    # to detect different chromophores or interactions
    protocol.comment("=== Initializing absorbance reader ===")

    # Common wavelengths for drug-surfactant studies:
    # - 280 nm: Protein/aromatic compounds
    # - 450 nm: Many dyes and indicators
    # - 600 nm: Turbidity/aggregation
    absorbance_reader.initialize(
        mode="multi",
        wavelengths=[450, 562, 600]
    )

    # Move plate to absorbance reader
    protocol.comment("=== Moving plate to absorbance reader ===")
    absorbance_reader.open_lid()
    protocol.move_labware(sample_plate, absorbance_reader, use_gripper=True)
    absorbance_reader.close_lid()

    # Perform absorbance measurements
    protocol.comment("=== Measuring absorbance ===")
    absorbance_data = absorbance_reader.read(
        export_filename="drug_surfactant_absorbance"
    )

    # Log some sample results
    protocol.comment("=== Absorbance measurements complete ===")
    protocol.comment(f"Sample A1 at 450nm: {absorbance_data[450]['A1']}")
    protocol.comment(f"Sample A1 at 562nm: {absorbance_data[562]['A1']}")
    protocol.comment(f"Sample A1 at 600nm: {absorbance_data[600]['A1']}")

    # Return plate to original position
    absorbance_reader.open_lid()
    protocol.move_labware(sample_plate, "D1", use_gripper=True)

    protocol.comment("=== Protocol complete ===")
    protocol.comment("Results exported to: drug_surfactant_absorbance.csv")
