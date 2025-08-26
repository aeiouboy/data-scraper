"""
Unit tests for DatabaseMatcher service
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from uuid import UUID, uuid4
from datetime import datetime

from src.services.matching.database_matcher import DatabaseMatcher
from src.models.matching import (
    MatchResultCreate, MatchResultResponse, MatchingMethod, 
    MatchStatus, MatchMetadataCreate
)


@pytest.fixture
def db_matcher():
    """Create DatabaseMatcher instance for testing"""
    with patch('src.services.matching.database_matcher.SupabaseService'):
        return DatabaseMatcher()


@pytest.fixture
def sample_match_data():
    """Sample match data for testing"""
    return {
        'source_product_id': uuid4(),
        'matched_product_id': uuid4(),
        'confidence_score': 0.85,
        'matching_method': MatchingMethod.HYBRID,
        'status': MatchStatus.PENDING
    }


@pytest.fixture
def sample_match_response():
    """Sample match response for testing"""
    return {
        'id': str(uuid4()),
        'source_product_id': str(uuid4()),
        'matched_product_id': str(uuid4()),
        'confidence_score': 0.85,
        'matching_method': 'hybrid',
        'status': 'pending',
        'created_at': '2025-08-25T10:00:00Z',
        'updated_at': '2025-08-25T10:00:00Z'
    }


class TestDatabaseMatcher:
    """Test cases for DatabaseMatcher"""
    
    @pytest.mark.asyncio
    async def test_find_matches_success(self, db_matcher, sample_match_response):
        """Test successful match finding"""
        # Mock the database query
        mock_result = Mock()
        mock_result.data = [sample_match_response]
        
        db_matcher.db_service.client.table.return_value.select.return_value\
            .order.return_value.limit.return_value.eq.return_value\
            .neq.return_value.gte.return_value.execute.return_value = mock_result
        
        product_id = UUID(sample_match_response['source_product_id'])
        matches = await db_matcher.find_matches(product_id)
        
        assert len(matches) == 1
        assert matches[0].confidence_score == 0.85
        assert matches[0].matching_method == MatchingMethod.HYBRID
    
    @pytest.mark.asyncio
    async def test_find_matches_empty_result(self, db_matcher):
        """Test finding matches with no results"""
        # Mock empty result
        mock_result = Mock()
        mock_result.data = []
        
        db_matcher.db_service.client.table.return_value.select.return_value\
            .order.return_value.limit.return_value.eq.return_value\
            .neq.return_value.gte.return_value.execute.return_value = mock_result
        
        product_id = uuid4()
        matches = await db_matcher.find_matches(product_id)
        
        assert matches == []
    
    @pytest.mark.asyncio
    async def test_create_match_success(self, db_matcher, sample_match_data):
        """Test successful match creation"""
        # Mock successful creation
        mock_result = Mock()
        mock_result.data = [{
            'id': str(uuid4()),
            **sample_match_data,
            'source_product_id': str(sample_match_data['source_product_id']),
            'matched_product_id': str(sample_match_data['matched_product_id']),
            'created_at': '2025-08-25T10:00:00Z',
            'updated_at': '2025-08-25T10:00:00Z'
        }]
        
        db_matcher.db_service.client.table.return_value.insert.return_value\
            .execute.return_value = mock_result
        
        # Mock the _check_existing_match method
        db_matcher._check_existing_match = AsyncMock(return_value=None)
        
        # Mock the _get_match_with_details method
        db_matcher._get_match_with_details = AsyncMock(
            return_value=MatchResultResponse(
                id=UUID(mock_result.data[0]['id']),
                **sample_match_data,
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        )
        
        match_create = MatchResultCreate(**sample_match_data)
        result = await db_matcher.create_match(match_create)
        
        assert result is not None
        assert result.confidence_score == 0.85
    
    @pytest.mark.asyncio
    async def test_create_match_already_exists(self, db_matcher, sample_match_data):
        """Test creating match that already exists"""
        # Mock existing match
        existing_match = MatchResultResponse(
            id=uuid4(),
            **sample_match_data,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        db_matcher._check_existing_match = AsyncMock(return_value=existing_match)
        
        match_create = MatchResultCreate(**sample_match_data)
        result = await db_matcher.create_match(match_create)
        
        assert result == existing_match
    
    @pytest.mark.asyncio
    async def test_update_match_success(self, db_matcher):
        """Test successful match update"""
        match_id = uuid4()
        update_data = {'confidence_score': 0.95, 'status': 'confirmed'}
        
        # Mock successful update
        mock_result = Mock()
        mock_result.data = [{'id': str(match_id), **update_data}]
        
        db_matcher.db_service.client.table.return_value.update.return_value\
            .eq.return_value.execute.return_value = mock_result
        
        # Mock the _get_match_with_details method
        updated_match = MatchResultResponse(
            id=match_id,
            source_product_id=uuid4(),
            matched_product_id=uuid4(),
            confidence_score=0.95,
            matching_method=MatchingMethod.HYBRID,
            status=MatchStatus.CONFIRMED,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db_matcher._get_match_with_details = AsyncMock(return_value=updated_match)
        
        result = await db_matcher.update_match(match_id, update_data)
        
        assert result is not None
        assert result.confidence_score == 0.95
    
    @pytest.mark.asyncio
    async def test_update_match_not_found(self, db_matcher):
        """Test updating non-existent match"""
        match_id = uuid4()
        update_data = {'confidence_score': 0.95}
        
        # Mock empty result
        mock_result = Mock()
        mock_result.data = []
        
        db_matcher.db_service.client.table.return_value.update.return_value\
            .eq.return_value.execute.return_value = mock_result
        
        result = await db_matcher.update_match(match_id, update_data)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_match_success(self, db_matcher):
        """Test successful match deletion"""
        match_id = uuid4()
        
        # Mock successful deletion
        mock_result = Mock()
        mock_result.data = [{'id': str(match_id)}]
        
        db_matcher.db_service.client.table.return_value.delete.return_value\
            .eq.return_value.execute.return_value = mock_result
        
        result = await db_matcher.delete_match(match_id)
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_delete_match_not_found(self, db_matcher):
        """Test deleting non-existent match"""
        match_id = uuid4()
        
        # Mock empty result
        mock_result = Mock()
        mock_result.data = []
        
        db_matcher.db_service.client.table.return_value.delete.return_value\
            .eq.return_value.execute.return_value = mock_result
        
        result = await db_matcher.delete_match(match_id)
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_get_match_stats(self, db_matcher):
        """Test getting match statistics"""
        # Mock various RPC calls
        db_matcher.db_service.client.table.return_value.select.return_value\
            .execute.return_value = Mock(count=100)
        
        db_matcher.db_service.client.rpc.return_value.execute.return_value = Mock(
            data=[{'status': 'pending', 'count': 50}]
        )
        
        stats = await db_matcher.get_match_stats()
        
        assert stats.total_matches == 100
    
    @pytest.mark.asyncio
    async def test_error_handling(self, db_matcher):
        """Test error handling in database operations"""
        # Mock database exception
        db_matcher.db_service.client.table.side_effect = Exception("Database error")
        
        product_id = uuid4()
        matches = await db_matcher.find_matches(product_id)
        
        # Should return empty list on error
        assert matches == []
    
    def test_confidence_score_validation(self, sample_match_data):
        """Test confidence score validation"""
        # Test valid score
        match_data = sample_match_data.copy()
        match_data['confidence_score'] = 0.85
        match = MatchResultCreate(**match_data)
        assert match.confidence_score == 0.85
        
        # Test score rounding
        match_data['confidence_score'] = 0.858
        match = MatchResultCreate(**match_data)
        assert match.confidence_score == 0.86
        
        # Test invalid scores
        with pytest.raises(ValueError):
            match_data['confidence_score'] = 1.5
            MatchResultCreate(**match_data)
        
        with pytest.raises(ValueError):
            match_data['confidence_score'] = -0.1
            MatchResultCreate(**match_data)
    
    def test_same_product_validation(self):
        """Test validation that source and matched products are different"""
        same_id = uuid4()
        
        with pytest.raises(ValueError):
            MatchResultCreate(
                source_product_id=same_id,
                matched_product_id=same_id,
                confidence_score=0.85,
                matching_method=MatchingMethod.HYBRID
            )


@pytest.mark.asyncio
async def test_match_result_serialization():
    """Test MatchResult serialization"""
    match_data = {
        'id': uuid4(),
        'source_product_id': uuid4(),
        'matched_product_id': uuid4(),
        'confidence_score': 0.85,
        'matching_method': MatchingMethod.HYBRID,
        'status': MatchStatus.PENDING,
        'created_at': datetime.now(),
        'updated_at': datetime.now()
    }
    
    match = MatchResultResponse(**match_data)
    
    # Test JSON serialization
    json_data = match.dict()
    assert json_data['confidence_score'] == 0.85
    assert json_data['matching_method'] == 'hybrid'
    assert json_data['status'] == 'pending'


if __name__ == "__main__":
    pytest.main([__file__])