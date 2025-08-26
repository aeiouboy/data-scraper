#!/bin/bash

# Railway Deployment Script for RIS Data Scrap
# Usage: ./deploy-railway.sh [production|staging]

set -e  # Exit on any error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Environment (default to production)
ENVIRONMENT=${1:-production}

echo -e "${BLUE}🚀 Railway Deployment Script${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "Environment: ${GREEN}$ENVIRONMENT${NC}"
echo ""

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo -e "${RED}❌ Railway CLI is not installed${NC}"
    echo -e "${YELLOW}Installing Railway CLI...${NC}"
    npm install -g @railway/cli
fi

# Login check
if ! railway whoami &> /dev/null; then
    echo -e "${YELLOW}⚡ Please login to Railway...${NC}"
    railway login
fi

# Validate configuration files
echo -e "${BLUE}📋 Validating configuration files...${NC}"

# Check railway.json
if [ ! -f "railway.json" ]; then
    echo -e "${RED}❌ railway.json not found${NC}"
    exit 1
fi

# Check nixpacks.toml
if [ ! -f "nixpacks.toml" ]; then
    echo -e "${RED}❌ nixpacks.toml not found${NC}"
    exit 1
fi

# Check requirements-railway.txt
if [ ! -f "requirements-railway.txt" ]; then
    echo -e "${RED}❌ requirements-railway.txt not found${NC}"
    exit 1
fi

# Check railway_start.py
if [ ! -f "railway_start.py" ]; then
    echo -e "${RED}❌ railway_start.py not found${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All configuration files found${NC}"

# Validate Python imports
echo -e "${BLUE}🐍 Validating Python imports...${NC}"
python -c "from src.api.main import app; print('✅ FastAPI app import successful')" || {
    echo -e "${RED}❌ FastAPI app import failed${NC}"
    exit 1
}

# Check environment variables
echo -e "${BLUE}🔧 Checking environment variables...${NC}"

REQUIRED_VARS=(
    "SUPABASE_URL"
    "SUPABASE_ANON_KEY"
    "SUPABASE_SERVICE_ROLE_KEY"
)

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        echo -e "${YELLOW}⚠️  $var not set in local environment${NC}"
        echo -e "${BLUE}Please set it in Railway dashboard after deployment${NC}"
    else
        echo -e "${GREEN}✅ $var is set${NC}"
        # Set in Railway (will overwrite if already exists)
        railway variables set "$var=${!var}" 2>/dev/null || echo -e "${YELLOW}⚠️  Could not set $var in Railway (may need to set manually)${NC}"
    fi
done

# Set production environment variables
echo -e "${BLUE}⚙️  Setting production environment variables...${NC}"
railway variables set ENVIRONMENT="$ENVIRONMENT"
railway variables set LOG_LEVEL="info"
railway variables set PYTHONUNBUFFERED="1"
railway variables set PYTHONDONTWRITEBYTECODE="1"

# Show current project
echo -e "${BLUE}📊 Railway Project Info:${NC}"
railway status

# Deploy
echo -e "${BLUE}🚀 Starting deployment...${NC}"
echo -e "${YELLOW}This may take several minutes...${NC}"

if railway up; then
    echo -e "${GREEN}✅ Deployment successful!${NC}"
    
    # Get the deployed URL
    URL=$(railway domain 2>/dev/null || echo "URL not available yet")
    if [ "$URL" != "URL not available yet" ]; then
        echo -e "${GREEN}🌐 Your API is available at: $URL${NC}"
        echo -e "${GREEN}📊 Health check: $URL/health${NC}"
        echo -e "${GREEN}📖 API docs: $URL/docs${NC}"
    fi
    
    # Show deployment status
    echo -e "${BLUE}📈 Checking deployment status...${NC}"
    railway status
    
    # Test health endpoint if URL is available
    if [ "$URL" != "URL not available yet" ]; then
        echo -e "${BLUE}🏥 Testing health endpoint...${NC}"
        sleep 10  # Wait for service to start
        if curl -s "$URL/health" | grep -q "healthy"; then
            echo -e "${GREEN}✅ Health check passed!${NC}"
        else
            echo -e "${YELLOW}⚠️  Health check may still be initializing...${NC}"
        fi
    fi
    
else
    echo -e "${RED}❌ Deployment failed${NC}"
    echo -e "${YELLOW}📝 Checking logs for errors...${NC}"
    railway logs --tail 50
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 Deployment complete!${NC}"
echo -e "${BLUE}📋 Next steps:${NC}"
echo -e "1. Check Railway dashboard for detailed metrics"
echo -e "2. Set up custom domain if needed"
echo -e "3. Configure frontend to use deployed API"
echo -e "4. Monitor logs: ${YELLOW}railway logs --tail${NC}"
echo ""
echo -e "${BLUE}🔗 Useful commands:${NC}"
echo -e "- View logs: ${YELLOW}railway logs${NC}"
echo -e "- Open dashboard: ${YELLOW}railway open${NC}"
echo -e "- Check status: ${YELLOW}railway status${NC}"
echo -e "- Shell access: ${YELLOW}railway shell${NC}"