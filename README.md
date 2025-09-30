# Drug-Surfactant Protocol API Migration

This repository has been successfully migrated from Jupyter notebook-based workflows to a modern FastAPI server using `opentrons.simulate` and `opentrons.execute`, following the decorator pattern from ac-dev-lab.

## 🎯 Migration Status: COMPLETED ✅

### Enhanced Features

#### 🔐 **Authentication System**
- JWT-based authentication with user roles
- Secure API endpoints with bearer token authorization
- Default users: `drug_surfactant_user` and `lab_admin`

#### 🏗️ **Task Management (ac-dev-lab Pattern)**
- Decorator-based task registration: `@task`
- Registered tasks:
  - `generate_protocol_text` - Protocol generation from experimental data
  - `simulate_protocol_task` - Protocol simulation using opentrons.simulate
  - `execute_protocol_task` - Protocol execution using opentrons.execute

#### 🚀 **Railway Cloud Deployment**
- Complete Railway deployment configuration
- Environment variable management
- Automated deployment script: `deploy_railway.sh`
- Docker containerization support

#### 📡 **Enhanced API Endpoints**
- `POST /login` - Authentication
- `GET /tasks` - List available tasks
- `POST /tasks/execute` - Execute tasks
- `POST /simulate` - Protocol simulation (authenticated)
- `POST /execute` - Protocol execution (authenticated)
- `GET /status` - Comprehensive API status

### Quick Start

#### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Start enhanced API server
python enhanced_api_server.py

# Test the API
python tests/test_enhanced_api.py
```

#### Railway Deployment
```bash
# Deploy to Railway (automated)
./deploy_railway.sh

# Or deploy manually via Railway CLI
railway login
railway init
railway up
```

#### Environment Configuration
```bash
# For production deployment, set these environment variables in Railway:
# JWT_SECRET_KEY=your_production_secret_key
# DRUG_SURFACTANT_PASSWORD=your_production_password
# LAB_ADMIN_PASSWORD=your_production_admin_password
```

### API Usage Examples

#### Authentication
```python
import enhanced_api_helper_functions as eapi_hf

# Login and get token
token = eapi_hf.login("drug_surfactant_user", "demo_password_123")

# Use helper functions (handles auth automatically)
protocol_text, sim_result = eapi_hf.generate_and_simulate_protocol(df_vol, iteration=1)
```

#### Task-Based Operations
```python
# Execute individual tasks
protocol_text = eapi_hf.execute_task("generate_protocol_text", {
    "data": experimental_data,
    "iteration": 1,
    "plate_well": "A1"
})

# Simulate protocol
sim_result = eapi_hf.execute_task("simulate_protocol_task", {
    "protocol_text": protocol_text
})
```

### Files Overview

| File | Purpose |
|------|---------|
| `enhanced_api_server.py` | Main FastAPI server with auth & task management |
| `enhanced_api_helper_functions.py` | Client helper functions |
| `enhanced_api_workflow_demo.ipynb` | Demo notebook |
| [`tests/test_enhanced_api.py`](tests/test_enhanced_api.py) | Comprehensive test suite |
| `deploy_railway.sh` | Railway deployment script |
| `railway.toml` | Railway configuration |
| `Dockerfile` | Container configuration |

### Migration Benefits

✅ **Protocol Validation** - All protocols validated before execution  
✅ **Cloud Deployment** - Ready for Railway platform  
✅ **Authentication** - Secure JWT-based access control  
✅ **Task Management** - ac-dev-lab decorator pattern  
✅ **Error Handling** - Comprehensive error reporting  
✅ **Scalability** - Handle multiple concurrent requests  
✅ **Remote Access** - API accessible from anywhere  

### Testing Results

All tests passed successfully:
- ✅ Enhanced File Structure
- ✅ Enhanced Dependencies  
- ✅ Authentication System
- ✅ Task Management
- ✅ Enhanced Protocol Simulation
- ✅ Enhanced Helper Functions
- ✅ API Status
- ✅ Railway Deployment Readiness

The enhanced API is production-ready and fully tested!