from typing import Dict, Any
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain.smith import RunEvalConfig
from langchain.callbacks.tracers import LangChainTracer
from langchain.callbacks.manager import CallbackManager
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class PromptEngine:
    def __init__(self):
        self.tracer = LangChainTracer(
            project_name=os.getenv("LANGCHAIN_PROJECT", "insurance_navigator")
        )
        self.callback_manager = CallbackManager([self.tracer])
        
    def create_chain(self, prompt_template: str) -> Any:
        """Create a basic LangChain chain with the given prompt template."""
        prompt = ChatPromptTemplate.from_template(prompt_template)
        
        chain = (
            {"input": RunnablePassthrough()}
            | prompt
            | StrOutputParser()
        )
        
        return chain
    
    def run_chain(self, chain: Any, input_data: Dict[str, Any]) -> str:
        """Run a chain with the given input data."""
        return chain.invoke(
            input_data,
            config={"callbacks": self.callback_manager}
        ) 