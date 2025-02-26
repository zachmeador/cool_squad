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
  
  onMount(() => {
    // Join the welcome channel by default
    if (!$currentChannel) {
      joinChannel('welcome');
    }
  });
</script>

<div class="chat-container">
  <aside class="sidebar">
    <div class="channels-header">
      <h3>channels</h3>
      <div class="connection-status">
        {#if $chatConnected}
          <span class="status connected">●</span>
        {:else}
          <span class="status disconnected">●</span>
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
          <div class="bot-item">@{bot}</div>
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
        </div>
      {:else}
        {#each $currentChannelMessages as message}
          <div class="message" class:bot-message={message.isBot}>
            <div class="message-header">
              <span class="sender">{message.sender}</span>
              <span class="timestamp">{formatTimestamp(message.timestamp)}</span>
            </div>
            <div class="message-content">{message.content}</div>
          </div>
        {/each}
      {/if}
    </div>
    
    <div class="message-input">
      <form on:submit|preventDefault={handleSendMessage}>
        <input 
          type="text" 
          bind:value={messageInput} 
          placeholder={$currentChannel ? "type a message..." : "join a channel first"} 
          disabled={!$currentChannel || !$chatConnected}
        />
        <button type="submit" disabled={!$currentChannel || !$chatConnected}>send</button>
      </form>
    </div>
  </main>
</div>

<style>
  .chat-container {
    display: flex;
    height: calc(100vh - 120px);
    overflow: hidden;
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
    flex-wrap: wrap;
    gap: 0.5rem;
  }
  
  .bot-item {
    background-color: var(--bg-tertiary);
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.875rem;
  }
  
  .chat-main {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
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
  }
  
  .message {
    background-color: var(--bg-secondary);
    padding: 0.75rem;
    border-radius: 8px;
    max-width: 80%;
    align-self: flex-start;
  }
  
  .bot-message {
    background-color: var(--bg-tertiary);
    align-self: flex-end;
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
  }
  
  @media (max-width: 768px) {
    .chat-container {
      flex-direction: column;
      height: calc(100vh - 140px);
    }
    
    .sidebar {
      width: 100%;
      height: 200px;
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
  }
</style> 