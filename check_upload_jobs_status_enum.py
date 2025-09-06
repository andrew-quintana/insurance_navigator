#!/usr/bin/env python3
"""
Script to check the possible status enumeration values for upload_jobs table
in the Supabase instance.
"""

import os
import sys
from supabase import create_client, Client
from typing import List, Dict, Any

def get_supabase_client() -> Client:
    """Initialize Supabase client using environment variables."""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_ANON_KEY")
    
    if not url or not key:
        print("Error: SUPABASE_URL and SUPABASE_ANON_KEY environment variables must be set")
        sys.exit(1)
    
    return create_client(url, key)

def get_status_constraint_info() -> Dict[str, Any]:
    """Query the database to get status constraint information."""
    supabase = get_supabase_client()
    
    # Query to get the check constraint definition for status column
    query = """
    SELECT 
        conname as constraint_name,
        pg_get_constraintdef(oid) as constraint_definition
    FROM pg_constraint 
    WHERE conrelid = 'upload_pipeline.upload_jobs'::regclass 
    AND conname LIKE '%status%';
    """
    
    try:
        result = supabase.rpc('exec_sql', {'sql': query}).execute()
        return result.data[0] if result.data else {}
    except Exception as e:
        print(f"Error querying constraint info: {e}")
        return {}

def get_current_status_values() -> List[str]:
    """Get all current status values from the upload_jobs table."""
    supabase = get_supabase_client()
    
    try:
        result = supabase.table('upload_jobs').select('status').execute()
        statuses = list(set([row['status'] for row in result.data if row['status']]))
        return sorted(statuses)
    except Exception as e:
        print(f"Error querying current status values: {e}")
        return []

def get_enum_values_from_constraint() -> List[str]:
    """Extract enum values from the constraint definition."""
    constraint_info = get_status_constraint_info()
    
    if not constraint_info:
        return []
    
    constraint_def = constraint_info.get('constraint_definition', '')
    
    # Look for the IN clause in the constraint definition
    if 'IN (' in constraint_def:
        # Extract the values between IN ( and )
        start = constraint_def.find('IN (') + 4
        end = constraint_def.find(')', start)
        values_str = constraint_def[start:end]
        
        # Parse the comma-separated values
        values = [v.strip().strip("'") for v in values_str.split(',')]
        return sorted(values)
    
    return []

def main():
    """Main function to display status enumeration information."""
    print("=== Upload Jobs Status Enumeration Analysis ===\n")
    
    # Get constraint definition
    print("1. Database Constraint Definition:")
    constraint_info = get_status_constraint_info()
    if constraint_info:
        print(f"   Constraint Name: {constraint_info.get('constraint_name', 'N/A')}")
        print(f"   Definition: {constraint_info.get('constraint_definition', 'N/A')}")
    else:
        print("   Could not retrieve constraint information")
    print()
    
    # Get allowed values from constraint
    print("2. Allowed Status Values (from constraint):")
    allowed_values = get_enum_values_from_constraint()
    if allowed_values:
        for i, value in enumerate(allowed_values, 1):
            print(f"   {i:2d}. {value}")
    else:
        print("   Could not extract values from constraint")
    print()
    
    # Get current values in use
    print("3. Current Status Values (in use):")
    current_values = get_current_status_values()
    if current_values:
        for i, value in enumerate(current_values, 1):
            print(f"   {i:2d}. {value}")
    else:
        print("   No data found or error occurred")
    print()
    
    # Summary
    print("4. Summary:")
    print(f"   Total allowed values: {len(allowed_values)}")
    print(f"   Values currently in use: {len(current_values)}")
    
    if allowed_values and current_values:
        unused_values = set(allowed_values) - set(current_values)
        if unused_values:
            print(f"   Unused allowed values: {sorted(unused_values)}")
        else:
            print("   All allowed values are currently in use")

if __name__ == "__main__":
    main()

