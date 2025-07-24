"""
Browser session manager with User-Agent rotation and session persistence
"""
import asyncio
import logging
from typing import Dict, List, Optional, Any
import aiohttp
import random
from datetime import datetime, timedelta
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class BrowserSessionManager:
    """Manages browser sessions with realistic User-Agent rotation and session persistence"""
    
    # Real User-Agent strings for different browsers and platforms
    USER_AGENTS = [
        # Chrome Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        
        # Chrome Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        
        # Firefox Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:119.0) Gecko/20100101 Firefox/119.0",
        
        # Firefox Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:119.0) Gecko/20100101 Firefox/119.0",
        
        # Safari Mac
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        
        # Edge Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0",
        
        # Mobile User-Agents (for mobile-optimized pages)
        "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Mobile/15E148 Safari/604.1",
        "Mozilla/5.0 (Linux; Android 10; SM-G975F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36",
    ]
    
    # Common Accept headers for different content types
    ACCEPT_HEADERS = {
        'html': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'json': 'application/json, text/plain, */*',
        'any': '*/*'
    }
    
    # Common Accept-Language headers
    ACCEPT_LANGUAGES = [
        'en-US,en;q=0.9',
        'en-GB,en;q=0.9',
        'th-TH,th;q=0.9,en;q=0.8',
        'en-US,en;q=0.9,th;q=0.8'
    ]
    
    def __init__(self, session_timeout: int = 3600, rotation_interval: int = 300):
        """
        Initialize browser session manager
        
        Args:
            session_timeout: Session timeout in seconds
            rotation_interval: User-Agent rotation interval in seconds
        """
        self.session_timeout = session_timeout
        self.rotation_interval = rotation_interval
        
        # Session management
        self._session: Optional[aiohttp.ClientSession] = None
        self._session_created_at: Optional[datetime] = None
        self._current_user_agent: Optional[str] = None
        self._user_agent_set_at: Optional[datetime] = None
        
        # Session persistence
        self._cookies: Dict[str, Any] = {}
        self._session_data: Dict[str, Any] = {}
        
        # Statistics
        self.stats = {
            'sessions_created': 0,
            'user_agents_rotated': 0,
            'requests_made': 0,
            'last_rotation': None
        }
    
    async def get_session(self) -> aiohttp.ClientSession:
        """Get current session or create new one if needed"""
        now = datetime.now()
        
        # Check if we need to create a new session
        if self._session is None or self._session_expired(now):
            await self._create_new_session()
        
        # Check if we need to rotate User-Agent
        if self._should_rotate_user_agent(now):
            await self._rotate_user_agent()
        
        self.stats['requests_made'] += 1
        return self._session
    
    def get_headers(self, content_type: str = 'html') -> Dict[str, str]:
        """Get realistic browser headers"""
        headers = {
            'User-Agent': self._current_user_agent or random.choice(self.USER_AGENTS),
            'Accept': self.ACCEPT_HEADERS.get(content_type, self.ACCEPT_HEADERS['html']),
            'Accept-Language': random.choice(self.ACCEPT_LANGUAGES),
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1'
        }
        
        # Add referer for subsequent requests
        if self._session_data.get('last_url'):
            headers['Referer'] = self._session_data['last_url']
        
        return headers
    
    def update_last_url(self, url: str):
        """Update the last visited URL for referer header"""
        self._session_data['last_url'] = url
    
    async def _create_new_session(self):
        """Create a new aiohttp session"""
        # Close existing session if any
        if self._session and not self._session.closed:
            await self._session.close()
        
        # Create connector with reasonable settings
        connector = aiohttp.TCPConnector(
            limit=100,  # Total connection limit
            limit_per_host=10,  # Per-host connection limit
            ttl_dns_cache=300,  # DNS cache TTL
            use_dns_cache=True,
            enable_cleanup_closed=True,
            keepalive_timeout=30,
            ssl=False  # Disable SSL verification for problematic sites
        )
        
        # Create timeout settings
        timeout = aiohttp.ClientTimeout(
            total=30,  # Total timeout
            connect=10,  # Connection timeout
            sock_read=20  # Socket read timeout
        )
        
        # Create session
        self._session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            cookie_jar=aiohttp.CookieJar(unsafe=True),  # Allow cookies for all domains
            headers=self.get_headers(),
            trust_env=True
        )
        
        # Restore cookies if available
        if self._cookies:
            for name, value in self._cookies.items():
                self._session.cookie_jar.update_cookies({name: value})
        
        self._session_created_at = datetime.now()
        self._current_user_agent = random.choice(self.USER_AGENTS)
        self._user_agent_set_at = datetime.now()
        
        self.stats['sessions_created'] += 1
        logger.info(f"Created new browser session with User-Agent: {self._current_user_agent}")
    
    def _session_expired(self, now: datetime) -> bool:
        """Check if current session has expired"""
        if self._session_created_at is None:
            return True
        
        return (now - self._session_created_at).total_seconds() > self.session_timeout
    
    def _should_rotate_user_agent(self, now: datetime) -> bool:
        """Check if User-Agent should be rotated"""
        if self._user_agent_set_at is None:
            return True
        
        return (now - self._user_agent_set_at).total_seconds() > self.rotation_interval
    
    async def _rotate_user_agent(self):
        """Rotate User-Agent while keeping session alive"""
        old_user_agent = self._current_user_agent
        
        # Select new User-Agent (ensure it's different from current)
        available_agents = [ua for ua in self.USER_AGENTS if ua != old_user_agent]
        self._current_user_agent = random.choice(available_agents)
        self._user_agent_set_at = datetime.now()
        
        # Update session headers
        if self._session:
            self._session.headers.update({'User-Agent': self._current_user_agent})
        
        self.stats['user_agents_rotated'] += 1
        self.stats['last_rotation'] = datetime.now().isoformat()
        
        logger.info(f"Rotated User-Agent: {old_user_agent[:50]}... -> {self._current_user_agent[:50]}...")
    
    def get_random_user_agent(self) -> str:
        """Get a random User-Agent without affecting the current session"""
        return random.choice(self.USER_AGENTS)
    
    def get_mobile_user_agent(self) -> str:
        """Get a mobile User-Agent for mobile-optimized pages"""
        mobile_agents = [ua for ua in self.USER_AGENTS if 'Mobile' in ua or 'iPhone' in ua]
        return random.choice(mobile_agents) if mobile_agents else random.choice(self.USER_AGENTS)
    
    def get_desktop_user_agent(self) -> str:
        """Get a desktop User-Agent"""
        desktop_agents = [ua for ua in self.USER_AGENTS if 'Mobile' not in ua and 'iPhone' not in ua]
        return random.choice(desktop_agents) if desktop_agents else random.choice(self.USER_AGENTS)
    
    async def save_session_data(self, file_path: str):
        """Save session data to file for persistence"""
        try:
            session_data = {
                'cookies': self._cookies,
                'session_data': self._session_data,
                'current_user_agent': self._current_user_agent,
                'stats': self.stats,
                'saved_at': datetime.now().isoformat()
            }
            
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Session data saved to {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to save session data: {str(e)}")
    
    async def load_session_data(self, file_path: str):
        """Load session data from file"""
        try:
            if not Path(file_path).exists():
                return
            
            with open(file_path, 'r', encoding='utf-8') as f:
                session_data = json.load(f)
            
            # Check if data is not too old (max 24 hours)
            saved_at = datetime.fromisoformat(session_data.get('saved_at', ''))
            if (datetime.now() - saved_at).total_seconds() > 86400:  # 24 hours
                logger.info("Session data too old, starting fresh")
                return
            
            self._cookies = session_data.get('cookies', {})
            self._session_data = session_data.get('session_data', {})
            self._current_user_agent = session_data.get('current_user_agent')
            self.stats.update(session_data.get('stats', {}))
            
            logger.info(f"Session data loaded from {file_path}")
            
        except Exception as e:
            logger.error(f"Failed to load session data: {str(e)}")
    
    def add_custom_headers(self, headers: Dict[str, str]):
        """Add custom headers to the session"""
        if self._session:
            self._session.headers.update(headers)
    
    def set_proxy(self, proxy: str):
        """Set proxy for the session (requires session recreation)"""
        self._session_data['proxy'] = proxy
        # Force session recreation on next request
        self._session_created_at = None
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get information about the current session"""
        return {
            'current_user_agent': self._current_user_agent,
            'session_created_at': self._session_created_at.isoformat() if self._session_created_at else None,
            'user_agent_set_at': self._user_agent_set_at.isoformat() if self._user_agent_set_at else None,
            'session_active': self._session is not None and not self._session.closed,
            'cookies_count': len(self._cookies),
            'stats': self.stats
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        return self.stats.copy()
    
    async def close(self):
        """Close the session and clean up resources"""
        if self._session and not self._session.closed:
            # Save cookies before closing
            if self._session.cookie_jar:
                self._cookies = {cookie.key: cookie.value for cookie in self._session.cookie_jar}
            
            await self._session.close()
            self._session = None
            
            logger.info("Browser session closed")
    
    def __del__(self):
        """Cleanup on object deletion"""
        if self._session and not self._session.closed:
            # Schedule cleanup in the event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self._session.close())
            except RuntimeError:
                # Event loop not running, can't schedule cleanup
                pass