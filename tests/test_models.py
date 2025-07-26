"""Unit tests for Pydantic data models.

This module contains comprehensive tests for all data models including
validation tests, error cases, and edge cases.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from phaser_mcp_server.models import ApiReference, DocumentationPage, SearchResult


class TestDocumentationPage:
    """Test cases for DocumentationPage model."""

    def test_valid_documentation_page_creation(self):
        """Test creating a valid DocumentationPage instance."""
        page = DocumentationPage(
            url="https://docs.phaser.io/phaser/getting-started",
            title="Getting Started with Phaser",
            content="# Getting Started\n\nThis guide helps you start.",
            last_modified=datetime(2024, 1, 15, 10, 30, 0),
            content_type="text/html",
            word_count=12,
        )

        assert page.url == "https://docs.phaser.io/phaser/getting-started"
        assert page.title == "Getting Started with Phaser"
        assert page.content == "# Getting Started\n\nThis guide helps you start."
        assert page.last_modified == datetime(2024, 1, 15, 10, 30, 0)
        assert page.content_type == "text/html"
        assert page.word_count == 12

    def test_documentation_page_with_defaults(self):
        """Test creating DocumentationPage with default values."""
        page = DocumentationPage(
            url="https://docs.phaser.io/phaser/sprites",
            title="Working with Sprites",
            content="Sprites are the basic building blocks of games.",
        )

        assert page.last_modified is None
        assert page.content_type == "text/html"
        assert page.word_count == 8  # Auto-calculated from content

    def test_word_count_auto_calculation(self):
        """Test automatic word count calculation."""
        content = "This is a test content with exactly ten words here."
        page = DocumentationPage(
            url="https://docs.phaser.io/phaser/test", title="Test Page", content=content
        )

        assert page.word_count == 10

    def test_word_count_manual_override(self):
        """Test that manually set word count is preserved."""
        page = DocumentationPage(
            url="https://docs.phaser.io/phaser/test",
            title="Test Page",
            content="Short content",
            word_count=100,  # Manually set, different from actual
        )

        assert page.word_count == 100  # Should preserve manual value

    def test_title_cleaning(self):
        """Test title cleaning functionality."""
        test_cases = [
            ("Getting Started - Phaser", "Getting Started"),
            ("API Reference | Phaser Documentation", "API Reference"),
            ("Sprites :: Phaser Documentation", "Sprites"),
            ("  Whitespace Title  ", "Whitespace Title"),
            ("Normal Title", "Normal Title"),
        ]

        for input_title, expected_title in test_cases:
            page = DocumentationPage(
                url="https://docs.phaser.io/phaser/test",
                title=input_title,
                content="Test content",
            )
            assert page.title == expected_title

    def test_invalid_url_schemes(self):
        """Test validation of URL schemes."""
        invalid_urls = [
            "ftp://docs.phaser.io/phaser/test",
            "file:///local/path",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "://docs.phaser.io/test",  # Empty scheme
        ]

        for invalid_url in invalid_urls:
            with pytest.raises(ValidationError) as exc_info:
                DocumentationPage(url=invalid_url, title="Test", content="Test content")
            assert "URL must use http or https scheme" in str(exc_info.value)

    def test_invalid_domains(self):
        """Test validation of allowed domains."""
        invalid_domains = [
            "https://malicious.com/phaser/docs",
            "https://example.com/docs",
            "https://phaser.fake.io/docs",
            "https://docs.phaser.evil.com/api",
        ]

        for invalid_url in invalid_domains:
            with pytest.raises(ValidationError) as exc_info:
                DocumentationPage(url=invalid_url, title="Test", content="Test content")
            assert "URL must be from allowed domains" in str(exc_info.value)

    def test_valid_domains(self):
        """Test that valid Phaser domains are accepted."""
        valid_urls = [
            "https://docs.phaser.io/phaser/getting-started",
            "http://docs.phaser.io/api/Phaser.Sprite",
            "https://phaser.io/tutorials",
            "https://www.phaser.io/examples",
        ]

        for valid_url in valid_urls:
            page = DocumentationPage(
                url=valid_url, title="Test", content="Test content"
            )
            assert page.url == valid_url

    def test_empty_url_validation(self):
        """Test validation of empty URLs."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentationPage(url="", title="Test", content="Test content")
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_empty_title_validation(self):
        """Test validation of empty titles."""
        invalid_titles = ["", "   ", "\t\n"]

        for invalid_title in invalid_titles:
            with pytest.raises(ValidationError) as exc_info:
                DocumentationPage(
                    url="https://docs.phaser.io/phaser/test",
                    title=invalid_title,
                    content="Test content",
                )
            if invalid_title == "":
                assert "String should have at least 1 character" in str(exc_info.value)
            else:
                assert "Title cannot be empty or whitespace only" in str(exc_info.value)

    def test_empty_content_validation(self):
        """Test validation of empty content."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentationPage(
                url="https://docs.phaser.io/phaser/test", title="Test", content=""
            )
        assert "at least 1 character" in str(exc_info.value)

    def test_url_length_validation(self):
        """Test URL length validation."""
        long_url = "https://docs.phaser.io/" + "a" * 2050

        with pytest.raises(ValidationError) as exc_info:
            DocumentationPage(url=long_url, title="Test", content="Test content")
        assert "at most 2048 characters" in str(exc_info.value)

    def test_title_length_validation(self):
        """Test title length validation."""
        long_title = "A" * 501

        with pytest.raises(ValidationError) as exc_info:
            DocumentationPage(
                url="https://docs.phaser.io/phaser/test",
                title=long_title,
                content="Test content",
            )
        assert "at most 500 characters" in str(exc_info.value)

    def test_negative_word_count_validation(self):
        """Test that negative word count is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentationPage(
                url="https://docs.phaser.io/phaser/test",
                title="Test",
                content="Test content",
                word_count=-1,
            )
        assert "greater than or equal to 0" in str(exc_info.value)

    def test_word_count_edge_cases(self):
        """Test word count calculation with edge cases."""
        # Test with content that has multiple spaces, tabs, newlines
        content = "  Word1   \t\t  Word2\n\n\nWord3  \r\n  Word4  "
        page = DocumentationPage(
            url="https://docs.phaser.io/phaser/test", title="Test", content=content
        )

        # Should count 4 words despite irregular spacing
        assert page.word_count == 4

    def test_word_count_with_various_content_types(self):
        """Test word count calculation with various content types."""
        test_cases = [
            # Markdown content with headers (simple split counts all tokens)
            (
                "# Header\n\n## Subheader\n\nContent here",
                6,
            ),  # #, Header, ##, Subheader, Content, here
            # Code blocks
            (
                "```python\nprint('hello')\n```\nSome text",
                5,
            ),  # ```python, print('hello'), ```, Some, text
            # HTML-like content (split by whitespace)
            (
                "<p>Paragraph with <strong>bold</strong> text</p>",
                4,
            ),  # <p>Paragraph, with, <strong>bold</strong>, text</p>
            # Mixed punctuation
            ("Hello, world! How are you? I'm fine.", 7),
            # Numbers and special characters
            ("Version 3.14.0 supports @decorators and #hashtags", 6),
            # Single word
            ("Word", 1),
            # Only punctuation and symbols
            ("!@#$%^&*()", 1),
            # Unicode characters
            ("こんにちは world 世界", 3),
            # URLs and email addresses
            ("Visit https://example.com or email test@example.com", 5),
            # Hyphenated words (treated as single words by split)
            (
                "Well-known state-of-the-art solution",
                3,
            ),  # Well-known, state-of-the-art, solution
            # Contractions
            ("Don't can't won't shouldn't", 4),
        ]

        for content, expected_count in test_cases:
            page = DocumentationPage(
                url="https://docs.phaser.io/phaser/test",
                title="Test",
                content=content,
            )
            assert page.word_count == expected_count, f"Failed for content: {content!r}"

    def test_url_validation_edge_cases(self):
        """Test URL validation with various edge cases."""
        # Test URLs with query parameters and fragments (without explicit ports)
        valid_edge_case_urls = [
            "https://docs.phaser.io/phaser/test?param=value",
            "https://docs.phaser.io/phaser/test#section",
            "https://docs.phaser.io/phaser/test?param=value&other=test#section",
            "https://docs.phaser.io/phaser/test/",  # Trailing slash
            "https://docs.phaser.io/phaser/test/../other",  # Path traversal (allowed in URL)
            "https://docs.phaser.io/phaser/test%20with%20spaces",  # URL encoded
        ]

        for url in valid_edge_case_urls:
            page = DocumentationPage(url=url, title="Test", content="Test content")
            assert page.url == url

        # Test invalid edge cases
        invalid_edge_case_urls = [
            "https://docs.phaser.io.evil.com/phaser/test",  # Subdomain attack
            "https://evil.docs.phaser.io/phaser/test",  # Subdomain attack
            "https://docs-phaser.io/phaser/test",  # Similar domain
            "https://docs.phaser.io.com/phaser/test",  # Wrong TLD
            "https://docss.phaser.io/phaser/test",  # Typosquatting
            "https://docs.phaser.io@evil.com/phaser/test",  # URL with userinfo
            "https://docs.phaser.io:443/phaser/test",  # Explicit port (not allowed by current validation)
        ]

        for url in invalid_edge_case_urls:
            with pytest.raises(ValidationError) as exc_info:
                DocumentationPage(url=url, title="Test", content="Test content")
            assert "URL must be from allowed domains" in str(exc_info.value)

    def test_title_cleaning_edge_cases(self):
        """Test title cleaning with various edge cases."""
        test_cases = [
            # Single suffix removal (only removes one suffix at a time)
            ("API Reference - Phaser", "API Reference"),
            ("Getting Started | Phaser Documentation", "Getting Started"),
            ("Tutorial :: Phaser Documentation", "Tutorial"),
            # Case sensitivity
            ("Title - phaser", "Title - phaser"),  # Should not match case-sensitive
            ("Title - PHASER", "Title - PHASER"),  # Should not match case-sensitive
            # Partial matches (should not be removed)
            ("Phaser Game Engine", "Phaser Game Engine"),
            ("Documentation for Phaser", "Documentation for Phaser"),
            # Unicode and special characters
            ("Título con acentos - Phaser", "Título con acentos"),
            ("Title with émojis 🎮 - Phaser", "Title with émojis 🎮"),
            # Very long titles
            ("A" * 400 + " - Phaser", "A" * 400),
            # Cases that don't match exact suffixes (so they're not removed)
            ("- Phaser", "- Phaser"),  # Doesn't match " - Phaser" exactly
            (
                "| Phaser Documentation",
                "| Phaser Documentation",
            ),  # Doesn't match " | Phaser Documentation" exactly
            # Multiple spaces and formatting
            ("  Title   with   spaces  - Phaser  ", "Title   with   spaces"),
            # HTML entities (if they somehow get through)
            ("Title &amp; More - Phaser", "Title &amp; More"),
        ]

        for input_title, expected_title in test_cases:
            page = DocumentationPage(
                url="https://docs.phaser.io/phaser/test",
                title=input_title,
                content="Test content",
            )
            assert page.title == expected_title, f"Failed for title: {input_title!r}"

    def test_url_validation_malformed_urls(self):
        """Test URL validation with malformed URLs."""
        # Test URLs that will fail domain validation
        malformed_urls = [
            "https://invalid-domain.com/test",  # Invalid domain
            "http://malicious.com/test",  # Invalid domain
            "ftp://docs.phaser.io/test",  # Invalid scheme
            "javascript:alert('xss')",  # Invalid scheme
            "",  # Empty URL (will fail min_length validation)
        ]

        for url in malformed_urls:
            with pytest.raises(ValidationError):
                DocumentationPage(url=url, title="Test", content="Test content")

    def test_content_type_validation(self):
        """Test content type field validation."""
        valid_content_types = [
            "text/html",
            "text/plain",
            "application/json",
            "text/markdown",
            "application/xml",
        ]

        for content_type in valid_content_types:
            page = DocumentationPage(
                url="https://docs.phaser.io/phaser/test",
                title="Test",
                content="Test content",
                content_type=content_type,
            )
            assert page.content_type == content_type

    def test_last_modified_datetime_handling(self):
        """Test last_modified datetime field handling."""
        from datetime import timezone

        # Test with timezone-aware datetime
        dt_with_tz = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        page = DocumentationPage(
            url="https://docs.phaser.io/phaser/test",
            title="Test",
            content="Test content",
            last_modified=dt_with_tz,
        )
        assert page.last_modified == dt_with_tz

        # Test with naive datetime
        dt_naive = datetime(2024, 1, 15, 10, 30, 0)
        page = DocumentationPage(
            url="https://docs.phaser.io/phaser/test",
            title="Test",
            content="Test content",
            last_modified=dt_naive,
        )
        assert page.last_modified == dt_naive


