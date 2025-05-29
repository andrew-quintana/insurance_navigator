#!/bin/bash

# Insurance Navigator - Debug Workflow Script
# Automatically handles authentication and displays detailed debug output

set -e  # Exit on any error

# Load environment variables from .env if it exists
if [ -f .env ]; then
    echo "📁 Loading environment from .env file..."
    export $(grep -v '^#' .env | xargs)
fi

# Configuration
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

echo -e "${BLUE}🔍 Insurance Navigator Debug Workflow${NC}"
echo -e "${BLUE}=====================================${NC}"
echo ""

# Function to get a fresh token
get_token() {
    echo -e "${YELLOW}🔑 Getting fresh authentication token...${NC}"
    echo -e "${CYAN}   → API URL: $API_BASE_URL/login${NC}"
    echo -e "${CYAN}   → Email: $DEBUG_USER_EMAIL${NC}"
    
    local response=$(curl -s -X POST "$API_BASE_URL/login" \
        -H "Content-Type: application/json" \
        -d "{\"email\": \"$DEBUG_USER_EMAIL\", \"password\": \"$DEBUG_USER_PASSWORD\"}" 2>/dev/null)
    
    # Check if we got a response
    if [ -z "$response" ]; then
        echo -e "${RED}❌ No response from login endpoint${NC}"
        exit 1
    fi
    
    # Check if login was successful
    local token=$(echo "$response" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(data.get('access_token', ''))
except:
    print('')
" 2>/dev/null)
    
    if [ -n "$token" ] && [ "$token" != "" ]; then
        echo -e "${GREEN}✅ Token obtained successfully${NC}"
        echo -e "${CYAN}   → Token length: ${#token} characters${NC}"
        echo "$token"
    else
        echo -e "${RED}❌ Failed to get token. Response:${NC}"
        echo "$response"
        exit 1
    fi
}

# Function to display detailed debug output
show_detailed_debug() {
    local token="$1"
    echo ""
    echo -e "${YELLOW}📊 Fetching latest workflow debug information...${NC}"
    echo -e "${CYAN}   → API URL: $API_BASE_URL/debug/latest-workflow${NC}"
    echo ""
    
    # Get the raw JSON first to parse and display detailed info
    local debug_response=$(curl -s -X GET "$API_BASE_URL/debug/latest-workflow" \
        -H "Authorization: Bearer $token" 2>/dev/null)
    
    if [ -z "$debug_response" ]; then
        echo -e "${RED}❌ No response from debug endpoint${NC}"
        exit 1
    fi
    
    # Check if we got valid JSON
    if ! echo "$debug_response" | python3 -c "import sys, json; json.load(sys.stdin)" 2>/dev/null; then
        echo -e "${RED}❌ Invalid JSON response:${NC}"
        echo "$debug_response"
        exit 1
    fi
    
    # Parse and display workflow summary
    echo -e "${MAGENTA}🔄 WORKFLOW EXECUTION SUMMARY${NC}"
    echo -e "${MAGENTA}=============================${NC}"
    
    local conversation_id=$(echo "$debug_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('conversation_id', 'N/A'))")
    local total_messages=$(echo "$debug_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('debug_info', {}).get('total_messages', 0))")
    local agents_executed=$(echo "$debug_response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('debug_info', {}).get('agents_executed', 0))")
    
    echo -e "📋 Conversation ID: ${CYAN}$conversation_id${NC}"
    echo -e "💬 Total Messages: ${CYAN}$total_messages${NC}"
    echo -e "🤖 Agents Executed: ${CYAN}$agents_executed${NC}"
    echo ""
    
    # Display workflow state information
    echo -e "${MAGENTA}📊 WORKFLOW STATE DETAILS${NC}"
    echo -e "${MAGENTA}=========================${NC}"
    
    echo "$debug_response" | python3 << 'EOF'
import json
import sys

data = json.load(sys.stdin)
workflow_states = data.get('workflow_states', {})

if workflow_states and 'state_data' in workflow_states:
    state_data = workflow_states['state_data']
    
    print(f"📋 Workflow Type: {workflow_states.get('workflow_type', 'N/A')}")
    print(f"🔄 Current Step: {workflow_states.get('current_step', 'N/A')}")
    print(f"🎯 Intent: {state_data.get('intent', 'N/A')}")
    print(f"🛡️ Security Check: {'✅ Passed' if state_data.get('security_check_passed') else '❌ Failed'}")
    
    error = state_data.get('error')
    if error:
        print(f"⚠️ Error: {error}")
    
    # Strategy results
    strategy_result = state_data.get('strategy_result')
    if strategy_result:
        print(f"\n🎯 STRATEGY SUMMARY:")
        print(f"   Service: {strategy_result.get('recommended_service', 'N/A')}")
        print(f"   Timeline: {strategy_result.get('estimated_timeline', 'N/A')}")
        print(f"   Confidence: {strategy_result.get('confidence', 'N/A')}")
        
        action_plan = strategy_result.get('action_plan', [])
        if action_plan:
            print(f"   Action Steps: {len(action_plan)} steps defined")
else:
    print("No workflow state data available")

print()
EOF
    
    # Display agent-by-agent execution details
    echo -e "${MAGENTA}🤖 DETAILED AGENT EXECUTION${NC}"
    echo -e "${MAGENTA}============================${NC}"
    
    # Use Python to parse and display agent states
    echo "$debug_response" | python3 << 'EOF'
import json
import sys
from datetime import datetime

data = json.load(sys.stdin)
agent_states = data.get('agent_states', [])

if not agent_states:
    print("❌ No agent execution data found")
    sys.exit(0)

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
            # Parse and format timestamp
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
            threat_level = result.get('threat_level', 'unknown')
            print(f"   🔒 Security Status: {'✅ PASSED' if passed else '❌ FAILED'}")
            print(f"   ⚠️  Threat Level: {threat_level.upper()}")
            
        elif agent_name == 'patient_navigator':
            intent = result.get('intent_type', 'N/A')
            confidence = result.get('confidence_score', 'N/A')
            analysis = result.get('analysis_details', {})
            print(f"   🎯 Intent Detected: {intent.upper()}")
            print(f"   📊 Confidence Score: {confidence}")
            if analysis:
                print(f"   📝 Analysis Details: {str(analysis)[:100]}...")
        
        elif agent_name == 'task_requirements':
            requirements = result.get('requirements', [])
            priority = result.get('priority_level', 'N/A')
            print(f"   📋 Priority Level: {priority.upper()}")
            if requirements:
                print(f"   📝 Requirements Found: {len(requirements)}")
                for j, req in enumerate(requirements[:3], 1):  # Show first 3
                    print(f"      {j}. {req}")
                if len(requirements) > 3:
                    print(f"      ... and {len(requirements) - 3} more requirements")
        
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
                for step_info in action_plan[:3]:  # Show first 3 steps
                    step_num = step_info.get('step_number', '?')
                    step_desc = step_info.get('step_description', 'N/A')
                    step_timeline = step_info.get('expected_timeline', 'N/A')
                    print(f"      Step {step_num}: {step_desc}")
                    print(f"         ⏱ Timeline: {step_timeline}")
                if len(action_plan) > 3:
                    print(f"      ... and {len(action_plan) - 3} more action steps")
            
            matched_services = result.get('matched_services', [])
            if matched_services:
                print(f"   🔍 Service Matches: {len(matched_services)} found")
                for service_info in matched_services[:3]:  # Show first 3
                    service_name = service_info.get('service_name', 'N/A')
                    is_covered = service_info.get('is_covered', False)
                    coverage_icon = "✅ COVERED" if is_covered else "❌ NOT COVERED"
                    print(f"      {coverage_icon} {service_name}")
        
        elif agent_name == 'regulatory':
            compliance_status = result.get('compliance_status', 'N/A')
            regulations = result.get('applicable_regulations', [])
            print(f"   ⚖️  Compliance Status: {compliance_status.upper()}")
            if regulations:
                print(f"   📜 Applicable Regulations: {len(regulations)}")
                for reg in regulations[:2]:  # Show first 2
                    print(f"      • {reg}")
                if len(regulations) > 2:
                    print(f"      • ... and {len(regulations) - 2} more regulations")
        
        elif agent_name == 'chat_communicator':
            response_type = result.get('response_type', 'N/A')
            tone = result.get('tone', 'N/A')
            print(f"   💬 Response Type: {response_type.upper()}")
            print(f"   🎭 Communication Tone: {tone.upper()}")
    
    # Error information
    error = state_data.get('error')
    if error:
        print(f"   ❌ Error Encountered: {error}")
    
    # Processing time
    processing_time = state_data.get('processing_time_seconds')
    if processing_time:
        print(f"   ⏱️  Processing Time: {processing_time:.2f} seconds")

print(f"\n{'='*60}")
print("✅ Detailed agent execution analysis complete!")
EOF

    echo ""
    echo -e "${GREEN}✅ Detailed workflow analysis complete!${NC}"
}

# Function to show readable debug output
show_readable_debug() {
    local token="$1"
    echo ""
    echo -e "${YELLOW}📖 HUMAN-READABLE SUMMARY REPORT${NC}"
    echo -e "${YELLOW}=================================${NC}"
    echo ""
    
    curl -s -X GET "$API_BASE_URL/debug/latest-workflow/readable" \
        -H "Authorization: Bearer $token" 2>/dev/null || {
        echo -e "${RED}❌ Failed to fetch readable debug information${NC}"
        exit 1
    }
}

# Main execution
main() {
    # Check if python3 is available
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ python3 is required but not installed.${NC}"
        exit 1
    fi
    
    # Get token
    TOKEN=$(get_token)
    
    # Show detailed debug breakdown
    show_detailed_debug "$TOKEN"
    
    # Show readable summary
    if [[ "$1" == "--readable" ]] || [[ "$1" == "" ]]; then
        show_readable_debug "$TOKEN"
    fi
    
    echo ""
    echo -e "${GREEN}🎉 Debug workflow completed successfully!${NC}"
    echo -e "${CYAN}💡 Use this data to understand how your agents are performing${NC}"
}

# Help function
show_help() {
    echo "Usage: $0 [--readable] [--help]"
    echo ""
    echo "Options:"
    echo "  --readable   Show both detailed breakdown and readable summary (default)"
    echo "  --help       Show this help message"
    echo ""
    echo "Environment variables:"
    echo "  API_BASE_URL         Base URL for the API (default: http://localhost:8000)"
    echo "  DEBUG_USER_EMAIL     Email for authentication (default: testuser@example.com)"
    echo "  DEBUG_USER_PASSWORD  Password for authentication (default: Password123!)"
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        show_help
        exit 0
        ;;
    --readable|"")
        main --readable
        ;;
    *)
        echo -e "${RED}❌ Unknown option: $1${NC}"
        show_help
        exit 1
        ;;
esac 