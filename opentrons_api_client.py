import requests
import json
import time
import os
from typing import Optional, Dict, Any

class OpenTronsAPI:
    def __init__(self, robot_ip: str = "192.168.0.5", port: int = 31950):
        """
        Initialize OpenTrons API client

        Args:
            robot_ip: IP address of the OpenTrons robot
            port: HTTP API port (default 31950)
        """
        self.base_url = f"http://{robot_ip}:{port}"
        self.session = requests.Session()

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return {}

    def get_robot_info(self) -> Dict[str, Any]:
        """Get robot information"""
        return self._make_request("GET", "/robot/info")

    def get_runs(self) -> Dict[str, Any]:
        """Get list of runs"""
        return self._make_request("GET", "/runs")

    def get_run(self, run_id: str) -> Dict[str, Any]:
        """Get specific run details"""
        return self._make_request("GET", f"/runs/{run_id}")

    def create_run(self, protocol_text: str, labware_offsets: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Create a new run with protocol

        Args:
            protocol_text: The Python protocol code as a string
            labware_offsets: Optional labware offset definitions
        """
        data = {
            "data": {
                "protocol": protocol_text
            }
        }

        if labware_offsets:
            data["data"]["labwareOffsets"] = labware_offsets

        return self._make_request("POST", "/runs", json=data)

    def upload_protocol_file(self, file_path: str) -> Dict[str, Any]:
        """
        Upload a protocol file directly

        Args:
            file_path: Path to the .py protocol file
        """
        with open(file_path, 'r') as f:
            protocol_text = f.read()

        return self.create_run(protocol_text)

    def start_run(self, run_id: str) -> Dict[str, Any]:
        """Start a created run"""
        return self._make_request("POST", f"/runs/{run_id}/start")

    def pause_run(self, run_id: str) -> Dict[str, Any]:
        """Pause a running run"""
        return self._make_request("POST", f"/runs/{run_id}/pause")

    def stop_run(self, run_id: str) -> Dict[str, Any]:
        """Stop a running run"""
        return self._make_request("POST", f"/runs/{run_id}/stop")

    def get_run_commands(self, run_id: str) -> Dict[str, Any]:
        """Get commands for a run"""
        return self._make_request("GET", f"/runs/{run_id}/commands")

    def get_current_run(self) -> Dict[str, Any]:
        """Get current run information"""
        return self._make_request("GET", "/runs/current")

    def wait_for_run_completion(self, run_id: str, poll_interval: int = 5) -> str:
        """
        Wait for run to complete and return final status

        Args:
            run_id: ID of the run to monitor
            poll_interval: Seconds between status checks
        """
        while True:
            run_data = self.get_run(run_id)
            status = run_data.get('data', {}).get('status')

            if status in ['succeeded', 'failed', 'stopped']:
                return status

            print(f"Run status: {status}, waiting {poll_interval}s...")
            time.sleep(poll_interval)

    def run_protocol_from_file(self, file_path: str) -> str:
        """
        Complete workflow: upload protocol, start run, wait for completion

        Args:
            file_path: Path to protocol file

        Returns:
            Final run status
        """
        print(f"Uploading protocol: {file_path}")

        # Create run
        create_response = self.upload_protocol_file(file_path)
        run_id = create_response.get('data', {}).get('id')

        if not run_id:
            print("Failed to create run")
            return "failed"

        print(f"Created run: {run_id}")

        # Start run
        start_response = self.start_run(run_id)
        if 'errors' in start_response:
            print(f"Failed to start run: {start_response['errors']}")
            return "failed"

        print("Run started, monitoring progress...")

        # Wait for completion
        final_status = self.wait_for_run_completion(run_id)

        print(f"Run completed with status: {final_status}")
        return final_status


# Example usage functions
def run_drug_surfactant_experiment(robot_ip: str, protocol_file_path: str) -> bool:
    """
    Run a complete drug-surfactant experiment via HTTP API

    Args:
        robot_ip: IP address of OpenTrons robot
        protocol_file_path: Path to generated protocol file

    Returns:
        True if experiment succeeded
    """
    api = OpenTronsAPI(robot_ip)

    # Check robot connectivity
    robot_info = api.get_robot_info()
    if not robot_info:
        print("Cannot connect to robot")
        return False

    print(f"Connected to robot: {robot_info}")

    # Run the protocol
    status = api.run_protocol_from_file(protocol_file_path)

    return status == "succeeded"


def monitor_experiment_progress(robot_ip: str, run_id: str):
    """
    Monitor experiment progress in real-time

    Args:
        robot_ip: IP address of OpenTrons robot
        run_id: ID of the run to monitor
    """
    api = OpenTronsAPI(robot_ip)

    while True:
        run_data = api.get_run(run_id)
        status = run_data.get('data', {}).get('status')
        current_command = run_data.get('data', {}).get('currentCommand')

        print(f"Status: {status}")
        if current_command:
            print(f"Current command: {current_command.get('commandType', 'Unknown')}")

        if status in ['succeeded', 'failed', 'stopped']:
            break

        time.sleep(10)  # Check every 10 seconds


if __name__ == "__main__":
    # Example usage
    ROBOT_IP = "192.168.10.143"
    PROTOCOL_FILE = "experiments/20250917_closed_loop/iteration_2/protocol/otflex_2.py"

    api = OpenTronsAPI(ROBOT_IP)

    # Test connection
    print("Testing robot connection...")
    robot_info = api.get_robot_info()
    print(f"Robot info: {robot_info}")

    # Run protocol
    success = run_drug_surfactant_experiment(ROBOT_IP, PROTOCOL_FILE)
    print(f"Experiment {'succeeded' if success else 'failed'}")