class TestSearchResult:
    """Test cases for SearchResult model."""

    def test_valid_search_result_creation(self):
        """Test creating a valid SearchResult instance."""
        result = SearchResult(
            rank_order=1,
            url="https://docs.phaser.io/phaser/sprites",
            title="Working with Sprites",
            snippet="Sprites are the basic building blocks of games.",
            relevance_score=0.95,
        )

        assert result.rank_order == 1
        assert result.url == "https://docs.phaser.io/phaser/sprites"
        assert result.title == "Working with Sprites"
        assert result.snippet == "Sprites are the basic building blocks of games."
        assert result.relevance_score == 0.95

    def test_search_result_with_defaults(self):
        """Test creating SearchResult with default values."""
        result = SearchResult(
            rank_order=2,
            url="https://docs.phaser.io/phaser/animations",
            title="Animation System",
        )

        assert result.snippet is None
        assert result.relevance_score is None

    def test_snippet_cleaning(self):
        """Test snippet text cleaning."""
        test_cases = [
            ("  Multiple   spaces   here  ", "Multiple spaces here"),
            ("\n\nNewlines\n\nand\n\ntabs\t\there\n\n", "Newlines and tabs here"),
            ("", None),  # Empty string becomes None
            ("   ", None),  # Whitespace only becomes None
            (None, None),  # None stays None
        ]

        for input_snippet, expected_snippet in test_cases:
            result = SearchResult(
                rank_order=1,
                url="https://docs.phaser.io/phaser/test",
                title="Test",
                snippet=input_snippet,
            )
            assert result.snippet == expected_snippet

    def test_invalid_rank_order(self):
        """Test validation of rank order."""
        invalid_ranks = [0, -1, -10]

        for invalid_rank in invalid_ranks:
            with pytest.raises(ValidationError) as exc_info:
                SearchResult(
                    rank_order=invalid_rank,
                    url="https://docs.phaser.io/phaser/test",
                    title="Test",
                )
            assert "greater than or equal to 1" in str(exc_info.value)

    def test_invalid_relevance_score(self):
        """Test validation of relevance score range."""
        invalid_scores = [-0.1, 1.1, 2.0, -1.0]

        for invalid_score in invalid_scores:
            with pytest.raises(ValidationError) as exc_info:
                SearchResult(
                    rank_order=1,
                    url="https://docs.phaser.io/phaser/test",
                    title="Test",
                    relevance_score=invalid_score,
                )
            error_msg = str(exc_info.value)
            assert (
                "less than or equal to 1" in error_msg
                or "greater than or equal to 0" in error_msg
            )

    def test_valid_relevance_scores(self):
        """Test valid relevance score values."""
        valid_scores = [0.0, 0.5, 1.0, 0.123, 0.999]

        for valid_score in valid_scores:
            result = SearchResult(
                rank_order=1,
                url="https://docs.phaser.io/phaser/test",
                title="Test",
                relevance_score=valid_score,
            )
            assert result.relevance_score == valid_score

    def test_empty_url_validation(self):
        """Test validation of empty URLs in search results."""
        with pytest.raises(ValidationError) as exc_info:
            SearchResult(rank_order=1, url="", title="Test")
        assert "String should have at least 1 character" in str(exc_info.value)

    def test_invalid_url_schemes_search(self):
        """Test validation of URL schemes in search results."""
        invalid_urls = [
            "ftp://docs.phaser.io/test",
            "file:///local/path",
            "javascript:void(0)",
            "://docs.phaser.io/test",  # Empty scheme
        ]

        for invalid_url in invalid_urls:
            with pytest.raises(ValidationError) as exc_info:
                SearchResult(rank_order=1, url=invalid_url, title="Test")
            assert "URL must use http or https scheme" in str(exc_info.value)

    def test_snippet_length_validation(self):
        """Test snippet length validation."""
        long_snippet = "A" * 1001

        with pytest.raises(ValidationError) as exc_info:
            SearchResult(
                rank_order=1,
                url="https://docs.phaser.io/phaser/test",
                title="Test",
                snippet=long_snippet,
            )
        assert "at most 1000 characters" in str(exc_info.value)

    def test_snippet_edge_cases(self):
        """Test snippet handling with various edge cases."""
        # Test with snippet containing only whitespace characters
        result = SearchResult(
            rank_order=1,
            url="https://docs.phaser.io/phaser/test",
            title="Test",
            snippet="\t\n\r   \t\n",  # Only whitespace
        )

        assert result.snippet is None

    def test_snippet_cleaning_various_formats(self):
        """Test snippet cleaning with various input formats."""
        test_cases = [
            # HTML-like content (tags are preserved, only whitespace is normalized)
            ("<p>This is a paragraph</p>", "<p>This is a paragraph</p>"),
            # Multiple line breaks and spaces
            ("Line1\n\n\nLine2\r\n\r\nLine3", "Line1 Line2 Line3"),
            # Mixed whitespace characters
            ("Word1\t\t\tWord2   \r\n   Word3", "Word1 Word2 Word3"),
            # Leading and trailing whitespace
            ("   Content in the middle   ", "Content in the middle"),
            # Special characters and punctuation
            ("Hello, world! How are you?", "Hello, world! How are you?"),
            # Unicode characters
            ("こんにちは world 世界", "こんにちは world 世界"),
            # Numbers and symbols
            ("Version 3.14.0 costs $29.99", "Version 3.14.0 costs $29.99"),
            # Code-like content
            ("function() { return true; }", "function() { return true; }"),
            # URLs in snippets
            (
                "Visit https://example.com for more",
                "Visit https://example.com for more",
            ),
            # Very long content with spaces
            ("A" * 100 + "   " + "B" * 100, "A" * 100 + " " + "B" * 100),
            # Content with quotes
            ("\"This is quoted\" and 'this too'", "\"This is quoted\" and 'this too'"),
            # Empty variations
            ("", None),
            ("   ", None),
            ("\n\n\n", None),
            ("\t\t\t", None),
            ("\r\n\r\n", None),
        ]

        for input_snippet, expected_snippet in test_cases:
            result = SearchResult(
                rank_order=1,
                url="https://docs.phaser.io/phaser/test",
                title="Test",
                snippet=input_snippet,
            )
            assert (
                result.snippet == expected_snippet
            ), f"Failed for snippet: {input_snippet!r}"

    def test_url_validation_edge_cases_search(self):
        """Test URL validation edge cases for SearchResult."""
        # Valid edge case URLs
        valid_urls = [
            "https://docs.phaser.io/phaser/test?query=value",
            "https://docs.phaser.io/phaser/test#anchor",
            "https://docs.phaser.io/phaser/test?a=1&b=2#section",
            "https://phaser.io/examples/v3.70.0/game-objects/sprites",
            "https://www.phaser.io/tutorials/getting-started",
            "http://docs.phaser.io/api/Phaser.Scene",  # HTTP should be allowed
            "https://docs.phaser.io/phaser/test/",  # Trailing slash
            "https://docs.phaser.io:443/phaser/test",  # Explicit HTTPS port
            "http://docs.phaser.io:80/phaser/test",  # Explicit HTTP port
            "https://docs.phaser.io/phaser/test%20encoded",  # URL encoded
        ]

        for url in valid_urls:
            result = SearchResult(
                rank_order=1,
                url=url,
                title="Test",
            )
            assert result.url == url

        # Invalid URLs (malformed or invalid schemes)
        invalid_urls = [
            "ftp://docs.phaser.io/test",  # Invalid scheme
            "javascript:void(0)",  # Invalid scheme
            "",  # Empty URL (will fail min_length validation)
            "not-a-url",  # Not a URL at all
        ]

        for url in invalid_urls:
            with pytest.raises(ValidationError):
                SearchResult(rank_order=1, url=url, title="Test")

    def test_relevance_score_edge_cases(self):
        """Test relevance score validation with edge cases."""
        # Test boundary values
        boundary_scores = [0.0, 1.0, 0.000001, 0.999999]

        for score in boundary_scores:
            result = SearchResult(
                rank_order=1,
                url="https://docs.phaser.io/phaser/test",
                title="Test",
                relevance_score=score,
            )
            assert result.relevance_score == score

        # Test invalid scores
        invalid_scores = [
            -0.000001,  # Just below 0
            1.000001,  # Just above 1
            float("inf"),  # Infinity
            float("-inf"),  # Negative infinity
            float("nan"),  # NaN
            -999.0,  # Very negative
            999.0,  # Very positive
        ]

        for score in invalid_scores:
            with pytest.raises(ValidationError) as exc_info:
                SearchResult(
                    rank_order=1,
                    url="https://docs.phaser.io/phaser/test",
                    title="Test",
                    relevance_score=score,
                )
            error_msg = str(exc_info.value)
            # Check for appropriate error message
            assert any(
                phrase in error_msg
                for phrase in [
                    "less than or equal to 1",
                    "greater than or equal to 0",
                    "ensure this value",
                    "Input should be",
                ]
            )

    def test_rank_order_edge_cases(self):
        """Test rank order validation with edge cases."""
        # Test valid rank orders
        valid_ranks = [1, 2, 10, 100, 1000, 999999]

        for rank in valid_ranks:
            result = SearchResult(
                rank_order=rank,
                url="https://docs.phaser.io/phaser/test",
                title="Test",
            )
            assert result.rank_order == rank

        # Test invalid rank orders
        invalid_ranks = [0, -1, -10, -999]

        for rank in invalid_ranks:
            with pytest.raises(ValidationError) as exc_info:
                SearchResult(
                    rank_order=rank,
                    url="https://docs.phaser.io/phaser/test",
                    title="Test",
                )
            assert "greater than or equal to 1" in str(exc_info.value)

    def test_search_result_title_edge_cases(self):
        """Test SearchResult title validation edge cases."""
        # Test title length limits
        max_length_title = "A" * 500  # Should be valid
        result = SearchResult(
            rank_order=1,
            url="https://docs.phaser.io/phaser/test",
            title=max_length_title,
        )
        assert result.title == max_length_title

        # Test title too long
        too_long_title = "A" * 501
        with pytest.raises(ValidationError) as exc_info:
            SearchResult(
                rank_order=1,
                url="https://docs.phaser.io/phaser/test",
                title=too_long_title,
            )
        assert "at most 500 characters" in str(exc_info.value)

        # Test empty title
        with pytest.raises(ValidationError) as exc_info:
            SearchResult(
                rank_order=1,
                url="https://docs.phaser.io/phaser/test",
                title="",
            )
        assert "at least 1 character" in str(exc_info.value)

    def test_search_result_url_length_validation(self):
        """Test SearchResult URL length validation."""
        # Test maximum valid URL length
        base_url = "https://docs.phaser.io/phaser/"
        max_path = "a" * (2048 - len(base_url))
        max_url = base_url + max_path

        result = SearchResult(
            rank_order=1,
            url=max_url,
            title="Test",
        )
        assert result.url == max_url

        # Test URL too long
        too_long_url = base_url + "a" * (2048 - len(base_url) + 1)
        with pytest.raises(ValidationError) as exc_info:
            SearchResult(
                rank_order=1,
                url=too_long_url,
                title="Test",
            )
        assert "at most 2048 characters" in str(exc_info.value)

    def test_snippet_max_length_validation(self):
        """Test snippet maximum length validation."""
        # Test maximum valid snippet length
        max_snippet = "A" * 1000
        result = SearchResult(
            rank_order=1,
            url="https://docs.phaser.io/phaser/test",
            title="Test",
            snippet=max_snippet,
        )
        assert result.snippet == max_snippet

        # Test snippet too long
        too_long_snippet = "A" * 1001
        with pytest.raises(ValidationError) as exc_info:
            SearchResult(
                rank_order=1,
                url="https://docs.phaser.io/phaser/test",
                title="Test",
                snippet=too_long_snippet,
            )
        assert "at most 1000 characters" in str(exc_info.value)


