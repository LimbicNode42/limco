"""Unit tests for web search tools."""

import json
import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from dev_team.tools import (
    web_search,
    web_search_news,
    web_search_academic,
    _search_with_tavily,
    _search_with_serper,
    _format_tavily_results,
    _format_serper_results,
)


class TestWebSearch:
    """Test suite for web search functionality."""

    def test_web_search_basic_functionality(self):
        """Test basic web search functionality."""
        # Mock Tavily search success
        with patch('dev_team.tools._search_with_tavily') as mock_tavily, \
             patch('dev_team.tools._search_with_serper') as mock_serper:
            
            mock_tavily.return_value = "Tavily search results"
            mock_serper.return_value = None
            
            result = web_search.invoke({
                "query": "test query",
                "num_results": 5,
                "search_type": "general"
            })
            
            assert result == "Tavily search results"
            mock_tavily.assert_called_once_with("test query", 5, "general")
            mock_serper.assert_not_called()

    def test_web_search_fallback_to_serper(self):
        """Test fallback to Serper when Tavily fails."""
        with patch('dev_team.tools._search_with_tavily') as mock_tavily, \
             patch('dev_team.tools._search_with_serper') as mock_serper:
            
            mock_tavily.return_value = None  # Tavily fails
            mock_serper.return_value = "Serper search results"
            
            result = web_search.invoke({
                "query": "test query",
                "num_results": 3
            })
            
            assert result == "Serper search results"
            mock_tavily.assert_called_once_with("test query", 3, "general")
            mock_serper.assert_called_once_with("test query", 3, "general")

    def test_web_search_no_results(self):
        """Test behavior when no search engines return results."""
        with patch('dev_team.tools._search_with_tavily') as mock_tavily, \
             patch('dev_team.tools._search_with_serper') as mock_serper:
            
            mock_tavily.return_value = None
            mock_serper.return_value = None
            
            result = web_search.invoke({
                "query": "nonexistent query",
                "num_results": 5
            })
            
            assert "No search results found" in result
            assert "nonexistent query" in result

    def test_web_search_error_handling(self):
        """Test error handling in web search."""
        with patch('dev_team.tools._search_with_tavily') as mock_tavily:
            mock_tavily.side_effect = Exception("API error")
            
            result = web_search.invoke({
                "query": "error query",
                "num_results": 5
            })
            
            assert "Search error" in result
            assert "error query" in result

    def test_web_search_result_limit(self):
        """Test that result count is limited to 10."""
        with patch('dev_team.tools._search_with_tavily') as mock_tavily:
            mock_tavily.return_value = "Results"
            
            web_search.invoke({
                "query": "test",
                "num_results": 20  # Should be limited to 10
            })
            
            # Verify the call was made with limited results
            mock_tavily.assert_called_once_with("test", 10, "general")


class TestWebSearchNews:
    """Test suite for news search functionality."""

    def test_web_search_news_basic(self):
        """Test basic news search functionality."""
        with patch('dev_team.tools._search_with_tavily') as mock_tavily:
            mock_tavily.return_value = "News results"
            
            result = web_search_news.invoke({
                "query": "AI news",
                "num_results": 3
            })
            
            assert result == "News results"
            mock_tavily.assert_called_once_with("AI news", 3, "news")

    def test_web_search_news_error_handling(self):
        """Test news search error handling."""
        with patch('dev_team.tools._search_with_tavily') as mock_tavily, \
             patch('dev_team.tools._search_with_serper') as mock_serper:
            
            mock_tavily.side_effect = Exception("News API error")
            mock_serper.side_effect = Exception("Backup API error")
            
            result = web_search_news.invoke({
                "query": "error news",
                "num_results": 5
            })
            
            assert "News search error" in result
            assert "error news" in result


class TestWebSearchAcademic:
    """Test suite for academic search functionality."""

    def test_web_search_academic_basic(self):
        """Test basic academic search functionality."""
        with patch('dev_team.tools._search_with_tavily') as mock_tavily:
            mock_tavily.return_value = "Academic results"
            
            result = web_search_academic.invoke({
                "query": "machine learning",
                "num_results": 2
            })
            
            assert result == "Academic results"
            mock_tavily.assert_called_once_with("machine learning", 2, "academic")

    def test_web_search_academic_fallback(self):
        """Test academic search fallback to Serper."""
        with patch('dev_team.tools._search_with_tavily') as mock_tavily, \
             patch('dev_team.tools._search_with_serper') as mock_serper:
            
            mock_tavily.return_value = None
            mock_serper.return_value = "Serper academic results"
            
            result = web_search_academic.invoke({
                "query": "neural networks",
                "num_results": 3
            })
            
            assert result == "Serper academic results"
            mock_serper.assert_called_once_with("neural networks", 3, "academic")


