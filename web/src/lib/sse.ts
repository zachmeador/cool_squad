'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid';

// sse base url
const SSE_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// mock data for development when backend is not available
const MOCK_MESSAGES = [
  {
    content: 'welcome to the chat!',
    author: 'system',
    timestamp: new Date().toISOString()
  },
  {
    content: 'this is mock data since the backend is not available.',
    author: 'system',
    timestamp: new Date().toISOString()
  }
];


// hook for chat sse
export function useChatSSE(channel: string, username: string) {
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState<any[]>([]);
  const eventSourceRef = useRef<EventSource | null>(null);
  const [error, setError] = useState<string | null>(null);
  const clientId = useRef(uuidv4());
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 3;
  const connectionTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // connect to sse
  useEffect(() => {
    if (!channel || !username) return;

    console.log(`attempting to connect to channel: ${channel} as ${username}`);

    // Clear any existing reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Clear any existing connection timeout
    if (connectionTimeoutRef.current) {
      clearTimeout(connectionTimeoutRef.current);
      connectionTimeoutRef.current = null;
    }

    // Clear any existing error
    setError(null);

    const connectSSE = () => {
      try {
        // Close any existing connection
        if (eventSourceRef.current) {
          console.log('closing existing connection');
          eventSourceRef.current.close();
        }

        const sseUrl = `${SSE_BASE_URL}/chat/${channel}?client_id=${clientId.current}`;
        console.log(`connecting to sse: ${sseUrl}`);
        
        const eventSource = new EventSource(sseUrl, { withCredentials: false });
        eventSourceRef.current = eventSource;

        // Set a timeout to show error if connection doesn't establish quickly
        connectionTimeoutRef.current = setTimeout(() => {
          if (!connected) {
            console.log('connection timeout, showing error');
            setError('failed to connect to chat server. please check your connection and try again.');
            if (eventSourceRef.current) {
              eventSourceRef.current.close();
            }
          }
        }, 5000);

        eventSource.onopen = () => {
          console.log(`connected to channel: ${channel}`);
          if (connectionTimeoutRef.current) {
            clearTimeout(connectionTimeoutRef.current);
            connectionTimeoutRef.current = null;
          }
          setConnected(true);
          setError(null);
          reconnectAttemptsRef.current = 0;
        };

        eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('received message:', data);
            
            if (data.type === 'history') {
              setMessages(data.messages || []);
            } else if (data.type === 'message') {
              setMessages(prev => [...prev, data]);
            }
          } catch (error) {
            console.error('error parsing message:', error);
          }
        };

        // Listen for ping events to keep connection alive
        eventSource.addEventListener('ping', () => {
          console.log('received ping');
        });

        eventSource.onerror = (error) => {
          console.error('sse error:', error);
          if (connectionTimeoutRef.current) {
            clearTimeout(connectionTimeoutRef.current);
            connectionTimeoutRef.current = null;
          }
          eventSource.close();
          setConnected(false);
          
          // If we've reached max reconnect attempts, show error
          if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
            console.log('max reconnect attempts reached, showing error');
            setError('failed to connect to chat server after multiple attempts. please check your connection and try again.');
            return;
          }
          
          // Try to reconnect after a delay, with exponential backoff
          reconnectAttemptsRef.current += 1;
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current - 1), 30000);
          console.log(`attempting to reconnect in ${delay}ms (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})...`);
          setError(`connection lost. attempting to reconnect (${reconnectAttemptsRef.current}/${maxReconnectAttempts})...`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connectSSE();
          }, delay);
        };

        return () => {
          if (connectionTimeoutRef.current) {
            clearTimeout(connectionTimeoutRef.current);
            connectionTimeoutRef.current = null;
          }
        };
      } catch (error) {
        console.error('error connecting to sse:', error);
        setError('failed to connect to chat server. please check your connection and try again.');
        return () => {};
      }
    };

    const cleanup = connectSSE();

    return () => {
      // Clean up on unmount
      if (typeof cleanup === 'function') {
        cleanup();
      }
      
      if (eventSourceRef.current) {
        console.log('closing sse connection on unmount');
        eventSourceRef.current.close();
      }
      
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      
      if (connectionTimeoutRef.current) {
        clearTimeout(connectionTimeoutRef.current);
      }
    };
  }, [channel, username]);

  // send message
  const sendMessage = useCallback(async (content: string) => {
    if (!connected) {
      setError('cannot send message: not connected to chat server');
      throw new Error('Not connected to chat server');
    }
    
    try {
      const response = await fetch(`${SSE_BASE_URL}/channels/${channel}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content,
          author: username
        }),
        signal: AbortSignal.timeout(5000), // Add timeout to prevent hanging requests
      });
      
      if (!response.ok) {
        console.error(`error sending message: ${response.status}`);
        setError(`failed to send message: ${response.status}`);
        throw new Error(`Failed to send message: ${response.status}`);
      }
    } catch (error) {
      console.error('error sending message:', error);
      setError('failed to send message. please try again.');
      throw error;
    }
  }, [channel, username, connected]);

  return { connected, messages, sendMessage, error };
}

// hook for board sse
export function useBoardSSE(board: string, username: string) {
  const [connected, setConnected] = useState(false);
  const [threads, setThreads] = useState<any[]>([]);
  const [currentThread, setCurrentThread] = useState<any>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const [error, setError] = useState<string | null>(null);
  const clientId = useRef(uuidv4());
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const maxReconnectAttempts = 3;
  const connectionTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // connect to sse
  useEffect(() => {
    if (!board || !username) return;

    // Clear any existing reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    // Clear any existing connection timeout
    if (connectionTimeoutRef.current) {
      clearTimeout(connectionTimeoutRef.current);
      connectionTimeoutRef.current = null;
    }

    // Clear any existing error
    setError(null);

    const connectSSE = () => {
      try {
        // Close any existing connection
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
        }

        const sseUrl = `${SSE_BASE_URL}/board/${board}?client_id=${clientId.current}`;
        console.log(`connecting to board sse: ${sseUrl}`);
        
        const eventSource = new EventSource(sseUrl, { withCredentials: false });
        eventSourceRef.current = eventSource;

        // Set a timeout to show error if connection doesn't establish quickly
        connectionTimeoutRef.current = setTimeout(() => {
          if (!connected) {
            console.log('connection timeout, showing error');
            setError('failed to connect to board server. please check your connection and try again.');
            if (eventSourceRef.current) {
              eventSourceRef.current.close();
            }
          }
        }, 5000);

        eventSource.onopen = () => {
          console.log(`connected to board: ${board}`);
          if (connectionTimeoutRef.current) {
            clearTimeout(connectionTimeoutRef.current);
            connectionTimeoutRef.current = null;
          }
          setConnected(true);
          setError(null);
          reconnectAttemptsRef.current = 0;
        };

        // Listen for message events
        eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('received board message:', data);
            
            if (data.type === 'board_update') {
              setThreads(data.board.threads || []);
            } else if (data.type === 'thread_update') {
              setCurrentThread(data.thread);
              
              // Also update the thread in the threads list
              setThreads(prev => 
                prev.map(t => t.id === data.thread.id ? data.thread : t)
              );
            }
          } catch (error) {
            console.error('error parsing message:', error);
          }
        };

        // Listen for ping events to keep connection alive
        eventSource.addEventListener('ping', () => {
          console.log('received ping');
        });

        eventSource.onerror = (error) => {
          console.error('sse error:', error);
          if (connectionTimeoutRef.current) {
            clearTimeout(connectionTimeoutRef.current);
            connectionTimeoutRef.current = null;
          }
          eventSource.close();
          setConnected(false);
          
          // If we've reached max reconnect attempts, show error
          if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
            console.log('max reconnect attempts reached, showing error');
            setError('failed to connect to board server after multiple attempts. please check your connection and try again.');
            return;
          }
          
          // Try to reconnect after a delay, with exponential backoff
          reconnectAttemptsRef.current += 1;
          const delay = Math.min(1000 * Math.pow(2, reconnectAttemptsRef.current - 1), 30000);
          console.log(`attempting to reconnect in ${delay}ms (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})...`);
          setError(`connection lost. attempting to reconnect (${reconnectAttemptsRef.current}/${maxReconnectAttempts})...`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connectSSE();
          }, delay);
        };

        return () => {
          if (connectionTimeoutRef.current) {
            clearTimeout(connectionTimeoutRef.current);
            connectionTimeoutRef.current = null;
          }
        };
      } catch (error) {
        console.error('error connecting to sse:', error);
        setError('failed to connect to board server. please check your connection and try again.');
        return () => {};
      }
    };

    const cleanup = connectSSE();

    return () => {
      // Clean up on unmount
      if (typeof cleanup === 'function') {
        cleanup();
      }
      
      if (eventSourceRef.current) {
        console.log('closing sse connection on unmount');
        eventSourceRef.current.close();
      }
      
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      
      if (connectionTimeoutRef.current) {
        clearTimeout(connectionTimeoutRef.current);
      }
    };
  }, [board, username]);

  // view thread
  const viewThread = useCallback(async (threadId: string) => {
    if (!threadId) {
      setCurrentThread(null);
      return;
    }

    try {
      const response = await fetch(`${SSE_BASE_URL}/boards/${board}/threads/${threadId}`, {
        signal: AbortSignal.timeout(5000)
      });
      
      if (!response.ok) {
        const errorText = await response.text().catch(() => 'Unknown error');
        throw new Error(`failed to fetch thread: ${response.status} - ${errorText}`);
      }
      
      const thread = await response.json();
      setCurrentThread(thread);
    } catch (error) {
      console.error('error fetching thread:', error);
      setError(`failed to fetch thread: ${error instanceof Error ? error.message : 'unknown error'}`);
    }
  }, [board]);

  // create thread
  const createThread = useCallback(async (title: string, content: string) => {
    if (!connected) {
      setError('cannot create thread: not connected to board server');
      throw new Error('Not connected to board server');
    }
    
    try {
      const response = await fetch(`${SSE_BASE_URL}/boards/${board}/threads`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          title,
          message: content,
          author: username
        }),
        signal: AbortSignal.timeout(5000)
      });
      
      if (!response.ok) {
        const errorText = await response.text().catch(() => 'Unknown error');
        throw new Error(`failed to create thread: ${response.status} - ${errorText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('error creating thread:', error);
      setError(`failed to create thread: ${error instanceof Error ? error.message : 'unknown error'}`);
      throw error;
    }
  }, [board, username, connected]);

  // reply to thread
  const replyToThread = useCallback(async (content: string) => {
    if (!connected) {
      setError('cannot reply to thread: not connected to board server');
      throw new Error('Not connected to board server');
    }
    
    if (!currentThread) {
      setError('no thread selected');
      throw new Error('No thread selected');
    }

    try {
      const response = await fetch(`${SSE_BASE_URL}/boards/${board}/threads/${currentThread.id}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content,
          author: username
        }),
        signal: AbortSignal.timeout(5000)
      });
      
      if (!response.ok) {
        const errorText = await response.text().catch(() => 'Unknown error');
        throw new Error(`failed to reply to thread: ${response.status} - ${errorText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('error replying to thread:', error);
      setError(`failed to reply to thread: ${error instanceof Error ? error.message : 'unknown error'}`);
      throw error;
    }
  }, [currentThread, board, username, connected]);

  return { 
    connected, 
    threads, 
    currentThread, 
    viewThread, 
    createThread, 
    replyToThread,
    error
  };
} 