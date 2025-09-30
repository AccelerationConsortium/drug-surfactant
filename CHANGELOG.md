# Changelog

All notable changes to the drug-surfactant project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2025-01-27

### Added - Enhanced API Implementation
- **Enhanced FastAPI server** (`enhanced_api_server.py`) with JWT authentication
- **Task management system** using decorator pattern from ac-dev-lab (@task decorator)
- **Authentication system** with user roles and JWT bearer tokens
- **Comprehensive test suite** (`tests/test_enhanced_api.py`) with 6 test categories
- **Enhanced helper functions** (`enhanced_api_helper_functions.py`) with auth support
- **Railway deployment script** (`deploy_railway.sh`) for automated cloud deployment
- **Enhanced demo notebook** (`enhanced_api_workflow_demo.ipynb`) showing new workflow

### Enhanced Features
- **Security**: JWT-based authentication with bearer tokens for all protected endpoints
- **Task Registration**: `@task` decorator following ac-dev-lab pattern for function registration
- **Error Handling**: Comprehensive error reporting and structured logging
- **API Architecture**: Authentication-protected endpoints with role-based access control
- **Cloud Deployment**: Full Railway integration with automated deployment scripts

### Authentication Dependencies Added
- `pyjwt==2.8.0` for JWT token handling
- `bcrypt==4.1.2` for secure password hashing
- `python-jose[cryptography]==3.3.0` for JWT validation and cryptography
- `python-multipart==0.0.6` for form data handling

### Testing Results
All 6 enhanced test categories passed:
- ✅ Enhanced File Structure
- ✅ Enhanced Dependencies  
- ✅ Authentication System
- ✅ Task Management
- ✅ Enhanced Protocol Simulation
- ✅ Enhanced Helper Functions
- ✅ API Status
- ✅ Railway Deployment Readiness

## [1.0.0] - 2024-09-30

### Added
- FastAPI server (`api_server.py`) with opentrons.simulate integration
- Protocol simulation endpoint using `opentrons.simulate` for validation
- Protocol execution endpoint using `opentrons.execute` for hardware control
- API helper functions (`api_helper_functions.py`) replacing SSH/SCP workflow
- Railway deployment configuration (`railway.toml`, `Dockerfile`)
- Comprehensive test suite (`tests/comprehensive_test.py`)
- Migration guide and documentation (`docs/MIGRATION_GUIDE.md`)
- Demo notebook (`api_workflow_demo.ipynb`) showing new workflow

### Changed
- Migrated from Jupyter notebook SSH/SCP workflow to API-based system
- Protocol generation now uses RESTful API instead of file uploads
- Cloud deployment via Railway instead of local robot computer access

### Deprecated
- `upload_file_to_robot()` function (replaced by API-based approach)
- SSH/SCP file transfer mechanism

### Removed
- Compiled Python files (.pyc) and cache directories
- macOS .DS_Store files from repository

### Fixed
- Added proper Python .gitignore template to prevent future commits of build artifacts
- Updated Railway configuration for proper cloud deployment