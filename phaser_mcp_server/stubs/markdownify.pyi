"""Type stubs for markdownify library.

This module provides type definitions for the markdownify library
to resolve type checking issues with Pyright.
"""

from typing import Any, List, Optional, Union, Callable, Pattern

# Constants for heading styles
ATX: str
ATX_CLOSED: str
SETEXT: str
UNDERLINED: str

# Constants for emphasis marks
ASTERISK: str
UNDERSCORE: str
BACKSLASH: str

# Constants for whitespace handling
SPACES: str
STRIP: str
LSTRIP: str
RSTRIP: str

# Regular expression patterns
re_all_whitespace: Pattern[str]
re_convert_heading: Pattern[str]
re_escape_misc_chars: Pattern[str]
re_escape_misc_dash_sequences: Pattern[str]
re_escape_misc_hashes: Pattern[str]
re_escape_misc_list_items: Pattern[str]
re_extract_newlines: Pattern[str]
re_html_heading: Pattern[str]
re_line_with_content: Pattern[str]
re_make_convert_fn_name: Pattern[str]
re_newline_whitespace: Pattern[str]
re_whitespace: Pattern[str]

def markdownify(
    html: Union[str, bytes],
    heading_style: str = "underlined",
    bullets: str = "*",
    emphasis_mark: str = "_",
    strong_mark: str = "**",
    sub_symbol: str = "",
    sup_symbol: str = "",
    wrap: bool = False,
    wrap_width: int = 80,
    convert: Optional[List[str]] = None,
    strip: Optional[List[str]] = None,
    default_title: bool = False,
    escape_asterisks: bool = True,
    escape_underscores: bool = True,
    escape_misc: bool = True,
    newline_style: str = "spaces",
    code_language: str = "",
    autolinks: bool = True,
    **options: Any,
) -> str:
    """Convert HTML to Markdown.

    Args:
        html: HTML content to convert
        heading_style: Style for headings ("underlined", "atx", "setext")
        bullets: Character to use for bullet points
        emphasis_mark: Character to use for emphasis
        strong_mark: Characters to use for strong text
        sub_symbol: Symbol for subscript
        sup_symbol: Symbol for superscript
        wrap: Whether to wrap long lines
        wrap_width: Width to wrap at
        convert: List of tags to convert
        strip: List of tags to strip
        default_title: Whether to use default title
        escape_asterisks: Whether to escape asterisks
        escape_underscores: Whether to escape underscores
        escape_misc: Whether to escape miscellaneous characters
        newline_style: Style for newlines
        code_language: Default language for code blocks
        autolinks: Whether to convert URLs to links
        **options: Additional options

    Returns:
        Markdown string
    """
    ...

class MarkdownConverter:
    """Main converter class for HTML to Markdown conversion."""

    def __init__(
        self,
        heading_style: str = "underlined",
        bullets: str = "*",
        emphasis_mark: str = "_",
        strong_mark: str = "**",
        sub_symbol: str = "",
        sup_symbol: str = "",
        wrap: bool = False,
        wrap_width: int = 80,
        convert: Optional[List[str]] = None,
        strip: Optional[List[str]] = None,
        default_title: bool = False,
        escape_asterisks: bool = True,
        escape_underscores: bool = True,
        escape_misc: bool = True,
        newline_style: str = "spaces",
        code_language: str = "",
        autolinks: bool = True,
        **options: Any,
    ) -> None: ...
    def convert(self, html: Union[str, bytes]) -> str: ...
    def convert_soup(self, soup: Any) -> str: ...
    def process_tag(
        self, node: Any, convert_as_inline: bool = False, children_only: bool = False
    ) -> str: ...

# Utility functions
def abstract_inline_conversion(
    markup_fn: Callable[[str], str]
) -> Callable[[Any, str], str]: ...
def chomp(text: str) -> str:
    """Remove trailing whitespace from text."""
    ...

def fill(text: str, width: int = 80) -> str:
    """Fill text to specified width."""
    ...

def should_remove_whitespace_inside(tag: Any) -> bool:
    """Check if whitespace should be removed inside a tag."""
    ...

def should_remove_whitespace_outside(tag: Any) -> bool:
    """Check if whitespace should be removed outside a tag."""
    ...

# Re-exported BeautifulSoup types for convenience
from bs4 import (
    BeautifulSoup as BeautifulSoup,
    Tag as Tag,
    NavigableString as NavigableString,
)

# Convenience aliases
md = markdownify
