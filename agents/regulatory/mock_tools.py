#!/usr/bin/env python3
"""
Mock tools for simulating regulatory agent functionality.
Used for testing and development without dependency conflicts.
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse


class MockRegulatoryAgent:
    """
    Mock regulatory agent for testing and simulation.
    Provides realistic responses without external dependencies.
    """
    
    def __init__(self):
        """Initialize the mock agent."""
        self.trusted_domains = {
            'cms.gov', 'medicare.gov', 'medicaid.gov', 'ssa.gov',
            'dhcs.ca.gov', 'health.ny.gov', 'mass.gov',
            'ecfr.gov', 'regulations.gov', 'federalregister.gov'
        }
        
        # Mock search results database
        self.mock_search_results = {
            'medicare coverage': [
                {
                    'title': 'Medicare Coverage Determination Process - CMS',
                    'url': 'https://www.cms.gov/medicare/coverage/determination-process',
                    'snippet': 'Medicare coverage determinations evaluate whether medical items and services are covered under Medicare.',
                    'domain': 'cms.gov',
                    'document_type': 'policy',
                    'priority_score': 0.95,
                    'content': 'Medicare coverage determinations are decisions about whether Medicare will cover specific medical items or services. The process involves medical review and evidence evaluation.'
                },
                {
                    'title': 'Medicare Part B Coverage Guidelines',
                    'url': 'https://www.medicare.gov/coverage/part-b-coverage',
                    'snippet': 'Part B covers medically necessary services and outpatient care.',
                    'domain': 'medicare.gov',
                    'document_type': 'guidance',
                    'priority_score': 0.85,
                    'content': 'Medicare Part B covers medically necessary services including doctor visits, preventive services, and outpatient care.'
                }
            ],
            'medicaid eligibility': [
                {
                    'title': 'Medicaid Eligibility Requirements - CMS',
                    'url': 'https://www.medicaid.gov/eligibility',
                    'snippet': 'Medicaid eligibility is based on income, family size, and state requirements.',
                    'domain': 'medicaid.gov',
                    'document_type': 'regulation',
                    'priority_score': 0.90,
                    'content': 'Medicaid eligibility varies by state but follows federal guidelines for income limits and family composition.'
                }
            ],
            'provider enrollment': [
                {
                    'title': 'Medicare Provider Enrollment Process',
                    'url': 'https://www.cms.gov/medicare/provider-enrollment',
                    'snippet': 'Healthcare providers must enroll in Medicare to receive payments.',
                    'domain': 'cms.gov',
                    'document_type': 'guidance',
                    'priority_score': 0.88,
                    'content': 'Medicare provider enrollment requires completion of enrollment applications and background screening.'
                }
            ]
        }
    
    def is_trusted_url(self, url: str) -> bool:
        """Check if URL is from a trusted domain."""
        try:
            domain = urlparse(url).netloc.lower().replace('www.', '')
            return any(domain == trusted or domain.endswith('.' + trusted) 
                      for trusted in self.trusted_domains)
        except Exception:
            return False
    
    def search_regulatory_documents(
        self,
        query: str,
        jurisdiction: str = None,
        program: str = None,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Mock search for regulatory documents.
        Returns realistic results based on query terms.
        """
        start_time = time.time()
        
        # Find relevant mock results
        query_lower = query.lower()
        results = []
        
        for search_term, mock_results in self.mock_search_results.items():
            if any(term in query_lower for term in search_term.split()):
                results.extend(mock_results)
        
        # Add context-specific filtering
        if jurisdiction == 'CA' and not any('ca.gov' in r['url'] for r in results):
            # Add California-specific result
            results.append({
                'title': f'California {query} Guidelines',
                'url': 'https://dhcs.ca.gov/test-guideline',
                'snippet': f'California-specific guidance on {query}',
                'domain': 'dhcs.ca.gov',
                'document_type': 'guidance',
                'priority_score': 0.80,
                'content': f'California state guidelines for {query} implementation.'
            })
        
        # Limit results
        results = results[:max_results]
        
        # Add search metadata
        for result in results:
            result.update({
                'jurisdiction': jurisdiction or 'federal',
                'programs': [program] if program else ['Medicare'],
                'search_query': query,
                'search_timestamp': datetime.now().isoformat()
            })
        
        processing_time = time.time() - start_time
        
        return {
            'query': query,
            'total_results': len(results),
            'results': results,
            'processing_time_seconds': processing_time,
            'search_timestamp': datetime.now().isoformat(),
            'mock_mode': True
        }
    
    def extract_document_content(self, url: str) -> Dict[str, Any]:
        """Mock content extraction from URLs."""
        # Find matching mock content
        for results_list in self.mock_search_results.values():
            for result in results_list:
                if result['url'] == url:
                    return {
                        'content_type': 'html',
                        'url': url,
                        'title': result['title'],
                        'content': result['content'],
                        'sections': [
                            {
                                'title': 'Overview',
                                'content': result['content'][:100] + '...'
                            }
                        ],
                        'extraction_method': 'mock',
                        'content_length': len(result['content'])
                    }
        
        # Generic mock content
        return {
            'content_type': 'html',
            'url': url,
            'title': f'Mock Document from {urlparse(url).netloc}',
            'content': f'This is mock content extracted from {url}. In a real implementation, this would contain the actual document content.',
            'extraction_method': 'mock',
            'content_length': 100
        }
    
    def cache_document(self, document: Dict[str, Any]) -> str:
        """Mock document caching."""
        doc_id = f"mock_doc_{int(time.time())}"
        print(f"📝 Mock: Cached document {document.get('title', 'Unknown')} with ID {doc_id}")
        return doc_id
    
    def analyze_strategy(
        self,
        strategy: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Mock strategy analysis.
        Provides realistic regulatory analysis without external dependencies.
        """
        start_time = time.time()
        
        # Extract key terms for search
        search_terms = self._extract_search_terms(strategy, context)
        
        # Mock search for relevant documents
        all_results = []
        for term in search_terms[:2]:
            results = self.search_regulatory_documents(
                query=term,
                jurisdiction=context.get('jurisdiction') if context else None,
                program=context.get('program') if context else None,
                max_results=3
            )
            all_results.extend(results.get('results', []))
        
        # Mock content extraction
        enriched_results = []
        for result in all_results[:3]:
            content = self.extract_document_content(result['url'])
            enriched_result = {**result, **content}
            enriched_results.append(enriched_result)
            
            # Mock caching
            self.cache_document(enriched_result)
        
        # Generate analysis
        analysis = self._generate_mock_analysis(strategy, context, enriched_results)
        
        processing_time = time.time() - start_time
        
        return {
            'strategy': strategy,
            'context': context or {},
            'analysis': analysis,
            'sources_found': len(enriched_results),
            'documents_cached': len(enriched_results),
            'processing_time_seconds': processing_time,
            'timestamp': datetime.now().isoformat(),
            'agent_version': 'mock_v1.0',
            'mock_mode': True,
            'sources': enriched_results
        }
    
    def _extract_search_terms(self, strategy: str, context: Optional[Dict[str, Any]]) -> List[str]:
        """Extract search terms from strategy."""
        terms = []
        
        regulatory_keywords = [
            'medicare', 'medicaid', 'coverage', 'policy', 'regulation',
            'eligibility', 'enrollment', 'benefits', 'provider'
        ]
        
        strategy_words = strategy.lower().split()
        key_terms = [word for word in strategy_words 
                    if word in regulatory_keywords or len(word) > 5]
        
        if context and context.get('program'):
            terms.append(f"{context['program']} {' '.join(key_terms[:3])}")
        
        terms.append(' '.join(key_terms[:4]))
        return terms
    
    def _generate_mock_analysis(
        self,
        strategy: str,
        context: Optional[Dict[str, Any]],
        sources: List[Dict[str, Any]]
    ) -> str:
        """Generate mock regulatory analysis."""
        
        parts = []
        
        # Header
        parts.append("# Mock Regulatory Strategy Analysis")
        parts.append(f"**Strategy:** {strategy}")
        parts.append("*Note: This is a mock analysis for testing purposes*")
        
        if context:
            parts.append(f"**Context:** {context}")
        
        # Sources
        parts.append(f"\n## 📋 Information Sources ({len(sources)} found)")
        for i, source in enumerate(sources, 1):
            parts.append(f"{i}. **{source.get('title', 'Untitled')}**")
            parts.append(f"   - URL: {source.get('url', 'Unknown')}")
            parts.append(f"   - Type: {source.get('document_type', 'document')}")
            parts.append(f"   - Priority: {source.get('priority_score', 0):.2f}")
        
        # Analysis
        parts.append(f"\n## ⚖️ Regulatory Assessment")
        
        strategy_lower = strategy.lower()
        
        if 'medicare' in strategy_lower:
            parts.append("✅ **Medicare regulations apply**")
            parts.append("- Must comply with CMS Medicare coverage determination processes")
            parts.append("- Required to follow Medicare provider enrollment requirements")
        
        if 'medicaid' in strategy_lower:
            parts.append("✅ **Medicaid regulations apply**")
            parts.append("- Subject to federal Medicaid requirements")
            parts.append("- State-specific Medicaid rules may vary")
        
        if 'coverage' in strategy_lower:
            parts.append("⚠️ **Coverage determination required**")
            parts.append("- Must establish medical necessity")
            parts.append("- Prior authorization may be required")
        
        # Mock insights from sources
        if sources:
            parts.append(f"\n## 📄 Document Insights")
            for source in sources[:2]:
                content = source.get('content', '')
                if content:
                    parts.append(f"- **{source.get('title', 'Document')}**: {content[:150]}...")
        
        # Recommendations
        parts.append(f"\n## 🎯 Recommendations")
        parts.append("1. Review all cited regulatory sources thoroughly")
        parts.append("2. Verify current policy status on official government sites")
        parts.append("3. Consider jurisdiction-specific requirements")
        parts.append("4. Consult with regulatory compliance experts")
        
        parts.append(f"\n**Mock Analysis completed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        parts.append(f"**Sources analyzed:** {len(sources)} documents")
        
        return '\n'.join(parts)
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get mock agent capabilities."""
        return {
            'agent_type': 'mock_regulatory',
            'version': 'mock_v1.0',
            'features': [
                'Mock regulatory document search',
                'Mock content extraction',
                'Mock strategy analysis',
                'Mock document caching',
                'Trusted domain filtering'
            ],
            'mock_mode': True,
            'dependencies': [],  # No external dependencies
            'supported_domains': list(self.trusted_domains)
        }


# Convenience functions
def create_mock_agent() -> MockRegulatoryAgent:
    """Create a mock regulatory agent."""
    return MockRegulatoryAgent()


def analyze_strategy_mock(strategy: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Quick strategy analysis using mock agent."""
    agent = create_mock_agent()
    return agent.analyze_strategy(strategy, context)


# Demo function
def demo_mock_agent():
    """Run a demonstration of the mock agent."""
    print("🎭 Mock Regulatory Agent Demo")
    print("=" * 50)
    
    agent = create_mock_agent()
    
    # Show capabilities
    print("📋 Mock Agent Capabilities:")
    capabilities = agent.get_capabilities()
    for feature in capabilities['features']:
        print(f"  ✅ {feature}")
    
    # Test search
    print(f"\n🔍 Mock Search Test:")
    results = agent.search_regulatory_documents(
        query="Medicare Part B coverage",
        jurisdiction="federal",
        program="Medicare",
        max_results=2
    )
    
    print(f"  ✅ Found {results['total_results']} results")
    if results['results']:
        first_result = results['results'][0]
        print(f"  ✅ Top result: {first_result['title']}")
        print(f"  ✅ Domain: {first_result['domain']}")
    
    # Test strategy analysis
    print(f"\n🎯 Mock Strategy Analysis:")
    strategy = "Implement Medicare Part B coverage for new telehealth services"
    context = {"jurisdiction": "federal", "program": "Medicare"}
    
    analysis_result = agent.analyze_strategy(strategy, context)
    print(f"  ✅ Analysis completed in {analysis_result['processing_time_seconds']:.2f}s")
    print(f"  ✅ Sources found: {analysis_result['sources_found']}")
    print(f"  ✅ Documents cached: {analysis_result['documents_cached']}")
    
    # Show analysis preview
    analysis_text = analysis_result['analysis']
    preview = analysis_text.split('\n')[:10]  # First 10 lines
    print(f"\n📄 Analysis Preview:")
    for line in preview:
        if line.strip():
            print(f"  {line}")
    
    print(f"\n✨ Mock agent demonstrates full regulatory analysis workflow!")


if __name__ == "__main__":
    demo_mock_agent() 