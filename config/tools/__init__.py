from typing import Dict, List, Optional
from langchain_core.tools import BaseTool
from .search_tools import get_search_tools
from .database_tools import get_database_tools
from .regulatory_tools import get_regulatory_tools

def get_all_tools() -> Dict[str, List[BaseTool]]:
    """Get all available tools grouped by category."""
    return {
        "search": get_search_tools(),
        "database": get_database_tools(),
        "regulatory": get_regulatory_tools()
    }

def get_tools_by_category(categories: List[str]) -> List[BaseTool]:
    """Get tools for specific categories."""
    all_tools = get_all_tools()
    tools = []
    for category in categories:
        if category in all_tools:
            tools.extend(all_tools[category])
    return tools

def get_tool_by_name(name: str) -> Optional[BaseTool]:
    """Get a specific tool by name."""
    all_tools = get_all_tools()
    for category_tools in all_tools.values():
        for tool in category_tools:
            if tool.name == name:
                return tool
    return None 