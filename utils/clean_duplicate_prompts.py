#!/usr/bin/env python3
"""
Clean Duplicate Prompts Script

This script identifies and handles duplicate prompt files in the prompts/agents directory.
It determines which prompts are actually used by the agents and moves duplicates to an archive folder.
"""

import os
import shutil
import re
import filecmp
from typing import Dict, List, Set, Tuple
import glob
import argparse

# Directory paths
AGENTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "agents")
PROMPTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "prompts")
AGENT_PROMPTS_DIR = os.path.join(PROMPTS_DIR, "agents")
ARCHIVE_DIR = os.path.join(PROMPTS_DIR, "archive")

# Ensure archive directory exists
os.makedirs(ARCHIVE_DIR, exist_ok=True)

def find_used_prompts() -> Set[str]:
    """
    Find all prompt files that are actually used in agent code.
    
    Returns:
        Set of prompt file names (without extension)
    """
    used_prompts = set()
    
    # Pattern to match load_prompt calls
    pattern = r'load_prompt\([\'"](.*?)[\'"]\)'
    
    # Search all agent files
    for agent_file in glob.glob(os.path.join(AGENTS_DIR, "*.py")):
        with open(agent_file, 'r', encoding='utf-8') as f:
            content = f.read()
            # Find all load_prompt calls
            matches = re.findall(pattern, content)
            used_prompts.update(matches)
    
    return used_prompts

def find_duplicate_prompts() -> Dict[str, List[str]]:
    """
    Find groups of duplicate prompt files based on content comparison.
    
    Returns:
        Dictionary mapping base name to list of duplicate file paths
    """
    prompt_files = glob.glob(os.path.join(AGENT_PROMPTS_DIR, "*.md"))
    
    # Group files by base name (without _prompt suffix)
    base_groups = {}
    for file_path in prompt_files:
        file_name = os.path.basename(file_path)
        base_name = file_name.replace("_prompt.md", "").replace("_security.md", "").replace("_assessment.md", "").replace("_redaction.md", "").replace("_qa.md", "").replace("_requirements.md", "").replace(".md", "")
        
        if base_name not in base_groups:
            base_groups[base_name] = []
        base_groups[base_name].append(file_path)
    
    # Only keep groups with multiple files
    duplicate_groups = {k: v for k, v in base_groups.items() if len(v) > 1}
    
    return duplicate_groups

def archive_duplicate(file_path: str, used_prompts: Set[str]) -> bool:
    """
    Archive a duplicate file if it's not in the list of used prompts.
    
    Args:
        file_path: Path to the file to potentially archive
        used_prompts: Set of prompt names that are being used
        
    Returns:
        True if archived, False otherwise
    """
    file_name = os.path.basename(file_path)
    prompt_name = os.path.splitext(file_name)[0]
    
    # If this exact prompt name is used, don't archive
    if prompt_name in used_prompts:
        return False
    
    # Check if a similar prompt is already being used
    # For example, if "prompt_security" is used, we can archive "prompt_security_old"
    for used_prompt in used_prompts:
        # Check if this prompt is a prefix or suffix of a used prompt
        if used_prompt.startswith(prompt_name + "_") or used_prompt.endswith("_" + prompt_name):
            # Move to archive
            dest_path = os.path.join(ARCHIVE_DIR, file_name)
            shutil.move(file_path, dest_path)
            print(f"Archived: {file_path} -> {dest_path} (superseded by {used_prompt})")
            return True
    
    # This is a bit more aggressive - if we have a base prompt like "agent_name.md"
    # and more specific prompts like "agent_name_purpose.md", we'll archive the base one
    base_name = prompt_name.split("_")[0]
    if prompt_name == base_name:  # This is a base prompt
        for used_prompt in used_prompts:
            if used_prompt.startswith(base_name + "_"):
                # Move to archive
                dest_path = os.path.join(ARCHIVE_DIR, file_name)
                shutil.move(file_path, dest_path)
                print(f"Archived: {file_path} -> {dest_path} (more specific prompt {used_prompt} exists)")
                return True
    
    return False

def are_similar_contents(file1: str, file2: str, threshold: float = 0.9) -> bool:
    """
    Compare two files to check if they have similar content.
    
    Args:
        file1: Path to first file
        file2: Path to second file
        threshold: Similarity threshold (0-1)
        
    Returns:
        True if files are similar, False otherwise
    """
    try:
        with open(file1, 'r', encoding='utf-8') as f1, open(file2, 'r', encoding='utf-8') as f2:
            content1 = f1.read()
            content2 = f2.read()
            
            # Very simple similarity check based on common lines
            lines1 = set(content1.splitlines())
            lines2 = set(content2.splitlines())
            
            common_lines = lines1.intersection(lines2)
            
            similarity = len(common_lines) / max(len(lines1), len(lines2))
            return similarity >= threshold
    except Exception as e:
        print(f"Error comparing {file1} and {file2}: {str(e)}")
        return False

def check_content_duplicates(file_paths: List[str]) -> List[Tuple[str, str]]:
    """
    Check which files are content duplicates or very similar.
    
    Args:
        file_paths: List of file paths to compare
        
    Returns:
        List of tuples of (primary_file, duplicate_file)
    """
    duplicates = []
    
    # Compare each file with every other file
    for i in range(len(file_paths)):
        for j in range(i + 1, len(file_paths)):
            # Check for exact match first
            if filecmp.cmp(file_paths[i], file_paths[j], shallow=False):
                duplicates.append((file_paths[i], file_paths[j]))
            # If not exact, check for similarity
            elif are_similar_contents(file_paths[i], file_paths[j]):
                duplicates.append((file_paths[i], file_paths[j]))