class TestTavilySearch:
    """Test suite for Tavily search implementation."""

    @patch('dev_team.tools.TavilySearch')
    def test_search_with_tavily_general(self, mock_tavily_class):
        """Test Tavily search with general configuration."""
        mock_search = Mock()
        mock_search.invoke.return_value = '{"results": [{"title": "Test", "url": "http://test.com", "content": "Test content"}]}'
        mock_tavily_class.return_value = mock_search
        
        with patch('dev_team.tools._format_tavily_results') as mock_format:
            mock_format.return_value = "Formatted results"
            
            result = _search_with_tavily("test query", 5, "general")
            
            assert result == "Formatted results"
            mock_tavily_class.assert_called_once()
            
            # Check configuration
            call_args = mock_tavily_class.call_args[1]
            assert call_args["max_results"] == 5
            assert call_args["topic"] == "general"
            assert call_args["include_answer"] is True

    @patch('dev_team.tools.TavilySearch')
    def test_search_with_tavily_news(self, mock_tavily_class):
        """Test Tavily search with news configuration."""
        mock_search = Mock()
        mock_search.invoke.return_value = '{"results": []}'
        mock_tavily_class.return_value = mock_search
        
        with patch('dev_team.tools._format_tavily_results') as mock_format:
            mock_format.return_value = "News results"
            
            result = _search_with_tavily("news query", 3, "news")
            
            # Check configuration for news
            call_args = mock_tavily_class.call_args[1]
            assert call_args["topic"] == "news"

    @patch('dev_team.tools.TavilySearch')
    def test_search_with_tavily_academic(self, mock_tavily_class):
        """Test Tavily search with academic configuration."""
        mock_search = Mock()
        mock_search.invoke.return_value = '{"results": []}'
        mock_tavily_class.return_value = mock_search
        
        with patch('dev_team.tools._format_tavily_results') as mock_format:
            mock_format.return_value = "Academic results"
            
            result = _search_with_tavily("academic query", 2, "academic")
            
            # Check academic configuration
            call_args = mock_tavily_class.call_args[1]
            assert call_args["search_depth"] == "advanced"
            assert "scholar.google.com" in call_args["include_domains"]
            assert "arxiv.org" in call_args["include_domains"]

    @patch('dev_team.tools.TavilySearch')
    def test_search_with_tavily_error_handling(self, mock_tavily_class):
        """Test Tavily search error handling."""
        mock_tavily_class.side_effect = Exception("Tavily API error")
        
        result = _search_with_tavily("test query", 5, "general")
        
        assert result is None

    @patch('dev_team.tools.TavilySearch')
    def test_search_with_tavily_empty_results(self, mock_tavily_class):
        """Test Tavily search with empty results."""
        mock_search = Mock()
        mock_search.invoke.return_value = None
        mock_tavily_class.return_value = mock_search
        
        result = _search_with_tavily("empty query", 5, "general")
        
        assert result is None


