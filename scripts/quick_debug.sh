#!/bin/bash

# Quick Debug Script - Insurance Navigator
# Shows detailed agent execution and workflow data

set -e

# Load environment variables from .env if it exists
if [ -f .env ]; then
    echo "📁 Loading environment from .env file..."
    export $(grep -v '^#' .env | xargs)
fi

# Set defaults if not provided
API_BASE_URL="${API_BASE_URL:-http://localhost:8000}"
DEBUG_USER_EMAIL="${DEBUG_USER_EMAIL:-testuser@example.com}"
DEBUG_USER_PASSWORD="${DEBUG_USER_PASSWORD:-Password123!}"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 INSURANCE NAVIGATOR - AGENT DEBUG ANALYSIS${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

echo -e "${YELLOW}🔑 Getting authentication token...${NC}"

# Get token
TOKEN=$(curl -s -X POST "$API_BASE_URL/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"$DEBUG_USER_EMAIL\", \"password\": \"$DEBUG_USER_PASSWORD\"}" | \
    python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo -e "${RED}❌ Failed to get token. Check your credentials.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Token obtained!${NC}"
echo ""

echo -e "${YELLOW}📊 Fetching detailed workflow debug information...${NC}"
echo ""

# Get debug JSON data
DEBUG_DATA=$(curl -s -X GET "$API_BASE_URL/debug/latest-workflow" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Accept: application/json")

if [ -z "$DEBUG_DATA" ]; then
    echo -e "${RED}❌ No debug data received${NC}"
    exit 1
fi

# Parse and display the data with Python
echo "$DEBUG_DATA" | python3 << 'EOF'
import json
import sys
from datetime import datetime

try:
    data = json.load(sys.stdin)
except:
    print("❌ Invalid JSON data received")
    sys.exit(1)

# Colors
GREEN = '\033[0;32m'
BLUE = '\033[0;34m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
CYAN = '\033[0;36m'
MAGENTA = '\033[0;35m'
NC = '\033[0m'

print(f"{MAGENTA}🔄 WORKFLOW EXECUTION SUMMARY{NC}")
print(f"{MAGENTA}============================{NC}")

conversation_id = data.get('conversation_id', 'N/A')
total_messages = data.get('debug_info', {}).get('total_messages', 0)
agents_executed = data.get('debug_info', {}).get('agents_executed', 0)

print(f"📋 Conversation ID: {CYAN}{conversation_id}{NC}")
print(f"💬 Total Messages: {CYAN}{total_messages}{NC}")
print(f"🤖 Agents Executed: {CYAN}{agents_executed}{NC}")
print()

# Show workflow state
workflow_states = data.get('workflow_states', {})
if workflow_states:
    state_data = workflow_states.get('state_data', {})
    print(f"{MAGENTA}📊 WORKFLOW STATE{NC}")
    print(f"{MAGENTA}================={NC}")
    print(f"📋 Workflow Type: {workflow_states.get('workflow_type', 'N/A')}")
    print(f"🔄 Current Step: {workflow_states.get('current_step', 'N/A')}")
    print(f"🎯 Intent: {state_data.get('intent', 'N/A')}")
    print(f"🛡️ Security Check: {'✅ Passed' if state_data.get('security_check_passed') else '❌ Failed'}")
    
    strategy_result = state_data.get('strategy_result')
    if strategy_result:
        print(f"\n🎯 STRATEGY RESULTS:")
        print(f"   Service: {strategy_result.get('recommended_service', 'N/A')}")
        print(f"   Timeline: {strategy_result.get('estimated_timeline', 'N/A')}")
        print(f"   Confidence: {strategy_result.get('confidence', 'N/A')}")
        
        action_plan = strategy_result.get('action_plan', [])
        if action_plan:
            print(f"   Action Steps: {len(action_plan)} defined")
    print()

# Show agent execution details
agent_states = data.get('agent_states', [])
if agent_states:
    print(f"{MAGENTA}🤖 DETAILED AGENT EXECUTION{NC}")
    print(f"{MAGENTA}==========================={NC}")
    
    agent_icons = {
        'prompt_security': '🛡️',
        'patient_navigator': '🧭', 
        'task_requirements': '📋',
        'service_access_strategy': '🎯',
        'regulatory': '⚖️',
        'chat_communicator': '💬'
    }
    
    for i, agent in enumerate(agent_states, 1):
        agent_name = agent.get('agent_name', 'Unknown')
        state = agent.get('state', {})
        state_data = state.get('state_data', {})
        
        icon = agent_icons.get(agent_name, '🤖')
        print(f"\n{i}. {icon} {agent_name.upper().replace('_', ' ')}")
        print("   " + "=" * (len(agent_name) + 2))
        
        # Step information
        step = state_data.get('step', 'N/A')
        print(f"   📍 Execution Step: {step}")
        
        # Timestamp
        updated_at = state.get('updated_at', 'N/A')
        if updated_at != 'N/A':
            try:
                dt = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                formatted_time = dt.strftime('%H:%M:%S')
                print(f"   🕒 Completed At: {formatted_time}")
            except:
                print(f"   🕒 Updated: {updated_at}")
        
        # Agent-specific results
        result = state_data.get('result', {})
        if result:
            if agent_name == 'prompt_security':
                passed = result.get('passed', False)
                print(f"   🔒 Security Status: {'✅ PASSED' if passed else '❌ FAILED'}")
                
            elif agent_name == 'patient_navigator':
                intent = result.get('intent_type', 'N/A')
                confidence = result.get('confidence_score', 'N/A')
                print(f"   🎯 Intent Detected: {intent.upper()}")
                print(f"   📊 Confidence Score: {confidence}")
                
                analysis = result.get('analysis_details', {})
                if analysis:
                    meta_intent = analysis.get('meta_intent', {})
                    if meta_intent:
                        print(f"   📝 Request Type: {meta_intent.get('request_type', 'N/A')}")
                        print(f"   🚨 Emergency: {'Yes' if meta_intent.get('emergency', False) else 'No'}")
            
            elif agent_name == 'task_requirements':
                print(f"   📋 Requirements Analysis: Completed")
            
            elif agent_name == 'service_access_strategy':
                service = result.get('recommended_service', 'N/A')
                timeline = result.get('estimated_timeline', 'N/A')
                confidence = result.get('confidence', 'N/A')
                print(f"   🎯 Recommended Service: {service}")
                print(f"   ⏱️  Estimated Timeline: {timeline}")
                print(f"   📊 Strategy Confidence: {confidence}")
                
                action_plan = result.get('action_plan', [])
                if action_plan:
                    print(f"   📋 Action Plan: {len(action_plan)} steps")
                    for step_info in action_plan:
                        step_num = step_info.get('step_number', '?')
                        step_desc = step_info.get('step_description', 'N/A')
                        step_timeline = step_info.get('expected_timeline', 'N/A')
                        print(f"      Step {step_num}: {step_desc}")
                        print(f"         ⏱ Timeline: {step_timeline}")
                        
                        resources = step_info.get('required_resources', [])
                        if resources:
                            print(f"         📋 Resources: {', '.join(resources)}")
                
                matched_services = result.get('matched_services', [])
                if matched_services:
                    print(f"   🔍 Service Matches: {len(matched_services)} found")
                    for service_info in matched_services:
                        service_name = service_info.get('service_name', 'N/A')
                        is_covered = service_info.get('is_covered', False)
                        coverage_icon = "✅ COVERED" if is_covered else "❌ NOT COVERED"
                        print(f"      {coverage_icon} {service_name}")
            
            elif agent_name == 'regulatory':
                print(f"   ⚖️  Compliance Check: Completed")
            
            elif agent_name == 'chat_communicator':
                print(f"   💬 Response Generation: Completed")
        
        # Error information
        error = state_data.get('error')
        if error:
            print(f"   ❌ Error Encountered: {error}")

print(f"\n{MAGENTA}{'='*60}{NC}")
print(f"{GREEN}✅ Detailed agent execution analysis complete!{NC}")
print()
EOF

echo -e "${YELLOW}📖 Getting human-readable summary...${NC}"
echo ""

# Get readable debug output
curl -s -X GET "$API_BASE_URL/debug/latest-workflow/readable" \
    -H "Authorization: Bearer $TOKEN"

echo ""
echo -e "${GREEN}🎉 Debug analysis complete!${NC}"
echo -e "${CYAN}💡 This shows you exactly how each agent processed your request${NC}" 