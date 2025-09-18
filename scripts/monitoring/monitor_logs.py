#!/usr/bin/env python3
"""
Log Monitoring Script for Insurance Navigator
Monitors both API server and Worker service logs in real-time
"""

import subprocess
import sys
import time
import signal
import os
from datetime import datetime
from typing import List, Optional

class LogMonitor:
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.running = True
        
    def start_api_logs(self):
        """Start monitoring API server logs"""
        print("🔍 Starting API Server log monitoring...")
        try:
            # Monitor the API server log file
            if os.path.exists("logs/api_server.log"):
                process = subprocess.Popen(
                    ["tail", "-f", "logs/api_server.log"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
                self.processes.append(process)
                print("✅ API Server logs: logs/api_server.log")
            else:
                print("⚠️  API Server log file not found: logs/api_server.log")
        except Exception as e:
            print(f"❌ Error starting API log monitoring: {e}")
    
    def start_worker_logs(self):
        """Start monitoring Worker service logs"""
        print("🔍 Starting Worker Service log monitoring...")
        try:
            # The worker service is running via uvicorn, so we need to check its output
            # Since it's running in a different terminal, we'll show how to access it
            print("ℹ️  Worker Service is running via uvicorn on port 8001")
            print("ℹ️  To see worker logs, check the terminal where it was started")
            print("ℹ️  Or restart it with: python -m uvicorn api.upload_pipeline.main:app --host 0.0.0.0 --port 8001 --log-level info")
        except Exception as e:
            print(f"❌ Error starting Worker log monitoring: {e}")
    
    def show_log_commands(self):
        """Show useful log monitoring commands"""
        print("\n" + "="*60)
        print("📋 LOG MONITORING COMMANDS")
        print("="*60)
        
        print("\n🔧 API Server Logs:")
        print("  Real-time:     tail -f logs/api_server.log")
        print("  Last 50 lines: tail -50 logs/api_server.log")
        print("  Search errors: grep -i error logs/api_server.log")
        print("  Search warnings: grep -i warning logs/api_server.log")
        
        print("\n🔧 Worker Service Logs:")
        print("  The worker service is running in a separate process")
        print("  To see its logs, you need to:")
        print("  1. Find the terminal where it's running")
        print("  2. Or restart it with logging:")
        print("     python -m uvicorn api.upload_pipeline.main:app --host 0.0.0.0 --port 8001 --log-level info > logs/worker_service.log 2>&1 &")
        
        print("\n🔧 Combined Log Monitoring:")
        print("  Monitor both:  tail -f logs/api_server.log logs/worker_service.log")
        print("  Search both:   grep -i 'error\\|warning' logs/*.log")
        
        print("\n🔧 Service Status:")
        print("  API Health:    curl -s http://localhost:8000/health | python -m json.tool")
        print("  Worker Health: curl -s http://localhost:8001/health | python -m json.tool")
        print("  Resilience:    curl -s http://localhost:8000/debug-resilience | python -m json.tool")
    
    def monitor_logs(self):
        """Start monitoring all logs"""
        print("🚀 Insurance Navigator Log Monitor")
        print("="*50)
        print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Start monitoring
        self.start_api_logs()
        self.start_worker_logs()
        
        # Show commands
        self.show_log_commands()
        
        print("\n" + "="*60)
        print("📊 REAL-TIME LOG MONITORING")
        print("="*60)
        print("Press Ctrl+C to stop monitoring")
        print("="*60)
        
        try:
            # Monitor the processes
            while self.running:
                time.sleep(1)
                
                # Check if processes are still running
                for i, process in enumerate(self.processes):
                    if process.poll() is not None:
                        print(f"⚠️  Process {i} has stopped")
                        self.processes.pop(i)
                        break
                        
        except KeyboardInterrupt:
            print("\n🛑 Stopping log monitoring...")
            self.stop()
    
    def stop(self):
        """Stop all monitoring processes"""
        self.running = False
        for process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
            except:
                process.kill()
        print("✅ Log monitoring stopped")

def main():
    monitor = LogMonitor()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "api":
            print("🔍 API Server Logs Only")
            monitor.start_api_logs()
            monitor.show_log_commands()
            
        elif command == "worker":
            print("🔍 Worker Service Logs Only")
            monitor.start_worker_logs()
            monitor.show_log_commands()
            
        elif command == "commands":
            print("📋 Log Monitoring Commands")
            monitor.show_log_commands()
            
        else:
            print(f"Unknown command: {command}")
            print("Usage: python monitor_logs.py [api|worker|commands]")
    else:
        # Full monitoring
        monitor.monitor_logs()

if __name__ == "__main__":
    main()
