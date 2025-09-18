#!/usr/bin/env python3
"""
Deploy upload pipeline to Render.com
"""

import os
import sys
import subprocess
import time
import requests
from pathlib import Path

class RenderDeployer:
    """Deploy upload pipeline to Render.com"""
    
    def __init__(self):
        self.render_config = "render-upload-pipeline.yaml"
        self.api_service_name = "upload-pipeline-api"
        self.worker_service_name = "upload-pipeline-worker"
        
    def check_prerequisites(self):
        """Check if prerequisites are met"""
        print("🔍 Checking prerequisites...")
        
        # Check if render CLI is installed
        try:
            result = subprocess.run(['render', '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Render CLI installed")
            else:
                print("❌ Render CLI not found. Please install it first:")
                print("   curl -fsSL https://cli.render.com/install | sh")
                return False
        except FileNotFoundError:
            print("❌ Render CLI not found. Please install it first:")
            print("   curl -fsSL https://cli.render.com/install | sh")
            return False
        
        # Check if logged in to Render
        try:
            result = subprocess.run(['render', 'whoami'], capture_output=True, text=True)
            if result.returncode == 0:
                print("✅ Logged in to Render")
            else:
                print("❌ Not logged in to Render. Please run: render login")
                return False
        except Exception as e:
            print(f"❌ Error checking Render login: {e}")
            return False
        
        # Check if config file exists
        if not Path(self.render_config).exists():
            print(f"❌ Render config file not found: {self.render_config}")
            return False
        else:
            print(f"✅ Render config file found: {self.render_config}")
        
        return True
    
    def deploy_services(self):
        """Deploy services to Render"""
        print("\n🚀 Deploying services to Render...")
        
        try:
            # Deploy using render.yaml
            print(f"Deploying with config: {self.render_config}")
            result = subprocess.run([
                'render', 'deploy', 
                '--config', self.render_config,
                '--service', self.api_service_name,
                '--service', self.worker_service_name
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ Services deployed successfully")
                print(result.stdout)
                return True
            else:
                print("❌ Deployment failed")
                print(result.stderr)
                return False
                
        except Exception as e:
            print(f"❌ Deployment error: {e}")
            return False
    
    def wait_for_services(self, timeout=300):
        """Wait for services to be healthy"""
        print(f"\n⏳ Waiting for services to be healthy (timeout: {timeout}s)...")
        
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                # Get service status
                result = subprocess.run([
                    'render', 'services', 'list'
                ], capture_output=True, text=True)
                
                if result.returncode == 0:
                    print("Service status:")
                    print(result.stdout)
                    
                    # Check if services are running
                    if "RUNNING" in result.stdout:
                        print("✅ Services are running")
                        return True
                    else:
                        print("⏳ Services still starting...")
                        time.sleep(10)
                else:
                    print(f"❌ Error checking service status: {result.stderr}")
                    time.sleep(10)
                    
            except Exception as e:
                print(f"❌ Error waiting for services: {e}")
                time.sleep(10)
        
        print("❌ Timeout waiting for services to be healthy")
        return False
    
    def test_deployed_services(self):
        """Test deployed services"""
        print("\n🧪 Testing deployed services...")
        
        # Get service URLs
        try:
            result = subprocess.run([
                'render', 'services', 'list', '--format', 'json'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                import json
                services = json.loads(result.stdout)
                
                api_url = None
                for service in services:
                    if service.get('name') == self.api_service_name:
                        api_url = service.get('serviceUrl')
                        break
                
                if api_url:
                    print(f"API URL: {api_url}")
                    
                    # Test health endpoint
                    try:
                        response = requests.get(f"{api_url}/health", timeout=10)
                        if response.status_code == 200:
                            data = response.json()
                            print(f"✅ API health check: {data['status']}")
                            return True
                        else:
                            print(f"❌ API health check failed: {response.status_code}")
                            return False
                    except Exception as e:
                        print(f"❌ API health check error: {e}")
                        return False
                else:
                    print("❌ Could not find API service URL")
                    return False
            else:
                print(f"❌ Error getting service URLs: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing services: {e}")
            return False
    
    def deploy(self):
        """Main deployment process"""
        print("🚀 Deploying Upload Pipeline to Render.com")
        print("=" * 50)
        
        # Check prerequisites
        if not self.check_prerequisites():
            print("\n❌ Prerequisites not met. Please fix and try again.")
            return False
        
        # Deploy services
        if not self.deploy_services():
            print("\n❌ Deployment failed.")
            return False
        
        # Wait for services
        if not self.wait_for_services():
            print("\n❌ Services did not become healthy in time.")
            return False
        
        # Test services
        if not self.test_deployed_services():
            print("\n❌ Service testing failed.")
            return False
        
        print("\n🎉 Deployment successful!")
        print("✅ Upload pipeline is deployed and running on Render.com")
        return True

def main():
    """Main function"""
    deployer = RenderDeployer()
    success = deployer.deploy()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
