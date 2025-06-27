"""
FastAPI application for HomePro Product Manager
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
from contextlib import asynccontextmanager

from app.api.routers import products, scraping, analytics, config
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("Starting HomePro Product Manager API")
    
    # Initialize services
    app.state.supabase = SupabaseService()
    
    yield
    
    # Shutdown
    logger.info("Shutting down HomePro Product Manager API")


# Create FastAPI app
app = FastAPI(
    title="HomePro Product Manager API",
    description="API for managing HomePro product scraping and search",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # React dev servers
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(products.router, prefix="/api/products", tags=["products"])
app.include_router(scraping.router, prefix="/api/scraping", tags=["scraping"])
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(config.router, prefix="/api/config", tags=["config"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "HomePro Product Manager API",
        "version": "1.0.0",
        "endpoints": {
            "products": "/api/products",
            "scraping": "/api/scraping",
            "analytics": "/api/analytics",
            "config": "/api/config",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )