import { useEffect, useRef, useState, useCallback } from 'react';
import { getApiBase } from '../api.js';

export const useWebSocket = (strategyId = null) => {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState(null);
  const [error, setError] = useState(null);
  const ws = useRef(null);
  const reconnectTimeout = useRef(null);
  const heartbeatInterval = useRef(null);

  const connect = useCallback(() => {
    const token = localStorage.getItem('token');
    if (!token) {
      setError('No authentication token found');
      return;
    }

    try {
      const wsUrl = `${getApiBase().replace('http', 'ws')}/ws?token=${token}`;
      ws.current = new WebSocket(wsUrl);

      ws.current.onopen = () => {
        setIsConnected(true);
        setError(null);
        console.log('WebSocket connected');

        // Subscribe to strategy if provided
        if (strategyId) {
          ws.current.send(JSON.stringify({
            type: 'subscribe',
            strategy_id: strategyId
          }));
        }

        // Start heartbeat
        heartbeatInterval.current = setInterval(() => {
          if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({ type: 'ping' }));
          }
        }, 30000);
      };

      ws.current.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          
          if (message.type === 'pong') {
            return; // Ignore heartbeat responses
          }
          
          setLastMessage(message);
          
          // Handle different message types
          switch (message.type) {
            case 'signal_created':
              console.log('New signal:', message.data);
              break;
            case 'trade_created':
              console.log('New trade:', message.data);
              break;
            case 'trade_closed':
              console.log('Trade closed:', message.data);
              break;
            case 'price_update':
              console.log('Price update:', message.data);
              break;
            default:
              console.log('Unknown message type:', message.type);
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      ws.current.onclose = (event) => {
        setIsConnected(false);
        console.log('WebSocket disconnected:', event.code, event.reason);
        
        // Clear heartbeat
        if (heartbeatInterval.current) {
          clearInterval(heartbeatInterval.current);
        }

        // Auto-reconnect after 5 seconds
        if (event.code !== 1000) { // Not a normal closure
          reconnectTimeout.current = setTimeout(() => {
            console.log('Attempting to reconnect...');
            connect();
          }, 5000);
        }
      };

      ws.current.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('WebSocket connection error');
      };

    } catch (err) {
      console.error('Error creating WebSocket:', err);
      setError('Failed to create WebSocket connection');
    }
  }, [strategyId]);

  const disconnect = useCallback(() => {
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
    }
    if (heartbeatInterval.current) {
      clearInterval(heartbeatInterval.current);
    }
    if (ws.current) {
      ws.current.close(1000, 'User disconnected');
      ws.current = null;
    }
    setIsConnected(false);
  }, []);

  const subscribe = useCallback((strategyIdToSubscribe) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
        type: 'subscribe',
        strategy_id: strategyIdToSubscribe
      }));
    }
  }, []);

  const unsubscribe = useCallback((strategyIdToUnsubscribe) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({
        type: 'unsubscribe',
        strategy_id: strategyIdToUnsubscribe
      }));
    }
  }, []);

  useEffect(() => {
    connect();
    return disconnect;
  }, [connect, disconnect]);

  useEffect(() => {
    // Handle strategy subscription changes
    if (isConnected && strategyId) {
      subscribe(strategyId);
    }
  }, [isConnected, strategyId, subscribe]);

  return {
    isConnected,
    lastMessage,
    error,
    subscribe,
    unsubscribe,
    disconnect,
    reconnect: connect
  };
};

export default useWebSocket;
