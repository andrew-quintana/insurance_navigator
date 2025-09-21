#!/usr/bin/env python3
"""
Git History Cleanup Script
This script removes all traces of sensitive data from git history using BFG Repo-Cleaner.
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(command, cwd=None):
    """Run a command and return the result."""
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    """Main cleanup function."""
    print("🔒 Starting Git History Cleanup Process")
    print("=" * 50)
    
    # Get project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Create credentials list file
    credentials_file = project_root / "credentials_to_remove.txt"
    with open(credentials_file, 'w') as f:
        f.write("""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
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
tukwof-pyVxo5-qejnoj
iSUAmk2NHMNW5bsn8F0UnPSCk9L+IxZhu/v/UyDwFcc=
llx-CRtlURo7FT74ZMydik58KjPHC5aTpOSuGjWqOkTXjrPQucUS
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
dfgzeastcxnoqshgyotp
eyJhbGciOiJIUzI1NiIs
""")
    
    print("✅ Created credentials list file")
    
    # Check if BFG is available
    bfg_jar = project_root / "bfg-1.14.0.jar"
    if not bfg_jar.exists():
        print("📥 Downloading BFG Repo-Cleaner...")
        success, stdout, stderr = run_command(
            "wget https://repo1.maven.org/maven2/com/madgag/bfg/1.14.0/bfg-1.14.0.jar"
        )
        if not success:
            print(f"❌ Failed to download BFG: {stderr}")
            return False
        print("✅ BFG downloaded successfully")
    
    # Create a backup of the current repository
    print("💾 Creating repository backup...")
    backup_dir = project_root.parent / f"{project_root.name}_backup"
    success, stdout, stderr = run_command(f"cp -r {project_root} {backup_dir}")
    if not success:
        print(f"❌ Failed to create backup: {stderr}")
        return False
    print("✅ Backup created successfully")
    
    # Clean the repository using BFG
    print("🧹 Cleaning repository with BFG...")
    success, stdout, stderr = run_command(
        f"java -jar {bfg_jar} --replace-text {credentials_file}",
        cwd=project_root
    )
    if not success:
        print(f"❌ BFG cleanup failed: {stderr}")
        return False
    print("✅ BFG cleanup completed")
    
    # Clean up git references
    print("🧹 Cleaning git references...")
    success, stdout, stderr = run_command("git reflog expire --expire=now --all")
    if not success:
        print(f"⚠️  Warning: Failed to clean reflog: {stderr}")
    
    success, stdout, stderr = run_command("git gc --prune=now --aggressive")
    if not success:
        print(f"⚠️  Warning: Failed to run garbage collection: {stderr}")
    
    print("✅ Git references cleaned")
    
    # Clean up temporary files
    print("🧹 Cleaning up temporary files...")
    credentials_file.unlink()
    if bfg_jar.exists():
        bfg_jar.unlink()
    
    print("✅ Temporary files cleaned")
    
    print("\n" + "=" * 50)
    print("✅ Git history cleanup completed!")
    print("📊 Repository has been cleaned of all sensitive data")
    print("💾 Backup created at:", backup_dir)
    print("\n⚠️  IMPORTANT: You must now force push to update the remote repository:")
    print("   git push origin --all --force")
    print("   git push origin --tags --force")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
