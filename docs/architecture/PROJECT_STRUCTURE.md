# Project Structure

This document outlines the recommended project structure following Python and web development best practices.

## Current Structure Analysis

The project has grown organically and needs reorganization for better maintainability, scalability, and clarity.

## Recommended Project Structure

```
ris-data-scrap/
├── .github/                    # GitHub specific files
│   ├── workflows/             # CI/CD workflows
│   └── ISSUE_TEMPLATE/        # Issue templates
│
├── docs/                      # All documentation
│   ├── api/                   # API documentation
│   ├── architecture/          # Architecture diagrams and docs
│   ├── deployment/            # Deployment guides
│   ├── development/           # Developer guides
│   └── user/                  # User documentation
│
├── src/                       # Source code
│   ├── api/                   # API layer
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI application
│   │   ├── dependencies.py    # Dependency injection
│   │   ├── middleware/        # API middleware
│   │   ├── routers/          # API endpoints
│   │   └── schemas/          # Pydantic models
│   │
│   ├── core/                  # Core business logic
│   │   ├── __init__.py
│   │   ├── config.py         # Configuration management
│   │   ├── constants.py      # Application constants
│   │   ├── exceptions.py     # Custom exceptions
│   │   └── logging.py        # Logging configuration
│   │
│   ├── models/               # Data models
│   │   ├── __init__.py
│   │   ├── database/         # SQLAlchemy models
│   │   ├── domain/           # Domain models
│   │   └── dto/              # Data transfer objects
│   │
│   ├── services/             # Business services
│   │   ├── __init__.py
│   │   ├── matching/         # Product matching service
│   │   ├── scraping/         # Scraping service
│   │   ├── analysis/         # Price analysis service
│   │   └── monitoring/       # Category monitoring
│   │
│   ├── scrapers/             # Retailer-specific scrapers
│   │   ├── __init__.py
│   │   ├── base.py           # Base scraper class
│   │   ├── homepro.py
│   │   ├── thaiwatsadu.py
│   │   └── ...
│   │
│   ├── database/             # Database layer
│   │   ├── __init__.py
│   │   ├── connection.py     # Database connection
│   │   ├── repositories/     # Repository pattern
│   │   └── migrations/       # Database migrations
│   │
│   └── utils/                # Utility functions
│       ├── __init__.py
│       ├── text.py           # Text processing
│       ├── validation.py     # Data validation
│       └── http.py           # HTTP utilities
│
├── tests/                    # All tests
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   ├── e2e/                 # End-to-end tests
│   └── fixtures/            # Test fixtures
│
├── scripts/                  # Utility scripts
│   ├── setup/               # Setup scripts
│   ├── migration/           # Data migration scripts
│   └── maintenance/         # Maintenance scripts
│
├── frontend/                 # React frontend
│   ├── public/
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── pages/          # Page components
│   │   ├── services/       # API services
│   │   ├── hooks/          # Custom React hooks
│   │   ├── contexts/       # React contexts
│   │   ├── utils/          # Frontend utilities
│   │   └── types/          # TypeScript types
│   └── ...
│
├── infrastructure/           # Infrastructure as Code
│   ├── docker/              # Docker configurations
│   ├── kubernetes/          # K8s manifests
│   └── terraform/           # Terraform configs
│
├── logs/                    # Application logs
├── data/                    # Data files (git-ignored)
├── .env.example             # Environment variables example
├── requirements.txt         # Python dependencies
├── requirements-dev.txt     # Development dependencies
├── pyproject.toml          # Python project configuration
├── setup.py                # Package setup
├── Makefile                # Common commands
└── README.md               # Project documentation
```

## Migration Plan

### Phase 1: Documentation Consolidation (Immediate)
1. Move all `*.md` files to appropriate `docs/` subdirectories
2. Create index files for each documentation category
3. Update all internal links

### Phase 2: Source Code Reorganization (Week 1)
1. Create `src/` directory structure
2. Move `app/` contents to appropriate `src/` subdirectories
3. Update all imports using proper package structure
4. Ensure all `__init__.py` files are in place

### Phase 3: Test Structure (Week 2)
1. Organize tests by type (unit, integration, e2e)
2. Create proper test fixtures
3. Add test documentation

### Phase 4: Configuration Management (Week 3)
1. Centralize all configuration in `src/core/config.py`
2. Use environment variables properly
3. Create configuration validation

### Phase 5: Scripts and Tools (Week 4)
1. Organize all scripts into categorized directories
2. Create Makefile for common operations
3. Document all scripts

## Benefits of This Structure

1. **Clear Separation of Concerns**: Each directory has a specific purpose
2. **Scalability**: Easy to add new features without cluttering
3. **Testability**: Clear test organization by type
4. **Maintainability**: Easier to find and modify code
5. **Onboarding**: New developers can understand the project quickly
6. **CI/CD Ready**: Structure supports automated testing and deployment

## Best Practices Implemented

1. **Package Structure**: Proper Python package with `__init__.py` files
2. **Configuration**: Centralized configuration management
3. **Logging**: Dedicated logs directory with rotation
4. **Testing**: Comprehensive test structure
5. **Documentation**: Organized documentation by audience
6. **Version Control**: Proper `.gitignore` patterns
7. **Dependencies**: Separated production and development requirements
8. **Type Safety**: TypeScript for frontend, type hints for Python

## Next Steps

1. Create migration scripts to automate the restructuring
2. Update all import statements
3. Update documentation references
4. Test all functionality after migration
5. Update CI/CD pipelines