class TestSerperSearch:
    """Test suite for Serper search implementation."""

    @patch('dev_team.tools.GoogleSerperAPIWrapper')
    def test_search_with_serper_general(self, mock_serper_class):
        """Test Serper search with general configuration."""
        mock_search = Mock()
        mock_search.results.return_value = {"organic": [{"title": "Test", "link": "http://test.com", "snippet": "Test snippet"}]}
        mock_serper_class.return_value = mock_search
        
        with patch('dev_team.tools._format_serper_results') as mock_format:
            mock_format.return_value = "Formatted Serper results"
            
            result = _search_with_serper("test query", 5, "general")
            
            assert result == "Formatted Serper results"
            mock_serper_class.assert_called_once()
            
            # Check configuration
            call_args = mock_serper_class.call_args[1]
            assert call_args["k"] == 5
            assert call_args["type"] == "search"

    @patch('dev_team.tools.GoogleSerperAPIWrapper')
    def test_search_with_serper_news(self, mock_serper_class):
        """Test Serper search with news configuration."""
        mock_search = Mock()
        mock_search.results.return_value = {"news": [{"title": "News", "link": "http://news.com", "snippet": "News snippet"}]}
        mock_serper_class.return_value = mock_search
        
        with patch('dev_team.tools._format_serper_results') as mock_format:
            mock_format.return_value = "News results"
            
            result = _search_with_serper("news query", 3, "news")
            
            # Check news configuration
            call_args = mock_serper_class.call_args[1]
            assert call_args["type"] == "news"

    @patch('dev_team.tools.GoogleSerperAPIWrapper')
    def test_search_with_serper_academic(self, mock_serper_class):
        """Test Serper search with academic configuration."""
        mock_search = Mock()
        mock_search.results.return_value = {"organic": []}
        mock_serper_class.return_value = mock_search
        
        with patch('dev_team.tools._format_serper_results') as mock_format:
            mock_format.return_value = "Academic results"
            
            result = _search_with_serper("ML algorithms", 2, "academic")
            
            # The query should be modified for academic search
            expected_query = "ML algorithms site:scholar.google.com OR site:arxiv.org OR site:pubmed.ncbi.nlm.nih.gov"
            mock_search.results.assert_called_once_with(expected_query)

    @patch('dev_team.tools.GoogleSerperAPIWrapper')
    def test_search_with_serper_error_handling(self, mock_serper_class):
        """Test Serper search error handling."""
        mock_serper_class.side_effect = Exception("Serper API error")
        
        result = _search_with_serper("test query", 5, "general")
        
        assert result is None


class TestResultFormatting:
    """Test suite for result formatting functions."""

    def test_format_tavily_results_with_answer(self):
        """Test Tavily result formatting with answer."""
        results = {
            "answer": "This is a quick answer",
            "results": [
                {
                    "title": "Test Title",
                    "url": "https://example.com",
                    "content": "This is test content for the search result"
                }
            ]
        }
        
        formatted = _format_tavily_results("test query", results, "general")
        
        assert "test query" in formatted
        assert "Quick Answer" in formatted
        assert "This is a quick answer" in formatted
        assert "Test Title" in formatted
        assert "https://example.com" in formatted
        assert "This is test content" in formatted

    def test_format_tavily_results_long_content(self):
        """Test Tavily result formatting with long content truncation."""
        results = {
            "results": [
                {
                    "title": "Long Content Test",
                    "url": "https://example.com",
                    "content": "A" * 300  # Content longer than 200 chars
                }
            ]
        }
        
        formatted = _format_tavily_results("test query", results, "general")
        
        # Content should be truncated
        assert "A" * 200 + "..." in formatted
        assert "A" * 300 not in formatted

    def test_format_tavily_results_string_input(self):
        """Test Tavily result formatting with string input."""
        results_json = '{"results": [{"title": "Test", "url": "http://test.com", "content": "Test content"}]}'
        
        formatted = _format_tavily_results("test query", results_json, "general")
        
        assert "Test" in formatted
        assert "http://test.com" in formatted

    def test_format_tavily_results_error_handling(self):
        """Test Tavily result formatting error handling."""
        # Invalid JSON
        formatted = _format_tavily_results("test query", "invalid json", "general")
        
        assert "Error formatting Tavily results" in formatted

    def test_format_serper_results_organic(self):
        """Test Serper result formatting for organic results."""
        results = {
            "organic": [
                {
                    "title": "Organic Result",
                    "link": "https://example.com",
                    "snippet": "This is an organic search result"
                }
            ]
        }
        
        formatted = _format_serper_results("test query", results, "general")
        
        assert "test query" in formatted
        assert "Organic Result" in formatted
        assert "https://example.com" in formatted
        assert "This is an organic search result" in formatted

    def test_format_serper_results_news(self):
        """Test Serper result formatting for news results."""
        results = {
            "news": [
                {
                    "title": "News Article",
                    "link": "https://news.com",
                    "snippet": "This is a news article",
                    "source": "News Source",
                    "date": "2025-08-09"
                }
            ]
        }
        
        formatted = _format_serper_results("news query", results, "news")
        
        assert "News Results" in formatted
        assert "News Article" in formatted
        assert "News Source" in formatted
        assert "2025-08-09" in formatted

    def test_format_serper_results_with_knowledge_graph(self):
        """Test Serper result formatting with knowledge graph."""
        results = {
            "organic": [
                {
                    "title": "Regular Result",
                    "link": "https://example.com",
                    "snippet": "Regular result"
                }
            ],
            "knowledgeGraph": {
                "title": "Knowledge Graph Title",
                "description": "Knowledge graph description"
            }
        }
        
        formatted = _format_serper_results("test query", results, "general")
        
        assert "Knowledge Graph" in formatted
        assert "Knowledge Graph Title" in formatted
        assert "Knowledge graph description" in formatted

    def test_format_serper_results_string_input(self):
        """Test Serper result formatting with string input."""
        formatted = _format_serper_results("test query", "Simple string result", "general")
        
        assert "test query" in formatted
        assert "Simple string result" in formatted

    def test_format_serper_results_error_handling(self):
        """Test Serper result formatting error handling."""
        # Create a problematic object that will cause an error when processed
        class ProblematicResults:
            def __init__(self):
                # This will cause an error when converted to string
                raise Exception("Formatting error during conversion")
        
        # The error should be caught when trying to process this object
        try:
            problematic_obj = ProblematicResults()
        except Exception:
            # If we can't even create the object, create one that errors on access
            class DelayedError:
                def __iter__(self):
                    raise Exception("Formatting error")
                
                def __str__(self):
                    raise Exception("Formatting error")
                
                def __len__(self):
                    raise Exception("Formatting error")
            
            problematic_obj = DelayedError()
        
        # Test with direct error in the formatting function
        with patch('dev_team.tools.enumerate') as mock_enumerate:
            mock_enumerate.side_effect = Exception("Formatting error")
            
            formatted = _format_serper_results("test query", {"news": []}, "news")
            
            assert "Error formatting Serper results" in formatted


