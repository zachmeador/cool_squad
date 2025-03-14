import { useState, useEffect } from 'react';
import { getChannelBots, addBotToChannel, removeBotFromChannel, getBots } from '@/lib/api';

interface ChannelBotsProps {
  channelName: string;
}

export default function ChannelBots({ channelName }: ChannelBotsProps) {
  const [bots, setBots] = useState<string[]>([]);
  const [availableBots, setAvailableBots] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [newBot, setNewBot] = useState('');
  
  useEffect(() => {
    loadBots();
    loadAvailableBots();
  }, [channelName]);
  
  const loadBots = async () => {
    try {
      setLoading(true);
      setError(null);
      const channelBots = await getChannelBots(channelName);
      setBots(channelBots);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'failed to load bots');
    } finally {
      setLoading(false);
    }
  };

  const loadAvailableBots = async () => {
    try {
      const allBots = await getBots();
      setAvailableBots(allBots);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'failed to load available bots');
    }
  };
  
  const handleAddBot = async (botName: string) => {
    try {
      await addBotToChannel(channelName, botName);
      await loadBots();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'failed to add bot');
    }
  };
  
  const handleRemoveBot = async (botName: string) => {
    // don't allow removing bots from everyone channel
    if (channelName === 'everyone') {
      setError('cannot remove bots from #everyone channel');
      return;
    }
    
    try {
      await removeBotFromChannel(channelName, botName);
      await loadBots();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'failed to remove bot');
    }
  };
  
  if (loading) {
    return <div className="text-gray-400">loading bots...</div>;
  }
  
  return (
    <div className="mt-4">
      <h3 className="text-sm font-semibold mb-2">bots in #{channelName}</h3>
      
      {error && (
        <div className="text-red-400 text-sm mb-2">{error}</div>
      )}
      
      <div className="space-y-2">
        {/* current bots */}
        {bots.map(bot => (
          <div key={bot} className="flex items-center justify-between bg-gray-700 px-2 py-1 rounded">
            <span className="text-sm">@{bot}</span>
            {channelName !== 'everyone' && (
              <button
                onClick={() => handleRemoveBot(bot)}
                className="text-red-400 hover:text-red-300 text-sm"
              >
                remove
              </button>
            )}
          </div>
        ))}
        
        {/* add bot dropdown */}
        {channelName !== 'everyone' && (
          <div className="flex gap-2 mt-4">
            <select
              value={newBot}
              onChange={(e) => setNewBot(e.target.value)}
              className="flex-1 px-2 py-1 bg-gray-700 border border-gray-600 rounded text-sm"
            >
              <option value="">select a bot...</option>
              {availableBots
                .filter(bot => !bots.includes(bot))
                .map(bot => (
                  <option key={bot} value={bot}>@{bot}</option>
                ))
            }
            </select>
            <button
              onClick={() => newBot && handleAddBot(newBot)}
              disabled={!newBot}
              className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700 disabled:opacity-50"
            >
              add
            </button>
          </div>
        )}
      </div>
    </div>
  );
} 