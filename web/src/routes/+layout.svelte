<!-- Main layout component -->
<script lang="ts">
  import { page } from '$app/stores';
  import { chatConnected, boardConnected } from '$lib/stores/websocket';
  import '../app.css';
  import { notification } from '$lib/stores/chat';
  import { fade } from 'svelte/transition';
  
  // Navigation items
  const navItems = [
    { path: '/', label: 'home' },
    { path: '/chat', label: 'chat' },
    { path: '/board', label: 'board' },
    { path: '/settings', label: 'settings' }
  ];
</script>

<div class="app">
  <header>
    <div class="container header-container">
      <div class="logo">
        <a href="/">cool_squad</a>
        <span class="version">v0.1.0</span>
      </div>
      
      <nav>
        <ul>
          {#each navItems as item}
            <li class:active={$page.url.pathname === item.path}>
              <a href={item.path}>{item.label}</a>
            </li>
          {/each}
        </ul>
      </nav>
    </div>
  </header>
  
  <main>
    <div class="container">
      <slot />
    </div>
  </main>
  
  {#if $notification}
    <div class="notification {$notification.type}" transition:fade={{ duration: 200 }}>
      {$notification.message}
    </div>
  {/if}
  
  <footer>
    <div class="container">
      <p>cool_squad &copy; {new Date().getFullYear()} - <a href="https://github.com/yourusername/cool_squad" target="_blank" rel="noopener noreferrer">github</a></p>
    </div>
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
    background-color: var(--bg-secondary);
    border-bottom: 1px solid var(--border);
    padding: 1rem 0;
  }
  
  .header-container {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }
  
  .logo {
    font-weight: bold;
    font-size: 1.25rem;
    display: flex;
    align-items: center;
  }
  
  .logo a {
    color: var(--accent-primary);
    text-decoration: none;
  }
  
  .version {
    font-size: 0.75rem;
    color: var(--text-secondary);
    margin-left: 0.5rem;
  }
  
  nav ul {
    display: flex;
    list-style: none;
    margin: 0;
    padding: 0;
    gap: 1.5rem;
  }
  
  nav a {
    color: var(--text-primary);
    text-decoration: none;
    font-size: 0.875rem;
    text-transform: lowercase;
    transition: color 0.2s;
  }
  
  nav a:hover {
    color: var(--accent-primary);
  }
  
  nav li.active a {
    color: var(--accent-primary);
    font-weight: bold;
  }
  
  main {
    flex: 1;
    padding: 2rem 0;
  }
  
  .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 1rem;
  }
  
  footer {
    background-color: var(--bg-secondary);
    border-top: 1px solid var(--border);
    padding: 1rem 0;
    font-size: 0.875rem;
    color: var(--text-secondary);
  }
  
  footer a {
    color: var(--accent-primary);
    text-decoration: none;
  }
  
  .notification {
    position: fixed;
    bottom: 2rem;
    right: 2rem;
    padding: 0.75rem 1.25rem;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    font-size: 0.875rem;
    z-index: 1000;
    max-width: 300px;
  }
  
  .notification.info {
    background-color: var(--bg-tertiary);
    color: var(--text-primary);
  }
  
  .notification.success {
    background-color: var(--success);
    color: white;
  }
  
  .notification.error {
    background-color: var(--error);
    color: white;
  }
  
  @media (max-width: 768px) {
    .header-container {
      flex-direction: column;
      gap: 1rem;
    }
    
    nav ul {
      gap: 1rem;
    }
  }
</style> 