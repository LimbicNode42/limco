"""Research and communication tools for web search and information gathering."""

import json
import os
from typing import Any, Optional
from langchain_core.tools import tool
from langchain_community.utilities import GoogleSerperAPIWrapper
from langchain_tavily import TavilySearch


@tool
def web_search(query: str, num_results: int = 5, search_type: str = "general") -> str:
    """Search the web for information using multiple search engines.
    
    This tool provides comprehensive web search using both Serper (Google) and Tavily APIs.
    It automatically tries Tavily first (faster, AI-optimized) and falls back to Serper if needed.
    
    Args:
        query: The search query string
        num_results: Number of results to return (default 5, max 10)
        search_type: Type of search - "general", "news", "academic", or "recent"
        
    Returns:
        Formatted search results with titles, URLs, and snippets
    """
    try:
        # Limit results to avoid overwhelming context
        num_results = min(num_results, 10)
        
        # Try Tavily first (optimized for AI agents)
        tavily_results = _search_with_tavily(query, num_results, search_type)
        if tavily_results:
            return tavily_results
            
        # Fallback to Serper (Google Search)
        serper_results = _search_with_serper(query, num_results, search_type)
        if serper_results:
            return serper_results
            
        return f"No search results found for '{query}'. Please check your internet connection or try a different query."
        
    except Exception as e:
        return f"Search error for '{query}': {str(e)}"


@tool  
def web_search_news(query: str, num_results: int = 5, time_range: str = "week") -> str:
    """Search for recent news articles about a topic.
    
    Args:
        query: News search query
        num_results: Number of results (default 5, max 10)
        time_range: "day", "week", "month", or "year"
        
    Returns:
        Formatted news search results
    """
    try:
        # Limit results to avoid overwhelming context
        num_results = min(num_results, 10)
        
        # Try Tavily first for news
        tavily_results = _search_with_tavily(query, num_results, "news")
        if tavily_results:
            return tavily_results
            
        # Fallback to Serper for news
        serper_results = _search_with_serper(query, num_results, "news")
        if serper_results:
            return serper_results
            
        return f"No news results found for '{query}'. Please try a different query."
        
    except Exception as e:
        return f"News search error for '{query}': {str(e)}"


@tool
def web_search_academic(query: str, num_results: int = 5) -> str:
    """Search for academic papers and scholarly articles.
    
    Args:
        query: Academic search query
        num_results: Number of results (default 5, max 10)
        
    Returns:
        Formatted academic search results
    """
    try:
        # Limit results to avoid overwhelming context
        num_results = min(num_results, 10)
        
        # Try Tavily first for academic content
        tavily_results = _search_with_tavily(query, num_results, "academic")
        if tavily_results:
            return tavily_results
            
        # Fallback to Serper for academic content
        serper_results = _search_with_serper(query, num_results, "academic")
        if serper_results:
            return serper_results
            
        return f"No academic results found for '{query}'. Please try a different query."
        
    except Exception as e:
        return f"Academic search error for '{query}': {str(e)}"


def _search_with_tavily(query: str, num_results: int, search_type: str) -> Optional[str]:
    """Search using Tavily API - optimized for AI agents."""
    try:
        # Configure Tavily based on search type
        tavily_config = {
            "max_results": num_results,
            "include_answer": True,
            "include_raw_content": False,
            "include_images": False,
        }
        
        if search_type == "news":
            tavily_config["topic"] = "news"
        elif search_type == "recent":
            tavily_config["search_depth"] = "advanced"
            tavily_config["time_range"] = "week"
        elif search_type == "academic":
            tavily_config["search_depth"] = "advanced"
            tavily_config["include_domains"] = ["scholar.google.com", "arxiv.org", "pubmed.ncbi.nlm.nih.gov"]
        else:
            tavily_config["topic"] = "general"
            
        search_tool = TavilySearch(**tavily_config)
        
        # Execute search
        results = search_tool.invoke({"query": query})
        
        if not results:
            return None
            
        # Parse and format results
        return _format_tavily_results(query, results, search_type)
        
    except Exception as e:
        print(f"Tavily search failed: {e}")
        return None


