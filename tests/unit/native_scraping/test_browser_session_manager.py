"""
Unit tests for browser session manager
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from scrapers.engines.browser_session_manager import BrowserSessionManager


@pytest.mark.unit
@pytest.mark.native
class TestBrowserSessionManager:
    """Test cases for browser session manager functionality"""
    
    def test_initialization(self):
        """Test session manager initialization"""
        manager = BrowserSessionManager()
        
        assert manager.session_pool_size == 5
        assert manager.session_timeout == 30
        assert manager.user_agent_pool_size == 15
        assert manager.retry_attempts == 3
        assert manager.retry_delay == 1
    
    def test_initialization_with_custom_params(self):
        """Test initialization with custom parameters"""
        manager = BrowserSessionManager(
            session_pool_size=10,
            session_timeout=60,
            user_agent_pool_size=20,
            retry_attempts=5,
            retry_delay=2
        )
        
        assert manager.session_pool_size == 10
        assert manager.session_timeout == 60
        assert manager.user_agent_pool_size == 20
        assert manager.retry_attempts == 5
        assert manager.retry_delay == 2
    
    def test_get_random_user_agent(self):
        """Test random user agent generation"""
        manager = BrowserSessionManager()
        
        # Test that user agents are generated
        ua1 = manager.get_random_user_agent()
        ua2 = manager.get_random_user_agent()
        
        assert ua1 is not None
        assert ua2 is not None
        assert isinstance(ua1, str)
        assert isinstance(ua2, str)
        assert len(ua1) > 0
        assert len(ua2) > 0
        
        # Test variety (run multiple times to increase chance of different UAs)
        user_agents = set()
        for _ in range(50):
            user_agents.add(manager.get_random_user_agent())
        
        # Should have at least 2 different user agents
        assert len(user_agents) >= 2
    
    def test_get_headers(self):
        """Test header generation"""
        manager = BrowserSessionManager()
        
        headers = manager.get_headers()
        
        # Check required headers
        assert 'User-Agent' in headers
        assert 'Accept' in headers
        assert 'Accept-Language' in headers
        assert 'Accept-Encoding' in headers
        assert 'Connection' in headers
        assert 'Upgrade-Insecure-Requests' in headers
        
        # Check header values
        assert headers['Accept-Language'] == 'en-US,en;q=0.9,th;q=0.8'
        assert headers['Accept-Encoding'] == 'gzip, deflate, br'
        assert headers['Connection'] == 'keep-alive'
        assert headers['Upgrade-Insecure-Requests'] == '1'
    
    def test_get_headers_with_custom_referer(self):
        """Test header generation with custom referer"""
        manager = BrowserSessionManager()
        
        referer = "https://example.com"
        headers = manager.get_headers(referer=referer)
        
        assert headers['Referer'] == referer
    
    def test_get_headers_with_custom_user_agent(self):
        """Test header generation with custom user agent"""
        manager = BrowserSessionManager()
        
        custom_ua = "Custom User Agent 1.0"
        headers = manager.get_headers(user_agent=custom_ua)
        
        assert headers['User-Agent'] == custom_ua
    
    def test_get_headers_randomization(self):
        """Test that headers are properly randomized"""
        manager = BrowserSessionManager()
        
        # Generate multiple headers
        headers_list = []
        for _ in range(10):
            headers_list.append(manager.get_headers())
        
        # Check that User-Agent varies
        user_agents = set(h['User-Agent'] for h in headers_list)
        assert len(user_agents) > 1  # Should have variety
    
    @pytest.mark.asyncio
    async def test_get_session_creation(self):
        """Test session creation"""
        manager = BrowserSessionManager()
        
        # Mock aiohttp.ClientSession
        with patch('aiohttp.ClientSession') as mock_session:
            mock_instance = Mock()
            mock_session.return_value = mock_instance
            
            session = await manager.get_session()
            
            assert session is not None
            mock_session.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_session_reuse(self):
        """Test session reuse from pool"""
        manager = BrowserSessionManager()
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_instance = Mock()
            mock_session.return_value = mock_instance
            
            # Get first session
            session1 = await manager.get_session()
            
            # Return it to pool
            await manager.return_session(session1)
            
            # Get second session (should be reused)
            session2 = await manager.get_session()
            
            # Should be the same session
            assert session1 is session2
    
    @pytest.mark.asyncio
    async def test_session_pool_limit(self):
        """Test session pool size limit"""
        manager = BrowserSessionManager(session_pool_size=2)
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_instances = [Mock() for _ in range(5)]
            mock_session.side_effect = mock_instances
            
            # Get sessions up to pool limit
            sessions = []
            for _ in range(5):
                session = await manager.get_session()
                sessions.append(session)
            
            # Should only create pool_size + active sessions
            assert len(manager._session_pool) + len(sessions) <= manager.session_pool_size + 3
    
    @pytest.mark.asyncio
    async def test_return_session(self):
        """Test returning session to pool"""
        manager = BrowserSessionManager()
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_instance = Mock()
            mock_instance.closed = False
            mock_session.return_value = mock_instance
            
            session = await manager.get_session()
            initial_pool_size = len(manager._session_pool)
            
            await manager.return_session(session)
            
            # Pool should have one more session
            assert len(manager._session_pool) == initial_pool_size + 1
    
    @pytest.mark.asyncio
    async def test_return_closed_session(self):
        """Test returning closed session (should not be added to pool)"""
        manager = BrowserSessionManager()
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_instance = Mock()
            mock_instance.closed = True
            mock_session.return_value = mock_instance
            
            session = await manager.get_session()
            initial_pool_size = len(manager._session_pool)
            
            await manager.return_session(session)
            
            # Pool should not change
            assert len(manager._session_pool) == initial_pool_size
    
    @pytest.mark.asyncio
    async def test_close_all_sessions(self):
        """Test closing all sessions"""
        manager = BrowserSessionManager()
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_instances = [Mock() for _ in range(3)]
            for mock in mock_instances:
                mock.close = AsyncMock()
                mock.closed = False
            mock_session.side_effect = mock_instances
            
            # Create some sessions
            sessions = []
            for _ in range(3):
                session = await manager.get_session()
                sessions.append(session)
            
            # Return them to pool
            for session in sessions:
                await manager.return_session(session)
            
            # Close all
            await manager.close()
            
            # All sessions should be closed
            for mock in mock_instances:
                mock.close.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_session_timeout_cleanup(self):
        """Test session timeout cleanup"""
        manager = BrowserSessionManager(session_timeout=0.1)
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_instance = Mock()
            mock_instance.closed = False
            mock_instance.close = AsyncMock()
            mock_session.return_value = mock_instance
            
            session = await manager.get_session()
            await manager.return_session(session)
            
            # Wait for timeout
            await asyncio.sleep(0.2)
            
            # Trigger cleanup
            await manager._cleanup_expired_sessions()
            
            # Session should be closed
            mock_instance.close.assert_called_once()
    
    def test_add_session_headers(self):
        """Test adding session-specific headers"""
        manager = BrowserSessionManager()
        
        base_headers = {'User-Agent': 'Test Agent'}
        session_headers = manager._add_session_headers(base_headers)
        
        # Should include original headers
        assert session_headers['User-Agent'] == 'Test Agent'
        
        # Should add additional headers
        assert 'DNT' in session_headers
        assert 'Cache-Control' in session_headers
        assert 'Pragma' in session_headers
    
    def test_get_session_cookies(self):
        """Test session cookie generation"""
        manager = BrowserSessionManager()
        
        cookies = manager.get_session_cookies()
        
        # Should return dict
        assert isinstance(cookies, dict)
        
        # Should have some common cookies
        assert len(cookies) > 0
    
    def test_get_session_info(self):
        """Test getting session information"""
        manager = BrowserSessionManager()
        
        info = manager.get_session_info()
        
        # Check required fields
        assert 'session_pool_size' in info
        assert 'active_sessions' in info
        assert 'user_agent_pool_size' in info
        assert 'session_timeout' in info
        assert 'retry_attempts' in info
        assert 'retry_delay' in info
    
    @pytest.mark.asyncio
    async def test_session_with_proxy(self):
        """Test session creation with proxy"""
        manager = BrowserSessionManager()
        
        proxy = "http://proxy.example.com:8080"
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_instance = Mock()
            mock_session.return_value = mock_instance
            
            session = await manager.get_session(proxy=proxy)
            
            # Should pass proxy to session
            assert session is not None
            mock_session.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_session_error_handling(self):
        """Test session error handling"""
        manager = BrowserSessionManager()
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_session.side_effect = Exception("Connection failed")
            
            # Should handle exception gracefully
            session = await manager.get_session()
            assert session is None
    
    def test_user_agent_variety(self):
        """Test user agent variety"""
        manager = BrowserSessionManager()
        
        # Test that we have reasonable variety
        user_agents = set()
        for _ in range(100):
            user_agents.add(manager.get_random_user_agent())
        
        # Should have good variety
        assert len(user_agents) >= 5
        
        # Check that user agents look realistic
        for ua in list(user_agents)[:5]:
            assert 'Mozilla' in ua
            assert any(browser in ua for browser in ['Chrome', 'Firefox', 'Safari', 'Edge'])
    
    def test_session_statistics(self):
        """Test session statistics tracking"""
        manager = BrowserSessionManager()
        
        # Initially should be zero
        stats = manager.get_session_stats()
        assert stats['sessions_created'] == 0
        assert stats['sessions_reused'] == 0
        assert stats['sessions_closed'] == 0
    
    @pytest.mark.asyncio
    async def test_session_health_check(self):
        """Test session health check"""
        manager = BrowserSessionManager()
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_instance = Mock()
            mock_instance.closed = False
            mock_session.return_value = mock_instance
            
            session = await manager.get_session()
            
            # Test healthy session
            is_healthy = manager._is_session_healthy(session)
            assert is_healthy is True
            
            # Test unhealthy session
            mock_instance.closed = True
            is_healthy = manager._is_session_healthy(session)
            assert is_healthy is False
    
    def test_repr(self):
        """Test string representation"""
        manager = BrowserSessionManager()
        
        # Should not raise exception
        str_repr = repr(manager)
        assert 'BrowserSessionManager' in str_repr
        assert 'pool_size=' in str_repr
        assert 'timeout=' in str_repr
    
    @pytest.mark.asyncio
    async def test_concurrent_session_access(self):
        """Test concurrent session access"""
        manager = BrowserSessionManager(session_pool_size=2)
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_instances = [Mock() for _ in range(5)]
            mock_session.side_effect = mock_instances
            
            # Create concurrent requests
            tasks = []
            for _ in range(5):
                task = asyncio.create_task(manager.get_session())
                tasks.append(task)
            
            # Should complete without error
            sessions = await asyncio.gather(*tasks)
            
            # Should have sessions
            assert len(sessions) == 5
            assert all(s is not None for s in sessions)
    
    @pytest.mark.asyncio
    async def test_session_rotation(self):
        """Test session rotation in pool"""
        manager = BrowserSessionManager(session_pool_size=3)
        
        with patch('aiohttp.ClientSession') as mock_session:
            mock_instances = [Mock() for _ in range(3)]
            for mock in mock_instances:
                mock.closed = False
            mock_session.side_effect = mock_instances
            
            # Fill pool
            sessions = []
            for _ in range(3):
                session = await manager.get_session()
                sessions.append(session)
            
            # Return all to pool
            for session in sessions:
                await manager.return_session(session)
            
            # Get sessions again - should rotate
            new_sessions = []
            for _ in range(3):
                session = await manager.get_session()
                new_sessions.append(session)
            
            # Should be same sessions in different order
            assert set(sessions) == set(new_sessions)