class TestApiReference:
    """Test cases for ApiReference model."""

    def test_valid_api_reference_creation(self):
        """Test creating a valid ApiReference instance."""
        api_ref = ApiReference(
            class_name="Sprite",
            url="https://docs.phaser.io/api/Phaser.GameObjects.Sprite",
            description="A Sprite Game Object is used to display textures.",
            methods=["setTexture", "setPosition", "destroy"],
            properties=["x", "y", "texture", "visible"],
            examples=[
                "const sprite = this.add.sprite(100, 100, 'player');",
                "sprite.setTexture('enemy');",
            ],
            parent_class="GameObject",
            namespace="Phaser.GameObjects",
        )

        assert api_ref.class_name == "Sprite"
        expected_url = "https://docs.phaser.io/api/Phaser.GameObjects.Sprite"
        assert api_ref.url == expected_url
        expected_desc = "A Sprite Game Object is used to display textures."
        assert api_ref.description == expected_desc
        assert api_ref.methods == ["setTexture", "setPosition", "destroy"]
        assert api_ref.properties == ["x", "y", "texture", "visible"]
        assert len(api_ref.examples) == 2
        assert api_ref.parent_class == "GameObject"
        assert api_ref.namespace == "Phaser.GameObjects"

    def test_api_reference_with_defaults(self):
        """Test creating ApiReference with default values."""
        api_ref = ApiReference(
            class_name="Scene",
            url="https://docs.phaser.io/api/Phaser.Scene",
            description=(
                "The Scene Manager is responsible for creating, processing "
                "and updating all of the Scenes in a Phaser Game instance."
            ),
        )

        assert api_ref.methods == []
        assert api_ref.properties == []
        assert api_ref.examples == []
        assert api_ref.parent_class is None
        assert api_ref.namespace is None

    def test_class_name_validation(self):
        """Test class name validation."""
        valid_names = [
            "Sprite",
            "GameObject",
            "Phaser.Scene",
            "Phaser.GameObjects.Sprite",
            "Scene_Manager",
            "Audio3D",
        ]

        for valid_name in valid_names:
            api_ref = ApiReference(
                class_name=valid_name,
                url="https://docs.phaser.io/api/test",
                description="Test description",
            )
            assert api_ref.class_name == valid_name

    def test_invalid_class_names(self):
        """Test validation of invalid class names."""
        invalid_names = [
            "",
            "   ",
            "Class-Name",  # Hyphen not allowed
            "Class Name",  # Space not allowed
            "Class@Name",  # Special character not allowed
            "Class#Name",  # Hash not allowed
        ]

        for invalid_name in invalid_names:
            with pytest.raises(ValidationError) as exc_info:
                ApiReference(
                    class_name=invalid_name,
                    url="https://docs.phaser.io/api/test",
                    description="Test description",
                )
            error_msg = str(exc_info.value)
            if invalid_name == "":
                assert "String should have at least 1 character" in error_msg
            elif invalid_name.strip():
                assert "Class name contains invalid characters" in error_msg
            else:
                assert "Class name cannot be empty or whitespace only" in error_msg

    def test_api_url_validation(self):
        """Test API URL validation."""
        # Valid API URLs
        valid_urls = [
            "https://docs.phaser.io/api/Phaser.Scene",
            "http://docs.phaser.io/api/Phaser.GameObjects.Sprite",
            "https://docs.phaser.io/api/Phaser.Sound.WebAudioSoundManager",
        ]

        for valid_url in valid_urls:
            api_ref = ApiReference(
                class_name="Test", url=valid_url, description="Test description"
            )
            assert api_ref.url == valid_url

    def test_invalid_api_urls(self):
        """Test validation of invalid API URLs."""
        # URLs that don't contain /api/ path from docs.phaser.io
        invalid_path_urls = [
            "https://docs.phaser.io/phaser/getting-started",
            "https://docs.phaser.io/tutorials/sprites",
        ]

        # URLs with invalid schemes
        invalid_scheme_urls = [
            "ftp://docs.phaser.io/api/test",
            "://docs.phaser.io/api/test",  # Empty scheme
        ]

        for invalid_url in invalid_path_urls:
            with pytest.raises(ValidationError) as exc_info:
                ApiReference(
                    class_name="Test", url=invalid_url, description="Test description"
                )
            assert "URL should be an API reference path" in str(exc_info.value)

        for invalid_url in invalid_scheme_urls:
            with pytest.raises(ValidationError) as exc_info:
                ApiReference(
                    class_name="Test", url=invalid_url, description="Test description"
                )
            assert "URL must use http or https scheme" in str(exc_info.value)

        # Test that phaser.io URLs are accepted (not docs.phaser.io)
        valid_url = "https://phaser.io/examples"
        api_ref = ApiReference(
            class_name="Test", url=valid_url, description="Test description"
        )
        assert api_ref.url == valid_url

    def test_methods_properties_deduplication(self):
        """Test deduplication of methods and properties lists."""
        api_ref = ApiReference(
            class_name="Test",
            url="https://docs.phaser.io/api/test",
            description="Test description",
            methods=["method1", "method2", "method1", "method3", "method2"],
            properties=["prop1", "prop2", "prop1", "prop3"],
        )

        # Should preserve order but remove duplicates
        assert api_ref.methods == ["method1", "method2", "method3"]
        assert api_ref.properties == ["prop1", "prop2", "prop3"]

    def test_methods_properties_cleaning(self):
        """Test cleaning of methods and properties lists."""
        api_ref = ApiReference(
            class_name="Test",
            url="https://docs.phaser.io/api/test",
            description="Test description",
            methods=["  method1  ", "", "method2", "   ", "method3"],
            properties=["prop1", "", "  prop2  ", "prop3"],
        )

        # Should clean whitespace and remove empty items
        assert api_ref.methods == ["method1", "method2", "method3"]
        assert api_ref.properties == ["prop1", "prop2", "prop3"]

    def test_examples_cleaning(self):
        """Test cleaning of code examples."""
        api_ref = ApiReference(
            class_name="Test",
            url="https://docs.phaser.io/api/test",
            description="Test description",
            examples=[
                "  const sprite = new Sprite();  ",
                "",
                "sprite.setPosition(100, 100);",
                "   ",
                "sprite.destroy();",
            ],
        )

        # Should clean whitespace and remove empty examples
        expected_examples = [
            "const sprite = new Sprite();",
            "sprite.setPosition(100, 100);",
            "sprite.destroy();",
        ]
        assert api_ref.examples == expected_examples

    def test_empty_description_validation(self):
        """Test validation of empty description."""
        with pytest.raises(ValidationError) as exc_info:
            ApiReference(
                class_name="Test", url="https://docs.phaser.io/api/test", description=""
            )
        assert "at least 1 character" in str(exc_info.value)

    def test_class_name_length_validation(self):
        """Test class name length validation."""
        long_name = "A" * 201

        with pytest.raises(ValidationError) as exc_info:
            ApiReference(
                class_name=long_name,
                url="https://docs.phaser.io/api/test",
                description="Test description",
            )
        assert "at most 200 characters" in str(exc_info.value)

    def test_parent_class_length_validation(self):
        """Test parent class length validation."""
        long_parent = "A" * 201

        with pytest.raises(ValidationError) as exc_info:
            ApiReference(
                class_name="Test",
                url="https://docs.phaser.io/api/test",
                description="Test description",
                parent_class=long_parent,
            )
        assert "at most 200 characters" in str(exc_info.value)

    def test_namespace_length_validation(self):
        """Test namespace length validation."""
        long_namespace = "A" * 201

        with pytest.raises(ValidationError) as exc_info:
            ApiReference(
                class_name="Test",
                url="https://docs.phaser.io/api/test",
                description="Test description",
                namespace=long_namespace,
            )
        assert "at most 200 characters" in str(exc_info.value)

    def test_empty_lists_handling(self):
        """Test ApiReference with various empty list scenarios."""
        # Test with empty strings in lists (should be filtered out)
        api_ref = ApiReference(
            class_name="Test",
            url="https://docs.phaser.io/api/test",
            description="Test description",
            methods=["method1", "", "method2", "   "],  # Mixed with empty
            properties=["", "prop1", "  "],
            examples=["", "example1", "   "],
        )

        # Should filter out empty and whitespace-only values
        assert api_ref.methods == ["method1", "method2"]
        assert api_ref.properties == ["prop1"]
        assert api_ref.examples == ["example1"]

    def test_class_name_validation_various_formats(self):
        """Test class name validation with various formats."""
        # Test valid class name formats
        valid_class_names = [
            "SimpleClass",
            "Phaser.Scene",
            "Phaser.GameObjects.Sprite",
            "Phaser.Sound.WebAudioSoundManager",
            "Class_With_Underscores",
            "Class123",
            "Audio3D",
            "HTML5AudioSoundManager",
            "A",  # Single character
            "A.B.C.D.E.F",  # Deep namespace
            "Class.With.Numbers123.AndMore",
            "Phaser.Cameras.Scene2D.Camera",
            "Phaser.Physics.Arcade.Body",
        ]

        for class_name in valid_class_names:
            api_ref = ApiReference(
                class_name=class_name,
                url="https://docs.phaser.io/api/test",
                description="Test description",
            )
            assert api_ref.class_name == class_name

        # Test invalid class name formats
        invalid_class_names = [
            "Class-Name",  # Hyphen not allowed
            "Class Name",  # Space not allowed
            "Class@Name",  # @ symbol not allowed
            "Class#Name",  # Hash not allowed
            "Class$Name",  # Dollar sign not allowed
            "Class%Name",  # Percent not allowed
            "Class&Name",  # Ampersand not allowed
            "Class*Name",  # Asterisk not allowed
            "Class+Name",  # Plus not allowed
            "Class=Name",  # Equals not allowed
            "Class[Name]",  # Brackets not allowed
            "Class{Name}",  # Braces not allowed
            "Class(Name)",  # Parentheses not allowed
            "Class<Name>",  # Angle brackets not allowed
            "Class/Name",  # Slash not allowed
            "Class\\Name",  # Backslash not allowed
            "Class|Name",  # Pipe not allowed
            "Class?Name",  # Question mark not allowed
            "Class!Name",  # Exclamation not allowed
            "Class,Name",  # Comma not allowed
            "Class;Name",  # Semicolon not allowed
            "Class:Name",  # Colon not allowed
            'Class"Name',  # Quote not allowed
            "Class'Name",  # Apostrophe not allowed
        ]

        for class_name in invalid_class_names:
            with pytest.raises(ValidationError) as exc_info:
                ApiReference(
                    class_name=class_name,
                    url="https://docs.phaser.io/api/test",
                    description="Test description",
                )
            assert "Class name contains invalid characters" in str(exc_info.value)

    def test_methods_properties_list_validation_edge_cases(self):
        """Test methods and properties list validation with edge cases."""
        # Test with various whitespace scenarios
        api_ref = ApiReference(
            class_name="Test",
            url="https://docs.phaser.io/api/test",
            description="Test description",
            methods=[
                "method1",
                "  method2  ",  # Leading/trailing spaces
                "\tmethod3\t",  # Tabs
                "\nmethod4\n",  # Newlines
                "\r\nmethod5\r\n",  # Carriage returns
                "method6",
                "",  # Empty string
                "   ",  # Only spaces
                "\t\n\r",  # Only whitespace
                "method7",
            ],
            properties=[
                "prop1",
                "  prop2  ",
                "",
                "prop3",
                "\t\t",
                "prop4",
                "   prop5   ",
            ],
        )

        # Should clean and deduplicate
        expected_methods = [
            "method1",
            "method2",
            "method3",
            "method4",
            "method5",
            "method6",
            "method7",
        ]
        expected_properties = ["prop1", "prop2", "prop3", "prop4", "prop5"]

        assert api_ref.methods == expected_methods
        assert api_ref.properties == expected_properties

    def test_methods_properties_deduplication_complex(self):
        """Test complex deduplication scenarios for methods and properties."""
        api_ref = ApiReference(
            class_name="Test",
            url="https://docs.phaser.io/api/test",
            description="Test description",
            methods=[
                "method1",
                "method2",
                "method1",  # Duplicate
                "  method2  ",  # Duplicate with spaces
                "method3",
                "method1",  # Another duplicate
                "method4",
                "method2",  # Another duplicate
                "method5",
            ],
            properties=[
                "prop1",
                "prop2",
                "prop1",  # Duplicate
                "  prop1  ",  # Duplicate with spaces (should be treated as same)
                "prop3",
                "prop2",  # Duplicate
            ],
        )

        # Should preserve order of first occurrence and remove duplicates
        assert api_ref.methods == [
            "method1",
            "method2",
            "method3",
            "method4",
            "method5",
        ]
        assert api_ref.properties == ["prop1", "prop2", "prop3"]

    def test_examples_list_validation_edge_cases(self):
        """Test examples list validation with edge cases."""
        # Test with various code example formats
        examples_input = [
            "const sprite = new Sprite();",
            "",  # Empty example
            "  sprite.setPosition(100, 100);  ",  # With spaces
            "   ",  # Only spaces
            """
            // Multi-line example
            function createSprite() {
                return new Sprite();
            }
            """,  # Multi-line with leading/trailing whitespace
            "\t\tsprite.destroy();\t\t",  # With tabs
            "sprite.update();",
            "",  # Another empty
            "// Final example\nsprite.render();",
        ]

        api_ref = ApiReference(
            class_name="Test",
            url="https://docs.phaser.io/api/test",
            description="Test description",
            examples=examples_input,
        )

        # Should clean and filter out empty examples
        expected_examples = [
            "const sprite = new Sprite();",
            "sprite.setPosition(100, 100);",
            """// Multi-line example
            function createSprite() {
                return new Sprite();
            }""",
            "sprite.destroy();",
            "sprite.update();",
            "// Final example\nsprite.render();",
        ]

        assert len(api_ref.examples) == len(expected_examples)
        for i, example in enumerate(api_ref.examples):
            assert example.strip() == expected_examples[i].strip()

    def test_parent_class_validation_edge_cases(self):
        """Test parent class validation with edge cases."""
        # Test valid parent class names
        valid_parent_classes = [
            "GameObject",
            "Phaser.GameObjects.GameObject",
            "Base_Class",
            "Parent123",
            "A",  # Single character
            None,  # None should be allowed
        ]

        for parent_class in valid_parent_classes:
            api_ref = ApiReference(
                class_name="Test",
                url="https://docs.phaser.io/api/test",
                description="Test description",
                parent_class=parent_class,
            )
            assert api_ref.parent_class == parent_class

        # Test parent class length validation
        long_parent = "A" * 201
        with pytest.raises(ValidationError) as exc_info:
            ApiReference(
                class_name="Test",
                url="https://docs.phaser.io/api/test",
                description="Test description",
                parent_class=long_parent,
            )
        assert "at most 200 characters" in str(exc_info.value)

        # Test maximum valid length
        max_parent = "A" * 200
        api_ref = ApiReference(
            class_name="Test",
            url="https://docs.phaser.io/api/test",
            description="Test description",
            parent_class=max_parent,
        )
        assert api_ref.parent_class == max_parent

    def test_namespace_validation_edge_cases(self):
        """Test namespace validation with edge cases."""
        # Test valid namespace formats
        valid_namespaces = [
            "Phaser",
            "Phaser.GameObjects",
            "Phaser.Physics.Arcade",
            "Phaser.Sound.WebAudio",
            "Custom_Namespace",
            "Namespace123",
            "A",  # Single character
            None,  # None should be allowed
        ]

        for namespace in valid_namespaces:
            api_ref = ApiReference(
                class_name="Test",
                url="https://docs.phaser.io/api/test",
                description="Test description",
                namespace=namespace,
            )
            assert api_ref.namespace == namespace

        # Test namespace length validation
        long_namespace = "A" * 201
        with pytest.raises(ValidationError) as exc_info:
            ApiReference(
                class_name="Test",
                url="https://docs.phaser.io/api/test",
                description="Test description",
                namespace=long_namespace,
            )
        assert "at most 200 characters" in str(exc_info.value)

        # Test maximum valid length
        max_namespace = "A" * 200
        api_ref = ApiReference(
            class_name="Test",
            url="https://docs.phaser.io/api/test",
            description="Test description",
            namespace=max_namespace,
        )
        assert api_ref.namespace == max_namespace

    def test_api_url_validation_comprehensive(self):
        """Test comprehensive API URL validation scenarios."""
        # Test valid API URLs with various patterns
        valid_api_urls = [
            "https://docs.phaser.io/api/Phaser.Scene",
            "https://docs.phaser.io/api/Phaser.GameObjects.Sprite",
            "https://docs.phaser.io/api/Phaser.Physics.Arcade.Body",
            "https://docs.phaser.io/api/Phaser.Sound.WebAudioSoundManager",
            "http://docs.phaser.io/api/Phaser.Cameras.Scene2D.Camera",
            "https://docs.phaser.io/api/Phaser.Input.Keyboard.KeyboardPlugin",
            "https://docs.phaser.io/api/test?param=value",  # With query params
            "https://docs.phaser.io/api/test#section",  # With fragment
        ]

        for url in valid_api_urls:
            api_ref = ApiReference(
                class_name="Test",
                url=url,
                description="Test description",
            )
            assert api_ref.url == url

        # Test URLs from other allowed domains (should not require /api/ path)
        other_domain_urls = [
            "https://phaser.io/examples",
            "https://www.phaser.io/tutorials",
            "https://phaser.io/news",
        ]

        for url in other_domain_urls:
            api_ref = ApiReference(
                class_name="Test",
                url=url,
                description="Test description",
            )
            assert api_ref.url == url

        # Test invalid API URLs (docs.phaser.io without /api/)
        invalid_api_urls = [
            "https://docs.phaser.io/phaser/getting-started",
            "https://docs.phaser.io/tutorials/sprites",
            "https://docs.phaser.io/examples/basic",
        ]

        for url in invalid_api_urls:
            with pytest.raises(ValidationError) as exc_info:
                ApiReference(
                    class_name="Test",
                    url=url,
                    description="Test description",
                )
            assert "URL should be an API reference path" in str(exc_info.value)

    def test_description_validation_edge_cases(self):
        """Test description field validation edge cases."""
        # Test minimum valid description
        min_description = "A"
        api_ref = ApiReference(
            class_name="Test",
            url="https://docs.phaser.io/api/test",
            description=min_description,
        )
        assert api_ref.description == min_description

        # Test very long description
        long_description = "A" * 10000  # Very long but should be valid
        api_ref = ApiReference(
            class_name="Test",
            url="https://docs.phaser.io/api/test",
            description=long_description,
        )
        assert api_ref.description == long_description

        # Test description with various characters
        complex_description = """
        This is a complex description with:
        - Special characters: !@#$%^&*()
        - Unicode: こんにちは 世界
        - Code: `const x = 5;`
        - HTML-like: <tag>content</tag>
        - URLs: https://example.com
        - Newlines and tabs
        """
        api_ref = ApiReference(
            class_name="Test",
            url="https://docs.phaser.io/api/test",
            description=complex_description,
        )
        assert api_ref.description == complex_description


