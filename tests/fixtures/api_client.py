"""API client fixtures for testing."""

import pytest
from fastapi.testclient import TestClient
from src.api.main import app
from src.api.auth import create_access_token
import os


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def authenticated_client(client):
    """Create an authenticated test client."""
    # Create a test token
    access_token = create_access_token(data={"sub": "test_user"})
    client.headers = {"Authorization": f"Bearer {access_token}"}
    return client


@pytest.fixture
def api_headers():
    """Common API headers for testing."""
    return {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


@pytest.fixture
def mock_firecrawl_api_key(monkeypatch):
    """Mock Firecrawl API key."""
    monkeypatch.setenv("FIRECRAWL_API_KEY", "test_firecrawl_key")
    

@pytest.fixture
def mock_supabase_credentials(monkeypatch):
    """Mock Supabase credentials."""
    monkeypatch.setenv("SUPABASE_URL", "https://test.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "test_anon_key")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "test_service_key")


@pytest.fixture
def mock_environment(mock_firecrawl_api_key, mock_supabase_credentials):
    """Set up all mock environment variables."""
    pass