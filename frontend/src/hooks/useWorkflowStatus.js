/**
 * useWorkflowStatus Hook
 * 
 * Custom React hook for managing workflow status connections
 * and state management for real-time updates.
 */

import { useState, useEffect, useCallback, useRef } from 'react';

export const useWorkflowStatus = (workflowId, userId, options = {}) => {
  const {
    autoConnect = true,
    reconnectAttempts = 3,
    reconnectDelay = 3000,
    onStatusUpdate = () => {},
    onComplete = () => {},
    onError = () => {}
  } = options;

  // State management
  const [status, setStatus] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState(null);
  const [progress, setProgress] = useState(0);
  const [currentStep, setCurrentStep] = useState(null);
  const [completedSteps, setCompletedSteps] = useState(new Set());

  // Refs for cleanup and reconnection
  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectCountRef = useRef(0);

  // Create WebSocket connection
  const connect = useCallback(() => {
    if (!workflowId || !userId) {
      setError('Missing workflowId or userId');
      return;
    }

    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return; // Already connected
    }

    try {
      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const wsUrl = `${protocol}//${window.location.host}/ws/workflow/${workflowId}?user_id=${userId}`;
      
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
          handleMessage(message);
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
        onError(err);
      };

    } catch (err) {
      console.error('Failed to create WebSocket connection:', err);
      setError('Failed to connect');
      onError(err);
    }
  }, [workflowId, userId, reconnectAttempts, onError]);

  // Handle reconnection
  const scheduleReconnect = useCallback(() => {
    if (reconnectCountRef.current >= reconnectAttempts) {
      setError(`Failed to reconnect after ${reconnectAttempts} attempts`);
      return;
    }

    reconnectCountRef.current++;
    setError(`Reconnecting... (${reconnectCountRef.current}/${reconnectAttempts})`);

    reconnectTimeoutRef.current = setTimeout(() => {
      connect();
    }, reconnectDelay);
  }, [connect, reconnectAttempts, reconnectDelay]);

  // Handle incoming messages
  const handleMessage = useCallback((message) => {
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
        
        onComplete(message.response, message.success);
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