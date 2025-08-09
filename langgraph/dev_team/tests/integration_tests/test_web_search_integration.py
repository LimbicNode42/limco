"""Integration tests for web search tools in agent workflows."""

import pytest
from unittest.mock import Mock, patch
from langgraph.graph import StateGraph
from dev_team.states import State
from dev_team.tools import web_search, web_search_news, web_search_academic


class TestWebSearchIntegration:
    """Integration tests for web search tools within agent workflows."""

    def test_web_search_tool_integration(self):
        """Test web search tool integration in agent workflow."""
        # Create a simple state for testing
        initial_state = {
            "messages": [],
            "current_task": "research",
            "context": {}
        }
        
        # Mock the search to return predictable results
        with patch('dev_team.tools._search_with_tavily') as mock_tavily:
            mock_tavily.return_value = "🔍 Mock search results for integration test query"
            
            # Test that the tool can be invoked with proper state
            result = web_search.invoke({
                "query": "integration test query",
                "num_results": 3,
                "search_type": "general"
            })
            
            assert "Mock search results" in result
            assert "integration test query" in result
            mock_tavily.assert_called_once_with("integration test query", 3, "general")

    def test_news_search_workflow_integration(self):
        """Test news search integration in research workflow."""
        with patch('dev_team.tools._search_with_tavily') as mock_tavily:
            mock_tavily.return_value = "📰 Mock news results about AI developments"
            
            # Simulate a researcher agent using news search
            result = web_search_news.invoke({
                "query": "latest AI developments",
                "num_results": 5
            })
            
            assert "Mock news results" in result
            assert "AI developments" in result

    def test_academic_search_workflow_integration(self):
        """Test academic search integration in research workflow."""
        with patch('dev_team.tools._search_with_tavily') as mock_tavily:
            mock_tavily.return_value = "🎓 Mock academic results about machine learning"
            
            # Simulate a researcher agent using academic search
            result = web_search_academic.invoke({
                "query": "machine learning algorithms",
                "num_results": 3
            })
            
            assert "Mock academic results" in result
            assert "machine learning" in result

    def test_search_error_handling_in_workflow(self):
        """Test error handling when search tools fail in workflow."""
        with patch('dev_team.tools._search_with_tavily') as mock_tavily, \
             patch('dev_team.tools._search_with_serper') as mock_serper:
            
            # Both search methods fail
            mock_tavily.side_effect = Exception("API error")
            mock_serper.side_effect = Exception("Backup API error")
            
            # Test that tools handle errors gracefully
            result = web_search.invoke({
                "query": "error test query",
                "num_results": 3
            })
            
            assert "Search error" in result
            assert "error test query" in result

    def test_multiple_search_tools_in_sequence(self):
        """Test using multiple search tools in sequence."""
        with patch('dev_team.tools._search_with_tavily') as mock_tavily:
            # Configure different responses for different search types
            def tavily_side_effect(query, num_results, search_type):
                return f"Mock {search_type} results for {query}"
            
            mock_tavily.side_effect = tavily_side_effect
            
            # Simulate an agent using multiple search tools
            general_result = web_search.invoke({
                "query": "Python programming",
                "search_type": "general"
            })
            
            news_result = web_search_news.invoke({
                "query": "Python programming"
            })
            
            academic_result = web_search_academic.invoke({
                "query": "Python programming"
            })
            
            assert "Mock general results" in general_result
            assert "Mock news results" in news_result
            assert "Mock academic results" in academic_result

    def test_search_tool_state_independence(self):
        """Test that search tools work independently of state."""
        # Test that search tools can be used without complex state dependencies
        with patch('dev_team.tools._search_with_tavily') as mock_tavily:
            mock_tavily.return_value = "Independent search results"
            
            # Test direct tool invocation
            result = web_search.invoke({
                "query": "independent test",
                "num_results": 2
            })
            
            assert "Independent search results" in result

    def test_search_tool_parameter_validation(self):
        """Test parameter validation in search tools."""
        with patch('dev_team.tools._search_with_tavily') as mock_tavily:
            mock_tavily.return_value = "Validation test results"
            
            # Test that num_results is properly limited
            web_search.invoke({
                "query": "validation test",
                "num_results": 50  # Should be limited to 10
            })
            
            # Verify the call was made with limited results
            mock_tavily.assert_called_once_with("validation test", 10, "general")

    def test_search_tool_concurrent_usage(self):
        """Test concurrent usage of search tools."""
        with patch('dev_team.tools._search_with_tavily') as mock_tavily:
            mock_tavily.return_value = "Concurrent search results"
            
            # Simulate multiple agents using search tools concurrently
            import threading
            results = []
            
            def search_worker(query_suffix):
                result = web_search.invoke({
                    "query": f"concurrent test {query_suffix}",
                    "num_results": 3
                })
                results.append(result)
            
            # Create multiple threads
            threads = []
            for i in range(3):
                thread = threading.Thread(target=search_worker, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Verify all searches completed
            assert len(results) == 3
            for result in results:
                assert "Concurrent search results" in result

    def test_search_results_formatting_consistency(self):
        """Test that search results are consistently formatted."""
        with patch('dev_team.tools._search_with_tavily') as mock_tavily:
            # Test with structured Tavily response
            mock_response = {
                "answer": "Test answer",
                "results": [
                    {
                        "title": "Test Title",
                        "url": "https://test.com",
                        "content": "Test content"
                    }
                ]
            }
            
            with patch('dev_team.tools._format_tavily_results') as mock_format:
                mock_format.return_value = "🔍 Formatted test results with emojis and structure"
                mock_tavily.return_value = "🔍 Formatted test results with emojis and structure"
                
                result = web_search.invoke({
                    "query": "formatting test",
                    "num_results": 3
                })
                
                # Verify consistent formatting
                assert "🔍" in result  # Search icon
                assert "Formatted test results" in result

    def test_api_key_environment_handling(self):
        """Test handling of API key environment variables."""
        import os
        
        # Test behavior when keys are available
        original_tavily = os.environ.get("TAVILY_API_KEY")
        original_serper = os.environ.get("SERPER_API_KEY")
        
        try:
            # Set test keys
            os.environ["TAVILY_API_KEY"] = "test_tavily_key"
            os.environ["SERPER_API_KEY"] = "test_serper_key"
            
            with patch('dev_team.tools._search_with_tavily') as mock_tavily:
                mock_tavily.return_value = "Results with API keys"
                
                result = web_search.invoke({
                    "query": "API key test",
                    "num_results": 3
                })
                
                assert "Results with API keys" in result
                
        finally:
            # Restore original environment
            if original_tavily is not None:
                os.environ["TAVILY_API_KEY"] = original_tavily
            elif "TAVILY_API_KEY" in os.environ:
                del os.environ["TAVILY_API_KEY"]
                
            if original_serper is not None:
                os.environ["SERPER_API_KEY"] = original_serper
            elif "SERPER_API_KEY" in os.environ:
                del os.environ["SERPER_API_KEY"]

    def test_search_tool_documentation_consistency(self):
        """Test that search tools have consistent documentation."""
        # Verify that all search tools have proper docstrings
        # Note: LangChain tool wrapper may modify the docstring, so we check the function directly
        assert web_search.func.__doc__ is not None
        assert "search" in web_search.func.__doc__.lower()
        
        assert web_search_news.func.__doc__ is not None
        assert "news" in web_search_news.func.__doc__.lower()
        
        assert web_search_academic.func.__doc__ is not None
        assert "academic" in web_search_academic.func.__doc__.lower()

    def test_large_query_handling(self):
        """Test handling of large search queries."""
        with patch('dev_team.tools._search_with_tavily') as mock_tavily:
            mock_tavily.return_value = "Large query results"
            
            # Test with a very long query
            large_query = "test query " * 100  # 1000+ characters
            
            result = web_search.invoke({
                "query": large_query,
                "num_results": 3
            })
            
            assert "Large query results" in result
            # Verify the tool handles large queries without crashing
            mock_tavily.assert_called_once_with(large_query, 3, "general")

    def test_special_character_query_handling(self):
        """Test handling of queries with special characters."""
        with patch('dev_team.tools._search_with_tavily') as mock_tavily:
            mock_tavily.return_value = "Special character results"
            
            # Test with various special characters
            special_queries = [
                "test & query",
                "test @ symbol",
                "test #hashtag",
                "test (parentheses)",
                "test [brackets]",
                "test {braces}",
                "test / slash",
                "test \\ backslash",
                "test + plus",
                "test = equals",
                "test ? question",
                "test ! exclamation"
            ]
            
            for query in special_queries:
                result = web_search.invoke({
                    "query": query,
                    "num_results": 1
                })
                
                assert "Special character results" in result
