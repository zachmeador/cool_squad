'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { UsernameInput } from './username-input';

export function Navigation() {
  const pathname = usePathname();
  
  const isActive = (path: string) => {
    return pathname === path;
  };
  
  return (
    <nav className="bg-gray-900 text-white p-4">
      <div className="container mx-auto flex flex-col md:flex-row justify-between items-center">
        <div className="flex items-center mb-4 md:mb-0">
          <Link href="/" className="text-xl font-bold">
            cool_squad
          </Link>
          <span className="ml-2 text-xs bg-gray-800 px-2 py-1 rounded">v0.1.0</span>
        </div>
        
        <div className="flex flex-col md:flex-row items-center gap-6">
          <div className="flex space-x-4">
            <Link 
              href="/" 
              className={`hover:text-blue-300 ${isActive('/') ? 'text-blue-400' : ''}`}
            >
              home
            </Link>
            <Link 
              href="/chat" 
              className={`hover:text-blue-300 ${isActive('/chat') ? 'text-blue-400' : ''}`}
            >
              chat
            </Link>
            <Link 
              href="/boards" 
              className={`hover:text-blue-300 ${isActive('/boards') ? 'text-blue-400' : ''}`}
            >
              boards
            </Link>
          </div>
          
          <div className="bg-gray-800 px-3 py-2 rounded mt-4 md:mt-0">
            <UsernameInput />
          </div>
        </div>
      </div>
    </nav>
  );
} 