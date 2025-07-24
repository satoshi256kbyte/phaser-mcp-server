"""Unit tests for Pydantic data models validation.

This module contains tests for data model validation, focusing on edge cases
and error handling.
"""

import pytest
from pydantic import ValidationError

from phaser_mcp_server.models import ApiReference, DocumentationPage


class TestModelValidation:
    """Test cases for model validation."""

    def test_invalid_types(self):
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

        # Test ApiReference with invalid types
        with pytest.raises(ValidationError):
            ApiReference(
                class_name=123,  # Not a string
                url="https://docs.phaser.io/api/test",
                description="Test description",
            )

        with pytest.raises(ValidationError):
            ApiReference(
                class_name="Test",
                url="https://docs.phaser.io/api/test",
                description="Test description",
                methods="not_a_list",  # String instead of list
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