def _search_with_serper(query: str, num_results: int, search_type: str) -> Optional[str]:
    """Search using Google Serper API."""
    try:
        # Configure Serper based on search type  
        serper_config = {"k": num_results}
        
        if search_type == "news":
            serper_config["type"] = "news"
        elif search_type == "recent":
            serper_config["tbs"] = "qdr:w"  # Past week
        elif search_type == "academic":
            serper_config["type"] = "search"
            # Add academic-focused terms to query
            query = f"{query} site:scholar.google.com OR site:arxiv.org OR site:pubmed.ncbi.nlm.nih.gov"
        else:
            serper_config["type"] = "search"
            
        search_wrapper = GoogleSerperAPIWrapper(**serper_config)
        
        # Execute search
        if search_type == "news" or search_type in ["general", "recent", "academic"]:
            results = search_wrapper.results(query)
        else:
            results = search_wrapper.run(query)
            
        if not results:
            return None
            
        # Format results based on type
        return _format_serper_results(query, results, search_type)
        
    except Exception as e:
        print(f"Serper search failed: {e}")
        return None


def _format_tavily_results(query: str, results: str, search_type: str) -> str:
    """Format Tavily search results."""
    try:
        # Parse JSON response if it's a string
        if isinstance(results, str):
            data = json.loads(results)
        else:
            data = results
            
        formatted_results = [f"🔍 Web Search Results for '{query}' (via Tavily)\n"]
        formatted_results.append(f"Search Type: {search_type.title()}\n")
        
        # Add answer if available
        if data.get("answer"):
            formatted_results.append(f"📋 **Quick Answer**: {data['answer']}\n")
            
        # Add search results
        if data.get("results"):
            formatted_results.append("📄 **Detailed Results**:")
            for i, result in enumerate(data["results"][:10], 1):
                title = result.get("title", "No title")
                url = result.get("url", "No URL")
                content = result.get("content", "No content available")
                
                # Truncate content to avoid overwhelming context
                if len(content) > 200:
                    content = content[:200] + "..."
                    
                formatted_results.append(f"\n{i}. **{title}**")
                formatted_results.append(f"   🔗 {url}")
                formatted_results.append(f"   📝 {content}")
                
        return "\n".join(formatted_results)
        
    except Exception as e:
        return f"Error formatting Tavily results: {str(e)}"


def _format_serper_results(query: str, results: Any, search_type: str) -> str:
    """Format Google Serper search results."""
    try:
        formatted_results = [f"🔍 Web Search Results for '{query}' (via Google/Serper)\n"]
        formatted_results.append(f"Search Type: {search_type.title()}\n")
        
        if isinstance(results, str):
            # Simple string result
            return f"🔍 Web Search Results for '{query}':\n{results}"
            
        elif isinstance(results, dict):
            # Structured results
            if search_type == "news" and "news" in results:
                formatted_results.append("📰 **News Results**:")
                for i, item in enumerate(results["news"][:10], 1):
                    title = item.get("title", "No title")
                    link = item.get("link", "No URL")
                    snippet = item.get("snippet", "No description")
                    source = item.get("source", "Unknown source")
                    date = item.get("date", "")
                    
                    formatted_results.append(f"\n{i}. **{title}**")
                    formatted_results.append(f"   📅 {date} | 📺 {source}")
                    formatted_results.append(f"   🔗 {link}")
                    formatted_results.append(f"   📝 {snippet}")
                    
            elif "organic" in results:
                # Regular search results
                formatted_results.append("📄 **Search Results**:")
                for i, item in enumerate(results["organic"][:10], 1):
                    title = item.get("title", "No title")
                    link = item.get("link", "No URL")
                    snippet = item.get("snippet", "No description")
                    
                    formatted_results.append(f"\n{i}. **{title}**")
                    formatted_results.append(f"   🔗 {link}")
                    formatted_results.append(f"   📝 {snippet}")
                    
            # Add knowledge graph if available
            if "knowledgeGraph" in results:
                kg = results["knowledgeGraph"]
                formatted_results.append(f"\n🧠 **Knowledge Graph**: {kg.get('title', '')}")
                if kg.get("description"):
                    formatted_results.append(f"   📝 {kg['description']}")
                    
        return "\n".join(formatted_results)
        
    except Exception as e:
        return f"Error formatting Serper results: {str(e)}"


__all__ = [
    'web_search',
    'web_search_news', 
    'web_search_academic'
]
