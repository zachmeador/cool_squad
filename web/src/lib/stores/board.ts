import { writable, derived } from 'svelte/store';
import { boardSocket } from './websocket';
import type { WebSocketMessage } from 'svelte-websocket-store';

export interface Board {
  id: string;
  name: string;
  description: string;
}

export interface Thread {
  id: string;
  boardId: string;
  title: string;
  createdBy: string;
  createdAt: string;
  isPinned: boolean;
  tags: string[];
  messageCount: number;
}

export interface ThreadMessage {
  id: string;
  threadId: string;
  content: string;
  sender: string;
  timestamp: string;
  isBot: boolean;
}

// Store for available boards
export const boards = writable<Board[]>([]);

// Store for the current active board
export const currentBoard = writable<string | null>(null);

// Store for threads in the current board
export const threads = writable<Thread[]>([]);

// Store for the current active thread
export const currentThread = writable<string | null>(null);

// Store for messages in the current thread
export const threadMessages = writable<ThreadMessage[]>([]);

// Derived store for the current board object
export const currentBoardObject = derived(
  [boards, currentBoard],
  ([$boards, $currentBoard]) => {
    if (!$currentBoard) return null;
    return $boards.find(board => board.id === $currentBoard) || null;
  }
);

// Derived store for the current thread object
export const currentThreadObject = derived(
  [threads, currentThread],
  ([$threads, $currentThread]) => {
    if (!$currentThread) return null;
    return $threads.find(thread => thread.id === $currentThread) || null;
  }
);

// List all available boards
export function listBoards() {
  boardSocket.update((current: WebSocketMessage) => {
    return {
      ...current,
      data: JSON.stringify({
        type: 'command',
        command: 'list_boards'
      })
    };
  });
}

// View a board's threads
export function viewBoard(boardId: string) {
  currentBoard.set(boardId);
  
  boardSocket.update((current: WebSocketMessage) => {
    return {
      ...current,
      data: JSON.stringify({
        type: 'command',
        command: 'view_board',
        boardId
      })
    };
  });
}

// View a thread's messages
export function viewThread(threadId: string) {
  currentThread.set(threadId);
  
  boardSocket.update((current: WebSocketMessage) => {
    return {
      ...current,
      data: JSON.stringify({
        type: 'command',
        command: 'view_thread',
        threadId
      })
    };
  });
}

// Create a new thread
export function createThread(title: string, content: string) {
  let currentBoardValue: string | null = null;
  
  // Get the current board value
  currentBoard.subscribe(value => {
    currentBoardValue = value;
  })();
  
  if (!currentBoardValue) return;
  
  boardSocket.update((current: WebSocketMessage) => {
    return {
      ...current,
      data: JSON.stringify({
        type: 'command',
        command: 'create_thread',
        boardId: currentBoardValue,
        title,
        content
      })
    };
  });
}

// Reply to a thread
export function replyToThread(content: string) {
  let currentThreadValue: string | null = null;
  
  // Get the current thread value
  currentThread.subscribe(value => {
    currentThreadValue = value;
  })();
  
  if (!currentThreadValue) return;
  
  boardSocket.update((current: WebSocketMessage) => {
    return {
      ...current,
      data: JSON.stringify({
        type: 'command',
        command: 'reply',
        threadId: currentThreadValue,
        content
      })
    };
  });
}

// Process incoming messages from the server
boardSocket.subscribe((value: WebSocketMessage) => {
  if (value && value.type === 'message' && value.data) {
    try {
      const data = JSON.parse(value.data);
      
      if (data.type === 'boards') {
        // Update available boards
        boards.set(data.boards);
      } else if (data.type === 'threads') {
        // Update threads for the current board
        threads.set(data.threads);
      } else if (data.type === 'thread_messages') {
        // Update messages for the current thread
        threadMessages.set(data.messages);
      } else if (data.type === 'thread_created') {
        // Handle new thread creation
        threads.update(t => [...t, data.thread]);
        currentThread.set(data.thread.id);
      } else if (data.type === 'thread_reply') {
        // Handle new reply
        threadMessages.update(msgs => [...msgs, data.message]);
      }
    } catch (error) {
      console.error('Error processing board message:', error);
    }
  }
}); 