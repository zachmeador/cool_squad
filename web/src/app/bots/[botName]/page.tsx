'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getBotInfo, getBotMonologue, updateBotMonologueSettings, clearBotThoughts } from '@/lib/api';
import { BotInfo, Monologue, Thought, ToolConsideration } from '@/lib/api';
import Link from 'next/link';

export default function BotPage({ params }: { params: { botName: string } }) {
  const [botInfo, setBotInfo] = useState<BotInfo | null>(null);
  const [monologue, setMonologue] = useState<Monologue | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'thoughts' | 'tools'>('thoughts');
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();
  const { botName } = params;

  useEffect(() => {
    const fetchBotData = async () => {
      try {
        setLoading(true);
        const [info, mono] = await Promise.all([
          getBotInfo(botName),
          getBotMonologue(botName).catch(() => null)
        ]);
        setBotInfo(info);
        setMonologue(mono);
      } catch (error) {
        console.error(`failed to fetch data for bot ${botName}:`, error);
        setError(`failed to load bot data: ${error}`);
      } finally {
        setLoading(false);
      }
    };
    
    fetchBotData();
  }, [botName]);

  const refreshMonologue = async () => {
    try {
      const mono = await getBotMonologue(botName);
      setMonologue(mono);
    } catch (error) {
      console.error(`failed to refresh monologue for ${botName}:`, error);
    }
  };

  const handleToggleMonologue = async () => {
    if (!botInfo) return;
    
    try {
      await updateBotMonologueSettings(botName, {
        use_monologue: !botInfo.use_monologue
      });
      
      // Update local state
      setBotInfo({
        ...botInfo,
        use_monologue: !botInfo.use_monologue
      });
      
      // Refresh monologue data if enabled
      if (!botInfo.use_monologue) {
        refreshMonologue();
      }
    } catch (error) {
      console.error(`failed to toggle monologue for ${botName}:`, error);
    }
  };

  const handleToggleDebugMode = async () => {
    if (!botInfo) return;
    
    try {
      await updateBotMonologueSettings(botName, {
        debug_mode: !botInfo.debug_mode
      });
      
      // Update local state
      setBotInfo({
        ...botInfo,
        debug_mode: !botInfo.debug_mode
      });
    } catch (error) {
      console.error(`failed to toggle debug mode for ${botName}:`, error);
    }
  };

  const handleClearThoughts = async () => {
    if (!confirm('are you sure you want to clear all thoughts?')) return;
    
    try {
      await clearBotThoughts(botName);
      refreshMonologue();
    } catch (error) {
      console.error(`failed to clear thoughts for ${botName}:`, error);
    }
  };

  const formatTimestamp = (timestamp: number) => {
    const date = new Date(timestamp * 1000);
    return date.toLocaleString();
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      'input': 'bg-blue-600',
      'reasoning': 'bg-purple-600',
      'response': 'bg-green-600',
      'tool_selection': 'bg-yellow-600',
      'tool_use': 'bg-orange-600',
      'tool_result': 'bg-teal-600',
      'final_response': 'bg-indigo-600',
      'autonomous': 'bg-pink-600',
      'error': 'bg-red-600',
      'general': 'bg-gray-600'
    };
    
    return colors[category] || 'bg-gray-600';
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-[70vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error || !botInfo) {
    return (
      <div className="container mx-auto p-4">
        <div className="bg-red-900 border-l-4 border-red-600 text-red-200 p-4 mb-6">
          <p>{error || `bot ${botName} not found`}</p>
        </div>
        <Link href="/bots" className="text-blue-400 hover:underline">
          ← back to bots
        </Link>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      <div className="mb-4">
        <Link href="/bots" className="text-blue-400 hover:underline">
          ← back to bots
        </Link>
      </div>
      
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6 mb-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-4">
          <h1 className="text-2xl font-bold text-purple-400 mb-2 md:mb-0">{botName}</h1>
          
          <div className="flex flex-wrap gap-2">
            <button
              onClick={handleToggleMonologue}
              className={`px-3 py-1 rounded text-sm ${
                botInfo.use_monologue 
                  ? 'bg-green-600 hover:bg-green-700' 
                  : 'bg-red-600 hover:bg-red-700'
              }`}
            >
              monologue: {botInfo.use_monologue ? 'on' : 'off'}
            </button>
            
            <button
              onClick={handleToggleDebugMode}
              className={`px-3 py-1 rounded text-sm ${
                botInfo.debug_mode 
                  ? 'bg-green-600 hover:bg-green-700' 
                  : 'bg-gray-600 hover:bg-gray-700'
              }`}
            >
              debug mode: {botInfo.debug_mode ? 'on' : 'off'}
            </button>
            
            <button
              onClick={refreshMonologue}
              className="bg-blue-600 hover:bg-blue-700 px-3 py-1 rounded text-sm"
            >
              refresh
            </button>
            
            <button
              onClick={handleClearThoughts}
              className="bg-red-600 hover:bg-red-700 px-3 py-1 rounded text-sm"
            >
              clear thoughts
            </button>
          </div>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <p className="text-gray-400 mb-1">personality:</p>
            <p className="bg-gray-700 p-2 rounded">{botInfo.personality}</p>
          </div>
          
          <div>
            <p className="text-gray-400 mb-1">model:</p>
            <p className="bg-gray-700 p-2 rounded">{botInfo.provider} / {botInfo.model}</p>
          </div>
        </div>
        
        {!botInfo.use_monologue && (
          <div className="bg-yellow-900 border-l-4 border-yellow-600 text-yellow-200 p-4 mt-4">
            <p>monologue is currently disabled for this bot. enable it to see thoughts.</p>
          </div>
        )}
      </div>
      
      {botInfo.use_monologue && monologue && (
        <div className="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
          <div className="flex border-b border-gray-700">
            <button
              className={`px-4 py-2 flex-1 ${activeTab === 'thoughts' ? 'bg-gray-700 font-medium' : ''}`}
              onClick={() => setActiveTab('thoughts')}
            >
              thoughts ({monologue.thoughts.length})
            </button>
            <button
              className={`px-4 py-2 flex-1 ${activeTab === 'tools' ? 'bg-gray-700 font-medium' : ''}`}
              onClick={() => setActiveTab('tools')}
            >
              tool considerations ({Object.keys(monologue.tool_considerations).length})
            </button>
          </div>
          
          <div className="p-4">
            {activeTab === 'thoughts' && (
              <div className="space-y-4">
                {monologue.thoughts.length === 0 ? (
                  <p className="text-gray-500 text-center py-4">no thoughts recorded yet</p>
                ) : (
                  monologue.thoughts.slice().reverse().map((thought, index) => (
                    <div key={index} className="border border-gray-700 rounded-lg overflow-hidden">
                      <div className="flex items-center px-3 py-2 border-b border-gray-700">
                        <span className={`${getCategoryColor(thought.category)} px-2 py-1 rounded text-xs mr-2`}>
                          {thought.category}
                        </span>
                        <span className="text-xs text-gray-400 ml-auto">
                          {formatTimestamp(thought.timestamp)}
                        </span>
                      </div>
                      <div className="p-3 whitespace-pre-wrap">
                        {thought.content}
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
            
            {activeTab === 'tools' && (
              <div className="space-y-4">
                {Object.keys(monologue.tool_considerations).length === 0 ? (
                  <p className="text-gray-500 text-center py-4">no tool considerations recorded yet</p>
                ) : (
                  Object.entries(monologue.tool_considerations).map(([name, tool]) => (
                    <div key={name} className="border border-gray-700 rounded-lg overflow-hidden">
                      <div className="flex items-center justify-between px-3 py-2 border-b border-gray-700 bg-gray-750">
                        <div className="flex items-center">
                          <span className="font-medium mr-2">{name}</span>
                          <span className={`px-2 py-1 rounded text-xs ${
                            tool.relevance_score > 0.7 ? 'bg-green-600' :
                            tool.relevance_score > 0.4 ? 'bg-yellow-600' : 'bg-red-600'
                          }`}>
                            relevance: {tool.relevance_score.toFixed(2)}
                          </span>
                        </div>
                        <span className="text-xs text-gray-400">
                          {formatTimestamp(tool.timestamp)}
                        </span>
                      </div>
                      <div className="p-3 whitespace-pre-wrap">
                        {tool.reasoning}
                      </div>
                    </div>
                  ))
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
} 