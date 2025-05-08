from typing import Dict, Any, List, Tuple, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import BaseTool
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class BaseAgent:
    def __init__(self, name: str, tools: Optional[List[BaseTool]] = None):
        self.name = name
        self.llm = ChatAnthropic(
            model="claude-3-sonnet-20240229",
            temperature=0
        )
        self.tools = tools or []
        
    def create_prompt(self, system_message: str) -> ChatPromptTemplate:
        """Create a chat prompt template with system message and tools."""
        messages = [
            ("system", system_message),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "{input}")
        ]
        
        # Add tool descriptions to system message if tools are provided
        if self.tools:
            tool_descriptions = "\n".join([f"- {tool.name}: {tool.description}" for tool in self.tools])
            messages[0] = ("system", f"{system_message}\n\nAvailable tools:\n{tool_descriptions}")
            
        return ChatPromptTemplate.from_messages(messages)
    
    def create_chain(self, prompt: ChatPromptTemplate) -> Any:
        """Create a chain with the prompt and tools if available."""
        chain = prompt | self.llm
        
        if self.tools:
            chain = chain.bind_tools(self.tools)
            
        return chain | StrOutputParser()
    
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
                elif role == "system":
                    message_history.append(SystemMessage(content=content))
        
        return chain.invoke({
            "messages": message_history,
            "input": input_text
        }) 