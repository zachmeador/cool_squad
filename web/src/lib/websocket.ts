// websocket client for cool_squad backend
'use client';

import { useEffect, useState, useCallback, useRef } from 'react';

// websocket base url
const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws';

// websocket message types
export interface WebSocketMessage {
  type: string;
  data: any;
}

// mock data for development when backend is not available
const MOCK_CHANNELS = ['welcome', 'general', 'random', 'bots'];
const MOCK_BOARDS = [
  { id: 'general', name: 'General Discussion', description: 'Talk about anything' },
  { id: 'tech', name: 'Technology', description: 'Discuss tech topics' },
  { id: 'random', name: 'Random', description: 'Random stuff' }
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

// hook for chat websocket
export function useChatWebSocket(channel: string, username: string) {
  const [connected, setConnected] = useState(false);
  const [messages, setMessages] = useState<any[]>([]);
  const socketRef = useRef<WebSocket | null>(null);
  const [usesMockData, setUsesMockData] = useState(false);

  // connect to websocket
  useEffect(() => {
    if (!channel || !username) return;

    try {
      const wsUrl = `${WS_BASE_URL}/chat/${channel}`;
      const socket = new WebSocket(wsUrl);
      socketRef.current = socket;

      socket.onopen = () => {
        console.log(`connected to chat channel: ${channel}`);
        setConnected(true);
        setUsesMockData(false);
        
        // join channel
        socket.send(JSON.stringify({
          type: 'command',
          command: 'join',
          channel,
          username
        }));
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('received chat message:', data);
          
          if (data.type === 'message') {
            setMessages(prev => [...prev, data]);
          } else if (data.type === 'history') {
            setMessages(data.messages || []);
          }
        } catch (error) {
          console.error('error parsing websocket message:', error);
        }
      };

      socket.onclose = () => {
        console.log(`disconnected from chat channel: ${channel}`);
        setConnected(false);
        
        // If we never connected successfully, use mock data
        if (!connected && !usesMockData) {
          console.log('using mock data for chat');
          setUsesMockData(true);
          setMessages([
            {
              content: `Welcome to the ${channel} channel!`,
              author: 'system',
              timestamp: new Date().toISOString()
            },
            {
              content: `This is mock data since the backend is not available.`,
              author: 'system',
              timestamp: new Date().toISOString()
            }
          ]);
        }
      };

      socket.onerror = (error) => {
        console.error('websocket error:', error);
        setConnected(false);
      };

      return () => {
        socket.close();
      };
    } catch (error) {
      console.error('error connecting to websocket:', error);
      
      // Use mock data if connection fails
      if (!usesMockData) {
        console.log('using mock data for chat due to connection error');
        setUsesMockData(true);
        setMessages([
          {
            content: `Welcome to the ${channel} channel!`,
            author: 'system',
            timestamp: new Date().toISOString()
          },
          {
            content: `This is mock data since the backend is not available.`,
            author: 'system',
            timestamp: new Date().toISOString()
          }
        ]);
      }
    }
  }, [channel, username, connected, usesMockData]);

  // send message
  const sendMessage = useCallback((content: string) => {
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
            content: `This is a mock response to: "${content}"`,
            author: 'bot',
            timestamp: new Date().toISOString()
          }
        ]);
      }, 1000);
      return;
    }
    
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      console.error('websocket not connected');
      return;
    }

    socketRef.current.send(JSON.stringify({
      type: 'message',
      content,
      author: username
    }));
  }, [username, usesMockData]);

  return { connected: connected || usesMockData, messages, sendMessage };
}

// hook for board websocket
export function useBoardWebSocket(board: string, username: string) {
  const [connected, setConnected] = useState(false);
  const [threads, setThreads] = useState<any[]>([]);
  const [currentThread, setCurrentThread] = useState<any>(null);
  const socketRef = useRef<WebSocket | null>(null);
  const [usesMockData, setUsesMockData] = useState(false);

  // connect to websocket
  useEffect(() => {
    if (!board || !username) return;

    try {
      const wsUrl = `${WS_BASE_URL}/board/${board}`;
      const socket = new WebSocket(wsUrl);
      socketRef.current = socket;

      socket.onopen = () => {
        console.log(`connected to board: ${board}`);
        setConnected(true);
        setUsesMockData(false);
        
        // list threads
        socket.send(JSON.stringify({
          type: 'command',
          command: 'view_board',
          boardId: board
        }));
      };

      socket.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log('received board message:', data);
          
          if (data.type === 'threads') {
            setThreads(data.threads || []);
          } else if (data.type === 'thread') {
            setCurrentThread(data);
          }
        } catch (error) {
          console.error('error parsing websocket message:', error);
        }
      };

      socket.onclose = () => {
        console.log(`disconnected from board: ${board}`);
        setConnected(false);
        
        // If we never connected successfully, use mock data
        if (!connected && !usesMockData) {
          console.log('using mock data for board');
          setUsesMockData(true);
          setThreads(MOCK_THREADS);
        }
      };

      socket.onerror = (error) => {
        console.error('websocket error:', error);
        setConnected(false);
      };

      return () => {
        socket.close();
      };
    } catch (error) {
      console.error('error connecting to websocket:', error);
      
      // Use mock data if connection fails
      if (!usesMockData) {
        console.log('using mock data for board due to connection error');
        setUsesMockData(true);
        setThreads(MOCK_THREADS);
      }
    }
  }, [board, username, connected, usesMockData]);

  // view thread
  const viewThread = useCallback((threadId: string) => {
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
    
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      console.error('websocket not connected');
      return;
    }

    if (!threadId) {
      setCurrentThread(null);
      return;
    }

    socketRef.current.send(JSON.stringify({
      type: 'command',
      command: 'view_thread',
      threadId
    }));
  }, [usesMockData]);

  // create thread
  const createThread = useCallback((title: string, content: string) => {
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
    
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN) {
      console.error('websocket not connected');
      return;
    }

    socketRef.current.send(JSON.stringify({
      type: 'command',
      command: 'create_thread',
      title,
      content,
      author: username
    }));
  }, [username, usesMockData]);

  // reply to thread
  const replyToThread = useCallback((content: string) => {
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
    
    if (!socketRef.current || socketRef.current.readyState !== WebSocket.OPEN || !currentThread) {
      console.error('websocket not connected or no thread selected');
      return;
    }

    socketRef.current.send(JSON.stringify({
      type: 'command',
      command: 'reply_to_thread',
      threadId: currentThread.id,
      content,
      author: username
    }));
  }, [currentThread, username, usesMockData]);

  return { 
    connected: connected || usesMockData, 
    threads, 
    currentThread, 
    viewThread, 
    createThread, 
    replyToThread 
  };
} 