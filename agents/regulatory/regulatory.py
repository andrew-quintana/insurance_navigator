"""
Regulatory Agent for Insurance Navigator

This module provides the main RegulatoryAgent class that integrates with the
multi-agent system for regulatory compliance and strategy analysis.
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

# Import the isolated implementation
from .regulatory_isolated import IsolatedRegulatoryAgent

logger = logging.getLogger(__name__)


class RegulatoryAgent:
    """
    Main regulatory agent class for the Insurance Navigator system.
    
    This agent is responsible for:
    1. Regulatory document search and analysis
    2. Compliance checking for insurance strategies
    3. Policy guidance and recommendations
    4. Integration with the multi-agent workflow
    """
    
    def __init__(
        self,
        db_config: Optional[Dict[str, Any]] = None,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
        anthropic_api_key: Optional[str] = None,
        use_mock: bool = False
    ):
        """Initialize the regulatory agent."""
        self.use_mock = use_mock
        
        if use_mock:
            # Use mock implementation for testing
            self.agent = self._create_mock_agent()
        else:
            # Use real isolated agent
            self.agent = IsolatedRegulatoryAgent(
                db_config=db_config,
                supabase_url=supabase_url,
                supabase_key=supabase_key,
                anthropic_api_key=anthropic_api_key
            )
        
        logger.info(f"Regulatory agent initialized (mock={use_mock})")
    
    def _create_mock_agent(self):
        """Create a mock agent for testing purposes."""
        class MockRegulatoryAgent:
            def get_capabilities(self):
                return {
                    "agent_type": "mock_regulatory",
                    "version": "1.0.0",
                    "mock_mode": True,
                    "features": [
                        "Mock regulatory search",
                        "Mock compliance checking",
                        "Mock strategy analysis"
                    ]
                }
            
            async def search_regulatory_documents(self, query, jurisdiction=None, program=None, max_results=5):
                return {
                    "query": query,
                    "total_results": 3,
                    "results": [
                        {
                            "title": f"Mock Regulatory Document for {query}",
                            "url": "https://mock.cms.gov/document1",
                            "snippet": f"Mock regulatory guidance related to {query}",
                            "domain": "cms.gov",
                            "document_type": "guidance",
                            "priority_score": 0.9
                        }
                    ],
                    "processing_time_seconds": 0.1
                }
            
            async def analyze_strategy(self, strategy, context=None):
                return {
                    "strategy": strategy,
                    "analysis": f"Mock Regulatory Strategy Analysis\n\nStrategy: {strategy}\n\nThis is a mock analysis for testing purposes. In production, this would provide detailed regulatory compliance analysis.",
                    "compliance_status": "compliant",
                    "recommendations": ["Mock recommendation 1", "Mock recommendation 2"],
                    "sources_found": 3,
                    "documents_cached": 2,
                    "processing_time_seconds": 0.2
                }
            
            async def check_compliance(self, message, strategy_metadata):
                return {
                    "status": "compliant",
                    "regulations_count": 5,
                    "compliance_score": 0.85,
                    "recommendations": ["Mock compliance recommendation"]
                }
        
        return MockRegulatoryAgent()
    
    async def search_regulatory_documents(
        self,
        query: str,
        jurisdiction: str = None,
        program: str = None,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """Search for regulatory documents."""
        return await self.agent.search_regulatory_documents(
            query=query,
            jurisdiction=jurisdiction,
            program=program,
            max_results=max_results
        )
    
    async def analyze_strategy(
        self,
        strategy: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Analyze a strategy for regulatory compliance."""
        return await self.agent.analyze_strategy(strategy=strategy, context=context)
    
    async def check_compliance(
        self,
        message: str,
        strategy_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Check compliance for a given message and strategy."""
        # For mock agent, use the mock method
        if hasattr(self.agent, 'check_compliance'):
            return await self.agent.check_compliance(message, strategy_metadata)
        
        # For isolated agent, perform compliance analysis
        compliance_query = f"compliance requirements for {message}"
        search_results = await self.agent.search_regulatory_documents(
            query=compliance_query,
            max_results=3
        )
        
        # Simple compliance scoring based on search results
        compliance_score = min(0.9, len(search_results.get('results', [])) * 0.3)
        
        return {
            "status": "compliant" if compliance_score > 0.5 else "needs_review",
            "regulations_count": len(search_results.get('results', [])),
            "compliance_score": compliance_score,
            "recommendations": [
                "Review regulatory documents found",
                "Ensure compliance with identified regulations"
            ]
        }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities."""
        return self.agent.get_capabilities()


# Convenience function for creating regulatory agent
def create_regulatory_agent(use_mock: bool = False, **kwargs) -> RegulatoryAgent:
    """Create a regulatory agent instance."""
    return RegulatoryAgent(use_mock=use_mock, **kwargs) 