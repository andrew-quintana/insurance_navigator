# AI Workflow Visualization Integration Guide

This guide explains how to integrate the real-time AI workflow visualization system with your insurance navigator application.

## Overview

The system provides:
- **Two Tool Modes**: Quick info retrieval (<500ms) and comprehensive access strategizing
- **Real-time Status Updates**: WebSocket/SSE-based workflow visualization
- **Comprehensive Logging**: Full observability with structured JSON logging
- **Frontend Components**: Ready-to-use React components for workflow visualization

## Backend Integration

### 1. Include WebSocket Routes

Add the WebSocket routes to your FastAPI application:

```python
# In your main.py or app.py
from api.websocket_routes import router as websocket_router

app = FastAPI()
app.include_router(websocket_router)
```

### 2. Use the Unified Navigator

Replace your existing agent calls with the unified navigator:

```python
from agents.unified_navigator.navigator_agent import UnifiedNavigatorAgent
from agents.unified_navigator.models import UnifiedNavigatorInput

# Initialize agent (auto-detects Claude API)
agent = UnifiedNavigatorAgent(use_mock=False)

# Execute with real-time logging
async def process_query(user_query: str, user_id: str):
    input_data = UnifiedNavigatorInput(
        user_query=user_query,
        user_id=user_id,
        session_id=request.session.get('session_id')
    )
    
    result = await agent.execute(input_data)
    return result
```

### 3. Environment Variables

Ensure these environment variables are set:

```bash
# Required for Claude API
ANTHROPIC_API_KEY=your_claude_api_key
ANTHROPIC_MODEL=claude-3-5-sonnet-20241022

# Optional for Tavily research (access strategy tool)
TAVILY_API_KEY=your_tavily_api_key

# Optional for web search
BRAVE_API_KEY=your_brave_search_api_key
```

## Frontend Integration

### 1. Import Components

```jsx
import WorkflowStatus from './components/WorkflowStatus';
import { useWorkflowStatus } from './hooks/useWorkflowStatus';
```

### 2. Basic Usage

```jsx
function ChatInterface() {
  const [workflowId, setWorkflowId] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [response, setResponse] = useState('');

  // Start workflow
  const handleSubmit = async (query) => {
    const newWorkflowId = `workflow-${Date.now()}`;
    setWorkflowId(newWorkflowId);
    setIsProcessing(true);

    try {
      // Call your API endpoint
      const result = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          query, 
          user_id: 'user123',
          workflow_id: newWorkflowId 
        })
      });
      
      const data = await result.json();
      // Response handling will be done via WebSocket
    } catch (error) {
      console.error('API call failed:', error);
      setIsProcessing(false);
    }
  };

  // Handle workflow completion
  const handleComplete = (finalResponse, success) => {
    setIsProcessing(false);
    if (success) {
      setResponse(finalResponse);
    }
  };

  return (
    <div>
      {/* Your existing chat UI */}
      
      {/* Workflow visualization */}
      {workflowId && (
        <WorkflowStatus
          workflowId={workflowId}
          userId="user123"
          onComplete={handleComplete}
          showSteps={true}
          showProgress={true}
        />
      )}
      
      {/* Response display */}
      {response && (
        <div className="response">{response}</div>
      )}
    </div>
  );
}
```

### 3. Advanced Usage with Hook

```jsx
function AdvancedChatInterface() {
  const [workflowId, setWorkflowId] = useState(null);
  
  const {
    status,
    isConnected,
    error,
    progress,
    currentStep,
    isProcessing,
    isCompleted
  } = useWorkflowStatus(workflowId, 'user123', {
    onStatusUpdate: (status) => {
      console.log('Status update:', status);
    },
    onComplete: (response, success) => {
      console.log('Workflow completed:', { response, success });
    },
    onError: (error) => {
      console.error('Workflow error:', error);
    }
  });

  return (
    <div>
      {/* Connection indicator */}
      <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
        {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
      </div>

      {/* Current status */}
      {status && (
        <div className="current-status">
          <div>{status.message}</div>
          <div>Progress: {Math.round(progress)}%</div>
        </div>
      )}

      {/* Error handling */}
      {error && (
        <div className="error">Error: {error}</div>
      )}
    </div>
  );
}
```

## Tool Selection Logic

The system automatically selects the optimal tool based on query analysis:

### Quick Info Tool
- **Triggers**: Specific policy questions ("what does my plan cover", "copay amount")
- **Speed**: <500ms response time
- **Technology**: BM25/TF-IDF document scoring + Claude SDK Read

### Access Strategy Tool
- **Triggers**: Strategic questions ("how to maximize benefits", "best approach")
- **Features**: Tavily research + RAG validation
- **Use Case**: Complex scenarios requiring external research

### Web Search Tool
- **Triggers**: Current events ("latest regulations", "2024 updates")
- **Technology**: Brave Search API

### RAG Search Tool
- **Triggers**: General document queries
- **Technology**: Traditional RAG with user's documents

## Workflow Status Steps

The frontend will display these workflow steps:

1. **sanitizing** (🔒) - Input validation and sanitization
2. **determining** (🤔) - Tool selection and query analysis  
3. **thinking** (🧠) - Information processing and analysis
4. **skimming** (⚡) - Quick policy lookup (Quick Info tool only)
5. **wording** (✍️) - Response generation and finalization

## Logging and Observability

All workflow events are logged as structured JSON:

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "type": "workflow_step",
  "data": {
    "step": "thinking",
    "message": "Searching your policy documents",
    "correlation_id": "wf-abc123"
  }
}
```

### Key Log Events:
- `workflow_start` - Workflow initialization
- `workflow_step` - Step transitions  
- `tool_execution` - Tool usage and results
- `llm_interaction` - API calls with token usage
- `workflow_completion` - Final results and metrics

## Testing

### Mock Mode
For development and testing without API costs:

```python
# Initialize in mock mode
agent = UnifiedNavigatorAgent(use_mock=True)
```

### WebSocket Testing
Test WebSocket connections:

```bash
curl -X POST http://localhost:8000/api/workflow/test-123/broadcast/test \
  -d "step=testing&message=Test message"
```

## Performance Considerations

- **Quick Info Tool**: Optimized for <500ms responses
- **WebSocket Keepalive**: Automatic connection management
- **Caching**: Built-in result caching for repeated queries  
- **Rate Limiting**: Anthropic API rate limiting included
- **Reconnection**: Automatic WebSocket reconnection with exponential backoff

## Error Handling

The system includes comprehensive error handling:

- **WebSocket Reconnection**: Automatic retry with configurable attempts
- **Graceful Degradation**: Fallback to alternative tools on failure  
- **Error Broadcasting**: Real-time error notifications to frontend
- **Logging**: All errors captured in structured logs

## Security Considerations

- **Input Sanitization**: All user inputs validated and sanitized
- **Output Filtering**: Response content filtered for sensitive information
- **API Key Protection**: Environment-based API key management
- **WebSocket Authentication**: User-based connection authorization

## Deployment

1. **Environment Setup**: Configure all required API keys
2. **WebSocket Support**: Ensure your deployment supports WebSocket connections
3. **Logging Configuration**: Set up log aggregation for observability
4. **Health Checks**: Monitor WebSocket connection health
5. **Scaling**: WebSocket connections are stateful - consider sticky sessions

For questions or issues, refer to the implementation files or create an issue in the repository.