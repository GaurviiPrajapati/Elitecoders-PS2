import os
import requests
import json
from langchain.tools import Tool

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

if not TAVILY_API_KEY:
    raise ValueError("Missing TAVILY_API_KEY")

def web_search(query: str) -> str:
    url = "https://api.tavily.com/search"
    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": "advanced",
        "include_answer": True
    }

    response = requests.post(url, json=payload)
    data = response.json()

    results = []

    for item in data.get("results", [])[:5]:
        results.append({
            "title": item["title"],
            "url": item["url"],
            "content": item["content"]
        })

    return json.dumps(results)


WebSearchTool = Tool(
    name="WebSearch",
    func=web_search,
    description="Use this tool when up-to-date or external authoritative information is required. Returns structured JSON with title, url, and content."
)