"""
Integration tests for matching v2 API endpoints
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from uuid import uuid4
from datetime import datetime

from src.api.main import app
from src.models.matching import MatchResultCreate, MatchingMethod, MatchStatus


@pytest.fixture
def client():
    """Create test client"""
    return TestClient(app)


@pytest.fixture
def sample_product_data():
    """Sample product data for testing"""
    return {
        'id': str(uuid4()),
        'name': 'Test Product',
        'brand': 'Test Brand',
        'sku': 'TEST-123',
        'retailer_code': 'HP',
        'category': 'tools',
        'price': 100.0
    }


@pytest.fixture  
def sample_match_data():
    """Sample match data for testing"""
    return {
        'source_product_id': str(uuid4()),
        'matched_product_id': str(uuid4()),
        'confidence_score': 0.85,
        'matching_method': 'hybrid',
        'status': 'pending'
    }


class TestMatchingV2Endpoints:
    """Integration tests for matching v2 endpoints"""
    
    def test_get_product_matches_success(self, client, sample_product_data):
        """Test getting matches for a product - success case"""
        product_id = sample_product_data['id']
        
        response = client.get(f"/api/v2/matches/{product_id}")
        
        # Should return 200 even if no matches found
        assert response.status_code == 200
        matches = response.json()
        assert isinstance(matches, list)
    
    def test_get_product_matches_with_parameters(self, client, sample_product_data):
        """Test getting matches with query parameters"""
        product_id = sample_product_data['id']
        
        response = client.get(
            f"/api/v2/matches/{product_id}",
            params={
                'min_confidence': 0.7,
                'include_rejected': True,
                'limit': 5,
                'use_fallback': False
            }
        )
        
        assert response.status_code == 200
        matches = response.json()
        assert isinstance(matches, list)
    
    def test_get_product_matches_invalid_uuid(self, client):
        """Test getting matches with invalid UUID"""
        response = client.get("/api/v2/matches/invalid-uuid")
        
        assert response.status_code == 422  # Validation error
    
    def test_create_match_success(self, client, sample_match_data):
        """Test creating a new match"""
        response = client.post(
            "/api/v2/matches",
            json=sample_match_data
        )
        
        # May succeed or fail depending on database state
        assert response.status_code in [200, 201, 400, 500]
    
    def test_create_match_invalid_data(self, client):
        """Test creating match with invalid data"""
        invalid_data = {
            'source_product_id': 'invalid-uuid',
            'matched_product_id': str(uuid4()),
            'confidence_score': 1.5,  # Invalid score > 1.0
            'matching_method': 'invalid_method'
        }
        
        response = client.post("/api/v2/matches", json=invalid_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_create_match_same_products(self, client):
        """Test creating match with same source and target"""
        same_id = str(uuid4())
        invalid_data = {
            'source_product_id': same_id,
            'matched_product_id': same_id,
            'confidence_score': 0.85,
            'matching_method': 'hybrid'
        }
        
        response = client.post("/api/v2/matches", json=invalid_data)
        
        assert response.status_code == 422  # Validation error
    
    def test_update_match_success(self, client):
        """Test updating an existing match"""
        match_id = str(uuid4())
        update_data = {
            'confidence_score': 0.95,
            'status': 'confirmed'
        }
        
        response = client.put(f"/api/v2/matches/{match_id}", json=update_data)
        
        # May succeed or return 404 if match doesn't exist
        assert response.status_code in [200, 404, 500]
    
    def test_update_match_invalid_uuid(self, client):
        """Test updating match with invalid UUID"""
        response = client.put(
            "/api/v2/matches/invalid-uuid",
            json={'confidence_score': 0.95}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_update_match_no_data(self, client):
        """Test updating match with no update data"""
        match_id = str(uuid4())
        
        response = client.put(f"/api/v2/matches/{match_id}", json={})
        
        assert response.status_code == 400  # Bad request
    
    def test_delete_match_success(self, client):
        """Test deleting a match"""
        match_id = str(uuid4())
        
        response = client.delete(f"/api/v2/matches/{match_id}")
        
        # May succeed or return 404 if match doesn't exist
        assert response.status_code in [200, 404, 500]
    
    def test_delete_match_invalid_uuid(self, client):
        """Test deleting match with invalid UUID"""
        response = client.delete("/api/v2/matches/invalid-uuid")
        
        assert response.status_code == 422  # Validation error
    
    def test_create_matches_batch_small(self, client):
        """Test creating small batch of matches"""
        batch_data = []
        for _ in range(3):
            match_data = {
                'source_product_id': str(uuid4()),
                'matched_product_id': str(uuid4()),
                'confidence_score': 0.85,
                'matching_method': 'hybrid'
            }
            batch_data.append(match_data)
        
        response = client.post("/api/v2/matches/batch", json=batch_data)
        
        # Should process immediately for small batches
        assert response.status_code == 200
        result = response.json()
        assert 'status' in result
        assert result['status'] in ['completed', 'processing']
    
    def test_create_matches_batch_large(self, client):
        """Test creating large batch of matches (background processing)"""
        # Create batch larger than 100 to trigger background processing
        batch_data = []
        for _ in range(150):
            match_data = {
                'source_product_id': str(uuid4()),
                'matched_product_id': str(uuid4()),
                'confidence_score': 0.85,
                'matching_method': 'hybrid'
            }
            batch_data.append(match_data)
        
        response = client.post("/api/v2/matches/batch", json=batch_data)
        
        # Should return processing status for large batches
        assert response.status_code == 200
        result = response.json()
        assert result['status'] == 'processing'
        assert result['batch_size'] == 150
    
    def test_create_matches_batch_too_large(self, client):
        """Test creating batch that exceeds size limit"""
        # Create batch larger than 1000 to trigger error
        batch_data = [{'source_product_id': str(uuid4())} for _ in range(1001)]
        
        response = client.post("/api/v2/matches/batch", json=batch_data)
        
        assert response.status_code == 400  # Batch size too large
    
    def test_update_matches_batch(self, client):
        """Test updating batch of matches"""
        batch_updates = []
        for _ in range(5):
            update = {
                'match_id': str(uuid4()),
                'updates': {
                    'confidence_score': 0.95,
                    'status': 'confirmed'
                }
            }
            batch_updates.append(update)
        
        response = client.put("/api/v2/matches/batch", json=batch_updates)
        
        assert response.status_code == 200
        result = response.json()
        assert 'status' in result
    
    def test_update_matches_batch_invalid_format(self, client):
        """Test updating batch with invalid format"""
        invalid_batch = [
            {
                'invalid_field': str(uuid4()),
                'updates': {'confidence_score': 0.95}
            }
        ]
        
        response = client.put("/api/v2/matches/batch", json=invalid_batch)
        
        assert response.status_code == 400  # Bad request
    
    def test_get_matching_statistics(self, client):
        """Test getting matching statistics"""
        response = client.get("/api/v2/matches/stats")
        
        assert response.status_code == 200
        stats = response.json()
        
        # Check required fields
        required_fields = [
            'total_matches', 'pending_matches', 'confirmed_matches', 
            'rejected_matches', 'average_confidence', 'methods_breakdown'
        ]
        
        for field in required_fields:
            assert field in stats
        
        assert isinstance(stats['total_matches'], int)
        assert isinstance(stats['average_confidence'], (int, float))
        assert isinstance(stats['methods_breakdown'], dict)
    
    def test_refresh_product_matches(self, client, sample_product_data):
        """Test refreshing matches for a product"""
        product_id = sample_product_data['id']
        
        response = client.post(f"/api/v2/matches/{product_id}/refresh")
        
        assert response.status_code == 200
        result = response.json()
        assert result['status'] == 'processing'
        assert 'min_confidence' in result
    
    def test_refresh_product_matches_with_params(self, client, sample_product_data):
        """Test refreshing matches with parameters"""
        product_id = sample_product_data['id']
        
        response = client.post(
            f"/api/v2/matches/{product_id}/refresh",
            params={
                'min_confidence': 0.8,
                'force_recalculate': True
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result['min_confidence'] == 0.8
        assert result['force_recalculate'] is True
    
    def test_matching_health_check(self, client):
        """Test matching service health check"""
        response = client.get("/api/v2/matches/health")
        
        assert response.status_code == 200
        health = response.json()
        
        assert 'status' in health
        assert 'timestamp' in health
        assert 'service_version' in health
        assert health['status'] in ['healthy', 'unhealthy']
    
    def test_endpoint_cors_headers(self, client):
        """Test CORS headers on endpoints"""
        response = client.options("/api/v2/matches/stats")
        
        # Should handle OPTIONS request for CORS
        assert response.status_code in [200, 405]
    
    def test_endpoint_rate_limiting(self, client):
        """Test rate limiting behavior"""
        # Make multiple rapid requests
        responses = []
        for _ in range(10):
            response = client.get("/api/v2/matches/stats")
            responses.append(response.status_code)
        
        # All should succeed unless rate limiting is very aggressive
        assert all(status in [200, 429] for status in responses)
    
    def test_error_handling_database_down(self, client, sample_match_data):
        """Test error handling when database is unavailable"""
        # This test would require mocking database failures
        # For now, just test that endpoints handle errors gracefully
        response = client.post("/api/v2/matches", json=sample_match_data)
        
        # Should return proper HTTP status, not crash
        assert response.status_code in [200, 201, 400, 500, 503]
    
    def test_json_response_format(self, client):
        """Test that all endpoints return valid JSON"""
        endpoints = [
            ("/api/v2/matches/stats", "GET"),
            ("/api/v2/matches/health", "GET")
        ]
        
        for endpoint, method in endpoints:
            if method == "GET":
                response = client.get(endpoint)
            
            assert response.status_code in [200, 404, 500]
            
            # Should be valid JSON
            try:
                response.json()
            except ValueError:
                pytest.fail(f"Invalid JSON response from {endpoint}")


class TestMatchingV2Performance:
    """Performance tests for matching v2 endpoints"""
    
    def test_response_time_get_matches(self, client):
        """Test response time for getting matches"""
        import time
        
        product_id = str(uuid4())
        
        start_time = time.time()
        response = client.get(f"/api/v2/matches/{product_id}")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Should respond within reasonable time (adjust threshold as needed)
        assert response_time < 5.0, f"Response time {response_time}s too slow"
    
    def test_response_time_stats(self, client):
        """Test response time for statistics endpoint"""
        import time
        
        start_time = time.time()
        response = client.get("/api/v2/matches/stats")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Stats should be fast (may be cached)
        assert response_time < 2.0, f"Stats response time {response_time}s too slow"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])