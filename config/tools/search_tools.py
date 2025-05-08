from typing import List
from langchain_core.tools import BaseTool
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_community.tools import WikipediaQueryRun
from langchain_community.utilities import WikipediaAPIWrapper

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