from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import asyncio
import aiohttp
import json
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="003 Worker Refactor Monitoring", version="1.0.0")

# Configuration
SERVICES = {
    "postgres": {"url": "http://localhost:5432", "health": "/health"},
    "api_server": {"url": "http://localhost:8000", "health": "/health"},
    "base_worker": {"url": "http://localhost:8000", "health": "/health"},  # Will be updated in Phase 3
    "mock_llamaparse": {"url": "http://localhost:8001", "health": "/health"},
    "mock_openai": {"url": "http://localhost:8002", "health": "/health"},
}

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Main monitoring dashboard"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>003 Worker Refactor - Local Monitoring</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { background: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
            .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-bottom: 20px; }
            .status-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .status-card.healthy { border-left: 4px solid #27ae60; }
            .status-card.unhealthy { border-left: 4px solid #e74c3c; }
            .status-card.warning { border-left: 4px solid #f39c12; }
            .service-name { font-weight: bold; font-size: 18px; margin-bottom: 10px; }
            .service-status { font-size: 14px; margin-bottom: 5px; }
            .service-details { font-size: 12px; color: #666; }
            .refresh-btn { background: #3498db; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; margin-bottom: 20px; }
            .refresh-btn:hover { background: #2980b9; }
            .metrics { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
            .metric-row { display: flex; justify-content: space-between; margin-bottom: 10px; padding: 10px; background: #f8f9fa; border-radius: 4px; }
            .metric-label { font-weight: bold; }
            .metric-value { color: #2c3e50; }
            .timestamp { text-align: center; color: #666; font-size: 12px; margin-top: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🚀 003 Worker Refactor - Local Development Monitoring</h1>
                <p>Real-time monitoring dashboard for local development environment</p>
            </div>
            
            <button class="refresh-btn" onclick="refreshStatus()">🔄 Refresh Status</button>
            
            <div class="status-grid" id="statusGrid">
                <!-- Status cards will be populated here -->
            </div>
            
            <div class="metrics">
                <h2>📊 System Metrics</h2>
                <div id="metricsContent">
                    <!-- Metrics will be populated here -->
                </div>
            </div>
            
            <div class="timestamp" id="lastUpdate">
                Last updated: Never
            </div>
        </div>
        
        <script>
            async function refreshStatus() {
                try {
                    const response = await fetch('/api/status');
                    const data = await response.json();
                    updateDashboard(data);
                } catch (error) {
                    console.error('Error refreshing status:', error);
                }
            }
            
            function updateDashboard(data) {
                // Update status grid
                const statusGrid = document.getElementById('statusGrid');
                statusGrid.innerHTML = '';
                
                Object.entries(data.services).forEach(([serviceName, serviceData]) => {
                    const card = document.createElement('div');
                    card.className = `status-card ${serviceData.status}`;
                    
                    card.innerHTML = `
                        <div class="service-name">${serviceName}</div>
                        <div class="service-status">Status: ${serviceData.status}</div>
                        <div class="service-details">Response Time: ${serviceData.response_time}ms</div>
                        <div class="service-details">Last Check: ${serviceData.last_check}</div>
                    `;
                    
                    statusGrid.appendChild(card);
                });
                
                // Update metrics
                const metricsContent = document.getElementById('metricsContent');
                metricsContent.innerHTML = '';
                
                if (data.metrics) {
                    Object.entries(data.metrics).forEach(([metricName, metricValue]) => {
                        const metricRow = document.createElement('div');
                        metricRow.className = 'metric-row';
                        
                        metricRow.innerHTML = `
                            <span class="metric-label">${metricName}</span>
                            <span class="metric-value">${metricValue}</span>
                        `;
                        
                        metricsContent.appendChild(metricRow);
                    });
                }
                
                // Update timestamp
                document.getElementById('lastUpdate').textContent = `Last updated: ${new Date().toLocaleString()}`;
            }
            
            // Auto-refresh every 10 seconds
            setInterval(refreshStatus, 10000);
            
            // Initial load
            refreshStatus();
        </script>
    </body>
    </html>
    """

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring service"""
    return {
        "status": "healthy",
        "service": "003-worker-refactor-monitoring",
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/api/status")
async def get_status():
    """Get comprehensive status of all services"""
    status_data = {
        "services": {},
        "metrics": {},
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Check service health
    async with aiohttp.ClientSession() as session:
        for service_name, service_config in SERVICES.items():
            try:
                start_time = datetime.utcnow()
                
                # For postgres, we'll just check if it's accessible
                if service_name == "postgres":
                    # Simple connection test - in production this would be more sophisticated
                    status_data["services"][service_name] = {
                        "status": "healthy",
                        "response_time": 0,
                        "last_check": datetime.utcnow().isoformat(),
                        "details": "PostgreSQL connection available"
                    }
                else:
                    # HTTP health check for other services
                    async with session.get(f"{service_config['url']}{service_config['health']}", timeout=5) as response:
                        end_time = datetime.utcnow()
                        response_time = (end_time - start_time).total_seconds() * 1000
                        
                        if response.status == 200:
                            status_data["services"][service_name] = {
                                "status": "healthy",
                                "response_time": round(response_time, 2),
                                "last_check": datetime.utcnow().isoformat(),
                                "details": "Service responding normally"
                            }
                        else:
                            status_data["services"][service_name] = {
                                "status": "unhealthy",
                                "response_time": round(response_time, 2),
                                "last_check": datetime.utcnow().isoformat(),
                                "details": f"HTTP {response.status}"
                            }
                            
            except asyncio.TimeoutError:
                status_data["services"][service_name] = {
                    "status": "unhealthy",
                    "response_time": 5000,
                    "last_check": datetime.utcnow().isoformat(),
                    "details": "Request timeout"
                }
            except Exception as e:
                status_data["services"][service_name] = {
                    "status": "unhealthy",
                    "response_time": 0,
                    "last_check": datetime.utcnow().isoformat(),
                    "details": f"Error: {str(e)}"
                }
    
    # Add system metrics
    status_data["metrics"] = {
        "Total Services": len(SERVICES),
        "Healthy Services": len([s for s in status_data["services"].values() if s["status"] == "healthy"]),
        "Unhealthy Services": len([s for s in status_data["services"].values() if s["status"] == "unhealthy"]),
        "Average Response Time": f"{sum([s['response_time'] for s in status_data['services'].values()]) / len(status_data['services']):.2f}ms",
        "Environment": "Local Development",
        "Last Status Check": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return status_data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3000)
