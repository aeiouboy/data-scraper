# 🐳 Docker Deployment Fix Guide

## Problem: pip install failing during Docker build

### 🎯 Quick Solutions

## Option 1: Use Minimal Dockerfile (Guaranteed to work)

```bash
# Use the minimal version with only core dependencies
docker build -f Dockerfile.minimal -t ris-data-scrap .
docker run -p 8080:8080 ris-data-scrap
```

## Option 2: Use Multi-stage Dockerfile (Best performance)

```bash
# Use multi-stage build for smaller final image
docker build -f Dockerfile.multistage -t ris-data-scrap .
docker run -p 8080:8080 ris-data-scrap
```

## Option 3: Use Lightweight Dockerfile

```bash
# Use the lightweight version without ML dependencies
docker build -f Dockerfile.lightweight -t ris-data-scrap .
docker run -p 8080:8080 ris-data-scrap
```

## Option 4: Build with Fixed Dockerfile

The updated `Dockerfile` now includes:
- ✅ All necessary system dependencies (gfortran, libopenblas-dev)
- ✅ Pre-installs numpy and scipy separately
- ✅ Uses full Python image instead of slim

```bash
docker build -t ris-data-scrap .
docker run -p 8080:8080 ris-data-scrap
```

## Option 3: Skip ML Dependencies

If you don't need the advanced matching features, use `requirements-docker.txt`:

```dockerfile
# In your Dockerfile, replace:
COPY requirements.txt .
# With:
COPY requirements-docker.txt requirements.txt
```

## 🚀 Alternative: Use Pre-built Images

### Google Cloud Run (Easiest)
```bash
# Build and deploy to Cloud Run
gcloud builds submit --tag gcr.io/PROJECT-ID/ris-data-scrap
gcloud run deploy --image gcr.io/PROJECT-ID/ris-data-scrap \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars ENVIRONMENT=production
```

### Heroku Container Registry
```bash
# Push to Heroku using containers
heroku container:login
heroku container:push web -a your-app-name
heroku container:release web -a your-app-name
```

## 🔧 Build Performance Tips

### 1. Use Multi-stage Build
```dockerfile
# Add this to Dockerfile for smaller final image
FROM python:3.11 as builder
# ... install dependencies

FROM python:3.11-slim as runtime
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY . .
```

### 2. Use Docker Layer Caching
```bash
# Build with cache from registry
docker build --cache-from ris-data-scrap:latest -t ris-data-scrap .
```

### 3. Build on Different Architecture
```bash
# If building on M1/M2 Mac for deployment
docker buildx build --platform linux/amd64 -t ris-data-scrap .
```

## 📋 Environment Variables for Container

```bash
docker run -p 8080:8080 \
  -e ENVIRONMENT=production \
  -e SUPABASE_URL=your-url \
  -e SUPABASE_ANON_KEY=your-key \
  -e SUPABASE_SERVICE_ROLE_KEY=your-service-key \
  -e FIRECRAWL_API_KEY=your-firecrawl-key \
  ris-data-scrap
```

## 🐛 Debugging Failed Builds

### 1. Build with verbose output
```bash
docker build --progress=plain --no-cache -t ris-data-scrap .
```

### 2. Interactive debugging
```bash
# Run a container with failed build image
docker run -it --entrypoint /bin/bash python:3.11
# Then manually run the failing commands
```

### 3. Check specific dependency
```bash
# Test individual package installation
docker run python:3.11 pip install sentence-transformers
```

## 🎯 Recommended Approach

**For production deployment, I recommend:**

1. **Try Render first** (no Docker needed) - just works with Python
2. **Use Heroku** with the fixed configuration files
3. **Use Docker only if** you specifically need containerization

The non-Docker platforms (Render, Railway, Heroku) are much simpler and handle Python dependencies automatically.