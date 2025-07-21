"""Pydantic data models for Phaser MCP Server.

This module defines the data models used throughout the Phaser MCP Server
for representing documentation pages, search results, and API references.
All models include comprehensive validation and type hints.
"""

from datetime import datetime
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator, model_validator


class DocumentationPage(BaseModel):
    r"""Represents a Phaser documentation page.

    This model encapsulates all information about a documentation page
    including its URL, title, content, and metadata.

    Attributes:
        url: The full URL of the documentation page
        title: The page title extracted from HTML
        content: The page content converted to Markdown format
        last_modified: Optional timestamp of last modification
        content_type: MIME type of the original content (default: text/html)
        word_count: Number of words in the content

    Example:
        >>> page = DocumentationPage(
        ...     url="https://docs.phaser.io/phaser/getting-started",
        ...     title="Getting Started with Phaser",
        ...     content="# Getting Started\\n\\nThis guide will help you...",
        ...     word_count=150
        ... )
    """

    url: str = Field(
        ...,
        description="Full URL of the documentation page",
        min_length=1,
        max_length=2048
    )

    title: str = Field(
        ...,
        description="Page title extracted from HTML",
        min_length=1,
        max_length=500
    )

    content: str = Field(
        ...,
        description="Page content converted to Markdown format",
        min_length=1
    )

    last_modified: datetime | None = Field(
        default=None,
        description="Timestamp of last modification"
    )

    content_type: str = Field(
        default="text/html",
        description="MIME type of the original content"
    )

    word_count: int = Field(
        default=0,
        description="Number of words in the content",
        ge=0
    )

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        """Validate that the URL is a valid Phaser documentation URL.

        Args:
            v: The URL string to validate

        Returns:
            The validated URL string

        Raises:
            ValueError: If the URL is invalid or not from allowed domains
        """
        if not v:
            raise ValueError("URL cannot be empty")

        try:
            parsed = urlparse(v)
        except Exception as e:
            raise ValueError(f"Invalid URL format: {e}") from e

        # Check for valid scheme
        if parsed.scheme not in ["http", "https"]:
            raise ValueError("URL must use http or https scheme")

        # Check for allowed Phaser domains
        allowed_domains = [
            "docs.phaser.io",
            "phaser.io",
            "www.phaser.io"
        ]

        if parsed.netloc not in allowed_domains:
            msg = f"URL must be from allowed domains: {allowed_domains}"
            raise ValueError(msg)

        return v

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate and clean the page title.

        Args:
            v: The title string to validate

        Returns:
            The cleaned title string
        """
        if not v or not v.strip():
            raise ValueError("Title cannot be empty or whitespace only")

        # Clean up common title artifacts
        cleaned = v.strip()

        # Remove common suffixes
        suffixes_to_remove = [
            " - Phaser",
            " | Phaser Documentation",
            " :: Phaser Documentation"
        ]

        for suffix in suffixes_to_remove:
            if cleaned.endswith(suffix):
                cleaned = cleaned[:-len(suffix)].strip()

        return cleaned

    @model_validator(mode="after")
    def calculate_word_count(self) -> "DocumentationPage":
        """Calculate word count from content if not provided."""
        if self.word_count == 0 and self.content:
            # Simple word count calculation
            words = self.content.split()
            self.word_count = len(words)
        return self


class SearchResult(BaseModel):
    """Represents a search result from Phaser documentation.

    This model encapsulates search result information including
    ranking, URL, title, and content snippet.

    Attributes:
        rank_order: The ranking position of this result (1-based)
        url: The URL of the found page
        title: The title of the found page
        snippet: Optional content snippet showing search context
        relevance_score: Optional relevance score (0.0 to 1.0)

    Example:
        >>> result = SearchResult(
        ...     rank_order=1,
        ...     url="https://docs.phaser.io/phaser/sprites",
        ...     title="Working with Sprites",
        ...     snippet="Sprites are the basic building blocks...",
        ...     relevance_score=0.95
        ... )
    """

    rank_order: int = Field(
        ...,
        description="Ranking position of this result (1-based)",
        ge=1
    )

    url: str = Field(
        ...,
        description="URL of the found page",
        min_length=1,
        max_length=2048
    )

    title: str = Field(
        ...,
        description="Title of the found page",
        min_length=1,
        max_length=500
    )

    snippet: str | None = Field(
        default=None,
        description="Content snippet showing search context",
        max_length=1000
    )

    relevance_score: float | None = Field(
        default=None,
        description="Relevance score between 0.0 and 1.0",
        ge=0.0,
        le=1.0
    )

    @field_validator("url")
    @classmethod
    def validate_search_url(cls, v: str) -> str:
        """Validate that the search result URL is valid.

        Args:
            v: The URL string to validate

        Returns:
            The validated URL string

        Raises:
            ValueError: If the URL is invalid
        """
        if not v:
            raise ValueError("Search result URL cannot be empty")

        try:
            parsed = urlparse(v)
        except Exception as e:
            raise ValueError(f"Invalid URL format: {e}") from e

        if parsed.scheme not in ["http", "https"]:
            raise ValueError("URL must use http or https scheme")

        return v

    @field_validator("snippet")
    @classmethod
    def validate_snippet(cls, v: str | None) -> str | None:
        """Validate and clean the content snippet.

        Args:
            v: The snippet string to validate

        Returns:
            The cleaned snippet string or None
        """
        if v is None:
            return None

        # Clean up whitespace and normalize
        cleaned = " ".join(v.split())

        # Return None if empty after cleaning
        return cleaned if cleaned else None


class ApiReference(BaseModel):
    """Represents a Phaser API reference entry.

    This model encapsulates API documentation information including
    class details, methods, properties, and usage examples.

    Attributes:
        class_name: The name of the API class or namespace
        url: The URL of the API reference page
        description: Description of the class or API
        methods: List of method names available in this class
        properties: List of property names available in this class
        examples: List of code examples demonstrating usage
        parent_class: Optional parent class name for inheritance
        namespace: Optional namespace this class belongs to

    Example:
        >>> api_ref = ApiReference(
        ...     class_name="Sprite",
        ...     url="https://docs.phaser.io/api/Phaser.GameObjects.Sprite",
        ...     description="A Sprite Game Object",
        ...     methods=["setTexture", "setPosition", "destroy"],
        ...     properties=["x", "y", "texture"],
        ...     namespace="Phaser.GameObjects"
        ... )
    """

    class_name: str = Field(
        ...,
        description="Name of the API class or namespace",
        min_length=1,
        max_length=200
    )

    url: str = Field(
        ...,
        description="URL of the API reference page",
        min_length=1,
        max_length=2048
    )

    description: str = Field(
        ...,
        description="Description of the class or API",
        min_length=1
    )

    methods: list[str] = Field(
        default_factory=list,
        description="List of method names available in this class"
    )

    properties: list[str] = Field(
        default_factory=list,
        description="List of property names available in this class"
    )

    examples: list[str] = Field(
        default_factory=list,
        description="List of code examples demonstrating usage"
    )

    parent_class: str | None = Field(
        default=None,
        description="Parent class name for inheritance",
        max_length=200
    )

    namespace: str | None = Field(
        default=None,
        description="Namespace this class belongs to",
        max_length=200
    )

    @field_validator("class_name")
    @classmethod
    def validate_class_name(cls, v: str) -> str:
        """Validate the API class name.

        Args:
            v: The class name to validate

        Returns:
            The validated class name

        Raises:
            ValueError: If the class name is invalid
        """
        if not v or not v.strip():
            raise ValueError("Class name cannot be empty or whitespace only")

        cleaned = v.strip()

        # Basic validation for valid identifier characters
        if not all(c.isalnum() or c in "._" for c in cleaned):
            raise ValueError("Class name contains invalid characters")

        return cleaned

    @field_validator("url")
    @classmethod
    def validate_api_url(cls, v: str) -> str:
        """Validate that the API reference URL is valid.

        Args:
            v: The URL string to validate

        Returns:
            The validated URL string

        Raises:
            ValueError: If the URL is invalid
        """
        if not v:
            raise ValueError("API reference URL cannot be empty")

        try:
            parsed = urlparse(v)
        except Exception as e:
            raise ValueError(f"Invalid URL format: {e}") from e

        if parsed.scheme not in ["http", "https"]:
            raise ValueError("URL must use http or https scheme")

        # Validate that it's likely an API reference URL
        if parsed.netloc == "docs.phaser.io" and "/api/" not in parsed.path:
            raise ValueError("URL should be an API reference path")

        return v

    @field_validator("methods", "properties")
    @classmethod
    def validate_string_lists(cls, v: list[str]) -> list[str]:
        """Validate lists of method/property names.

        Args:
            v: List of strings to validate

        Returns:
            The validated list with cleaned strings
        """
        if not v:
            return []

        # Clean and validate each item
        cleaned_items = []
        for item in v:
            if isinstance(item, str) and item.strip():
                cleaned_items.append(item.strip())

        # Remove duplicates while preserving order
        seen = set()
        result = []
        for item in cleaned_items:
            if item not in seen:
                seen.add(item)
                result.append(item)

        return result

    @field_validator("examples")
    @classmethod
    def validate_examples(cls, v: list[str]) -> list[str]:
        """Validate code examples.

        Args:
            v: List of code example strings

        Returns:
            The validated list of examples
        """
        if not v:
            return []

        # Clean and validate each example
        cleaned_examples = []
        for example in v:
            if isinstance(example, str) and example.strip():
                # Normalize whitespace but preserve code structure
                cleaned = example.strip()
                if cleaned:
                    cleaned_examples.append(cleaned)

        return cleaned_examples


# Export all models
__all__ = [
    "DocumentationPage",
    "SearchResult",
    "ApiReference"
]
