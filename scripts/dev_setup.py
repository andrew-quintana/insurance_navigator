#!/usr/bin/env python3
"""
Development Environment Setup Script (Python version)
Automatically starts ngrok, extracts URL, and updates configuration files
"""

import os
import sys
import json
import time
import subprocess
import requests
from pathlib import Path
from typing import Optional

class DevSetup:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.ngrok_url: Optional[str] = None
        self.ngrok_pid: Optional[int] = None
        
    def log(self, message: str, level: str = "INFO"):
        """Print colored log messages"""
        colors = {
            "INFO": "\033[0;34m",
            "SUCCESS": "\033[0;32m",
            "WARNING": "\033[1;33m",
            "ERROR": "\033[0;31m"
        }
        reset = "\033[0m"
        print(f"{colors.get(level, '')}[{level}]{reset} {message}")
    
    def check_prerequisites(self) -> bool:
        """Check if required tools are available"""
        # Check if ngrok is installed
        try:
            subprocess.run(["ngrok", "version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            self.log("ngrok is not installed. Please install it first:", "ERROR")
            self.log("  brew install ngrok  # on macOS", "ERROR")
            self.log("  or download from https://ngrok.com/download", "ERROR")
            return False
        
        # Check if API server is running
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code != 200:
                raise requests.RequestException("API server not healthy")
        except requests.RequestException:
            self.log("API server is not running on port 8000", "WARNING")
            self.log("Please start the API server first:", "WARNING")
            self.log("  ENVIRONMENT=development python main.py", "WARNING")
            return False
        
        self.log("API server is running ✅", "SUCCESS")
        return True
    
    def start_ngrok(self) -> bool:
        """Start ngrok tunnel"""
        self.log("Cleaning up existing ngrok processes...")
        try:
            subprocess.run(["pkill", "-f", "ngrok"], capture_output=True)
            time.sleep(2)
        except:
            pass
        
        self.log("Starting ngrok tunnel...")
        try:
            # Start ngrok in background
            process = subprocess.Popen(
                ["ngrok", "http", "8000", "--log=stdout"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.ngrok_pid = process.pid
            
            # Wait for ngrok to start
            self.log("Waiting for ngrok to initialize...")
            time.sleep(5)
            
            return True
        except Exception as e:
            self.log(f"Failed to start ngrok: {e}", "ERROR")
            return False
    
    def extract_ngrok_url(self) -> bool:
        """Extract ngrok URL from ngrok API"""
        self.log("Extracting ngrok URL...")
        
        for attempt in range(10):
            try:
                # Try ngrok API
                response = requests.get("http://localhost:4040/api/tunnels", timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    for tunnel in data.get("tunnels", []):
                        if tunnel.get("proto") == "https":
                            self.ngrok_url = tunnel.get("public_url")
                            break
                
                if self.ngrok_url:
                    break
                    
            except requests.RequestException:
                pass
            
            self.log(f"Attempt {attempt + 1}/10: Waiting for ngrok URL...")
            time.sleep(2)
        
        if not self.ngrok_url:
            self.log("Failed to extract ngrok URL after 10 attempts", "ERROR")
            return False
        
        self.log(f"Ngrok URL extracted: {self.ngrok_url}", "SUCCESS")
        return True
    
    def update_config_files(self) -> bool:
        """Update configuration files with ngrok URL"""
        self.log("Updating configuration files...")
        
        try:
            # Update .env.development (for reference, but services will use dynamic discovery)
            env_dev_path = self.project_root / ".env.development"
            if env_dev_path.exists():
                self.log("Updating .env.development...")
                content = env_dev_path.read_text()
                if "NGROK_URL=" in content:
                    content = content.replace(
                        content.split("NGROK_URL=")[1].split("\n")[0],
                        self.ngrok_url
                    )
                else:
                    content += f"\nNGROK_URL={self.ngrok_url}\n"
                env_dev_path.write_text(content)
                self.log("Updated .env.development", "SUCCESS")
            else:
                self.log("Creating .env.development...")
                env_dev_path.write_text(f"NGROK_URL={self.ngrok_url}\n")
                self.log("Created .env.development", "SUCCESS")
            
            # Update ui/.env.local (frontend still needs static URLs)
            ui_env_path = self.project_root / "ui" / ".env.local"
            ui_env_content = f"""# Supabase Configuration
NEXT_PUBLIC_SUPABASE_URL=http://127.0.0.1:54321
NEXT_PUBLIC_SUPABASE_ANON_KEY=${SUPABASE_JWT_TOKEN}

# API Configuration
NEXT_PUBLIC_API_URL={self.ngrok_url}
NEXT_PUBLIC_API_BASE_URL={self.ngrok_url}

# Feature Flags
NEXT_PUBLIC_ENABLE_VECTOR_PROCESSING=true
NEXT_PUBLIC_ENABLE_REGULATORY_PROCESSING=true
"""
            
            if ui_env_path.exists():
                self.log("Updating ui/.env.local...")
                ui_env_path.write_text(ui_env_content)
                self.log("Updated ui/.env.local", "SUCCESS")
            else:
                self.log("Creating ui/.env.local...")
                ui_env_path.write_text(ui_env_content)
                self.log("Created ui/.env.local", "SUCCESS")
            
            # Note: Worker now uses dynamic ngrok discovery, no need to update hardcoded URLs
            self.log("Worker uses dynamic ngrok discovery - no hardcoded URLs to update", "SUCCESS")
            
            return True
            
        except Exception as e:
            self.log(f"Failed to update configuration files: {e}", "ERROR")
            return False
    
    def save_ngrok_pid(self):
        """Save ngrok PID for cleanup"""
        if self.ngrok_pid:
            pid_file = Path("/tmp/ngrok.pid")
            pid_file.write_text(str(self.ngrok_pid))
            self.log("Ngrok PID saved to /tmp/ngrok.pid")
    
    def display_summary(self):
        """Display setup summary"""
        print()
        self.log("🎉 Development environment setup complete!", "SUCCESS")
        print()
        print("📋 Summary:")
        print(f"  • Ngrok URL: {self.ngrok_url}")
        print("  • API Server: http://localhost:8000")
        print("  • Frontend: http://localhost:3000 (if running)")
        print("  • Ngrok Dashboard: http://localhost:4040")
        print()
        print("📁 Updated files:")
        print("  • .env.development (for reference)")
        print("  • ui/.env.local (frontend needs static URLs)")
        print("  • backend/workers/enhanced_base_worker.py (now uses dynamic discovery)")
        print()
        print("🔄 Next steps:")
        print("  1. Restart the enhanced worker to pick up the new ngrok URL:")
        print("     python backend/workers/enhanced_runner.py")
        print("  2. Restart the frontend to pick up the new API URL:")
        print("     cd ui && npm run dev")
        print()
        if self.ngrok_pid:
            print(f"🛑 To stop ngrok: kill {self.ngrok_pid}")
        print("📊 Monitor ngrok: http://localhost:4040")
    
    def run(self) -> bool:
        """Run the complete setup process"""
        try:
            if not self.check_prerequisites():
                return False
            
            if not self.start_ngrok():
                return False
            
            if not self.extract_ngrok_url():
                return False
            
            if not self.update_config_files():
                return False
            
            self.save_ngrok_pid()
            self.display_summary()
            return True
            
        except KeyboardInterrupt:
            self.log("Setup interrupted by user", "WARNING")
            return False
        except Exception as e:
            self.log(f"Setup failed: {e}", "ERROR")
            return False

def main():
    """Main entry point"""
    setup = DevSetup()
    success = setup.run()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
