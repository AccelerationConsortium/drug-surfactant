# Railway Deployment Guide

This guide explains how to deploy the drug-surfactant enhanced API to Railway.

## Prerequisites

- Railway account (sign up at https://railway.com)
- Railway CLI installed (`npm install -g @railway/cli`)
- RAILWAY_API_KEY or Railway login credentials

## Deployment Options

### Option 1: Automated Deployment Script

The simplest method is to use the provided deployment script:

```bash
./deploy_railway.sh
```

This script will:
1. Authenticate with Railway using your API key
2. Create a new Railway project named "drug-surfactant-api"
3. Set environment variables for JWT secrets and passwords
4. Deploy the application
5. Display the deployment URL and credentials

### Option 2: Manual Deployment via Railway CLI

If you prefer manual control:

```bash
# 1. Login to Railway
export RAILWAY_TOKEN=$RAILWAY_API_KEY
# or use: railway login

# 2. Initialize project
railway init --name drug-surfactant-api

# 3. Set environment variables
railway variables set JWT_SECRET_KEY=$(openssl rand -base64 32)
railway variables set DRUG_SURFACTANT_PASSWORD="your_secure_password"
railway variables set ADMIN_PASSWORD="your_admin_password"
railway variables set PORT=8000

# 4. Deploy
railway up

# 5. Get deployment URL
railway domain
```

### Option 3: Railway Web Dashboard

1. Go to https://railway.com/dashboard
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose the `drug-surfactant` repository
5. Select the branch with the enhanced API
6. Configure environment variables:
   - `JWT_SECRET_KEY` - Generate with `openssl rand -base64 32`
   - `DRUG_SURFACTANT_PASSWORD` - Set your user password
   - `ADMIN_PASSWORD` - Set your admin password
   - `PORT` - Set to `8000`
7. Railway will automatically detect and deploy using the Dockerfile

## Configuration Files

The deployment uses these configuration files:

- **`railway.toml`** - Railway service configuration
- **`Dockerfile`** - Container build instructions
- **`requirements.txt`** - Python dependencies

## Environment Variables

Required environment variables for production:

| Variable | Description | Example |
|----------|-------------|---------|
| `JWT_SECRET_KEY` | Secret key for JWT token signing | `openssl rand -base64 32` |
| `DRUG_SURFACTANT_PASSWORD` | Password for drug_surfactant_user | `secure_password_123` |
| `ADMIN_PASSWORD` | Password for lab_admin user | `admin_password_456` |
| `PORT` | Port for the API server | `8000` |

## Verifying Deployment

Once deployed, verify your deployment:

```bash
# Get deployment URL
RAILWAY_URL=$(railway domain)

# Test health endpoint
curl https://$RAILWAY_URL/health

# Test authentication
curl -X POST https://$RAILWAY_URL/login \
  -H "Content-Type: application/json" \
  -d '{"username":"drug_surfactant_user","password":"YOUR_PASSWORD"}'

# Test status endpoint
curl https://$RAILWAY_URL/status
```

## Using the Deployed API

Update your client configuration to use the Railway URL:

```python
import os
import enhanced_api_helper_functions as eapi_hf

# Set the API URL to your Railway deployment
os.environ["DRUG_SURFACTANT_API_URL"] = "https://your-app.railway.app"
os.environ["DRUG_SURFACTANT_USERNAME"] = "drug_surfactant_user"
os.environ["DRUG_SURFACTANT_PASSWORD"] = "your_password"

# Use the API
protocol_text, sim_result = eapi_hf.generate_and_simulate_protocol(
    df_vol, 
    iteration=1
)
```

## API Endpoints

Once deployed, your API will have these endpoints:

- `GET /` - Root endpoint
- `GET /health` - Health check
- `POST /login` - JWT authentication
- `GET /tasks` - List registered tasks (requires auth)
- `POST /tasks/execute` - Execute a task (requires auth)
- `POST /simulate` - Simulate protocol (requires auth)
- `POST /execute` - Execute protocol on hardware (requires auth)
- `GET /status` - Comprehensive API status

## Monitoring

Railway provides built-in monitoring:

1. Go to your project dashboard on Railway
2. Click on the service to view:
   - Deployment logs
   - Resource usage (CPU, memory)
   - Request metrics
   - Environment variables

## Troubleshooting

### Deployment Fails

Check the deployment logs in Railway dashboard:

```bash
railway logs
```

Common issues:
- Missing environment variables
- Port configuration mismatch
- Dependency installation failures

### Authentication Issues

Verify your JWT secret and passwords are correctly set:

```bash
railway variables list
```

### Connection Issues

Ensure the Railway domain is accessible:

```bash
curl -I https://your-app.railway.app/health
```

## Security Considerations

For production deployments:

1. **Use strong passwords** - Generate secure passwords for all users
2. **Rotate JWT secrets** - Regularly update JWT_SECRET_KEY
3. **Enable HTTPS** - Railway provides HTTPS by default
4. **Restrict CORS** - Update CORS settings in `enhanced_api_server.py`
5. **Monitor logs** - Regularly review deployment logs for suspicious activity

## Scaling

Railway automatically handles scaling. To configure:

1. Go to your service settings on Railway
2. Adjust resources (CPU, memory) as needed
3. Configure auto-scaling policies

## Cost Estimation

Railway pricing is usage-based. Monitor your usage:

```bash
railway usage
```

The drug-surfactant API is lightweight and should fit within Railway's free tier for development/testing.

## Support

For Railway-specific issues:
- Railway Documentation: https://docs.railway.com
- Railway Discord: https://discord.gg/railway

For API-specific issues:
- Open an issue in the GitHub repository
- Check the MIGRATION_GUIDE.md for common questions