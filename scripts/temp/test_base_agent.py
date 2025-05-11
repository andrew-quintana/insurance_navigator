import pytest
from unittest.mock import Mock, patch
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.tools import BaseTool
from agents.base_agent import BaseAgent

class MockTool(BaseTool):
    name = "mock_tool"
    description = "A mock tool for testing"
    
    def _run(self, query: str) -> str:
        return f"Mock tool response to: {query}"

@pytest.fixture
def base_agent():
    return BaseAgent(name="test_agent")

@pytest.fixture
def agent_with_tools():
    tools = [MockTool()]
    return BaseAgent(name="test_agent", tools=tools)

@pytest.fixture
def agent_with_memory():
    return BaseAgent(
        name="test_agent",
        memory=Mock(return_messages=True)
    )

@pytest.fixture
def agent_with_human_in_loop():
    return BaseAgent(
        name="test_agent",
        human_in_loop=True
    )

def test_agent_initialization(base_agent):
    assert base_agent.name == "test_agent"
    assert base_agent.tools == []
    assert base_agent.human_in_loop is False
    assert base_agent.state_history == []

def test_agent_with_tools(agent_with_tools):
    assert len(agent_with_tools.tools) == 1
    assert isinstance(agent_with_tools.tools[0], MockTool)

def test_create_prompt(base_agent):
    system_message = "Test system message"
    prompt = base_agent.create_prompt(system_message)
    assert prompt.messages[0][1] == system_message

def test_create_prompt_with_tools(agent_with_tools):
    system_message = "Test system message"
    prompt = agent_with_tools.create_prompt(system_message)
    assert "Available tools:" in prompt.messages[0][1]
    assert "mock_tool" in prompt.messages[0][1]

def test_save_and_load_state(base_agent):
    test_state = {"input": "test", "messages": []}
    base_agent.save_state(test_state)
    
    loaded_state = base_agent.load_state()
    assert loaded_state["input"] == test_state["input"]
    assert "timestamp" in loaded_state
    assert "agent_name" in loaded_state

def test_export_import_state_history(base_agent, tmp_path):
    test_state = {"input": "test", "messages": []}
    base_agent.save_state(test_state)
    
    export_path = tmp_path / "state_history.json"
    base_agent.export_state_history(str(export_path))
    
    new_agent = BaseAgent(name="new_agent")
    new_agent.import_state_history(str(export_path))
    
    assert len(new_agent.state_history) == 1
    assert new_agent.state_history[0]["input"] == test_state["input"]

@patch('builtins.input', return_value="")
def test_run_without_human_in_loop(mock_input, base_agent):
    prompt = base_agent.create_prompt("Test system message")
    response = base_agent.run(prompt, "test input")
    assert isinstance(response, str)

@patch('builtins.input', return_value="human feedback")
def test_run_with_human_in_loop(mock_input, agent_with_human_in_loop):
    prompt = agent_with_human_in_loop.create_prompt("Test system message")
    response = agent_with_human_in_loop.run(prompt, "test input")
    assert response == "human feedback"

def test_memory_integration(agent_with_memory):
    prompt = agent_with_memory.create_prompt("Test system message")
    agent_with_memory.run(prompt, "test input")
    
    # Verify memory was updated
    agent_with_memory.memory.save_context.assert_called_once() 