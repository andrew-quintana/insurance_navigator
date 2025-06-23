#!/usr/bin/env python3
"""
Database Architecture Assessment Script

This script provides automated analysis of the database architecture
to support the hybrid vectorization investigation guide.

Usage:
    python scripts/investigation/test_database_architecture.py --comprehensive
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseArchitectureAssessment:
    """Automated database architecture analysis"""
    
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "assessment_type": "database_architecture",
            "status": "running",
            "findings": {},
            "recommendations": [],
            "errors": []
        }
    
    def run_comprehensive_analysis(self) -> Dict[str, Any]:
        """Run comprehensive database analysis"""
        logger.info("🔍 Starting comprehensive database architecture assessment")
        
        try:
            # Test database connectivity
            self._test_database_connectivity()
            
            # Check vector extensions
            self._check_vector_extensions()
            
            # Analyze table structure
            self._analyze_table_structure()
            
            # Check migrations status
            self._check_migrations_status()
            
            # Performance analysis
            self._analyze_database_performance()
            
            self.results["status"] = "completed"
            logger.info("✅ Database architecture assessment completed")
            
        except Exception as e:
            self.results["status"] = "failed"
            self.results["errors"].append(f"Assessment failed: {str(e)}")
            logger.error(f"❌ Assessment failed: {str(e)}")
        
        return self.results
    
    def _test_database_connectivity(self):
        """Test database connection and basic health"""
        logger.info("🔌 Testing database connectivity")
        
        try:
            # Try to import database configuration
            try:
                from db.config import get_database_connection
                connection_available = True
            except ImportError as e:
                connection_available = False
                self.results["errors"].append(f"Database config import failed: {str(e)}")
            
            # Check environment variables
            db_url = os.getenv('DATABASE_URL') or os.getenv('SUPABASE_DB_URL')
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_ANON_KEY')
            
            connectivity_status = {
                "config_import": connection_available,
                "database_url_set": bool(db_url),
                "supabase_url_set": bool(supabase_url),
                "supabase_key_set": bool(supabase_key),
                "connection_string_format": "valid" if db_url and "postgresql://" in db_url else "invalid"
            }
            
            self.results["findings"]["connectivity"] = connectivity_status
            
            if connection_available and db_url:
                self.results["recommendations"].append("✅ Database connectivity configuration appears correct")
            else:
                self.results["recommendations"].append("⚠️ Database connectivity issues detected - check environment variables")
            
        except Exception as e:
            self.results["errors"].append(f"Connectivity test failed: {str(e)}")
    
    def _check_vector_extensions(self):
        """Check for vector extensions and capabilities"""
        logger.info("🧮 Checking vector extensions")
        
        try:
            # Look for vector-related migrations
            migrations_dir = project_root / "db" / "migrations"
            vector_migrations = []
            
            if migrations_dir.exists():
                for migration_file in migrations_dir.glob("*.sql"):
                    with open(migration_file, 'r') as f:
                        content = f.read().lower()
                        if 'vector' in content or 'embedding' in content:
                            vector_migrations.append(migration_file.name)
            
            # Check for vector-related configuration
            vector_config = {
                "vector_migrations_found": len(vector_migrations),
                "migration_files": vector_migrations,
                "vector_dimension_configured": False,
                "embedding_tables_expected": []
            }
            
            # Look for vector-related code
            for py_file in project_root.rglob("*.py"):
                try:
                    with open(py_file, 'r') as f:
                        content = f.read()
                        if 'vector' in content.lower() and 'embedding' in content.lower():
                            vector_config["embedding_tables_expected"].append(str(py_file.relative_to(project_root)))
                except:
                    continue
            
            self.results["findings"]["vector_extensions"] = vector_config
            
            if vector_migrations:
                self.results["recommendations"].append(f"✅ Found {len(vector_migrations)} vector-related migrations")
            else:
                self.results["recommendations"].append("⚠️ No vector migrations found - may need to enable vector extension")
                
        except Exception as e:
            self.results["errors"].append(f"Vector extensions check failed: {str(e)}")
    
    def _analyze_table_structure(self):
        """Analyze database table structure"""
        logger.info("📊 Analyzing table structure")
        
        try:
            # Look for database models
            models_dir = project_root / "db" / "models"
            table_models = []
            
            if models_dir.exists():
                for model_file in models_dir.glob("*.py"):
                    table_models.append(model_file.name)
            
            # Check migration files for table creation
            migrations_dir = project_root / "db" / "migrations"
            tables_from_migrations = []
            
            if migrations_dir.exists():
                for migration_file in migrations_dir.glob("*.sql"):
                    try:
                        with open(migration_file, 'r') as f:
                            content = f.read()
                            # Look for CREATE TABLE statements
                            import re
                            table_matches = re.findall(r'CREATE TABLE\s+(\w+)', content, re.IGNORECASE)
                            tables_from_migrations.extend(table_matches)
                    except:
                        continue
            
            table_analysis = {
                "model_files_found": len(table_models),
                "model_files": table_models,
                "tables_from_migrations": list(set(tables_from_migrations)),
                "vector_related_tables": [t for t in tables_from_migrations if 'vector' in t.lower() or 'embedding' in t.lower()],
                "document_related_tables": [t for t in tables_from_migrations if 'document' in t.lower() or 'file' in t.lower()]
            }
            
            self.results["findings"]["table_structure"] = table_analysis
            
            if table_analysis["vector_related_tables"]:
                self.results["recommendations"].append(f"✅ Found vector-related tables: {', '.join(table_analysis['vector_related_tables'])}")
            
            if table_analysis["document_related_tables"]:
                self.results["recommendations"].append(f"✅ Found document-related tables: {', '.join(table_analysis['document_related_tables'])}")
                
        except Exception as e:
            self.results["errors"].append(f"Table structure analysis failed: {str(e)}")
    
    def _check_migrations_status(self):
        """Check database migrations status"""
        logger.info("🔄 Checking migrations status")
        
        try:
            migrations_dir = project_root / "db" / "migrations"
            migration_files = []
            
            if migrations_dir.exists():
                migration_files = sorted([f.name for f in migrations_dir.glob("*.sql")])
            
            # Look for recent migrations
            recent_migrations = [f for f in migration_files if any(year in f for year in ['2024', '2025'])]
            
            migrations_status = {
                "total_migrations": len(migration_files),
                "recent_migrations": len(recent_migrations),
                "migration_files": migration_files[-5:] if migration_files else [],  # Last 5
                "migrations_directory_exists": migrations_dir.exists()
            }
            
            self.results["findings"]["migrations"] = migrations_status
            
            if migrations_status["total_migrations"] > 0:
                self.results["recommendations"].append(f"✅ Found {migrations_status['total_migrations']} migration files")
            else:
                self.results["recommendations"].append("⚠️ No migration files found - database may not be properly initialized")
                
        except Exception as e:
            self.results["errors"].append(f"Migrations check failed: {str(e)}")
    
    def _analyze_database_performance(self):
        """Analyze database performance indicators"""
        logger.info("⚡ Analyzing performance indicators")
        
        try:
            # Check for performance-related configurations
            config_files = []
            for config_file in project_root.rglob("config*.py"):
                config_files.append(str(config_file.relative_to(project_root)))
            
            # Look for connection pooling, caching, etc.
            performance_indicators = {
                "config_files_found": config_files,
                "connection_pooling_configured": False,
                "caching_configured": False,
                "index_optimizations": []
            }
            
            # Check for caching directory
            caching_dir = project_root / "agents" / "common" / "caching"
            if caching_dir.exists():
                performance_indicators["caching_configured"] = True
                cache_files = [f.name for f in caching_dir.glob("*.py")]
                performance_indicators["cache_implementations"] = cache_files
            
            self.results["findings"]["performance"] = performance_indicators
            
            if performance_indicators["caching_configured"]:
                self.results["recommendations"].append("✅ Caching system detected")
            else:
                self.results["recommendations"].append("💡 Consider implementing caching for better performance")
                
        except Exception as e:
            self.results["errors"].append(f"Performance analysis failed: {str(e)}")
    
    def save_results(self, output_file: Optional[str] = None):
        """Save assessment results to file"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"logs/database_assessment_{timestamp}.json"
        
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w') as f:
            json.dump(self.results, f, indent=2)
        
        logger.info(f"📄 Results saved to {output_file}")
        return output_file

