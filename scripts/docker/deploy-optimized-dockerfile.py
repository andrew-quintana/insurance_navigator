#!/usr/bin/env python3
"""
Deploy Optimized Dockerfile
Safely replaces current Dockerfile with optimized version
"""

import shutil
import os
from datetime import datetime
from pathlib import Path

def backup_current_dockerfile():
    """Backup current Dockerfile before replacement"""
    backup_dir = Path("docker-backups")
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = backup_dir / f"Dockerfile.backup.{timestamp}"
    
    if Path("Dockerfile").exists():
        shutil.copy2("Dockerfile", backup_file)
        print(f"📦 Backed up current Dockerfile to {backup_file}")
        return str(backup_file)
    else:
        print("⚠️  No current Dockerfile found to backup")
        return None

def deploy_optimized_dockerfile():
    """Deploy the optimized Dockerfile"""
    if not Path("Dockerfile.optimized-production").exists():
        print("❌ Dockerfile.optimized-production not found!")
        return False
    
    # Backup current
    backup_file = backup_current_dockerfile()
    
    # Replace current with optimized
    shutil.copy2("Dockerfile.optimized-production", "Dockerfile")
    print("✅ Deployed optimized Dockerfile")
    
    # Verify deployment
    if Path("Dockerfile").exists():
        print("✅ Verification: New Dockerfile is in place")
        return True
    else:
        print("❌ Verification failed: Dockerfile not found")
        return False

def create_rollback_script():
    """Create a rollback script in case we need to revert"""
    rollback_script = """#!/bin/bash
# Rollback script for Dockerfile optimization
# Generated automatically - use with caution

echo "🔄 Rolling back to previous Dockerfile..."

if [ -f "docker-backups/Dockerfile.backup.latest" ]; then
    cp docker-backups/Dockerfile.backup.latest Dockerfile
    echo "✅ Rollback complete"
else
    echo "❌ No backup found for rollback"
    exit 1
fi
"""
    
    with open("rollback-dockerfile.sh", "w") as f:
        f.write(rollback_script)
    
    os.chmod("rollback-dockerfile.sh", 0o755)
    print("📝 Created rollback script: rollback-dockerfile.sh")

def main():
    print("🚀 Deploying Optimized Dockerfile")
    print("=" * 40)
    
    # Check if we're in the right directory
    if not Path("main.py").exists():
        print("❌ Error: Not in project root directory")
        return
    
    # Deploy optimized Dockerfile
    if deploy_optimized_dockerfile():
        print("\n🎉 Deployment successful!")
        print("\nNext steps:")
        print("1. Test the new Dockerfile locally:")
        print("   docker build -t insurance-navigator:test .")
        print("2. If everything works, commit the changes:")
        print("   git add Dockerfile .dockerignore")
        print("   git commit -m 'Optimize Dockerfile for faster builds'")
        print("3. Deploy to Render")
        print("\nIf you need to rollback:")
        print("   ./rollback-dockerfile.sh")
        
        # Create rollback script
        create_rollback_script()
    else:
        print("❌ Deployment failed!")

if __name__ == "__main__":
    main()
