# tools.py

from langchain_core.tools import tool
from tavily import TavilyClient
import os
import json

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not TAVILY_API_KEY:
    raise ValueError("Missing TAVILY_API_KEY")

tavily = TavilyClient(api_key=TAVILY_API_KEY)


@tool
def WebSearchTool(query: str) -> str:
    """
    Use this tool when up-to-date or external authoritative
    information is required. Returns structured JSON with
    title, url, and content.
    """

    results = tavily.search(
        query=query,
        search_depth="advanced",
        max_results=5
    )

    formatted = []

    for item in results.get("results", []):
        formatted.append({
            "title": item["title"],
            "url": item["url"],
            "content": item["content"]
        })

    return json.dumps({
        "instructions": "Use these sources. Cite URLs in your final answer.",
        "sources": formatted
    }, indent=2)