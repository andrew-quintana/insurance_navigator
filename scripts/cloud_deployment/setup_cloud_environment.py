#!/usr/bin/env python3
"""
Cloud Environment Setup Script

Sets up cloud deployment environment for Phase 1 testing.
Configures Vercel, Render, and Supabase for production deployment.
"""

import os
import sys
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional


class CloudEnvironmentSetup:
    """Sets up cloud deployment environment"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.config = {}
        self.setup_log = []
    
    def log(self, message: str):
        """Log setup progress"""
        print(f"🔧 {message}")
        self.setup_log.append(message)
    
    def error(self, message: str):
        """Log error and exit"""
        print(f"❌ {message}")
        sys.exit(1)
    
    def success(self, message: str):
        """Log success"""
        print(f"✅ {message}")
        self.setup_log.append(f"SUCCESS: {message}")
    
    def setup_vercel_environment(self) -> bool:
        """Set up Vercel environment"""
        self.log("Setting up Vercel environment...")
        
        try:
            # Check if Vercel CLI is installed
            result = subprocess.run(['vercel', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                self.log("Installing Vercel CLI...")
                subprocess.run(['npm', 'install', '-g', 'vercel'], check=True)
            
            # Check if project is linked
            vercel_dir = self.project_root / "ui"
            os.chdir(vercel_dir)
            
            result = subprocess.run(['vercel', 'ls'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                self.log("Linking Vercel project...")
                subprocess.run(['vercel', 'link'], check=True)
            
            # Set environment variables
            env_vars = {
                'NEXT_PUBLIC_API_BASE_URL': 'https://insurance-navigator-api.onrender.com',
                'NEXT_PUBLIC_APP_ENV': 'production',
                'NEXT_PUBLIC_APP_VERSION': '1.0.0'
            }
            
            for key, value in env_vars.items():
                self.log(f"Setting Vercel environment variable: {key}")
                subprocess.run(['vercel', 'env', 'add', key, 'production'], 
                             input=value, text=True, check=True)
            
            self.success("Vercel environment setup completed")
            return True
            
        except subprocess.CalledProcessError as e:
            self.error(f"Vercel setup failed: {e}")
        except Exception as e:
            self.error(f"Vercel setup error: {e}")
    
    def setup_render_environment(self) -> bool:
        """Set up Render environment"""
        self.log("Setting up Render environment...")
        
        try:
            # Check if Render CLI is installed
            result = subprocess.run(['render', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                self.log("Installing Render CLI...")
                subprocess.run(['npm', 'install', '-g', '@render/cli'], check=True)
            
            # Login to Render
            self.log("Logging into Render...")
            subprocess.run(['render', 'login'], check=True)
            
            # Create service from render.yaml
            render_config = self.project_root / "config" / "render" / "render.yaml"
            if render_config.exists():
                self.log("Creating Render service from configuration...")
                subprocess.run(['render', 'service', 'create', '--file', str(render_config)], 
                             check=True)
            
            self.success("Render environment setup completed")
            return True
            
        except subprocess.CalledProcessError as e:
            self.error(f"Render setup failed: {e}")
        except Exception as e:
            self.error(f"Render setup error: {e}")
    
    def setup_supabase_environment(self) -> bool:
        """Set up Supabase environment"""
        self.log("Setting up Supabase environment...")
        
        try:
            # Check if Supabase CLI is installed
            result = subprocess.run(['supabase', '--version'], 
                                  capture_output=True, text=True)
            if result.returncode != 0:
                self.log("Installing Supabase CLI...")
                subprocess.run(['npm', 'install', '-g', 'supabase'], check=True)
            
            # Login to Supabase
            self.log("Logging into Supabase...")
            subprocess.run(['supabase', 'login'], check=True)
            
            # Link to project
            supabase_dir = self.project_root / "supabase"
            os.chdir(supabase_dir)
            
            self.log("Linking Supabase project...")
            subprocess.run(['supabase', 'link', '--project-ref', 'your-project-id'], 
                         check=True)
            
            # Deploy migrations
            self.log("Deploying database migrations...")
            subprocess.run(['supabase', 'db', 'push'], check=True)
            
            # Deploy edge functions
            self.log("Deploying edge functions...")
            subprocess.run(['supabase', 'functions', 'deploy'], check=True)
            
            self.success("Supabase environment setup completed")
            return True
            
        except subprocess.CalledProcessError as e:
            self.error(f"Supabase setup failed: {e}")
        except Exception as e:
            self.error(f"Supabase setup error: {e}")
    
    def create_deployment_scripts(self) -> bool:
        """Create deployment scripts"""
        self.log("Creating deployment scripts...")
        
        try:
            scripts_dir = self.project_root / "scripts" / "cloud_deployment"
            scripts_dir.mkdir(parents=True, exist_ok=True)
            
            # Create Vercel deployment script
            vercel_script = scripts_dir / "deploy_vercel.sh"
            with open(vercel_script, 'w') as f:
                f.write("""#!/bin/bash
