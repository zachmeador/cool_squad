// api client for cool_squad backend

// types
export interface Message {
  content: string;
  author: string;
  timestamp: string;
}

export interface Channel {
  name: string;
  messages: Message[];
}

export interface Board {
  id: string;
  name: string;
  description: string;
}

export interface Thread {
  id: string;
  title: string;
  author: string;
  created_at: number;
  pinned: boolean;
  tags: string[];
}

export interface ThreadDetail extends Thread {
  messages: Message[];
}

// api base url
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// mock data for development when backend is not available
const MOCK_CHANNELS = ['welcome', 'general', 'random', 'bots'];
const MOCK_BOARDS = [
  { id: 'general', name: 'General Discussion', description: 'Talk about anything' },
  { id: 'tech', name: 'Technology', description: 'Discuss tech topics' },
  { id: 'random', name: 'Random', description: 'Random stuff' }
];

// api functions
export async function getChannels(): Promise<string[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/channels`);
    if (!response.ok) throw new Error('failed to fetch channels');
    return response.json();
  } catch (error) {
    console.error('Error fetching channels:', error);
    return MOCK_CHANNELS;
  }
}

export async function getChannel(channelName: string): Promise<Channel> {
  try {
    const response = await fetch(`${API_BASE_URL}/channels/${channelName}`);
    if (!response.ok) throw new Error(`failed to fetch channel ${channelName}`);
    return response.json();
  } catch (error) {
    console.error(`Error fetching channel ${channelName}:`, error);
    return {
      name: channelName,
      messages: [
        {
          content: 'This is mock data since the backend is not available.',
          author: 'system',
          timestamp: new Date().toISOString()
        }
      ]
    };
  }
}

export async function postMessage(channelName: string, message: Omit<Message, 'timestamp'>): Promise<Message> {
  try {
    const response = await fetch(`${API_BASE_URL}/channels/${channelName}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(message),
    });
    if (!response.ok) throw new Error(`failed to post message to ${channelName}`);
    return response.json();
  } catch (error) {
    console.error(`Error posting message to ${channelName}:`, error);
    return {
      ...message,
      timestamp: new Date().toISOString()
    };
  }
}

export async function getBoards(): Promise<Board[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/boards`);
    if (!response.ok) throw new Error('failed to fetch boards');
    return response.json();
  } catch (error) {
    console.error('Error fetching boards:', error);
    return MOCK_BOARDS;
  }
}

export async function getBoardThreads(boardName: string): Promise<Thread[]> {
  try {
    const response = await fetch(`${API_BASE_URL}/boards/${boardName}`);
    if (!response.ok) throw new Error(`failed to fetch threads for board ${boardName}`);
    return response.json();
  } catch (error) {
    console.error(`Error fetching threads for board ${boardName}:`, error);
    return [
      { 
        id: '1', 
        title: 'Welcome to the boards', 
        author: 'system', 
        created_at: Date.now() / 1000, 
        pinned: true,
        tags: ['welcome', 'important']
      }
    ];
  }
}

export async function getThread(boardName: string, threadId: string): Promise<ThreadDetail> {
  try {
    const response = await fetch(`${API_BASE_URL}/boards/${boardName}/threads/${threadId}`);
    if (!response.ok) throw new Error(`failed to fetch thread ${threadId}`);
    return response.json();
  } catch (error) {
    console.error(`Error fetching thread ${threadId}:`, error);
    return {
      id: threadId,
      title: 'Mock Thread',
      author: 'system',
      created_at: Date.now() / 1000,
      pinned: false,
      tags: [],
      messages: [
        {
          content: 'This is mock data since the backend is not available.',
          author: 'system',
          timestamp: new Date().toISOString()
        }
      ]
    };
  }
}

export async function createThread(
  boardName: string, 
  title: string, 
  firstMessage: Omit<Message, 'timestamp'>
): Promise<Thread> {
  try {
    const response = await fetch(`${API_BASE_URL}/boards/${boardName}/threads`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title,
        first_message: firstMessage,
      }),
    });
    if (!response.ok) throw new Error(`failed to create thread on board ${boardName}`);
    return response.json();
  } catch (error) {
    console.error(`Error creating thread on board ${boardName}:`, error);
    return {
      id: `mock-${Date.now()}`,
      title,
      author: firstMessage.author,
      created_at: Date.now() / 1000,
      pinned: false,
      tags: []
    };
  }
}

export async function postThreadMessage(
  boardName: string, 
  threadId: string, 
  message: Omit<Message, 'timestamp'>
): Promise<Message> {
  try {
    const response = await fetch(`${API_BASE_URL}/boards/${boardName}/threads/${threadId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(message),
    });
    if (!response.ok) throw new Error(`failed to post message to thread ${threadId}`);
    return response.json();
  } catch (error) {
    console.error(`Error posting message to thread ${threadId}:`, error);
    return {
      ...message,
      timestamp: new Date().toISOString()
    };
  }
} 