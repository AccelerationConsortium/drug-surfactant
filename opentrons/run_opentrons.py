from opentrons import execute, simulate
import sys, os
from pathlib import Path

def get_api():
    mode = os.environ.get("OPENTRONS_MODE", "simulate").lower()

    if mode == "execute":
        print(" Running on robot (execute mode)")
        return execute.get_protocol_api("2.21")
    elif mode == "simulate":
        print(" Running locally (simulate mode)")
        return simulate.get_protocol_api("2.21")
    else:
        raise ValueError(f" Invalid OPENTRONS_MODE: {mode}. Use 'simulate' or 'execute'.")

def run_protocol(protocol_path: str):
    print(f"Running {protocol_path}...")
    protocol = get_api()
    with open(protocol_path) as f:
        exec(f.read(), {"protocol": protocol})
    print("Protocol execution finished.")

    if os.environ.get("OPENTRONS_MODE", "simulate").lower() == "execute":
        print("Currently running on robot: processing csv data here")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run_opentrons.py <protocol_file>")
        sys.exit(1)
    protocol_path = Path(sys.argv[1])
    run_protocol(protocol_path)