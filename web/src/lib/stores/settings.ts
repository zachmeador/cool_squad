import { writable } from 'svelte/store';
import { browser } from '$app/environment';

// Interface for user settings
export interface UserSettings {
  username: string;
  apiKeys: {
    openai?: string;
    anthropic?: string;
    cohere?: string;
    replicate?: string;
  };
  dataDirectory: string;
}

// Default settings
const defaultSettings: UserSettings = {
  username: 'user',
  apiKeys: {},
  dataDirectory: '_data'
};

// Load settings from localStorage if available
const storedSettings = browser ? 
  JSON.parse(localStorage.getItem('cool_squad_settings') || 'null') : 
  null;

// Create the settings store
export const settings = writable<UserSettings>(storedSettings || defaultSettings);

// Save settings to localStorage when they change
if (browser) {
  settings.subscribe(value => {
    localStorage.setItem('cool_squad_settings', JSON.stringify(value));
  });
}

// Update a specific setting
export function updateSetting<K extends keyof UserSettings>(
  key: K, 
  value: UserSettings[K]
) {
  settings.update(s => ({ ...s, [key]: value }));
}

// Update an API key
export function updateApiKey(provider: keyof UserSettings['apiKeys'], key: string) {
  settings.update(s => ({
    ...s,
    apiKeys: {
      ...s.apiKeys,
      [provider]: key
    }
  }));
}

// Clear all API keys
export function clearApiKeys() {
  settings.update(s => ({
    ...s,
    apiKeys: {}
  }));
}

// Reset settings to defaults
export function resetSettings() {
  settings.set(defaultSettings);
} 