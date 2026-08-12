import React, { useState } from 'react';
import { Terminal, Copy, Check, ChevronDown, ChevronRight, Clock, Hash } from 'lucide-react';

export default function SqlViewer({ sqlInfo }) {
  const [isOpen, setIsOpen] = useState(false); // Collapsed by default for clean UI
  const [copied, setCopied] = useState(false);

  if (!sqlInfo || !sqlInfo.query) return null;

  const { query, row_count, execution_time_ms } = sqlInfo;

  const handleCopy = () => {
    navigator.clipboard.writeText(query);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="rounded-2xl border border-slate-200 bg-white overflow-hidden my-3 text-xs shadow-sm">
      <div 
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center justify-between px-4 py-2.5 bg-slate-50/80 cursor-pointer select-none hover:bg-slate-100/60 transition-colors"
      >
        <div className="flex items-center space-x-2">
          {isOpen ? <ChevronDown size={14} className="text-slate-500" /> : <ChevronRight size={14} className="text-slate-400" />}
          <Terminal size={14} className="text-indigo-600" />
          <span className="font-semibold text-slate-700">View Data Query Details</span>
          
          {execution_time_ms !== undefined && (
            <span className="flex items-center space-x-1 px-2 py-0.5 rounded-md bg-white border border-slate-200 text-slate-500 font-mono text-[11px]">
              <Clock size={11} className="text-amber-500" />
              <span>{execution_time_ms} ms</span>
            </span>
          )}

          {row_count !== undefined && (
            <span className="flex items-center space-x-1 px-2 py-0.5 rounded-md bg-white border border-slate-200 text-slate-500 font-mono text-[11px]">
              <Hash size={11} className="text-emerald-600" />
              <span>{row_count} records</span>
            </span>
          )}
        </div>

        <button
          onClick={(e) => {
            e.stopPropagation();
            handleCopy();
          }}
          className="p-1 rounded hover:bg-slate-200 text-slate-500 transition-colors flex items-center space-x-1"
          title="Copy SQL Query"
        >
          {copied ? <Check size={13} className="text-emerald-600" /> : <Copy size={13} />}
          <span>{copied ? "Copied" : "Copy"}</span>
        </button>
      </div>

      {isOpen && (
        <div className="p-4 bg-slate-900 font-mono text-indigo-200 text-xs overflow-x-auto leading-relaxed">
          <code>{query}</code>
        </div>
      )}
    </div>
  );
}
