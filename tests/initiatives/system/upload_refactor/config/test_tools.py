import pytest
from config.tools import ToolConfig
from langchain_core.tools import BaseTool

def test_get_search_tools():
    tools = ToolConfig.get_search_tools()
    assert len(tools) == 2
    assert all(isinstance(tool, BaseTool) for tool in tools)
    assert any(tool.name == "web_search" for tool in tools)
    assert any(tool.name == "wikipedia_search" for tool in tools)

def test_get_document_tools():
    tools = ToolConfig.get_document_tools()
    assert len(tools) == 2
    assert all(isinstance(tool, BaseTool) for tool in tools)
    assert any(tool.name == "document_parser" for tool in tools)
    assert any(tool.name == "policy_analyzer" for tool in tools)

def test_get_all_tools():
    all_tools = ToolConfig.get_all_tools()
    assert set(all_tools.keys()) == {"search", "document"}
    assert all(isinstance(tools, list) for tools in all_tools.values())
    assert all(all(isinstance(tool, BaseTool) for tool in tools) 
              for tools in all_tools.values())

def test_get_tools_by_category():
    # Test single category
    search_tools = ToolConfig.get_tools_by_category(["search"])
    assert len(search_tools) == 2
    assert all(tool.name in ["web_search", "wikipedia_search"] for tool in search_tools)
    
    # Test multiple categories
    tools = ToolConfig.get_tools_by_category(["search", "document"])
    assert len(tools) == 4
    assert any(tool.name == "web_search" for tool in tools)
    assert any(tool.name == "document_parser" for tool in tools)
    
    # Test invalid category
    tools = ToolConfig.get_tools_by_category(["invalid"])
    assert len(tools) == 0

def test_get_tool_by_name():
    # Test existing tool
    tool = ToolConfig.get_tool_by_name("web_search")
    assert tool is not None
    assert tool.name == "web_search"
    
    # Test non-existing tool
    tool = ToolConfig.get_tool_by_name("non_existing_tool")
    assert tool is None 