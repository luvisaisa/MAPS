/**
 * MAPS - Real-time Job Progress Hook
 * 
 * Custom React hook for tracking batch job progress with WebSocket or SSE
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import { apiClient } from '../services/api';
import type { JobProgressUpdate, ProcessingJob } from '../types/api';

interface UseJobProgressOptions {
  jobId: string;
  enabled?: boolean;
  useWebSocket?: boolean; // true for WebSocket, false for SSE
  onComplete?: (job: ProcessingJob) => void;
  onError?: (error: Error) => void;
}

interface UseJobProgressReturn {
  progress: JobProgressUpdate | null;
  isConnected: boolean;
  error: Error | null;
  disconnect: () => void;
  reconnect: () => void;
}

export function useJobProgress({
  jobId,
  enabled = true,
  useWebSocket = true,
  onComplete,
  onError,
}: UseJobProgressOptions): UseJobProgressReturn {
  const [progress, setProgress] = useState<JobProgressUpdate | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const sseRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<number | null>(null);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (sseRef.current) {
      sseRef.current.close();
      sseRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const connect = useCallback(() => {
    if (!enabled || !jobId) return;

    disconnect();

    try {
      if (useWebSocket) {
        // WebSocket connection
        const ws = apiClient.connectWebSocket(jobId, (message) => {
          if (message.type === 'progress' && message.data) {
            setProgress(message.data as JobProgressUpdate);
          } else if (message.type === 'complete') {
            if (onComplete) {
              onComplete(message.data as ProcessingJob);
            }
            disconnect();
          } else if (message.type === 'error') {
            const err = new Error((message.data as any)?.error || 'Unknown error');
            setError(err);
            if (onError) {
              onError(err);
            }
          }
        });

        ws.onopen = () => setIsConnected(true);
        ws.onclose = () => {
          setIsConnected(false);
          // Auto-reconnect after 3 seconds if not manually disconnected
          if (enabled) {
            reconnectTimeoutRef.current = setTimeout(connect, 3000);
          }
        };
        ws.onerror = () => {
          const err = new Error('WebSocket connection error');
          setError(err);
          if (onError) {
            onError(err);
          }
        };

        wsRef.current = ws;
      } else {
        // Server-Sent Events connection
        const eventSource = apiClient.subscribeToJobProgress(jobId, (update) => {
          setProgress(update);
          
          if (update.status === 'completed' || update.status === 'failed' || update.status === 'cancelled') {
            if (onComplete && update.status === 'completed') {
              // Fetch full job details
              apiClient.getJob(jobId).then(onComplete).catch(console.error);
            }
            disconnect();
          }
        });

        eventSource.onopen = () => setIsConnected(true);
        eventSource.onerror = () => {
          setIsConnected(false);
          const err = new Error('SSE connection error');
          setError(err);
          if (onError) {
            onError(err);
          }
          // Auto-reconnect
          if (enabled) {
            reconnectTimeoutRef.current = setTimeout(connect, 3000) as unknown as number;
          }
        };

        sseRef.current = eventSource;
      }
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Connection failed');
      setError(error);
      if (onError) {
        onError(error);
      }
    }
  }, [jobId, enabled, useWebSocket, onComplete, onError, disconnect]);

  useEffect(() => {
    if (enabled) {
      connect();
    }
    return () => {
      disconnect();
    };
  }, [enabled, connect, disconnect]);

  return {
    progress,
    isConnected,
    error,
    disconnect,
    reconnect: connect,
  };
}
