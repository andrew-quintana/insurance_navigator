from typing import Dict, Any, List, Optional
from langchain_core.tools import BaseTool, Tool
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ToolConfig:
    """Configuration for available tools in the system."""
    
    @staticmethod
    def get_search_tools() -> List[BaseTool]:
        """Get search-related tools."""
        search = DuckDuckGoSearchRun()
        wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
        
        return [
            Tool(
                name="web_search",
                description="Search the web for current information",
                func=search.run
            ),
            Tool(
                name="wikipedia_search",
                description="Search Wikipedia for detailed information",
                func=wikipedia.run
            )
        ]
    
    @staticmethod
    def get_document_tools() -> List[BaseTool]:
        """Get document processing tools."""
        return [
            Tool(
                name="document_parser",
                description="Parse and extract information from documents",
                func=lambda x: "Document parsing not implemented yet"
            ),
            Tool(
                name="policy_analyzer",
                description="Analyze insurance policy documents",
                func=lambda x: "Policy analysis not implemented yet"
            )
        ]
    
    @staticmethod
    def get_all_tools() -> Dict[str, List[BaseTool]]:
        """Get all available tools grouped by category."""
        return {
            "search": ToolConfig.get_search_tools(),
            "document": ToolConfig.get_document_tools()
        }
    
    @staticmethod
    def get_tools_by_category(categories: List[str]) -> List[BaseTool]:
        """Get tools for specified categories."""
        all_tools = ToolConfig.get_all_tools()
        tools = []
        for category in categories:
            if category in all_tools:
                tools.extend(all_tools[category])
        return tools
    
    @staticmethod
    def get_tool_by_name(name: str) -> BaseTool:
        """Get a specific tool by name."""
        all_tools = ToolConfig.get_all_tools()
        for category_tools in all_tools.values():
            for tool in category_tools:
                if tool.name == name:
                    return tool
        return None 