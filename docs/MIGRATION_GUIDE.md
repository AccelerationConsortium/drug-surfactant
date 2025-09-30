# Migration from Jupyter Notebooks to opentrons.simulate/execute

This document describes the migration from the Jupyter notebook-based workflow to an API-based system using `opentrons.simulate` and `opentrons.execute`.

## Overview

The drug-surfactant project has been migrated from a Jupyter notebook workflow that used SSH/SCP for file transfer to a modern API-based system that provides:

- Protocol simulation using `opentrons.simulate`
- Protocol execution using `opentrons.execute` 
- RESTful API for remote protocol management
- Cloud deployment capability via Railway
- Better error handling and debugging

## Architecture Changes

### Before (Jupyter Notebook Workflow)
```
Jupyter Notebook → Generate Protocol File → SSH/SCP Upload → Manual Robot Operation
```

### After (API-Based Workflow)
```
Client → FastAPI Server → opentrons.simulate → opentrons.execute → Robot
```

## Key Components

### 1. FastAPI Server (`api_server.py`)

A FastAPI application that provides:

- **Health Check Endpoint**: `/health`
- **Protocol Simulation**: `/simulate` - Uses `opentrons.simulate` to validate protocols
- **Protocol Execution**: `/execute` - Uses `opentrons.execute` for robot control
- **Protocol Retrieval**: `/protocols/{iteration}` - Get saved protocols

### 2. API Helper Functions (`api_helper_functions.py`)

Updated helper functions that use the API instead of SSH/SCP:

- `simulate_protocol()` - Simulate protocols via API
- `execute_protocol()` - Execute protocols via API  
- `generate_and_simulate_protocol()` - Generate and validate protocols
- `run_protocol_on_robot()` - Execute on hardware

Maintains compatibility with existing optimization workflow functions.

### 3. Deployment Configuration

- **Dockerfile**: Container configuration for deployment
- **requirements.txt**: Python dependencies
- **railway.toml**: Railway platform configuration

## API Endpoints

### GET /health
Returns API health status and Opentrons version.

### POST /simulate
Simulates a protocol using `opentrons.simulate`.

**Request Body:**
```json
{
  "data": [{"trial_index": "0", "drug": "120", ...}],
  "iteration": 1,
  "plate_well": "H3",
  "deepplate_well": "H3"
}
```

**Response:**
```json
{
  "success": true,
  "protocol_text": "from opentrons import protocol_api...",
  "run_log": ["Protocol simulation completed successfully"],
  "error": null
}
```

### POST /execute
Executes a protocol on real hardware using `opentrons.execute`.

**Request Body:**
```json
{
  "protocol_text": "from opentrons import protocol_api...",
  "run_id": "iteration_1"
}
```

**Response:**
```json
{
  "success": true,
  "run_id": "iteration_1",
  "status": "completed",
  "error": null
}
```

## Migration Guide

### For Existing Jupyter Notebooks

1. **Replace file upload with API calls:**
   ```python
   # Old way
   hf.upload_file_to_robot(local_file_path, remote_file_name)
   
   # New way
   import api_helper_functions as api_hf
   protocol_text, sim_result = api_hf.generate_and_simulate_protocol(df_vol, iteration)
   exec_result = api_hf.run_protocol_on_robot(protocol_text, iteration)
   ```

2. **Use API-based helper functions:**
   ```python
   # Import the new API-based helpers
   import api_helper_functions as api_hf
   
   # Check API availability
   if api_hf.check_api_health():
       # Use new workflow
   ```

### For New Development

Use the demonstration notebook `api_workflow_demo.ipynb` as a starting point.

## Deployment

### Local Development
```bash
# Start the API server
python api_server.py

# Server runs on http://localhost:8000
```

### Railway Deployment
The API is specifically configured for Railway platform deployment:

```bash
# Deploy to Railway using the Railway CLI
railway login
railway init --name drug-surfactant-api
railway up
```

Alternatively, use the Railway MCP server tools for automated deployment.

The Railway configuration is in `railway.toml` and uses the `Dockerfile` for deployment.

### Environment Variables
- `DRUG_SURFACTANT_API_URL`: API base URL (defaults to localhost:8000)
- `OPENTRONS_PROTOCOL_API_VERSION`: Protocol API version (defaults to 2.21)

## Benefits of Migration

1. **Protocol Validation**: All protocols are validated with `opentrons.simulate` before execution
2. **Remote Access**: API can be accessed remotely, not just from robot computer
3. **Cloud Deployment**: Can be deployed on cloud platforms like Railway
4. **Better Error Handling**: Structured error responses and logging
5. **Scalability**: Can handle multiple concurrent requests
6. **Integration**: RESTful API can be integrated with various clients
7. **Debugging**: Better visibility into protocol execution steps

## Backward Compatibility

The migration maintains compatibility with existing code:

- All optimization functions remain unchanged
- Data processing functions are preserved
- File format compatibility is maintained
- The old `upload_file_to_robot()` function is preserved but deprecated

## Testing

Use the provided test scripts to verify functionality:

```bash
# Test core API functionality
python tests/test_api_simple.py

# Test with sample data
python tests/test_api.py
```

## Troubleshooting

### Common Issues

1. **API Server Not Running**: Check that `python api_server.py` is running
2. **Import Errors**: Ensure all dependencies are installed with `pip install -r requirements.txt`
3. **Protocol Template Not Found**: Verify the template file exists at the expected path
4. **Simulation Failures**: Check protocol syntax and Opentrons API compatibility

### Logs

The FastAPI server provides detailed logs for debugging:
- Request/response details
- Simulation results
- Execution status
- Error messages

## Future Enhancements

1. **Authentication**: Add API key authentication for production deployment
2. **Protocol Storage**: Database for storing and versioning protocols
3. **Real-time Status**: WebSocket support for real-time execution updates
4. **Batch Processing**: Support for running multiple protocols in sequence
5. **Integration**: Direct integration with optimization frameworks