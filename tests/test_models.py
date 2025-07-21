"""Unit tests for Pydantic data models.

This module contains comprehensive tests for all data models including
validation tests, error cases, and edge cases.
"""

from datetime import datetime
from typing import Any, Dict

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
            content="# Getting Started\n\nThis guide will help you get started with Phaser.",
            last_modified=datetime(2024, 1, 15, 10, 30, 0),
            content_type="text/html",
            word_count=12
        )
        
        assert page.url == "https://docs.phaser.io/phaser/getting-started"
        assert page.title == "Getting Started with Phaser"
        assert page.content == "# Getting Started\n\nThis guide will help you get started with Phaser."
        assert page.last_modified == datetime(2024, 1, 15, 10, 30, 0)
        assert page.content_type == "text/html"
        assert page.word_count == 12
    
    def test_documentation_page_with_defaults(self):
        """Test creating DocumentationPage with default values."""
        page = DocumentationPage(
            url="https://docs.phaser.io/phaser/sprites",
            title="Working with Sprites",
            content="Sprites are the basic building blocks of games."
        )
        
        assert page.last_modified is None
        assert page.content_type == "text/html"
        assert page.word_count == 8  # Auto-calculated from content
    
    def test_word_count_auto_calculation(self):
        """Test automatic word count calculation."""
        content = "This is a test content with exactly ten words here."
        page = DocumentationPage(
            url="https://docs.phaser.io/phaser/test",
            title="Test Page",
            content=content
        )
        
        assert page.word_count == 10
    
    def test_word_count_manual_override(self):
        """Test that manually set word count is preserved."""
        page = DocumentationPage(
            url="https://docs.phaser.io/phaser/test",
            title="Test Page",
            content="Short content",
            word_count=100  # Manually set, different from actual
        )
        
        assert page.word_count == 100  # Should preserve manual value
    
    def test_title_cleaning(self):
        """Test title cleaning functionality."""
        test_cases = [
            ("Getting Started - Phaser", "Getting Started"),
            ("API Reference | Phaser Documentation", "API Reference"),
            ("Sprites :: Phaser Documentation", "Sprites"),
            ("  Whitespace Title  ", "Whitespace Title"),
            ("Normal Title", "Normal Title")
        ]
        
        for input_title, expected_title in test_cases:
            page = DocumentationPage(
                url="https://docs.phaser.io/phaser/test",
                title=input_title,
                content="Test content"
            )
            assert page.title == expected_title
    
    def test_invalid_url_schemes(self):
        """Test validation of URL schemes."""
        invalid_urls = [
            "ftp://docs.phaser.io/phaser/test",
            "file:///local/path",
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>"
        ]
        
        for invalid_url in invalid_urls:
            with pytest.raises(ValidationError) as exc_info:
                DocumentationPage(
                    url=invalid_url,
                    title="Test",
                    content="Test content"
                )
            assert "URL must use http or https scheme" in str(exc_info.value)
    
    def test_invalid_domains(self):
        """Test validation of allowed domains."""
        invalid_domains = [
            "https://malicious.com/phaser/docs",
            "https://example.com/docs",
            "https://phaser.fake.io/docs",
            "https://docs.phaser.evil.com/api"
        ]
        
        for invalid_url in invalid_domains:
            with pytest.raises(ValidationError) as exc_info:
                DocumentationPage(
                    url=invalid_url,
                    title="Test",
                    content="Test content"
                )
            assert "URL must be from allowed domains" in str(exc_info.value)
    
    def test_valid_domains(self):
        """Test that valid Phaser domains are accepted."""
        valid_urls = [
            "https://docs.phaser.io/phaser/getting-started",
            "http://docs.phaser.io/api/Phaser.Sprite",
            "https://phaser.io/tutorials",
            "https://www.phaser.io/examples"
        ]
        
        for valid_url in valid_urls:
            page = DocumentationPage(
                url=valid_url,
                title="Test",
                content="Test content"
            )
            assert page.url == valid_url
    
    def test_empty_url_validation(self):
        """Test validation of empty URLs."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentationPage(
                url="",
                title="Test",
                content="Test content"
            )
        assert "String should have at least 1 character" in str(exc_info.value)
    
    def test_empty_title_validation(self):
        """Test validation of empty titles."""
        invalid_titles = ["", "   ", "\t\n"]
        
        for invalid_title in invalid_titles:
            with pytest.raises(ValidationError) as exc_info:
                DocumentationPage(
                    url="https://docs.phaser.io/phaser/test",
                    title=invalid_title,
                    content="Test content"
                )
            if invalid_title == "":
                assert "String should have at least 1 character" in str(exc_info.value)
            else:
                assert "Title cannot be empty or whitespace only" in str(exc_info.value)
    
    def test_empty_content_validation(self):
        """Test validation of empty content."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentationPage(
                url="https://docs.phaser.io/phaser/test",
                title="Test",
                content=""
            )
        assert "at least 1 character" in str(exc_info.value)
    
    def test_url_length_validation(self):
        """Test URL length validation."""
        long_url = "https://docs.phaser.io/" + "a" * 2050
        
        with pytest.raises(ValidationError) as exc_info:
            DocumentationPage(
                url=long_url,
                title="Test",
                content="Test content"
            )
        assert "at most 2048 characters" in str(exc_info.value)
    
    def test_title_length_validation(self):
        """Test title length validation."""
        long_title = "A" * 501
        
        with pytest.raises(ValidationError) as exc_info:
            DocumentationPage(
                url="https://docs.phaser.io/phaser/test",
                title=long_title,
                content="Test content"
            )
        assert "at most 500 characters" in str(exc_info.value)
    
    def test_negative_word_count_validation(self):
        """Test that negative word count is rejected."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentationPage(
                url="https://docs.phaser.io/phaser/test",
                title="Test",
                content="Test content",
                word_count=-1
            )
        assert "greater than or equal to 0" in str(exc_info.value)


class TestSearchResult:
    """Test cases for SearchResult model."""
    
    def test_valid_search_result_creation(self):
        """Test creating a valid SearchResult instance."""
        result = SearchResult(
            rank_order=1,
            url="https://docs.phaser.io/phaser/sprites",
            title="Working with Sprites",
            snippet="Sprites are the basic building blocks of games.",
            relevance_score=0.95
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
            title="Animation System"
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
            (None, None)  # None stays None
        ]
        
        for input_snippet, expected_snippet in test_cases:
            result = SearchResult(
                rank_order=1,
                url="https://docs.phaser.io/phaser/test",
                title="Test",
                snippet=input_snippet
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
                    title="Test"
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
                    relevance_score=invalid_score
                )
            assert "less than or equal to 1" in str(exc_info.value) or "greater than or equal to 0" in str(exc_info.value)
    
    def test_valid_relevance_scores(self):
        """Test valid relevance score values."""
        valid_scores = [0.0, 0.5, 1.0, 0.123, 0.999]
        
        for valid_score in valid_scores:
            result = SearchResult(
                rank_order=1,
                url="https://docs.phaser.io/phaser/test",
                title="Test",
                relevance_score=valid_score
            )
            assert result.relevance_score == valid_score
    
    def test_empty_url_validation(self):
        """Test validation of empty URLs in search results."""
        with pytest.raises(ValidationError) as exc_info:
            SearchResult(
                rank_order=1,
                url="",
                title="Test"
            )
        assert "String should have at least 1 character" in str(exc_info.value)
    
    def test_invalid_url_schemes_search(self):
        """Test validation of URL schemes in search results."""
        invalid_urls = [
            "ftp://docs.phaser.io/test",
            "file:///local/path",
            "javascript:void(0)"
        ]
        
        for invalid_url in invalid_urls:
            with pytest.raises(ValidationError) as exc_info:
                SearchResult(
                    rank_order=1,
                    url=invalid_url,
                    title="Test"
                )
            assert "URL must use http or https scheme" in str(exc_info.value)
    
    def test_snippet_length_validation(self):
        """Test snippet length validation."""
        long_snippet = "A" * 1001
        
        with pytest.raises(ValidationError) as exc_info:
            SearchResult(
                rank_order=1,
                url="https://docs.phaser.io/phaser/test",
                title="Test",
                snippet=long_snippet
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
                "sprite.setTexture('enemy');"
            ],
            parent_class="GameObject",
            namespace="Phaser.GameObjects"
        )
        
        assert api_ref.class_name == "Sprite"
        assert api_ref.url == "https://docs.phaser.io/api/Phaser.GameObjects.Sprite"
        assert api_ref.description == "A Sprite Game Object is used to display textures."
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
            description="The Scene Manager is responsible for creating, processing and updating all of the Scenes in a Phaser Game instance."
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
            "Audio3D"
        ]
        
        for valid_name in valid_names:
            api_ref = ApiReference(
                class_name=valid_name,
                url="https://docs.phaser.io/api/test",
                description="Test description"
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
            "Class#Name"   # Hash not allowed
        ]
        
        for invalid_name in invalid_names:
            with pytest.raises(ValidationError) as exc_info:
                ApiReference(
                    class_name=invalid_name,
                    url="https://docs.phaser.io/api/test",
                    description="Test description"
                )
            if invalid_name == "":
                assert "String should have at least 1 character" in str(exc_info.value)
            elif invalid_name.strip():
                assert "Class name contains invalid characters" in str(exc_info.value)
            else:
                assert "Class name cannot be empty or whitespace only" in str(exc_info.value)
    
    def test_api_url_validation(self):
        """Test API URL validation."""
        # Valid API URLs
        valid_urls = [
            "https://docs.phaser.io/api/Phaser.Scene",
            "http://docs.phaser.io/api/Phaser.GameObjects.Sprite",
            "https://docs.phaser.io/api/Phaser.Sound.WebAudioSoundManager"
        ]
        
        for valid_url in valid_urls:
            api_ref = ApiReference(
                class_name="Test",
                url=valid_url,
                description="Test description"
            )
            assert api_ref.url == valid_url
    
    def test_invalid_api_urls(self):
        """Test validation of invalid API URLs."""
        # URLs that don't contain /api/ path from docs.phaser.io
        invalid_urls = [
            "https://docs.phaser.io/phaser/getting-started",
            "https://docs.phaser.io/tutorials/sprites",
        ]
        
        for invalid_url in invalid_urls:
            with pytest.raises(ValidationError) as exc_info:
                ApiReference(
                    class_name="Test",
                    url=invalid_url,
                    description="Test description"
                )
            assert "URL should be an API reference path" in str(exc_info.value)
        
        # Test that phaser.io URLs are accepted (not docs.phaser.io)
        valid_url = "https://phaser.io/examples"
        api_ref = ApiReference(
            class_name="Test",
            url=valid_url,
            description="Test description"
        )
        assert api_ref.url == valid_url
    
    def test_methods_properties_deduplication(self):
        """Test deduplication of methods and properties lists."""
        api_ref = ApiReference(
            class_name="Test",
            url="https://docs.phaser.io/api/test",
            description="Test description",
            methods=["method1", "method2", "method1", "method3", "method2"],  # Duplicates
            properties=["prop1", "prop2", "prop1", "prop3"]  # Duplicates
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
            properties=["prop1", "", "  prop2  ", "prop3"]
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
                "sprite.destroy();"
            ]
        )
        
        # Should clean whitespace and remove empty examples
        expected_examples = [
            "const sprite = new Sprite();",
            "sprite.setPosition(100, 100);",
            "sprite.destroy();"
        ]
        assert api_ref.examples == expected_examples
    
    def test_empty_description_validation(self):
        """Test validation of empty description."""
        with pytest.raises(ValidationError) as exc_info:
            ApiReference(
                class_name="Test",
                url="https://docs.phaser.io/api/test",
                description=""
            )
        assert "at least 1 character" in str(exc_info.value)
    
    def test_class_name_length_validation(self):
        """Test class name length validation."""
        long_name = "A" * 201
        
        with pytest.raises(ValidationError) as exc_info:
            ApiReference(
                class_name=long_name,
                url="https://docs.phaser.io/api/test",
                description="Test description"
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
                parent_class=long_parent
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
                namespace=long_namespace
            )
        assert "at most 200 characters" in str(exc_info.value)


class TestEdgeCases:
    """Edge case tests for better coverage."""
    
    def test_search_result_malformed_url(self):
        """Test SearchResult with malformed URL."""
        with pytest.raises(ValidationError):
            SearchResult(
                rank_order=1,
                url="not-a-valid-url-at-all",
                title="Test"
            )
    
    def test_api_reference_empty_lists_handling(self):
        """Test ApiReference with various empty list scenarios."""
        # Test with empty strings in lists (should be filtered out)
        api_ref = ApiReference(
            class_name="Test",
            url="https://docs.phaser.io/api/test",
            description="Test description",
            methods=["method1", "", "method2", "   "],  # Mixed with empty and whitespace
            properties=["", "prop1", "  "],
            examples=["", "example1", "   "]
        )
        
        # Should filter out empty and whitespace-only values
        assert api_ref.methods == ["method1", "method2"]
        assert api_ref.properties == ["prop1"]
        assert api_ref.examples == ["example1"]
    
    def test_documentation_page_word_count_edge_cases(self):
        """Test word count calculation with edge cases."""
        # Test with content that has multiple spaces, tabs, newlines
        content = "  Word1   \t\t  Word2\n\n\nWord3  \r\n  Word4  "
        page = DocumentationPage(
            url="https://docs.phaser.io/phaser/test",
            title="Test",
            content=content
        )
        
        # Should count 4 words despite irregular spacing
        assert page.word_count == 4
    
    def test_search_result_snippet_edge_cases(self):
        """Test snippet handling with various edge cases."""
        # Test with snippet containing only whitespace characters
        result = SearchResult(
            rank_order=1,
            url="https://docs.phaser.io/phaser/test",
            title="Test",
            snippet="\t\n\r   \t\n"  # Only whitespace
        )
        
        assert result.snippet is None


class TestModelIntegration:
    """Integration tests for model interactions."""
    
    def test_models_json_serialization(self):
        """Test that all models can be serialized to JSON."""
        # Test DocumentationPage
        page = DocumentationPage(
            url="https://docs.phaser.io/phaser/test",
            title="Test Page",
            content="Test content"
        )
        page_json = page.model_dump()
        assert isinstance(page_json, dict)
        assert page_json["url"] == "https://docs.phaser.io/phaser/test"
        
        # Test SearchResult
        result = SearchResult(
            rank_order=1,
            url="https://docs.phaser.io/phaser/test",
            title="Test Result"
        )
        result_json = result.model_dump()
        assert isinstance(result_json, dict)
        assert result_json["rank_order"] == 1
        
        # Test ApiReference
        api_ref = ApiReference(
            class_name="Test",
            url="https://docs.phaser.io/api/test",
            description="Test description"
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
            "word_count": 2
        }
        page = DocumentationPage(**page_data)
        assert page.url == page_data["url"]
        assert page.word_count == 2
        
        # Test SearchResult
        result_data = {
            "rank_order": 1,
            "url": "https://docs.phaser.io/phaser/test",
            "title": "Test Result",
            "relevance_score": 0.8
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
            "properties": ["x", "y"]
        }
        api_ref = ApiReference(**api_data)
        assert api_ref.class_name == "Sprite"
        assert len(api_ref.methods) == 2
        assert len(api_ref.properties) == 2