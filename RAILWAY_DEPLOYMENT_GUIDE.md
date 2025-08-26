# Railway Deployment Guide

Complete guide to deploying RIS Data Scrap system to Railway.

## 📋 Prerequisites

1. **Railway Account**: [Sign up at railway.app](https://railway.app)
2. **Supabase Database**: Production database credentials
3. **Environment Variables**: All required API keys and secrets

## 🚀 Quick Deploy

### Option 1: Deploy from GitHub (Recommended)

1. Connect your GitHub repository to Railway
2. Railway will automatically detect the configuration from `railway.json`
3. Set environment variables (see section below)
4. Deploy!

### Option 2: Railway CLI Deploy

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project
railway init

# Set environment variables
railway variables set SUPABASE_URL=your_supabase_url
railway variables set SUPABASE_ANON_KEY=your_anon_key
railway variables set SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Deploy
railway up
```

## 🔧 Configuration Files

### Railway Configuration (`railway.json`)
- **Health Check**: `/health` endpoint with 300s timeout
- **Restart Policy**: ON_FAILURE with 10 max retries
- **Environment**: Production settings with optimized variables

### Nixpacks Configuration (`nixpacks.toml`)
- **Python Version**: 3.11
- **Build Optimization**: Multi-phase build with validation
- **Dependencies**: Railway-specific requirements from `requirements-railway.txt`

### Requirements (`requirements-railway.txt`)
- **Minimal Dependencies**: Only essential packages for Railway
- **Version Pinning**: Exact versions to prevent proxy issues
- **No Heavy Dependencies**: Excludes numpy/pandas for faster builds

## 🌍 Environment Variables

### Required Variables
```bash
# Database
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key

# Application
ENVIRONMENT=production
LOG_LEVEL=info

# Optional - API Services
FIRECRAWL_API_KEY=your_firecrawl_key
```

### Automatic Variables (Set by Railway)
```bash
PORT=8000  # Railway sets this automatically
PYTHONUNBUFFERED=1
PYTHONDONTWRITEBYTECODE=1
```

## 📊 Health Monitoring

### Health Check Endpoint
- **URL**: `https://your-app.railway.app/health`
- **Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-12-28T10:30:00Z",
  "version": "2.0.0",
  "environment": "production",
  "uptime": 3600,
  "services": {
    "api": "healthy",
    "database": "healthy"
  }
}
```

### Railway Monitoring
- Health checks run every 60 seconds
- Automatic restarts on failure
- Real-time logs and metrics in Railway dashboard

## 🔄 Deployment Process

### Build Phase
1. **Setup**: Install Python 3.11 and build tools
2. **Install**: Create virtual environment and install dependencies
3. **Build**: Validate FastAPI app import
4. **Start**: Launch with `railway_start.py`

### Runtime Phase
1. **Proxy Clearing**: Remove any proxy configurations
2. **Service Initialization**: Start Supabase connections
3. **Server Start**: Launch uvicorn with production settings
4. **Health Check**: Enable monitoring endpoint

## 🎯 Performance Optimization

### Railway Configuration
- **Single Worker**: Optimized for Railway free tier
- **Connection Pooling**: Efficient database connections
- **Static File Serving**: Optimized for web assets
- **Caching**: Built-in response caching

### Database Optimization
- **Connection Limits**: Suitable for Railway environment
- **Query Optimization**: Indexed queries for better performance
- **Data Pagination**: Efficient data loading

## 🔍 Troubleshooting

### Common Issues

#### 1. Proxy Errors
```
ProxyError: Cannot connect through proxy
```
**Solution**: Railway automatically clears proxy variables in `railway_start.py`

#### 2. Import Errors
```
ImportError: No module named 'src'
```
**Solution**: Project root is added to Python path in startup script

#### 3. Port Binding Issues
```
[Errno 98] Address already in use
```
**Solution**: Railway sets PORT automatically, app binds to `0.0.0.0:$PORT`

#### 4. Database Connection Issues
```
Connection timeout to Supabase
```
**Solution**: Check environment variables and Supabase URL format

### Debug Steps

1. **Check Logs**: View Railway deployment logs
2. **Environment**: Verify all environment variables are set
3. **Health Check**: Test `/health` endpoint
4. **Database**: Verify Supabase connection
5. **Dependencies**: Ensure all packages installed correctly

### Log Analysis

#### Successful Startup
```
🔧 Starting Railway deployment process...
✅ uvicorn imported successfully
🚀 Starting RIS Data Scrap API for Railway
📊 Environment: production
🌐 Host: 0.0.0.0
🔌 Port: 8000
✅ FastAPI app imported successfully
🚀 Starting uvicorn server...
```

#### Error Indicators
```
❌ Failed to import FastAPI app
🔍 PROXY ERROR DETECTED!
❌ Failed to start API server
```

## 🌐 Frontend Configuration

### For Production Build
If deploying frontend separately:

```bash
# Update API base URL
export REACT_APP_API_URL=https://your-api.railway.app

# Build for production
npm run build
```

### Environment Variables
```bash
REACT_APP_API_URL=https://your-railway-api.railway.app
REACT_APP_ENVIRONMENT=production
```

## 📈 Monitoring & Scaling

### Railway Dashboard
- **Deployment Status**: Real-time deployment progress
- **Resource Usage**: CPU, Memory, Network metrics
- **Logs**: Application and system logs
- **Environment**: Variable management

### Performance Metrics
- **Response Time**: API endpoint performance
- **Error Rate**: Failed request tracking
- **Uptime**: Service availability
- **Database**: Connection pool status

### Scaling Options
- **Vertical**: Increase memory/CPU resources
- **Database**: Upgrade Supabase plan for more connections
- **CDN**: Add Railway's built-in CDN for static assets

## 🔐 Security

### Production Security
- **HTTPS**: Enabled by default on Railway
- **Environment Variables**: Secured and encrypted
- **CORS**: Configured for production domains
- **Rate Limiting**: Built-in DDoS protection

### Best Practices
- Use service role keys for database operations
- Rotate API keys regularly
- Monitor access logs
- Set appropriate CORS origins

## 📞 Support

### Railway Support
- **Documentation**: [railway.app/docs](https://docs.railway.app)
- **Discord**: Railway community server
- **GitHub**: Railway platform issues

### Project Support
- **Health Check**: `GET /health`
- **API Documentation**: `GET /docs`
- **Admin Interface**: Railway dashboard