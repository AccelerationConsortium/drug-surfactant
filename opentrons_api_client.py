import requests
import json
import time
import os
from typing import Optional, Dict, Any

class OpenTronsAPI:
    def __init__(self, robot_ip: str = "192.168.0.5", port: int = 31950):
        self.base_url = f"http://{robot_ip}:{port}"
        self.session = requests.Session()
        self.headers = {"opentrons-version": "4"}

    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return {}
    
    def get_health(self):
        response = requests.get(f"{self.base_url}/health", headers=self.headers)
        return response.json()

    def get_robot_info(self) -> Dict[str, Any]:
        return self._make_request("GET", "/robot/info")

    def get_runs(self) -> Dict[str, Any]:
        return self._make_request("GET", "/runs")

    def get_run(self, run_id: str) -> Dict[str, Any]:
        return self._make_request("GET", f"/runs/{run_id}")

    def create_run(self, protocol_id, run_time_parameters=None, labware_offets=None):
        """Create a new run from a protocol."""
        data = {"data": {"protocolId": protocol_id}}
        if run_time_parameters:
            data["data"]["runTimeParameterValues"] = run_time_parameters
        if labware_offets:
            data["data"]["labwareOffsets"] = labware_offets
        response = requests.post(f"{self.base_url}/runs", json=data, headers=self.headers)
        return response.json()

    def upload_protocol(self, file_path: str) -> Dict[str, Any]:
        with open(file_path, "rb") as f:
            files = {"files": f}
            response = requests.post(f"{self.base_url}/protocols", files=files, headers=self.headers)
        return response.json()

    def start_run(self, run_id: str) -> Dict[str, Any]:
        """Start a run."""
        response = requests.post(
            f"{self.base_url}/runs/{run_id}/actions",
            json={"data": {"actionType": "play"}},
            headers = {
                **self.headers,
                "Content-Type": "application/json",
            },
        )
        return response.json()

    def get_run_commands(self, run_id: str) -> Dict[str, Any]:
        """Get commands for a run"""
        return self._make_request("GET", f"/runs/{run_id}/commands")

    def get_current_run(self) -> Dict[str, Any]:
        """Get current run information"""
        return self._make_request("GET", "/runs/current")

    def wait_for_run_completion(self, run_id: str, poll_interval: int = 5) -> str:
        while True:
            run_data = self.get_run(run_id)
            status = run_data.get('data', {}).get('status')

            if status in ['succeeded', 'failed', 'stopped']:
                return status

            print(f"Run status: {status}, waiting {poll_interval}s...")
            time.sleep(poll_interval)
    
    # Based on the protocol template file
    def labware_offsets_for_run(self):
        return[{
                "definitionUri": "custom_beta/allenlab_8_wellplate_20000ul/1",
                "location": { "slotName": "C1" },
                "vector": { "x": 0.0, "y": 0.0, "z": 0.0 }
            },
            {
                "definitionUri": "custom_beta/allenlab_8_wellplate_20000ul/1",
                "location": { "slotName": "C2" },
                "vector": { "x": 0.0, "y": 0.0, "z": 0.0 }
            },
            # {
            #     "definitionUri": "opentrons/corning_96_wellplate_360ul_flat/1",
            #     "location": { "slotName": "D1" },
            #     "vector": { "x": 0.0, "y": 0.0, "z": 0.0 }
            # }
            ]


    def run_protocol_from_file(self, file_path: str) -> str:
        print(f"Uploading protocol: {file_path}")

        # Create run
        create_response = self.upload_protocol(file_path)
        protocol_id = create_response["data"]["id"]
        print(f"Uploaded protocol: {protocol_id}")

        run_response = self.create_run(protocol_id, {"wavelength": 600}, self.labware_offsets_for_run())
        run_id = run_response["data"]["id"]
        print(f"Created run: {run_id}")

        start_response = self.start_run(run_id)
        print(f"Started run: {run_id}")

        if not run_id:
            print("Failed to create run")
            return "failed"

        print(f"Created run: {run_id}")

        start_response = self.start_run(run_id)
        if 'errors' in start_response:
            print(f"Failed to start run: {start_response['errors']}")
            return "failed"

        print("Run started")

        final_status = self.wait_for_run_completion(run_id)

        print(f"Run completed with status: {final_status}")
        return final_status
