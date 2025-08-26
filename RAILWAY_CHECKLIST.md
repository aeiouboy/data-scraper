# Railway Deployment Checklist

Pre-deployment checklist to ensure successful Railway deployment.

## ✅ Pre-Deployment Checklist

### 🔧 Configuration Files
- [ ] `railway.json` - Railway deployment configuration
- [ ] `nixpacks.toml` - Build configuration with Python 3.11
- [ ] `requirements-railway.txt` - Minimal production dependencies
- [ ] `railway_start.py` - Production startup script
- [ ] `RAILWAY_DEPLOYMENT_GUIDE.md` - Complete deployment guide

### 🐍 Python Application
- [ ] Health check endpoint `/health` working
- [ ] FastAPI app imports without errors
- [ ] All required dependencies in `requirements-railway.txt`
- [ ] No proxy configuration conflicts
- [ ] Environment variable handling

### 🌍 Environment Variables
- [ ] `SUPABASE_URL` - Database connection URL
- [ ] `SUPABASE_ANON_KEY` - Public API key
- [ ] `SUPABASE_SERVICE_ROLE_KEY` - Admin API key
- [ ] `ENVIRONMENT=production` - Runtime environment
- [ ] `LOG_LEVEL=info` - Logging configuration
- [ ] `FIRECRAWL_API_KEY` (Optional) - Web scraping service

### 🗄️ Database Configuration
- [ ] Supabase project running in production
- [ ] Database schema up to date
- [ ] Required tables and indexes exist
- [ ] Connection limits appropriate for Railway
- [ ] Backup and recovery configured

### 🔒 Security Setup
- [ ] CORS origins configured for production domain
- [ ] API keys secured (not in code)
- [ ] Rate limiting configured
- [ ] HTTPS enforcement enabled
- [ ] Sensitive data properly encrypted

### 📊 Monitoring & Logging
- [ ] Health check endpoint responsive
- [ ] Logging levels appropriate
- [ ] Error tracking configured
- [ ] Performance monitoring ready
- [ ] Uptime monitoring setup

### 🧪 Testing
- [ ] Local testing completed
- [ ] API endpoints working
- [ ] Database connections verified
- [ ] Critical user flows tested
- [ ] Load testing completed

## 🚀 Deployment Steps

### 1. Pre-Deploy Validation
```bash
# Check Python imports
python -c "from src.api.main import app; print('✅ FastAPI import successful')"

# Validate configuration
cat railway.json
cat nixpacks.toml
```

### 2. Environment Setup
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Initialize project (if new)
railway init
```

### 3. Set Environment Variables
```bash
# Required variables
railway variables set SUPABASE_URL="your_url"
railway variables set SUPABASE_ANON_KEY="your_key"
railway variables set SUPABASE_SERVICE_ROLE_KEY="your_service_key"

# Production settings
railway variables set ENVIRONMENT="production"
railway variables set LOG_LEVEL="info"
```

### 4. Deploy Application
```bash
# Quick deploy
railway up

# Or use deployment script
./deploy-railway.sh production
```

### 5. Post-Deploy Verification
```bash
# Check deployment status
railway status

# View logs
railway logs --tail 100

# Test health endpoint
curl https://your-app.railway.app/health
```

## 🔍 Common Issues & Solutions

### Build Errors
**Issue**: Python dependencies fail to install
```
ERROR: Could not find a version that satisfies the requirement
```
**Solution**: Check `requirements-railway.txt` for version conflicts

**Issue**: FastAPI import fails
```
ModuleNotFoundError: No module named 'src'
```
**Solution**: Verify Python path configuration in `railway_start.py`

### Runtime Errors
**Issue**: Port binding fails
```
[Errno 98] Address already in use
```
**Solution**: Railway sets `PORT` automatically, ensure app uses `0.0.0.0:$PORT`

**Issue**: Database connection timeout
```
Connection timeout to Supabase
```
**Solution**: Verify Supabase URL format and network connectivity

### Performance Issues
**Issue**: Slow response times
**Solution**: 
- Check Railway resource allocation
- Optimize database queries
- Review connection pooling

**Issue**: Memory limit exceeded
**Solution**:
- Monitor memory usage in Railway dashboard
- Optimize imports and data loading
- Consider upgrading Railway plan

## 📈 Post-Deployment Tasks

### Immediate Tasks (0-1 hour)
- [ ] Verify health check endpoint
- [ ] Test critical API endpoints
- [ ] Check application logs
- [ ] Validate database connectivity
- [ ] Configure custom domain (if needed)

### Short-term Tasks (1-24 hours)
- [ ] Monitor performance metrics
- [ ] Set up alerting/notifications
- [ ] Update frontend API configuration
- [ ] Test end-to-end user flows
- [ ] Document API endpoints

### Long-term Tasks (1-7 days)
- [ ] Configure backup strategies
- [ ] Set up monitoring dashboards
- [ ] Optimize performance based on metrics
- [ ] Plan scaling strategy
- [ ] Security audit and hardening

## 🔗 Resources

### Railway Documentation
- [Getting Started](https://docs.railway.app/getting-started)
- [Environment Variables](https://docs.railway.app/develop/variables)
- [Custom Domains](https://docs.railway.app/deploy/custom-domains)
- [Monitoring](https://docs.railway.app/monitor/observability)

### Project Resources
- **API Documentation**: `https://your-app.railway.app/docs`
- **Health Check**: `https://your-app.railway.app/health`
- **Railway Dashboard**: Access through railway.app
- **Logs**: `railway logs --tail`

### Support Channels
- **Railway Discord**: Community support
- **Railway Docs**: Comprehensive guides
- **GitHub Issues**: Project-specific issues
- **Supabase Support**: Database-related issues