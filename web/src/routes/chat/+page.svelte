<script lang="ts">
  import { onMount } from 'svelte';
  import { 
    channels, 
    currentChannel, 
    currentChannelMessages, 
    joinChannel, 
    sendMessage,
    bots
  } from '$lib/stores/chat';
  import { chatConnected } from '$lib/stores/websocket';
  import { marked } from 'marked';
  
  let messageInput = '';
  let channelInput = '';
  let messagesContainer: HTMLElement;
  
  // Auto-scroll to bottom when new messages arrive
  $: if (messagesContainer && $currentChannelMessages) {
    setTimeout(() => {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }, 0);
  }
  
  function handleSendMessage() {
    if (!messageInput.trim()) return;
    
    sendMessage(messageInput);
    messageInput = '';
  }
  
  function handleJoinChannel() {
    if (!channelInput.trim()) return;
    
    joinChannel(channelInput);
    channelInput = '';
  }
  
  function formatTimestamp(timestamp: string) {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
  
  function getInitials(name: string) {
    return name.substring(0, 2).toLowerCase();
  }
  
  function getAvatarColor(name: string) {
    // Generate a consistent color based on the name
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
      hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }
    
    // Convert to hex color
    const c = (hash & 0x00FFFFFF)
      .toString(16)
      .toUpperCase();
    
    return "#" + "00000".substring(0, 6 - c.length) + c;
  }
  
  function isBot(name: string) {
    return $bots.includes(name);
  }
  
  onMount(() => {
    // Join the welcome channel by default
    if (!$currentChannel) {
      joinChannel('welcome');
    }
    
    // Configure marked for security
    marked.setOptions({
      breaks: true,
      gfm: true,
      sanitize: true
    });
  });
</script>

