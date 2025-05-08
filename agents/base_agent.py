from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool
import json
from datetime import datetime

class BaseAgent:
    def __init__(
        self,
        name: str,
        tools: List[BaseTool] = None,
        memory: Any = None,
        human_in_loop: bool = False
    ):
        self.name = name
        self.tools = tools or []
        self.memory = memory
        self.human_in_loop = human_in_loop
        self.state_history = []
        
    def create_prompt(self, system_message: str) -> ChatPromptTemplate:
        """Create a prompt template with system message and available tools."""
        messages = [
            ("system", system_message)
        ]
        
        if self.tools:
            tool_descriptions = "\n".join([
                f"- {tool.name}: {tool.description}"
                for tool in self.tools
            ])
            messages[0] = (
                "system",
                f"{system_message}\n\nAvailable tools:\n{tool_descriptions}"
            )
        
        return ChatPromptTemplate.from_messages(messages)
    
    def save_state(self, state: Dict[str, Any]) -> None:
        """Save the current state to history."""
        state_with_metadata = {
            **state,
            "timestamp": datetime.now().isoformat(),
            "agent_name": self.name
        }
        self.state_history.append(state_with_metadata)
        
    def load_state(self) -> Dict[str, Any]:
        """Load the most recent state."""
        if not self.state_history:
            return {}
        return self.state_history[-1]
    
    def run(self, prompt: ChatPromptTemplate, input_text: str) -> str:
        """Run the agent with the given prompt and input."""
        if self.human_in_loop:
            return input("Enter your feedback: ")
            
        # Save state
        current_state = {
            "input": input_text,
            "prompt": str(prompt)
        }
        self.save_state(current_state)
        
        # Update memory if available
        if self.memory:
            self.memory.save_context(
                {"input": input_text},
                {"output": f"Agent {self.name} processed: {input_text}"}
            )
        
        return f"Agent {self.name} processed: {input_text}"
    
    def export_state_history(self, filepath: str) -> None:
        """Export state history to a JSON file."""
        with open(filepath, 'w') as f:
            json.dump(self.state_history, f, indent=2)
            
    def import_state_history(self, filepath: str) -> None:
        """Import state history from a JSON file."""
        with open(filepath, 'r') as f:
            self.state_history = json.load(f) 