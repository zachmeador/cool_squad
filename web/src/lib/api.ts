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

// new interfaces for monologue
export interface Thought {
  content: string;
  category: string;
  timestamp: number;
}

export interface ToolConsideration {
  tool_name: string;
  reasoning: string;
  relevance_score: number;
  timestamp: number;
}

export interface Monologue {
  thoughts: Thought[];
  tool_considerations: Record<string, ToolConsideration>;
  max_thoughts: number;
  last_interaction_time: number;
}

export interface BotInfo {
  name: string;
  personality: string;
  provider: string;
  model: string;
  use_monologue: boolean;
  debug_mode: boolean;
}

// api base url
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';

// helper function to create fetch options with timeout
const createFetchOptions = (options: RequestInit = {}, timeoutMs = 5000): RequestInit => {
  return {
    ...options,
    signal: AbortSignal.timeout(timeoutMs),
    headers: {
      'Content-Type': 'application/json',
      ...(options.headers || {})
    }
  };
};

// api functions
export async function getChannels(): Promise<string[]> {
  console.log('fetching channels from:', `${API_BASE_URL}/channels`);
  const response = await fetch(`${API_BASE_URL}/channels`, createFetchOptions());
  
  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unknown error');
    throw new Error(`failed to fetch channels: ${response.status} - ${errorText}`);
  }
  
  return response.json();
}

export async function getChannel(channelName: string): Promise<Channel> {
  const response = await fetch(`${API_BASE_URL}/channels/${channelName}`, createFetchOptions());
  
  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unknown error');
    throw new Error(`failed to fetch channel ${channelName}: ${response.status} - ${errorText}`);
  }
  
  return response.json();
}

export async function postMessage(channelName: string, message: Omit<Message, 'timestamp'>): Promise<Message> {
  const response = await fetch(`${API_BASE_URL}/channels/${channelName}/messages`, createFetchOptions({
    method: 'POST',
    body: JSON.stringify(message),
  }));
  
  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unknown error');
    throw new Error(`failed to post message to ${channelName}: ${response.status} - ${errorText}`);
  }
  
  return response.json();
}

export async function getBoards(): Promise<Board[]> {
  const response = await fetch(`${API_BASE_URL}/boards`, createFetchOptions());
  
  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unknown error');
    throw new Error(`failed to fetch boards: ${response.status} - ${errorText}`);
  }
  
  return response.json();
}

export async function getBoardThreads(boardName: string): Promise<Thread[]> {
  const response = await fetch(`${API_BASE_URL}/boards/${boardName}`, createFetchOptions());
  
  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unknown error');
    throw new Error(`failed to fetch threads for board ${boardName}: ${response.status} - ${errorText}`);
  }
  
  return response.json();
}

export async function getThread(boardName: string, threadId: string): Promise<ThreadDetail> {
  const response = await fetch(`${API_BASE_URL}/boards/${boardName}/threads/${threadId}`, createFetchOptions());
  
  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unknown error');
    throw new Error(`failed to fetch thread ${threadId}: ${response.status} - ${errorText}`);
  }
  
  return response.json();
}

export async function createThread(
  boardName: string, 
  title: string, 
  firstMessage: Omit<Message, 'timestamp'>
): Promise<Thread> {
  const response = await fetch(`${API_BASE_URL}/boards/${boardName}/threads`, createFetchOptions({
    method: 'POST',
    body: JSON.stringify({
      title,
      first_message: firstMessage,
    }),
  }));
  
  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unknown error');
    throw new Error(`failed to create thread on board ${boardName}: ${response.status} - ${errorText}`);
  }
  
  return response.json();
}

export async function postThreadMessage(
  boardName: string, 
  threadId: string, 
  message: Omit<Message, 'timestamp'>
): Promise<Message> {
  const response = await fetch(`${API_BASE_URL}/boards/${boardName}/threads/${threadId}/messages`, createFetchOptions({
    method: 'POST',
    body: JSON.stringify(message),
  }));
  
  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unknown error');
    throw new Error(`failed to post message to thread ${threadId}: ${response.status} - ${errorText}`);
  }
  
  return response.json();
}

// monologue api functions
export async function getBots(): Promise<string[]> {
  const response = await fetch(`${API_BASE_URL}/bots`, createFetchOptions());
  
  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unknown error');
    throw new Error(`failed to fetch bots: ${response.status} - ${errorText}`);
  }
  
  return response.json();
}

export async function getBotInfo(botName: string): Promise<BotInfo> {
  const response = await fetch(`${API_BASE_URL}/bots/${botName}`, createFetchOptions());
  
  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unknown error');
    throw new Error(`failed to fetch bot info for ${botName}: ${response.status} - ${errorText}`);
  }
  
  return response.json();
}

export async function getBotMonologue(botName: string): Promise<Monologue> {
  const response = await fetch(`${API_BASE_URL}/bots/${botName}/monologue`, createFetchOptions());
  
  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unknown error');
    throw new Error(`failed to fetch monologue for ${botName}: ${response.status} - ${errorText}`);
  }
  
  return response.json();
}

export async function updateBotMonologueSettings(
  botName: string,
  settings: {
    use_monologue?: boolean;
    debug_mode?: boolean;
    max_thoughts?: number;
  }
): Promise<{ status: string; message: string }> {
  const response = await fetch(`${API_BASE_URL}/bots/${botName}/monologue/settings`, createFetchOptions({
    method: 'PATCH',
    body: JSON.stringify(settings),
  }));
  
  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unknown error');
    throw new Error(`failed to update monologue settings for ${botName}: ${response.status} - ${errorText}`);
  }
  
  return response.json();
}

export async function addBotThought(
  botName: string,
  thought: {
    content: string;
    category?: string;
  }
): Promise<{ status: string; message: string }> {
  const response = await fetch(`${API_BASE_URL}/bots/${botName}/monologue/thoughts`, createFetchOptions({
    method: 'POST',
    body: JSON.stringify(thought),
  }));
  
  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unknown error');
    throw new Error(`failed to add thought for ${botName}: ${response.status} - ${errorText}`);
  }
  
  return response.json();
}

export async function clearBotThoughts(
  botName: string
): Promise<{ status: string; message: string }> {
  const response = await fetch(`${API_BASE_URL}/bots/${botName}/monologue/thoughts`, createFetchOptions({
    method: 'DELETE',
  }));
  
  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unknown error');
    throw new Error(`failed to clear thoughts for ${botName}: ${response.status} - ${errorText}`);
  }
  
  return response.json();
}

export async function clearBotToolConsiderations(
  botName: string
): Promise<{ status: string; message: string }> {
  const response = await fetch(`${API_BASE_URL}/bots/${botName}/monologue/tool-considerations`, createFetchOptions({
    method: 'DELETE',
  }));
  
  if (!response.ok) {
    const errorText = await response.text().catch(() => 'Unknown error');
    throw new Error(`failed to clear tool considerations for ${botName}: ${response.status} - ${errorText}`);
  }
  
  return response.json();
} 