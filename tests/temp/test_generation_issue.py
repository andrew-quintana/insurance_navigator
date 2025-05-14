"""
Test script to isolate the issue with MagicMock and Generation validation.
"""

from unittest.mock import MagicMock
from langchain_core.outputs.generation import Generation
from langchain_core.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

# Define a simple output schema
class TestOutput(BaseModel):
    value: str = Field(description="A test value")

def test_generation_with_mock():
    """Test creating a Generation with a MagicMock."""
    try:
        # This will fail because MagicMock is not a valid string
        mock = MagicMock()
        generation = Generation(text=mock)
        print("SUCCESS: Created Generation with mock")
    except Exception as e:
        print(f"FAILURE: Could not create Generation with mock: {e}")

def test_parser_with_mock():
    """Test using a MagicMock with an output parser."""
    parser = PydanticOutputParser(pydantic_object=TestOutput)
    mock = MagicMock()
    
    try:
        # This will fail because the parser expects a string
        result = parser.parse(mock)
        print(f"SUCCESS: Parser accepted mock: {result}")
    except Exception as e:
        print(f"FAILURE: Parser rejected mock: {e}")
        print(f"Mock type: {type(mock)}")
        print(f"Mock repr: {repr(mock)}")

def test_mock_with_str():
    """Test using a MagicMock with a __str__ method."""
    mock = MagicMock()
    mock.__str__.return_value = "This is a mock string"
    
    try:
        # This still fails because Pydantic checks the type, not just str representation
        generation = Generation(text=mock)
        print("SUCCESS: Created Generation with mock.__str__")
    except Exception as e:
        print(f"FAILURE: Could not create Generation with mock.__str__: {e}")

def test_mock_content():
    """Test using a MagicMock with a content attribute."""
    mock = MagicMock()
    mock.content = "This is mock content"
    
    try:
        # Using the content attribute directly should work
        model = TestOutput(value=mock.content)
        print(f"SUCCESS: Created model with mock.content: {model}")
    except Exception as e:
        print(f"FAILURE: Could not create model with mock.content: {e}")

if __name__ == "__main__":
    test_generation_with_mock()
    test_parser_with_mock()
    test_mock_with_str()
    test_mock_content() 