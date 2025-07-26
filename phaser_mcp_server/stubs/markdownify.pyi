"""Type stubs for markdownify library.

This module provides type definitions for the markdownify library
to resolve type checking issues with Pyright.
"""

from collections.abc import Callable
from typing import Any

# Re-exported BeautifulSoup types for convenience
from bs4 import (
    BeautifulSoup as BeautifulSoup,
)
from bs4 import (
    NavigableString as NavigableString,
)
from bs4 import (
    Tag as Tag,
)

# Constants for heading styles
ATX: str
ATX_CLOSED: str
SETEXT: str
UNDERLINED: str

# Constants for emphasis marks
ASTERISK: str
UNDERSCORE: str
BACKSLASH: str

# Constants for list bullets
UNORDERED: str
ORDERED: str

# Constants for code block styles
FENCED: str
INDENTED: str

# Type aliases
TagOrString = Tag | NavigableString
ConvertFunction = Callable[[Tag, bool, dict[str, Any]], str]

class MarkdownConverter:
    """Main converter class for HTML to Markdown conversion."""

    def __init__(
        self,
        *,
        heading_style: str = ATX,
        bullets: str = UNORDERED,
        emphasis_mark: str = ASTERISK,
        strong_mark: str = ASTERISK,
        code_language: str = "",
        wrap: bool = False,
        wrap_width: int = 80,
        autolinks: bool = True,
        convert: list[str] | None = None,
        strip: list[str] | None = None,
        default_title: bool = False,
        escape_asterisks: bool = True,
        escape_underscores: bool = True,
        escape_misc: bool = True,
        newline_style: str = "\n",
        **options: Any,
    ) -> None: ...
    def convert(self, soup: BeautifulSoup | Tag | str) -> str:
        """Convert HTML to Markdown."""
        ...

    def process_tag(
        self,
        node: Tag,
        convert_as_inline: bool,
        children_only: bool = False,
    ) -> str:
        """Process a single HTML tag."""
        ...

    def convert_a(self, el: Tag, text: str, convert_as_inline: bool) -> str: ...
    def convert_b(self, el: Tag, text: str, convert_as_inline: bool) -> str: ...
    def convert_blockquote(
        self, el: Tag, text: str, convert_as_inline: bool
    ) -> str: ...
    def convert_br(self, el: Tag, text: str, convert_as_inline: bool) -> str: ...
    def convert_code(self, el: Tag, text: str, convert_as_inline: bool) -> str: ...
    def convert_del(self, el: Tag, text: str, convert_as_inline: bool) -> str: ...
    def convert_em(self, el: Tag, text: str, convert_as_inline: bool) -> str: ...
    def convert_h1(self, el: Tag, text: str, convert_as_inline: bool) -> str: ...
    def convert_h2(self, el: Tag, text: str, convert_as_inline: bool) -> str: ...
    def convert_h3(self, el: Tag, text: str, convert_as_inline: bool) -> str: ...
    def convert_h4(self, el: Tag, text: str, convert_as_inline: bool) -> str: ...
    def convert_h5(self, el: Tag, text: str, convert_as_inline: bool) -> str: ...
    def convert_h6(self, el: Tag, text: str, convert_as_inline: bool) -> str: ...
    def convert_hr(self, el: Tag, text: str, convert_as_inline: bool) -> str: ...
    def convert_i(self, el: Tag, text: str, convert_as_inline: bool) -> str: ...
    def convert_img(self, el: Tag, text: str, convert_as_inline: bool) -> str: ...
    def convert_li(self, el: Tag, text: str, convert_as_inline: bool) -> str: ...
    def convert_ol(self, el: Tag, text: str, convert_as_inline: bool) -> str: ...
    def convert_p(self, el: Tag, text: str, convert_as_inline: bool) -> str: ...
    def convert_pre(self, el: Tag, text: str, convert_as_inline: bool) -> str: ...
    def convert_s(self, el: Tag, text: str, convert_as_inline: bool) -> str: ...
    def convert_strong(self, el: Tag, text: str, convert_as_inline: bool) -> str: ...
    def convert_table(self, el: Tag, text: str, convert_as_inline: bool) -> str: ...
    def convert_td(self, el: Tag, text: str, convert_as_inline: bool) -> str: ...
    def convert_th(self, el: Tag, text: str, convert_as_inline: bool) -> str: ...
    def convert_tr(self, el: Tag, text: str, convert_as_inline: bool) -> str: ...
    def convert_u(self, el: Tag, text: str, convert_as_inline: bool) -> str: ...
    def convert_ul(self, el: Tag, text: str, convert_as_inline: bool) -> str: ...

def markdownify(
    html: str | BeautifulSoup | Tag,
    *,
    heading_style: str = ATX,
    bullets: str = UNORDERED,
    emphasis_mark: str = ASTERISK,
    strong_mark: str = ASTERISK,
    code_language: str = "",
    wrap: bool = False,
    wrap_width: int = 80,
    autolinks: bool = True,
    convert: list[str] | None = None,
    strip: list[str] | None = None,
    default_title: bool = False,
    escape_asterisks: bool = True,
    escape_underscores: bool = True,
    escape_misc: bool = True,
    newline_style: str = "\n",
    **options: Any,
) -> str:
    """Convert HTML to Markdown.

    Args:
        html: HTML content to convert
        heading_style: Style for headings (ATX, ATX_CLOSED, SETEXT, UNDERLINED)
        bullets: Style for unordered lists (UNORDERED, ORDERED)
        emphasis_mark: Mark for emphasis (ASTERISK, UNDERSCORE)
        strong_mark: Mark for strong text (ASTERISK, UNDERSCORE)
        code_language: Default language for code blocks
        wrap: Whether to wrap long lines
        wrap_width: Width for line wrapping
        autolinks: Whether to convert URLs to links automatically
        convert: List of tags to convert
        strip: List of tags to strip
        default_title: Whether to use default title for links
        escape_asterisks: Whether to escape asterisks
        escape_underscores: Whether to escape underscores
        escape_misc: Whether to escape miscellaneous characters
        newline_style: Style for newlines
        **options: Additional options

    Returns:
        Markdown string
    """
    ...

# Convenience aliases
md = markdownify
