# HomePro Product Manager - Setup Guide

This guide will help you set up and run the HomePro Product Manager application, which includes a FastAPI backend and React frontend.

## Prerequisites

- Python 3.13+
- Node.js 16+ and npm
- Supabase account and database
- Firecrawl API key

## Environment Setup

### 1. Clone the Repository
```bash
git clone git@github.com:aeiouboy/data-scraper.git
cd data-scraper
```

### 2. Configure Environment Variables
Copy the example environment file and add your credentials:
```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```bash
# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key

# Firecrawl API
FIRECRAWL_API_KEY=your_firecrawl_api_key

# Optional: Environment
ENVIRONMENT=development
```

### 3. Database Setup
1. Create a new Supabase project
2. Run the SQL schema from `scripts/create_schema.sql` in your Supabase SQL Editor
3. Enable Row Level Security (RLS) if required

## Backend Setup (FastAPI)

### 1. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

**If you encounter dependency conflicts with httpx/supabase:**
```bash
pip install "httpx>=0.24,<0.26" "supabase>=2.3.0" --upgrade
```

### 3. Test Database Connection
```bash
python3 -m app.test_connection
```

### 4. Start the API Server
```bash
python3 run_api.py
```

The API will be available at:
- **API Server**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Frontend Setup (React)

### 1. Navigate to Frontend Directory
```bash
cd frontend
```

### 2. Install Dependencies
```bash
npm install
```

### 3. Start Development Server
```bash
PORT=3002 npm start
```

The frontend will be available at:
- **Web Interface**: http://localhost:3002

## Running Both Services

### Option 1: Two Terminal Windows

**Terminal 1 - Backend:**
```bash
cd "/path/to/project"
source venv/bin/activate
python3 run_api.py
```

**Terminal 2 - Frontend:**
```bash
cd "/path/to/project/frontend"
PORT=3002 npm start
```

### Option 2: Background Process (Backend only)
```bash
# Start backend in background
source venv/bin/activate
nohup python3 run_api.py &

# Start frontend normally
cd frontend
PORT=3002 npm start
```

## Verification

1. **API Health Check:**
   ```bash
   curl http://localhost:8000/docs
   ```

2. **Frontend Access:**
   Open http://localhost:3002 in your browser

3. **Full Integration Test:**
   - Navigate to Products page
   - Try searching for products
   - Create a test scraping job

## Features Available

### 🎯 Dashboard
- Overview metrics (total products, prices, sales)
- Daily scraping activity charts
- Recent job status

### 🔍 Product Management
- Advanced search and filtering
- Brand and category filters
- Price range filtering
- Individual product rescraping
- Real-time product data

### 🚀 Scraping Management
- Create scraping jobs (Category, Product, Search)
- Real-time job monitoring with progress bars
- Job status tracking and cancellation
- Success rate analytics

### 📊 Analytics
- Price trend visualization framework
- Scraping performance metrics
- Category distribution charts

### ⚙️ Settings
- Configure scraping parameters
- Set concurrent job limits
- Adjust rate limiting
- Environment information

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError: No module named 'uvicorn'**
   ```bash
   source venv/bin/activate
   pip install fastapi uvicorn
   ```

2. **react-scripts: command not found**
   ```bash
   cd frontend
   npm install react-scripts --save
   npm install
   ```

3. **Port already in use**
   ```bash
   # For frontend
   PORT=3003 npm start
   
   # For backend, edit run_api.py to change port
   ```

4. **Database connection errors**
   - Verify Supabase credentials in `.env`
   - Check if database schema is created
   - Ensure network connectivity

5. **Firecrawl API errors**
   - Verify API key is correct
   - Check API quota/limits
   - Ensure URL format is correct

### Performance Tips

1. **Backend Optimization:**
   - Use connection pooling for database
   - Implement caching for frequent queries
   - Monitor memory usage during scraping

2. **Frontend Optimization:**
   - Enable React Query caching
   - Implement virtual scrolling for large datasets
   - Use production build for deployment

## Development Commands

### Backend
```bash
# Run tests
pytest

# Format code
black app/

# Type checking
mypy app/

# Database migrations (if needed)
python3 scripts/migrate.py
```

### Frontend
```bash
# Run tests
npm test

# Build for production
npm run build

# Analyze bundle size
npm run build -- --analyze
```

## Production Deployment

### Backend
```bash
# Install production dependencies only
pip install --no-dev -r requirements.txt

# Run with production WSGI server
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### Frontend
```bash
# Build optimized production bundle
npm run build

# Serve static files (example with serve)
npx serve -s build -l 3000
```

## Support

For issues and feature requests:
- Check existing issues in the repository
- Create detailed bug reports with logs
- Include environment information and steps to reproduce

---

**Quick Start Commands:**
```bash
# Backend
source venv/bin/activate && python3 run_api.py

# Frontend (new terminal)
cd frontend && PORT=3002 npm start
```

🚀 **Access the application at http://localhost:3002**