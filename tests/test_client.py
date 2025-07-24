"""Unit tests for the Phaser documentation HTTP client.

This module contains comprehensive tests for the PhaserDocsClient class,
including tests for HTTP requests, error handling, retry logic, and security validation.
"""

from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
from pytest_mock import MockerFixture

from phaser_mcp_server.client import (
    HTTPError,
    NetworkError,
    PhaserDocsClient,
    PhaserDocsError,
    RateLimitError,
    ValidationError,
)
from phaser_mcp_server.models import DocumentationPage


class TestPhaserDocsClient:
    """Test cases for PhaserDocsClient class."""

    @pytest.fixture
    def client(self) -> PhaserDocsClient:
        """Create a test client instance."""
        return PhaserDocsClient(
            base_url="https://docs.phaser.io",
            timeout=10.0,
            max_retries=2,
            retry_delay=0.1,  # Fast retries for testing
        )

    @pytest.fixture
    def mock_httpx_client(self, mocker: MockerFixture) -> Mock:
        """Mock httpx.AsyncClient."""
        mock_client = AsyncMock()
        mocker.patch("httpx.AsyncClient", return_value=mock_client)
        return mock_client

    def test_init_valid_base_url(self) -> None:
        """Test client initialization with valid base URL."""
        client = PhaserDocsClient(base_url="https://docs.phaser.io")
        assert client.base_url == "https://docs.phaser.io"
        assert client.timeout == 30.0
        assert client.max_retries == 3
        assert client.retry_delay == 1.0

    def test_init_invalid_base_url(self) -> None:
        """Test client initialization with invalid base URL."""
        with pytest.raises(ValueError, match="Base URL must be from allowed domains"):
            PhaserDocsClient(base_url="https://malicious.com")

    def test_init_custom_parameters(self) -> None:
        """Test client initialization with custom parameters."""
        client = PhaserDocsClient(
            base_url="https://phaser.io", timeout=15.0, max_retries=5, retry_delay=2.0
        )
        assert client.base_url == "https://phaser.io"
        assert client.timeout == 15.0
        assert client.max_retries == 5
        assert client.retry_delay == 2.0

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_httpx_client: Mock) -> None:
        """Test async context manager functionality."""
        client = PhaserDocsClient()

        async with client:
            assert client._client is not None

        # Client should be closed after context exit
        mock_httpx_client.aclose.assert_called_once()

    def test_is_allowed_url_valid_domains(self) -> None:
        """Test URL validation for allowed domains."""
        client = PhaserDocsClient()

        valid_urls = [
            "https://docs.phaser.io/phaser/",
            "http://docs.phaser.io/api/",
            "https://phaser.io/examples",
            "https://www.phaser.io/news",
        ]

        for url in valid_urls:
            assert client._is_allowed_url(url), f"URL should be allowed: {url}"

    def test_is_allowed_url_invalid_domains(self) -> None:
        """Test URL validation rejects invalid domains."""
        client = PhaserDocsClient()

        invalid_urls = [
            "https://malicious.com/phaser",
            "http://evil.docs.phaser.io/",  # Subdomain attack
            "https://docs.phaser.io.evil.com/",  # Domain spoofing
            "ftp://docs.phaser.io/",  # Wrong scheme
            "javascript:alert('xss')",  # Script injection
        ]

        for url in invalid_urls:
            assert not client._is_allowed_url(url), f"URL should be rejected: {url}"

    def test_is_allowed_url_security_checks(self) -> None:
        """Test URL security validation."""
        client = PhaserDocsClient()

        # Path traversal attempts
        assert not client._is_allowed_url("https://docs.phaser.io/../../../etc/passwd")
        assert not client._is_allowed_url("https://docs.phaser.io/phaser/../admin")

        # Suspicious query parameters
        assert not client._is_allowed_url(
            "https://docs.phaser.io/?redirect=javascript:alert(1)"
        )
        assert not client._is_allowed_url(
            "https://docs.phaser.io/?data=data:text/html,<script>"
        )

        # Suspicious fragments
        assert not client._is_allowed_url("https://docs.phaser.io/#javascript:void(0)")

        # Encoded attack attempts (new security feature)
        assert not client._is_allowed_url("https://docs.phaser.io/%2e%2e/etc/passwd")
        assert not client._is_allowed_url("https://docs.phaser.io/%00")
        assert not client._is_allowed_url("https://docs.phaser.io/%2f%2f")

        # Excessively long URLs (new security feature)
        long_url = "https://docs.phaser.io/" + "a" * 2050
        assert not client._is_allowed_url(long_url)

        # Valid URLs should still pass
        assert client._is_allowed_url("https://docs.phaser.io/phaser/")
        assert client._is_allowed_url("https://docs.phaser.io/api/Phaser.Game")

    def test_sanitize_input(self) -> None:
        """Test input sanitization."""
        client = PhaserDocsClient()

        # Normal input
        assert client._sanitize_input("normal text") == "normal text"

        # Input with control characters
        assert client._sanitize_input("text\x00with\x01nulls") == "textwithnulls"

        # Input with tabs and newlines (should be preserved)
        assert client._sanitize_input("text\twith\ntabs") == "text\twith\ntabs"

        # Empty input
        assert client._sanitize_input("") == ""
        assert client._sanitize_input("   ") == ""

        # Long input (should be truncated)
        long_input = "a" * 3000
        result = client._sanitize_input(long_input)
        assert len(result) == 2048

    def test_validate_url_relative_paths(self) -> None:
        """Test URL validation with relative paths."""
        client = PhaserDocsClient(base_url="https://docs.phaser.io")

        # Absolute path
        result = client._validate_url("/phaser/getting-started")
        assert result == "https://docs.phaser.io/phaser/getting-started"

        # Relative path
        result = client._validate_url("api/sprites")
        assert result == "https://docs.phaser.io/api/sprites"

        # Full URL
        result = client._validate_url("https://docs.phaser.io/phaser/")
        assert result == "https://docs.phaser.io/phaser/"

    def test_validate_url_security_rejection(self) -> None:
        """Test URL validation rejects malicious URLs."""
        client = PhaserDocsClient()

        malicious_urls = [
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "vbscript:msgbox('xss')",
            "file:///etc/passwd",
            "https://malicious.com/phaser",
        ]

        for url in malicious_urls:
            with pytest.raises(ValueError):
                client._validate_url(url)

    def test_validate_search_query(self) -> None:
        """Test search query validation."""
        client = PhaserDocsClient()

        # Valid queries
        assert client._validate_search_query("sprite animation") == "sprite animation"
        assert client._validate_search_query("  phaser game  ") == "phaser game"

        # Empty queries
        with pytest.raises(ValueError, match="Search query cannot be empty"):
            client._validate_search_query("")

        with pytest.raises(
            ValueError, match="Search query is empty after sanitization"
        ):
            client._validate_search_query("   ")

        # Malicious queries
        malicious_queries = [
            "<script>alert('xss')</script>",
            "javascript:alert(1)",
            "eval(malicious_code)",
            "document.cookie",
            "window.location = 'evil.com'",
        ]

        for query in malicious_queries:
            with pytest.raises(ValueError, match="Suspicious pattern detected"):
                client._validate_search_query(query)

    @pytest.mark.asyncio
    async def test_fetch_page_success(
        self, client: PhaserDocsClient, mock_httpx_client: Mock
    ) -> None:
        """Test successful page fetching."""
        # Setup mock response
        mock_response = Mock()
        mock_response.text = "<html><title>Test Page</title><body>Content</body></html>"
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html", "content-length": "50"}
        mock_response.url = "https://docs.phaser.io/phaser/"
        mock_response._content = (
            b"<html><title>Test Page</title><body>Content</body></html>"
        )
        mock_response.raise_for_status = Mock()
        mock_httpx_client.get.return_value = mock_response

        # Test fetch
        result = await client.fetch_page("https://docs.phaser.io/phaser/")

        assert result == "<html><title>Test Page</title><body>Content</body></html>"
        mock_httpx_client.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_page_http_error(
        self, client: PhaserDocsClient, mock_httpx_client: Mock
    ) -> None:
        """Test page fetching with HTTP error."""
        # Setup mock to raise HTTP error
        mock_response = Mock()
        mock_response.status_code = 404
        mock_httpx_client.get.return_value = mock_response
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Not Found", request=Mock(), response=mock_response
        )

        with pytest.raises(HTTPError, match="Page not found"):
            await client.fetch_page("https://docs.phaser.io/nonexistent")

    @pytest.mark.asyncio
    async def test_fetch_page_network_error(
        self, client: PhaserDocsClient, mock_httpx_client: Mock
    ) -> None:
        """Test page fetching with network error."""
        # Setup mock to raise connection error
        mock_httpx_client.get.side_effect = httpx.ConnectError("Connection failed")

        with pytest.raises(NetworkError, match="Connection error"):
            await client.fetch_page("https://docs.phaser.io/phaser/")

    @pytest.mark.asyncio
    async def test_fetch_page_timeout_error(
        self, client: PhaserDocsClient, mock_httpx_client: Mock
    ) -> None:
        """Test page fetching with timeout error."""
        # Setup mock to raise timeout error
        mock_httpx_client.get.side_effect = httpx.TimeoutException("Request timeout")

        with pytest.raises(NetworkError, match="Request timeout"):
            await client.fetch_page("https://docs.phaser.io/phaser/")

    @pytest.mark.asyncio
    async def test_retry_logic_success_after_failure(
        self, client: PhaserDocsClient, mock_httpx_client: Mock
    ) -> None:
        """Test retry logic succeeds after initial failure."""
        # Setup mock to fail once then succeed
        mock_response_fail = Mock()
        mock_response_fail.status_code = 500
        mock_response_fail.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error", request=Mock(), response=mock_response_fail
        )

        mock_response_success = Mock()
        mock_response_success.text = "Success"
        mock_response_success.status_code = 200
        mock_response_success.headers = {
            "content-type": "text/html",
            "content-length": "7",
        }
        mock_response_success.url = "https://docs.phaser.io/phaser/"
        mock_response_success._content = b"Success"
        mock_response_success.raise_for_status = Mock()

        mock_httpx_client.get.side_effect = [mock_response_fail, mock_response_success]

        result = await client.fetch_page("https://docs.phaser.io/phaser/")
        assert result == "Success"
        assert mock_httpx_client.get.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_logic_rate_limit(
        self, client: PhaserDocsClient, mock_httpx_client: Mock
    ) -> None:
        """Test retry logic handles rate limiting."""
        # Setup mock to return 429 (rate limited) for all attempts
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "0.1"}
        mock_httpx_client.get.return_value = mock_response

        with pytest.raises(RateLimitError, match="Rate limited after"):
            await client.fetch_page("https://docs.phaser.io/phaser/")

    @pytest.mark.asyncio
    async def test_get_page_content(
        self, client: PhaserDocsClient, mock_httpx_client: Mock
    ) -> None:
        """Test getting page content as DocumentationPage."""
        # Setup mock response
        html_content = (
            "<html><title>Phaser Sprites</title><body>"
            "<h1>Sprites</h1><p>Content about sprites</p></body></html>"
        )
        mock_response = Mock()
        mock_response.text = html_content
        mock_response.status_code = 200
        mock_response.headers = {
            "content-type": "text/html",
            "content-length": str(len(html_content)),
        }
        mock_response.url = "https://docs.phaser.io/phaser/sprites"
        mock_response._content = html_content.encode("utf-8")
        mock_response.raise_for_status = Mock()
        mock_httpx_client.get.return_value = mock_response

        result = await client.get_page_content("https://docs.phaser.io/phaser/sprites")

        assert isinstance(result, DocumentationPage)
        assert result.url == "https://docs.phaser.io/phaser/sprites"
        assert result.title == "Phaser Sprites"
        assert result.content == html_content
        assert result.content_type == "text/html"

    def test_extract_title(self) -> None:
        """Test HTML title extraction."""
        client = PhaserDocsClient()

        # Normal title
        html = "<html><head><title>Test Title</title></head><body></body></html>"
        assert client._extract_title(html) == "Test Title"

        # Title with extra whitespace
        html = "<html><head><title>  Spaced Title  </title></head><body></body></html>"
        assert client._extract_title(html) == "Spaced Title"

        # No title tag
        html = "<html><head></head><body></body></html>"
        assert client._extract_title(html) == "Phaser Documentation"

        # Malformed HTML
        html = "<html><title>Broken"
        assert client._extract_title(html) == "Phaser Documentation"

    @pytest.mark.asyncio
    async def test_search_content_validation(self, client: PhaserDocsClient) -> None:
        """Test search content validation."""
        # Valid search
        result = await client.search_content("sprite animation", limit=5)
        assert isinstance(result, list)
        assert len(result) == 0  # Empty for now since search is not implemented

        # Invalid query
        with pytest.raises(ValidationError):
            await client.search_content("", limit=5)

        # Invalid limit
        with pytest.raises(ValueError, match="Limit must be a positive integer"):
            await client.search_content("test", limit=0)

        with pytest.raises(ValueError, match="Limit must be a positive integer"):
            await client.search_content("test", limit=-1)

    @pytest.mark.asyncio
    async def test_search_content_limit_capping(self, client: PhaserDocsClient) -> None:
        """Test search content limit capping."""
        # Large limit should be capped
        result = await client.search_content("test", limit=200)
        assert isinstance(result, list)
        # The actual limit capping is logged but doesn't affect the empty result for now

    def test_log_security_event(self, client: PhaserDocsClient) -> None:
        """Test security event logging."""
        with patch("phaser_mcp_server.client.logger") as mock_logger:
            client._log_security_event(
                "TEST_EVENT", "Test details", "https://example.com"
            )
            mock_logger.warning.assert_called_once_with(
                "SECURITY_EVENT: TEST_EVENT - Test details - URL: https://example.com"
            )

            # Test without URL
            mock_logger.reset_mock()
            client._log_security_event("TEST_EVENT", "Test details")
            mock_logger.warning.assert_called_once_with(
                "SECURITY_EVENT: TEST_EVENT - Test details"
            )

    @pytest.mark.asyncio
    async def test_validate_response_security(self, client: PhaserDocsClient) -> None:
        """Test response security validation."""
        # Test valid response
        mock_response = Mock()
        mock_response.headers = {
            "content-type": "text/html; charset=utf-8",
            "content-length": "1000",
        }
        mock_response.url = "https://docs.phaser.io/test"
        mock_response._content = b"a" * 1000

        # Should not raise any exception
        client._validate_response_security(mock_response)

        # Test response too large (content-length)
        mock_response.headers["content-length"] = str(client.MAX_RESPONSE_SIZE + 1)
        with pytest.raises(ValidationError, match="Response too large"):
            client._validate_response_security(mock_response)

        # Test response too large (actual content)
        mock_response.headers["content-length"] = "1000"
        mock_response._content = b"a" * (client.MAX_RESPONSE_SIZE + 1)
        with pytest.raises(ValidationError, match="Response content too large"):
            client._validate_response_security(mock_response)

    @pytest.mark.asyncio
    async def test_fetch_page_with_response_validation(
        self, client: PhaserDocsClient, mock_httpx_client: Mock
    ) -> None:
        """Test page fetching with response security validation."""
        # Setup mock response that passes validation
        mock_response = Mock()
        mock_response.text = "<html><title>Test</title></html>"
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html", "content-length": "100"}
        mock_response.url = "https://docs.phaser.io/test"
        mock_response._content = b"<html><title>Test</title></html>"
        mock_response.raise_for_status = Mock()
        mock_httpx_client.get.return_value = mock_response

        result = await client.fetch_page("https://docs.phaser.io/test")
        assert result == "<html><title>Test</title></html>"

        # Test with response that fails validation
        mock_response.headers["content-length"] = str(client.MAX_RESPONSE_SIZE + 1)
        with pytest.raises(ValidationError, match="Response too large"):
            await client.fetch_page("https://docs.phaser.io/test")

    @pytest.mark.asyncio
    async def test_get_api_reference_success(
        self, client: PhaserDocsClient, mock_httpx_client: Mock
    ) -> None:
        """Test successful API reference retrieval."""
        # Mock HTML content with API information
        mock_html = """
        <html>
            <head><title>Sprite API Reference</title></head>
            <body>
                <h1>Sprite</h1>
                <div class="description">
                    A Sprite Game Object is used to display textures.
                </div>
                <div class="methods">
                    <h3>Methods</h3>
                    <ul>
                        <li>setTexture(key)</li>
                        <li>setPosition(x, y)</li>
                        <li>destroy()</li>
                    </ul>
                </div>
                <div class="properties">
                    <h3>Properties</h3>
                    <ul>
                        <li>x</li>
                        <li>y</li>
                        <li>texture</li>
                    </ul>
                </div>
                <pre><code>
                    const sprite = this.add.sprite(100, 100, 'player');
                </code></pre>
            </body>
        </html>
        """

        # Setup mock response
        mock_response = Mock()
        mock_response.text = mock_html
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "text/html"}
        mock_response.raise_for_status = Mock()
        mock_response.url = "https://docs.phaser.io/api/Sprite"
        # Mock the _content attribute for security validation
        mock_response._content = mock_html.encode("utf-8")
        mock_httpx_client.get.return_value = mock_response

        await client._ensure_client()

        result = await client.get_api_reference("Sprite")

        assert result.class_name == "Sprite"
        assert result.url == "https://docs.phaser.io/api/Sprite"
        assert "Sprite Game Object" in result.description
        assert "setTexture" in result.methods
        assert "setPosition" in result.methods
        assert "destroy" in result.methods
        assert "x" in result.properties
        assert "y" in result.properties
        assert "texture" in result.properties
        assert len(result.examples) > 0
        assert "sprite" in result.examples[0]

    @pytest.mark.asyncio
    async def test_get_api_reference_not_found(
        self, client: PhaserDocsClient, mock_httpx_client: Mock
    ) -> None:
        """Test API reference retrieval when page not found."""
        # Setup mock to return 404 for all URLs
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.url = "https://docs.phaser.io/api/NonExistentClass"
        mock_response.headers = {"content-type": "text/html"}
        mock_response._content = b""

        # Create proper HTTPStatusError with response
        http_error = httpx.HTTPStatusError(
            "Not Found", request=Mock(), response=mock_response
        )
        mock_response.raise_for_status.side_effect = http_error
        mock_httpx_client.get.return_value = mock_response

        await client._ensure_client()

        result = await client.get_api_reference("NonExistentClass")

        # Should return a basic reference when no page is found
        assert result.class_name == "NonExistentClass"
        assert result.url == "https://docs.phaser.io/api/NonExistentClass"
        assert "No specific documentation page found" in result.description
        assert result.methods == []
        assert result.properties == []
        assert result.examples == []

    @pytest.mark.asyncio
    async def test_get_api_reference_empty_class_name(
        self, client: PhaserDocsClient
    ) -> None:
        """Test API reference with empty class name."""
        with pytest.raises(ValidationError, match="Class name is empty"):
            await client.get_api_reference("")

    @pytest.mark.asyncio
    async def test_get_api_reference_multiple_url_attempts(
        self, client: PhaserDocsClient, mock_httpx_client: Mock
    ) -> None:
        """Test API reference tries multiple URL patterns."""
        # Mock to fail on first URL but succeed on second
        mock_html = (
            "<html><body><h1>Phaser.GameObjects.Sprite</h1>"
            "<p>Sprite class</p></body></html>"
        )

        def mock_get_side_effect(url):
            mock_response = Mock()
            if "api/Sprite" in url and "Phaser.GameObjects" not in url:
                # First URL fails
                mock_response.status_code = 404
                mock_response.url = url
                mock_response.headers = {"content-type": "text/html"}
                mock_response._content = b""
                http_error = httpx.HTTPStatusError(
                    "Not Found", request=Mock(), response=mock_response
                )
                mock_response.raise_for_status.side_effect = http_error
            else:
                # Second URL succeeds
                mock_response.text = mock_html
                mock_response.status_code = 200
                mock_response.headers = {"content-type": "text/html"}
                mock_response.url = url
                mock_response._content = mock_html.encode("utf-8")
                mock_response.raise_for_status = Mock()
            return mock_response

        mock_httpx_client.get.side_effect = mock_get_side_effect

        await client._ensure_client()

        result = await client.get_api_reference("Sprite")

        assert result.class_name == "Sprite"
        assert "Phaser.GameObjects.Sprite" in result.url
        assert "Sprite class" in result.description

    def test_extract_api_information_from_html(self) -> None:
        """Test API information extraction from HTML."""
        client = PhaserDocsClient()

        html_content = """
        <html>
            <body>
                <div class="description">Test class description</div>
                <div class="methods">
                    <h3>Methods</h3>
                    <ul>
                        <li>method1(param)</li>
                        <li>method2()</li>
                    </ul>
                </div>
                <div class="properties">
                    <h3>Properties</h3>
                    <ul>
                        <li>prop1</li>
                        <li>prop2</li>
                    </ul>
                </div>
                <pre><code>const example = new TestClass();</code></pre>
                <div class="inheritance">extends BaseClass</div>
            </body>
        </html>
        """

        result = client._extract_api_information_from_html(html_content, "TestClass")

        assert result["description"] == "Test class description"
        assert "method1" in result["methods"]
        assert "method2" in result["methods"]
        assert "prop1" in result["properties"]
        assert "prop2" in result["properties"]
        assert len(result["examples"]) > 0
        assert "TestClass" in result["examples"][0]
        assert result["parent_class"] == "BaseClass"

    @pytest.mark.asyncio
    async def test_client_cleanup(
        self, client: PhaserDocsClient, mock_httpx_client: Mock
    ) -> None:
        """Test proper client cleanup."""
        await client._ensure_client()
        assert client._client is not None

        await client.close()
        mock_httpx_client.aclose.assert_called_once()
        assert client._client is None

    def test_calculate_retry_delay(self) -> None:
        """Test exponential backoff calculation."""
        client = PhaserDocsClient(retry_delay=1.0)

        assert client._calculate_retry_delay(0) == 1.0
        assert client._calculate_retry_delay(1) == 2.0
        assert client._calculate_retry_delay(2) == 4.0
        assert client._calculate_retry_delay(3) == 8.0

    def test_validate_url_empty(self) -> None:
        """Test URL validation with empty URL."""
        client = PhaserDocsClient()

        with pytest.raises(ValueError, match="URL cannot be empty"):
            client._validate_url("")

    def test_is_allowed_url_exception_handling(self) -> None:
        """Test URL validation exception handling."""
        client = PhaserDocsClient()

        # Test with malformed URL that causes urlparse to fail
        with patch("phaser_mcp_server.client.urlparse") as mock_urlparse:
            mock_urlparse.side_effect = Exception("Parse error")
            result = client._is_allowed_url("malformed://url")
            assert result is False

    @pytest.mark.asyncio
    async def test_handle_rate_limit_max_retries(
        self, client: PhaserDocsClient
    ) -> None:
        """Test rate limit handling when max retries exceeded."""
        with pytest.raises(RateLimitError, match="Rate limited after"):
            await client._handle_rate_limit(
                client.max_retries, "https://docs.phaser.io/test"
            )

    @pytest.mark.asyncio
    async def test_handle_rate_limit_with_retry(self, client: PhaserDocsClient) -> None:
        """Test rate limit handling with retry."""
        # Should not raise exception for attempts less than max_retries
        await client._handle_rate_limit(0, "https://docs.phaser.io/test")

    @pytest.mark.asyncio
    async def test_handle_server_error_retry(self, client: PhaserDocsClient) -> None:
        """Test server error handling with retry."""
        # Should return True for server errors with retries available
        result = await client._handle_server_error(500, 0)
        assert result is True

        # Should return False when max retries exceeded
        result = await client._handle_server_error(500, client.max_retries)
        assert result is False

        # Should return False for non-server errors
        result = await client._handle_server_error(404, 0)
        assert result is False

    def test_handle_http_status_error_404(self) -> None:
        """Test HTTP status error handling for 404."""
        client = PhaserDocsClient()
        mock_response = Mock()
        mock_response.status_code = 404
        error = httpx.HTTPStatusError(
            "Not Found", request=Mock(), response=mock_response
        )

        with pytest.raises(HTTPError, match="Page not found"):
            client._handle_http_status_error(error, "https://docs.phaser.io/test")

    def test_handle_http_status_error_403(self) -> None:
        """Test HTTP status error handling for 403."""
        client = PhaserDocsClient()
        mock_response = Mock()
        mock_response.status_code = 403
        error = httpx.HTTPStatusError(
            "Forbidden", request=Mock(), response=mock_response
        )

        with pytest.raises(HTTPError, match="Access forbidden"):
            client._handle_http_status_error(error, "https://docs.phaser.io/test")

    def test_handle_http_status_error_client_error(self) -> None:
        """Test HTTP status error handling for other client errors."""
        client = PhaserDocsClient()
        mock_response = Mock()
        mock_response.status_code = 400
        error = httpx.HTTPStatusError(
            "Bad Request", request=Mock(), response=mock_response
        )

        with pytest.raises(HTTPError, match="Client error 400"):
            client._handle_http_status_error(error, "https://docs.phaser.io/test")

    def test_handle_http_status_error_server_error(self) -> None:
        """Test HTTP status error handling for server errors."""
        client = PhaserDocsClient()
        mock_response = Mock()
        mock_response.status_code = 500
        error = httpx.HTTPStatusError(
            "Server Error", request=Mock(), response=mock_response
        )

        result = client._handle_http_status_error(error, "https://docs.phaser.io/test")
        assert isinstance(result, HTTPError)
        assert "HTTP error 500" in str(result)

    @pytest.mark.asyncio
    async def test_handle_network_error_with_retry(
        self, client: PhaserDocsClient
    ) -> None:
        """Test network error handling with retry."""
        error = Exception("Network error")
        result = await client._handle_network_error(error, 0, "TEST_ERROR")

        assert isinstance(result, NetworkError)
        assert "TEST_ERROR: Network error" in str(result)

    @pytest.mark.asyncio
    async def test_handle_network_error_max_retries(
        self, client: PhaserDocsClient
    ) -> None:
        """Test network error handling at max retries."""
        error = Exception("Network error")
        result = await client._handle_network_error(
            error, client.max_retries, "TEST_ERROR"
        )

        assert isinstance(result, NetworkError)
        assert "TEST_ERROR: Network error" in str(result)

    def test_validate_response_security_invalid_content_length(self) -> None:
        """Test response security validation with invalid content-length."""
        client = PhaserDocsClient()
        mock_response = Mock()
        mock_response.headers = {
            "content-type": "text/html",
            "content-length": "invalid",
        }
        mock_response.url = "https://docs.phaser.io/test"
        mock_response._content = None  # No content to check

        # Should not raise exception but log warning
        with patch("phaser_mcp_server.client.logger") as mock_logger:
            client._validate_response_security(mock_response)
            mock_logger.warning.assert_called_once()

    def test_validate_response_security_no_content_length(self) -> None:
        """Test response security validation without content-length header."""
        client = PhaserDocsClient()
        mock_response = Mock()
        mock_response.headers = {"content-type": "text/html"}
        mock_response.url = "https://docs.phaser.io/test"
        mock_response._content = b"test content"

        # Should not raise exception
        client._validate_response_security(mock_response)

    def test_validate_response_security_unexpected_content_type(self) -> None:
        """Test response security validation with unexpected content type."""
        client = PhaserDocsClient()
        mock_response = Mock()
        mock_response.headers = {"content-type": "application/json"}
        mock_response.url = "https://docs.phaser.io/test"
        mock_response._content = None  # No content to check

        # Should log warning but not raise exception
        with patch("phaser_mcp_server.client.logger") as mock_logger:
            client._validate_response_security(mock_response)
            mock_logger.warning.assert_called_once()

    def test_validate_response_security_with_security_headers(self) -> None:
        """Test response security validation logs security headers."""
        client = PhaserDocsClient()
        mock_response = Mock()
        mock_response.headers = {
            "content-type": "text/html",
            "x-frame-options": "DENY",
            "x-content-type-options": "nosniff",
            "content-security-policy": "default-src 'self'",
        }
        mock_response.url = "https://docs.phaser.io/test"
        mock_response._content = None  # No content to check

        with patch("phaser_mcp_server.client.logger") as mock_logger:
            client._validate_response_security(mock_response)
            # Should log debug messages for security headers
            assert mock_logger.debug.call_count >= 3

    @pytest.mark.asyncio
    async def test_make_request_with_retry_no_client(
        self, client: PhaserDocsClient
    ) -> None:
        """Test request with retry when client is not initialized."""
        # Ensure client is None
        client._client = None

        with pytest.raises(RuntimeError, match="HTTP client not initialized"):
            await client._make_request_with_retry("https://docs.phaser.io/test")

    @pytest.mark.asyncio
    async def test_make_request_with_retry_validation_error(
        self, client: PhaserDocsClient, mock_httpx_client: Mock
    ) -> None:
        """Test request with retry when validation error occurs."""
        # Ensure client is initialized
        await client._ensure_client()

        # Setup mock to raise validation error
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {
            "content-type": "text/html",
            "content-length": str(client.MAX_RESPONSE_SIZE + 1),
        }
        mock_response.url = "https://docs.phaser.io/test"
        mock_response.raise_for_status = Mock()
        mock_httpx_client.get.return_value = mock_response

        with pytest.raises(ValidationError, match="Response too large"):
            await client._make_request_with_retry("https://docs.phaser.io/test")

    @pytest.mark.asyncio
    async def test_make_request_with_retry_unexpected_error(
        self, client: PhaserDocsClient, mock_httpx_client: Mock
    ) -> None:
        """Test request with retry when unexpected error occurs."""
        # Ensure client is initialized
        await client._ensure_client()

        # Setup mock to raise unexpected error
        mock_httpx_client.get.side_effect = ValueError("Unexpected error")

        with pytest.raises(NetworkError, match="Unexpected error"):
            await client._make_request_with_retry("https://docs.phaser.io/test")

    @pytest.mark.asyncio
    async def test_fetch_page_unexpected_error(
        self, client: PhaserDocsClient, mock_httpx_client: Mock
    ) -> None:
        """Test fetch page with unexpected error."""
        # Setup mock to raise unexpected error after validation
        mock_httpx_client.get.side_effect = ValueError("Unexpected error")

        with pytest.raises(NetworkError, match="Unexpected error"):
            await client.fetch_page("https://docs.phaser.io/test")

    def test_extract_title_multiline(self) -> None:
        """Test title extraction with multiline title."""
        client = PhaserDocsClient()

        html = (
            "<html><head><title>Multi\nLine\nTitle</title></head><body></body></html>"
        )
        result = client._extract_title(html)
        assert result == "Multi Line Title"

    def test_extract_title_with_exception(self) -> None:
        """Test title extraction when regex fails."""
        client = PhaserDocsClient()

        with patch("re.search") as mock_search:
            mock_search.side_effect = Exception("Regex error")
            result = client._extract_title("<html><title>Test</title></html>")
            assert result == "Phaser Documentation"

    @pytest.mark.asyncio
    async def test_search_content_malicious_query(
        self, client: PhaserDocsClient
    ) -> None:
        """Test search content with malicious query patterns."""
        malicious_queries = [
            "<script>alert('xss')</script>",
            "javascript:alert(1)",
            "eval(malicious_code)",
            "document.cookie",
            "window.location = 'evil.com'",
        ]

        for query in malicious_queries:
            with pytest.raises(ValidationError, match="Suspicious pattern detected"):
                await client.search_content(query)

    @pytest.mark.asyncio
    async def test_search_content_query_truncation(
        self, client: PhaserDocsClient
    ) -> None:
        """Test search content with query that gets truncated."""
        long_query = "a" * 250  # Longer than max_query_length (200)

        with patch("phaser_mcp_server.client.logger") as mock_logger:
            result = await client.search_content(long_query)
            assert isinstance(result, list)
            # Should log truncation warning and search not implemented warning
            assert mock_logger.warning.call_count == 2

    def test_validate_search_query_truncation_logging(self) -> None:
        """Test search query validation logs truncation."""
        client = PhaserDocsClient()
        long_query = "a" * 250

        with patch("phaser_mcp_server.client.logger") as mock_logger:
            result = client._validate_search_query(long_query)
            assert len(result) == 200
            # Should log security event
            mock_logger.warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_retry_logic_all_attempts_fail(
        self, client: PhaserDocsClient, mock_httpx_client: Mock
    ) -> None:
        """Test retry logic when all attempts fail."""
        # Ensure client is initialized
        await client._ensure_client()

        # Setup mock to always fail with server error
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Server Error", request=Mock(), response=mock_response
        )
        mock_httpx_client.get.return_value = mock_response

        with pytest.raises(HTTPError, match="HTTP error 500"):
            await client._make_request_with_retry("https://docs.phaser.io/test")

        # Should have tried max_retries + 1 times
        assert mock_httpx_client.get.call_count == client.max_retries + 1

    @pytest.mark.asyncio
    async def test_retry_logic_rate_limit_then_success(
        self, client: PhaserDocsClient, mock_httpx_client: Mock
    ) -> None:
        """Test retry logic with rate limit followed by success."""
        # Ensure client is initialized
        await client._ensure_client()

        # Setup mock to return 429 first, then success
        mock_response_429 = Mock()
        mock_response_429.status_code = 429

        mock_response_success = Mock()
        mock_response_success.status_code = 200
        mock_response_success.text = "Success"
        mock_response_success.headers = {
            "content-type": "text/html",
            "content-length": "7",
        }
        mock_response_success.url = "https://docs.phaser.io/test"
        mock_response_success._content = b"Success"
        mock_response_success.raise_for_status = Mock()

        mock_httpx_client.get.side_effect = [mock_response_429, mock_response_success]

        result = await client._make_request_with_retry("https://docs.phaser.io/test")
        assert result == mock_response_success
        assert mock_httpx_client.get.call_count == 2

    @pytest.mark.asyncio
    async def test_make_request_with_retry_rate_limit_error_reraise(
        self, client: PhaserDocsClient, mock_httpx_client: Mock
    ) -> None:
        """Test that RateLimitError is re-raised immediately."""
        # Ensure client is initialized
        await client._ensure_client()

        # Setup mock to raise RateLimitError
        mock_httpx_client.get.side_effect = RateLimitError("Rate limited")

        with pytest.raises(RateLimitError, match="Rate limited"):
            await client._make_request_with_retry("https://docs.phaser.io/test")

    @pytest.mark.asyncio
    async def test_make_request_with_retry_validation_error_reraise(
        self, client: PhaserDocsClient, mock_httpx_client: Mock
    ) -> None:
        """Test that ValidationError is re-raised immediately."""
        # Ensure client is initialized
        await client._ensure_client()

        # Setup mock to raise ValidationError
        mock_httpx_client.get.side_effect = ValidationError("Validation failed")

        with pytest.raises(ValidationError, match="Validation failed"):
            await client._make_request_with_retry("https://docs.phaser.io/test")

    @pytest.mark.asyncio
    async def test_make_request_with_retry_no_last_exception(
        self, client: PhaserDocsClient, mock_httpx_client: Mock
    ) -> None:
        """Test request retry when no last exception is set."""
        # Ensure client is initialized
        await client._ensure_client()

        # Setup mock to always return None (simulating no exception but failure)
        mock_httpx_client.get.return_value = None

        with pytest.raises(NetworkError, match="Unexpected error"):
            await client._make_request_with_retry("https://docs.phaser.io/test")

    @pytest.mark.asyncio
    async def test_fetch_page_validation_error_conversion(
        self, client: PhaserDocsClient
    ) -> None:
        """Test that ValueError from URL validation is converted to ValidationError."""
        with pytest.raises(ValidationError, match="URL cannot be empty"):
            await client.fetch_page("")

    @pytest.mark.asyncio
    async def test_get_page_content_validation_error_conversion(
        self, client: PhaserDocsClient
    ) -> None:
        """Test that ValueError from URL validation is converted to ValidationError."""
        with pytest.raises(ValidationError, match="URL cannot be empty"):
            await client.get_page_content("")

    @pytest.mark.asyncio
    async def test_search_content_validation_error_conversion(
        self, client: PhaserDocsClient
    ) -> None:
        """Test that ValueError from query validation is converted to ValidationError.

        Ensures proper error handling.
        """
        with pytest.raises(ValidationError, match="Search query cannot be empty"):
            await client.search_content("")