<div class="chat-container">
  <aside class="sidebar">
    <div class="channels-header">
      <h3>channels</h3>
      <div class="connection-status">
        {#if $chatConnected}
          <span class="status connected" title="connected">●</span>
        {:else}
          <span class="status disconnected" title="disconnected">●</span>
        {/if}
      </div>
    </div>
    
    <div class="channel-list">
      {#each $channels as channel}
        <button 
          class="channel-item" 
          class:active={$currentChannel === channel.id}
          on:click={() => joinChannel(channel.id)}
        >
          # {channel.name}
        </button>
      {/each}
    </div>
    
    <div class="join-channel">
      <form on:submit|preventDefault={handleJoinChannel}>
        <input 
          type="text" 
          bind:value={channelInput} 
          placeholder="join channel..." 
        />
        <button type="submit">join</button>
      </form>
    </div>
    
    <div class="bots-list">
      <h3>bots</h3>
      <div class="bot-items">
        {#each $bots as bot}
          <div class="bot-item" style="background-color: {getAvatarColor(bot)}20;">
            <div class="bot-avatar" style="background-color: {getAvatarColor(bot)};">
              {getInitials(bot)}
            </div>
            <span>@{bot}</span>
          </div>
        {/each}
      </div>
    </div>
  </aside>
  
  <main class="chat-main">
    <div class="chat-header">
      {#if $currentChannel}
        <h2># {$currentChannel}</h2>
      {:else}
        <h2>select a channel</h2>
      {/if}
    </div>
    
    <div class="messages" bind:this={messagesContainer}>
      {#if $currentChannelMessages.length === 0}
        <div class="empty-state">
          <p>no messages yet. start the conversation!</p>
          <p class="hint">try mentioning a bot with @botname</p>
        </div>
      {:else}
        {#each $currentChannelMessages as message}
          <div class="message" class:bot-message={isBot(message.sender)}>
            <div class="message-avatar" style="background-color: {getAvatarColor(message.sender)};">
              {getInitials(message.sender)}
            </div>
            <div class="message-bubble">
              <div class="message-header">
                <span class="sender">{message.sender}</span>
                <span class="timestamp">{formatTimestamp(message.timestamp)}</span>
              </div>
              <div class="message-content">
                {@html marked(message.content)}
              </div>
            </div>
          </div>
        {/each}
      {/if}
    </div>
    
    <div class="message-input">
      <form on:submit|preventDefault={handleSendMessage}>
        <input 
          type="text" 
          bind:value={messageInput} 
          placeholder={$currentChannel ? "type a message... (markdown supported)" : "join a channel first"} 
          disabled={!$currentChannel || !$chatConnected}
        />
        <button type="submit" disabled={!$currentChannel || !$chatConnected}>send</button>
      </form>
      {#if !$chatConnected}
        <div class="connection-warning">disconnected from server. reconnecting...</div>
      {/if}
    </div>
  </main>
</div>

<style>
  .chat-container {
    display: flex;
    height: calc(100vh - 120px);
    overflow: hidden;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  }
  
  .sidebar {
    width: 250px;
    background-color: var(--bg-secondary);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
  }
  
  .channels-header {
    padding: 1rem;
    border-bottom: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .connection-status {
    font-size: 0.75rem;
  }
  
  .status {
    font-size: 1rem;
  }
  
  .connected {
    color: var(--success);
  }
  
  .disconnected {
    color: var(--error);
  }
  
  .channel-list {
    flex: 1;
    overflow-y: auto;
    padding: 0.5rem;
  }
  
  .channel-item {
    display: block;
    width: 100%;
    text-align: left;
    padding: 0.5rem;
    background: none;
    border: none;
    border-radius: 4px;
    color: var(--text-primary);
    cursor: pointer;
    margin-bottom: 0.25rem;
    transition: background-color 0.2s;
  }
  
  .channel-item:hover {
    background-color: var(--bg-tertiary);
  }
  
  .channel-item.active {
    background-color: var(--bg-tertiary);
    color: var(--accent-primary);
    font-weight: bold;
  }
  
  .join-channel {
    padding: 0.5rem;
    border-top: 1px solid var(--border);
  }
  
  .join-channel form {
    display: flex;
    gap: 0.5rem;
  }
  
  .join-channel input {
    flex: 1;
  }
  
  .bots-list {
    padding: 0.5rem;
    border-top: 1px solid var(--border);
  }
  
  .bots-list h3 {
    margin-bottom: 0.5rem;
  }
  
  .bot-items {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .bot-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem;
    border-radius: 4px;
    font-size: 0.875rem;
    transition: transform 0.2s;
  }
  
  .bot-item:hover {
    transform: translateX(2px);
  }
  
  .bot-avatar {
    width: 24px;
    height: 24px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.75rem;
    color: white;
    font-weight: bold;
  }
  
  .chat-main {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    background-color: var(--bg-primary);
  }
  
  .chat-header {
    padding: 1rem;
    border-bottom: 1px solid var(--border);
  }
  
  .messages {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
  
  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: var(--text-secondary);
    text-align: center;
  }
  
  .hint {
    font-size: 0.875rem;
    margin-top: 0.5rem;
    opacity: 0.7;
  }
  
  .message {
    display: flex;
    gap: 0.75rem;
    max-width: 85%;
    align-self: flex-start;
  }
  
  .message-avatar {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.875rem;
    color: white;
    font-weight: bold;
    flex-shrink: 0;
  }
  
  .message-bubble {
    background-color: var(--bg-secondary);
    padding: 0.75rem;
    border-radius: 8px;
    border-top-left-radius: 2px;
    flex: 1;
  }
  
  .bot-message {
    align-self: flex-end;
  }
  
  .bot-message .message-bubble {
    background-color: var(--bg-tertiary);
    border-top-left-radius: 8px;
    border-top-right-radius: 2px;
  }
  
  .message-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.5rem;
    font-size: 0.875rem;
  }
  
  .sender {
    font-weight: bold;
    color: var(--accent-primary);
  }
  
  .timestamp {
    color: var(--text-secondary);
  }
  
  .message-content {
    word-break: break-word;
    line-height: 1.4;
  }
  
  .message-content :global(p) {
    margin: 0 0 0.5rem 0;
  }
  
  .message-content :global(p:last-child) {
    margin-bottom: 0;
  }
  
  .message-content :global(pre) {
    background-color: var(--bg-primary);
    padding: 0.5rem;
    border-radius: 4px;
    overflow-x: auto;
    font-size: 0.875rem;
  }
  
  .message-content :global(code) {
    background-color: var(--bg-primary);
    padding: 0.125rem 0.25rem;
    border-radius: 3px;
    font-size: 0.875rem;
  }
  
  .message-input {
    padding: 1rem;
    border-top: 1px solid var(--border);
  }
  
  .message-input form {
    display: flex;
    gap: 0.5rem;
  }
  
  .message-input input {
    flex: 1;
    padding: 0.75rem;
    border-radius: 8px;
  }
  
  .message-input button {
    padding: 0.75rem 1.25rem;
    border-radius: 8px;
  }
  
  .connection-warning {
    color: var(--error);
    font-size: 0.875rem;
    margin-top: 0.5rem;
    text-align: center;
  }
  
  @media (max-width: 768px) {
    .chat-container {
      flex-direction: column;
      height: calc(100vh - 140px);
    }
    
    .sidebar {
      width: 100%;
      height: auto;
      max-height: 200px;
      border-right: none;
      border-bottom: 1px solid var(--border);
    }
    
    .channel-list {
      display: flex;
      overflow-x: auto;
      padding: 0.5rem;
    }
    
    .channel-item {
      white-space: nowrap;
    }
    
    .bot-items {
      flex-direction: row;
      flex-wrap: wrap;
    }
  }
</style> 