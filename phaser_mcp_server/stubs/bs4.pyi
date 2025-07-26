"""Type stubs for BeautifulSoup4 library.

This module provides type definitions for the BeautifulSoup4 library
to resolve type checking issues with Pyright.
"""

import re
from collections.abc import Callable, Iterable, Iterator
from typing import Any

class NavigableString(str):
    """A NavigableString is just a Python string that knows about its place.

    This class represents a string that is aware of its position in the parse tree.
    """

    def __new__(cls, value: str) -> NavigableString:
        """Create a new NavigableString instance."""
        ...

    @property
    def parent(self) -> Tag | None:
        """Return the parent Tag of this NavigableString."""
        ...

    @property
    def next_sibling(self) -> Tag | NavigableString | None:
        """Return the next sibling element."""
        ...

    @property
    def previous_sibling(self) -> Tag | NavigableString | None:
        """Return the previous sibling element."""
        ...

    @property
    def next_element(self) -> Tag | NavigableString | None:
        """Return the next element in the parse tree."""
        ...

    @property
    def previous_element(self) -> Tag | NavigableString | None:
        """Return the previous element in the parse tree."""
        ...

    def extract(self) -> NavigableString:
        """Remove this element from the tree and return it."""
        ...

    def replace_with(self, *args: Tag | NavigableString | str) -> NavigableString:
        """Replace this element with the given elements."""
        ...

class PageElement:
    """Base class for all parse tree elements."""

    @property
    def parent(self) -> Tag | None:
        """Return the parent Tag of this element."""
        ...

    @property
    def next_sibling(self) -> Tag | NavigableString | None:
        """Return the next sibling element."""
        ...

    @property
    def previous_sibling(self) -> Tag | NavigableString | None:
        """Return the previous sibling element."""
        ...

    @property
    def next_element(self) -> Tag | NavigableString | None:
        """Return the next element in the parse tree."""
        ...

    @property
    def previous_element(self) -> Tag | NavigableString | None:
        """Return the previous element in the parse tree."""
        ...

    @property
    def name(self) -> str | None:
        """Return the name of this element."""
        ...

    def extract(self) -> PageElement:
        """Remove this element from the tree and return it."""
        ...

    def replace_with(self, *args: Tag | NavigableString | str) -> PageElement:
        """Replace this element with the given elements."""
        ...

    def wrap(self, wrap_with: Tag) -> Tag:
        """Wrap this element in the given tag."""
        ...

    def unwrap(self) -> PageElement | None:
        """Remove this element's tag and return its contents."""
        ...

    def get_text(
        self,
        separator: str = "",
        strip: bool = False,
        types: tuple = (NavigableString,),
    ) -> str:
        """Get all text content from this element and its descendants."""
        ...

    def find(
        self,
        name: str
        | list[str]
        | re.Pattern[str]
        | Callable[[str], bool]
        | bool
        | None = None,
        attrs: dict[str, Any] | str | None = None,
        recursive: bool = True,
        string: str | re.Pattern[str] | None = None,
        **kwargs: Any,
    ) -> Tag | None:
        """Find the first matching element."""
        ...

    def find_all(
        self,
        name: str
        | list[str]
        | re.Pattern[str]
        | Callable[[str], bool]
        | bool
        | None = None,
        attrs: dict[str, Any] | str | None = None,
        recursive: bool = True,
        string: str | re.Pattern[str] | None = None,
        limit: int | None = None,
        **kwargs: Any,
    ) -> ResultSet[Tag]:
        """Find all matching elements."""
        ...

    def select(self, selector: str) -> list[Tag]:
        """Find elements using CSS selector."""
        ...

    def select_one(self, selector: str) -> Tag | None:
        """Find the first element using CSS selector."""
        ...

    def find_previous(
        self,
        name: str
        | list[str]
        | re.Pattern[str]
        | Callable[[str], bool]
        | bool
        | None = None,
        attrs: dict[str, Any] | str | None = None,
        string: str | re.Pattern[str] | None = None,
        **kwargs: Any,
    ) -> Tag | None:
        """Find the previous matching element."""
        ...

