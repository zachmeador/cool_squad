'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { getBots } from '@/lib/api';
import Link from 'next/link';

export default function BotsPage() {
  const [bots, setBots] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const fetchBots = async () => {
      try {
        const botList = await getBots();
        setBots(botList);
      } catch (error) {
        console.error('failed to fetch bots:', error);
      } finally {
        setLoading(false);
      }
    };
    
    fetchBots();
  }, []);

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

  if (loading) {
    return (
      <div className="flex justify-center items-center h-[70vh]">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-6">bots</h1>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {bots.map((bot) => (
          <Link 
            href={`/bots/${bot}`} 
            key={bot}
            className="bg-gray-800 border border-gray-700 rounded-lg p-4 hover:bg-gray-700 transition-colors"
          >
            <div className="flex items-center">
              <div 
                className="w-12 h-12 rounded-full flex items-center justify-center text-white mr-4"
                style={{ backgroundColor: getAvatarColor(bot) }}
              >
                {bot.substring(0, 2).toLowerCase()}
              </div>
              <div>
                <h2 className="text-lg font-semibold text-purple-400">{bot}</h2>
                <p className="text-gray-400 text-sm">view monologue</p>
              </div>
            </div>
          </Link>
        ))}
      </div>
      
      {bots.length === 0 && (
        <div className="text-center text-gray-500 mt-8">
          no bots available
        </div>
      )}
    </div>
  );
} 