# Vercel Deployment Script

set -e

echo "🚀 Deploying to Vercel..."

cd ui

# Install dependencies
npm ci

# Build the application
npm run build

# Deploy to Vercel
vercel --prod

echo "✅ Vercel deployment completed"
""")
            vercel_script.chmod(0o755)
            
            # Create Render deployment script
            render_script = scripts_dir / "deploy_render.sh"
            with open(render_script, 'w') as f:
                f.write("""#!/bin/bash
# Render Deployment Script

set -e

echo "🚀 Deploying to Render..."

# Deploy service from configuration
render service create --file config/render/render.yaml

echo "✅ Render deployment completed"
""")
            render_script.chmod(0o755)
            
            # Create Supabase deployment script
            supabase_script = scripts_dir / "deploy_supabase.sh"
            with open(supabase_script, 'w') as f:
                f.write("""#!/bin/bash
# Supabase Deployment Script

set -e

echo "🚀 Deploying to Supabase..."

cd supabase

# Deploy database migrations
supabase db push

# Deploy edge functions
supabase functions deploy

echo "✅ Supabase deployment completed"
""")
            supabase_script.chmod(0o755)
            
            self.success("Deployment scripts created")
            return True
            
        except Exception as e:
            self.error(f"Failed to create deployment scripts: {e}")
    
    def create_environment_validation(self) -> bool:
        """Create environment validation script"""
        self.log("Creating environment validation...")
        
        try:
            validation_script = self.project_root / "scripts" / "cloud_deployment" / "validate_environment.py"
            
            with open(validation_script, 'w') as f:
                f.write("""#!/usr/bin/env python3
\"\"\"
Environment Validation Script

Validates that all required environment variables are set for cloud deployment.
\"\"\"

import os
import sys
from typing import List, Dict

def validate_environment() -> bool:
    \"\"\"Validate environment variables\"\"\"
    required_vars = {
        'SUPABASE_URL': 'Supabase project URL',
        'SUPABASE_ANON_KEY': 'Supabase anonymous key',
        'SUPABASE_SERVICE_ROLE_KEY': 'Supabase service role key',
        'OPENAI_API_KEY': 'OpenAI API key',
        'LLAMAPARSE_API_KEY': 'LlamaParse API key',
        'JWT_SECRET_KEY': 'JWT secret key'
    }
    
    missing_vars = []
    
    for var, description in required_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"{var} ({description})")
    
    if missing_vars:
        print("❌ Missing required environment variables:")
        for var in missing_vars:
            print(f"  - {var}")
        return False
    
    print("✅ All required environment variables are set")
    return True

if __name__ == "__main__":
    if validate_environment():
        sys.exit(0)
    else:
        sys.exit(1)
""")
            
            validation_script.chmod(0o755)
            self.success("Environment validation script created")
            return True
            
        except Exception as e:
            self.error(f"Failed to create environment validation: {e}")
    
    def run_setup(self) -> bool:
        """Run complete setup process"""
        self.log("Starting cloud environment setup...")
        
        try:
            # Create deployment scripts
            if not self.create_deployment_scripts():
                return False
            
            # Create environment validation
            if not self.create_environment_validation():
                return False
            
            # Note: Actual platform setup requires manual configuration
            self.log("Cloud environment setup preparation completed")
            self.log("Manual steps required:")
            self.log("1. Configure Vercel project and environment variables")
            self.log("2. Configure Render service and environment variables")
            self.log("3. Configure Supabase project and environment variables")
            self.log("4. Run Phase 1 tests to validate setup")
            
            self.success("Cloud environment setup preparation completed")
            return True
            
        except Exception as e:
            self.error(f"Setup failed: {e}")


def main():
    """Main function"""
    setup = CloudEnvironmentSetup()
    
    try:
        success = setup.run_setup()
        if success:
            print("\n🎉 Cloud environment setup preparation completed!")
            print("\nNext steps:")
            print("1. Configure actual cloud platform credentials")
            print("2. Deploy to Vercel, Render, and Supabase")
            print("3. Run Phase 1 tests to validate deployment")
            sys.exit(0)
        else:
            print("\n💥 Cloud environment setup failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n⚠️ Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Setup failed with error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
