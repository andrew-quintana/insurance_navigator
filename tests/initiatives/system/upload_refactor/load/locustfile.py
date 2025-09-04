"""Load testing configuration using Locust."""
import json
import random
from locust import HttpUser, task, between
from datetime import datetime
from typing import Dict, Any

class InsuranceNavigatorUser(HttpUser):
    """Simulates a regular user of the Insurance Navigator platform."""
    
    wait_time = between(3, 7)  # Wait 3-7 seconds between tasks
    
    def on_start(self):
        """Setup before starting tasks."""
        # Login
        self.token = None
        self.user_id = None
        self.login()
    
    def login(self):
        """Login and store the token."""
        # Generate unique email for concurrent testing
        unique_id = f"{int(random.random() * 1000000)}"
        email = f"loadtest_user_{unique_id}@example.com"
        
        # Register first (in case user doesn't exist)
        register_data = {
            "email": email,
            "password": "LoadTest123!",
            "name": f"Load Test User {unique_id}"
        }
        
        with self.client.post("/register", json=register_data, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                self.token = data["access_token"]
                self.user_id = data.get("user_id")
            else:
                # If registration fails, try login
                login_data = {
                    "email": email,
                    "password": "LoadTest123!"
                }
                response = self.client.post("/login", json=login_data)
                data = response.json()
                self.token = data["access_token"]
                self.user_id = data.get("user_id")
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers with auth token."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    @task(3)
    def chat_query(self):
        """Send a chat query - highest frequency task."""
        queries = [
            "What are my prescription drug benefits?",
            "How do I find a specialist in my network?",
            "What is my deductible?",
            "How do I submit a claim?",
            "Do I need prior authorization for this procedure?"
        ]
        
        data = {
            "query": random.choice(queries),
            "user_id": self.user_id
        }
        
        self.client.post(
            "/chat",
            headers=self.get_headers(),
            json=data
        )
    
    @task(2)
    def view_documents(self):
        """View user's documents - medium frequency task."""
        self.client.get(
            "/documents",
            headers=self.get_headers()
        )
    
    @task(1)
    def upload_document(self):
        """Upload a document - lower frequency task."""
        # Simulate document metadata
        doc_data = {
            "filename": f"test_document_{random.randint(1000, 9999)}.pdf",
            "document_type": "insurance_policy",
            "metadata": {
                "policy_number": f"POL-{random.randint(10000, 99999)}",
                "insurance_type": random.choice(["health", "dental", "vision"])
            }
        }
        
        self.client.post(
            "/documents/upload",
            headers=self.get_headers(),
            json=doc_data
        )

class InsuranceNavigatorAdmin(HttpUser):
    """Simulates an admin user with additional privileges."""
    
    wait_time = between(5, 10)  # Longer wait time for admin tasks
    
    def on_start(self):
        """Setup before starting tasks."""
        self.token = None
        self.login_as_admin()
    
    def login_as_admin(self):
        """Login as admin user."""
        login_data = {
            "email": "admin@insurance-navigator.com",
            "password": "AdminLoadTest123!"
        }
        
        response = self.client.post("/login", json=login_data)
        data = response.json()
        self.token = data["access_token"]
    
    def get_headers(self) -> Dict[str, str]:
        """Get headers with admin auth token."""
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    @task(3)
    def monitor_system_health(self):
        """Check system health metrics."""
        self.client.get(
            "/admin/health",
            headers=self.get_headers()
        )
    
    @task(2)
    def view_user_analytics(self):
        """View user analytics and metrics."""
        self.client.get(
            "/admin/analytics/users",
            headers=self.get_headers()
        )
    
    @task(1)
    def manage_documents(self):
        """Manage document processing queue."""
        self.client.get(
            "/admin/documents/queue",
            headers=self.get_headers()
        )

def run_load_test():
    """Run load test from command line."""
    import subprocess
    import sys
    
    # Default test parameters
    duration = "10m"
    users = 100
    spawn_rate = 10
    
    # Allow parameter override from command line
    if len(sys.argv) > 1:
        duration = sys.argv[1]
    if len(sys.argv) > 2:
        users = int(sys.argv[2])
    if len(sys.argv) > 3:
        spawn_rate = int(sys.argv[3])
    
    # Run Locust in headless mode
    cmd = [
        "locust",
        "-f", __file__,
        "--headless",
        "--host=http://localhost:8000",
        "--users", str(users),
        "--spawn-rate", str(spawn_rate),
        "--run-time", duration
    ]
    
    subprocess.run(cmd)

if __name__ == "__main__":
    run_load_test() 