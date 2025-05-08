from typing import List, Dict, Any
from langchain_core.tools import BaseTool
from langchain.tools import Tool
from config.tools.database_tools import SupabaseClient

def get_insurance_tools() -> List[BaseTool]:
    """Get insurance-specific tools."""
    supabase = SupabaseClient.get_instance()
    
    return [
        Tool(
            name="coverage_checker",
            description="Check insurance coverage for specific services",
            func=lambda service: supabase.table("coverage").select("*").eq("service", service).execute().data
        ),
        Tool(
            name="premium_calculator",
            description="Calculate insurance premiums based on coverage and risk factors",
            func=lambda factors: supabase.table("premiums").select("*").eq("risk_factors", factors).execute().data
        ),
        Tool(
            name="policy_lookup",
            description="Look up policy details by policy number",
            func=lambda policy_number: supabase.table("policies").select("*").eq("policy_number", policy_number).execute().data
        ),
        Tool(
            name="claim_status",
            description="Check the status of an insurance claim",
            func=lambda claim_id: supabase.table("claims").select("*").eq("claim_id", claim_id).execute().data
        )
    ] 