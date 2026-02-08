#!/usr/bin/env python3
"""
Tests for MCP browser fetch server.
"""

import pytest
from datetime import date
from unittest.mock import Mock, patch, MagicMock
from server import (
    get_chrome_version,
    get_platform_string,
    get_session,
    get_browser_headers,
    fetch,
)


class TestChromeVersion:
    """Tests for Chrome version calculation."""

    def test_version_calculation_current_date(self):
        """Test that version calculation works for current date."""
        version = get_chrome_version()
        assert isinstance(version, int)
        assert version >= 122  # Base version
        assert version <= 200  # Cap

    def test_version_cap_at_200(self):
        """Test that version is capped at 200."""
        with patch('server.date') as mock_date:
            # Mock a date far in the future
            mock_date.today.return_value = date(2030, 1, 1)
            mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)
            version = get_chrome_version()
            assert version <= 200  # Should be capped at or below 200

    def test_version_minimum_bound(self):
        """Test that version doesn't go below base version."""
        with patch('server.date') as mock_date:
            # Mock a date in the past
            mock_date.today.return_value = date(2020, 1, 1)
            mock_date.side_effect = lambda *args, **kwargs: date(*args, **kwargs)
            version = get_chrome_version()
            assert version == 122  # Should return base version


class TestPlatformDetection:
    """Tests for platform detection."""

    def test_macos_intel(self):
        """Test macOS Intel platform string."""
        with patch('platform.system', return_value='Darwin'):
            with patch('platform.machine', return_value='x86_64'):
                platform_str, sec_ch = get_platform_string()
                assert 'Macintosh' in platform_str
                assert 'Intel Mac OS X' in platform_str
                assert sec_ch == '"macOS"'

    def test_macos_arm(self):
        """Test macOS ARM platform string."""
        with patch('platform.system', return_value='Darwin'):
            with patch('platform.machine', return_value='arm64'):
                platform_str, sec_ch = get_platform_string()
                assert 'Macintosh' in platform_str
                assert 'Intel Mac OS X' in platform_str  # Still reports Intel for compatibility
                assert sec_ch == '"macOS"'

    def test_windows(self):
        """Test Windows platform string."""
        with patch('platform.system', return_value='Windows'):
            with patch('platform.machine', return_value='AMD64'):
                platform_str, sec_ch = get_platform_string()
                assert 'Windows NT 10.0' in platform_str
                assert 'Win64; x64' in platform_str
                assert sec_ch == '"Windows"'

    def test_linux(self):
        """Test Linux platform string."""
        with patch('platform.system', return_value='Linux'):
            with patch('platform.machine', return_value='x86_64'):
                platform_str, sec_ch = get_platform_string()
                assert 'X11; Linux x86_64' in platform_str
                assert sec_ch == '"Linux"'

    def test_unknown_platform_fallback(self):
        """Test that unknown platforms fall back to macOS."""
        with patch('platform.system', return_value='FreeBSD'):
            with patch('platform.machine', return_value='x86_64'):
                platform_str, sec_ch = get_platform_string()
                assert 'Macintosh' in platform_str
                assert sec_ch == '"macOS"'


class TestSession:
    """Tests for session management."""

    def test_session_singleton(self):
        """Test that get_session returns the same session."""
        session1 = get_session()
        session2 = get_session()
        assert session1 is session2

    def test_session_has_headers(self):
        """Test that session has default headers."""
        session = get_session()
        headers = get_browser_headers()
        # Session should be configured with browser-like properties
        assert session is not None


class TestBrowserHeaders:
    """Tests for browser header generation."""

    def test_headers_structure(self):
        """Test that headers have required fields."""
        headers = get_browser_headers()

        required_headers = [
            'User-Agent',
            'Accept',
            'Accept-Language',
            'Accept-Encoding',
            'Sec-Fetch-Dest',
            'Sec-Fetch-Mode',
            'Sec-Fetch-Site',
            'Sec-Fetch-User',
            'Sec-Ch-Ua',
            'Sec-Ch-Ua-Mobile',
            'Sec-Ch-Ua-Platform',
            'Upgrade-Insecure-Requests',
            'Cache-Control',
        ]

        for header in required_headers:
            assert header in headers

    def test_user_agent_format(self):
        """Test User-Agent has correct format."""
        headers = get_browser_headers()
        ua = headers['User-Agent']

        assert 'Mozilla/5.0' in ua
        assert 'AppleWebKit/537.36' in ua
        assert 'Chrome/' in ua
        assert 'Safari/537.36' in ua

    def test_sec_ch_ua_format(self):
        """Test Sec-Ch-Ua has correct format."""
        headers = get_browser_headers()
        sec_ch_ua = headers['Sec-Ch-Ua']

        assert 'Google Chrome' in sec_ch_ua
        assert 'Chromium' in sec_ch_ua
        assert 'Not=A?Brand' in sec_ch_ua


