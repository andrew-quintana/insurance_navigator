#!/usr/bin/env python3
"""
Script to create new build log markdown files with auto-fetched logs.

Creates four .md files with the naming pattern: YYYYMMDDHHMM-{render,vercel,safari,visual_observation}.md
- Render and Vercel logs are auto-fetched from APIs using deployment start time
- Safari and Visual Observation files are manual entry with minimal content

Usage:
    python scripts/create_build_logs.py                    # Use latest deployments
    python scripts/create_build_logs.py 202506041530       # Use specific timestamp
    python scripts/create_build_logs.py --render-only      # Only fetch Render logs
    python scripts/create_build_logs.py --vercel-only      # Only fetch Vercel logs
"""

import os
import sys
import requests
from datetime import datetime, timezone, timedelta
from pathlib import Path
import json
import argparse

# Define PST timezone (UTC-8, or UTC-7 during DST)
def get_pst_timezone():
    """Get PST timezone object, accounting for daylight saving time."""
    # PST is UTC-8, PDT is UTC-7
    # For simplicity, we'll use PST (UTC-8) - you can enhance this for DST if needed
    return timezone(timedelta(hours=-8))

def load_env_file(env_path=".env"):
    """Load environment variables from .env file."""
    if not os.path.exists(env_path):
        return False
    
    try:
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    # Remove quotes if present
                    value = value.strip('"\'')
                    os.environ[key.strip()] = value
        return True
    except Exception as e:
        print(f"❌ Error loading .env file: {e}")
        return False


def get_timestamp():
    """Get timestamp in YYYYMMDDHHMM format using PST."""
    pst = get_pst_timezone()
    return datetime.now(pst).strftime("%Y%m%d%H%M")


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


def parse_deployment_timestamp(timestamp_str):
    """Parse deployment timestamp to YYYYMMDDHHMM format in PST."""
    try:
        pst = get_pst_timezone()
        # Handle ISO format timestamps
        if 'T' in str(timestamp_str):
            dt = datetime.fromisoformat(str(timestamp_str).replace('Z', '+00:00'))
            # Convert to PST
            dt_pst = dt.astimezone(pst)
        else:
            # Handle millisecond timestamps (convert to seconds)
            timestamp_int = int(timestamp_str)
            if timestamp_int > 1e12:  # Millisecond timestamp
                timestamp_int = timestamp_int // 1000
            dt = datetime.fromtimestamp(timestamp_int, tz=timezone.utc)
            # Convert to PST
            dt_pst = dt.astimezone(pst)
        
        return dt_pst.strftime("%Y%m%d%H%M")
    except Exception as e:
        print(f"Warning: Could not parse timestamp {timestamp_str}: {e}")
        return get_timestamp()


def fetch_vercel_logs():
    """Fetch latest Vercel deployment logs."""
    token = os.getenv('VERCEL_API_TOKEN')
    project_id = os.getenv('VERCEL_PROJECT_ID')
    
    if not token or not project_id:
        print("⚠️  Missing VERCEL_API_TOKEN or VERCEL_PROJECT_ID environment variables")
        print("   Set these to enable automatic Vercel log fetching")
        return None, None
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get latest deployment
        deployments_url = f"https://api.vercel.com/v6/deployments?projectId={project_id}&limit=1"
        response = requests.get(deployments_url, headers=headers)
        response.raise_for_status()
        
        deployments = response.json().get('deployments', [])
        if not deployments:
            print("❌ No Vercel deployments found")
            return None, None
            
        deployment = deployments[0]
        deployment_id = deployment['uid']
        created_at = deployment['createdAt']
        
        # Try to get deployment events (limited info available via API)
        build_events = ""
        try:
            logs_url = f"https://api.vercel.com/v2/deployments/{deployment_id}/events"
            response = requests.get(logs_url, headers=headers)
            response.raise_for_status()
            events = response.json()
            
            if events and len(events) > 0:
                build_events += "## Available Events\n\n"
                event_count = 0
                for event in events:
                    timestamp = event.get('createdAt', '')
                    message = event.get('text', '')
                    if message:  # Only include events with actual messages
                        build_events += f"[{timestamp}] {message}\n"
                        event_count += 1
                
                if event_count == 0:
                    build_events = ""
                    
        except Exception as e:
            print(f"Warning: Could not fetch deployment events: {e}")
        
        # Format logs with helpful information
        timestamp_formatted = parse_deployment_timestamp(created_at)
        log_content = f"# Vercel Build Log - {timestamp_formatted}\n\n"
        log_content += f"**Deployment ID:** {deployment_id}\n"
        log_content += f"**Started:** {created_at}\n"
        log_content += f"**URL:** https://{deployment.get('url', 'N/A')}\n"
        log_content += f"**Status:** {deployment.get('state', 'N/A')}\n\n"
        
        # Add helpful links
        log_content += "## Build Logs Access\n\n"
        log_content += "**Note:** Detailed build logs (like console output, npm install logs, etc.) are not available via Vercel's public API.\n\n"
        log_content += "**To view complete build logs:**\n"
        log_content += f"1. Visit the [Vercel Dashboard](https://vercel.com/dashboard)\n"
        log_content += f"2. Navigate to your project\n"
        log_content += f"3. Click on this deployment: `{deployment_id}`\n"
        log_content += f"4. Click the 'Build Logs' button\n\n"
        log_content += f"**Direct deployment link:** https://vercel.com/dashboard/deployments/{deployment_id}\n\n"
        
        if build_events:
            log_content += build_events
        else:
            log_content += "## Events\n\n*No deployment events available via API*\n"
        
        # Add deployment metadata
        log_content += "\n## Deployment Info\n\n"
        log_content += f"- **Environment:** {deployment.get('target', 'production')}\n"
        log_content += f"- **Region:** {deployment.get('regions', ['N/A'])[0] if deployment.get('regions') else 'N/A'}\n"
        log_content += f"- **Build Duration:** {deployment.get('buildingAt', 'N/A')} - {deployment.get('readyStateAt', 'N/A')}\n"
        
        return timestamp_formatted, log_content
        
    except Exception as e:
        print(f"❌ Error fetching Vercel logs: {e}")
        return None, None


