# 🚀 Deployment Guide

## Backend Deployment (Railway)

### 1. Setup Railway Project
1. Go to [railway.app](https://railway.app)
2. Click "Start a New Project" → "Deploy from GitHub repo"
3. Connect GitHub and select `aeiouboy/data-scraper`
4. Select branch: `feature/comprehensive-testing-framework`

### 2. Configure Environment Variables
Add these in Railway's Variables tab:

```bash
ENVIRONMENT=production
PORT=8000
HOST=0.0.0.0
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
FIRECRAWL_API_KEY=your-firecrawl-key
LOG_LEVEL=info
```

### 3. Deployment Settings
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `python run_api.py`
- **Port**: Railway will auto-detect from PORT env var

## Frontend Deployment (Vercel)

### 1. Setup Vercel Project
1. Go to [vercel.com](https://vercel.com)
2. Click "New Project" → "Import Git Repository"
3. Select `aeiouboy/data-scraper`
4. Configure:
   - **Framework Preset**: React
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `build`

### 2. Configure Environment Variables
Add these in Vercel's Environment Variables:

```bash
REACT_APP_API_URL=https://your-railway-app.railway.app/api
```

### 3. Update vercel.json
After getting your Railway URL, update `frontend/vercel.json`:

```json
{
  "rewrites": [
    {
      "source": "/api/(.*)",
      "destination": "https://YOUR-ACTUAL-RAILWAY-URL.railway.app/api/$1"
    }
  ]
}
```

## Post-Deployment Steps

### 1. Update CORS Settings
In your deployed backend, ensure CORS allows your Vercel domain:

```python
# In src/api/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://your-vercel-app.vercel.app",
        "http://localhost:3000"  # for development
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. Test Deployment
1. Visit your Vercel frontend URL
2. Check that API calls work properly
3. Test key features:
   - Product search
   - Price comparisons
   - Scraping functionality

### 3. Monitor Deployment
- **Railway**: Check logs in Railway dashboard
- **Vercel**: Check function logs in Vercel dashboard
- **Database**: Monitor Supabase dashboard for activity

## Troubleshooting

### Common Issues
1. **CORS Errors**: Update allowed origins in FastAPI
2. **API Connection Issues**: Check Railway URL in Vercel env vars
3. **Build Failures**: Check dependencies and node version
4. **Database Connection**: Verify Supabase credentials

### Logs
- **Railway Logs**: `railway logs`
- **Vercel Logs**: Available in Vercel dashboard
- **Browser Console**: Check for frontend errors

## URLs
- **Backend API**: `https://your-app.railway.app`
- **Frontend**: `https://your-app.vercel.app`
- **API Docs**: `https://your-app.railway.app/docs`