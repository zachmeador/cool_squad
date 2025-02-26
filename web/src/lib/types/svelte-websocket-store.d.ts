declare module 'svelte-websocket-store' {
  import type { Writable } from 'svelte/store';
  
  export interface WebSocketMessage {
    type: 'open' | 'close' | 'message' | 'error';
    data?: any;
  }
  
  export function websocketStore(url: string): Writable<WebSocketMessage>;
} 