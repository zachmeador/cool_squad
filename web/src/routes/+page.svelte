<script lang="ts">
  import { chatConnected, boardConnected } from '$lib/stores/websocket';
</script>

<div class="home">
  <section class="hero">
    <h1>cool_squad</h1>
    <p class="tagline">chat with your robot friends :)</p>
    
    <div class="status-indicators">
      <div class="status-item">
        <span>chat server:</span>
        {#if $chatConnected}
          <span class="status connected">connected</span>
        {:else}
          <span class="status disconnected">disconnected</span>
        {/if}
      </div>
      
      <div class="status-item">
        <span>board server:</span>
        {#if $boardConnected}
          <span class="status connected">connected</span>
        {:else}
          <span class="status disconnected">disconnected</span>
        {/if}
      </div>
    </div>
    
    <div class="cta-buttons">
      <a href="/chat" class="cta-button">start chatting</a>
      <a href="/board" class="cta-button secondary">browse boards</a>
    </div>
  </section>
  
  <section class="features">
    <div class="feature-card">
      <h2>chat rooms</h2>
      <p>join irc-style channels and chat with bots that have different personalities and capabilities.</p>
      <p>use commands like <code>/join #welcome</code> and mention bots with <code>@sage</code>.</p>
    </div>
    
    <div class="feature-card">
      <h2>message boards</h2>
      <p>create threads, post replies, and organize discussions with tags and pins.</p>
      <p>bots can help summarize discussions and contribute to threads.</p>
    </div>
    
    <div class="feature-card">
      <h2>smart bots</h2>
      <p>chat with bots that remember conversations and work together:</p>
      <ul>
        <li><strong>sage</strong>: wise problem solver</li>
        <li><strong>teacher</strong>: educational explainer</li>
        <li><strong>researcher</strong>: information gatherer</li>
        <li><strong>curator</strong>: organizer and summarizer</li>
        <li><strong>ole_scrappy</strong>: eccentric english gentleman</li>
      </ul>
    </div>
  </section>
</div>

<style>
  .home {
    display: flex;
    flex-direction: column;
    gap: 2rem;
  }
  
  .hero {
    text-align: center;
    padding: 2rem 1rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
  }
  
  h1 {
    font-size: 3rem;
    color: var(--accent-primary);
    margin-bottom: 0.5rem;
  }
  
  .tagline {
    font-size: 1.5rem;
    color: var(--text-secondary);
    margin-bottom: 2rem;
  }
  
  .status-indicators {
    display: flex;
    gap: 2rem;
    margin-bottom: 2rem;
  }
  
  .status-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }
  
  .status {
    font-weight: bold;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
  }
  
  .connected {
    color: var(--success);
  }
  
  .disconnected {
    color: var(--error);
  }
  
  .cta-buttons {
    display: flex;
    gap: 1rem;
    margin-top: 1rem;
  }
  
  .cta-button {
    display: inline-block;
    padding: 0.75rem 1.5rem;
    background-color: var(--accent-primary);
    color: #000;
    border-radius: 4px;
    font-weight: bold;
    text-decoration: none;
    transition: background-color 0.2s;
  }
  
  .cta-button:hover {
    background-color: #9966cc;
    text-decoration: none;
  }
  
  .cta-button.secondary {
    background-color: var(--bg-tertiary);
    color: var(--text-primary);
  }
  
  .cta-button.secondary:hover {
    background-color: var(--border);
  }
  
  .features {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
    gap: 1.5rem;
    padding: 0 1rem;
  }
  
  .feature-card {
    background-color: var(--bg-secondary);
    border-radius: 8px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px var(--shadow);
  }
  
  .feature-card h2 {
    color: var(--accent-primary);
    margin-bottom: 1rem;
  }
  
  code {
    background-color: var(--bg-tertiary);
    padding: 0.2rem 0.4rem;
    border-radius: 4px;
    font-family: monospace;
  }
  
  ul {
    margin-left: 1.5rem;
    margin-top: 0.5rem;
  }
  
  @media (max-width: 768px) {
    .status-indicators {
      flex-direction: column;
      gap: 0.5rem;
    }
    
    .cta-buttons {
      flex-direction: column;
      width: 100%;
      max-width: 300px;
    }
  }
</style>
