import { useEffect, useRef, useState, useCallback } from 'react';
import { createWebSocket } from '@/lib/api';

export interface StreamMessage {
  type: 'thought' | 'action' | 'terminal' | 'status' | 'result' | 'error';
  content: string;
  timestamp: string;
  metadata?: Record<string, unknown>;
}

export function useAgentStream(taskId: string | null) {
  const [messages, setMessages] = useState<StreamMessage[]>([]);
  const [status, setStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const connect = useCallback(() => {
    if (!taskId) return;

    setStatus('connecting');
    setError(null);

    const ws = createWebSocket(taskId);

    ws.onopen = () => {
      setStatus('connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as StreamMessage;
        setMessages((prev) => [...prev, data]);
      } catch (e) {
        // Handle raw text messages
        setMessages((prev) => [...prev, {
          type: 'terminal',
          content: event.data,
          timestamp: new Date().toISOString(),
        }]);
      }
    };

    ws.onerror = () => {
      setStatus('error');
      setError('WebSocket connection error');
    };

    ws.onclose = () => {
      setStatus('disconnected');
      
      // Auto-reconnect after 3 seconds
      reconnectTimeoutRef.current = setTimeout(() => {
        if (taskId) {
          connect();
        }
      }, 3000);
    };

    wsRef.current = ws;
  }, [taskId]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setStatus('disconnected');
  }, []);

  const sendMessage = useCallback((message: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(message);
    }
  }, []);

  useEffect(() => {
    if (taskId) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [taskId, connect, disconnect]);

  return {
    messages,
    status,
    error,
    sendMessage,
    disconnect,
    reconnect: connect,
  };
}