import { writable, derived } from 'svelte/store';
import { chatSocket } from './websocket';
import type { WebSocketMessage } from 'svelte-websocket-store';

export interface ChatMessage {
  id: string;
  channel: string;
  sender: string;
  content: string;
  timestamp: string;
  isBot: boolean;
}

export interface Channel {
  id: string;
  name: string;
  description: string;
}

// Store for available channels
export const channels = writable<Channel[]>([]);

// Store for the current active channel
export const currentChannel = writable<string | null>(null);

// Store for all messages
export const messages = writable<ChatMessage[]>([]);

// Derived store for messages in the current channel
export const currentChannelMessages = derived(
  [messages, currentChannel],
  ([$messages, $currentChannel]) => {
    if (!$currentChannel) return [];
    return $messages.filter(msg => msg.channel === $currentChannel);
  }
);

// Store for available bots
export const bots = writable<string[]>([
  'sage',
  'teacher',
  'researcher',
  'curator',
  'ole_scrappy'
]);

// Join a channel
export function joinChannel(channelName: string) {
  if (channelName.startsWith('#')) {
    channelName = channelName.substring(1);
  }
  
  currentChannel.set(channelName);
  
  // Send join command to server
  chatSocket.update((current: WebSocketMessage) => {
    return { 
      ...current, 
      data: JSON.stringify({ 
        type: 'command', 
        command: 'join', 
        channel: channelName 
      }) 
    };
  });
}

// Send a message to the current channel
export function sendMessage(content: string) {
  let currentChannelValue: string | null = null;
  
  // Get the current channel value
  currentChannel.subscribe(value => {
    currentChannelValue = value;
  })();
  
  if (!currentChannelValue) return;
  
  // Check if it's a command
  if (content.startsWith('/')) {
    const parts = content.substring(1).split(' ');
    const command = parts[0];
    
    if (command === 'join' && parts.length > 1) {
      joinChannel(parts[1]);
      return;
    }
  }
  
  // Send message to server
  chatSocket.update((current: WebSocketMessage) => {
    return { 
      ...current, 
      data: JSON.stringify({ 
        type: 'message', 
        channel: currentChannelValue, 
        content 
      }) 
    };
  });
}

// Process incoming messages from the server
chatSocket.subscribe((value: WebSocketMessage) => {
  if (value && value.type === 'message' && value.data) {
    try {
      const data = JSON.parse(value.data);
      
      if (data.type === 'channels') {
        // Update available channels
        channels.set(data.channels);
      } else if (data.type === 'message') {
        // Add new message
        messages.update(msgs => [
          ...msgs, 
          {
            id: data.id || `msg-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`,
            channel: data.channel,
            sender: data.sender,
            content: data.content,
            timestamp: data.timestamp || new Date().toISOString(),
            isBot: data.isBot || false
          }
        ]);
      }
    } catch (error) {
      console.error('Error processing message:', error);
    }
  }
}); 