from typing import Dict, Any, List, Tuple, Optional, Union
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import BaseTool
from langchain_core.memory import BaseMemory
from langchain.memory import ConversationBufferMemory
from langchain_core.runnables import RunnablePassthrough
import os
from dotenv import load_dotenv
import json
from datetime import datetime
from utils.logging import AgentLogger, PromptLogger

# Load environment variables
load_dotenv()

class BaseAgent:
    def __init__(
        self, 
        name: str, 
        tools: Optional[List[BaseTool]] = None,
        memory: Optional[BaseMemory] = None,
        human_in_loop: bool = False
    ):
        self.name = name
        self.llm = ChatAnthropic(
            model="claude-3-sonnet-20240229",
            temperature=0
        )
        self.tools = tools or []
        self.memory = memory or ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        self.human_in_loop = human_in_loop
        self.state_history: List[Dict[str, Any]] = []
        
        # Initialize loggers
        self.agent_logger = AgentLogger(name)
        self.prompt_logger = PromptLogger(name)
        
    def create_prompt(self, system_message: str) -> ChatPromptTemplate:
        """Create a chat prompt template with system message and tools."""
        messages = [
            ("system", system_message),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}")
        ]
        
        # Add tool descriptions to system message if tools are provided
        if self.tools:
            tool_descriptions = "\n".join([f"- {tool.name}: {tool.description}" for tool in self.tools])
            messages[0] = ("system", f"{system_message}\n\nAvailable tools:\n{tool_descriptions}")
            
        prompt = ChatPromptTemplate.from_messages(messages)
        
        # Log prompt creation
        self.prompt_logger.log_prompt(
            prompt_template=str(prompt),
            variables={"system_message": system_message, "tools": [t.name for t in self.tools]}
        )
        
        return prompt
    
    def create_chain(self, prompt: ChatPromptTemplate) -> Any:
        """Create a chain with the prompt, tools, and memory."""
        chain = (
            RunnablePassthrough.assign(
                chat_history=lambda x: self.memory.load_memory_variables({})["chat_history"]
            )
            | prompt
            | self.llm
        )
        
        if self.tools:
            chain = chain.bind_tools(self.tools)
            
        return chain | StrOutputParser()
    
    def save_state(self, state: Dict[str, Any]) -> None:
        """Save the current state with timestamp."""
        state_with_time = {
            **state,
            "timestamp": datetime.now().isoformat(),
            "agent_name": self.name
        }
        self.state_history.append(state_with_time)
        
    def load_state(self, timestamp: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Load a specific state by timestamp or return the latest."""
        if not self.state_history:
            return None
            
        if timestamp:
            for state in reversed(self.state_history):
                if state["timestamp"] == timestamp:
                    return state
            return None
            
        return self.state_history[-1]
    
    def run(self, prompt: ChatPromptTemplate, input_text: str, 
            messages: List[Tuple[str, str]] = None) -> str:
        """Run the agent with the given input and message history."""
        try:
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
            
            # Save current state
            current_state = {
                "input": input_text,
                "messages": [{"role": m.type, "content": m.content} for m in message_history]
            }
            self.save_state(current_state)
            
            # Get response
            response = chain.invoke({
                "input": input_text
            })
            
            # If human-in-the-loop is enabled, get human feedback
            if self.human_in_loop:
                print(f"\nAgent {self.name} response: {response}")
                feedback = input("Human feedback (press Enter to accept, or type feedback): ")
                if feedback.strip():
                    response = feedback
                    print(f"Using human feedback: {response}")
            
            # Save response to memory
            self.memory.save_context(
                {"input": input_text},
                {"output": response}
            )
            
            # Save final state
            final_state = {
                **current_state,
                "response": response
            }
            self.save_state(final_state)
            
            # Log successful interaction
            self.agent_logger.log_interaction(
                input_text=input_text,
                response=response,
                tools_used=[t.name for t in self.tools],
                state=final_state
            )
            
            return response
            
        except Exception as e:
            # Log error
            self.agent_logger.log_error(
                error=e,
                context={
                    "input": input_text,
                    "messages": messages,
                    "tools": [t.name for t in self.tools]
                }
            )
            raise
    
    def export_state_history(self, filepath: str) -> None:
        """Export the state history to a JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.state_history, f, indent=2)
            
    def import_state_history(self, filepath: str) -> None:
        """Import state history from a JSON file."""
        with open(filepath, 'r') as f:
            self.state_history = json.load(f) 