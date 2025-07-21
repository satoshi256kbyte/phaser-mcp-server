"""HTML parser and Markdown conversion module for Phaser documentation.

This module provides HTML parsing functionality specifically designed for
Phaser documentation structure, with conversion to clean Markdown format
while preserving code blocks and formatting.
"""

import re
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, NavigableString, Tag
from loguru import logger
from markdownify import markdownify as md


class PhaserParseError(Exception):
    """Base exception for Phaser documentation parsing errors."""


class HTMLParseError(PhaserParseError):
    """HTML parsing specific errors."""


class MarkdownConversionError(PhaserParseError):
    """Markdown conversion specific errors."""


class PhaserDocumentParser:
    """Parser for Phaser documentation HTML content.

    This parser is specifically designed to handle Phaser documentation
    structure and convert it to clean, readable Markdown while preserving
    important formatting and code examples.

    Attributes:
        base_url: Base URL for resolving relative links
        preserve_code_blocks: Whether to preserve code block formatting
        max_content_length: Maximum content length to prevent DoS
    """

    # Phaser-specific selectors for content extraction
    CONTENT_SELECTORS = [
        "main",
        ".content",
        ".documentation-content",
        ".api-content",
        ".tutorial-content",
        "article",
        ".main-content",
        ".phaser-content",
        ".docs-content",
        ".guide-content"
    ]

    # Selectors for elements to remove (navigation, ads, etc.)
    REMOVE_SELECTORS = [
        "nav",
        ".navigation",
        ".sidebar",
        ".breadcrumb",
        ".footer",
        ".header",
        ".advertisement",
        ".social-links",
        ".page-navigation",
        ".toc-container",
        "script",
        "style",
        "noscript"
    ]

    # Code block selectors
    CODE_SELECTORS = [
        "pre",
        "code",
        ".code-block",
        ".highlight",
        ".language-javascript",
        ".language-js",
        ".language-typescript",
        ".language-ts",
        ".phaser-code",
        ".example-code",
        ".snippet",
        ".code-sample"
    ]

    # API-specific selectors
    API_SELECTORS = {
        "class_name": [".class-name", ".api-title", "h1"],
        "description": [".description", ".class-description", ".summary"],
        "methods": [".method", ".function", ".api-method"],
        "properties": [".property", ".api-property"],
        "examples": [".example", ".code-example", ".usage-example"]
    }

    def __init__(
        self,
        base_url: str = "https://docs.phaser.io",
        preserve_code_blocks: bool = True,
        max_content_length: int = 1024 * 1024  # 1MB
    ) -> None:
        """Initialize the Phaser document parser.

        Args:
            base_url: Base URL for resolving relative links
            preserve_code_blocks: Whether to preserve code block formatting
            max_content_length: Maximum content length to prevent DoS
        """
        self.base_url = base_url.rstrip("/")
        self.preserve_code_blocks = preserve_code_blocks
        self.max_content_length = max_content_length

        logger.debug(f"Initialized PhaserDocumentParser with base_url: {self.base_url}")

    def parse_html_content(self, html_content: str, url: str = "") -> Dict[str, Any]:
        """Parse HTML content and extract structured information.

        Args:
            html_content: HTML content to parse
            url: Source URL for context and link resolution

        Returns:
            Dictionary containing parsed content information

        Raises:
            HTMLParseError: If HTML parsing fails
        """
        try:
            # Validate input
            self._validate_html_input(html_content)

            # Create soup object
            soup = self._create_soup(html_content)

            # Clean unwanted elements
            self._remove_unwanted_elements(soup)

            # Resolve relative URLs if URL provided
            if url:
                self._resolve_relative_urls(soup, url)

            # Extract main content
            main_content = self._extract_main_content(soup)
            if not main_content:
                raise HTMLParseError("No main content found in HTML")

            # Extract title
            title = self._extract_title(soup)

            # Extract code blocks
            code_blocks = self._extract_code_blocks(main_content)

            # Get clean text content
            text_content = main_content.get_text(separator=" ", strip=True)

            return {
                "title": title,
                "content": main_content,
                "text_content": text_content,
                "code_blocks": code_blocks,
                "soup": soup,
                "url": url
            }

        except HTMLParseError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error parsing HTML: {e}")
            raise HTMLParseError(f"Unexpected parsing error: {e}") from e

    def convert_to_markdown(self, content_input: Union[str, Dict[str, Any]], url: str = "") -> str:
        """Convert HTML content or parsed content to Markdown format.

        Args:
            content_input: Either HTML string or parsed content dictionary
            url: Source URL for context (used when content_input is HTML string)

        Returns:
            Clean Markdown content

        Raises:
            MarkdownConversionError: If conversion fails
        """
        try:
            # Handle both HTML string and parsed content dictionary
            if isinstance(content_input, str):
                # HTML string input - parse it first
                parsed_content = self.parse_html_content(content_input, url)
            elif isinstance(content_input, dict):
                # Already parsed content dictionary
                parsed_content = content_input
            else:
                raise MarkdownConversionError("Invalid input type - expected string or dict")

            if not parsed_content or "content" not in parsed_content:
                raise MarkdownConversionError("Invalid parsed content structure")

            soup = parsed_content["content"]
            if not soup:
                raise MarkdownConversionError("No content to convert")

            # Prepare HTML for optimal Markdown conversion
            prepared_soup = self._prepare_html_for_markdown(soup)

            # Convert to Markdown using markdownify
            markdown_content = md(
                str(prepared_soup),
                heading_style="ATX",  # Use # style headings
                bullets="-",  # Use - for bullet points
                strip=["script", "style", "meta", "link"],
                escape_asterisks=False,
                escape_underscores=False,
                wrap=True,
                wrap_width=80
            )

            if not markdown_content:
                raise MarkdownConversionError("Markdown conversion resulted in empty content")

            # Post-process the Markdown
            cleaned_markdown = self._clean_markdown_content(markdown_content)

            # Fix code block formatting
            cleaned_markdown = self._fix_code_block_formatting(cleaned_markdown)

            # Add title if available
            if parsed_content.get("title"):
                title = parsed_content["title"]
                if not cleaned_markdown.startswith(f"# {title}"):
                    cleaned_markdown = f"# {title}\n\n{cleaned_markdown}"

            logger.debug(f"Successfully converted to Markdown: {len(cleaned_markdown)} characters")
            return cleaned_markdown

        except MarkdownConversionError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during Markdown conversion: {e}")
            raise MarkdownConversionError(f"Conversion failed: {e}") from e

    def format_api_reference_to_markdown(self, api_ref: "ApiReference") -> str:
        """Format API reference object to Markdown.

        Args:
            api_ref: ApiReference object to format

        Returns:
            Formatted Markdown content
        """
        try:
            from .models import ApiReference
            
            if not isinstance(api_ref, ApiReference):
                raise ValueError("Expected ApiReference object")

            markdown_parts = []

            # Add class name as main heading
            if api_ref.class_name:
                markdown_parts.append(f"# {api_ref.class_name}")

            # Add description
            if api_ref.description:
                markdown_parts.append(f"\n{api_ref.description}")

            # Add URL reference
            if api_ref.url:
                markdown_parts.append(f"\n**Reference:** [{api_ref.url}]({api_ref.url})")

            # Add methods section
            if api_ref.methods:
                markdown_parts.append("\n## Methods")
                for method in api_ref.methods:
                    markdown_parts.append(f"- {method}")

            # Add properties section
            if api_ref.properties:
                markdown_parts.append("\n## Properties")
                for prop in api_ref.properties:
                    markdown_parts.append(f"- {prop}")

            # Add examples section
            if api_ref.examples:
                markdown_parts.append("\n## Examples")
                for example in api_ref.examples:
                    markdown_parts.append(f"\n```javascript\n{example}\n```")

            return "\n".join(markdown_parts)

        except Exception as e:
            logger.error(f"Error formatting API reference: {e}")
            return f"# {api_ref.class_name if hasattr(api_ref, 'class_name') else 'API Reference'}\n\nError formatting API reference: {e}"

    def _validate_html_input(self, html_content: str) -> None:
        """Validate HTML input for security and size constraints."""
        if not html_content:
            raise HTMLParseError("HTML content cannot be empty")

        if not isinstance(html_content, str):
            raise HTMLParseError("HTML content must be a string")

        if len(html_content) > self.max_content_length:
            raise HTMLParseError(
                f"HTML content too large: {len(html_content)} bytes "
                f"(max: {self.max_content_length})"
            )

    def _create_soup(self, html_content: str) -> BeautifulSoup:
        """Create BeautifulSoup object with proper parser configuration."""
        try:
            soup = BeautifulSoup(html_content, "html.parser")
            if not soup:
                raise HTMLParseError("Failed to parse HTML content")
            return soup
        except Exception as e:
            logger.error(f"HTML parsing failed: {e}")
            raise HTMLParseError(f"HTML parsing failed: {e}") from e

    def _remove_unwanted_elements(self, soup: BeautifulSoup) -> None:
        """Remove unwanted elements from the parsed HTML."""
        for selector in self.REMOVE_SELECTORS:
            for element in soup.select(selector):
                element.decompose()

    def _extract_main_content(self, soup: BeautifulSoup) -> Tag | None:
        """Extract the main content area from the HTML."""
        for selector in self.CONTENT_SELECTORS:
            content = soup.select_one(selector)
            if content and content.get_text(strip=True):
                logger.debug(f"Found main content using selector: {selector}")
                return content

        body = soup.find("body")
        if body:
            logger.debug("Using body as main content (fallback)")
            return body

        logger.warning("No main content area found, using entire document")
        return soup

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title from HTML."""
        title_selectors = ["h1", ".page-title", ".api-title", ".class-name", "title"]

        for selector in title_selectors:
            title_element = soup.select_one(selector)
            if title_element:
                title = title_element.get_text(strip=True)
                if title:
                    title = self._clean_title(title)
                    logger.debug(f"Extracted title using {selector}: {title}")
                    return title

        return "Phaser Documentation"

    def _clean_title(self, title: str) -> str:
        """Clean and normalize page title."""
        if not title:
            return "Phaser Documentation"

        suffixes_to_remove = [
            " - Phaser",
            " | Phaser Documentation",
            " :: Phaser Documentation",
            " - Phaser 3 Documentation",
            " | Phaser 3"
        ]

        cleaned = title.strip()
        for suffix in suffixes_to_remove:
            if cleaned.endswith(suffix):
                cleaned = cleaned[:-len(suffix)].strip()

        cleaned = re.sub(r'\s+', ' ', cleaned)
        return cleaned if cleaned else "Phaser Documentation"

    def _resolve_relative_urls(self, soup: BeautifulSoup, base_url: str) -> None:
        """Resolve relative URLs to absolute URLs."""
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if href and not href.startswith(("http://", "https://", "mailto:", "#")):
                absolute_url = urljoin(base_url, href)
                link["href"] = absolute_url

        for img in soup.find_all("img", src=True):
            src = img["src"]
            if src and not src.startswith(("http://", "https://", "data:")):
                absolute_url = urljoin(base_url, src)
                img["src"] = absolute_url

    def _extract_code_blocks(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract code blocks with metadata."""
        code_blocks = []

        for selector in self.CODE_SELECTORS:
            for element in soup.select(selector):
                code_text = element.get_text()
                if code_text.strip():
                    language = self._detect_code_language(element)
                    
                    code_blocks.append({
                        "content": code_text.strip(),
                        "language": language,
                        "element": element,
                        "context": self._get_code_context(element)
                    })

        logger.debug(f"Extracted {len(code_blocks)} code blocks")
        return code_blocks

    def _detect_code_language(self, element: Tag) -> str:
        """Detect programming language from code element."""
        classes = element.get("class", [])
        for class_name in classes:
            if isinstance(class_name, str):
                class_lower = class_name.lower()
                if "javascript" in class_lower or "js" in class_lower:
                    return "javascript"
                elif "typescript" in class_lower or "ts" in class_lower:
                    return "typescript"
                elif "html" in class_lower:
                    return "html"
                elif "css" in class_lower:
                    return "css"
                elif "json" in class_lower:
                    return "json"

        return "javascript"  # Default for Phaser documentation

    def _get_code_context(self, element: Tag) -> str:
        """Get context information for a code block."""
        context_elements = []

        parent = element.parent
        if parent:
            current = parent.previous_sibling
            while current and len(context_elements) < 3:
                if isinstance(current, Tag):
                    if current.name in ["h1", "h2", "h3", "h4", "h5", "h6"]:
                        context_elements.append(current.get_text(strip=True))
                        break
                    elif current.name in ["p", "div"] and current.get_text(strip=True):
                        text = current.get_text(strip=True)
                        if len(text) < 200:
                            context_elements.append(text)
                current = current.previous_sibling

        return " | ".join(reversed(context_elements)) if context_elements else ""

    def _prepare_html_for_markdown(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Prepare HTML for optimal Markdown conversion."""
        prepared_soup = BeautifulSoup(str(soup), "html.parser")

        for code_element in prepared_soup.find_all(["pre", "code"]):
            if not code_element.get("class"):
                language = self._detect_code_language(code_element)
                code_element["class"] = [f"language-{language}"]

        return prepared_soup

    def _clean_markdown_content(self, content: str) -> str:
        """Clean and normalize Markdown content."""
        if not content:
            return ""

        # Remove excessive whitespace
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        content = re.sub(r'[ \t]+', ' ', content)

        # Fix heading spacing
        content = re.sub(r'\n(#{1,6})', r'\n\n\1', content)
        content = re.sub(r'(#{1,6}[^\n]*)\n([^\n#])', r'\1\n\n\2', content)

        # Fix list formatting
        content = re.sub(r'\n(\s*[-*+])', r'\n\n\1', content)

        return content.strip()

    def _fix_code_block_formatting(self, content: str) -> str:
        """Fix code block formatting in Markdown."""
        # Fix inline code that should be code blocks
        content = re.sub(
            r'`([^`\n]*\n[^`]*)`',
            r'```\n\1\n```',
            content,
            flags=re.MULTILINE
        )

        # Ensure code blocks have proper language tags
        def add_language_to_code_block(match):
            code_content = match.group(1)
            if any(keyword in code_content.lower() for keyword in ['function', 'var', 'let', 'const', 'class']):
                return f'```javascript\n{code_content}\n```'
            elif '<' in code_content and '>' in code_content:
                return f'```html\n{code_content}\n```'
            else:
                return f'```javascript\n{code_content}\n```'

        content = re.sub(
            r'```\n([^`]+)\n```',
            add_language_to_code_block,
            content,
            flags=re.MULTILINE | re.DOTALL
        )

        return content


# Export the parser class
__all__ = ["PhaserDocumentParser"]