def fetch_render_logs():
    """Fetch latest Render deployment logs."""
    token = os.getenv('RENDER_API_TOKEN')
    service_id = os.getenv('RENDER_SERVICE_ID')
    
    if not token or not service_id:
        print("⚠️  Missing RENDER_API_TOKEN or RENDER_SERVICE_ID environment variables")
        print("   Set these to enable automatic Render log fetching")
        return None, None
    
    try:
        headers = {"Authorization": f"Bearer {token}"}
        
        # Get latest deployment
        deploys_url = f"https://api.render.com/v1/services/{service_id}/deploys?limit=1"
        response = requests.get(deploys_url, headers=headers)
        response.raise_for_status()
        
        deploys = response.json()
        if not deploys or len(deploys) == 0:
            print("❌ No Render deployments found")
            return None, None
            
        # Extract deploy info from the response structure
        deploy_info = deploys[0]
        deploy = deploy_info.get('deploy', {})
        deploy_id = deploy.get('id', 'unknown')
        created_at = deploy.get('createdAt', deploy.get('startedAt', ''))
        
        # Format basic deployment info (since logs endpoint is not working)
        timestamp_formatted = parse_deployment_timestamp(created_at)
        log_content = f"# Render Build Log - {timestamp_formatted}\n\n"
        log_content += f"**Deploy ID:** {deploy_id}\n"
        log_content += f"**Started:** {created_at}\n"
        log_content += f"**Status:** {deploy.get('status', 'N/A')}\n"
        log_content += f"**Trigger:** {deploy.get('trigger', 'N/A')}\n"
        
        # Add commit info if available
        commit = deploy.get('commit', {})
        if commit:
            log_content += f"**Commit ID:** {commit.get('id', 'N/A')[:8]}...\n"
            log_content += f"**Commit Message:** {commit.get('message', 'N/A')}\n"
        
        # Try to get deployment logs, but handle failures gracefully
        try:
            logs_url = f"https://api.render.com/v1/services/{service_id}/deploys/{deploy_id}/logs"
            response = requests.get(logs_url, headers=headers)
            if response.status_code == 200:
                logs = response.text
                log_content += "\n## Deployment Logs\n\n"
                log_content += "```\n"
                log_content += logs
                log_content += "\n```\n"
            else:
                log_content += f"\n## Deployment Logs\n\n*Logs not accessible via API (Status: {response.status_code})*\n"
                log_content += f"*Check Render dashboard for detailed logs: https://dashboard.render.com/web/{service_id}*\n"
        except Exception as logs_error:
            log_content += f"\n## Deployment Logs\n\n*Error fetching logs: {logs_error}*\n"
            log_content += f"*Check Render dashboard for detailed logs: https://dashboard.render.com/web/{service_id}*\n"
        
        return timestamp_formatted, log_content
        
    except Exception as e:
        print(f"❌ Error fetching Render logs: {e}")
        return None, None


