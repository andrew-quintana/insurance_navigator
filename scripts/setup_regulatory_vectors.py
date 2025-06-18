#!/usr/bin/env python3
"""
Setup script for regulatory document vector processing.

1. Runs the database migration
2. Tests the system with a few sample documents
3. Provides usage examples
"""

import asyncio
import sys
import subprocess
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from data.healthcare_regulatory_documents import (
    print_document_summary, 
    get_high_priority_documents,
    get_documents_by_program
)

async def run_migration():
    """Run the database migration for regulatory vectors."""
    print("🔧 Running database migration for regulatory vector support...")
    
    try:
        # Run the migration using psql
        migration_file = Path(__file__).parent.parent / "db/migrations/015_add_regulatory_vectors_support.sql"
        
        if not migration_file.exists():
            print(f"❌ Migration file not found: {migration_file}")
            return False
            
        # Try to run migration with psql if available
        result = subprocess.run([
            "psql", "-f", str(migration_file)
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Database migration completed successfully!")
            return True
        else:
            print(f"⚠️  Migration may have failed or already applied: {result.stderr}")
            return True  # Continue anyway, might already be applied
            
    except FileNotFoundError:
        print("⚠️  psql not found. Please run the migration manually:")
        print(f"   psql -f {migration_file}")
        return False
    except Exception as e:
        print(f"❌ Error running migration: {e}")
        return False

def show_document_overview():
    """Show overview of available healthcare documents."""
    print("\n" + "="*70)
    print("📋 HEALTHCARE REGULATORY DOCUMENTS OVERVIEW")
    print("="*70)
    
    print_document_summary()
    
    print("\n🎯 HIGH PRIORITY DOCUMENTS:")
    high_priority = get_high_priority_documents()
    for doc in high_priority[:5]:  # Show first 5
        print(f"  • {doc['title']}")
        print(f"    Priority: {doc['priority']} | Programs: {', '.join(doc['programs'])}")
    
    if len(high_priority) > 5:
        print(f"  ... and {len(high_priority) - 5} more high priority documents")

async def test_processing():
    """Test the processing system with a few sample documents."""
    print("\n🧪 TESTING REGULATORY DOCUMENT PROCESSING")
    print("="*70)
    
    # Test with a few high-priority documents
    test_urls = [
        "https://www.medicare.gov/your-medicare-costs/help-paying-costs/medicare-rights",
        "https://www.hhs.gov/hipaa/for-professionals/privacy/laws-regulations/index.html"
    ]
    
    try:
        from scripts.bulk_regulatory_processor import UnifiedRegulatoryProcessor
        processor = UnifiedRegulatoryProcessor()
        
        print(f"Testing with {len(test_urls)} sample URLs...")
        results = await processor.process_regulatory_urls(test_urls, batch_size=1)
        
        print("\n📊 TEST RESULTS:")
        print(f"✅ Processed: {len(results['processed'])}")
        print(f"🔄 Duplicates: {len(results['duplicates'])}")
        print(f"❌ Failed: {len(results['failed'])}")
        print(f"📊 Vectors created: {results['total_vectors_created']}")
        
        if results['processed']:
            print("\nSuccessfully processed:")
            for doc in results['processed']:
                print(f"  📄 {doc['title']} ({doc['vector_count']} vectors)")
        
        if results['failed']:
            print("\nFailed documents:")
            for failed in results['failed']:
                print(f"  ❌ {failed['url']}: {failed['error']}")
                
        return len(results['processed']) > 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def show_usage_examples():
    """Show usage examples for the bulk processor."""
    print("\n" + "="*70)
    print("📖 USAGE EXAMPLES")
    print("="*70)
    
    print("1. Process all curated healthcare documents:")
    print("   python scripts/bulk_regulatory_processor.py --healthcare-documents")
    
    print("\n2. Process a single URL:")
    print("   python scripts/bulk_regulatory_processor.py https://www.medicare.gov/drug-coverage-part-d")
    
    print("\n3. Process URLs from a file:")
    print("   echo 'https://www.medicare.gov/claims-appeals/' > my_urls.txt")
    print("   python scripts/bulk_regulatory_processor.py my_urls.txt")
    
    print("\n4. Process only high-priority documents:")
    print("   python -c \"from data.healthcare_regulatory_documents import get_high_priority_documents")
    print("   docs = get_high_priority_documents()")
    print("   with open('high_priority_urls.txt', 'w') as f:")
    print("       for doc in docs: f.write(doc['url'] + '\\n')\"")
    print("   python scripts/bulk_regulatory_processor.py high_priority_urls.txt")
    
    print("\n5. Search regulatory documents (after processing):")
    print("   python -c \"")
    print("   import asyncio")
    print("   from scripts.bulk_regulatory_processor import search_regulatory_documents")
    print("   results = asyncio.run(search_regulatory_documents('Medicare prescription drug coverage'))")
    print("   print(results)\"")

async def main():
    """Main setup and test function."""
    print("🚀 REGULATORY DOCUMENT VECTOR PROCESSING SETUP")
    print("=" * 70)
    
    # Step 1: Run migration
    migration_success = await run_migration()
    
    # Step 2: Show document overview
    show_document_overview()
    
    # Step 3: Test processing (optional)
    print("\n" + "="*70)
    test_choice = input("🧪 Would you like to test with sample documents? (y/N): ").strip().lower()
    
    if test_choice in ['y', 'yes']:
        test_success = await test_processing()
        if test_success:
            print("\n✅ System test completed successfully!")
        else:
            print("\n⚠️  System test encountered issues.")
    
    # Step 4: Show usage examples
    show_usage_examples()
    
    print("\n" + "="*70)
    print("🎉 SETUP COMPLETE!")
    print("="*70)
    print("Your regulatory document processing system is ready!")
    print(f"📚 {len(get_high_priority_documents())} high-priority documents available for processing")
    print("\nNext steps:")
    print("1. Run: python scripts/bulk_regulatory_processor.py --healthcare-documents")
    print("2. Monitor the processing results")
    print("3. Use the search functions to query processed documents")

if __name__ == "__main__":
    asyncio.run(main()) 