class TestModelSerialization:
    """Tests for model serialization and deserialization."""

    def test_documentation_page_json_serialization(self):
        """Test DocumentationPage JSON serialization."""
        from datetime import datetime, timezone

        # Create a comprehensive DocumentationPage
        page = DocumentationPage(
            url="https://docs.phaser.io/phaser/getting-started",
            title="Getting Started with Phaser",
            content="# Getting Started\n\nThis guide helps you start with Phaser.",
            last_modified=datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc),
            content_type="text/html",
            word_count=10,
        )

        # Test model_dump (JSON serialization)
        page_dict = page.model_dump()
        assert isinstance(page_dict, dict)
        assert page_dict["url"] == "https://docs.phaser.io/phaser/getting-started"
        assert page_dict["title"] == "Getting Started with Phaser"
        assert (
            page_dict["content"]
            == "# Getting Started\n\nThis guide helps you start with Phaser."
        )
        assert page_dict["content_type"] == "text/html"
        assert page_dict["word_count"] == 10
        assert "last_modified" in page_dict

        # Test model_dump_json (JSON string serialization)
        page_json_str = page.model_dump_json()
        assert isinstance(page_json_str, str)
        assert "getting-started" in page_json_str
        assert "Getting Started with Phaser" in page_json_str

        # Test round-trip serialization
        import json

        page_dict_from_json = json.loads(page_json_str)
        reconstructed_page = DocumentationPage(**page_dict_from_json)
        assert reconstructed_page.url == page.url
        assert reconstructed_page.title == page.title
        assert reconstructed_page.content == page.content
        assert reconstructed_page.content_type == page.content_type
        assert reconstructed_page.word_count == page.word_count

    def test_search_result_json_serialization(self):
        """Test SearchResult JSON serialization."""
        # Create a comprehensive SearchResult
        result = SearchResult(
            rank_order=1,
            url="https://docs.phaser.io/phaser/sprites",
            title="Working with Sprites",
            snippet="Sprites are the basic building blocks of games in Phaser.",
            relevance_score=0.95,
        )

        # Test model_dump
        result_dict = result.model_dump()
        assert isinstance(result_dict, dict)
        assert result_dict["rank_order"] == 1
        assert result_dict["url"] == "https://docs.phaser.io/phaser/sprites"
        assert result_dict["title"] == "Working with Sprites"
        assert (
            result_dict["snippet"]
            == "Sprites are the basic building blocks of games in Phaser."
        )
        assert result_dict["relevance_score"] == 0.95

        # Test model_dump_json
        result_json_str = result.model_dump_json()
        assert isinstance(result_json_str, str)
        assert "sprites" in result_json_str
        assert "0.95" in result_json_str

        # Test round-trip serialization
        import json

        result_dict_from_json = json.loads(result_json_str)
        reconstructed_result = SearchResult(**result_dict_from_json)
        assert reconstructed_result.rank_order == result.rank_order
        assert reconstructed_result.url == result.url
        assert reconstructed_result.title == result.title
        assert reconstructed_result.snippet == result.snippet
        assert reconstructed_result.relevance_score == result.relevance_score

    def test_api_reference_json_serialization(self):
        """Test ApiReference JSON serialization."""
        # Create a comprehensive ApiReference
        api_ref = ApiReference(
            class_name="Sprite",
            url="https://docs.phaser.io/api/Phaser.GameObjects.Sprite",
            description="A Sprite Game Object is used to display textures in your game.",
            methods=["setTexture", "setPosition", "destroy", "setVisible"],
            properties=["x", "y", "texture", "visible", "alpha"],
            examples=[
                "const sprite = this.add.sprite(100, 100, 'player');",
                "sprite.setTexture('enemy');",
                "sprite.destroy();",
            ],
            parent_class="GameObject",
            namespace="Phaser.GameObjects",
        )

        # Test model_dump
        api_dict = api_ref.model_dump()
        assert isinstance(api_dict, dict)
        assert api_dict["class_name"] == "Sprite"
        assert api_dict["url"] == "https://docs.phaser.io/api/Phaser.GameObjects.Sprite"
        assert (
            api_dict["description"]
            == "A Sprite Game Object is used to display textures in your game."
        )
        assert api_dict["methods"] == [
            "setTexture",
            "setPosition",
            "destroy",
            "setVisible",
        ]
        assert api_dict["properties"] == ["x", "y", "texture", "visible", "alpha"]
        assert len(api_dict["examples"]) == 3
        assert api_dict["parent_class"] == "GameObject"
        assert api_dict["namespace"] == "Phaser.GameObjects"

        # Test model_dump_json
        api_json_str = api_ref.model_dump_json()
        assert isinstance(api_json_str, str)
        assert "Sprite" in api_json_str
        assert "setTexture" in api_json_str

        # Test round-trip serialization
        import json

        api_dict_from_json = json.loads(api_json_str)
        reconstructed_api = ApiReference(**api_dict_from_json)
        assert reconstructed_api.class_name == api_ref.class_name
        assert reconstructed_api.url == api_ref.url
        assert reconstructed_api.description == api_ref.description
        assert reconstructed_api.methods == api_ref.methods
        assert reconstructed_api.properties == api_ref.properties
        assert reconstructed_api.examples == api_ref.examples
        assert reconstructed_api.parent_class == api_ref.parent_class
        assert reconstructed_api.namespace == api_ref.namespace

    def test_models_from_dict_comprehensive(self):
        """Test creating models from dictionary data with comprehensive scenarios."""
        # Test DocumentationPage from dict with all fields
        page_data = {
            "url": "https://docs.phaser.io/phaser/test",
            "title": "Test Page - Phaser",  # Will be cleaned
            "content": "This is test content with multiple words",
            "last_modified": "2024-01-15T10:30:00Z",
            "content_type": "text/markdown",
            "word_count": 0,  # Will be auto-calculated
        }
        page = DocumentationPage(**page_data)
        assert page.url == page_data["url"]
        assert page.title == "Test Page"  # Cleaned
        assert (
            page.word_count == 7
        )  # Auto-calculated: "This", "is", "test", "content", "with", "multiple", "words"

        # Test DocumentationPage from dict with minimal fields
        minimal_page_data = {
            "url": "https://docs.phaser.io/phaser/minimal",
            "title": "Minimal Page",
            "content": "Minimal content",
        }
        minimal_page = DocumentationPage(**minimal_page_data)
        assert minimal_page.url == minimal_page_data["url"]
        assert minimal_page.content_type == "text/html"  # Default
        assert minimal_page.last_modified is None  # Default

        # Test SearchResult from dict with all fields
        result_data = {
            "rank_order": 5,
            "url": "https://docs.phaser.io/phaser/search-result",
            "title": "Search Result Title",
            "snippet": "  This is a snippet with   extra   spaces  ",  # Will be cleaned
            "relevance_score": 0.75,
        }
        result = SearchResult(**result_data)
        assert result.rank_order == 5
        assert result.snippet == "This is a snippet with extra spaces"  # Cleaned

        # Test SearchResult from dict with minimal fields
        minimal_result_data = {
            "rank_order": 1,
            "url": "https://docs.phaser.io/phaser/minimal-result",
            "title": "Minimal Result",
        }
        minimal_result = SearchResult(**minimal_result_data)
        assert minimal_result.snippet is None  # Default
        assert minimal_result.relevance_score is None  # Default

        # Test ApiReference from dict with all fields
        api_data = {
            "class_name": "  TestClass  ",  # Will be cleaned
            "url": "https://docs.phaser.io/api/TestClass",
            "description": "Test class description",
            "methods": [
                "method1",
                "",
                "method2",
                "  method3  ",
            ],  # Will be cleaned and filtered
            "properties": [
                "prop1",
                "prop2",
                "",
                "  prop3  ",
            ],  # Will be cleaned and filtered
            "examples": [
                "example1",
                "",
                "  example2  ",
            ],  # Will be cleaned and filtered
            "parent_class": "ParentClass",
            "namespace": "Test.Namespace",
        }
        api_ref = ApiReference(**api_data)
        assert api_ref.class_name == "TestClass"  # Cleaned
        assert api_ref.methods == [
            "method1",
            "method2",
            "method3",
        ]  # Cleaned and filtered
        assert api_ref.properties == ["prop1", "prop2", "prop3"]  # Cleaned and filtered
        assert api_ref.examples == ["example1", "example2"]  # Cleaned and filtered

        # Test ApiReference from dict with minimal fields
        minimal_api_data = {
            "class_name": "MinimalClass",
            "url": "https://docs.phaser.io/api/MinimalClass",
            "description": "Minimal class description",
        }
        minimal_api = ApiReference(**minimal_api_data)
        assert minimal_api.methods == []  # Default
        assert minimal_api.properties == []  # Default
        assert minimal_api.examples == []  # Default
        assert minimal_api.parent_class is None  # Default
        assert minimal_api.namespace is None  # Default

    def test_model_validation_during_deserialization(self):
        """Test model validation during deserialization from dictionaries."""
        # Test DocumentationPage validation errors during deserialization
        invalid_page_data = {
            "url": "invalid-url",  # Invalid URL
            "title": "Test Page",
            "content": "Test content",
        }
        with pytest.raises(ValidationError) as exc_info:
            DocumentationPage(**invalid_page_data)
        assert "URL must use http or https scheme" in str(exc_info.value)

        # Test SearchResult validation errors during deserialization
        invalid_result_data = {
            "rank_order": 0,  # Invalid rank (must be >= 1)
            "url": "https://docs.phaser.io/phaser/test",
            "title": "Test Result",
        }
        with pytest.raises(ValidationError) as exc_info:
            SearchResult(**invalid_result_data)
        assert "greater than or equal to 1" in str(exc_info.value)

        # Test ApiReference validation errors during deserialization
        invalid_api_data = {
            "class_name": "Invalid-Class-Name",  # Invalid characters
            "url": "https://docs.phaser.io/api/test",
            "description": "Test description",
        }
        with pytest.raises(ValidationError) as exc_info:
            ApiReference(**invalid_api_data)
        assert "Class name contains invalid characters" in str(exc_info.value)

    def test_model_serialization_with_none_values(self):
        """Test model serialization with None values."""
        # Test DocumentationPage with None last_modified
        page = DocumentationPage(
            url="https://docs.phaser.io/phaser/test",
            title="Test Page",
            content="Test content",
            last_modified=None,
        )
        page_dict = page.model_dump()
        assert page_dict["last_modified"] is None

        # Test SearchResult with None snippet and relevance_score
        result = SearchResult(
            rank_order=1,
            url="https://docs.phaser.io/phaser/test",
            title="Test Result",
            snippet=None,
            relevance_score=None,
        )
        result_dict = result.model_dump()
        assert result_dict["snippet"] is None
        assert result_dict["relevance_score"] is None

        # Test ApiReference with None parent_class and namespace
        api_ref = ApiReference(
            class_name="Test",
            url="https://docs.phaser.io/api/test",
            description="Test description",
            parent_class=None,
            namespace=None,
        )
        api_dict = api_ref.model_dump()
        assert api_dict["parent_class"] is None
        assert api_dict["namespace"] is None

    def test_model_serialization_exclude_fields(self):
        """Test model serialization with field exclusion."""
        # Test excluding specific fields during serialization
        page = DocumentationPage(
            url="https://docs.phaser.io/phaser/test",
            title="Test Page",
            content="Test content",
            word_count=2,
        )

        # Exclude word_count from serialization
        page_dict = page.model_dump(exclude={"word_count"})
        assert "word_count" not in page_dict
        assert "url" in page_dict
        assert "title" in page_dict

        # Exclude multiple fields
        page_dict_minimal = page.model_dump(
            exclude={"word_count", "content_type", "last_modified"}
        )
        assert "word_count" not in page_dict_minimal
        assert "content_type" not in page_dict_minimal
        assert "last_modified" not in page_dict_minimal
        assert "url" in page_dict_minimal

    def test_model_serialization_include_fields(self):
        """Test model serialization with field inclusion."""
        # Test including only specific fields during serialization
        api_ref = ApiReference(
            class_name="Test",
            url="https://docs.phaser.io/api/test",
            description="Test description",
            methods=["method1", "method2"],
            properties=["prop1", "prop2"],
        )

        # Include only basic fields
        api_dict_basic = api_ref.model_dump(
            include={"class_name", "url", "description"}
        )
        assert len(api_dict_basic) == 3
        assert "class_name" in api_dict_basic
        assert "url" in api_dict_basic
        assert "description" in api_dict_basic
        assert "methods" not in api_dict_basic
        assert "properties" not in api_dict_basic

    def test_model_validation_with_extra_fields(self):
        """Test model validation with extra fields in input data."""
        # Test that extra fields are ignored by default
        page_data_with_extra = {
            "url": "https://docs.phaser.io/phaser/test",
            "title": "Test Page",
            "content": "Test content",
            "extra_field": "This should be ignored",
            "another_extra": 123,
        }

        # Should create successfully, ignoring extra fields
        page = DocumentationPage(**page_data_with_extra)
        assert page.url == page_data_with_extra["url"]
        assert page.title == page_data_with_extra["title"]
        assert not hasattr(page, "extra_field")
        assert not hasattr(page, "another_extra")


