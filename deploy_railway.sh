#!/bin/bash
# Railway Deployment Script for Drug-Surfactant API

echo "🚀 Deploying Drug-Surfactant API to Railway..."

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    curl -fsSL https://railway.com/install.sh | sh
    export PATH=$PATH:$HOME/.railway/bin
fi

# Login to Railway
echo "🔐 Logging in to Railway..."
if [ -n "$RAILWAY_API_KEY" ]; then
    echo "Using API key for authentication..."
    export RAILWAY_TOKEN=$RAILWAY_API_KEY
else
    echo "Please run: railway login"
    exit 1
fi

# Initialize project
echo "📦 Initializing Railway project..."
railway init --name drug-surfactant-api

# Set environment variables
echo "⚙️ Setting environment variables..."
railway variables set JWT_SECRET_KEY=$(openssl rand -base64 32)
railway variables set DRUG_SURFACTANT_PASSWORD="secure_password_$(openssl rand -hex 8)"
railway variables set ADMIN_PASSWORD="admin_password_$(openssl rand -hex 8)"
railway variables set PORT=8000

# Deploy the application
echo "🚢 Deploying to Railway..."
railway up --detach

# Get the deployment URL
echo "🌐 Getting deployment URL..."
DEPLOYMENT_URL=$(railway domain)

echo "✅ Deployment complete!"
echo "🔗 API URL: $DEPLOYMENT_URL"
echo "📚 API Documentation: $DEPLOYMENT_URL/docs"
echo "🏥 Health Check: $DEPLOYMENT_URL/health"

# Display credentials
echo ""
echo "🔑 Default Login Credentials:"
echo "Username: drug_surfactant_user"
echo "Password: $(railway variables get DRUG_SURFACTANT_PASSWORD 2>/dev/null || echo 'Check Railway dashboard')"
echo ""
echo "Admin Username: lab_admin"  
echo "Admin Password: $(railway variables get ADMIN_PASSWORD 2>/dev/null || echo 'Check Railway dashboard')"

echo ""
echo "📋 Next Steps:"
echo "1. Test the API endpoints at $DEPLOYMENT_URL/docs"
echo "2. Update your local environment to use the deployed API"
echo "3. Configure your client applications with the new URL"