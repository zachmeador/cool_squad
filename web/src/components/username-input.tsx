'use client';

import { useState } from 'react';
import { useUser } from '@/lib/user-context';

export function UsernameInput() {
  const { username, setUsername } = useUser();
  const [inputValue, setInputValue] = useState(username);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputValue.trim()) {
      setUsername(inputValue.trim());
    }
  };

  if (username) {
    return (
      <div className="flex items-center gap-2 text-sm">
        <span>chatting as:</span>
        <span className="font-bold">{username}</span>
        <button 
          onClick={() => setUsername('')}
          className="text-xs px-2 py-1 bg-gray-700 text-gray-200 rounded hover:bg-gray-600"
        >
          change
        </button>
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-2 w-full">
      <label htmlFor="username" className="text-sm">
        choose a username to start chatting
      </label>
      <div className="flex gap-2">
        <input
          id="username"
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded text-gray-200"
          placeholder="username"
          autoComplete="off"
        />
        <button 
          type="submit"
          disabled={!inputValue.trim()}
          className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50 hover:bg-blue-700"
        >
          set
        </button>
      </div>
    </form>
  );
} 