class TestModelIntegration:
    """Integration tests for model interactions."""

    def test_models_json_serialization(self):
        """Test that all models can be serialized to JSON."""
        # Test DocumentationPage
        page = DocumentationPage(
            url="https://docs.phaser.io/phaser/test",
            title="Test Page",
            content="Test content",
        )
        page_json = page.model_dump()
        assert isinstance(page_json, dict)
        assert page_json["url"] == "https://docs.phaser.io/phaser/test"

        # Test SearchResult
        result = SearchResult(
            rank_order=1, url="https://docs.phaser.io/phaser/test", title="Test Result"
        )
        result_json = result.model_dump()
        assert isinstance(result_json, dict)
        assert result_json["rank_order"] == 1

        # Test ApiReference
        api_ref = ApiReference(
            class_name="Test",
            url="https://docs.phaser.io/api/test",
            description="Test description",
        )
        api_json = api_ref.model_dump()
        assert isinstance(api_json, dict)
        assert api_json["class_name"] == "Test"

    def test_models_from_dict(self):
        """Test creating models from dictionary data."""
        # Test DocumentationPage
        page_data = {
            "url": "https://docs.phaser.io/phaser/test",
            "title": "Test Page",
            "content": "Test content",
            "word_count": 2,
        }
        page = DocumentationPage(**page_data)
        assert page.url == page_data["url"]
        assert page.word_count == 2

        # Test SearchResult
        result_data = {
            "rank_order": 1,
            "url": "https://docs.phaser.io/phaser/test",
            "title": "Test Result",
            "relevance_score": 0.8,
        }
        result = SearchResult(**result_data)
        assert result.rank_order == 1
        assert result.relevance_score == 0.8

        # Test ApiReference
        api_data = {
            "class_name": "Sprite",
            "url": "https://docs.phaser.io/api/Phaser.Sprite",
            "description": "A sprite object",
            "methods": ["setTexture", "destroy"],
            "properties": ["x", "y"],
        }
        api_ref = ApiReference(**api_data)
        assert api_ref.class_name == "Sprite"
        assert len(api_ref.methods) == 2
        assert len(api_ref.properties) == 2

    def test_comprehensive_validation_coverage(self):
        """Test additional validation scenarios for better coverage."""
        # Test ApiReference with lists containing empty strings and whitespace
        api_ref = ApiReference(
            class_name="Test",
            url="https://docs.phaser.io/api/test",
            description="Test description",
            methods=["method1", "", "method2", "   ", "method3"],
            properties=["prop1", "", "prop2", "\t\n", "prop3"],
            examples=["example1", "", "example2", "  \t  ", "example3"],
        )

        # Should filter out empty and whitespace-only values
        assert api_ref.methods == ["method1", "method2", "method3"]
        assert api_ref.properties == ["prop1", "prop2", "prop3"]
        assert api_ref.examples == ["example1", "example2", "example3"]

        # Test edge case with completely empty lists
        api_ref_empty = ApiReference(
            class_name="EmptyTest",
            url="https://docs.phaser.io/api/empty",
            description="Empty test",
            methods=[],
            properties=[],
            examples=[],
        )

        assert api_ref_empty.methods == []
        assert api_ref_empty.properties == []
        assert api_ref_empty.examples == []


