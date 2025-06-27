# HomePro Product Manager UI

A modern web interface for managing HomePro product scraping, search, and analytics.

## Features

### 1. **Dashboard**
- Real-time overview of product statistics
- Daily scraping activity monitoring
- Top brands and categories
- Price distribution analysis

### 2. **Product Management**
- Advanced search with filters:
  - Full-text search
  - Brand and category filters
  - Price range slider
  - On-sale and in-stock filters
- Sortable data grid with pagination
- One-click product rescraping
- Export functionality (CSV)

### 3. **Scraping Management**
- Create and monitor scraping jobs
- Support for different job types:
  - Category scraping
  - Batch product scraping
  - Search result scraping
- Real-time job progress tracking
- Job cancellation and history

### 4. **Analytics**
- Price trend analysis
- Scraping performance metrics
- Category distribution charts
- Export reports

### 5. **Settings**
- Configure scraping parameters
- Manage rate limits
- Environment information
- Reset to defaults option

## Setup Instructions

### Prerequisites
- Node.js 16+ and npm
- Running backend API (port 8000)

### Installation

1. **Navigate to frontend directory**
   ```bash
   cd frontend
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Start development server**
   ```bash
   npm start
   ```

   The UI will open at http://localhost:3000

### Environment Configuration

Create a `.env` file in the frontend directory:

```env
REACT_APP_API_URL=http://localhost:8000/api
```

## Usage Guide

### Starting a Scraping Job

1. Navigate to **Scraping** page
2. Click **New Scraping Job**
3. Select job type:
   - **Category**: Scrape all products from a category URL
   - **Product**: Scrape specific product URLs
   - **Search**: Scrape search results
4. Enter target URL or product URLs
5. Set max pages (for category/search)
6. Click **Create Job**

### Searching Products

1. Go to **Products** page
2. Enter search query or use filters:
   - Select brands/categories
   - Adjust price range
   - Toggle on-sale/in-stock filters
3. Click **Search**
4. Sort by clicking column headers
5. Rescrape individual products with refresh icon

### Monitoring Performance

1. Check **Dashboard** for overview
2. View **Analytics** for detailed metrics
3. Monitor active jobs in **Scraping** page

## Architecture

### Technology Stack
- **React 18** with TypeScript
- **Material-UI** for components
- **React Query** for data fetching
- **React Router** for navigation
- **Axios** for API calls
- **Chart.js** for visualizations

### Project Structure
```
frontend/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   └── Layout.tsx
│   ├── pages/
│   │   ├── Dashboard.tsx
│   │   ├── Products.tsx
│   │   ├── Scraping.tsx
│   │   ├── Analytics.tsx
│   │   └── Settings.tsx
│   ├── services/
│   │   └── api.ts
│   ├── App.tsx
│   ├── index.tsx
│   └── index.css
├── package.json
└── tsconfig.json
```

### API Integration

The UI communicates with the backend through these endpoints:

- `/api/products` - Product search and management
- `/api/scraping` - Job creation and monitoring
- `/api/analytics` - Dashboard and metrics
- `/api/config` - Settings management

## Development

### Building for Production
```bash
npm run build
```

### Running Tests
```bash
npm test
```

### Code Style
- Use TypeScript for type safety
- Follow React best practices
- Use Material-UI theme consistently
- Handle loading and error states

## Deployment

### Docker
```dockerfile
FROM node:16-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
EXPOSE 80
```

### Environment Variables
- `REACT_APP_API_URL` - Backend API URL
- `REACT_APP_ENV` - Environment (development/production)

## Troubleshooting

### Common Issues

1. **API Connection Failed**
   - Ensure backend is running on port 8000
   - Check CORS settings in backend
   - Verify API URL in .env file

2. **Blank Page**
   - Check browser console for errors
   - Ensure all dependencies are installed
   - Clear browser cache

3. **Search Not Working**
   - Check if products exist in database
   - Verify Supabase connection
   - Check browser network tab for API errors

## Future Enhancements

- [ ] WebSocket for real-time updates
- [ ] Advanced analytics charts
- [ ] Bulk operations
- [ ] User authentication
- [ ] Dark mode theme
- [ ] Mobile responsive improvements
- [ ] Export to Excel
- [ ] Scheduled scraping

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review API logs
3. Open an issue on GitHub