class Tag(PageElement):
    """A Tag represents an HTML or XML tag that is part of a parse tree."""

    name: str
    attrs: dict[str, str | list[str]]
    contents: list[Tag | NavigableString]
    string: NavigableString | None

    def __init__(
        self,
        parser: Any = None,
        builder: Any = None,
        name: str | None = None,
        namespace: str | None = None,
        prefix: str | None = None,
        attrs: dict[str, Any] | None = None,
        parent: Tag | None = None,
        previous: Tag | NavigableString | None = None,
        is_xml: bool | None = None,
        sourceline: int | None = None,
        sourcepos: int | None = None,
        can_be_empty_element: bool | None = None,
        cdata_list_attributes: list[str] | None = None,
        preserve_whitespace_tags: list[str] | None = None,
        interesting_string_types: type | None = None,
        namespaces: dict[str, str] | None = None,
    ) -> None:
        """Initialize a new Tag."""
        ...
    # Navigation methods
    def find(
        self,
        name: str
        | list[str]
        | re.Pattern[str]
        | Callable[[str], bool]
        | bool
        | None = None,
        attrs: dict[str, Any] | str | None = None,
        recursive: bool = True,
        string: str | re.Pattern[str] | None = None,
        **kwargs: Any,
    ) -> Tag | None:
        """Find the first matching element."""
        ...

    def find_all(
        self,
        name: str
        | list[str]
        | re.Pattern[str]
        | Callable[[str], bool]
        | bool
        | None = None,
        attrs: dict[str, Any] | str | None = None,
        recursive: bool = True,
        string: str | re.Pattern[str] | None = None,
        limit: int | None = None,
        **kwargs: Any,
    ) -> ResultSet[Tag]:
        """Find all matching elements."""
        ...

    def select(self, selector: str) -> list[Tag]:
        """Find elements using CSS selector."""
        ...

    def select_one(self, selector: str) -> Tag | None:
        """Find the first element using CSS selector."""
        ...
    # Content methods
    def get_text(
        self,
        separator: str = "",
        strip: bool = False,
        types: tuple = (NavigableString,),
    ) -> str:
        """Get all text content from this element and its descendants."""
        ...

    def get(self, key: str, default: Any = None) -> Any:
        """Get an attribute value."""
        ...

    def __getitem__(self, key: str) -> str | list[str]:
        """Get an attribute value using bracket notation."""
        ...

    def __setitem__(self, key: str, value: str | list[str]) -> None:
        """Set an attribute value using bracket notation."""
        ...

    def __delitem__(self, key: str) -> None:
        """Delete an attribute using bracket notation."""
        ...

    def __contains__(self, key: str) -> bool:
        """Check if an attribute exists."""
        ...
    # Tree modification methods
    def append(self, tag: Tag | NavigableString | str) -> None:
        """Append a child element."""
        ...

    def insert(self, position: int, new_child: Tag | NavigableString | str) -> None:
        """Insert a child element at the specified position."""
        ...

    def insert_before(self, *args: Tag | NavigableString | str) -> None:
        """Insert elements before this element."""
        ...

    def insert_after(self, *args: Tag | NavigableString | str) -> None:
        """Insert elements after this element."""
        ...

    def clear(self, decompose: bool = False) -> None:
        """Remove all children from this element."""
        ...

    def extract(self) -> Tag:
        """Remove this element from the tree and return it."""
        ...

    def decompose(self) -> None:
        """Destroy this element and its children."""
        ...

    def replace_with(self, *args: Tag | NavigableString | str) -> Tag:
        """Replace this element with the given elements."""
        ...

    def wrap(self, wrap_with: Tag) -> Tag:
        """Wrap this element in the given tag."""
        ...

    def unwrap(self) -> Tag | None:
        """Remove this element's tag and return its contents."""
        ...
    # String representation
    def __str__(self) -> str:
        """Return string representation of this element."""
        ...

    def __repr__(self) -> str:
        """Return detailed string representation of this element."""
        ...
    # Iteration
    def __iter__(self) -> Iterator[Tag | NavigableString]:
        """Iterate over direct children."""
        ...

    def children(self) -> Iterator[Tag | NavigableString]:
        """Iterate over direct children."""
        ...

    def descendants(self) -> Iterator[Tag | NavigableString]:
        """Iterate over all descendants."""
        ...

    def strings(self) -> Iterator[NavigableString]:
        """Iterate over all strings in this element."""
        ...

    def stripped_strings(self) -> Iterator[str]:
        """Iterate over all non-empty strings in this element."""
        ...
    # Factory methods
    def new_tag(
        self,
        name: str,
        namespace: str | None = None,
        nsprefix: str | None = None,
        attrs: dict[str, Any] | None = None,
        sourceline: int | None = None,
        sourcepos: int | None = None,
        **kwattrs: Any,
    ) -> Tag:
        """Create a new tag."""
        ...

    def new_string(self, s: str, subclass: type = NavigableString) -> NavigableString:
        """Create a new NavigableString."""
        ...

class ResultSet(list[Tag]):
    """A ResultSet is just a list that keeps track of the SoupStrainer.

    This class represents a list that maintains information about the
    SoupStrainer that created it.
    """

    def __init__(self, source: Any, result: Iterable[Tag] = ()) -> None:
        """Initialize a new ResultSet."""
        ...

class BeautifulSoup(Tag):
    """The BeautifulSoup class turns a document into a tree of Python objects."""

    def __init__(
        self,
        markup: str | bytes = "",
        features: str | list[str] | None = None,
        builder: Any = None,
        parse_only: Any = None,
        from_encoding: str | None = None,
        exclude_encodings: list[str] | None = None,
        element_classes: dict[type, type] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize a new BeautifulSoup parser."""
        ...
    # Factory methods for creating new tags
    def new_tag(
        self,
        name: str,
        namespace: str | None = None,
        nsprefix: str | None = None,
        attrs: dict[str, Any] | None = None,
        sourceline: int | None = None,
        sourcepos: int | None = None,
        **kwattrs: Any,
    ) -> Tag:
        """Create a new tag."""
        ...

    def new_string(self, s: str, subclass: type = NavigableString) -> NavigableString:
        """Create a new NavigableString."""
        ...
    # Encoding methods
    def encode(
        self,
        encoding: str = "utf-8",
        indent_level: int | None = None,
        formatter: str | Callable[[str], str] = "minimal",
        errors: str = "xmlcharrefreplace",
    ) -> bytes:
        """Encode the document as bytes."""
        ...

    def decode(
        self,
        indent_level: int | None = None,
        eventual_encoding: str = "utf-8",
        formatter: str | Callable[[str], str] = "minimal",
    ) -> str:
        """Decode the document as a string."""
        ...

# Type aliases for common usage patterns
TagOrString = Tag | NavigableString
TagOrElement = Tag | PageElement | NavigableString