def create_minimal_template(service_name, timestamp):
    """Create a minimal template for manual entry files."""
    return f"""# {service_name.title()} Log - {timestamp}

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


def create_build_logs(timestamp=None, render_only=False, vercel_only=False, safari_only=False, visual_only=False):
    """Create build log files with auto-fetched logs for render and vercel."""
    
    # Get the project root directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    build_logs_dir = project_root / "ui" / "build_logs"
    
    # Ensure build_logs directory exists
    build_logs_dir.mkdir(parents=True, exist_ok=True)
    
    created_files = []
    deployment_timestamp = timestamp
    
    # Initialize content variables
    vercel_content = None
    render_content = None
    
    # Auto-fetch logs and determine deployment timestamp
    if not render_only and not timestamp:
        print("🔍 Fetching Vercel deployment logs...")
        vercel_timestamp, vercel_content = fetch_vercel_logs()
        if vercel_timestamp and not deployment_timestamp:
            deployment_timestamp = vercel_timestamp
    
    if not vercel_only and not timestamp:
        print("🔍 Fetching Render deployment logs...")
        render_timestamp, render_content = fetch_render_logs()
        if render_timestamp and not deployment_timestamp:
            deployment_timestamp = render_timestamp
    
    # Use provided timestamp or current timestamp if no deployment found
    if not deployment_timestamp:
        if timestamp and validate_timestamp(timestamp):
            deployment_timestamp = timestamp
        else:
            deployment_timestamp = get_timestamp()
            if timestamp:
                print(f"Error: Invalid timestamp format '{timestamp}'. Expected format: YYYYMMDDHHMM")
                print("Example: 202506041530")
                return False
    
    print(f"📅 Using deployment timestamp: {deployment_timestamp}")
    
    # Create files based on mode
    services = []
    if not vercel_only:
        services.append("render")
    if not render_only:
        services.append("vercel")
    if not render_only and not vercel_only:
        services.extend(["safari", "visual_observation"])
    
    for service in services:
        filename = f"{deployment_timestamp}-{service}.md"
        filepath = build_logs_dir / filename
        
        # Check if file already exists
        if filepath.exists():
            print(f"Warning: File {filename} already exists. Skipping...")
            continue
        
        # Get content for the file
        if service == "render" and render_content is not None:
            template_content = render_content
        elif service == "vercel" and vercel_content is not None:
            template_content = vercel_content
        elif service == "visual_observation":
            template_content = create_visual_observation_template(deployment_timestamp)
        else:
            # Fallback for manual entry files or when API fetch failed
            template_content = create_minimal_template(service, deployment_timestamp)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(template_content)
            created_files.append(filename)
            
            if service in ['render', 'vercel'] and template_content and template_content.startswith('# '):
                print(f"✅ Created: {filename} (auto-fetched)")
            else:
                print(f"✓ Created: {filename} (manual entry)")
                
        except Exception as e:
            print(f"Error creating {filename}: {e}")
            return False
    
    if created_files:
        print(f"\n🎉 Successfully created {len(created_files)} build log files:")
        for filename in created_files:
            print(f"   - {filename}")
        print(f"\nFiles created in: {build_logs_dir}")
        
        # Show API setup instructions if needed
        if not os.getenv('VERCEL_API_TOKEN'):
            print(f"\n💡 To enable Vercel auto-fetch, set environment variables:")
            print(f"   export VERCEL_API_TOKEN='your-token'")
            print(f"   export VERCEL_PROJECT_ID='your-project-id'")
        
        if not os.getenv('RENDER_API_TOKEN'):
            print(f"\n💡 To enable Render auto-fetch, set environment variables:")
            print(f"   export RENDER_API_TOKEN='your-token'")
            print(f"   export RENDER_SERVICE_ID='your-service-id'")
            
    else:
        print("\n⚠️  No new files were created (all files already exist)")
    
    return True


def main():
    """Main function to handle command line arguments and create build logs."""
    
    # Load environment variables from .env file
    load_env_file()
    
    parser = argparse.ArgumentParser(description="Create build logs with auto-fetched deployment logs")
    parser.add_argument('timestamp', nargs='?', help='Custom timestamp (YYYYMMDDHHMM format)')
    parser.add_argument('--render-only', action='store_true', help='Only fetch Render logs')
    parser.add_argument('--vercel-only', action='store_true', help='Only fetch Vercel logs')
    parser.add_argument('--safari-only', action='store_true', help='Only fetch Safari logs')
    parser.add_argument('--visual-only', action='store_true', help='Only fetch Visual Observation logs')
    parser.add_argument('--latest', action='store_true', help='Explicitly fetch most recent deployments from each service')
    
    args = parser.parse_args()
    
    # Handle conflicting arguments
    if args.timestamp and args.latest:
        print("❌ Error: Cannot use both custom timestamp and --latest flag")
        print("   Use either a specific timestamp OR --latest, not both")
        sys.exit(1)
    
    timestamp = args.timestamp
    if args.latest:
        print("🔄 Explicitly fetching most recent deployments...")
        timestamp = None  # Force latest deployment fetch
    elif timestamp:
        print(f"📅 Using provided timestamp: {timestamp}")
    else:
        print("🔄 Using latest deployment timestamps (default behavior)...")
    
    if args.render_only:
        print("🔧 Mode: Render logs only")
    elif args.vercel_only:
        print("🌐 Mode: Vercel logs only")
    elif args.safari_only:
        print("🧭 Mode: Safari logs only")
    elif args.visual_only:
        print("👀 Mode: Visual Observation logs only")
    else:
        print("📋 Mode: Full deployment logs (Render + Vercel + Safari + Visual Observation)")
    
    success = create_build_logs(
        timestamp=timestamp,
        render_only=args.render_only,
        vercel_only=args.vercel_only,
        safari_only=args.safari_only,
        visual_only=args.visual_only
    )
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main() 