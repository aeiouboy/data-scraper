# RIS Data Scrap Makefile
# Common commands for development and deployment

.PHONY: help install install-dev setup test lint format run-api run-frontend run-all clean docs logs

# Default target
help:
	@echo "RIS Data Scrap - Available commands:"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make install      - Install production dependencies"
	@echo "  make install-dev  - Install development dependencies"
	@echo "  make setup        - Complete project setup"
	@echo ""
	@echo "Development:"
	@echo "  make run-api      - Run API server (port 8001)"
	@echo "  make run-frontend - Run frontend dev server (port 3000)"
	@echo "  make run-all      - Run both API and frontend"
	@echo "  make test         - Run all tests"
	@echo "  make lint         - Run linting checks"
	@echo "  make format       - Format code"
	@echo ""
	@echo "Database:"
	@echo "  make db-migrate   - Run database migrations"
	@echo "  make db-seed      - Seed database with sample data"
	@echo ""
	@echo "Scraping:"
	@echo "  make scrape-all   - Run all scrapers"
	@echo "  make monitor      - Run category monitoring"
	@echo ""
	@echo "Utilities:"
	@echo "  make logs         - Tail API logs"
	@echo "  make clean        - Clean temporary files"
	@echo "  make docs         - Generate documentation"

# Variables
PYTHON := python3
PIP := pip3
NPM := npm
VENV := venv
API_PORT := 8001
FRONTEND_PORT := 3000

# Setup & Installation
install:
	$(PIP) install -r requirements.txt

install-dev: install
	$(PIP) install -r requirements-dev.txt
	cd frontend && $(NPM) install

setup: install-dev
	@echo "Setting up environment..."
	cp .env.example .env
	@echo "Please edit .env with your configuration"
	mkdir -p logs data
	@echo "Setup complete!"

# Development
run-api:
	@echo "Starting API server on port $(API_PORT)..."
	$(PYTHON) run_api.py

run-frontend:
	@echo "Starting frontend dev server on port $(FRONTEND_PORT)..."
	cd frontend && $(NPM) start

run-all:
	@echo "Starting all services..."
	@make -j 2 run-api run-frontend

# Testing
test:
	@echo "Running tests..."
	pytest tests/ -v --cov=app --cov-report=html

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

test-e2e:
	pytest tests/e2e/ -v

# Code Quality
lint:
	@echo "Running linters..."
	# Python linting
	flake8 app/ tests/
	mypy app/
	# Frontend linting
	cd frontend && $(NPM) run lint

format:
	@echo "Formatting code..."
	# Python formatting
	black app/ tests/ scripts/
	isort app/ tests/ scripts/
	# Frontend formatting
	cd frontend && $(NPM) run format

# Database
db-migrate:
	@echo "Running database migrations..."
	$(PYTHON) scripts/migration/run_migrations.py

db-seed:
	@echo "Seeding database..."
	$(PYTHON) scripts/setup/seed_database.py

# Scraping
scrape-all:
	@echo "Running all scrapers..."
	$(PYTHON) scripts/scraping/scrape_multi_retailer.py --all

scrape-hp:
	$(PYTHON) scripts/scraping/scrape.py --retailer HP --limit 100

scrape-twd:
	$(PYTHON) scripts/scraping/scrape.py --retailer TWD --limit 100

monitor:
	@echo "Running category monitoring..."
	$(PYTHON) scripts/monitoring/run_monitoring_direct.py

# Matching
run-matching:
	@echo "Running product matching..."
	$(PYTHON) scripts/matching/improve_matching_algorithm.py

# Utilities
logs:
	@echo "Tailing API logs..."
	tail -f logs/api.log

logs-scraper:
	tail -f logs/scrapers.log

clean:
	@echo "Cleaning temporary files..."
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	find . -type f -name '.DS_Store' -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	cd frontend && rm -rf node_modules/.cache

docs:
	@echo "Generating documentation..."
	$(PYTHON) scripts/reorganize_docs.py
	@echo "Documentation generated in docs/"

# Docker
docker-build:
	docker-compose build

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

# Deployment
deploy-staging:
	@echo "Deploying to staging..."
	# Add your staging deployment commands here

deploy-production:
	@echo "Deploying to production..."
	@echo "WARNING: This will deploy to production. Are you sure? [y/N]"
	@read ans && [ $${ans:-N} = y ]
	# Add your production deployment commands here

# Development shortcuts
.PHONY: api frontend worker

api: run-api
frontend: run-frontend
worker:
	celery -A app.workers worker --loglevel=info

# Quick commands
.PHONY: mm match price

mm: run-matching
match: run-matching
price:
	$(PYTHON) scripts/analysis/check_price_comparison_categories.py