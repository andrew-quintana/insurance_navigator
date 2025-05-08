from typing import List, Dict, Any
from langchain_core.tools import BaseTool
from langchain.tools import Tool
from langchain_community.tools import DuckDuckGoSearchRun
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Common regulatory bodies and resources
REGULATORY_BODIES = {
    "HIPAA": {
        "name": "Health Insurance Portability and Accountability Act",
        "url": "https://www.hhs.gov/hipaa",
        "description": "Federal law protecting sensitive patient health information"
    },
    "CMS": {
        "name": "Centers for Medicare & Medicaid Services",
        "url": "https://www.cms.gov",
        "description": "Federal agency administering healthcare insurance programs"
    },
    "HHS": {
        "name": "Department of Health and Human Services",
        "url": "https://www.hhs.gov",
        "description": "Federal department overseeing healthcare regulations"
    },
    "OIG": {
        "name": "Office of Inspector General",
        "url": "https://oig.hhs.gov",
        "description": "Investigates healthcare fraud and abuse"
    }
}

def get_regulatory_tools() -> List[BaseTool]:
    """Get regulatory and compliance-related tools."""
    search = DuckDuckGoSearchRun()
    
    def search_regulations(query: str) -> str:
        """Search for healthcare regulations and compliance information."""
        # Add regulatory context to the search
        enhanced_query = f"healthcare insurance regulations {query} site:hhs.gov OR site:cms.gov OR site:oig.hhs.gov"
        return search.run(enhanced_query)
    
    def check_hipaa_compliance(description: str) -> str:
        """Check if a process or action complies with HIPAA regulations."""
        # Add HIPAA-specific context
        query = f"HIPAA compliance requirements for {description}"
        return search.run(query)
    
    def verify_claim_legitimacy(claim_details: str) -> str:
        """Verify if a claim appears legitimate based on regulatory guidelines."""
        # Add fraud detection context
        query = f"healthcare insurance fraud detection guidelines for {claim_details}"
        return search.run(query)
    
    def get_regulatory_updates() -> str:
        """Get recent updates from healthcare regulatory bodies."""
        updates = []
        for body, info in REGULATORY_BODIES.items():
            query = f"recent updates {body} healthcare regulations site:{info['url']}"
            result = search.run(query)
            updates.append(f"{body} Updates:\n{result}\n")
        return "\n".join(updates)
    
    return [
        Tool(
            name="search_regulations",
            description="Search for healthcare regulations and compliance information",
            func=search_regulations
        ),
        Tool(
            name="check_hipaa_compliance",
            description="Check if a process or action complies with HIPAA regulations",
            func=check_hipaa_compliance
        ),
        Tool(
            name="verify_claim_legitimacy",
            description="Verify if a claim appears legitimate based on regulatory guidelines",
            func=verify_claim_legitimacy
        ),
        Tool(
            name="get_regulatory_updates",
            description="Get recent updates from healthcare regulatory bodies",
            func=get_regulatory_updates
        )
    ] 