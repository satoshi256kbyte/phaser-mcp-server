"""HTML parser and Markdown conversion module for Phaser documentation.

This module provides HTML parsing functionality specifically designed for
Phaser documentation structure, with conversion to clean Markdown format
while preserving code blocks and formatting.
"""

import re
from re import Match
from typing import Any, TypeVar, cast
from urllib.parse import urljoin

from bs4 import BeautifulSoup, NavigableString, PageElement, Tag
from loguru import logger
from markdownify import markdownify as md

from .models import ApiReference

# Type variables and common types
T = TypeVar("T")
TagOrElement = Tag | PageElement | NavigableString
TagOrSoup = Tag | BeautifulSoup
# More specific type aliases for better type safety
ContentDict = dict[str, str | list[dict[str, str]]]
CodeBlock = dict[str, Any]

# Suppress specific pyright warnings for BeautifulSoup usage
# These suppressions are necessary due to limitations in BeautifulSoup type stubs
# reportUnknownMemberType: BeautifulSoup's get_text() method has partially
# unknown types
# reportUnnecessaryIsInstance: Some isinstance checks are flagged as
# unnecessary but are needed for runtime safety
# pyright: reportUnknownMemberType=false
# pyright: reportUnnecessaryIsInstance=false


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
        ".guide-content",
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
        "noscript",
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
        ".code-sample",
    ]

    # API-specific selectors
    API_SELECTORS = {
        "class_name": [".class-name", ".api-title", "h1"],
        "description": [".description", ".class-description", ".summary"],
        "methods": [".method", ".function", ".api-method"],
        "properties": [".property", ".api-property"],
        "examples": [".example", ".code-example", ".usage-example"],
    }

    def __init__(
        self,
        base_url: str = "https://docs.phaser.io",
        preserve_code_blocks: bool = True,
        max_content_length: int = 1024 * 1024,  # 1MB
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

    def parse_html_content(self, html_content: str, url: str = "") -> dict[str, Any]:
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

            # Extract Phaser-specific content
            phaser_content: ContentDict = {
                "game_objects": [],
                "scenes": [],
                "physics": [],
                "input": [],
                "input_handlers": [],
                "animations": [],
                "code_blocks": [],
                "examples": [],
                "tutorials": [],
                "raw_content": "",
            }

            # Look for Phaser-specific patterns in code blocks
            phaser_patterns = [
                "Phaser.Game",
                "this.add",
                "this.load",
                "this.scene",
                "this.physics",
                "this.anims",
                "this.input",
                "this.cameras",
                "this.tweens",
                "this.sound",
                "Phaser.Scene",
                "Phaser.GameObjects",
                "Phaser.Physics",
                "Phaser.Input",
                "Phaser.Animations",
            ]

            for block in code_blocks:
                code_text = block["content"]
                if any(pattern in code_text for pattern in phaser_patterns):
                    # Use proper type assertion for better type safety
                    code_blocks_list = phaser_content["code_blocks"]
                    assert isinstance(code_blocks_list, list)
                    code_blocks_list.append(block)

                    # Categorize by content with improved type handling
                    if "this.add" in code_text or "Phaser.GameObjects" in code_text:
                        game_objects_list = phaser_content["game_objects"]
                        assert isinstance(game_objects_list, list)
                        game_objects_list.append(block)
                    if "this.scene" in code_text or "Phaser.Scene" in code_text:
                        scenes_list = phaser_content["scenes"]
                        assert isinstance(scenes_list, list)
                        scenes_list.append(block)
                    if "this.physics" in code_text or "Phaser.Physics" in code_text:
                        physics_list = phaser_content["physics"]
                        assert isinstance(physics_list, list)
                        physics_list.append(block)
                    if "this.input" in code_text or "Phaser.Input" in code_text:
                        input_list = phaser_content["input"]
                        assert isinstance(input_list, list)
                        input_list.append(block)
                    if (
                        "pointerdown" in code_text
                        or "click" in code_text.lower()
                        or "touch" in code_text.lower()
                        or "setInteractive" in code_text
                    ):
                        input_handlers_list = phaser_content["input_handlers"]
                        assert isinstance(input_handlers_list, list)
                        input_handlers_list.append(block)
                    if "this.anims" in code_text or "Phaser.Animations" in code_text:
                        animations_list = phaser_content["animations"]
                        assert isinstance(animations_list, list)
                        animations_list.append(block)

                    # Add to examples if it looks like a complete code example
                    if len(code_text.strip().split("\n")) > 3:
                        examples_list = phaser_content["examples"]
                        assert isinstance(examples_list, list)
                        examples_list.append(block)

                    # Check for tutorial context
                    context = block.get("context", "")
                    if (
                        "tutorial" in code_text.lower()
                        or "guide" in code_text.lower()
                        or "tutorial" in context.lower()
                        or "guide" in context.lower()
                    ):
                        tutorials_list = phaser_content["tutorials"]
                        assert isinstance(tutorials_list, list)
                        tutorials_list.append(block)

            # Get clean text content with proper type handling
            # main_content is guaranteed to be not None due to the check above
            text_content = main_content.get_text(separator=" ", strip=True)

            return {
                "title": title,
                "content": main_content,
                "text_content": text_content,
                "code_blocks": code_blocks,
                "phaser_content": phaser_content,
                "soup": soup,
                "url": url,
            }

        except HTMLParseError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error parsing HTML: {e}")
            raise HTMLParseError(f"Unexpected parsing error: {e}") from e

    def convert_to_markdown(
        self, content_input: str | dict[str, Any], url: str = ""
    ) -> str:
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
                raise MarkdownConversionError(
                    "Invalid input type - expected string or dict"
                )

            if not parsed_content or "content" not in parsed_content:
                raise MarkdownConversionError("Invalid parsed content structure")

            soup = parsed_content["content"]
            if not soup:
                raise MarkdownConversionError("No content to convert")

            # Prepare HTML for optimal Markdown conversion
            prepared_soup = self._prepare_html_for_markdown(soup)

            # Convert to Markdown using markdownify with explicit type annotations
            html_content: str = str(prepared_soup)
            markdown_content: str = md(
                html_content,
                heading_style="ATX",  # Use # style headings
                bullets="-",  # Use - for bullet points
                strip=["script", "style", "meta", "link"],
                escape_asterisks=False,
                escape_underscores=False,
                wrap=True,
                wrap_width=80,
            )

            if not markdown_content:
                # Return empty string instead of raising an error
                return ""

            # Post-process the Markdown
            cleaned_markdown = self._clean_markdown_content(markdown_content)

            # Fix code block formatting
            cleaned_markdown = self._fix_code_block_formatting(cleaned_markdown)

            # Add title if available
            if parsed_content.get("title"):
                title = parsed_content["title"]
                if not cleaned_markdown.startswith(f"# {title}"):
                    cleaned_markdown = f"# {title}\n\n{cleaned_markdown}"

            logger.debug(
                f"Successfully converted to Markdown: {len(cleaned_markdown)} chars"
            )
            return cleaned_markdown

        except MarkdownConversionError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error during Markdown conversion: {e}")
            raise MarkdownConversionError(f"Conversion failed: {e}") from e

    def extract_api_information(self, soup: BeautifulSoup) -> dict[str, Any]:
        """Extract API information from HTML.

        Args:
            soup: BeautifulSoup object containing API documentation

        Returns:
            Dictionary with API information (class_name, description, methods,
            properties, examples)

        Raises:
            HTMLParseError: If API information extraction fails
        """
        try:
            api_info: dict[str, str | list[str]] = {
                "class_name": "",
                "description": "",
                "methods": [],
                "properties": [],
                "examples": [],
            }

            # Extract class name with improved type handling
            for selector in self.API_SELECTORS["class_name"]:
                element = soup.select_one(selector)
                if element is not None:
                    # select_one returns Tag or None, so we can safely access get_text
                    text = element.get_text(strip=True)
                    if text:
                        api_info["class_name"] = text
                        break

            # Extract description with improved type handling
            for selector in self.API_SELECTORS["description"]:
                element = soup.select_one(selector)
                if element is not None:
                    # select_one returns Tag or None, so we can safely access get_text
                    text = element.get_text(strip=True)
                    if text:
                        api_info["description"] = text
                        break

            # Extract methods with improved type handling
            methods_list = api_info["methods"]
            assert isinstance(methods_list, list)
            for selector in self.API_SELECTORS["methods"]:
                for element in soup.select(selector):
                    # soup.select returns list[Tag], so element is always Tag
                    method_name = element.get_text(strip=True)
                    if method_name and method_name not in methods_list:
                        methods_list.append(method_name)

            # Extract properties with improved type handling
            properties_list = api_info["properties"]
            assert isinstance(properties_list, list)
            for selector in self.API_SELECTORS["properties"]:
                for element in soup.select(selector):
                    # soup.select returns list[Tag], so element is always Tag
                    prop_name = element.get_text(strip=True)
                    if prop_name and prop_name not in properties_list:
                        properties_list.append(prop_name)

            # Extract examples with improved type handling
            examples_list = api_info["examples"]
            assert isinstance(examples_list, list)
            for selector in self.API_SELECTORS["examples"]:
                for element in soup.select(selector):
                    # soup.select returns list[Tag], so element is always Tag
                    # First try to find code element
                    code_element = element.find("code")
                    if code_element is not None:
                        # find returns Tag or None, so we can safely access get_text
                        example_code = code_element.get_text(strip=True)
                        if example_code and example_code not in examples_list:
                            examples_list.append(example_code)
                    else:
                        # If no code element, use the element's text directly
                        example_text = element.get_text(strip=True)
                        if example_text and example_text not in examples_list:
                            examples_list.append(example_text)

            # If no examples found, try to find code blocks that might be examples
            if not examples_list:
                for code in soup.find_all(["pre", "code"]):
                    # find_all returns ResultSet[Tag], so code is always Tag
                    code_text = code.get_text(strip=True)
                    # Look for any substantial code block as an example
                    if (
                        code_text
                        and len(code_text.strip().split("\n")) > 1
                        and (
                            "=" in code_text
                            or "(" in code_text
                            or "new " in code_text
                            or "this." in code_text
                            or "function" in code_text
                        )
                    ):
                        examples_list.append(code_text)

            logger.debug(f"Extracted API information: {api_info['class_name']}")
            return api_info

        except Exception as e:
            logger.error(f"Error extracting API information: {e}")
            raise HTMLParseError(f"Failed to extract API information: {e}") from e

    def format_api_reference_to_markdown(self, api_ref: "ApiReference") -> str:
        """Format API reference object to Markdown.

        Args:
            api_ref: ApiReference object to format

        Returns:
            Formatted Markdown content
        """
        try:
            # ApiReference already imported at module level

            # Type check for ApiReference - this is a runtime validation
            if not hasattr(api_ref, "class_name"):
                raise ValueError("Expected ApiReference object")

            markdown_parts: list[str] = []

            # Add class name as main heading
            if api_ref.class_name:
                markdown_parts.append(f"# {api_ref.class_name}")

            # Add description
            if api_ref.description:
                markdown_parts.append(f"\n{api_ref.description}")

            # Add URL reference
            if api_ref.url:
                markdown_parts.append(
                    f"\n**Reference:** [{api_ref.url}]({api_ref.url})"
                )

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
            return (
                f"# {api_ref.class_name if hasattr(api_ref, 'class_name') else 'API'}"
                f"\n\n"
                f"Error formatting API reference: {e}"
            )

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
                if hasattr(element, "decompose"):
                    element.decompose()

    def _extract_main_content(self, soup: BeautifulSoup) -> Tag | None:
        """Extract the main content area from the HTML."""
        for selector in self.CONTENT_SELECTORS:
            content = soup.select_one(selector)
            if content is not None and content.get_text(strip=True):
                # select_one returns Tag or None, so content is Tag here
                logger.debug(f"Found main content using selector: {selector}")
                return content

        body = soup.find("body")
        if body is not None:
            # find returns Tag or None, so body is Tag here
            logger.debug("Using body as main content (fallback)")
            return body

        logger.warning("No main content area found, using entire document")
        # Create a wrapper tag containing all soup contents
        wrapper = soup.new_tag("div")
        for element in soup.contents:
            if hasattr(element, "extract"):
                wrapper.append(element.extract())
        return wrapper

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title from HTML."""
        title_selectors = ["h1", ".page-title", ".api-title", ".class-name", "title"]

        for selector in title_selectors:
            title_element = soup.select_one(selector)
            if title_element is not None:
                # select_one returns Tag or None, so title_element is Tag here
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
            " | Phaser 3",
        ]

        cleaned = title.strip()
        for suffix in suffixes_to_remove:
            if cleaned.endswith(suffix):
                cleaned = cleaned[: -len(suffix)].strip()

        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned if cleaned else "Phaser Documentation"

    def _resolve_relative_urls(self, soup: BeautifulSoup, base_url: str) -> None:
        """Resolve relative URLs to absolute URLs."""
        for link in soup.find_all("a", href=True):
            href = link.get("href")
            if (
                href
                and isinstance(href, str)
                and not href.startswith(("http://", "https://", "mailto:", "#"))
            ):
                absolute_url = urljoin(base_url, href)
                link["href"] = absolute_url

        for img in soup.find_all("img", src=True):
            src = img.get("src")
            if (
                src
                and isinstance(src, str)
                and not src.startswith(("http://", "https://", "data:"))
            ):
                absolute_url = urljoin(base_url, src)
                img["src"] = absolute_url

    def _extract_code_blocks(self, soup: TagOrSoup) -> list[CodeBlock]:
        """Extract code blocks with metadata."""
        code_blocks: list[CodeBlock] = []

        for selector in self.CODE_SELECTORS:
            for element in soup.select(selector):
                # soup.select returns list[Tag], so element is always Tag
                code_text = element.get_text()
                if code_text.strip():
                    language = self._detect_code_language(element)

                    code_blocks.append(
                        {
                            "content": code_text.strip(),
                            "language": language,
                            "element": element,
                            "context": self._get_code_context(element),
                        }
                    )

        logger.debug(f"Extracted {len(code_blocks)} code blocks")
        return code_blocks

    def _detect_code_language(self, element: Tag) -> str:
        """Detect programming language from code element."""
        classes = element.get("class", [])
        if isinstance(classes, str):  # type: ignore[reportUnnecessaryIsInstance]
            classes = [classes]

        for class_name in classes:
            if isinstance(class_name, str):  # type: ignore[reportUnnecessaryIsInstance]
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
        context_elements: list[str] = []

        parent = element.parent
        if parent is not None:
            # parent can be Tag or BeautifulSoup, both have previous_sibling
            current = parent.previous_sibling
            while current and len(context_elements) < 3:
                if isinstance(current, Tag):
                    if current.name and current.name in [
                        "h1",
                        "h2",
                        "h3",
                        "h4",
                        "h5",
                        "h6",
                    ]:
                        context_elements.append(current.get_text(strip=True))
                        break
                    elif (
                        current.name
                        and current.name in ["p", "div"]
                        and current.get_text(strip=True)
                    ):
                        text = current.get_text(strip=True)
                        if len(text) < 200:
                            context_elements.append(text)
                current = current.previous_sibling

        return " | ".join(reversed(context_elements)) if context_elements else ""

    def _prepare_html_for_markdown(self, soup: BeautifulSoup) -> BeautifulSoup:
        """Prepare HTML for optimal Markdown conversion."""
        prepared_soup = BeautifulSoup(str(soup), "html.parser")

        # Enhance code blocks
        self._enhance_code_block_extraction(prepared_soup)

        # Normalize heading hierarchy
        self._normalize_heading_hierarchy(prepared_soup)

        # Prepare tables for markdown
        self._prepare_tables_for_markdown(prepared_soup)

        # Prepare lists for markdown
        self._prepare_lists_for_markdown(prepared_soup)

        # Add language classes to code elements
        for code_element in prepared_soup.find_all(["pre", "code"]):
            # find_all returns ResultSet[Tag], so code_element is always Tag
            if not code_element.get("class"):
                language = self._detect_code_language(code_element)
                code_element["class"] = [f"language-{language}"]

        return prepared_soup

    def _enhance_code_block_extraction(self, soup: BeautifulSoup) -> None:
        """Enhance code blocks for better Markdown conversion."""
        # Find all code blocks
        for code_element in soup.find_all(["pre", "code"]):
            # find_all returns ResultSet[Tag], so code_element is always Tag
            # Add language class if not present
            if not code_element.get("class"):
                language = self._detect_code_language(code_element)
                code_element["class"] = [f"language-{language}"]

                # Check for Phaser-specific content
                code_text = code_element.get_text()
                phaser_patterns = [
                    "Phaser.Game",
                    "this.add",
                    "this.load",
                    "this.scene",
                    "this.physics",
                    "this.anims",
                    "this.input",
                    "this.cameras",
                    "this.tweens",
                    "this.sound",
                    "Phaser.Scene",
                    "Phaser.GameObjects",
                    "Phaser.Physics",
                    "Phaser.Input",
                    "Phaser.Animations",
                ]
                if any(pattern in code_text for pattern in phaser_patterns):
                    code_element["data-phaser"] = "true"

                # Ensure code blocks have proper structure
                if (
                    code_element.name == "code"
                    and code_element.parent is not None
                    and hasattr(code_element.parent, "name")
                    and code_element.parent.name != "pre"
                ):
                    # Wrap standalone code elements in pre tags
                    pre_tag = soup.new_tag("pre")
                    code_element.wrap(pre_tag)

        # Find method signatures that should be code blocks
        for method_sig in soup.select(".method-signature, .function-signature"):
            # soup.select returns list[Tag], so method_sig is always Tag
            code_text = method_sig.get_text(strip=True)
            if code_text:
                pre_tag = soup.new_tag("pre")
                code_tag = soup.new_tag("code", attrs={"class": "language-javascript"})
                code_tag.string = soup.new_string(code_text)
                pre_tag.append(code_tag)
                method_sig.append(pre_tag)
                method_sig["data-method-signature"] = "true"

    def _normalize_heading_hierarchy(self, soup: BeautifulSoup) -> None:
        """Normalize heading hierarchy for consistent Markdown output."""
        # Find all headings
        headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])

        # Find the minimum heading level used
        min_level = 6
        for heading in headings:
            # find_all returns ResultSet[Tag], so heading is always Tag
            if heading.name:
                level = int(heading.name[1])
                min_level = min(min_level, level)

        # If minimum level is not h1, normalize the hierarchy
        if min_level > 1:
            for heading in headings:
                # find_all returns ResultSet[Tag], so heading is always Tag
                if heading.name:
                    current_level = int(heading.name[1])
                    new_level = max(1, current_level - min_level + 1)
                    new_tag = soup.new_tag(f"h{new_level}")
                    new_tag.string = soup.new_string(heading.get_text())
                    heading.replace_with(new_tag)

    def _prepare_tables_for_markdown(self, soup: BeautifulSoup) -> None:
        """Prepare tables for better Markdown conversion."""
        for table in soup.find_all("table"):
            # find_all returns ResultSet[Tag], so table is always Tag
            # Ensure tables have proper structure
            if not table.find("thead"):
                # Check if first row can be used as header
                first_row = table.find("tr")
                if first_row is not None:
                    # find returns Tag or None, so first_row is Tag here
                    # Convert td to th in the header row
                    for td in first_row.find_all("td"):
                        # find_all returns ResultSet[Tag], so td is always Tag
                        th = soup.new_tag("th")
                        th.string = soup.new_string(td.get_text())
                        td.replace_with(th)

                    thead = soup.new_tag("thead")
                    thead.append(first_row.extract())
                    table.insert(0, thead)

            # Add tbody if not present
            if not table.find("tbody"):
                tbody = soup.new_tag("tbody")
                # Move all remaining rows to tbody
                for row in table.find_all("tr"):
                    # find_all returns ResultSet[Tag], so row is always Tag
                    tbody.append(row.extract())
                table.append(tbody)

            # Ensure all cells have content
            for cell in table.find_all(["td", "th"]):
                # find_all returns ResultSet[Tag], so cell is always Tag
                if not cell.get_text(strip=True):
                    cell.string = soup.new_string(" ")

    def _prepare_lists_for_markdown(self, soup: BeautifulSoup) -> None:
        """Prepare lists for better Markdown conversion."""
        # Fix nested lists
        for nested_list in soup.select("ul ul, ol ol, ul ol, ol ul"):
            # soup.select returns list[Tag], so nested_list is always Tag
            # Add spacing before nested lists
            if nested_list.previous_sibling:
                spacer = soup.new_tag("span")
                spacer.string = soup.new_string(" ")
                nested_list.insert_before(spacer)

            # Move nested lists inside parent li if they're not already
            parent_li = nested_list.find_previous("li")
            if (
                parent_li is not None
                and hasattr(parent_li, "contents")
                and nested_list not in parent_li.contents
            ):
                parent_li.append(nested_list)

        # Ensure list items have content
        for li in soup.find_all("li"):
            # find_all returns ResultSet[Tag], so li is always Tag
            if not li.get_text(strip=True):
                li.string = soup.new_string(" ")

    def _extract_phaser_specific_content(self, soup: BeautifulSoup) -> dict[str, Any]:
        """Extract Phaser-specific content patterns."""
        phaser_patterns = [
            "Phaser.Game",
            "this.add",
            "this.load",
            "this.scene",
            "this.physics",
            "this.anims",
            "this.input",
            "this.cameras",
            "this.tweens",
            "this.sound",
            "Phaser.Scene",
            "Phaser.GameObjects",
            "Phaser.Physics",
            "Phaser.Input",
            "Phaser.Animations",
        ]

        result: dict[str, str | list[dict[str, str]]] = {
            "game_objects": [],
            "scenes": [],
            "physics": [],
            "input": [],
            "input_handlers": [],
            "animations": [],
            "code_blocks": [],
            "examples": [],
            "tutorials": [],
            "raw_content": "",
        }

        phaser_content: list[str] = []

        # Look for code blocks with Phaser patterns
        for code in soup.find_all(["pre", "code"]):
            # find_all returns ResultSet[Tag], so code is always Tag
            code_text = code.get_text()
            if any(pattern in code_text for pattern in phaser_patterns):
                # Get context (heading or paragraph before the code)
                context = ""
                # First try to find a heading in the parent's previous siblings
                current = code.parent if code.parent else None
                while current and not context:
                    prev = current.previous_sibling
                    while prev and not context:
                        if (
                            isinstance(prev, Tag)
                            and hasattr(prev, "name")
                            and prev.name in ["h1", "h2", "h3", "h4", "h5", "h6"]
                        ):
                            context = prev.get_text(strip=True)
                            break
                        elif (
                            isinstance(prev, Tag)
                            and hasattr(prev, "name")
                            and prev.name in ["p"]
                            and prev.get_text(strip=True)
                        ):
                            context = prev.get_text(strip=True)
                            break
                        prev = prev.previous_sibling
                    current = current.parent

                # Also check for headings that come before the code block
                # in the document
                if not context:
                    # Look for the nearest preceding heading in the entire
                    # document
                    all_headings = soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"])
                    # Use a simpler approach to find context without
                    # position comparison
                    for heading in reversed(all_headings):
                        # find_all returns ResultSet[Tag], so heading is always Tag
                        # Check if this heading appears before the code
                        # block in the HTML
                        heading_text = str(heading)
                        code_text_str = str(code)
                        soup_str = str(soup)
                        if soup_str.find(heading_text) < soup_str.find(code_text_str):
                            context = heading.get_text(strip=True)
                            break

                    # Add to appropriate category
                    code_block = {"content": code_text, "context": context}
                    code_blocks_list = cast(list[dict[str, str]], result["code_blocks"])
                    code_blocks_list.append(code_block)

                    # Categorize by content
                    if (
                        "this.add" in code_text
                        or "Phaser.GameObjects" in code_text
                        or "sprite" in code_text.lower()
                    ):
                        game_objects_list = cast(
                            list[dict[str, str]], result["game_objects"]
                        )
                        game_objects_list.append(code_block)
                    if (
                        "this.scene" in code_text
                        or "Phaser.Scene" in code_text
                        or "scene" in code_text.lower()
                    ):
                        scenes_list = cast(list[dict[str, str]], result["scenes"])
                        scenes_list.append(code_block)
                    if (
                        "this.physics" in code_text
                        or "Phaser.Physics" in code_text
                        or "physics" in code_text.lower()
                    ):
                        physics_list = cast(list[dict[str, str]], result["physics"])
                        physics_list.append(code_block)
                    if (
                        "this.input" in code_text
                        or "Phaser.Input" in code_text
                        or "input" in code_text.lower()
                    ):
                        input_list = cast(list[dict[str, str]], result["input"])
                        input_list.append(code_block)
                    if (
                        "pointerdown" in code_text
                        or "click" in code_text.lower()
                        or "touch" in code_text.lower()
                    ):
                        input_handlers_list = cast(
                            list[dict[str, str]], result["input_handlers"]
                        )
                        input_handlers_list.append(code_block)
                    if (
                        "this.anims" in code_text
                        or "Phaser.Animations" in code_text
                        or "animation" in code_text.lower()
                    ):
                        animations_list = cast(
                            list[dict[str, str]], result["animations"]
                        )
                        animations_list.append(code_block)
                    if (
                        "tutorial" in code_text.lower()
                        or "guide" in code_text.lower()
                        or "tutorial" in context.lower()
                        or "guide" in context.lower()
                    ):
                        tutorials_list = cast(list[dict[str, str]], result["tutorials"])
                        tutorials_list.append(code_block)

                    # Add to examples if it looks like a complete code example
                    if len(code_text.strip().split("\n")) > 3:
                        examples_list = cast(list[dict[str, str]], result["examples"])
                        examples_list.append(code_block)

                    # Add to raw content
                    if context:
                        phaser_content.append(f"<h4>{context}</h4>")
                    phaser_content.append(str(code))

        result["raw_content"] = "\n".join(phaser_content) if phaser_content else ""
        return result

    def _post_process_markdown(self, markdown: str) -> str:
        """Post-process Markdown content for better readability."""
        if not markdown:
            return ""

        # Remove excessive whitespace
        processed = re.sub(r"\n{3,}", "\n\n", markdown)

        # Fix heading spacing
        processed = re.sub(r"(#{1,6}[^\n]*)\n([^\n])", r"\1\n\n\2", processed)

        # Fix list spacing
        processed = re.sub(r"(\n- [^\n]*)\n([^\n-])", r"\1\n\n\2", processed)

        # Clean up code blocks
        processed = re.sub(r"```\s*\n\s*```", "", processed)

        # Fix link formatting
        processed = self._clean_link_formatting(processed)

        # Ensure it ends with a newline
        processed = processed.strip() + "\n"

        return processed

    def _clean_link_formatting(self, content: str) -> str:
        """Clean and fix link formatting in Markdown."""
        # Fix empty links
        content = re.sub(r"\[\s*\]\(\s*\)", "", content)

        # Fix duplicate text/URL links
        content = re.sub(r"\[([^\]]+)\]\(\1\)", r"\1", content)

        # Remove empty links
        content = re.sub(r"\[([^\]]+)\]\(\s*\)", r"\1", content)

        # Fix links with spaces in URL
        def fix_url_spaces(match: Match[str]) -> str:
            text = match.group(1)
            url = match.group(2).strip()
            url = url.replace(" ", "%20")
            return f"[{text}]({url})"

        content = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", fix_url_spaces, content)

        return content

    def _clean_markdown_content(self, content: str) -> str:
        """Clean and normalize Markdown content."""
        if not content:
            return ""

        # Remove excessive whitespace
        content = re.sub(r"\n\s*\n\s*\n", "\n\n", content)
        content = re.sub(r"[ \t]+", " ", content)

        # Fix heading spacing
        content = re.sub(r"\n(#{1,6})", r"\n\n\1", content)
        content = re.sub(r"(#{1,6}[^\n]*)\n([^\n#])", r"\1\n\n\2", content)

        # Fix list formatting
        content = re.sub(r"\n(\s*[-*+])", r"\n\n\1", content)

        return content.strip()

    def _fix_code_block_formatting(self, content: str) -> str:
        """Fix code block formatting in Markdown."""
        # Fix inline code that should be code blocks
        content = re.sub(
            r"`([^`\n]*\n[^`]*)`", r"```\n\1\n```", content, flags=re.MULTILINE
        )

        # Ensure code blocks have proper language tags
        def add_language_to_code_block(match: Match[str]) -> str:
            code_content = match.group(1)
            if any(
                keyword in code_content.lower()
                for keyword in ["function", "var", "let", "const", "class"]
            ):
                return f"```javascript\n{code_content}\n```"
            elif "<" in code_content and ">" in code_content:
                return f"```html\n{code_content}\n```"
            else:
                return f"```javascript\n{code_content}\n```"

        content = re.sub(
            r"```\n([^`]+)\n```",
            add_language_to_code_block,
            content,
            flags=re.MULTILINE | re.DOTALL,
        )

        return content

    def parse_html_to_markdown(
        self,
        html_content: str,
        url: str = "",
        max_length: int = 0,
        start_index: int = 0,
    ) -> str:
        """Parse HTML content and convert to Markdown with optional pagination.

        Args:
            html_content: HTML content to parse
            url: Source URL for context
            max_length: Maximum length of content to return (0 for no limit)
            start_index: Starting index for pagination

        Returns:
            Markdown-formatted content

        Raises:
            HTMLParseError: If HTML parsing fails
            MarkdownConversionError: If Markdown conversion fails
        """
        try:
            # Parse HTML to structured content
            parsed_content = self.parse_html_content(html_content, url)

            # Convert to Markdown
            markdown_content = self.convert_to_markdown(parsed_content)

            # Apply pagination if requested
            if max_length > 0:
                if start_index >= len(markdown_content):
                    return ""

                end_index = min(start_index + max_length, len(markdown_content))
                markdown_content = markdown_content[start_index:end_index]

                # Ensure we don't cut in the middle of a word
                if end_index < len(markdown_content):
                    last_space = markdown_content.rfind(" ")
                    if last_space > 0:
                        markdown_content = markdown_content[:last_space]

            return markdown_content

        except (HTMLParseError, MarkdownConversionError) as e:
            logger.error(f"Error parsing HTML to Markdown: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in parse_html_to_markdown: {e}")
            raise MarkdownConversionError(
                f"Failed to convert HTML to Markdown: {e}"
            ) from e


# Export the parser class
__all__ = ["PhaserDocumentParser"]