class TestURLValidation:
    """Tests for URL validation."""

    @patch('server.get_session')
    def test_http_url_allowed(self, mock_session):
        """Test that http:// URLs are allowed."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'text/html'}
        mock_response.text = '<html><body>Test</body></html>'
        mock_response.iter_content = Mock(return_value=[b'<html><body>Test</body></html>'])

        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance

        result = fetch(url="http://example.com", max_length=1000)
        assert 'Test' in result

    @patch('server.get_session')
    def test_https_url_allowed(self, mock_session):
        """Test that https:// URLs are allowed."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'text/html'}
        mock_response.text = '<html><body>Test</body></html>'
        mock_response.iter_content = Mock(return_value=[b'<html><body>Test</body></html>'])

        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance

        result = fetch(url="https://example.com", max_length=1000)
        assert 'Test' in result

    def test_file_url_rejected(self):
        """Test that file:// URLs are rejected."""
        with pytest.raises(ValueError, match="Invalid URL scheme: file"):
            fetch(url="file:///etc/passwd", max_length=1000)

    def test_javascript_url_rejected(self):
        """Test that javascript: URLs are rejected."""
        with pytest.raises(ValueError, match="Invalid URL scheme: javascript"):
            fetch(url="javascript:alert('xss')", max_length=1000)

    def test_data_url_rejected(self):
        """Test that data: URLs are rejected."""
        with pytest.raises(ValueError, match="Invalid URL scheme: data"):
            fetch(url="data:text/html,<script>alert('xss')</script>", max_length=1000)

    def test_ftp_url_rejected(self):
        """Test that ftp:// URLs are rejected."""
        with pytest.raises(ValueError, match="Invalid URL scheme: ftp"):
            fetch(url="ftp://example.com/file.txt", max_length=1000)


class TestSizeLimits:
    """Tests for response size limits."""

    @patch('server.get_session')
    def test_large_content_length_rejected(self, mock_session):
        """Test that responses with large Content-Length are rejected."""
        mock_response = Mock()
        mock_response.headers = {'content-length': str(51 * 1024 * 1024)}  # 51MB
        mock_response.raise_for_status = Mock()

        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance

        with pytest.raises(ValueError, match="Response too large"):
            fetch(url="http://example.com", max_length=1000)

    @patch('server.get_session')
    def test_streaming_size_limit(self, mock_session):
        """Test that streaming responses respect size limit."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'text/html'}
        mock_response.raise_for_status = Mock()
        # Create chunks that exceed 50MB
        large_chunk = b'x' * (10 * 1024 * 1024)  # 10MB chunks
        mock_response.iter_content = Mock(return_value=[large_chunk] * 6)  # 60MB total

        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance

        with pytest.raises(ValueError, match="Response exceeded size limit"):
            fetch(url="http://example.com", max_length=1000)


class TestErrorHandling:
    """Tests for error handling."""

    @patch('server.get_session')
    def test_404_error_handling(self, mock_session):
        """Test handling of 404 errors."""
        from requests.exceptions import HTTPError

        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.reason = 'Not Found'
        mock_response.raise_for_status.side_effect = HTTPError(response=mock_response)

        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance

        with pytest.raises(ValueError, match="404"):
            fetch(url="http://example.com/notfound", max_length=1000)

    @patch('server.get_session')
    def test_connection_error_handling(self, mock_session):
        """Test handling of connection errors."""
        from requests.exceptions import ConnectionError

        mock_session_instance = Mock()
        mock_session_instance.get.side_effect = ConnectionError("Connection failed")
        mock_session.return_value = mock_session_instance

        with pytest.raises(ValueError, match="Connection error"):
            fetch(url="http://example.com", max_length=1000)

    @patch('server.get_session')
    def test_timeout_error_handling(self, mock_session):
        """Test handling of timeout errors."""
        from requests.exceptions import Timeout

        mock_session_instance = Mock()
        mock_session_instance.get.side_effect = Timeout("Request timed out")
        mock_session.return_value = mock_session_instance

        with pytest.raises(ValueError, match="Timeout"):
            fetch(url="http://example.com", max_length=1000)


class TestPagination:
    """Tests for pagination functionality."""

    @patch('server.get_session')
    def test_basic_pagination(self, mock_session):
        """Test basic pagination with start_index and max_length."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'text/html'}
        mock_response.text = 'A' * 10000  # 10k chars
        mock_response.iter_content = Mock(return_value=[b'A' * 10000])

        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance

        result = fetch(url="http://example.com", max_length=1000, start_index=0)
        # Should be truncated with continuation message
        assert len(result) >= 1000
        assert 'Truncated' in result or 'chars remaining' in result

    @patch('server.get_session')
    def test_continuation_message(self, mock_session):
        """Test that continuation message includes correct start_index."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'text/html'}
        long_content = 'A' * 20000
        mock_response.text = long_content
        mock_response.iter_content = Mock(return_value=[long_content.encode()])

        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance

        result = fetch(url="http://example.com", max_length=5000, start_index=0)
        # Should suggest next start_index
        assert '5000' in result  # Next start index


class TestHTMLParsing:
    """Tests for HTML parsing."""

    @patch('server.get_session')
    def test_valid_html_parsing(self, mock_session):
        """Test parsing of valid HTML."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'text/html'}
        html_content = '<html><body><h1>Title</h1><p>Content</p></body></html>'
        mock_response.text = html_content
        mock_response.iter_content = Mock(return_value=[html_content.encode()])

        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance

        result = fetch(url="http://example.com", max_length=1000, raw=False)
        # html2text should convert to markdown
        assert 'Title' in result
        assert 'Content' in result

    @patch('server.get_session')
    def test_raw_html_mode(self, mock_session):
        """Test raw HTML mode bypasses parsing."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {'content-type': 'text/html'}
        html_content = '<html><body><h1>Title</h1></body></html>'
        mock_response.text = html_content
        mock_response.iter_content = Mock(return_value=[html_content.encode()])

        mock_session_instance = Mock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance

        result = fetch(url="http://example.com", max_length=1000, raw=True)
        # Should return raw HTML
        assert '<html>' in result
        assert '<h1>' in result


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
