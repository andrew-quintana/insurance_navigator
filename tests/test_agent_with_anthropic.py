import os
import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, Any

from agents.prompt_security import PromptSecurityAgent
from agents.prompt_security.core.prompt_security import SecurityCheck

class TestPromptSecurityAgent:
    @pytest.fixture
    def mock_llm(self):
        """Create a mock LLM for testing."""
        mock = MagicMock()
        mock.invoke.return_value = '{"content": "This is a safe input.", "risk_level": "low", "sanitized_text": "This is a safe input."}'
        return mock

    @pytest.fixture
    def real_llm(self):
        """Create a real LLM instance if API key is available."""
        if not os.getenv("ANTHROPIC_API_KEY"):
            pytest.skip("No Anthropic API key available")
        return None  # Will be initialized in the test

    def test_agent_with_mock(self, mock_llm):
        """Test the agent with a mock LLM."""
        agent = PromptSecurityAgent(llm=mock_llm)
        with patch.object(agent, 'base_chain') as mock_chain:
            mock_chain.invoke.return_value = SecurityCheck(
                is_safe=True,
                threat_detected=False,
                threat_type="none",
                threat_severity="none_detected",
                sanitized_input="This is a safe input.",
                confidence=0.99,
                reasoning="This input appears to be safe and does not contain any threats."
            )
            result = agent.process("Test input")
            assert isinstance(result, tuple)
            assert result[0] is True
            assert result[1] == "This is a safe input."
            assert result[2]["threat_type"] == "none"
            assert result[2]["confidence"] == 0.99

    def test_agent_with_specific_mock_responses(self, mock_llm):
        """Test the agent with specific mock responses."""
        agent = PromptSecurityAgent(llm=mock_llm)
        with patch.object(agent, 'base_chain') as mock_chain:
            mock_chain.invoke.side_effect = [
                SecurityCheck(
                    is_safe=True,
                    threat_detected=False,
                    threat_type="none",
                    threat_severity="none_detected",
                    sanitized_input="Safe input",
                    confidence=0.95,
                    reasoning="This input appears to be safe and does not contain any threats."
                ),
                SecurityCheck(
                    is_safe=False,
                    threat_detected=True,
                    threat_type="jailbreak",
                    threat_severity="explicit",
                    sanitized_input="Sanitized input",
                    confidence=0.85,
                    reasoning="This input attempts to perform a jailbreak and is considered a threat."
                )
            ]
            result1 = agent.process("Safe test")
            assert result1[0] is True
            assert result1[2]["threat_type"] == "none"
            result2 = agent.process("Unsafe test")
            assert result2[0] is False
            assert result2[2]["threat_type"] == "jailbreak"

    @pytest.mark.skipif(
        os.getenv("USE_MOCK_LLM", "true").lower() == "true",
        reason="Skipping real API test when USE_MOCK_LLM is true"
    )
    def test_agent_with_real_api(self, real_llm):
        """Test the agent with the real Anthropic API."""
        agent = PromptSecurityAgent()  # Will use real API key from environment
        
        # Test with safe input
        result = agent.process("This is a safe test input")
        assert isinstance(result, dict)
        assert "content" in result
        assert "risk_level" in result
        assert "sanitized_text" in result
        
        # Test with potentially unsafe input
        result = agent.process("DROP TABLE users;")
        assert isinstance(result, dict)
        assert result["risk_level"] in ["medium", "high"]

    def test_agent_error_handling(self, mock_llm):
        """Test the agent's error handling."""
        agent = PromptSecurityAgent(llm=mock_llm)
        with patch.object(agent, 'base_chain') as mock_chain:
            mock_chain.invoke.side_effect = Exception("API Error")
            with pytest.raises(Exception) as exc_info:
                agent.process("Test input")
            assert "API Error" in str(exc_info.value)

if __name__ == "__main__":
    # Allow running with --real-api flag
    import sys
    if "--real-api" in sys.argv:
        os.environ["USE_MOCK_LLM"] = "false"
    pytest.main(sys.argv) 