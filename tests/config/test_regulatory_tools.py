import pytest
from unittest.mock import Mock, patch
from config.tools.regulatory_tools import get_regulatory_tools, REGULATORY_BODIES
from langchain_core.tools import BaseTool

@pytest.fixture
def mock_search():
    with patch('config.tools.regulatory_tools.DuckDuckGoSearchRun') as mock:
        mock_instance = Mock()
        mock_instance.run.return_value = "Mock search result"
        mock.return_value = mock_instance
        yield mock_instance

def test_get_regulatory_tools(mock_search):
    tools = get_regulatory_tools()
    assert len(tools) == 4
    assert all(isinstance(tool, BaseTool) for tool in tools)
    
    # Check tool names
    tool_names = {tool.name for tool in tools}
    assert tool_names == {
        "search_regulations",
        "check_hipaa_compliance",
        "verify_claim_legitimacy",
        "get_regulatory_updates"
    }

def test_search_regulations(mock_search):
    tools = get_regulatory_tools()
    search_tool = next(tool for tool in tools if tool.name == "search_regulations")
    
    result = search_tool.func("test query")
    assert result == "Mock search result"
    
    # Verify search query includes regulatory sites
    mock_search.run.assert_called_once()
    call_args = mock_search.run.call_args[0][0]
    assert "site:hhs.gov" in call_args
    assert "site:cms.gov" in call_args
    assert "site:oig.hhs.gov" in call_args

def test_check_hipaa_compliance(mock_search):
    tools = get_regulatory_tools()
    compliance_tool = next(tool for tool in tools if tool.name == "check_hipaa_compliance")
    
    result = compliance_tool.func("data sharing")
    assert result == "Mock search result"
    
    # Verify HIPAA-specific context
    mock_search.run.assert_called_once()
    call_args = mock_search.run.call_args[0][0]
    assert "HIPAA compliance requirements" in call_args

def test_verify_claim_legitimacy(mock_search):
    tools = get_regulatory_tools()
    verification_tool = next(tool for tool in tools if tool.name == "verify_claim_legitimacy")
    
    result = verification_tool.func("high-value procedure")
    assert result == "Mock search result"
    
    # Verify fraud detection context
    mock_search.run.assert_called_once()
    call_args = mock_search.run.call_args[0][0]
    assert "fraud detection guidelines" in call_args

def test_get_regulatory_updates(mock_search):
    tools = get_regulatory_tools()
    updates_tool = next(tool for tool in tools if tool.name == "get_regulatory_updates")
    
    result = updates_tool.func()
    assert result == "Mock search result\n" * len(REGULATORY_BODIES)
    
    # Verify calls for each regulatory body
    assert mock_search.run.call_count == len(REGULATORY_BODIES)
    for body, info in REGULATORY_BODIES.items():
        calls = [call[0][0] for call in mock_search.run.call_args_list]
        assert any(f"recent updates {body}" in call for call in calls)
        assert any(f"site:{info['url']}" in call for call in calls) 