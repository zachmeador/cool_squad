import { writable } from 'svelte/store';
import { websocketStore, type WebSocketMessage } from 'svelte-websocket-store';

// Chat server connection
export const chatSocket = websocketStore('ws://localhost:8765');

// Board server connection
export const boardSocket = websocketStore('ws://localhost:8766');

// Connection status stores
export const chatConnected = writable(false);
export const boardConnected = writable(false);

// Update connection status when websocket state changes
chatSocket.subscribe((value: WebSocketMessage) => {
  if (value && value.type === 'open') {
    chatConnected.set(true);
  } else if (value && value.type === 'close') {
    chatConnected.set(false);
  }
});

boardSocket.subscribe((value: WebSocketMessage) => {
  if (value && value.type === 'open') {
    boardConnected.set(true);
  } else if (value && value.type === 'close') {
    boardConnected.set(false);
  }
});

// Helper functions to send messages
export function sendChatMessage(message: string) {
  chatSocket.update((current: WebSocketMessage) => {
    return { ...current, data: JSON.stringify({ type: 'message', content: message }) };
  });
}

export function sendBoardMessage(message: string) {
  boardSocket.update((current: WebSocketMessage) => {
    return { ...current, data: JSON.stringify({ type: 'message', content: message }) };
  });
} 