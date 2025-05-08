from typing import Dict, Any, List, Tuple
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class BaseAgent:
    def __init__(self, name: str):
        self.name = name
        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0
        )
        
    def create_prompt(self, system_message: str) -> ChatPromptTemplate:
        """Create a chat prompt template with system message."""
        return ChatPromptTemplate.from_messages([
            ("system", system_message),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "{input}")
        ])
    
    def create_chain(self, prompt: ChatPromptTemplate) -> Any:
        """Create a basic chain with the prompt."""
        return prompt | self.llm | StrOutputParser()
    
    def run(self, prompt: ChatPromptTemplate, input_text: str, 
            messages: List[Tuple[str, str]] = None) -> str:
        """Run the agent with the given input and message history."""
        chain = self.create_chain(prompt)
        
        # Convert message history to LangChain message format
        message_history = []
        if messages:
            for role, content in messages:
                if role == "human":
                    message_history.append(HumanMessage(content=content))
                elif role == "ai":
                    message_history.append(AIMessage(content=content))
        
        return chain.invoke({
            "messages": message_history,
            "input": input_text
        }) 