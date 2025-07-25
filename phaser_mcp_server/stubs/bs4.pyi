"""Type stubs for BeautifulSoup4 library.

This module provides type definitions for the BeautifulSoup4 library
to resolve type checking issues with Pyright.
"""

from typing import Any, Dict, Iterable, List, Optional, Union, Iterator, Callable
import re

class NavigableString(str):
    """A NavigableString is just a Python string that knows about its place in the parse tree."""

    def __new__(cls, value: str) -> "NavigableString":
        """Create a new NavigableString instance."""
        ...

    @property
    def parent(self) -> Optional["Tag"]:
        """Return the parent Tag of this NavigableString."""
        ...

    @property
    def next_sibling(self) -> Optional[Union["Tag", "NavigableString"]]:
        """Return the next sibling element."""
        ...

    @property
    def previous_sibling(self) -> Optional[Union["Tag", "NavigableString"]]:
        """Return the previous sibling element."""
        ...

    @property
    def next_element(self) -> Optional[Union["Tag", "NavigableString"]]:
        """Return the next element in the parse tree."""
        ...

    @property
    def previous_element(self) -> Optional[Union["Tag", "NavigableString"]]:
        """Return the previous element in the parse tree."""
        ...

    def extract(self) -> "NavigableString":
        """Remove this element from the tree and return it."""
        ...

    def replace_with(
        self, *args: Union["Tag", "NavigableString", str]
    ) -> "NavigableString":
        """Replace this element with the given elements."""
        ...

class PageElement:
    """Base class for all parse tree elements."""

    @property
    def parent(self) -> Optional["Tag"]:
        """Return the parent Tag of this element."""
        ...

    @property
    def next_sibling(self) -> Optional[Union["Tag", "NavigableString"]]:
        """Return the next sibling element."""
        ...

    @property
    def previous_sibling(self) -> Optional[Union["Tag", "NavigableString"]]:
        """Return the previous sibling element."""
        ...

    @property
    def next_element(self) -> Optional[Union["Tag", "NavigableString"]]:
        """Return the next element in the parse tree."""
        ...

    @property
    def previous_element(self) -> Optional[Union["Tag", "NavigableString"]]:
        """Return the previous element in the parse tree."""
        ...

    @property
    def name(self) -> Optional[str]:
        """Return the name of this element."""
        ...

    def extract(self) -> "PageElement":
        """Remove this element from the tree and return it."""
        ...

    def replace_with(
        self, *args: Union["Tag", "NavigableString", str]
    ) -> "PageElement":
        """Replace this element with the given elements."""
        ...

    def wrap(self, wrap_with: "Tag") -> "Tag":
        """Wrap this element in the given tag."""
        ...

    def unwrap(self) -> Optional["PageElement"]:
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
        name: Optional[
            Union[str, List[str], re.Pattern[str], Callable[[str], bool], bool]
        ] = None,
        attrs: Optional[Union[Dict[str, Any], str]] = None,
        recursive: bool = True,
        string: Optional[Union[str, re.Pattern[str]]] = None,
        **kwargs: Any,
    ) -> Optional["Tag"]:
        """Find the first matching element."""
        ...

    def find_all(
        self,
        name: Optional[
            Union[str, List[str], re.Pattern[str], Callable[[str], bool], bool]
        ] = None,
        attrs: Optional[Union[Dict[str, Any], str]] = None,
        recursive: bool = True,
        string: Optional[Union[str, re.Pattern[str]]] = None,
        limit: Optional[int] = None,
        **kwargs: Any,
    ) -> "ResultSet[Tag]":
        """Find all matching elements."""
        ...

    def select(self, selector: str) -> List["Tag"]:
        """Find elements using CSS selector."""
        ...

    def select_one(self, selector: str) -> Optional["Tag"]:
        """Find the first element using CSS selector."""
        ...

    def find_previous(
        self,
        name: Optional[
            Union[str, List[str], re.Pattern[str], Callable[[str], bool], bool]
        ] = None,
        attrs: Optional[Union[Dict[str, Any], str]] = None,
        string: Optional[Union[str, re.Pattern[str]]] = None,
        **kwargs: Any,
    ) -> Optional["Tag"]:
        """Find the previous matching element."""
        ...

