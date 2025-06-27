# HomePro Product Manager UI

A modern web interface for managing HomePro product scraping, search, and analytics.

## Features

### 1. **Dashboard**
- Overview of key metrics (total products, average price, products on sale, etc.)
- Daily scraping activity visualization
- Top brands and price distribution
- Recent scraping job status

### 2. **Products Management**
- **Search & Filter**: Full-text search with advanced filtering
  - Filter by brand, category, price range
  - Filter by sale status and availability
- **Data Grid**: Sortable, paginated product listing
- **Actions**: 
  - Trigger individual product rescrape
  - View product on HomePro website
  - Export data (coming soon)

### 3. **Scraping Management**
- **Job Creation**: Create new scraping jobs
  - Category scraping: Discover and scrape all products in a category
  - Product scraping: Scrape specific product URLs
  - Search scraping: Scrape search results
- **Job Monitoring**: Real-time job status and progress
- **Job Control**: Cancel running jobs
- **Statistics**: View success rates and performance metrics

### 4. **Analytics**
- Price trend visualization
- Scraping performance metrics
- Category and brand distribution charts
- Export analytics reports

### 5. **Settings**
- Configure scraping parameters
  - Enable/disable scraping
  - Set concurrent job limits
  - Configure rate limiting
- View environment information
- Reset to default settings

## Tech Stack

### Backend (FastAPI)
- **Framework**: FastAPI with async support
- **Database**: Supabase (PostgreSQL)
- **Scraping**: Firecrawl API integration
- **Background Jobs**: Async background tasks

### Frontend (React + TypeScript)
- **UI Framework**: Material-UI (MUI)
- **State Management**: React Query (TanStack Query)
- **Routing**: React Router v6
- **Data Grid**: MUI X Data Grid
- **Charts**: Chart.js with react-chartjs-2

## Setup Instructions

### Backend Setup

1. Install Python dependencies:
```bash
pip install fastapi uvicorn
```

2. Run the API server:
```bash
python3 run_api.py
```

The API will be available at `http://localhost:8000`
- API documentation: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Frontend Setup

1. Navigate to frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Start development server:
```bash
npm start
```

The UI will be available at `http://localhost:3000`

## API Endpoints

### Products
- `POST /api/products/search` - Search products with filters
- `GET /api/products/{id}` - Get product details
- `GET /api/products/{id}/price-history` - Get price history
- `POST /api/products/{id}/rescrape` - Trigger product rescrape
- `GET /api/products/filters/brands` - Get all brands
- `GET /api/products/filters/categories` - Get all categories

### Scraping
- `POST /api/scraping/jobs` - Create scraping job
- `GET /api/scraping/jobs` - List scraping jobs
- `GET /api/scraping/jobs/{id}` - Get job details
- `POST /api/scraping/jobs/{id}/cancel` - Cancel job
- `POST /api/scraping/discover` - Discover product URLs

### Analytics
- `GET /api/analytics/dashboard` - Get dashboard data
- `GET /api/analytics/products/trends` - Get product trends
- `GET /api/analytics/scraping/performance` - Get performance metrics

### Configuration
- `GET /api/config` - Get configuration
- `PATCH /api/config` - Update configuration
- `POST /api/config/reset` - Reset to defaults

## Development

### Adding New Features

1. **Backend**: Add new endpoints in `app/api/routers/`
2. **Frontend**: 
   - Add new pages in `frontend/src/pages/`
   - Add API calls in `frontend/src/services/api.ts`
   - Update navigation in `frontend/src/components/Layout.tsx`

### Environment Variables

Backend (.env):
```
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_ROLE_KEY=your_service_role_key
FIRECRAWL_API_KEY=your_firecrawl_key
```

Frontend (.env):
```
REACT_APP_API_URL=http://localhost:8000/api
```

## Future Enhancements

1. **Real-time Updates**: WebSocket integration for live job progress
2. **Advanced Analytics**: More detailed charts and reports
3. **Bulk Operations**: Bulk product updates and exports
4. **Scheduling**: Automated scraping schedules
5. **Notifications**: Email/webhook alerts for price changes
6. **User Management**: Multi-user support with roles
7. **API Rate Limiting**: Per-user API rate limits
8. **Data Export**: CSV/Excel export functionality

## Screenshots

(Add screenshots of the UI here)

## License

This project is proprietary and confidential.