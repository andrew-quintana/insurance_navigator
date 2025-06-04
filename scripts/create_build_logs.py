#!/usr/bin/env python3
"""
Script to create new build log markdown files.

Creates four .md files with the naming pattern: YYYYMMDDHHMM-{render,safari,vercel,visual_observation}.md
Can use current timestamp or accept a custom timestamp as input.

Usage:
    python scripts/create_build_logs.py                    # Use current timestamp
    python scripts/create_build_logs.py 202506041530       # Use provided timestamp
"""

import os
import sys
from datetime import datetime
from pathlib import Path


def get_timestamp():
    """Get timestamp in YYYYMMDDHHMM format."""
    return datetime.now().strftime("%Y%m%d%H%M")


def validate_timestamp(timestamp_str):
    """Validate timestamp format YYYYMMDDHHMM."""
    if len(timestamp_str) != 12:
        return False
    
    try:
        # Try to parse the timestamp to validate it's a valid date/time
        datetime.strptime(timestamp_str, "%Y%m%d%H%M")
        return True
    except ValueError:
        return False


def create_build_log_template(service_name, timestamp):
    """Create a minimal template for build log files."""
    return f"""# {service_name.title()} Build Log - {timestamp}

"""


def create_visual_observation_template(timestamp):
    """Create a template for visual observation log files."""
    return f"""# Visual Observations - {timestamp}

## Session Overview
- **Timestamp**: {timestamp}
- **Observer**: 
- **Environment**: Production
- **Focus Area**: 

## Visual Observations

### User Interface
- **Layout & Design**:
  - 

- **User Experience**:
  - 

- **Performance**:
  - 

### Functionality
- **Core Features**:
  - 

- **Navigation**:
  - 

- **Responsiveness**:
  - 

### Issues Noticed
- **Visual Bugs**:
  - 

- **Performance Issues**:
  - 

- **Usability Concerns**:
  - 

### Positive Observations
- **Working Well**:
  - 

- **Good UX Elements**:
  - 

- **Performance Highlights**:
  - 

## Recommendations

### Immediate Actions
- [ ] 

### Future Improvements
- [ ] 

### Follow-up Required
- [ ] 

## Summary
- **Overall Assessment**: 
- **Priority Level**: 
- **Next Review Date**: 

---
*Visual observation log created on {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}*
"""


def create_build_logs(timestamp=None):
    """Create build log files for render, safari, vercel, and visual observation."""
    
    # Use provided timestamp or current timestamp
    if timestamp is None:
        timestamp = get_timestamp()
    elif not validate_timestamp(timestamp):
        print(f"Error: Invalid timestamp format '{timestamp}'. Expected format: YYYYMMDDHHMM")
        print("Example: 202506041530")
        return False
    
    # Get the project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    build_logs_dir = project_root / "ui" / "build_logs"
    
    # Ensure build_logs directory exists
    build_logs_dir.mkdir(parents=True, exist_ok=True)
    
    services = ["render", "safari", "vercel", "visual_observation"]
    created_files = []
    
    for service in services:
        filename = f"{timestamp}-{service}.md"
        filepath = build_logs_dir / filename
        
        # Check if file already exists
        if filepath.exists():
            print(f"Warning: File {filename} already exists. Skipping...")
            continue
        
        # Create the file with appropriate template content
        if service == "visual_observation":
            template_content = create_visual_observation_template(timestamp)
        else:
            template_content = create_build_log_template(service, timestamp)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(template_content)
            created_files.append(filename)
            print(f"✓ Created: {filename}")
        except Exception as e:
            print(f"Error creating {filename}: {e}")
            return False
    
    if created_files:
        print(f"\n✅ Successfully created {len(created_files)} build log files:")
        for filename in created_files:
            print(f"   - {filename}")
        print(f"\nFiles created in: {build_logs_dir}")
    else:
        print("\n⚠️  No new files were created (all files already exist)")
    
    return True


def main():
    """Main function to handle command line arguments and create build logs."""
    
    # Check command line arguments
    if len(sys.argv) > 2:
        print("Usage: python scripts/create_build_logs.py [YYYYMMDDHHMM]")
        print("Example: python scripts/create_build_logs.py 202506041530")
        sys.exit(1)
    
    timestamp = None
    if len(sys.argv) == 2:
        timestamp = sys.argv[1]
        print(f"Using provided timestamp: {timestamp}")
    else:
        timestamp = get_timestamp()
        print(f"Using current timestamp: {timestamp}")
    
    success = create_build_logs(timestamp)
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main() 