class TestPhaserDocsExceptions:
    """Test custom exception classes."""

    def test_exception_hierarchy(self) -> None:
        """Test exception class hierarchy."""
        assert issubclass(NetworkError, PhaserDocsError)
        assert issubclass(HTTPError, PhaserDocsError)
        assert issubclass(ValidationError, PhaserDocsError)
        assert issubclass(RateLimitError, PhaserDocsError)

    def test_exception_messages(self) -> None:
        """Test exception message handling."""
        network_error = NetworkError("Connection failed")
        assert str(network_error) == "Connection failed"

        http_error = HTTPError("404 Not Found")
        assert str(http_error) == "404 Not Found"

        validation_error = ValidationError("Invalid URL")
        assert str(validation_error) == "Invalid URL"

        rate_limit_error = RateLimitError("Too many requests")
        assert str(rate_limit_error) == "Too many requests"


@pytest.mark.integration
class TestPhaserDocsClientIntegration:
    """Integration tests for PhaserDocsClient.

    These tests require network access and are marked as integration tests.
    They can be skipped in CI/CD environments where network access is limited.
    """

    @pytest.mark.asyncio
    async def test_real_phaser_docs_access(self) -> None:
        """Test accessing real Phaser documentation (requires network)."""
        client = PhaserDocsClient()

        try:
            async with client:
                # Test fetching a real page (this might fail if the site is down)
                content = await client.fetch_page("https://docs.phaser.io/")
                assert len(content) > 0
                assert "phaser" in content.lower()
        except (NetworkError, HTTPError) as e:
            # Skip test if network is unavailable
            pytest.skip(f"Network unavailable for integration test: {e}")

    @pytest.mark.asyncio
    async def test_invalid_phaser_page(self) -> None:
        """Test accessing invalid Phaser page (requires network)."""
        client = PhaserDocsClient()

        try:
            async with client:
                with pytest.raises(HTTPError):
                    await client.fetch_page(
                        "https://docs.phaser.io/nonexistent-page-12345"
                    )
        except NetworkError as e:
            # Skip test if network is unavailable
            pytest.skip(f"Network unavailable for integration test: {e}")
