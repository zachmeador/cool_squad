'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useUser } from '@/lib/user-context';
import { UsernameInput } from './username-input';

export default function Navigation() {
  const pathname = usePathname();
  const { username, isLoggedIn } = useUser();
  
  const isActive = (path: string) => {
    if (path === '/' && pathname === '/') return true;
    if (path !== '/' && pathname.startsWith(path)) return true;
    return false;
  };
  
  return (
    <nav className="bg-gray-900 border-b border-gray-800 py-4">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center">
          <div className="flex items-center">
            <Link href="/" className="text-xl font-bold text-white mr-8">
              cool_squad
            </Link>
            
            <div className="hidden md:flex space-x-4">
              <Link 
                href="/" 
                className={`px-3 py-2 rounded-md text-sm ${
                  isActive('/') 
                    ? 'bg-gray-700 text-white' 
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
              >
                home
              </Link>
              <Link 
                href="/chat" 
                className={`px-3 py-2 rounded-md text-sm ${
                  isActive('/chat') 
                    ? 'bg-gray-700 text-white' 
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
              >
                chat
              </Link>
              <Link 
                href="/boards" 
                className={`px-3 py-2 rounded-md text-sm ${
                  isActive('/boards') 
                    ? 'bg-gray-700 text-white' 
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
              >
                boards
              </Link>
              <Link 
                href="/bots" 
                className={`px-3 py-2 rounded-md text-sm ${
                  isActive('/bots') 
                    ? 'bg-gray-700 text-white' 
                    : 'text-gray-300 hover:bg-gray-700 hover:text-white'
                }`}
              >
                bots
              </Link>
            </div>
          </div>
          
          <div className="flex items-center">
            <UsernameInput />
          </div>
        </div>
      </div>
    </nav>
  );
} 