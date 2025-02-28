'use client';

import { useState, useEffect, useRef } from 'react';
import { useUser } from '@/lib/user-context';
// import { useChatWebSocket } from '@/lib/websocket';
import { useChatSSE } from '@/lib/sse';
import { getChannels } from '@/lib/api';

export default function ChatPage() {
  const { username, isLoggedIn } = useUser();
  const [channels, setChannels] = useState<string[]>([]);
  const [currentChannel, setCurrentChannel] = useState<string>('welcome');
  const [messageInput, setMessageInput] = useState('');
  const [channelInput, setChannelInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  
  // Replace WebSocket with SSE
  const { connected, messages, sendMessage } = useChatSSE(
    currentChannel,
    username || 'guest'
  );
  
  // fetch available channels
  useEffect(() => {
    const fetchChannels = async () => {
      try {
        const channelList = await getChannels();
        setChannels(channelList);
      } catch (error) {
        console.error('failed to fetch channels:', error);
      }
    };
    
    fetchChannels();
  }, []);
  
  // scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);
  
  const handleSendMessage = (e: React.FormEvent) => {
    e.preventDefault();
    if (!messageInput.trim() || !isLoggedIn) return;
    
    sendMessage(messageInput);
    setMessageInput('');
  };
  
  const handleJoinChannel = (e: React.FormEvent) => {
    e.preventDefault();
    if (!channelInput.trim()) return;
    
    const channelName = channelInput.startsWith('#') 
      ? channelInput.substring(1) 
      : channelInput;
    
    setCurrentChannel(channelName);
    setChannelInput('');
  };
  
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };
  
  const getAvatarColor = (name: string) => {
    // generate a consistent color based on the name
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
      hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }
    
    // convert to hex color
    const c = (hash & 0x00FFFFFF)
      .toString(16)
      .toUpperCase();
    
    return "#" + "00000".substring(0, 6 - c.length) + c;
  };
  
  const isBot = (name: string) => {
    const bots = ['sage', 'teacher', 'researcher', 'curator', 'ole_scrappy', 'normie'];
    return bots.includes(name);
  };
  
  if (!isLoggedIn) {
    return (
      <div className="flex flex-col items-center justify-center h-[70vh]">
        <div className="bg-yellow-900 border-l-4 border-yellow-600 text-yellow-200 p-4 mb-6">
          <p>please set a username to start chatting</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 h-[80vh]">
      {/* sidebar */}
      <div className="bg-gray-800 p-4 rounded md:col-span-1 flex flex-col">
        <div className="flex justify-between items-center mb-4">
          <h2 className="font-bold">channels</h2>
          <div className="connection-status">
            {connected ? (
              <span className="inline-block w-3 h-3 bg-green-500 rounded-full" title="connected"></span>
            ) : (
              <span className="inline-block w-3 h-3 bg-red-500 rounded-full" title="disconnected"></span>
            )}
          </div>
        </div>
        
        <div className="mb-4">
          <form onSubmit={handleJoinChannel} className="flex gap-2">
            <input
              type="text"
              value={channelInput}
              onChange={(e) => setChannelInput(e.target.value)}
              placeholder="join channel..."
              className="flex-1 px-2 py-1 border bg-gray-700 border-gray-600 rounded text-sm text-gray-200"
            />
            <button 
              type="submit"
              className="bg-blue-600 text-white px-2 py-1 rounded text-sm hover:bg-blue-700"
              disabled={!channelInput.trim()}
            >
              join
            </button>
          </form>
        </div>
        
        <div className="channel-list flex-1 overflow-y-auto">
          {channels.map((channel) => (
            <button
              key={channel}
              className={`w-full text-left px-3 py-2 rounded mb-1 text-sm ${
                currentChannel === channel 
                  ? 'bg-blue-600 text-white' 
                  : 'hover:bg-gray-700 text-gray-300'
              }`}
              onClick={() => setCurrentChannel(channel)}
            >
              #{channel}
            </button>
          ))}
        </div>
      </div>
      
      {/* chat area */}
      <div className="bg-gray-800 border border-gray-700 rounded p-4 md:col-span-3 flex flex-col h-full">
        <div className="mb-4 pb-2 border-b border-gray-700">
          <h2 className="font-bold">#{currentChannel}</h2>
        </div>
        
        <div className="flex-1 overflow-y-auto mb-4">
          {messages.length === 0 ? (
            <div className="text-center text-gray-500 mt-8">
              no messages yet in #{currentChannel}
            </div>
          ) : (
            <div className="space-y-4">
              {messages.map((msg, index) => (
                <div key={index} className="flex items-start">
                  <div 
                    className="w-8 h-8 rounded-full flex items-center justify-center text-white mr-3"
                    style={{ backgroundColor: getAvatarColor(msg.author) }}
                  >
                    {msg.author.substring(0, 2).toLowerCase()}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-baseline">
                      <span className={`font-bold mr-2 ${isBot(msg.author) ? 'text-purple-400' : ''}`}>
                        {msg.author}
                      </span>
                      <span className="text-xs text-gray-500">
                        {formatTimestamp(msg.timestamp)}
                      </span>
                    </div>
                    <div className="mt-1 text-gray-300 whitespace-pre-wrap">
                      {msg.content}
                    </div>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>
        
        <form onSubmit={handleSendMessage} className="flex gap-2">
          <input
            type="text"
            value={messageInput}
            onChange={(e) => setMessageInput(e.target.value)}
            placeholder={`message #${currentChannel}...`}
            className="flex-1 px-3 py-2 bg-gray-700 border border-gray-600 rounded text-gray-200"
          />
          <button 
            type="submit"
            className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
            disabled={!messageInput.trim()}
          >
            send
          </button>
        </form>
      </div>
    </div>
  );
} 