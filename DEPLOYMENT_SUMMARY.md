# 🆓 Ready-to-Deploy FastAPI + Supabase + Render (FREE TIER)

## ✅ Files Created & Ready

| File | Purpose | Status |
|------|---------|--------|
| `Dockerfile` | Production container config | ✅ Ready |
| `render.yaml` | Render deployment config (FREE TIER) | ✅ Ready |
| `.dockerignore` | Optimized Docker builds | ✅ Ready |
| `deploy-guide.md` | Comprehensive deployment guide | ✅ Ready |
| `FREE_TIER_DEPLOYMENT.md` | **FREE TIER specific guide** | ✅ Ready |
| `scripts/quick_deploy.sh` | Pre-deployment validation script | ✅ Ready |
| `scripts/keep_warm.sh` | **Keep Render app warm (free tier)** | ✅ Ready |

## 💰 **COST: $0/month** 🎉

- ✅ **Render Free**: $0/month (512MB RAM, sleeps after 15min)
- ✅ **Supabase Free**: $0/month (500MB DB, 2GB bandwidth)
- ✅ **GitHub**: $0/month (public repo)

## 🔐 Environment Variables Needed

Since you have Supabase already configured, collect these values:

### From Supabase Dashboard (Settings → API):
```bash
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=***REMOVED***...
SUPABASE_SERVICE_ROLE_KEY=***REMOVED***...
```

### From Supabase Dashboard (Settings → Database):
```bash
DATABASE_URL=postgresql://postgres.your-project-ref:your-password@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

### Use Supabase JWT Secret:
```bash
JWT_SECRET_KEY=your-existing-supabase-jwt-secret
```

## 🚀 Deploy to Render FREE - 5 Minutes

### 1. Push to GitHub (if not done):
```bash
git add .
git commit -m "Add FREE TIER deployment files"
git push origin main
```

### 2. Create Render Service (FREE):
1. Go to [render.com](https://render.com) → Sign up/Login (FREE)
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub repository
4. Render auto-detects `render.yaml` with **FREE TIER** ✅

### 3. Configure Environment Variables:
In Render dashboard → Your service → Environment tab, add:

```bash
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your-anon-key-here
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key-here
DATABASE_URL=postgresql://postgres.your-project-ref:password@aws-0-us-east-1.pooler.supabase.com:6543/postgres
JWT_SECRET_KEY=your-existing-supabase-jwt-secret
```

### 4. Deploy & Test:
- Render automatically builds and deploys (FREE)
- Your API will be live at: `https://your-app-name.onrender.com`
- Test: `https://your-app-name.onrender.com/health`

## ⚠️ **Free Tier Considerations**

### **Render Free Limitations:**
- 🛌 **Sleeps after 15 minutes** of inactivity
- ⏰ **~30 second startup** when app wakes up
- 💾 **512MB RAM, 0.1 CPU** (sufficient for most use)
- 🕐 **750 hours/month** (unlimited if it's your only service)

### **Supabase Free Limitations:**
- 💾 **500MB database** storage
- 📊 **2GB bandwidth/month**
- 📁 **50MB file** storage
- 😴 **Pauses after 7 days** of inactivity

### **Optional: Keep App Warm**
```bash
# Update the URL in scripts/keep_warm.sh then run:
./scripts/keep_warm.sh

# Or use UptimeRobot.com (free) to ping every 5 minutes
```

## 🧪 Local Testing Before Deploy

```bash
# Run our validation script
./scripts/quick_deploy.sh

# Or test Docker manually:
docker build -t insurance-navigator .
docker run -p 8000:8000 --env-file .env insurance-navigator

# Test endpoints:
curl http://localhost:8000/health
```

## 🔍 Your App Architecture (FREE)

```
Frontend (Vercel Free) → Render Free (FastAPI) → Supabase Free (PostgreSQL + Auth)
```

- **Frontend**: Your existing UI in `/ui` directory (deploy free on Vercel)
- **Backend**: FastAPI app deployed to Render (FREE)
- **Database**: Supabase PostgreSQL with authentication (FREE)
- **Total Cost**: **$0/month** 🎉

## ⚡ Quick Commands

```bash
# Validate everything is ready
./scripts/quick_deploy.sh

# Test health endpoint after deploy
curl https://your-app-name.onrender.com/health

# Keep app warm (optional)
./scripts/keep_warm.sh

# Check logs
# Go to Render dashboard → Service → Logs

# Redeploy
git push origin main  # Auto-deploys
```

## 🔧 Free Tier Optimizations Included

- ✅ Production-ready Dockerfile with security
- ✅ Health checks for monitoring
- ✅ Optimized Docker builds (.dockerignore)
- ✅ Auto-deploy on git push
- ✅ Connection pooling via Supabase
- ✅ CORS configured for your frontend
- ✅ Environment-based configuration
- ✅ Keep-warm script for Render free tier

## 🎯 Upgrade Path

### When to Upgrade Render to Starter ($7/month):
- ❌ Sleep mode affects user experience
- ❌ Need guaranteed uptime
- ❌ App gets frequent traffic

### When to Upgrade Supabase to Pro ($25/month):
- ❌ Database approaching 500MB
- ❌ Bandwidth approaching 2GB/month
- ❌ Need point-in-time recovery

## 🚨 Important Notes

- Your Supabase JWT secret is already secure ✅
- All sensitive data goes in Render environment variables ✅
- SSL/HTTPS is automatic with Render ✅
- Database migrations run automatically ✅
- **Apps sleep on FREE tier - this is normal** ✅

---

## 🎉 **Deploy Now - COMPLETELY FREE**

```bash
git add .
git commit -m "Ready for FREE TIER deployment"
git push origin main
```

**Your FREE API will be live in ~5 minutes at:**  
`https://your-app-name.onrender.com` 

Perfect for MVPs, testing, demos, and learning! 🚀 