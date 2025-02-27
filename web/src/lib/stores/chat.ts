import { writable, derived, get } from 'svelte/store';
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

// Store for notification message
export const notification = writable<{message: string, type: 'info' | 'error' | 'success'} | null>(null);

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

// Show a notification
export function showNotification(message: string, type: 'info' | 'error' | 'success' = 'info') {
  notification.set({ message, type });
  
  // Auto-clear after 3 seconds
  setTimeout(() => {
    notification.set(null);
  }, 3000);
}

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
  
  showNotification(`joined #${channelName}`, 'success');
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
    
    if (command === 'help') {
      // Add a local help message
      const helpMessage: ChatMessage = {
        id: `help-${Date.now()}`,
        channel: currentChannelValue,
        sender: 'system',
        content: `
## available commands:
- \`/join #channel\` - join a channel
- \`/help\` - show this help message

## mentioning bots:
- mention a bot with \`@botname\` to get their attention
- available bots: ${get(bots).join(', ')}

## markdown support:
- **bold**: \`**bold**\`
- *italic*: \`*italic*\`
- \`code\`: \`\`\`code\`\`\`
- [link](https://example.com): \`[link](https://example.com)\`
- lists: \`- item\` or \`1. item\`
        `,
        timestamp: new Date().toISOString(),
        isBot: true
      };
      
      messages.update(msgs => [...msgs, helpMessage]);
      return;
    }
  }
  
  // Check for bot mentions
  const botMentions = content.match(/@(\w+)/g);
  if (botMentions) {
    const mentionedBots = botMentions
      .map(mention => mention.substring(1))
      .filter(bot => get(bots).includes(bot));
    
    if (mentionedBots.length > 0) {
      // Add a local message indicating the bot is being called
      setTimeout(() => {
        mentionedBots.forEach(bot => {
          const typingMessage: ChatMessage = {
            id: `typing-${bot}-${Date.now()}`,
            channel: currentChannelValue!,
            sender: 'system',
            content: `_@${bot} is thinking..._`,
            timestamp: new Date().toISOString(),
            isBot: true
          };
          
          messages.update(msgs => [...msgs, typingMessage]);
        });
      }, 500);
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
  
  // Add a local message immediately for better UX
  const localMessage: ChatMessage = {
    id: `local-${Date.now()}`,
    channel: currentChannelValue,
    sender: 'you',
    content,
    timestamp: new Date().toISOString(),
    isBot: false
  };
  
  messages.update(msgs => [...msgs, localMessage]);
}

// Process incoming message from server
export function processServerMessage(data: any) {
  if (data.type === 'channels') {
    channels.set(data.channels);
  } else if (data.type === 'message') {
    // Check if this is a duplicate of a local message
    const isDuplicate = get(messages).some((msg: ChatMessage) => 
      msg.sender === 'you' && 
      msg.content === data.content &&
      msg.channel === data.channel &&
      new Date(msg.timestamp).getTime() > Date.now() - 5000
    );
    
    if (!isDuplicate) {
      const newMessage: ChatMessage = {
        id: data.id || `server-${Date.now()}`,
        channel: data.channel,
        sender: data.sender,
        content: data.content,
        timestamp: data.timestamp || new Date().toISOString(),
        isBot: data.isBot || false
      };
      
      // Remove any typing indicators for this bot
      messages.update(msgs => {
        const filtered = msgs.filter(msg => 
          !(msg.sender === 'system' && 
            msg.content.includes(`@${data.sender} is thinking`))
        );
        return [...filtered, newMessage];
      });
    }
  }
}

// Helper to get all messages for a channel
export function getChannelMessages(channelName: string): ChatMessage[] {
  return get(messages).filter((msg: ChatMessage) => msg.channel === channelName);
}

// Initialize the chat store
chatSocket.subscribe((value: WebSocketMessage) => {
  if (value && value.type === 'message' && value.data) {
    try {
      const data = JSON.parse(value.data);
      processServerMessage(data);
    } catch (e) {
      console.error('Failed to parse message:', e);
    }
  }
}); 