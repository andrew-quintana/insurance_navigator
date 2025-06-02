# 🆓 FREE TIER Deployment: FastAPI + Supabase + Render

Deploy your Insurance Navigator completely **FREE** using free tiers from Supabase and Render!

## 💰 **Cost Breakdown: $0/month**
- ✅ **Render Free**: $0/month
- ✅ **Supabase Free**: $0/month  
- ✅ **GitHub**: Free for public repos
- **Total: FREE** 🎉

## 🚀 **Quick Deploy (5 minutes)**

### 1. **Supabase Free Setup** 
```bash
# Go to https://supabase.com
# Sign up with GitHub (free)
# Create new project:
#   - Name: insurance-navigator
#   - Database password: (generate strong one)
#   - Region: (closest to you)
#   - Pricing: FREE TIER (automatically selected)
```

**Free Tier Includes:**
- ✅ 500MB database storage
- ✅ 2GB bandwidth/month
- ✅ 50MB file storage
- ✅ Authentication & real-time features
- ✅ Up to 50,000 monthly active users

### 2. **Render Free Setup**
```bash
# Go to https://render.com
# Sign up with GitHub (free)
# Create Blueprint:
#   - Connect your GitHub repo
#   - Render detects render.yaml
#   - Plan: FREE (automatically from render.yaml)
```

**Free Tier Includes:**
- ✅ 750 hours/month (enough for 24/7 if it's your only service)
- ✅ 512MB RAM, 0.1 CPU
- ✅ Sleeps after 15 mins of inactivity (spins up in ~30 seconds)
- ✅ Custom domains supported
- ✅ SSL certificates included

### 3. **Environment Variables (Same as Paid)**
```bash
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
DATABASE_URL=postgresql://postgres.your-project-ref:password@aws-0-us-east-1.pooler.supabase.com:6543/postgres
JWT_SECRET_KEY=your-existing-supabase-jwt-secret
```

## ⚠️ **Free Tier Limitations**

### Render Free Limitations:
- **Sleep Mode**: App sleeps after 15 mins of inactivity
- **Cold Start**: ~30 second startup time when "waking up"
- **Build Time**: 20 minutes max build time
- **Bandwidth**: No specific limit but fair usage
- **Support**: Community support only

### Supabase Free Limitations:
- **Database**: 500MB storage limit
- **Bandwidth**: 2GB/month
- **Storage**: 50MB file storage
- **Pausing**: Projects pause after 7 days of inactivity
- **Backups**: No point-in-time recovery

## 🎯 **Optimizations for Free Tier**

### 1. **Keep App Warm (Optional)**
```bash
# Add this to your cron job or use a service like UptimeRobot
# Ping every 14 minutes to prevent sleeping:
curl https://your-app-name.onrender.com/health
```

### 2. **Database Optimization**
```python
# Already included in your app:
# - Connection pooling via Supabase
# - Efficient queries in your services
# - Proper indexing
```

### 3. **Monitor Usage**
- **Supabase**: Dashboard shows database size & bandwidth usage
- **Render**: Dashboard shows build minutes & uptime
- **Set up alerts** when approaching limits

## 🚦 **When to Upgrade**

### Upgrade Render ($7/month) when:
- ❌ Sleep mode affects user experience  
- ❌ Need guaranteed uptime
- ❌ Need faster build times
- ❌ Need premium support

### Upgrade Supabase ($25/month) when:
- ❌ Database > 500MB
- ❌ Bandwidth > 2GB/month  
- ❌ Need point-in-time recovery
- ❌ Need more file storage

## 🧪 **Testing Free Tier Limits**

### Check Supabase Usage:
```sql
-- Database size query
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### Monitor Render:
- Dashboard shows real-time metrics
- Build time tracking
- Sleep/wake logs

## 🔄 **Free Tier Deployment Commands**

```bash
# 1. Push to GitHub
git add .
git commit -m "Deploy to free tier"
git push origin main

# 2. Test locally first (optional)
docker build -t insurance-navigator .
docker run -p 8000:8000 --env-file .env insurance-navigator

# 3. Test deployed API (after Render deployment)
curl https://your-app-name.onrender.com/health

# 4. Monitor sleep/wake
curl -w "@curl-format.txt" https://your-app-name.onrender.com/health
```

## 📊 **Free Tier vs Paid Comparison**

| Feature | Free Tier | Paid Tier |
|---------|-----------|-----------|
| **Cost** | $0/month | ~$32/month |
| **Database** | 500MB | 8GB+ |
| **Sleep Mode** | Yes (15 min) | No |
| **Startup Time** | ~30 seconds | Instant |
| **Uptime** | Fair usage | 99.9%+ SLA |
| **Support** | Community | Priority |
| **Backups** | None | Point-in-time |

## 🎯 **Free Tier Strategy**

### Phase 1: **MVP & Testing** (Free Tier)
- ✅ Perfect for development and testing
- ✅ Demo to users and stakeholders  
- ✅ Validate product-market fit
- ✅ Learn the platform

### Phase 2: **Growth** (Upgrade Selectively)
- Upgrade Render first if sleep mode is problematic
- Keep Supabase free until hitting storage limits
- Monitor usage and upgrade as needed

### Phase 3: **Production** (Full Paid)
- Both services on paid plans
- Professional support
- Guaranteed uptime and performance

## 🚀 **Deploy Now - FREE**

```bash
# Everything is already configured for free tier!
git add .
git commit -m "Ready for free tier deployment"
git push origin main

# Then create Render Blueprint with your repo
# Your app will be live in ~5 minutes at:
# https://your-app-name.onrender.com
```

---

**Perfect for:** MVPs, testing, demos, learning, side projects
**Upgrade when:** You have users who need guaranteed uptime 🚀 