def main() -> None:
    """Clean duplicate prompt files."""
    # Parse arguments
    parser = argparse.ArgumentParser(description='Clean duplicate prompt files')
    parser.add_argument('--dry-run', action='store_true', help='Do not actually archive files')
    args = parser.parse_args()
    
    # Find prompts that are actually used
    used_prompts = find_used_prompts()
    print(f"Found {len(used_prompts)} prompts used in agent code:")
    for p in sorted(used_prompts):
        print(f"  - {p}")
    print()
    
    # Find all prompt files
    prompt_files = glob.glob(os.path.join(AGENT_PROMPTS_DIR, "*.md"))
    print(f"Found {len(prompt_files)} prompt files")
    
    # Identify unused prompts
    unused_prompts = []
    for file_path in prompt_files:
        file_name = os.path.basename(file_path)
        prompt_name = os.path.splitext(file_name)[0]
        if prompt_name not in used_prompts:
            unused_prompts.append(file_path)
    
    print(f"Found {len(unused_prompts)} potentially unused prompt files:")
    for p in sorted(unused_prompts):
        print(f"  - {os.path.basename(p)}")
    print()
    
    # Find potential duplicate groups
    duplicate_groups = find_duplicate_prompts()
    print(f"Found {len(duplicate_groups)} groups of potential duplicates:")
    for base, files in duplicate_groups.items():
        print(f"  {base}: {[os.path.basename(f) for f in files]}")
    print()
    
    # First, check for content duplicates
    print("Checking for content duplicates:")
    content_duplicates_to_archive = []
    
    for base, files in duplicate_groups.items():
        # Make sure all files still exist
        existing_files = [f for f in files if os.path.exists(f)]
        if len(existing_files) < 2:
            continue
            
        content_duplicates = check_content_duplicates(existing_files)
        
        if content_duplicates:
            print(f"Content duplicates for {base}:")
            for primary, duplicate in content_duplicates:
                primary_name = os.path.splitext(os.path.basename(primary))[0]
                duplicate_name = os.path.splitext(os.path.basename(duplicate))[0]
                
                print(f"  {os.path.basename(primary)} == {os.path.basename(duplicate)}")
                
                # Determine which one to archive based on usage
                if primary_name in used_prompts and duplicate_name not in used_prompts:
                    content_duplicates_to_archive.append(duplicate)
                    print(f"  Will archive: {duplicate_name} (unused)")
                elif duplicate_name in used_prompts and primary_name not in used_prompts:
                    content_duplicates_to_archive.append(primary)
                    print(f"  Will archive: {primary_name} (unused)")
                elif primary_name not in used_prompts and duplicate_name not in used_prompts:
                    # If neither is used, archive both in dry run for further inspection
                    if args.dry_run:
                        print(f"  Will need review: {primary_name} and {duplicate_name} (both unused)")
                    else:
                        # If we're running for real, archive the one with longer name
                        if len(primary_name) > len(duplicate_name):
                            content_duplicates_to_archive.append(primary)
                            print(f"  Will archive: {primary_name} (longer name)")
                        else:
                            content_duplicates_to_archive.append(duplicate)
                            print(f"  Will archive: {duplicate_name} (longer name)")
    
    # Archive files that are not used directly
    archived_count = 0
    files_to_archive = set(unused_prompts + content_duplicates_to_archive)
    
    for file_path in sorted(files_to_archive):
        if not os.path.exists(file_path):
            continue
            
        file_name = os.path.basename(file_path)
        prompt_name = os.path.splitext(file_name)[0]
        
        # Special case handling for known pairs
        # 1. For regulatory files
        if prompt_name == "regulatory":
            if "regulatory_assessment" in used_prompts and "regulatory_redaction" in used_prompts:
                print(f"Regulatory is unused - both assessment and redaction prompts exist")
                if not args.dry_run:
                    dest_path = os.path.join(ARCHIVE_DIR, file_name)
                    shutil.move(file_path, dest_path)
                    print(f"Archived: {file_path} -> {dest_path} (unused base prompt)")
                    archived_count += 1
                else:
                    print(f"Would archive: {file_path} (dry run)")
                continue
        
        # 2. Handle duplicate database_guard files
        if prompt_name == "database_guard":
            if "database_guard_security" in used_prompts:
                print(f"Database guard base prompt is unused - security prompt exists")
                if not args.dry_run:
                    dest_path = os.path.join(ARCHIVE_DIR, file_name)
                    shutil.move(file_path, dest_path)
                    print(f"Archived: {file_path} -> {dest_path} (unused base prompt)")
                    archived_count += 1
                else:
                    print(f"Would archive: {file_path} (dry run)")
                continue
        
        # Try to archive using our generic logic
        if not args.dry_run:
            if archive_duplicate(file_path, used_prompts):
                archived_count += 1
        else:
            # Simulate archive
            base_name = prompt_name.split("_")[0]
            will_archive = False
            
            # Check if this is superseded by a more specific prompt
            for used_prompt in used_prompts:
                if used_prompt.startswith(prompt_name + "_") or used_prompt.endswith("_" + prompt_name):
                    print(f"Would archive: {file_path} (superseded by {used_prompt}) (dry run)")
                    will_archive = True
                    break
            
            # Check if this is a base prompt with more specific versions
            if prompt_name == base_name:
                for used_prompt in used_prompts:
                    if used_prompt.startswith(base_name + "_"):
                        print(f"Would archive: {file_path} (more specific prompt {used_prompt} exists) (dry run)")
                        will_archive = True
                        break
            
            if not will_archive:
                print(f"Would not archive: {file_path} (no archive condition met) (dry run)")
    
    if args.dry_run:
        print(f"\nWould archive {archived_count} duplicate prompt files (dry run).")
    else:
        print(f"\nArchived {archived_count} duplicate prompt files.")

if __name__ == "__main__":
    main() 