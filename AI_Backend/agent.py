# agent.py

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from tools import WebSearchTool
import os


class AgentFactory:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv("GEMINI_API_KEY"),
            temperature=0.3
        )

    def create_agent(self, system_prompt: str):

        grounded_prompt = f"""
        {system_prompt}

        GLOBAL RULES:

        TOOL USAGE RULES:
        - Use WebSearchTool when:
            * The query involves current events
            * Regulations, laws, or compliance standards
            * Financial or cybersecurity threats
            * Time-sensitive information
        - Do NOT answer from memory when real-time accuracy is required.

        CITATION RULES:
        - If web search is used, you MUST cite the URLs provided.
        - Never fabricate sources.
        - Format citations as:
        [Source: <URL>
        ]

        SAFETY RULES:
        - If unsure, say: "Insufficient verified information."
        - Never invent statistics, standards, or regulations.
        - Never answer outside your defined domain.
        - If query is outside scope, respond:
        "This query is outside the current domain scope."

        FINAL RESPONSE RULES:
        - Summarize tool results concisely.
        - Do NOT include raw scraped text.
        - Limit answer to 600 words maximum.
        - Provide a clean "Sources" section at the end.
        """

        agent = create_agent(
        model=self.llm,
        tools=[WebSearchTool],
        system_prompt=grounded_prompt
    )

        return agent