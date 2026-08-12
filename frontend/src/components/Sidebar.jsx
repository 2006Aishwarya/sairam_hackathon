import React, { useState } from 'react';
import {
  MessageSquare, Database, Sparkles, Plus,
  TrendingUp, Users, Package, PieChart, GitFork, Settings,
  History, Trash2, Clock
} from 'lucide-react';
import SchemaExplorer from './SchemaExplorer';

export default function Sidebar({
  activeTab,
  setActiveTab,
  onSampleClick,
  onNewChat,
  currentSessionId,
  sessions = [],
  onSelectSession,
  onDeleteSession,
  pinnedCount,
  onOpenSettings
}) {
  const [sidebarMode, setSidebarMode] = useState('history'); // 'history' | 'prompts' | 'schema'

  const samplePrompts = [
    {
      category: "Sales Trends",
      icon: <TrendingUp size={15} className="text-indigo-600" />,
      query: "Show me the monthly sales revenue trend over the last year"
    },
    {
      category: "Top Customers",
      icon: <Users size={15} className="text-emerald-600" />,
      query: "Show me our top customers by total amount spent"
    },
    {
      category: "Inventory Health",
      icon: <Package size={15} className="text-amber-600" />,
      query: "Show me low inventory stock items and restock levels"
    },
    {
      category: "Category Share",
      icon: <PieChart size={15} className="text-purple-600" />,
      query: "What is the revenue breakdown across product categories?"
    },
    {
      category: "Fulfillment Pipeline",
      icon: <GitFork size={15} className="text-rose-600" />,
      query: "Create a flowchart showing how orders flow through our system"
    },
    {
      category: "Database ER Diagram",
      icon: <Database size={15} className="text-cyan-600" />,
      query: "Draw me the ER diagram for this database"
    }
  ];

  return (
    <aside className="w-72 bg-white border-r border-slate-200 flex flex-col h-full shrink-0 shadow-sm">
      {/* Brand Header */}
      <div className="p-4 border-b border-slate-100 flex items-center justify-between">
        <div className="flex items-center space-x-2.5">
          <div className="p-2 rounded-2xl bg-gradient-to-br from-indigo-500 via-purple-500 to-emerald-500 text-white shadow-md shadow-indigo-500/20">
            <Sparkles size={18} />
          </div>
          <div>
            <h1 className="font-bold text-sm text-slate-800 leading-tight">Data Companion</h1>
            <span className="text-[11px] text-indigo-600 font-medium">Your AI Analyst</span>
          </div>
        </div>

        <button
          onClick={onNewChat}
          title="New Chat Session"
          className="p-1.5 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-600 border border-slate-200 transition-colors flex items-center space-x-1 text-xs font-semibold"
        >
          <Plus size={15} />
          <span className="hidden sm:inline">New</span>
        </button>
      </div>

      {/* Navigation Tabs */}
      <div className="px-3 pt-3 border-b border-slate-100 pb-3">
        <button
          onClick={() => setActiveTab('chat')}
          className="w-full py-2 rounded-xl text-xs font-semibold flex items-center justify-center space-x-1.5 transition-all bg-indigo-600 text-white shadow-md shadow-indigo-500/25"
        >
          <MessageSquare size={14} />
          <span>Analyze Chat</span>
        </button>
      </div>

      {/* Mode Selector for Sidebar */}
      <div className="p-2.5 flex space-x-1 border-b border-slate-100 bg-slate-50/50 text-xs">
        <button
          onClick={() => setSidebarMode('history')}
          className={`flex-1 py-1 rounded-lg text-[11px] font-semibold transition-colors flex items-center justify-center space-x-1 ${sidebarMode === 'history'
              ? 'bg-white text-indigo-700 shadow-sm border border-slate-200'
              : 'text-slate-500 hover:text-slate-800'
            }`}
        >
          <History size={12} />
          <span>History</span>
        </button>
        <button
          onClick={() => setSidebarMode('prompts')}
          className={`flex-1 py-1 rounded-lg text-[11px] font-semibold transition-colors ${sidebarMode === 'prompts'
              ? 'bg-white text-indigo-700 shadow-sm border border-slate-200'
              : 'text-slate-500 hover:text-slate-800'
            }`}
        >
          Prompts
        </button>
        <button
          onClick={() => setSidebarMode('schema')}
          className={`flex-1 py-1 rounded-lg text-[11px] font-semibold transition-colors ${sidebarMode === 'schema'
              ? 'bg-white text-indigo-700 shadow-sm border border-slate-200'
              : 'text-slate-500 hover:text-slate-800'
            }`}
        >
          Schema
        </button>
      </div>

      {/* Main Sidebar Content */}
      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {sidebarMode === 'history' ? (
          <div className="space-y-2">
            <div className="flex items-center justify-between px-1">
              <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                Saved Chat Sessions
              </span>
              <button
                onClick={onNewChat}
                className="text-[11px] font-semibold text-indigo-600 hover:text-indigo-700 flex items-center space-x-0.5"
              >
                <Plus size={11} />
                <span>New Chat</span>
              </button>
            </div>

            {sessions.length === 0 ? (
              <div className="p-4 text-center text-xs text-slate-400 border border-dashed border-slate-200 rounded-2xl">
                No past chat history yet. Ask a question to save your first session!
              </div>
            ) : (
              sessions.map((sess) => {
                const isActive = sess.session_id === currentSessionId;
                return (
                  <div
                    key={sess.session_id}
                    className={`group relative p-2.5 rounded-2xl border transition-all flex items-start justify-between cursor-pointer ${
                      isActive
                        ? 'bg-indigo-50/90 border-indigo-200 text-indigo-900 shadow-sm'
                        : 'bg-white hover:bg-slate-50 border-slate-200/80 text-slate-700 hover:border-slate-300'
                    }`}
                    onClick={() => {
                      setActiveTab('chat');
                      onSelectSession && onSelectSession(sess.session_id);
                    }}
                  >
                    <div className="flex items-start space-x-2 min-w-0 pr-6">
                      <MessageSquare size={14} className={`shrink-0 mt-0.5 ${isActive ? 'text-indigo-600' : 'text-slate-400'}`} />
                      <div className="min-w-0">
                        <h4 className="text-xs font-bold truncate leading-snug">
                          {sess.title || 'Chat Session'}
                        </h4>
                        <div className="flex items-center space-x-2 text-[10px] text-slate-400 mt-1">
                          <span className="flex items-center space-x-0.5">
                            <Clock size={10} />
                            <span>{sess.updated_at ? sess.updated_at.split(' ')[0] : 'Today'}</span>
                          </span>
                          {sess.message_count !== undefined && (
                            <span>• {sess.message_count} msgs</span>
                          )}
                        </div>
                      </div>
                    </div>

                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        if (confirm("Delete this chat session history?")) {
                          onDeleteSession && onDeleteSession(sess.session_id);
                        }
                      }}
                      title="Delete chat session"
                      className="opacity-0 group-hover:opacity-100 p-1 rounded-lg hover:bg-rose-100 text-rose-600 transition-opacity absolute right-2 top-2"
                    >
                      <Trash2 size={13} />
                    </button>
                  </div>
                );
              })
            )}
          </div>
        ) : sidebarMode === 'prompts' ? (
          <div className="space-y-2">
            <div className="text-[11px] font-bold text-slate-400 px-1 uppercase tracking-wider">
              Popular Analyst Topics
            </div>
            {samplePrompts.map((item, idx) => (
              <button
                key={idx}
                onClick={() => onSampleClick(item.query)}
                className="w-full p-3 rounded-2xl bg-white hover:bg-indigo-50/50 border border-slate-200/80 hover:border-indigo-200 text-left transition-all group flex items-start space-x-2.5 shadow-sm"
              >
                <div className="p-1.5 rounded-xl bg-slate-50 border border-slate-100 shrink-0 mt-0.5">
                  {item.icon}
                </div>
                <div>
                  <div className="text-[11px] font-bold text-slate-500 group-hover:text-indigo-600 transition-colors">
                    {item.category}
                  </div>
                  <div className="text-xs text-slate-700 line-clamp-2 mt-0.5 font-medium">
                    "{item.query}"
                  </div>
                </div>
              </button>
            ))}
          </div>
        ) : (
          <SchemaExplorer onSelectTable={(tbl) => onSampleClick(`Show me summary records from ${tbl} table`)} />
        )}
      </div>

      {/* Footer Settings */}
      <div className="p-3 border-t border-slate-100 bg-slate-50/50">
        <button
          onClick={onOpenSettings}
          className="w-full py-2 px-3 rounded-xl bg-white hover:bg-slate-100 text-slate-700 text-xs font-semibold border border-slate-200 flex items-center justify-center space-x-2 transition-colors shadow-sm"
        >
          <Settings size={14} className="text-indigo-600" />
          <span>API Key & Engine Settings</span>
        </button>
      </div>
    </aside>
  );
}