class TestEdgeCasesAndErrorHandling:
    """Additional edge case tests for comprehensive coverage."""

    def test_documentation_page_invalid_url_format(self):
        """Test DocumentationPage with completely invalid URL format."""
        with pytest.raises(ValidationError):
            DocumentationPage(
                url="not-a-url-at-all", title="Test", content="Test content"
            )

    def test_search_result_invalid_url_format(self):
        """Test SearchResult with completely invalid URL format."""
        with pytest.raises(ValidationError):
            SearchResult(rank_order=1, url="not-a-url-at-all", title="Test")

    def test_api_reference_invalid_url_format(self):
        """Test ApiReference with completely invalid URL format."""
        with pytest.raises(ValidationError):
            ApiReference(
                class_name="Test",
                url="not-a-url-at-all",
                description="Test description",
            )

    def test_api_reference_non_string_list_items(self):
        """Test ApiReference validation with non-string list items."""
        # Test with non-string values in methods list
        with pytest.raises(ValidationError):
            ApiReference(
                class_name="Test",
                url="https://docs.phaser.io/api/test",
                description="Test description",
                methods=[123, True, None, "validMethod"],  # Non-string values
            )

        # Test with non-string values in properties list
        with pytest.raises(ValidationError):
            ApiReference(
                class_name="Test",
                url="https://docs.phaser.io/api/test",
                description="Test description",
                properties=[123, {}, [], "validProperty"],  # Non-string values
            )

        # Test with non-string values in examples list
        with pytest.raises(ValidationError):
            ApiReference(
                class_name="Test",
                url="https://docs.phaser.io/api/test",
                description="Test description",
                examples=[123, True, {}, "validExample"],  # Non-string values
            )

    def test_api_reference_validation_with_non_string_items(self):
        """Test ApiReference validation with non-string items in lists."""
        # This tests the type validation in Pydantic
        with pytest.raises(ValidationError):
            ApiReference(
                class_name="Test",
                url="https://docs.phaser.io/api/test",
                description="Test description",
                methods=["valid_method", 123, "another_method"],  # Invalid int
            )

    def test_model_field_type_validation(self):
        """Test type validation for model fields."""
        # Test invalid types for various fields
        with pytest.raises(ValidationError):
            DocumentationPage(
                url=123,
                title="Test",
                content="Test content",  # Should be string
            )

        with pytest.raises(ValidationError):
            SearchResult(
                rank_order="not_a_number",  # Should be int
                url="https://docs.phaser.io/test",
                title="Test",
            )

        with pytest.raises(ValidationError):
            ApiReference(
                class_name="Test",
                url="https://docs.phaser.io/api/test",
                description=None,  # Should be string, not None
            )

    def test_boundary_values(self):
        """Test boundary values for numeric fields."""
        # Test minimum valid rank_order
        result = SearchResult(
            rank_order=1,  # Minimum valid value
            url="https://docs.phaser.io/test",
            title="Test",
        )
        assert result.rank_order == 1

        # Test boundary relevance scores
        result_min = SearchResult(
            rank_order=1,
            url="https://docs.phaser.io/test",
            title="Test",
            relevance_score=0.0,  # Minimum valid value
        )
        assert result_min.relevance_score == 0.0

        result_max = SearchResult(
            rank_order=1,
            url="https://docs.phaser.io/test",
            title="Test",
            relevance_score=1.0,  # Maximum valid value
        )
        assert result_max.relevance_score == 1.0

        # Test minimum valid word_count (but will be auto-calculated if 0)
        page = DocumentationPage(
            url="https://docs.phaser.io/test",
            title="Test",
            content="Test",
            word_count=0,  # Will be auto-calculated since it's 0
        )
        assert page.word_count == 1  # Auto-calculated from "Test" content

    def test_unicode_content_handling(self):
        """Test handling of Unicode content in models."""
        # Test with Unicode characters
        unicode_content = "テスト content with 日本語 and émojis 🎮"
        page = DocumentationPage(
            url="https://docs.phaser.io/phaser/test",
            title="Unicode Test",
            content=unicode_content,
        )
        assert page.content == unicode_content

        # Test Unicode in search results
        result = SearchResult(
            rank_order=1,
            url="https://docs.phaser.io/test",
            title="Unicode Test",
            snippet="Snippet with 日本語 characters",
        )
        assert "日本語" in result.snippet

    def test_very_long_valid_content(self):
        """Test with very long but valid content."""
        # Test with long but valid content (under limits)
        long_content = "Word " * 1000  # 5000 characters, under typical limits
        page = DocumentationPage(
            url="https://docs.phaser.io/phaser/test",
            title="Long Content Test",
            content=long_content,
        )
        assert len(page.content) == len(long_content)
        assert page.word_count == 1000  # Should count words correctly

    def test_model_equality_and_hashing(self):
        """Test model equality and hashing behavior."""
        # Test that identical models are equal
        page1 = DocumentationPage(
            url="https://docs.phaser.io/test", title="Test", content="Content"
        )
        page2 = DocumentationPage(
            url="https://docs.phaser.io/test", title="Test", content="Content"
        )
        # Note: Pydantic models are equal if all fields are equal
        assert page1.model_dump() == page2.model_dump()

        # Test that different models are not equal
        page3 = DocumentationPage(
            url="https://docs.phaser.io/different", title="Test", content="Content"
        )
        assert page1.model_dump() != page3.model_dump()

    def test_invalid_type_validation(self):
        """Test validation with invalid types for fields."""
        # Test DocumentationPage with invalid types
        with pytest.raises(ValidationError):
            DocumentationPage(
                url=123,
                title="Test",
                content="Test content",  # Not a string
            )

        with pytest.raises(ValidationError):
            DocumentationPage(
                url="https://docs.phaser.io/phaser/test",
                title=["Not", "a", "string"],  # Not a string
                content="Test content",
            )

        with pytest.raises(ValidationError):
            DocumentationPage(
                url="https://docs.phaser.io/phaser/test",
                title="Test",
                content={"not": "a string"},  # Not a string
                word_count="not an integer",  # Not an integer
            )

    def test_serialization_edge_cases(self):
        """Test serialization edge cases for models."""
        # Test with very long content
        long_content = "A" * 10000
        page = DocumentationPage(
            url="https://docs.phaser.io/phaser/test",
            title="Test Page",
            content=long_content,
        )
        page_json = page.model_dump()
        assert page_json["content"] == long_content
        assert page_json["word_count"] == 1  # One very long "word"

        # Test with special characters in title
        special_title = "Test & Title < with > special & chars"
        page = DocumentationPage(
            url="https://docs.phaser.io/phaser/test",
            title=special_title,
            content="Test content",
        )
        page_json = page.model_dump()
        assert page_json["title"] == special_title

        # Test with Unicode characters
        unicode_content = "テスト コンテンツ 😊 🎮 🕹️"
        page = DocumentationPage(
            url="https://docs.phaser.io/phaser/test",
            title="Unicode Test",
            content=unicode_content,
        )
        page_json = page.model_dump()
        assert page_json["content"] == unicode_content
        assert page_json["word_count"] == 5  # Unicode words counted correctly

    def test_model_round_trip(self):
        """Test model serialization and deserialization round trip."""
        # Create original model
        original = DocumentationPage(
            url="https://docs.phaser.io/phaser/test",
            title="Test Page",
            content="Test content with some words",
            last_modified=datetime(2024, 1, 15, 10, 30, 0),
            content_type="text/markdown",
            word_count=5,
        )

        # Serialize to dict
        data = original.model_dump()

        # Deserialize back to model
        recreated = DocumentationPage(**data)

        # Compare
        assert recreated.url == original.url
        assert recreated.title == original.title
        assert recreated.content == original.content
        assert recreated.last_modified == original.last_modified
        assert recreated.content_type == original.content_type
        assert recreated.word_count == original.word_count

        # Do the same for SearchResult
        original_result = SearchResult(
            rank_order=1,
            url="https://docs.phaser.io/phaser/test",
            title="Test Result",
            snippet="This is a test snippet",
            relevance_score=0.95,
        )

        result_data = original_result.model_dump()
        recreated_result = SearchResult(**result_data)

        assert recreated_result.rank_order == original_result.rank_order
        assert recreated_result.url == original_result.url
        assert recreated_result.title == original_result.title
        assert recreated_result.snippet == original_result.snippet
        assert recreated_result.relevance_score == original_result.relevance_score

        # And for ApiReference
        original_api = ApiReference(
            class_name="TestClass",
            url="https://docs.phaser.io/api/TestClass",
            description="Test API description",
            methods=["method1", "method2"],
            properties=["prop1", "prop2"],
            examples=["example code 1", "example code 2"],
            parent_class="ParentClass",
            namespace="Test.Namespace",
        )

        api_data = original_api.model_dump()
        recreated_api = ApiReference(**api_data)

        assert recreated_api.class_name == original_api.class_name
        assert recreated_api.url == original_api.url
        assert recreated_api.description == original_api.description
        assert recreated_api.methods == original_api.methods
        assert recreated_api.properties == original_api.properties
        assert recreated_api.examples == original_api.examples
        assert recreated_api.parent_class == original_api.parent_class
        assert recreated_api.namespace == original_api.namespace

    def test_url_parsing_exception_handling(self):
        """Test URL parsing exception handling in validators."""
        # Test with extremely malformed URLs that might cause urlparse to fail
        # These are edge cases that could potentially cause urlparse exceptions

        # Test with None (should be caught by empty check first)
        with pytest.raises(ValidationError):
            DocumentationPage(
                url=None,  # type: ignore
                title="Test",
                content="Test content",
            )

        # Test with non-string URL
        with pytest.raises(ValidationError):
            SearchResult(
                rank_order=1,
                url=123,  # type: ignore
                title="Test",
            )

        # Test with non-string URL for ApiReference
        with pytest.raises(ValidationError):
            ApiReference(
                class_name="TestClass",
                url=[],  # type: ignore
                description="Test description",
            )


class TestEmptyUrlValidation:
    """Test empty URL validation for all models."""

    def test_documentation_page_empty_url_validation(self):
        """Test DocumentationPage validation with empty URL."""
        # Test with empty URL
        with pytest.raises(ValidationError):
            DocumentationPage(url="", title="Test Page", content="Test content")

    def test_search_result_empty_url_validation(self):
        """Test SearchResult validation with empty URL."""
        # Test with empty URL
        with pytest.raises(ValidationError):
            SearchResult(rank_order=1, url="", title="Test Result")

    def test_api_reference_empty_url_validation(self):
        """Test ApiReference validation with empty URL."""
        # Test with empty URL
        with pytest.raises(ValidationError):
            ApiReference(class_name="TestClass", url="", description="Test description")
