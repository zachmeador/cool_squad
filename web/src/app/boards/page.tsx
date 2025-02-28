'use client';

import { useState, useEffect } from 'react';
import { useUser } from '@/lib/user-context';
import { useBoardSSE } from '@/lib/sse';
import { getBoards } from '@/lib/api';
import { Thread } from '@/lib/api';

export default function BoardsPage() {
  const { username, isLoggedIn } = useUser();
  const [boards, setBoards] = useState<{id: string, name: string, description: string}[]>([]);
  const [currentBoard, setCurrentBoard] = useState<string>('general');
  const [showNewThreadForm, setShowNewThreadForm] = useState(false);
  const [threadTitle, setThreadTitle] = useState('');
  const [threadContent, setThreadContent] = useState('');
  const [replyContent, setReplyContent] = useState('');
  
  const { 
    connected, 
    threads, 
    currentThread, 
    viewThread, 
    createThread, 
    replyToThread 
  } = useBoardSSE(
    currentBoard,
    username || 'guest'
  );
  
  // fetch available boards
  useEffect(() => {
    const fetchBoards = async () => {
      try {
        const boardList = await getBoards();
        setBoards(boardList);
      } catch (error) {
        console.error('failed to fetch boards:', error);
      }
    };
    
    fetchBoards();
  }, []);
  
  const handleCreateThread = (e: React.FormEvent) => {
    e.preventDefault();
    if (!threadTitle.trim() || !threadContent.trim() || !isLoggedIn) return;
    
    createThread(threadTitle, threadContent);
    setThreadTitle('');
    setThreadContent('');
    setShowNewThreadForm(false);
  };
  
  const handleReplyToThread = (e: React.FormEvent) => {
    e.preventDefault();
    if (!replyContent.trim() || !isLoggedIn || !currentThread) return;
    
    replyToThread(replyContent);
    setReplyContent('');
  };
  
  const formatDate = (timestamp: number) => {
    const date = new Date(timestamp * 1000);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };
  
  if (!isLoggedIn) {
    return (
      <div className="flex flex-col items-center justify-center h-[70vh]">
        <div className="bg-yellow-900 border-l-4 border-yellow-600 text-yellow-200 p-4 mb-6">
          <p>please set a username to view boards</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-4 gap-4 h-[80vh]">
      {/* sidebar */}
      <div className="bg-gray-800 p-4 rounded md:col-span-1 flex flex-col">
        <div className="flex justify-between items-center mb-4">
          <h2 className="font-bold">boards</h2>
          <div className="connection-status">
            {connected ? (
              <span className="inline-block w-3 h-3 bg-green-500 rounded-full" title="connected"></span>
            ) : (
              <span className="inline-block w-3 h-3 bg-red-500 rounded-full" title="disconnected"></span>
            )}
          </div>
        </div>
        
        <div className="board-list flex-1 overflow-y-auto">
          {boards.map((board) => (
            <button
              key={board.id}
              className={`w-full text-left px-3 py-2 rounded mb-1 text-sm ${
                currentBoard === board.id 
                  ? 'bg-blue-600 text-white' 
                  : 'hover:bg-gray-700 text-gray-300'
              }`}
              onClick={() => setCurrentBoard(board.id)}
            >
              {board.name}
              {board.description && (
                <p className="text-xs opacity-75 truncate">{board.description}</p>
              )}
            </button>
          ))}
        </div>
      </div>
      
      {/* board content */}
      <div className="bg-gray-800 border border-gray-700 rounded p-4 md:col-span-3 flex flex-col h-full">
        {!currentThread ? (
          // threads list view
          <>
            <div className="mb-4 pb-2 border-b border-gray-700 flex justify-between items-center">
              <h2 className="font-bold">{boards.find(b => b.id === currentBoard)?.name || currentBoard}</h2>
              <button 
                onClick={() => setShowNewThreadForm(!showNewThreadForm)}
                className="bg-blue-600 text-white px-3 py-1 rounded text-sm hover:bg-blue-700"
              >
                {showNewThreadForm ? 'cancel' : 'new thread'}
              </button>
            </div>
            
            {showNewThreadForm && (
              <div className="mb-6 bg-gray-700 p-4 rounded border border-gray-600">
                <h3 className="font-bold mb-3">create new thread</h3>
                <form onSubmit={handleCreateThread}>
                  <div className="mb-3">
                    <label htmlFor="thread-title" className="block text-sm mb-1">title</label>
                    <input
                      id="thread-title"
                      type="text"
                      value={threadTitle}
                      onChange={(e) => setThreadTitle(e.target.value)}
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded text-gray-200"
                      placeholder="thread title..."
                    />
                  </div>
                  <div className="mb-3">
                    <label htmlFor="thread-content" className="block text-sm mb-1">content</label>
                    <textarea
                      id="thread-content"
                      value={threadContent}
                      onChange={(e) => setThreadContent(e.target.value)}
                      className="w-full px-3 py-2 bg-gray-800 border border-gray-600 rounded h-24 text-gray-200"
                      placeholder="write your post..."
                    />
                  </div>
                  <div className="flex justify-end">
                    <button 
                      type="submit"
                      className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
                      disabled={!threadTitle.trim() || !threadContent.trim()}
                    >
                      create thread
                    </button>
                  </div>
                </form>
              </div>
            )}
            
            <div className="flex-1 overflow-y-auto">
              {threads.length === 0 ? (
                <div className="text-center text-gray-500 mt-8">
                  no threads yet in this board
                </div>
              ) : (
                <div className="space-y-2">
                  {threads.map((thread: Thread) => (
                    <div 
                      key={thread.id}
                      className="p-3 border border-gray-700 rounded hover:bg-gray-700 cursor-pointer"
                      onClick={() => viewThread(thread.id)}
                    >
                      <div className="flex justify-between items-start">
                        <h3 className="font-bold">{thread.title}</h3>
                        {thread.pinned && (
                          <span className="bg-yellow-900 text-yellow-200 text-xs px-2 py-1 rounded">
                            pinned
                          </span>
                        )}
                      </div>
                      <div className="text-sm text-gray-400 mt-1">
                        by {thread.author} • {formatDate(thread.created_at)}
                      </div>
                      {thread.tags && thread.tags.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {thread.tags.map((tag, i) => (
                            <span key={i} className="bg-gray-600 text-gray-200 text-xs px-2 py-1 rounded">
                              {tag}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        ) : (
          // thread detail view
          <>
            <div className="mb-4 pb-2 border-b border-gray-700 flex justify-between items-center">
              <button 
                onClick={() => viewThread('')}
                className="text-blue-400 hover:underline text-sm flex items-center"
              >
                ← back to threads
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto mb-4">
              <div className="mb-6">
                <h2 className="text-xl font-bold">{currentThread.title}</h2>
                <div className="text-sm text-gray-400 mt-1">
                  by {currentThread.author} • {formatDate(currentThread.created_at)}
                </div>
              </div>
              
              <div className="space-y-6">
                {currentThread.messages && currentThread.messages.map((msg: any, index: number) => (
                  <div key={index} className="border-b border-gray-700 pb-4">
                    <div className="flex items-baseline">
                      <span className="font-bold mr-2">{msg.author}</span>
                      <span className="text-xs text-gray-500">
                        {formatDate(msg.timestamp)}
                      </span>
                    </div>
                    <div className="mt-2 text-gray-300 whitespace-pre-wrap">{msg.content}</div>
                  </div>
                ))}
              </div>
            </div>
            
            <form onSubmit={handleReplyToThread} className="mt-4">
              <textarea
                value={replyContent}
                onChange={(e) => setReplyContent(e.target.value)}
                className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded h-24 mb-2 text-gray-200"
                placeholder="write your reply..."
              />
              <div className="flex justify-end">
                <button 
                  type="submit"
                  className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
                  disabled={!replyContent.trim()}
                >
                  post reply
                </button>
              </div>
            </form>
          </>
        )}
      </div>
    </div>
  );
} 