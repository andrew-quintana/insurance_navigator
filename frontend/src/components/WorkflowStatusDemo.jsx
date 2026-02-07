/**
 * WorkflowStatusDemo Component
 * 
 * Demo and integration example for the WorkflowStatus component
 * Shows how to integrate with the main chat interface.
 */

import React, { useState, useCallback } from 'react';
import WorkflowStatus from './WorkflowStatus';

const WorkflowStatusDemo = () => {
  const [workflowId, setWorkflowId] = useState(null);
  const [userId] = useState('demo-user-123');
  const [isProcessing, setIsProcessing] = useState(false);
  const [response, setResponse] = useState('');
  const [query, setQuery] = useState('');

  // Simulate starting a workflow
  const startWorkflow = useCallback(async () => {
    if (!query.trim()) return;

    const newWorkflowId = `workflow-${Date.now()}`;
    setWorkflowId(newWorkflowId);
    setIsProcessing(true);
    setResponse('');

    // In a real app, this would trigger the actual API call
    console.log(`Starting workflow ${newWorkflowId} for query: ${query}`);
  }, [query]);

  // Handle workflow completion
  const handleWorkflowComplete = useCallback((finalResponse, success) => {
    setIsProcessing(false);
    if (success) {
      setResponse(finalResponse);
    }
  }, []);

  // Handle workflow errors
  const handleWorkflowError = useCallback((error) => {
    setIsProcessing(false);
    console.error('Workflow error:', error);
  }, []);

  return (
    <div className="workflow-demo">
      <div className="demo-header">
        <h2>AI Workflow Visualization Demo</h2>
        <p>Experience real-time workflow processing with visual feedback</p>
      </div>

      {/* Query Input */}
      <div className="query-section">
        <div className="input-group">
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask me about your insurance coverage..."
            className="query-input"
            rows={3}
            disabled={isProcessing}
          />
          <button 
            onClick={startWorkflow}
            disabled={isProcessing || !query.trim()}
            className="start-button"
          >
            {isProcessing ? 'Processing...' : 'Start Analysis'}
          </button>
        </div>
      </div>

      {/* Workflow Status Visualization */}
      {workflowId && (
        <WorkflowStatus
          workflowId={workflowId}
          userId={userId}
          onComplete={handleWorkflowComplete}
          onError={handleWorkflowError}
          showSteps={true}
          showProgress={true}
        />
      )}

      {/* Response Display */}
      {response && (
        <div className="response-section">
          <div className="response-header">
            <h3>Analysis Complete</h3>
          </div>
          <div className="response-content">
            {response}
          </div>
        </div>
      )}

      {/* Integration Instructions */}
      <div className="integration-guide">
        <h3>Integration Guide</h3>
        <div className="code-example">
          <h4>1. Import the component:</h4>
          <pre>{`import WorkflowStatus from './components/WorkflowStatus';`}</pre>
          
          <h4>2. Use in your chat interface:</h4>
          <pre>{`<WorkflowStatus
  workflowId={workflowId}
  userId={userId}
  onComplete={(response, success) => {
    // Handle completion
    setFinalResponse(response);
  }}
  onError={(error) => {
    // Handle errors
    console.error('Workflow failed:', error);
  }}
  showSteps={true}
  showProgress={true}
/>`}</pre>

          <h4>3. Backend integration:</h4>
          <pre>{`# Add to your FastAPI app
from api.websocket_routes import router as ws_router
app.include_router(ws_router)

# In your workflow execution
from agents.unified_navigator.websocket_handler import get_workflow_broadcaster
broadcaster = get_workflow_broadcaster()
await broadcaster.broadcast_status(workflow_id, status)`}</pre>
        </div>
      </div>

      <style jsx>{`
        .workflow-demo {
          max-width: 800px;
          margin: 0 auto;
          padding: 20px;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', roboto, sans-serif;
        }

        .demo-header {
          text-align: center;
          margin-bottom: 30px;
        }

        .demo-header h2 {
          color: #1f2937;
          margin-bottom: 8px;
        }

        .demo-header p {
          color: #6b7280;
        }

        .query-section {
          margin-bottom: 20px;
        }

        .input-group {
          display: flex;
          gap: 12px;
          align-items: flex-end;
        }

        .query-input {
          flex: 1;
          padding: 12px;
          border: 2px solid #e5e7eb;
          border-radius: 8px;
          font-size: 14px;
          resize: vertical;
          font-family: inherit;
        }

        .query-input:focus {
          outline: none;
          border-color: #3b82f6;
        }

        .query-input:disabled {
          background-color: #f9fafb;
          cursor: not-allowed;
        }

        .start-button {
          padding: 12px 24px;
          background: #3b82f6;
          color: white;
          border: none;
          border-radius: 8px;
          font-weight: 600;
          cursor: pointer;
          transition: background 0.2s;
        }

        .start-button:hover:not(:disabled) {
          background: #1d4ed8;
        }

        .start-button:disabled {
          background: #9ca3af;
          cursor: not-allowed;
        }

        .response-section {
          margin-top: 20px;
          padding: 20px;
          background: #f0f9ff;
          border-radius: 8px;
          border: 1px solid #0ea5e9;
        }

        .response-header h3 {
          margin: 0 0 12px 0;
          color: #0c4a6e;
        }

        .response-content {
          color: #1e293b;
          line-height: 1.6;
          white-space: pre-wrap;
        }

        .integration-guide {
          margin-top: 40px;
          padding: 20px;
          background: #f8fafc;
          border-radius: 8px;
          border: 1px solid #e2e8f0;
        }

        .integration-guide h3 {
          margin-top: 0;
          color: #1f2937;
        }

        .code-example h4 {
          margin: 20px 0 8px 0;
          color: #374151;
          font-size: 14px;
        }

        .code-example pre {
          background: #1f2937;
          color: #e5e7eb;
          padding: 12px;
          border-radius: 6px;
          font-size: 12px;
          overflow-x: auto;
          margin: 8px 0;
        }

        @media (max-width: 768px) {
          .workflow-demo {
            padding: 16px;
          }

          .input-group {
            flex-direction: column;
          }

          .query-input {
            margin-bottom: 12px;
          }
        }
      `}</style>
    </div>
  );
};

export default WorkflowStatusDemo;