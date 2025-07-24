# 🚀 Multi-Platform Backend Deployment Guide

## Platform Comparison

| Platform | Difficulty | Free Tier | Best For | Setup Time |
|----------|------------|-----------|----------|------------|
| **Render** | ⭐⭐ Easy | ✅ 750hrs/month | Python apps | 5 min |
| **Railway** | ⭐⭐ Easy | ✅ $5/month credit | Modern apps | 5 min |
| **Heroku** | ⭐⭐⭐ Medium | ✅ 1000hrs/month | Enterprise | 10 min |
| **Fly.io** | ⭐⭐⭐ Medium | ✅ Limited | Global edge | 15 min |
| **DigitalOcean** | ⭐⭐⭐ Medium | ❌ $5/month | Developers | 10 min |
| **Google Cloud Run** | ⭐⭐⭐⭐ Hard | ✅ Generous | Serverless | 20 min |

## 🥇 Recommended: Render (Most Reliable)

### Quick Deploy
1. Go to [render.com](https://render.com)
2. **"New Web Service"** → **"Build and deploy from Git"**
3. Connect GitHub → Select `aeiouboy/data-scraper`
4. Settings:
   - **Branch**: `feature/comprehensive-testing-framework`
   - **Runtime**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python run_api.py`
   - **Port**: Auto-detected

### Environment Variables
```bash
ENVIRONMENT=production
SUPABASE_URL=your-supabase-url
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-key
FIRECRAWL_API_KEY=your-firecrawl-key
LOG_LEVEL=info
```

## 🥈 Alternative: Heroku

### Deploy Button
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/aeiouboy/data-scraper/tree/feature/comprehensive-testing-framework)

### Manual Deploy
```bash
# Install Heroku CLI first
heroku create your-app-name
heroku config:set ENVIRONMENT=production
heroku config:set SUPABASE_URL=your-url
# ... add other env vars
git push heroku feature/comprehensive-testing-framework:main
```

## 🥉 Alternative: Fly.io

### Deploy Commands
```bash
# Install flyctl first
flyctl auth login
flyctl launch --no-deploy
flyctl secrets set ENVIRONMENT=production
flyctl secrets set SUPABASE_URL=your-url
# ... add other secrets
flyctl deploy
```

## 🐳 Docker Deployment (Any Platform)

The included `Dockerfile` works with:
- Google Cloud Run
- AWS ECS/Fargate  
- Azure Container Instances
- DigitalOcean Apps

### Google Cloud Run Example
```bash
# Build and deploy
gcloud builds submit --tag gcr.io/PROJECT-ID/ris-data-scrap
gcloud run deploy --image gcr.io/PROJECT-ID/ris-data-scrap --platform managed
```

## 📋 Required Environment Variables

All platforms need these variables:

```bash
# Core Settings
ENVIRONMENT=production
HOST=0.0.0.0
PORT=8000  # or platform-specific port

# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# External APIs
FIRECRAWL_API_KEY=your-firecrawl-api-key

# Optional
LOG_LEVEL=info
PYTHON_VERSION=3.11
```

## 🔧 Platform-Specific Files Created

- `render.yaml` - Render configuration
- `app.json` - Heroku configuration  
- `fly.toml` - Fly.io configuration
- `.do/app.yaml` - DigitalOcean configuration
- `Dockerfile` - Container deployment
- `.ebextensions/python.config` - AWS Elastic Beanstalk

## 🧪 Testing Your Deployment

After deployment, test these endpoints:
```bash
# Health check
curl https://your-app.domain.com/

# API documentation
curl https://your-app.domain.com/docs

# API endpoint test
curl https://your-app.domain.com/api/retailers
```

## 🚨 Troubleshooting

### Common Issues
1. **Port binding**: Make sure PORT env var is set correctly
2. **Dependencies**: Check requirements.txt is complete
3. **Python version**: Ensure Python 3.11 is specified
4. **Start command**: Verify `python run_api.py` works locally

### Platform-Specific Issues
- **Render**: Usually just works, check build logs
- **Railway**: May need manual start command override
- **Heroku**: Check dyno formation and scaling
- **Fly.io**: Verify fly.toml configuration matches your needs

Choose the platform that best fits your needs and budget!