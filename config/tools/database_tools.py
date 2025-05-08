from typing import List, Dict, Any, Optional
from langchain_core.tools import BaseTool
from langchain.tools import Tool
from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SupabaseClient:
    _instance: Optional[Client] = None
    
    @classmethod
    def get_instance(cls) -> Client:
        if cls._instance is None:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
            if not url or not key:
                raise ValueError("Supabase credentials not found in environment variables")
            cls._instance = create_client(url, key)
        return cls._instance

def get_database_tools() -> List[BaseTool]:
    """Get database-related tools."""
    supabase = SupabaseClient.get_instance()
    
    return [
        Tool(
            name="query_database",
            description="Query the Supabase database with SQL",
            func=lambda query: supabase.table("your_table").select("*").execute().data
        ),
        Tool(
            name="insert_record",
            description="Insert a record into the Supabase database",
            func=lambda data: supabase.table("your_table").insert(data).execute().data
        ),
        Tool(
            name="update_record",
            description="Update a record in the Supabase database",
            func=lambda data: supabase.table("your_table").update(data).execute().data
        ),
        Tool(
            name="delete_record",
            description="Delete a record from the Supabase database",
            func=lambda id: supabase.table("your_table").delete().eq("id", id).execute().data
        )
    ] 