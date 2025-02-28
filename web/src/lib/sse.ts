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

const MOCK_THREADS = [
  { 
    id: '1', 
    title: 'Welcome to the boards', 
    author: 'system', 
    created_at: Date.now() / 1000, 
    pinned: true,
    tags: ['welcome', 'important']
  }
];

// hook for chat sse
export function useChatSSE(channel: string, username: string) {
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState<any[]>([]);
  const eventSourceRef = useRef<EventSource | null>(null);
  const [usesMockData, setUsesMockData] = useState(false);
  const clientId = useRef(uuidv4());
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // connect to sse
  useEffect(() => {
    if (!channel || !username) return;

    // Clear any existing reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    const connectSSE = () => {
      try {
        // Close any existing connection
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
        }

        const sseUrl = `${SSE_BASE_URL}/sse/chat/${channel}?client_id=${clientId.current}`;
        console.log(`connecting to sse: ${sseUrl}`);
        
        const eventSource = new EventSource(sseUrl);
        eventSourceRef.current = eventSource;

        eventSource.onopen = () => {
          console.log(`connected to chat channel: ${channel}`);
          setConnected(true);
          setUsesMockData(false);
        };

        // Listen for message events
        eventSource.addEventListener('message', (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log('received chat message:', data);
            
            if (data.type === 'message') {
              setMessages(prev => [...prev, data]);
            } else if (data.type === 'history') {
              setMessages(data.messages || []);
            }
          } catch (error) {
            console.error('error parsing sse message:', error);
          }
        });

        // Listen for ping events to keep connection alive
        eventSource.addEventListener('ping', () => {
          // Just acknowledge the ping
          console.log('received ping');
        });

        eventSource.onerror = (error) => {
          console.error('sse error:', error);
          eventSource.close();
          setConnected(false);
          
          // If we never connected successfully, use mock data
          if (!connected && !usesMockData) {
            console.log('using mock data for chat');
            setUsesMockData(true);
            setMessages(MOCK_MESSAGES);
          }
          
          // Try to reconnect after a delay
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('attempting to reconnect...');
            connectSSE();
          }, 3000);
        };
      } catch (error) {
        console.error('error connecting to sse:', error);
        
        // Use mock data if connection fails
        if (!usesMockData) {
          console.log('using mock data for chat due to connection error');
          setUsesMockData(true);
          setMessages(MOCK_MESSAGES);
        }
        
        // Try to reconnect after a delay
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('attempting to reconnect...');
          connectSSE();
        }, 3000);
      }
    };

    connectSSE();

    return () => {
      // Clean up on unmount
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [channel, username]);

  // send message
  const sendMessage = useCallback(async (content: string) => {
    if (usesMockData) {
      // Handle mock data
      setMessages(prev => [
        ...prev, 
        {
          content,
          author: username,
          timestamp: new Date().toISOString()
        }
      ]);
      
      // Add bot response after a delay
      setTimeout(() => {
        setMessages(prev => [
          ...prev,
          {
            content: `this is a mock response to: "${content}"`,
            author: 'bot',
            timestamp: new Date().toISOString()
          }
        ]);
      }, 1000);
      return;
    }
    
    try {
      // Add the message to the local state immediately for better UX
      const timestamp = new Date().toISOString();
      setMessages(prev => [
        ...prev, 
        {
          content,
          author: username,
          timestamp
        }
      ]);
      
      const response = await fetch(`${SSE_BASE_URL}/channels/${channel}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content,
          author: username
        }),
      });
      
      if (!response.ok) {
        console.error(`error sending message: ${response.status}`);
      }
    } catch (error) {
      console.error('error sending message:', error);
    }
  }, [channel, username, usesMockData]);

  return { connected: connected || usesMockData, messages, sendMessage };
}

// hook for board sse
export function useBoardSSE(board: string, username: string) {
  const [connected, setConnected] = useState(false);
  const [threads, setThreads] = useState<any[]>([]);
  const [currentThread, setCurrentThread] = useState<any>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const [usesMockData, setUsesMockData] = useState(false);
  const clientId = useRef(uuidv4());
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  // connect to sse
  useEffect(() => {
    if (!board || !username) return;

    // Clear any existing reconnect timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }

    const connectSSE = () => {
      try {
        // Close any existing connection
        if (eventSourceRef.current) {
          eventSourceRef.current.close();
        }

        const sseUrl = `${SSE_BASE_URL}/sse/board/${board}?client_id=${clientId.current}`;
        console.log(`connecting to board sse: ${sseUrl}`);
        
        const eventSource = new EventSource(sseUrl);
        eventSourceRef.current = eventSource;

        eventSource.onopen = () => {
          console.log(`connected to board: ${board}`);
          setConnected(true);
          setUsesMockData(false);
        };

        // Listen for message events
        eventSource.addEventListener('message', (event) => {
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
            console.error('error parsing sse message:', error);
          }
        });

        // Listen for ping events to keep connection alive
        eventSource.addEventListener('ping', () => {
          // Just acknowledge the ping
          console.log('received ping');
        });

        eventSource.onerror = (error) => {
          console.error('sse error:', error);
          eventSource.close();
          setConnected(false);
          
          // If we never connected successfully, use mock data
          if (!connected && !usesMockData) {
            console.log('using mock data for board');
            setUsesMockData(true);
            setThreads(MOCK_THREADS);
          }
          
          // Try to reconnect after a delay
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log('attempting to reconnect...');
            connectSSE();
          }, 3000);
        };
      } catch (error) {
        console.error('error connecting to sse:', error);
        
        // Use mock data if connection fails
        if (!usesMockData) {
          console.log('using mock data for board due to connection error');
          setUsesMockData(true);
          setThreads(MOCK_THREADS);
        }
        
        // Try to reconnect after a delay
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('attempting to reconnect...');
          connectSSE();
        }, 3000);
      }
    };

    connectSSE();

    return () => {
      // Clean up on unmount
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
      
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [board, username]);

  // view thread
  const viewThread = useCallback(async (threadId: string) => {
    if (usesMockData) {
      if (!threadId) {
        setCurrentThread(null);
        return;
      }
      
      // Mock thread data
      setCurrentThread({
        id: threadId,
        title: 'Mock Thread',
        author: 'system',
        created_at: Date.now() / 1000,
        messages: [
          {
            content: 'This is a mock thread since the backend is not available.',
            author: 'system',
            timestamp: Date.now() / 1000
          }
        ]
      });
      return;
    }
    
    if (!threadId) {
      setCurrentThread(null);
      return;
    }

    try {
      const response = await fetch(`${SSE_BASE_URL}/boards/${board}/threads/${threadId}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const thread = await response.json();
      setCurrentThread(thread);
    } catch (error) {
      console.error('error fetching thread:', error);
    }
  }, [board, usesMockData]);

  // create thread
  const createThread = useCallback(async (title: string, content: string) => {
    if (usesMockData) {
      // Create mock thread
      const newThread = {
        id: `mock-${Date.now()}`,
        title,
        author: username,
        created_at: Date.now() / 1000,
        pinned: false,
        tags: []
      };
      
      setThreads(prev => [newThread, ...prev]);
      return;
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
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error('error creating thread:', error);
    }
  }, [board, username, usesMockData]);

  // reply to thread
  const replyToThread = useCallback(async (content: string) => {
    if (usesMockData && currentThread) {
      // Add mock reply
      const updatedThread = {
        ...currentThread,
        messages: [
          ...(currentThread.messages || []),
          {
            content,
            author: username,
            timestamp: Date.now() / 1000
          }
        ]
      };
      
      setCurrentThread(updatedThread);
      return;
    }
    
    if (!currentThread) {
      console.error('no thread selected');
      return;
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
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
    } catch (error) {
      console.error('error replying to thread:', error);
    }
  }, [currentThread, board, username, usesMockData]);

  return { 
    connected: connected || usesMockData, 
    threads, 
    currentThread, 
    viewThread, 
    createThread, 
    replyToThread 
  };
} 