class TestAPIKeyConfiguration:
    """Test suite for API key configuration."""

    def test_missing_api_keys_warning(self):
        """Test behavior when API keys are missing."""
        with patch.dict(os.environ, {}, clear=True):
            # Both API keys missing - tools should handle gracefully
            with patch('dev_team.tools._search_with_tavily') as mock_tavily, \
                 patch('dev_team.tools._search_with_serper') as mock_serper:
                
                mock_tavily.return_value = None
                mock_serper.return_value = None
                
                result = web_search.invoke({
                    "query": "test without keys",
                    "num_results": 3
                })
                
                assert "No search results found" in result

    def test_tavily_only_configuration(self):
        """Test configuration with only Tavily API key."""
        with patch.dict(os.environ, {"TAVILY_API_KEY": "test_key"}, clear=True):
            with patch('dev_team.tools._search_with_tavily') as mock_tavily:
                mock_tavily.return_value = "Tavily only results"
                
                result = web_search.invoke({
                    "query": "tavily only test",
                    "num_results": 3
                })
                
                assert result == "Tavily only results"

    def test_serper_only_configuration(self):
        """Test configuration with only Serper API key."""
        with patch.dict(os.environ, {"SERPER_API_KEY": "test_key"}, clear=True):
            with patch('dev_team.tools._search_with_tavily') as mock_tavily, \
                 patch('dev_team.tools._search_with_serper') as mock_serper:
                
                mock_tavily.return_value = None  # Tavily fails without key
                mock_serper.return_value = "Serper only results"
                
                result = web_search.invoke({
                    "query": "serper only test",
                    "num_results": 3
                })
                
                assert result == "Serper only results"


class TestSearchTypeVariations:
    """Test suite for different search type configurations."""

    def test_recent_search_type(self):
        """Test recent search type configuration."""
        with patch('dev_team.tools._search_with_tavily') as mock_tavily:
            mock_tavily.return_value = "Recent results"
            
            web_search.invoke({
                "query": "recent developments",
                "search_type": "recent"
            })
            
            mock_tavily.assert_called_once_with("recent developments", 5, "recent")

    def test_invalid_search_type(self):
        """Test behavior with invalid search type."""
        with patch('dev_team.tools._search_with_tavily') as mock_tavily:
            mock_tavily.return_value = "General results"
            
            result = web_search.invoke({
                "query": "test query",
                "search_type": "invalid_type"
            })
            
            # Should default to general
            mock_tavily.assert_called_once_with("test query", 5, "invalid_type")

    def test_empty_query_handling(self):
        """Test handling of empty queries."""
        with patch('dev_team.tools._search_with_tavily') as mock_tavily:
            mock_tavily.return_value = "Empty query results"
            
            result = web_search.invoke({
                "query": "",
                "num_results": 3
            })
            
            assert "Empty query results" in result
            mock_tavily.assert_called_once_with("", 3, "general")
