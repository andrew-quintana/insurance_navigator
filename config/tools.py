from typing import Dict, Any, List, Optional
from langchain_core.tools import BaseTool
from langchain.tools import Tool
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
        return [
            DuckDuckGoSearchRun(
                name="web_search",
                description="Search the web for current information"
            ),
            WikipediaQueryRun(
                api_wrapper=WikipediaAPIWrapper(),
                name="wikipedia_search",
                description="Search Wikipedia for factual information"
            )
        ]
    
    @staticmethod
    def get_insurance_tools() -> List[BaseTool]:
        """Get insurance-specific tools."""
        # These would be custom tools for insurance-related tasks
        return [
            Tool(
                name="coverage_checker",
                description="Check insurance coverage for specific services",
                func=lambda x: "Coverage check not implemented yet"
            ),
            Tool(
                name="premium_calculator",
                description="Calculate insurance premiums based on coverage and risk factors",
                func=lambda x: "Premium calculation not implemented yet"
            )
        ]
    
    @staticmethod
    def get_document_tools() -> List[BaseTool]:
        """Get document processing tools."""
        # These would be tools for processing insurance documents
        return [
            Tool(
                name="document_parser",
                description="Parse insurance documents for key information",
                func=lambda x: "Document parsing not implemented yet"
            ),
            Tool(
                name="policy_analyzer",
                description="Analyze insurance policy documents",
                func=lambda x: "Policy analysis not implemented yet"
            )
        ]
    
    @classmethod
    def get_all_tools(cls) -> Dict[str, List[BaseTool]]:
        """Get all available tools grouped by category."""
        return {
            "search": cls.get_search_tools(),
            "insurance": cls.get_insurance_tools(),
            "document": cls.get_document_tools()
        }
    
    @classmethod
    def get_tools_by_category(cls, categories: List[str]) -> List[BaseTool]:
        """Get tools for specific categories."""
        all_tools = cls.get_all_tools()
        tools = []
        for category in categories:
            if category in all_tools:
                tools.extend(all_tools[category])
        return tools
    
    @classmethod
    def get_tool_by_name(cls, name: str) -> Optional[BaseTool]:
        """Get a specific tool by name."""
        all_tools = cls.get_all_tools()
        for category_tools in all_tools.values():
            for tool in category_tools:
                if tool.name == name:
                    return tool
        return None 