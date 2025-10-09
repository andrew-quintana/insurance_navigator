#!/usr/bin/env python3
"""
FM-038 Phase 1: Comprehensive Chat Flow Investigation Script

This script simulates the complete chat endpoint flow with detailed logging to understand
every step from authentication to response, including all function inputs/outputs.

Date: 2025-01-27
Priority: P0 - Critical Investigation
Status: Phase 1 - Comprehensive Investigation Script

Purpose:
- Authenticate with provided credentials
- Make chat requests to /chat endpoint
- Log every function call with inputs/outputs
- Track complete pipeline from auth to response
- Identify where the zero-chunk issue occurs
- Monitor performance and detect silent failures

Authentication Credentials:
- User: sendaqmail@gmail.com
- Password: xasdez-katjuc-zyttI2
- Test User ID: cae3b3ec-b355-4509-bd4e-0f7da8cb2858
"""

import asyncio
import aiohttp
import json
import logging
import sys
import time
import os
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field
from dotenv import load_dotenv
import traceback

# Load environment variables
load_dotenv('.env.production')

# Configure comprehensive logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)8s] %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'chat_flow_investigation_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

logger = logging.getLogger(__name__)

# Test credentials
TEST_USER_EMAIL = "sendaqmail@gmail.com"
TEST_USER_PASSWORD = "xasdez-katjuc-zyttI2"
TEST_USER_ID = "cae3b3ec-b355-4509-bd4e-0f7da8cb2858"

# API Configuration - Try multiple potential endpoints
API_BASE_URLS = [
    os.getenv("PRODUCTION_API_URL", "").rstrip('/'),
    "https://insurance-navigator-3o99.onrender.com",
    "http://localhost:8000"
]

# Remove empty strings
API_BASE_URLS = [url for url in API_BASE_URLS if url]

@dataclass
class FunctionCall:
    """Track a function call with inputs/outputs"""
    name: str
    start_time: float
    end_time: Optional[float] = None
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Any = None
    error: Optional[str] = None
    duration_ms: Optional[float] = None
    
    def complete(self, outputs: Any = None, error: Optional[str] = None):
        """Mark function call as complete"""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.outputs = outputs
        self.error = error

@dataclass
class InvestigationMetrics:
    """Track metrics for the complete investigation"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    function_calls: List[FunctionCall] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    
    def add_function_call(self, func_call: FunctionCall):
        """Add a function call to tracking"""
        self.function_calls.append(func_call)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get investigation summary"""
        total_duration = time.time() - self.start_time
        return {
            "total_duration_seconds": total_duration,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "function_calls": len(self.function_calls),
            "average_function_duration_ms": sum(fc.duration_ms for fc in self.function_calls if fc.duration_ms) / len(self.function_calls) if self.function_calls else 0
        }

