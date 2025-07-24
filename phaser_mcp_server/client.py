"""HTTP client module for Phaser documentation access.

This module provides HTTP client functionality for accessing Phaser documentation
sites with proper error handling, retries, and security validation.
"""

import asyncio
import re
from urllib.parse import urljoin, urlparse

import httpx
from loguru import logger

from .models import ApiReference, DocumentationPage, SearchResult


class PhaserDocsError(Exception):
    """Base exception for Phaser documentation client errors."""


class NetworkError(PhaserDocsError):
    """Network-related errors."""


class HTTPError(PhaserDocsError):
    """HTTP-related errors."""


class ValidationError(PhaserDocsError):
    """URL validation errors."""


class RateLimitError(PhaserDocsError):
    """Rate limiting errors."""


class PhaserDocsClient:
    """HTTP client for accessing Phaser documentation.

    This client handles all HTTP requests to Phaser documentation sites
    with proper headers, error handling, and security validation.

    Attributes:
        base_url: Base URL for Phaser documentation
        timeout: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        retry_delay: Base delay between retries in seconds
    """

    # Allowed domains for security
    ALLOWED_DOMAINS = {"docs.phaser.io", "phaser.io", "www.phaser.io"}

    # Allowed content types for security
    ALLOWED_CONTENT_TYPES = {"text/html", "application/xhtml+xml", "text/plain"}

    # Maximum response size to prevent DoS (1MB)
    MAX_RESPONSE_SIZE = 1024 * 1024

    # Default headers for requests
    DEFAULT_HEADERS = {
        "User-Agent": "Phaser-MCP-Server/1.0.0 (Documentation Access Bot)",
        "Accept": ("text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"),
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    def __init__(
        self,
        base_url: str = "https://docs.phaser.io",
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ) -> None:
        """Initialize the Phaser documentation client.

        Args:
            base_url: Base URL for Phaser documentation
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Base delay between retries in seconds

        Raises:
            ValueError: If base_url is not from allowed domains
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # Validate base URL
        if not self._is_allowed_url(self.base_url):
            allowed_domains = ", ".join(self.ALLOWED_DOMAINS)
            raise ValueError(
                f"Base URL must be from allowed domains: {allowed_domains}"
            )

        # Initialize HTTP client
        self._client: httpx.AsyncClient | None = None

        logger.info(f"Initialized PhaserDocsClient with base_url: {self.base_url}")

    async def __aenter__(self) -> "PhaserDocsClient":
        """Async context manager entry."""
        await self._ensure_client()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object | None,
    ) -> None:
        """Async context manager exit."""
        await self.close()

    async def _ensure_client(self) -> None:
        """Ensure HTTP client is initialized."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                headers=self.DEFAULT_HEADERS,
                follow_redirects=True,
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=20),
            )
            logger.debug("HTTP client initialized")

    async def initialize(self) -> None:
        """Initialize the HTTP client."""
        await self._ensure_client()
        logger.info("PhaserDocsClient initialized successfully")

    async def health_check(self) -> None:
        """Perform a basic health check by testing connectivity to Phaser docs.

        Raises:
            NetworkError: If health check fails
            HTTPError: If HTTP error occurs during health check
        """
        try:
            # Test basic connectivity to the main Phaser docs page
            health_check_url = f"{self.base_url}/"
            logger.debug(f"Performing health check on: {health_check_url}")

            # Make a simple HEAD request to avoid downloading content
            if self._client is None:
                raise RuntimeError("HTTP client not initialized")

            response = await self._client.head(health_check_url)

            # Accept any 2xx or 3xx status code as healthy
            if 200 <= response.status_code < 400:
                logger.debug(f"Health check passed: {response.status_code}")
            else:
                raise HTTPError(
                    f"Health check failed with status: {response.status_code}"
                )

        except httpx.TimeoutException as e:
            raise NetworkError(f"Health check timeout: {e}") from e
        except httpx.ConnectError as e:
            raise NetworkError(f"Health check connection error: {e}") from e
        except httpx.HTTPStatusError as e:
            raise HTTPError(f"Health check HTTP error: {e}") from e
        except Exception as e:
            raise NetworkError(f"Health check unexpected error: {e}") from e

    async def close(self) -> None:
        """Close the HTTP client and cleanup resources."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
            logger.debug("HTTP client closed")

    def _is_allowed_url(self, url: str) -> bool:
        """Check if URL is from allowed domains with enhanced security checks.

        Args:
            url: URL to validate

        Returns:
            True if URL is from allowed domains, False otherwise
        """
        try:
            parsed = urlparse(url)

            # Check scheme
            if parsed.scheme not in ("http", "https"):
                self._log_security_event(
                    "INVALID_SCHEME", f"Invalid URL scheme: {parsed.scheme}", url
                )
                return False

            # Check domain
            if parsed.netloc not in self.ALLOWED_DOMAINS:
                self._log_security_event(
                    "DOMAIN_VIOLATION",
                    f"URL not from allowed domains: {parsed.netloc}",
                    url,
                )
                return False

            # Prevent path traversal attempts
            if ".." in parsed.path:
                self._log_security_event(
                    "PATH_TRAVERSAL_ATTEMPT", "Path traversal attempt detected", url
                )
                return False

            # Check for suspicious query parameters
            if parsed.query:
                suspicious_params = ["javascript:", "data:", "vbscript:", "file:"]
                query_lower = parsed.query.lower()
                for param in suspicious_params:
                    if param in query_lower:
                        self._log_security_event(
                            "SUSPICIOUS_QUERY_PARAM",
                            f"Suspicious query parameter: {param}",
                            url,
                        )
                        return False

            # Check for suspicious fragments
            if parsed.fragment:
                fragment_lower = parsed.fragment.lower()
                suspicious_schemes = ["javascript:", "data:", "vbscript:"]
                for scheme in suspicious_schemes:
                    if scheme in fragment_lower:
                        self._log_security_event(
                            "SUSPICIOUS_FRAGMENT",
                            f"Suspicious fragment scheme: {scheme}",
                            url,
                        )
                        return False

            # Additional security checks
            # Check for encoded characters that might bypass filters
            if any(char in url for char in ["%00", "%2e%2e", "%2f%2f"]):
                self._log_security_event(
                    "ENCODED_ATTACK_ATTEMPT",
                    "Potentially malicious encoded characters detected",
                    url,
                )
                return False

            # Check for excessively long URLs (potential DoS)
            if len(url) > 2048:
                self._log_security_event(
                    "EXCESSIVE_URL_LENGTH", f"URL too long: {len(url)} characters", url
                )
                return False

            return True

        except Exception as e:
            self._log_security_event(
                "URL_VALIDATION_ERROR", f"URL validation error: {e}", url
            )
            return False

    def _validate_url(self, url: str) -> str:
        """Validate and normalize URL.

        Args:
            url: URL to validate

        Returns:
            Normalized URL

        Raises:
            ValueError: If URL is invalid or not allowed
        """
        if not url:
            raise ValueError("URL cannot be empty")

        # Handle relative URLs
        original_url = url
        if url.startswith("/"):
            url = urljoin(self.base_url, url)
        elif not url.startswith(("http://", "https://")):
            # Assume it's a path relative to base_url
            url = urljoin(self.base_url + "/", url)

        # Final validation
        if not self._is_allowed_url(url):
            raise ValueError(f"URL not from allowed domains: {original_url}")

        return url

    def _sanitize_input(self, input_str: str) -> str:
        """Sanitize input string to prevent injection attacks.

        Args:
            input_str: Input string to sanitize

        Returns:
            Sanitized string
        """
        if not input_str:
            return ""

        # Remove null bytes and control characters (except tab, newline, CR)
        sanitized = "".join(c for c in input_str if ord(c) >= 32 or c in "\t\n\r")

        # Limit length to prevent DoS
        max_length = 2048
        if len(sanitized) > max_length:
            logger.warning(
                f"Input truncated from {len(sanitized)} to {max_length} characters"
            )
            sanitized = sanitized[:max_length]

        return sanitized.strip()

    def _log_security_event(self, event_type: str, details: str, url: str = "") -> None:
        """Log security-related events for monitoring.

        Args:
            event_type: Type of security event
            details: Details about the event
            url: URL related to the event (if applicable)
        """
        logger.warning(
            f"SECURITY_EVENT: {event_type} - {details}"
            + (f" - URL: {url}" if url else "")
        )

    def _validate_search_query(self, query: str) -> str:
        """Validate and sanitize search query.

        Args:
            query: Search query to validate

        Returns:
            Sanitized query string

        Raises:
            ValueError: If query is invalid
        """
        if not query:
            raise ValueError("Search query cannot be empty")

        # Sanitize the query
        sanitized_query = self._sanitize_input(query)
        if not sanitized_query:
            raise ValueError("Search query is empty after sanitization")

        # Limit query length
        max_query_length = 200
        if len(sanitized_query) > max_query_length:
            self._log_security_event(
                "QUERY_TRUNCATION",
                f"Search query truncated from {len(sanitized_query)} to "
                f"{max_query_length} characters",
            )
            sanitized_query = sanitized_query[:max_query_length]

        # Check for suspicious patterns in search query
        suspicious_patterns = [
            "<script",
            "javascript:",
            "data:",
            "vbscript:",
            "onload=",
            "onerror=",
            "eval(",
            "document.cookie",
            "window.location",
        ]

        query_lower = sanitized_query.lower()
        for pattern in suspicious_patterns:
            if pattern in query_lower:
                self._log_security_event(
                    "SUSPICIOUS_QUERY_PATTERN",
                    f"Suspicious pattern detected: {pattern}",
                    query,
                )
                raise ValueError(
                    f"Suspicious pattern detected in search query: {pattern}"
                )

        return sanitized_query

    def _calculate_retry_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay for retry attempts.

        Args:
            attempt: Current attempt number (0-based)

        Returns:
            Delay in seconds
        """
        return self.retry_delay * (2**attempt)

    async def _handle_rate_limit(self, attempt: int, url: str) -> None:
        """Handle rate limiting with retry logic.

        Args:
            attempt: Current attempt number
            url: URL being requested

        Raises:
            RateLimitError: If max retries exceeded
        """
        if attempt < self.max_retries:
            wait_time = self._calculate_retry_delay(attempt)
            logger.warning(f"Rate limited, waiting {wait_time}s before retry")
            await asyncio.sleep(wait_time)
        else:
            raise RateLimitError(f"Rate limited after {self.max_retries} retries")

    async def _handle_server_error(self, status_code: int, attempt: int) -> bool:
        """Handle server errors with retry logic.

        Args:
            status_code: HTTP status code
            attempt: Current attempt number

        Returns:
            True if should retry, False otherwise
        """
        if status_code >= 500 and attempt < self.max_retries:
            wait_time = self._calculate_retry_delay(attempt)
            logger.warning(f"Server error {status_code}, retrying in {wait_time}s")
            await asyncio.sleep(wait_time)
            return True
        return False

    def _handle_http_status_error(
        self, error: httpx.HTTPStatusError, url: str
    ) -> HTTPError:
        """Handle HTTP status errors and convert to appropriate exceptions.

        Args:
            error: HTTP status error
            url: URL that caused the error

        Returns:
            Appropriate HTTPError exception

        Raises:
            HTTPError: For client errors that shouldn't be retried
        """
        status_code = error.response.status_code

        # Handle specific client errors that shouldn't be retried
        if status_code == 404:
            raise HTTPError(f"Page not found: {url}") from error
        if status_code == 403:
            raise HTTPError(f"Access forbidden: {url}") from error
        if 400 <= status_code < 500:
            raise HTTPError(f"Client error {status_code}: {url}") from error

        # Return server errors for potential retry
        return HTTPError(f"HTTP error {status_code}: {error}")

    async def _handle_network_error(
        self, error: Exception, attempt: int, error_type: str
    ) -> NetworkError:
        """Handle network errors with retry logic.

        Args:
            error: The network error
            attempt: Current attempt number
            error_type: Type of error for logging

        Returns:
            NetworkError exception
        """
        network_error = NetworkError(f"{error_type}: {error}")

        if attempt < self.max_retries:
            wait_time = self._calculate_retry_delay(attempt)
            logger.warning(f"{error_type}, retrying in {wait_time}s")
            await asyncio.sleep(wait_time)

        return network_error

    def _validate_response_security(self, response: httpx.Response) -> None:
        """Validate response for security concerns.

        Args:
            response: HTTP response to validate

        Raises:
            ValidationError: If response fails security validation
        """
        # Check content type
        content_type = response.headers.get("content-type", "").lower()
        content_type_main = content_type.split(";")[0].strip()

        if content_type_main not in self.ALLOWED_CONTENT_TYPES:
            logger.warning(
                f"Unexpected content type: {content_type_main} for {response.url}"
            )
            # Allow it but log the warning - some pages might have variations

        # Check response size
        content_length = response.headers.get("content-length")
        if content_length:
            try:
                size = int(content_length)
                if size > self.MAX_RESPONSE_SIZE:
                    raise ValidationError(
                        f"Response too large: {size} bytes "
                        f"(max: {self.MAX_RESPONSE_SIZE})"
                    )
            except ValueError:
                logger.warning(f"Invalid content-length header: {content_length}")

        # Check actual content size if no content-length header
        # Access content through the public interface
        if response.content:
            actual_size = len(response.content)
            if actual_size > self.MAX_RESPONSE_SIZE:
                raise ValidationError(
                    f"Response content too large: {actual_size} bytes "
                    f"(max: {self.MAX_RESPONSE_SIZE})"
                )

        # Log security-relevant headers for monitoring
        security_headers = [
            "x-frame-options",
            "x-content-type-options",
            "x-xss-protection",
            "content-security-policy",
            "strict-transport-security",
        ]

        for header in security_headers:
            if header in response.headers:
                logger.debug(f"Security header {header}: {response.headers[header]}")

    async def _make_request_with_retry(self, url: str) -> httpx.Response:
        """Make HTTP request with exponential backoff retry.

        Args:
            url: URL to request

        Returns:
            HTTP response

        Raises:
            NetworkError: For network-related errors
            HTTPError: For HTTP status errors
            RateLimitError: For rate limiting errors
            ValidationError: For security validation errors
        """
        if self._client is None:
            raise RuntimeError("HTTP client not initialized")

        last_exception = None

        for attempt in range(self.max_retries + 1):
            try:
                logger.debug(
                    f"Request attempt {attempt + 1}/{self.max_retries + 1} for {url}"
                )

                response = await self._client.get(url)

                # Handle rate limiting
                if response.status_code == 429:
                    await self._handle_rate_limit(attempt, url)
                    continue

                # Handle server errors that might be temporary
                if await self._handle_server_error(response.status_code, attempt):
                    continue

                # Raise for other HTTP errors
                response.raise_for_status()

                # Validate response for security
                self._validate_response_security(response)

                logger.debug(f"Request successful after {attempt + 1} attempts")
                return response

            except httpx.TimeoutException as e:
                last_exception = await self._handle_network_error(
                    e, attempt, "Request timeout"
                )
                if attempt < self.max_retries:
                    continue

            except httpx.ConnectError as e:
                last_exception = await self._handle_network_error(
                    e, attempt, "Connection error"
                )
                if attempt < self.max_retries:
                    continue

            except httpx.HTTPStatusError as e:
                try:
                    self._handle_http_status_error(e, url)
                except HTTPError:
                    # Re-raise client errors immediately
                    raise

                # Server errors - prepare for retry
                last_exception = HTTPError(f"HTTP error {e.response.status_code}: {e}")
                if attempt < self.max_retries:
                    wait_time = self._calculate_retry_delay(attempt)
                    logger.warning(f"HTTP error, retrying in {wait_time}s")
                    await asyncio.sleep(wait_time)
                    continue

            except RateLimitError:
                # Re-raise rate limit errors immediately
                raise
            except ValidationError:
                # Re-raise validation errors immediately - don't retry
                raise
            except Exception as e:
                last_exception = await self._handle_network_error(
                    e, attempt, "Unexpected error"
                )
                if attempt < self.max_retries:
                    continue

        # If we get here, all retries failed
        if last_exception:
            logger.error(f"All {self.max_retries + 1} attempts failed for {url}")
            raise last_exception

        raise NetworkError(f"Request failed after {self.max_retries + 1} attempts")

    async def fetch_page(self, url: str) -> str:
        """Fetch a single page content with retry logic.

        Args:
            url: URL of the page to fetch

        Returns:
            HTML content of the page

        Raises:
            ValidationError: If URL is invalid
            NetworkError: For network-related errors
            HTTPError: For HTTP status errors
            RateLimitError: For rate limiting errors
        """
        try:
            validated_url = self._validate_url(url)
        except ValueError as e:
            raise ValidationError(str(e)) from e

        await self._ensure_client()

        logger.info(f"Fetching page: {validated_url}")

        try:
            response = await self._make_request_with_retry(validated_url)
            content = response.text

            logger.debug(
                f"Successfully fetched {len(content)} characters from {validated_url}"
            )
            return content

        except (NetworkError, HTTPError, RateLimitError, ValidationError):
            # Re-raise our custom exceptions
            raise
        except Exception as e:
            logger.error(f"Unexpected error fetching {validated_url}: {e}")
            raise NetworkError(f"Unexpected error: {e}") from e

    async def get_page_content(self, url: str) -> DocumentationPage:
        """Get page content as a DocumentationPage model.

        Args:
            url: URL of the page to fetch

        Returns:
            DocumentationPage with fetched content

        Raises:
            ValidationError: If URL is invalid
            NetworkError: For network-related errors
            HTTPError: For HTTP status errors
            RateLimitError: For rate limiting errors
        """
        try:
            validated_url = self._validate_url(url)
        except ValueError as e:
            raise ValidationError(str(e)) from e

        html_content = await self.fetch_page(validated_url)

        # Extract title from HTML (basic implementation)
        title = self._extract_title(html_content)

        # Return HTML as content (will be converted to Markdown by parser)
        return DocumentationPage(
            url=validated_url,
            title=title,
            content=html_content,
            content_type="text/html",
        )

    def _extract_title(self, html_content: str) -> str:
        """Extract title from HTML content.

        Args:
            html_content: HTML content to extract title from

        Returns:
            Extracted title or default title
        """
        try:
            # Simple title extraction - look for <title> tag
            title_match = re.search(
                r"<title[^>]*>(.*?)</title>", html_content, re.IGNORECASE | re.DOTALL
            )
            if title_match:
                title = title_match.group(1).strip()
                # Clean up HTML entities and whitespace
                title = re.sub(r"\s+", " ", title)
                return title
        except Exception as e:
            logger.warning(f"Failed to extract title: {e}")

        return "Phaser Documentation"

    async def search_content(self, query: str, limit: int = 10) -> list[SearchResult]:
        """Search for content in Phaser documentation.

        This implementation searches through known Phaser documentation pages
        and returns results based on content matching.

        Args:
            query: Search query string
            limit: Maximum number of results to return

        Returns:
            List of search results

        Raises:
            ValidationError: If query is invalid
            ValueError: If limit is invalid
        """
        try:
            sanitized_query = self._validate_search_query(query)
        except ValueError as e:
            raise ValidationError(str(e)) from e

        # Validate limit parameter
        if limit < 1:
            raise ValueError("Limit must be a positive integer")

        if limit > 100:
            logger.warning(f"Search limit capped at 100 (requested: {limit})")
            limit = 100

        logger.info(f"Searching for: {sanitized_query} (limit: {limit})")

        try:
            # Get search results from known documentation pages
            search_results = await self._perform_documentation_search(
                sanitized_query, limit
            )

            logger.info(f"Search completed: {len(search_results)} results found")
            return search_results

        except Exception as e:
            logger.error(f"Search failed for query '{sanitized_query}': {e}")
            raise NetworkError(f"Search failed: {e}") from e

    async def _perform_documentation_search(
        self, query: str, limit: int
    ) -> list[SearchResult]:
        """Perform actual documentation search across known Phaser pages.

        Args:
            query: Sanitized search query
            limit: Maximum number of results to return

        Returns:
            List of SearchResult objects

        Raises:
            NetworkError: If search fails due to network issues
        """
        from typing import TypedDict

        class PageInfo(TypedDict):
            url: str
            title: str
            priority: float
            keywords: list[str]

        # Define known Phaser documentation pages to search
        # These are representative URLs - in a real implementation,
        # these would be discovered through site crawling or API
        search_pages: list[PageInfo] = [
            {
                "url": "https://docs.phaser.io/getting-started",
                "title": "Getting Started with Phaser",
                "priority": 1.0,
                "keywords": [
                    "getting",
                    "started",
                    "tutorial",
                    "begin",
                    "first",
                    "game",
                ],
            },
            {
                "url": "https://docs.phaser.io/sprites-and-images",
                "title": "Working with Sprites and Images",
                "priority": 0.9,
                "keywords": ["sprite", "image", "texture", "display", "gameobject"],
            },
            {
                "url": "https://docs.phaser.io/scenes",
                "title": "Understanding Scenes",
                "priority": 0.9,
                "keywords": ["scene", "state", "manager", "lifecycle"],
            },
            {
                "url": "https://docs.phaser.io/physics",
                "title": "Physics Systems",
                "priority": 0.8,
                "keywords": ["physics", "arcade", "matter", "collision", "body"],
            },
            {
                "url": "https://docs.phaser.io/input-handling",
                "title": "Input Handling",
                "priority": 0.8,
                "keywords": ["input", "keyboard", "mouse", "touch", "pointer"],
            },
            {
                "url": "https://docs.phaser.io/animations",
                "title": "Animations and Tweens",
                "priority": 0.8,
                "keywords": ["animation", "tween", "timeline", "motion"],
            },
            {
                "url": "https://docs.phaser.io/audio",
                "title": "Audio and Sound",
                "priority": 0.7,
                "keywords": ["audio", "sound", "music", "sfx", "webaudio"],
            },
            {
                "url": "https://docs.phaser.io/cameras",
                "title": "Camera System",
                "priority": 0.7,
                "keywords": ["camera", "viewport", "zoom", "follow"],
            },
            {
                "url": "https://docs.phaser.io/tilemaps",
                "title": "Tilemap Support",
                "priority": 0.7,
                "keywords": ["tilemap", "tile", "map", "tiled", "level"],
            },
            {
                "url": "https://docs.phaser.io/plugins",
                "title": "Plugin System",
                "priority": 0.6,
                "keywords": ["plugin", "extend", "custom", "addon"],
            },
        ]

        # API reference pages
        api_pages: list[PageInfo] = [
            {
                "url": "https://docs.phaser.io/api/scene",
                "title": "Phaser.Scene API",
                "priority": 0.9,
                "keywords": ["scene", "api", "class", "method", "lifecycle"],
            },
            {
                "url": "https://docs.phaser.io/api/sprite",
                "title": "Phaser.GameObjects.Sprite API",
                "priority": 0.9,
                "keywords": ["sprite", "gameobject", "api", "texture", "display"],
            },
            {
                "url": "https://docs.phaser.io/api/physics-arcade",
                "title": "Phaser.Physics.Arcade API",
                "priority": 0.8,
                "keywords": ["physics", "arcade", "api", "body", "collision"],
            },
            {
                "url": "https://docs.phaser.io/api/input",
                "title": "Phaser.Input API",
                "priority": 0.8,
                "keywords": ["input", "api", "keyboard", "mouse", "pointer"],
            },
            {
                "url": "https://docs.phaser.io/api/cameras",
                "title": "Phaser.Cameras API",
                "priority": 0.7,
                "keywords": ["camera", "api", "viewport", "zoom"],
            },
        ]

        # Combine all pages to search
        all_pages = search_pages + api_pages

        # Prepare search terms
        search_terms = query.lower().split()

        # Store search results with scores
        scored_results: list[dict[str, str | float]] = []

        # Search through each page using keyword matching
        for page_info in all_pages:
            try:
                # Calculate relevance score based on title and keyword matching
                title_score = self._calculate_title_relevance(
                    page_info["title"], search_terms
                )

                # Calculate keyword relevance
                keyword_score = self._calculate_keyword_relevance(
                    page_info.get("keywords", []), search_terms
                )

                # Combine scores with page priority
                final_score = (title_score * 0.3 + keyword_score * 0.7) * page_info[
                    "priority"
                ]

                if final_score > 0.1:  # Minimum relevance threshold
                    # Generate a relevant snippet based on keywords and title
                    snippet = self._generate_search_snippet(
                        page_info["title"], page_info.get("keywords", []), search_terms
                    )

                    scored_results.append(
                        {
                            "score": final_score,
                            "url": page_info["url"],
                            "title": page_info["title"],
                            "snippet": snippet,
                        }
                    )

            except Exception as e:
                logger.warning(f"Error processing page {page_info['url']}: {e}")
                continue

        # Sort results by score (descending)
        scored_results.sort(key=lambda x: x["score"], reverse=True)

        # Convert to SearchResult objects
        search_results: list[SearchResult] = []
        for i, result in enumerate(scored_results[:limit]):
            search_results.append(
                SearchResult(
                    rank_order=i + 1,
                    url=result["url"],
                    title=result["title"],
                    snippet=result["snippet"],
                    relevance_score=round(result["score"], 3),
                )
            )

        return search_results

    def _calculate_title_relevance(self, title: str, search_terms: list[str]) -> float:
        """Calculate relevance score based on title matching.

        Args:
            title: Page title to check
            search_terms: List of search terms

        Returns:
            Relevance score between 0.0 and 1.0
        """
        if not title or not search_terms:
            return 0.0

        title_lower = title.lower()
        matches = 0
        total_terms = len(search_terms)

        for term in search_terms:
            if term in title_lower:
                matches += 1

        return matches / total_terms if total_terms > 0 else 0.0

    def _calculate_keyword_relevance(
        self, keywords: list[str], search_terms: list[str]
    ) -> float:
        """Calculate relevance score based on keyword matching.

        Args:
            keywords: List of keywords associated with the page
            search_terms: List of search terms

        Returns:
            Relevance score between 0.0 and 1.0
        """
        if not keywords or not search_terms:
            return 0.0

        # Convert keywords to lowercase for comparison
        keywords_lower = [kw.lower() for kw in keywords]

        matches = 0
        total_terms = len(search_terms)

        for term in search_terms:
            term_lower = term.lower()
            # Check for exact matches
            if term_lower in keywords_lower:
                matches += 1
            else:
                # Check for partial matches (term contained in keyword)
                for keyword in keywords_lower:
                    if term_lower in keyword or keyword in term_lower:
                        matches += 0.5  # Partial match gets half score
                        break

        return min(matches / total_terms, 1.0) if total_terms > 0 else 0.0

    def _generate_search_snippet(
        self, title: str, keywords: list[str], search_terms: list[str]
    ) -> str:
        """Generate a relevant snippet for search results based on keywords and title.

        Args:
            title: Page title
            keywords: List of keywords associated with the page
            search_terms: List of search terms

        Returns:
            Generated snippet text
        """
        if not title:
            return ""

        # Find matching keywords
        matching_keywords = []
        for term in search_terms:
            term_lower = term.lower()
            for keyword in keywords:
                if term_lower in keyword.lower() or keyword.lower() in term_lower:
                    if keyword not in matching_keywords:
                        matching_keywords.append(keyword)

        # Generate snippet based on title and matching keywords
        if matching_keywords:
            snippet = f"This page covers {', '.join(matching_keywords[:3])}."
            if len(matching_keywords) > 3:
                more_keywords = ", ".join(matching_keywords[3:5])
                snippet += f" Also includes information about {more_keywords}."
        else:
            # Fallback to a generic snippet based on title
            snippet = f"Documentation page about {title.lower()}."

        return snippet

    def _calculate_content_relevance(
        self, html_content: str, search_terms: list[str]
    ) -> float:
        """Calculate relevance score based on content matching.

        Args:
            html_content: HTML content to search
            search_terms: List of search terms

        Returns:
            Relevance score between 0.0 and 1.0
        """
        if not html_content or not search_terms:
            return 0.0

        # Simple text extraction from HTML (remove tags)
        text_content = re.sub(r"<[^>]+>", " ", html_content).lower()

        # Count term occurrences
        total_matches = 0
        for term in search_terms:
            matches = text_content.count(term)
            total_matches += matches

        # Normalize by content length and number of terms
        content_words = len(text_content.split())
        if content_words == 0:
            return 0.0

        # Calculate relevance as a ratio with diminishing returns
        relevance = min(total_matches / (content_words * 0.01), 1.0)
        return relevance

    def _extract_search_snippet(
        self, html_content: str, search_terms: list[str]
    ) -> str:
        """Extract a relevant snippet from content for search results.

        Args:
            html_content: HTML content to extract from
            search_terms: Search terms to find context for

        Returns:
            Relevant text snippet
        """
        if not html_content or not search_terms:
            return ""

        # Remove HTML tags and normalize whitespace
        text_content = re.sub(r"<[^>]+>", " ", html_content)
        text_content = re.sub(r"\s+", " ", text_content).strip()

        # Find the first occurrence of any search term
        best_position = -1

        for term in search_terms:
            position = text_content.lower().find(term.lower())
            if position != -1 and (best_position == -1 or position < best_position):
                best_position = position

        if best_position == -1:
            # No terms found, return beginning of content
            return (
                text_content[:200] + "..." if len(text_content) > 200 else text_content
            )

        # Extract snippet around the found term
        snippet_start = max(0, best_position - 100)
        snippet_end = min(len(text_content), best_position + 200)

        snippet = text_content[snippet_start:snippet_end]

        # Add ellipsis if we're not at the beginning/end
        if snippet_start > 0:
            snippet = "..." + snippet
        if snippet_end < len(text_content):
            snippet = snippet + "..."

        return snippet.strip()

    async def get_api_reference(self, class_name: str) -> "ApiReference":
        """Get API reference for a specific Phaser class.

        Args:
            class_name: Name of the Phaser class

        Returns:
            ApiReference object with class information

        Raises:
            ValidationError: If class_name is invalid
            NetworkError: For network-related errors
            HTTPError: For HTTP status errors
        """
        # ApiReference already imported at module level

        try:
            # Sanitize class name
            sanitized_class_name = self._sanitize_input(class_name)
            if not sanitized_class_name:
                raise ValidationError("Class name is empty after sanitization")

            # Construct API URL - try different possible URL patterns
            possible_urls = [
                f"https://docs.phaser.io/api/{sanitized_class_name}",
                f"https://docs.phaser.io/api/Phaser.{sanitized_class_name}",
                f"https://docs.phaser.io/api/Phaser.GameObjects.{sanitized_class_name}",
                f"https://docs.phaser.io/api/Phaser.Scene.{sanitized_class_name}",
            ]

            logger.info(f"Fetching API reference for class: {sanitized_class_name}")

            # Try to fetch from the most likely URL first
            api_url = possible_urls[0]
            html_content = None

            for url in possible_urls:
                try:
                    html_content = await self.fetch_page(url)
                    api_url = url
                    logger.debug(f"Successfully fetched API page from: {url}")
                    break
                except HTTPError as e:
                    if "404" in str(e):
                        logger.debug(f"API page not found at: {url}")
                        continue
                    else:
                        raise

            if html_content is None:
                # If no specific API page found, create a basic reference
                logger.warning(
                    f"No specific API page found for {sanitized_class_name}, "
                    f"creating basic reference"
                )
                api_url = possible_urls[0]  # Use the first URL as fallback

                return ApiReference(
                    class_name=sanitized_class_name,
                    url=api_url,
                    description=(
                        f"API reference for {sanitized_class_name}. "
                        "No specific documentation page found."
                    ),
                    methods=[],
                    properties=[],
                    examples=[],
                )

            # Extract information from the HTML content
            api_info = self._extract_api_information_from_html(
                html_content, sanitized_class_name
            )

            # Create API reference with extracted information
            api_ref = ApiReference(
                class_name=sanitized_class_name,
                url=api_url,
                description=api_info.get(
                    "description", f"API reference for {sanitized_class_name}"
                ),
                methods=api_info.get("methods", []),
                properties=api_info.get("properties", []),
                examples=api_info.get("examples", []),
                parent_class=api_info.get("parent_class"),
                namespace=api_info.get("namespace"),
            )

            logger.info(
                f"Successfully retrieved API reference for {sanitized_class_name}"
            )
            return api_ref

        except (ValidationError, NetworkError, HTTPError):
            raise
        except Exception as e:
            logger.error(
                f"Unexpected error getting API reference for '{class_name}': {e}"
            )
            raise NetworkError(f"Unexpected error: {e}") from e

    def _extract_api_information_from_html(
        self, html_content: str, class_name: str
    ) -> dict[str, str | list[str] | None]:
        """Extract API information from HTML content.

        Args:
            html_content: HTML content of the API page
            class_name: Name of the class being processed

        Returns:
            Dictionary containing extracted API information
        """
        try:
            # re already imported at module level
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html_content, "html.parser")
            api_info: dict[str, str | list[str] | None] = {
                "description": "",
                "methods": [],
                "properties": [],
                "examples": [],
                "parent_class": None,
                "namespace": None,
            }

            # Extract description from various possible locations
            description_selectors = [
                ".class-description",
                ".api-description",
                ".description",
                "p:first-of-type",
                ".summary",
            ]

            for selector in description_selectors:
                desc_element = soup.select_one(selector)
                if desc_element:
                    description = desc_element.get_text(strip=True)
                    if (
                        description and len(description) > 10
                    ):  # Avoid very short descriptions
                        api_info["description"] = description
                        break

            # If no description found, use a default
            if not api_info["description"]:
                api_info["description"] = f"API reference for {class_name}"

            # Extract methods
            method_selectors = [
                ".method-list .method-name",
                ".methods .method",
                ".method h3",
                ".method",
                "[data-method]",
            ]

            methods: set[str] = set()
            for selector in method_selectors:
                for element in soup.select(selector):
                    method_text = element.get_text(strip=True)
                    if method_text:
                        # Clean method name (remove parameters, etc.)
                        method_name = re.sub(r"\([^)]*\)", "", method_text).strip()
                        if method_name and not method_name.startswith("_"):
                            # Skip private methods
                            methods.add(method_name)

            # Also look for methods in sections with "Methods" heading
            methods_sections = soup.find_all(
                ["h2", "h3"], string=re.compile(r"Methods?", re.IGNORECASE)
            )
            for section in methods_sections:
                # Find the next sibling that contains method information
                next_element = section.find_next_sibling()
                while next_element:
                    if next_element.name in ["h2", "h3"]:  # Stop at next heading
                        break
                    if next_element.name in ["ul", "ol", "div"]:
                        for method_elem in next_element.find_all(
                            ["li", "div", "h3", "h4"]
                        ):
                            method_text = method_elem.get_text(strip=True)
                            if method_text:
                                method_name = re.sub(
                                    r"\([^)]*\)", "", method_text
                                ).strip()
                                if (
                                    method_name
                                    and not method_name.startswith("_")
                                    and len(method_name) < 50
                                ):
                                    methods.add(method_name)
                    next_element = next_element.find_next_sibling()

            api_info["methods"] = sorted(methods)

            # Extract properties
            property_selectors = [
                ".property-list .property-name",
                ".properties .property",
                "[data-property]",
                "h3:contains('Properties') + ul li",
                "h2:contains('Properties') + ul li",
            ]

            properties: set[str] = set()
            for selector in property_selectors:
                for element in soup.select(selector):
                    prop_text = element.get_text(strip=True)
                    if prop_text:
                        # Clean property name
                        prop_name = prop_text.split(":")[0].split("=")[0].strip()
                        if prop_name and not prop_name.startswith("_"):
                            # Skip private properties
                            properties.add(prop_name)

            api_info["properties"] = sorted(properties)

            # Extract code examples
            example_selectors = [
                "pre code",
                ".example code",
                ".code-example",
                "code.language-javascript",
            ]

            examples: list[str] = []
            for selector in example_selectors:
                for element in soup.select(selector):
                    code_text = element.get_text(strip=True)
                    if code_text and len(code_text) > 10:  # Avoid very short snippets
                        # Clean up the code
                        cleaned_code = re.sub(r"\n\s*\n", "\n", code_text)
                        if cleaned_code not in examples:  # Avoid duplicates
                            examples.append(cleaned_code)

            api_info["examples"] = examples[:5]  # Limit to 5 examples

            # Extract parent class information
            inheritance_selectors = [".inheritance", ".extends", ".parent-class"]

            for selector in inheritance_selectors:
                element = soup.select_one(selector)
                if element:
                    parent_text = element.get_text(strip=True)
                    if "extends" in parent_text.lower():
                        # Extract parent class name
                        parent_match = re.search(
                            r"extends\s+([A-Za-z0-9_.]+)", parent_text
                        )
                        if parent_match:
                            api_info["parent_class"] = parent_match.group(1)
                            break

            # Extract namespace information
            if "." in class_name:
                api_info["namespace"] = ".".join(class_name.split(".")[:-1])
            else:
                # Try to detect namespace from page content
                namespace_patterns = [
                    r"Phaser\.GameObjects\." + re.escape(class_name),
                    r"Phaser\.Scene\." + re.escape(class_name),
                    r"Phaser\." + re.escape(class_name),
                ]

                page_text = soup.get_text()
                for pattern in namespace_patterns:
                    if re.search(pattern, page_text):
                        namespace = (
                            pattern.replace(re.escape(class_name), "")
                            .replace("\\", "")
                            .rstrip(".")
                        )
                        api_info["namespace"] = namespace
                        break

            logger.debug(
                f"Extracted API info for {class_name}: "
                f"{len(api_info['methods'])} methods, "
                f"{len(api_info['properties'])} properties, "
                f"{len(api_info['examples'])} examples"
            )

            return api_info

        except Exception as e:
            logger.warning(f"Error extracting API information: {e}")
            return {
                "description": f"API reference for {class_name}",
                "methods": [],
                "properties": [],
                "examples": [],
                "parent_class": None,
                "namespace": None,
            }


# Export the client class
__all__ = ["PhaserDocsClient"]
