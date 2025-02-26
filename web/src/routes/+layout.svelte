<!-- Main layout component -->
<script lang="ts">
  import { page } from '$app/stores';
  import { chatConnected, boardConnected } from '$lib/stores/websocket';
  import '../app.css';
</script>

<div class="app">
  <header>
    <div class="logo">cool_squad</div>
    <nav>
      <a href="/" class:active={$page.url.pathname === '/'}>home</a>
      <a href="/chat" class:active={$page.url.pathname.startsWith('/chat')}>
        chat
        {#if $chatConnected}
          <span class="status connected">●</span>
        {:else}
          <span class="status disconnected">●</span>
        {/if}
      </a>
      <a href="/board" class:active={$page.url.pathname.startsWith('/board')}>
        board
        {#if $boardConnected}
          <span class="status connected">●</span>
        {:else}
          <span class="status disconnected">●</span>
        {/if}
      </a>
      <a href="/settings" class:active={$page.url.pathname.startsWith('/settings')}>settings</a>
    </nav>
  </header>

  <main>
    <slot />
  </main>

  <footer>
    <p>cool_squad - chat with your robot friends :)</p>
  </footer>
</div>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', sans-serif;
    background-color: #121212;
    color: #e0e0e0;
  }

  .app {
    display: flex;
    flex-direction: column;
    min-height: 100vh;
  }

  header {
    background-color: #1e1e1e;
    padding: 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #333;
  }

  .logo {
    font-size: 1.5rem;
    font-weight: bold;
    color: #bb86fc;
  }

  nav {
    display: flex;
    gap: 1.5rem;
  }

  nav a {
    color: #e0e0e0;
    text-decoration: none;
    padding: 0.5rem;
    border-radius: 4px;
    transition: background-color 0.2s;
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }

  nav a:hover {
    background-color: #333;
  }

  nav a.active {
    color: #bb86fc;
    font-weight: bold;
  }

  .status {
    font-size: 0.75rem;
  }

  .connected {
    color: #4caf50;
  }

  .disconnected {
    color: #f44336;
  }

  main {
    flex: 1;
    padding: 1rem;
    max-width: 1200px;
    width: 100%;
    margin: 0 auto;
  }

  footer {
    background-color: #1e1e1e;
    padding: 1rem;
    text-align: center;
    border-top: 1px solid #333;
    font-size: 0.875rem;
    color: #888;
  }
</style> 