class ChatFlowInvestigator:
    """Comprehensive chat flow investigation orchestrator"""
    
    def __init__(self):
        self.metrics = InvestigationMetrics()
        self.session: Optional[aiohttp.ClientSession] = None
        self.access_token: Optional[str] = None
        self.user_data: Optional[Dict[str, Any]] = None
        self.api_base_url: Optional[str] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        timeout = aiohttp.ClientTimeout(total=120)  # 2 minute timeout
        self.session = aiohttp.ClientSession(timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def log_section(self, title: str):
        """Log a section header"""
        logger.info("=" * 80)
        logger.info(f"  {title}")
        logger.info("=" * 80)
    
    def log_function_input(self, func_name: str, **kwargs):
        """Log function inputs"""
        logger.debug(f"📥 FUNCTION INPUT: {func_name}")
        for key, value in kwargs.items():
            value_str = str(value)
            if len(value_str) > 200:
                value_str = value_str[:200] + "..."
            logger.debug(f"   {key} ({type(value).__name__}): {value_str}")
    
    def log_function_output(self, func_name: str, output: Any, error: Optional[str] = None):
        """Log function outputs"""
        if error:
            logger.error(f"❌ FUNCTION ERROR: {func_name}")
            logger.error(f"   Error: {error}")
        else:
            logger.debug(f"📤 FUNCTION OUTPUT: {func_name}")
            output_str = str(output)
            if len(output_str) > 200:
                output_str = output_str[:200] + "..."
            logger.debug(f"   Output ({type(output).__name__}): {output_str}")
    
    async def find_working_api_endpoint(self) -> Optional[str]:
        """Find a working API endpoint from the list"""
        self.log_section("FINDING WORKING API ENDPOINT")
        
        for base_url in API_BASE_URLS:
            logger.info(f"🔍 Testing endpoint: {base_url}")
            try:
                health_url = f"{base_url}/health"
                async with self.session.get(health_url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        logger.info(f"✅ Found working endpoint: {base_url}")
                        self.api_base_url = base_url
                        return base_url
                    else:
                        logger.warning(f"⚠️  Endpoint responded with status {response.status}")
            except Exception as e:
                logger.warning(f"❌ Endpoint not accessible: {str(e)}")
        
        logger.error("❌ No working API endpoint found!")
        return None
    
    async def authenticate(self) -> bool:
        """
        Step 1: Authentication Flow
        - Login with provided credentials
        - Obtain JWT token
        - Log authentication success/failure
        """
        self.log_section("STEP 1: AUTHENTICATION FLOW")
        
        func_call = FunctionCall(
            name="authenticate",
            start_time=time.time(),
            inputs={
                "email": TEST_USER_EMAIL,
                "password": "***REDACTED***"
            }
        )
        
        try:
            self.log_function_input(
                "POST /login",
                email=TEST_USER_EMAIL,
                password_length=len(TEST_USER_PASSWORD)
            )
            
            login_url = f"{self.api_base_url}/login"
            logger.info(f"🔐 Attempting login at: {login_url}")
            
            payload = {
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
            
            async with self.session.post(login_url, json=payload) as response:
                response_text = await response.text()
                logger.debug(f"Response status: {response.status}")
                logger.debug(f"Response headers: {dict(response.headers)}")
                logger.debug(f"Response body: {response_text[:500]}")
                
                if response.status == 200:
                    auth_data = json.loads(response_text)
                    self.access_token = auth_data.get("access_token")
                    self.user_data = auth_data.get("user", {})
                    
                    logger.info("✅ Authentication successful!")
                    logger.info(f"   User ID: {self.user_data.get('id')}")
                    logger.info(f"   Email: {self.user_data.get('email')}")
                    logger.info(f"   Token length: {len(self.access_token) if self.access_token else 0}")
                    
                    func_call.complete(outputs={
                        "success": True,
                        "user_id": self.user_data.get('id'),
                        "token_present": bool(self.access_token)
                    })
                    self.metrics.add_function_call(func_call)
                    self.log_function_output("authenticate", {"success": True})
                    return True
                else:
                    error_msg = f"Login failed with status {response.status}: {response_text}"
                    logger.error(f"❌ {error_msg}")
                    func_call.complete(error=error_msg)
                    self.metrics.add_function_call(func_call)
                    self.log_function_output("authenticate", None, error=error_msg)
                    return False
                    
        except Exception as e:
            error_msg = f"Authentication exception: {str(e)}\n{traceback.format_exc()}"
            logger.error(f"❌ {error_msg}")
            func_call.complete(error=error_msg)
            self.metrics.add_function_call(func_call)
            self.log_function_output("authenticate", None, error=error_msg)
            return False
    
    async def send_chat_message(self, message: str, conversation_id: str = "") -> Optional[Dict[str, Any]]:
        """
        Step 2: Chat Request Flow
        - Make POST request to /chat endpoint
        - Include proper headers (Authorization, Content-Type)
        - Log request/response details
        """
        self.log_section(f"STEP 2: CHAT REQUEST - '{message[:50]}...'")
        
        func_call = FunctionCall(
            name="send_chat_message",
            start_time=time.time(),
            inputs={
                "message": message[:200],
                "message_length": len(message),
                "conversation_id": conversation_id,
                "user_id": self.user_data.get('id') if self.user_data else None
            }
        )
        
        try:
            self.log_function_input(
                "POST /chat",
                message=message[:200],
                conversation_id=conversation_id,
                has_token=bool(self.access_token)
            )
            
            chat_url = f"{self.api_base_url}/chat"
            logger.info(f"💬 Sending chat request to: {chat_url}")
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/json"
            }
            
            payload = {
                "message": message,
                "conversation_id": conversation_id,
                "user_language": "en",
                "context": {}
            }
            
            logger.debug(f"Request headers: {headers}")
            logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")
            
            request_start = time.time()
            
            async with self.session.post(chat_url, json=payload, headers=headers) as response:
                request_duration = (time.time() - request_start) * 1000
                
                response_text = await response.text()
                logger.info(f"⏱️  Request duration: {request_duration:.2f}ms")
                logger.debug(f"Response status: {response.status}")
                logger.debug(f"Response headers: {dict(response.headers)}")
                
                if response.status == 200:
                    response_data = json.loads(response_text)
                    logger.info("✅ Chat request successful!")
                    logger.info(f"   Response text length: {len(response_data.get('text', ''))}")
                    logger.debug(f"   Response preview: {response_data.get('text', '')[:200]}...")
                    
                    func_call.complete(outputs={
                        "success": True,
                        "response_length": len(response_data.get('text', '')),
                        "request_duration_ms": request_duration
                    })
                    self.metrics.add_function_call(func_call)
                    self.metrics.successful_requests += 1
                    self.log_function_output("send_chat_message", response_data)
                    return response_data
                else:
                    error_msg = f"Chat request failed with status {response.status}: {response_text}"
                    logger.error(f"❌ {error_msg}")
                    func_call.complete(error=error_msg)
                    self.metrics.add_function_call(func_call)
                    self.metrics.failed_requests += 1
                    self.log_function_output("send_chat_message", None, error=error_msg)
                    return None
                    
        except Exception as e:
            error_msg = f"Chat request exception: {str(e)}\n{traceback.format_exc()}"
            logger.error(f"❌ {error_msg}")
            func_call.complete(error=error_msg)
            self.metrics.add_function_call(func_call)
            self.metrics.failed_requests += 1
            self.log_function_output("send_chat_message", None, error=error_msg)
            return None
    
    async def analyze_production_logs(self):
        """
        Step 3: Production Log Analysis
        - Connect to production logs if possible
        - Look for RAG operation logs
        - Identify any errors or warnings
        """
        self.log_section("STEP 3: PRODUCTION LOG ANALYSIS")
        
        logger.info("📊 Production log analysis would require direct server access")
        logger.info("   For complete analysis, check Render dashboard logs:")
        logger.info(f"   - Service: srv-d0v2nqvdiees73cejf0g")
        logger.info(f"   - Look for: 'RAG Operation Started' and 'RAG Operation SUCCESS/FAILED'")
        logger.info(f"   - Look for: CHECKPOINT logs (A-H)")
        logger.info(f"   - Look for: PRE-EMBEDDING and POST-EMBEDDING logs")
    
    def print_investigation_summary(self):
        """Print comprehensive investigation summary"""
        self.log_section("INVESTIGATION SUMMARY")
        
        summary = self.metrics.get_summary()
        
        logger.info("📊 Overall Metrics:")
        logger.info(f"   Total Duration: {summary['total_duration_seconds']:.2f}s")
        logger.info(f"   Total Requests: {summary['total_requests']}")
        logger.info(f"   Successful: {summary['successful_requests']}")
        logger.info(f"   Failed: {summary['failed_requests']}")
        logger.info(f"   Function Calls: {summary['function_calls']}")
        logger.info(f"   Avg Function Duration: {summary['average_function_duration_ms']:.2f}ms")
        
        logger.info("\n📋 Function Call Timeline:")
        for i, func_call in enumerate(self.metrics.function_calls, 1):
            status = "✅" if not func_call.error else "❌"
            duration = f"{func_call.duration_ms:.2f}ms" if func_call.duration_ms else "N/A"
            logger.info(f"   {i}. {status} {func_call.name} - {duration}")
            if func_call.error:
                logger.info(f"      Error: {func_call.error[:100]}...")
        
        logger.info("\n🔍 Key Observations:")
        if summary['failed_requests'] > 0:
            logger.warning(f"   ⚠️  {summary['failed_requests']} request(s) failed")
        if summary['successful_requests'] > 0:
            logger.info(f"   ✅ {summary['successful_requests']} request(s) succeeded")
        
        # Check for specific issues
        auth_calls = [fc for fc in self.metrics.function_calls if fc.name == "authenticate"]
        if auth_calls and auth_calls[0].error:
            logger.error("   ❌ Authentication failed - cannot proceed with chat tests")
        
        chat_calls = [fc for fc in self.metrics.function_calls if fc.name == "send_chat_message"]
        if chat_calls:
            successful_chats = [fc for fc in chat_calls if not fc.error]
            if successful_chats:
                logger.info(f"   ✅ {len(successful_chats)} chat request(s) completed successfully")
                logger.info("   📝 Check production logs for RAG operation details:")
                logger.info("      - Search for 'RAG Operation Started' logs")
                logger.info("      - Look for 'Chunks:X/Y' in operation logs")
                logger.info("      - Check for CHECKPOINT logs (A-H)")
                logger.info("      - Look for embedding generation logs")
    
    async def run_comprehensive_investigation(self):
        """Run the complete investigation flow"""
        self.log_section("STARTING COMPREHENSIVE CHAT FLOW INVESTIGATION")
        logger.info(f"Investigation started at: {datetime.now().isoformat()}")
        logger.info(f"Test user: {TEST_USER_EMAIL}")
        logger.info(f"Test user ID: {TEST_USER_ID}")
        
        try:
            # Step 0: Find working API endpoint
            if not await self.find_working_api_endpoint():
                logger.error("❌ Cannot proceed without a working API endpoint")
                # Save report even on early exit
                await self.save_investigation_report()
                return
            
            # Step 1: Authenticate
            if not await self.authenticate():
                logger.error("❌ Authentication failed - cannot proceed")
                # Save report even on early exit
                await self.save_investigation_report()
                return
            
            # Wait a moment after authentication
            await asyncio.sleep(1)
            
            # Step 2: Send test chat messages
            test_messages = [
                "What mental health services are covered under my insurance plan?",
                "Does my policy cover ambulance services?",
                "What are the copay requirements for primary care visits?"
            ]
            
            for i, message in enumerate(test_messages, 1):
                logger.info(f"\n{'='*80}")
                logger.info(f"TEST MESSAGE {i}/{len(test_messages)}")
                logger.info(f"{'='*80}")
                
                self.metrics.total_requests += 1
                response = await self.send_chat_message(message)
                
                if response:
                    logger.info(f"✅ Message {i} processed successfully")
                else:
                    logger.error(f"❌ Message {i} failed")
                
                # Wait between requests
                if i < len(test_messages):
                    logger.info("⏳ Waiting 5 seconds before next request...")
                    await asyncio.sleep(5)
            
            # Step 3: Analyze production logs (informational)
            await self.analyze_production_logs()
            
            # Step 4: Print summary
            self.print_investigation_summary()
            
            # Save detailed report
            await self.save_investigation_report()
            
        except Exception as e:
            logger.error(f"❌ Investigation failed with exception: {str(e)}")
            logger.error(traceback.format_exc())
            # Save report even on exception
            try:
                await self.save_investigation_report()
            except:
                pass  # Don't fail if report save fails
    
    async def save_investigation_report(self):
        """Save detailed investigation report to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"chat_flow_investigation_report_{timestamp}.json"
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "test_user": TEST_USER_EMAIL,
            "test_user_id": TEST_USER_ID,
            "api_base_url": self.api_base_url,
            "metrics": self.metrics.get_summary(),
            "function_calls": [
                {
                    "name": fc.name,
                    "duration_ms": fc.duration_ms,
                    "inputs": fc.inputs,
                    "outputs": str(fc.outputs)[:500] if fc.outputs else None,
                    "error": fc.error
                }
                for fc in self.metrics.function_calls
            ]
        }
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"📄 Investigation report saved to: {report_file}")

async def main():
    """Main entry point"""
    logger.info("=" * 80)
    logger.info("FM-038 Phase 1: Comprehensive Chat Flow Investigation")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Purpose: Investigate complete chat flow from auth to response")
    logger.info("Focus: Function inputs/outputs, RAG operations, error detection")
    logger.info("")
    
    async with ChatFlowInvestigator() as investigator:
        await investigator.run_comprehensive_investigation()
    
    logger.info("")
    logger.info("=" * 80)
    logger.info("Investigation Complete")
    logger.info("=" * 80)
    logger.info("")
    logger.info("Next Steps:")
    logger.info("1. Review the investigation report JSON file")
    logger.info("2. Check production logs in Render dashboard")
    logger.info("3. Look for RAG operation logs and CHECKPOINT entries")
    logger.info("4. Proceed to Phase 2: Interactive Debugging Notebook")
    logger.info("")

if __name__ == "__main__":
    asyncio.run(main())

