from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from tools import WebSearchTool
import os

class AgentFactory:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=os.getenv("GEMINI_API_KEY")
        )

    def create_agent(self, system_prompt: str):
        memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

        agent = initialize_agent(
            tools=[WebSearchTool],
            llm=self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            memory=memory,
            verbose=False,
            max_iterations=3,
            handle_parsing_errors=True
        )

        return agent