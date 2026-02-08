/**
 * WorkflowStatus Component
 * 
 * Real-time workflow visualization showing the current status of AI processing
 * with step indicators, progress bar, and status messages.
 */

import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { buildWebSocketUrl } from '../lib/api-config';
import './WorkflowStatus.css';

interface WorkflowStatusProps {
  workflowId: string;
  userId: string;
  onComplete?: (response: string, success: boolean) => void;
  onError?: (error: string) => void;
  showSteps?: boolean;
  showProgress?: boolean;
}

interface WorkflowStatusData {
  step: string;
  message: string;
  progress: number;
  timestamp: Date;
}

interface WebSocketMessage {
  type: string;
  status?: WorkflowStatusData;
  response?: string;
  success?: boolean;
}

const WorkflowStatus: React.FC<WorkflowStatusProps> = ({ 
  workflowId, 
  userId, 
  onComplete = () => {},
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  onError = () => {},
  showSteps = true,
  showProgress = true 
}) => {
  const [status, setStatus] = useState<WorkflowStatusData | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<number>(0);
  const [completedSteps, setCompletedSteps] = useState<Set<string>>(new Set());
  const [currentStep, setCurrentStep] = useState<string | null>(null);

  // Define workflow steps and their display information (memoized to prevent dependency changes)
  const workflowSteps = useMemo(() => [
    {
      key: 'sanitizing',
      label: 'Input Sanitization',
      description: 'Validating and sanitizing input',
      icon: '🔒',
      color: '#3b82f6'
    },
    {
      key: 'determining',
      label: 'Tool Selection',
      description: 'Analyzing query and selecting optimal tool',
      icon: '🤔',
      color: '#8b5cf6'
    },
    {
      key: 'thinking',
      label: 'Processing',
      description: 'Searching information and analyzing',
      icon: '🧠',
      color: '#06b6d4'
    },
    {
      key: 'skimming',
      label: 'Quick Lookup',
      description: 'Performing quick policy lookup',
      icon: '⚡',
      color: '#10b981'
    },
    {
      key: 'wording',
      label: 'Response Generation',
      description: 'Generating personalized response',
      icon: '✍️',
      color: '#f59e0b'
    }
  ], []);

  // Handle incoming WebSocket messages
  const handleWebSocketMessage = useCallback((message: WebSocketMessage) => {
    switch (message.type) {
      case 'connection_confirmed':
        setStatus({
          step: 'connected',
          message: 'Connected to workflow',
          progress: 0,
          timestamp: new Date()
        });
        break;

      case 'workflow_status':
        if (!message.status) break;
        
        const newStatus = {
          step: message.status.step,
          message: message.status.message,
          progress: message.status.progress || 0,
          timestamp: new Date(message.status.timestamp)
        };
        
        setStatus(newStatus);
        setProgress(newStatus.progress * 100);
        setCurrentStep(newStatus.step);
        
        // Mark previous steps as completed
        const stepIndex = workflowSteps.findIndex(s => s.key === newStatus.step);
        if (stepIndex >= 0) {
          setCompletedSteps(prev => {
            const newSet = new Set(prev);
            for (let i = 0; i < stepIndex; i++) {
              newSet.add(workflowSteps[i].key);
            }
            return newSet;
          });
        }
        break;

      case 'workflow_complete':
        setStatus({
          step: 'completed',
          message: 'Workflow completed successfully',
          progress: 1,
          timestamp: new Date()
        });
        
        setProgress(100);
        setCurrentStep('completed');
        
        // Mark all steps as completed
        setCompletedSteps(new Set(workflowSteps.map(s => s.key)));
        
        onComplete(message.response || '', message.success || false);
        break;

      case 'ping':
        // Heartbeat - no action needed
        break;

      default:
        console.log('Unknown message type:', message.type);
    }
  }, [onComplete, workflowSteps]);

  // WebSocket connection management
  const connectWebSocket = useCallback(() => {
    if (!workflowId || !userId) return;

    const wsUrl = buildWebSocketUrl(`/ws/workflow/${workflowId}`, { user_id: userId });
    
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected for workflow:', workflowId);
      setIsConnected(true);
      setError(null);
    };

    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        handleWebSocketMessage(message);
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
      
      // Attempt to reconnect after 3 seconds if not completed
      if (currentStep !== 'completed') {
        setTimeout(connectWebSocket, 3000);
      }
    };

    ws.onerror = (err) => {
      console.error('WebSocket error:', err);
      setError('Connection error');
    };

    return ws;
  }, [workflowId, userId, currentStep, handleWebSocketMessage]);

  // Initialize WebSocket connection
  useEffect(() => {
    const ws = connectWebSocket();
    return () => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [connectWebSocket]);

  // Error boundary
  if (error) {
    return (
      <div className="workflow-status error">
        <div className="error-message">
          <span className="error-icon">⚠️</span>
          Connection Error: {error}
        </div>
      </div>
    );
  }

  // Not connected yet
  if (!isConnected || !status) {
    return (
      <div className="workflow-status connecting">
        <div className="connecting-spinner"></div>
        <div className="connecting-message">Connecting to workflow...</div>
      </div>
    );
  }

  return (
    <div className="workflow-status">
      {/* Current Status Display */}
      <div className="current-status">
        <div className="status-header">
          <div className="status-icon">
            {currentStep === 'completed' ? '✅' : '⚡'}
          </div>
          <div className="status-text">
            <div className="status-message">{status.message}</div>
            <div className="status-timestamp">
              {status.timestamp?.toLocaleTimeString()}
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        {showProgress && (
          <div className="progress-container">
            <div className="progress-bar">
              <div 
                className="progress-fill"
                style={{ 
                  width: `${progress}%`,
                  backgroundColor: currentStep === 'completed' ? '#10b981' : '#3b82f6'
                }}
              />
            </div>
            <div className="progress-text">{Math.round(progress)}%</div>
          </div>
        )}
      </div>

      {/* Step Indicators */}
      {showSteps && (
        <div className="workflow-steps">
          {workflowSteps.map((step, index) => {
            const isCompleted = completedSteps.has(step.key);
            const isCurrent = currentStep === step.key;
            const isUpcoming = !isCompleted && !isCurrent;

            return (
              <div 
                key={step.key}
                className={`step-item ${isCompleted ? 'completed' : ''} ${isCurrent ? 'current' : ''} ${isUpcoming ? 'upcoming' : ''}`}
              >
                <div 
                  className="step-indicator"
                  style={{ 
                    backgroundColor: isCompleted || isCurrent ? step.color : '#e5e7eb'
                  }}
                >
                  {isCompleted ? '✓' : step.icon}
                </div>
                <div className="step-info">
                  <div className="step-label">{step.label}</div>
                  <div className="step-description">{step.description}</div>
                </div>
                {index < workflowSteps.length - 1 && (
                  <div 
                    className="step-connector"
                    style={{
                      backgroundColor: isCompleted ? '#10b981' : '#e5e7eb'
                    }}
                  />
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Connection Status */}
      <div className="connection-status">
        <div className={`connection-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
          {isConnected ? '🟢' : '🔴'}
        </div>
        <span className="connection-text">
          {isConnected ? 'Connected' : 'Disconnected'}
        </span>
      </div>
    </div>
  );
};

export default WorkflowStatus;