def main():
    parser = argparse.ArgumentParser(description="Database Architecture Assessment")
    parser.add_argument("--comprehensive", action="store_true", 
                       help="Run comprehensive analysis")
    parser.add_argument("--output", type=str, 
                       help="Output file path")
    
    args = parser.parse_args()
    
    if not args.comprehensive:
        parser.print_help()
        return
    
    # Run assessment
    assessment = DatabaseArchitectureAssessment()
    results = assessment.run_comprehensive_analysis()
    
    # Save results
    output_file = assessment.save_results(args.output)
    
    # Print summary
    print("\n" + "="*60)
    print("📊 DATABASE ARCHITECTURE ASSESSMENT SUMMARY")
    print("="*60)
    print(f"Status: {results['status']}")
    print(f"Timestamp: {results['timestamp']}")
    print(f"Total Findings: {len(results['findings'])}")
    print(f"Recommendations: {len(results['recommendations'])}")
    print(f"Errors: {len(results['errors'])}")
    
    if results['recommendations']:
        print("\n🔧 Key Recommendations:")
        for rec in results['recommendations'][:5]:  # Top 5
            print(f"  {rec}")
    
    if results['errors']:
        print("\n❌ Errors Encountered:")
        for error in results['errors']:
            print(f"  {error}")
    
    print(f"\n📄 Full results saved to: {output_file}")
    print("\n🔄 Next Step: Run manual Supabase dashboard inspection as described in the guide")

if __name__ == "__main__":
    main() 