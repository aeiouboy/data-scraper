# RIS Data Scrap

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18%2B-61dafb.svg)](https://reactjs.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

A comprehensive web scraping and price comparison system for Thai home improvement retailers.

## 🚀 Features

- **Multi-Retailer Scraping**: Automated data collection from major Thai retailers
- **Smart Product Matching**: AI-powered cross-retailer product matching with confidence scoring
- **Price Tracking**: Historical price tracking and analysis
- **Real-time Monitoring**: Category and product availability monitoring
- **RESTful API**: FastAPI-based backend with comprehensive endpoints
- **Modern UI**: React-based dashboard for data visualization and management

## 📋 Table of Contents

- [Architecture](#architecture)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Project Organization](#project-organization)
- [Testing](#testing)
- [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)

## 🏗 Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React UI      │────▶│   FastAPI       │────▶│   PostgreSQL    │
│   (Frontend)    │     │   (Backend)     │     │   (Supabase)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │  Firecrawl API  │
                        │  (Scraping)     │
                        └─────────────────┘
```

## 📂 Project Organization

This project follows a professional enterprise-grade organization structure:

```
ris-data-scrap/
├── src/                     # Application source code
│   ├── api/                 # FastAPI application & routers
│   ├── core/                # Core business logic
│   ├── models/              # Data models
│   ├── scrapers/            # Web scraping engines
│   ├── services/            # Business services
│   └── utils/               # Utility functions
├── data/                    # Data lifecycle management
│   ├── active/              # Current operational data
│   │   ├── analysis/        # Data quality & performance analysis
│   │   ├── scraping/        # Scraping results & validation
│   │   └── testing/         # Test data & results
│   ├── archive/             # Historical data & backups
│   └── config/              # Data management configurations
├── docs/                    # Comprehensive documentation
│   ├── api/                 # API documentation & guides
│   ├── architecture/        # System architecture docs
│   ├── development/         # Developer guides
│   ├── features/            # Feature specifications
│   └── project_management/  # Project management docs
├── scripts/                 # Automation & utility scripts
│   ├── scraping/            # Data collection scripts
│   ├── monitoring/          # System monitoring scripts
│   └── utilities/           # Maintenance scripts
├── tools/                   # Development & operations tools
│   ├── data_quality/        # Data validation tools
│   ├── fixes/               # Issue resolution tools
│   └── validation/          # Quality assurance tools
├── tests/                   # Comprehensive test suite
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── e2e/                 # End-to-end tests
└── frontend/                # React application
    ├── src/                 # Frontend source code
    └── tests/               # Frontend tests
```

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/yourusername/ris-data-scrap.git
cd ris-data-scrap

# Run setup
make setup

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run everything
make run-all
```

Visit:
- Frontend: http://localhost:3000
- API Docs: http://localhost:8001/docs

## 📦 Installation

### Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL (or Supabase account)
- Firecrawl API key

### Backend Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up database
python scripts/database/create_schema.py
```

### Frontend Setup

```bash
cd frontend
npm install
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Application
ENVIRONMENT=development
APP_NAME="RIS Data Scrap"

# Database
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key

# API Keys
FIRECRAWL_API_KEY=your-firecrawl-key

# Server
HOST=0.0.0.0
PORT=8001
```

### Retailer Configuration

Supported retailers are configured in `app/config/retailers.py`:
- HomePro (HP)
- Thai Watsadu (TWD)
- Global House (GH)
- DoHome (DH)
- Boonthavorn (BT)
- MegaHome (MH)

## 🔧 Usage

### Running the API Server

```bash
# Development mode with auto-reload
make run-api

# Or directly
python run_api.py
```

### Running the Frontend

```bash
# Development server
make run-frontend

# Or directly
cd frontend && npm start
```

### Scraping Products

```bash
# Scrape all retailers
make scrape-all

# Scrape specific retailer
python scrape.py --retailer HP --category "power-tools" --limit 100

# Run with monitoring
python scrape_multi_retailer.py --retailers HP TWD --monitor
```

### Product Matching

```bash
# Run matching algorithm
make run-matching

# Or directly
python improve_matching_algorithm.py
```

## 📚 API Documentation

### Key Endpoints

#### Products
- `GET /api/products` - List products with filtering
- `GET /api/products/{id}` - Get product details
- `POST /api/products/search` - Advanced search

#### Price Comparisons
- `GET /api/price-comparisons-v2/detailed-comparisons` - Get price comparisons
- `GET /api/price-comparisons-v2/categories-with-savings` - Categories with savings

#### Scraping
- `POST /api/scraping/jobs` - Create scraping job
- `GET /api/scraping/jobs/{id}` - Get job status

Full API documentation available at http://localhost:8001/docs

## 🛠 Development

### Code Style

```bash
# Format code
make format

# Run linters
make lint
```

### Project Structure

```
ris-data-scrap/
├── app/               # Backend application
│   ├── api/          # API endpoints
│   ├── core/         # Core functionality
│   ├── models/       # Data models
│   ├── scrapers/     # Retailer scrapers
│   └── services/     # Business logic
├── frontend/          # React frontend
├── tests/            # Test suites
├── scripts/          # Utility scripts
├── logs/             # Application logs
└── docs/             # Documentation
```

## 🧪 Testing

```bash
# Run all tests
make test

# Run specific test types
make test-unit
make test-integration
make test-e2e

# With coverage
pytest --cov=app tests/
```

## 🚀 Deployment

### Docker Deployment

```bash
# Build containers
docker-compose build

# Run services
docker-compose up -d

# View logs
docker-compose logs -f
```

### Production Deployment

1. Set environment to production in `.env`
2. Configure proper database credentials
3. Set up reverse proxy (nginx)
4. Enable HTTPS
5. Configure monitoring

See [Deployment Guide](docs/deployment/DEPLOYMENT.md) for detailed instructions.

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) for the amazing web framework
- [React](https://reactjs.org/) for the UI library
- [Supabase](https://supabase.io/) for the database platform
- [Firecrawl](https://firecrawl.com/) for web scraping infrastructure

## 📞 Support

- Documentation: [docs/](docs/)
- Issues: [GitHub Issues](https://github.com/yourusername/ris-data-scrap/issues)
- Email: support@example.com

---

Made with ❤️ for the Thai retail community