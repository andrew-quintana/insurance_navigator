# Build Logs API Setup Guide

This guide helps you set up automatic fetching of deployment logs from Vercel and Render for your build log files.

## 🌐 Vercel API Setup

### 1. Create API Token
1. Go to [Vercel Account Tokens](https://vercel.com/account/tokens)
2. Click "Create Token"
3. Give it a name like "Build Logs Fetcher"
4. Set expiration as needed
5. Copy the token (you won't see it again!)

### 2. Get Project ID
1. Go to your Vercel project dashboard
2. Click "Settings" tab
3. In "General" section, copy the "Project ID"

### 3. Set Environment Variables
```bash
export VERCEL_API_TOKEN="vercel_xxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export VERCEL_PROJECT_ID="prj_xxxxxxxxxxxxxxxxxxxxxxxxx"
```

## 🔧 Render API Setup

### 1. Create API Token
1. Go to [Render Account API Keys](https://dashboard.render.com/account/api-keys)
2. Click "Create API Key"
3. Give it a name like "Build Logs Fetcher"
4. Copy the token

### 2. Get Service ID
1. Go to your Render service dashboard
2. Look at the URL: `https://dashboard.render.com/web/srv-xxxxxxxxxxxxxxxxxxxxx`
3. Copy the service ID (the `srv-xxxxxxxxxxxxxxxxxxxxx` part)

### 3. Set Environment Variables
```bash
export RENDER_API_TOKEN="rnd_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
export RENDER_SERVICE_ID="srv-xxxxxxxxxxxxxxxxxxxxx"
```

## 💾 Persistent Setup

### Option 1: Add to Shell Profile
Add the export commands to your shell profile:

**For Bash/Zsh:**
```bash
echo 'export VERCEL_API_TOKEN="your-token"' >> ~/.bashrc
echo 'export VERCEL_PROJECT_ID="your-project-id"' >> ~/.bashrc
echo 'export RENDER_API_TOKEN="your-token"' >> ~/.bashrc
echo 'export RENDER_SERVICE_ID="your-service-id"' >> ~/.bashrc
source ~/.bashrc
```

### Option 2: Create .env File
Create a `.env` file in your project root:

```bash
# Build Logs API Configuration
VERCEL_API_TOKEN=vercel_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
VERCEL_PROJECT_ID=prj_xxxxxxxxxxxxxxxxxxxxxxxxx
RENDER_API_TOKEN=rnd_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
RENDER_SERVICE_ID=srv-xxxxxxxxxxxxxxxxxxxxx
```

Then load it before running the script:
```bash
source .env
./scripts/new_build_logs.sh
```

## 🧪 Test Your Setup

Run the setup check:
```bash
./scripts/new_build_logs.sh --setup
```

Test fetching logs:
```bash
# Test both APIs
./scripts/new_build_logs.sh

# Test only Vercel
./scripts/new_build_logs.sh --vercel-only

# Test only Render
./scripts/new_build_logs.sh --render-only
```

## 🔐 Security Best Practices

1. **Never commit API tokens** to version control
2. **Set expiration dates** on tokens when possible
3. **Use read-only permissions** where available
4. **Rotate tokens periodically**
5. **Keep tokens in secure environment variable storage**

## 🔧 Troubleshooting

### "Missing API Token" Error
- Verify environment variables are set: `echo $VERCEL_API_TOKEN`
- Check for typos in variable names
- Ensure tokens haven't expired

### "No Deployments Found" Error
- Verify project/service IDs are correct
- Check that deployments exist in the dashboard
- Ensure API token has read permissions

### "API Error" Messages
- Check API token permissions
- Verify network connectivity
- Check service status pages:
  - [Vercel Status](https://vercel-status.com/)
  - [Render Status](https://status.render.com/)

## 📊 What Gets Fetched

### Vercel Logs Include:
- Build events and timestamps
- Deployment ID and URL
- Build status and duration
- Error messages and warnings
- Function deployments

### Render Logs Include:
- Full deployment logs
- Build steps and timing
- Docker build output
- Service startup logs
- Error traces

## 🎯 Usage Examples

```bash
# Auto-fetch latest deployments (recommended)
./scripts/new_build_logs.sh

# Create logs for specific deployment time
./scripts/new_build_logs.sh 202506041530

# Only get Vercel logs (for frontend deploys)
./scripts/new_build_logs.sh --vercel-only

# Only get Render logs (for backend deploys)
./scripts/new_build_logs.sh --render-only
```

## 📝 File Output

The script creates files with actual deployment timestamps:
- `{YYYYMMDDHHMM}-render.md` - Auto-fetched Render logs
- `{YYYYMMDDHHMM}-vercel.md` - Auto-fetched Vercel logs  
- `{YYYYMMDDHHMM}-safari.md` - Manual entry (browser logs)
- `{YYYYMMDDHHMM}-visual_observation.md` - Manual entry (observations)

Where `{YYYYMMDDHHMM}` is the actual deployment start time! 