class Tag(PageElement):
    """A Tag represents an HTML or XML tag that is part of a parse tree."""

    name: str
    attrs: Dict[str, Union[str, List[str]]]
    contents: List[Union["Tag", NavigableString]]
    string: Optional[NavigableString]

    def __init__(
        self,
        parser: Any = None,
        builder: Any = None,
        name: Optional[str] = None,
        namespace: Optional[str] = None,
        prefix: Optional[str] = None,
        attrs: Optional[Dict[str, Any]] = None,
        parent: Optional["Tag"] = None,
        previous: Optional[Union["Tag", NavigableString]] = None,
        is_xml: Optional[bool] = None,
        sourceline: Optional[int] = None,
        sourcepos: Optional[int] = None,
        can_be_empty_element: Optional[bool] = None,
        cdata_list_attributes: Optional[List[str]] = None,
        preserve_whitespace_tags: Optional[List[str]] = None,
        interesting_string_types: Optional[type] = None,
        namespaces: Optional[Dict[str, str]] = None,
    ) -> None:
        """Initialize a new Tag."""
        ...
    # Navigation methods
    def find(
        self,
        name: Optional[
            Union[str, List[str], re.Pattern[str], Callable[[str], bool], bool]
        ] = None,
        attrs: Optional[Union[Dict[str, Any], str]] = None,
        recursive: bool = True,
        string: Optional[Union[str, re.Pattern[str]]] = None,
        **kwargs: Any,
    ) -> Optional["Tag"]:
        """Find the first matching element."""
        ...

    def find_all(
        self,
        name: Optional[
            Union[str, List[str], re.Pattern[str], Callable[[str], bool], bool]
        ] = None,
        attrs: Optional[Union[Dict[str, Any], str]] = None,
        recursive: bool = True,
        string: Optional[Union[str, re.Pattern[str]]] = None,
        limit: Optional[int] = None,
        **kwargs: Any,
    ) -> "ResultSet[Tag]":
        """Find all matching elements."""
        ...

    def select(self, selector: str) -> List["Tag"]:
        """Find elements using CSS selector."""
        ...

    def select_one(self, selector: str) -> Optional["Tag"]:
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

    def __getitem__(self, key: str) -> Union[str, List[str]]:
        """Get an attribute value using bracket notation."""
        ...

    def __setitem__(self, key: str, value: Union[str, List[str]]) -> None:
        """Set an attribute value using bracket notation."""
        ...

    def __delitem__(self, key: str) -> None:
        """Delete an attribute using bracket notation."""
        ...

    def __contains__(self, key: str) -> bool:
        """Check if an attribute exists."""
        ...
    # Tree modification methods
    def append(self, tag: Union["Tag", NavigableString, str]) -> None:
        """Append a child element."""
        ...

    def insert(
        self, position: int, new_child: Union["Tag", NavigableString, str]
    ) -> None:
        """Insert a child element at the specified position."""
        ...

    def insert_before(self, *args: Union["Tag", NavigableString, str]) -> None:
        """Insert elements before this element."""
        ...

    def insert_after(self, *args: Union["Tag", NavigableString, str]) -> None:
        """Insert elements after this element."""
        ...

    def clear(self, decompose: bool = False) -> None:
        """Remove all children from this element."""
        ...

    def extract(self) -> "Tag":
        """Remove this element from the tree and return it."""
        ...

    def decompose(self) -> None:
        """Destroy this element and its children."""
        ...

    def replace_with(self, *args: Union["Tag", NavigableString, str]) -> "Tag":
        """Replace this element with the given elements."""
        ...

    def wrap(self, wrap_with: "Tag") -> "Tag":
        """Wrap this element in the given tag."""
        ...

    def unwrap(self) -> Optional["Tag"]:
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
    def __iter__(self) -> Iterator[Union["Tag", NavigableString]]:
        """Iterate over direct children."""
        ...

    def children(self) -> Iterator[Union["Tag", NavigableString]]:
        """Iterate over direct children."""
        ...

    def descendants(self) -> Iterator[Union["Tag", NavigableString]]:
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
        namespace: Optional[str] = None,
        nsprefix: Optional[str] = None,
        attrs: Optional[Dict[str, Any]] = None,
        sourceline: Optional[int] = None,
        sourcepos: Optional[int] = None,
        **kwattrs: Any,
    ) -> "Tag":
        """Create a new tag."""
        ...

    def new_string(self, s: str, subclass: type = NavigableString) -> NavigableString:
        """Create a new NavigableString."""
        ...

class ResultSet(List[Tag]):
    """A ResultSet is just a list that keeps track of the SoupStrainer that created it."""

    def __init__(self, source: Any, result: Iterable[Tag] = ()) -> None:
        """Initialize a new ResultSet."""
        ...

class BeautifulSoup(Tag):
    """The BeautifulSoup class turns a document into a tree of Python objects."""

    def __init__(
        self,
        markup: Union[str, bytes] = "",
        features: Optional[Union[str, List[str]]] = None,
        builder: Any = None,
        parse_only: Any = None,
        from_encoding: Optional[str] = None,
        exclude_encodings: Optional[List[str]] = None,
        element_classes: Optional[Dict[type, type]] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize a new BeautifulSoup parser."""
        ...
    # Factory methods for creating new tags
    def new_tag(
        self,
        name: str,
        namespace: Optional[str] = None,
        nsprefix: Optional[str] = None,
        attrs: Optional[Dict[str, Any]] = None,
        sourceline: Optional[int] = None,
        sourcepos: Optional[int] = None,
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
        indent_level: Optional[int] = None,
        formatter: Union[str, Callable[[str], str]] = "minimal",
        errors: str = "xmlcharrefreplace",
    ) -> bytes:
        """Encode the document as bytes."""
        ...

    def decode(
        self,
        indent_level: Optional[int] = None,
        eventual_encoding: str = "utf-8",
        formatter: Union[str, Callable[[str], str]] = "minimal",
    ) -> str:
        """Decode the document as a string."""
        ...

# Type aliases for common usage patterns
TagOrString = Union[Tag, NavigableString]
TagOrElement = Union[Tag, PageElement, NavigableString]
