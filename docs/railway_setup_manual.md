# Manual Railway Setup Instructions

Since automated Railway deployment requires interactive authentication, follow these steps to deploy manually.

## Step 1: Create Railway Account

1. Go to https://railway.com
2. Sign up for a free account
3. Verify your email address

## Step 2: Create New Project via Dashboard

1. Log in to https://railway.com/dashboard
2. Click "New Project"
3. Select "Empty Project"
4. Name it "drug-surfactant-api"

## Step 3: Deploy from GitHub

1. In your project, click "New"
2. Select "GitHub Repo"
3. Connect your GitHub account if not already connected
4. Select the `AccelerationConsortium/drug-surfactant` repository
5. Select the branch `copilot/fix-dcf5da3a-6378-4dd4-af2f-5536edcd6f44`

## Step 4: Configure Service

Railway will auto-detect the Dockerfile and configuration. Verify:

1. **Build Settings**
   - Builder: Dockerfile
   - Dockerfile Path: `./Dockerfile`
   - Build Command: (leave empty, handled by Dockerfile)

2. **Start Command**
   - Command: (leave empty, handled by Dockerfile CMD)

## Step 5: Set Environment Variables

In the Railway dashboard, go to Variables and add:

```bash
JWT_SECRET_KEY=<generate with: openssl rand -base64 32>
DRUG_SURFACTANT_PASSWORD=demo_password_123
ADMIN_PASSWORD=admin_password_456
PORT=8000
```

### Generate JWT Secret

On your local machine:
```bash
openssl rand -base64 32
```

Copy the output and paste it as `JWT_SECRET_KEY` in Railway.

## Step 6: Generate Domain

1. Go to Settings tab in your Railway service
2. Click "Generate Domain" under "Networking"
3. Railway will create a public URL like `https://drug-surfactant-api-production-XXXX.up.railway.app`
4. Copy this URL for use in your client

## Step 7: Deploy

Railway will automatically deploy your application. Monitor the deployment:

1. Go to "Deployments" tab
2. Watch the build logs
3. Wait for status to show "Active"

## Step 8: Verify Deployment

Test your deployed API:

```bash
# Replace with your actual Railway URL
RAILWAY_URL="https://drug-surfactant-api-production-XXXX.up.railway.app"

# Test health
curl $RAILWAY_URL/health

# Test login
curl -X POST $RAILWAY_URL/login \
  -H "Content-Type: application/json" \
  -d '{"username":"drug_surfactant_user","password":"demo_password_123"}'

# Test status
curl $RAILWAY_URL/status
```

## Step 9: Update Client Configuration

In your local environment or notebook:

```python
import os
import enhanced_api_helper_functions as eapi_hf

# Set Railway URL
os.environ["DRUG_SURFACTANT_API_URL"] = "https://drug-surfactant-api-production-XXXX.up.railway.app"
os.environ["DRUG_SURFACTANT_USERNAME"] = "drug_surfactant_user"
os.environ["DRUG_SURFACTANT_PASSWORD"] = "demo_password_123"

# Test connection
success = eapi_hf.test_api_connection()

if success:
    print("✅ Successfully connected to Railway deployment!")
```

## Step 10: Test Communication

Run the MVP communication test against your Railway deployment:

```python
# In tests/mvp_communication_test.py, update the API_BASE_URL:
API_BASE_URL = "https://drug-surfactant-api-production-XXXX.up.railway.app"

# Then run:
python tests/mvp_communication_test.py
```

## Monitoring and Logs

View real-time logs in Railway dashboard:

1. Go to your service in Railway
2. Click "Logs" tab
3. View application logs, errors, and requests

## Troubleshooting

### Build Fails

Check the build logs in Railway dashboard. Common issues:

- **Missing Dockerfile**: Ensure Dockerfile is in the repository root
- **Dependency errors**: Check requirements.txt has all dependencies
- **Build timeout**: Increase timeout in Railway project settings

### Runtime Errors

Check application logs:

1. Authentication errors: Verify environment variables are set correctly
2. Port binding errors: Ensure PORT=8000 is set
3. Import errors: Verify all dependencies are in requirements.txt

### Connection Timeout

If you can't connect to the Railway URL:

1. Verify the domain was generated correctly
2. Check the service is "Active" in deployments
3. Ensure firewall allows outbound HTTPS connections
4. Try accessing /health endpoint directly in browser

## Security Best Practices

For production:

1. **Change default passwords**: Use strong, unique passwords
2. **Rotate JWT secret**: Generate new secret periodically
3. **Enable Railway's built-in security**: Check Railway security settings
4. **Monitor access logs**: Review logs regularly for suspicious activity

## Cost Management

Railway offers:
- **Free tier**: $5 credit per month (sufficient for testing)
- **Pay as you go**: Usage-based pricing beyond free tier

Monitor usage in Railway dashboard under "Usage" tab.

## Next Steps

After successful deployment:

1. ✅ Share the Railway URL with team members
2. ✅ Update documentation with the production URL
3. ✅ Set up automated testing against the production API
4. ✅ Configure monitoring and alerts
5. ✅ Plan for production password management

## Support Resources

- Railway Documentation: https://docs.railway.com
- Railway Community: https://discord.gg/railway
- Railway Status: https://status.railway.com