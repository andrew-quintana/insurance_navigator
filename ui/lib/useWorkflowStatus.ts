/**
 * useWorkflowStatus Hook
 * 
 * Custom React hook for managing workflow status connections
 * and state management for real-time updates.
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { buildWebSocketUrl } from './api-config';

interface WorkflowStatusUpdate {
  step: string;
  message: string;
  progress: number;
  timestamp: Date;
}

interface WebSocketMessage {
  type: string;
  status?: WorkflowStatusUpdate;
  response?: string;
  success?: boolean;
}

interface UseWorkflowStatusOptions {
  autoConnect?: boolean;
  reconnectAttempts?: number;
  reconnectDelay?: number;
  onStatusUpdate?: (status: WorkflowStatusUpdate) => void;
  onComplete?: (response: string, success: boolean) => void;
  onError?: (error: Error | string) => void;
}

// Remove duplicate interface - using WorkflowStatusUpdate above

export const useWorkflowStatus = (
  workflowId: string | null, 
  userId: string | null, 
  options: UseWorkflowStatusOptions = {}
) => {
  const {
    autoConnect = true,
    reconnectAttempts = 3,
    reconnectDelay = 3000,
    onStatusUpdate = () => {},
    onComplete = () => {},
    onError = () => {}
  } = options;

  // State management
  const [status, setStatus] = useState<WorkflowStatusUpdate | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState<number>(0);
  const [currentStep, setCurrentStep] = useState<string | null>(null);
  const [completedSteps, setCompletedSteps] = useState<Set<string>>(new Set());

  // Refs for cleanup and reconnection
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectCountRef = useRef(0);
  const connectRef = useRef<(() => void) | null>(null);
  const handleMessageRef = useRef<((message: WebSocketMessage) => void) | null>(null);

  // Handle reconnection
  const scheduleReconnect = useCallback(() => {
    if (reconnectCountRef.current >= reconnectAttempts) {
      setError(`Failed to reconnect after ${reconnectAttempts} attempts`);
      return;
    }

    reconnectCountRef.current++;
    setError(`Reconnecting... (${reconnectCountRef.current}/${reconnectAttempts})`);

    reconnectTimeoutRef.current = setTimeout(() => {
      connectRef.current?.();
    }, reconnectDelay);
  }, [reconnectAttempts, reconnectDelay]);

  // Create WebSocket connection
  const connect = useCallback((): void => {
    if (!workflowId || !userId) {
      setError('Missing workflowId or userId');
      return;
    }

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    try {
      // Use centralized configuration to build WebSocket URL
      const wsUrl = buildWebSocketUrl(`/ws/workflow/${workflowId}`, { user_id: userId });
      
      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('WorkflowStatus WebSocket connected:', workflowId);
        setIsConnected(true);
        setError(null);
        reconnectCountRef.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleMessageRef.current?.(message);
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
          setError('Message parsing error');
        }
      };

      ws.onclose = (event) => {
        console.log('WorkflowStatus WebSocket closed:', event.code, event.reason);
        setIsConnected(false);
        wsRef.current = null;

        // Attempt reconnection if not intentional close and within limits
        if (event.code !== 1000 && reconnectCountRef.current < reconnectAttempts) {
          scheduleReconnect();
        }
      };

      ws.onerror = (err) => {
        console.error('WorkflowStatus WebSocket error:', err);
        setError('Connection error');
        onError('WebSocket connection error');
      };

    } catch (err) {
      console.error('Failed to create WebSocket connection:', err);
      setError('Failed to connect');
      onError(err instanceof Error ? err : 'Failed to create WebSocket connection');
    }
  }, [workflowId, userId, reconnectAttempts, onError, scheduleReconnect]);

  // Update ref to avoid circular dependency
  connectRef.current = connect;

  // Handle incoming messages
  const handleMessage = useCallback((message: WebSocketMessage) => {
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
        
        // Update completed steps
        const stepOrder = ['sanitizing', 'determining', 'thinking', 'skimming', 'wording'];
        const currentIndex = stepOrder.indexOf(newStatus.step);
        if (currentIndex >= 0) {
          setCompletedSteps(prev => {
            const newSet = new Set(prev);
            for (let i = 0; i < currentIndex; i++) {
              newSet.add(stepOrder[i]);
            }
            return newSet;
          });
        }
        
        onStatusUpdate(newStatus);
        break;

      case 'workflow_complete':
        const completeStatus = {
          step: 'completed',
          message: 'Workflow completed successfully',
          progress: 1,
          timestamp: new Date()
        };
        
        setStatus(completeStatus);
        setProgress(100);
        setCurrentStep('completed');
        setCompletedSteps(new Set(['sanitizing', 'determining', 'thinking', 'skimming', 'wording']));
        
        onComplete(message.response || '', message.success || false);
        break;

      case 'ping':
        // Send pong response
        if (wsRef.current?.readyState === WebSocket.OPEN) {
          wsRef.current.send('pong');
        }
        break;

      default:
        console.log('Unknown WebSocket message type:', message.type, message);
    }
  }, [onStatusUpdate, onComplete]);

  // Update ref to avoid circular dependency
  handleMessageRef.current = handleMessage;

  // Disconnect WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    if (wsRef.current) {
      wsRef.current.close(1000, 'Intentional disconnect');
      wsRef.current = null;
    }

    setIsConnected(false);
    setStatus(null);
    setProgress(0);
    setCurrentStep(null);
    setCompletedSteps(new Set());
    setError(null);
  }, []);

  // Manual reconnect
  const reconnect = useCallback(() => {
    disconnect();
    setTimeout(() => {
      reconnectCountRef.current = 0;
      connect();
    }, 100);
  }, [disconnect, connect]);

  // Auto-connect effect
  useEffect(() => {
    if (autoConnect && workflowId && userId) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, workflowId, userId, connect, disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    // State
    status,
    isConnected,
    error,
    progress,
    currentStep,
    completedSteps,
    
    // Actions
    connect,
    disconnect,
    reconnect,
    
    // Utilities
    isProcessing: currentStep && currentStep !== 'completed',
    isCompleted: currentStep === 'completed',
    connectionState: isConnected ? 'connected' : error ? 'error' : 'disconnected'
  };
};