import React from 'react';
import { User, Sparkles, CheckCircle, Search, FileSpreadsheet, Database, Cpu, Loader2, Square } from 'lucide-react';
import SqlViewer from './SqlViewer';
import DynamicChart from './DynamicChart';
import MermaidDiagram from './MermaidDiagram';
import InsightsCard from './InsightsCard';
import FormattedMarkdown from './FormattedMarkdown';

export default function MessageItem({ message, onPinChart, onFollowupClick, onStopRequest }) {
  const isUser = message.role === 'user';

  const getHumanizedLogLabel = (toolName) => {
    switch (toolName) {
      case 'get_schema':
        return 'Understanding schema...';
      case 'execute_query':
        return 'Gathering database records...';
      case 'generate_chart':
        return 'Crafting visual chart...';
      case 'generate_flowchart':
        return 'Drawing process flowchart...';
      case 'explain_data':
        return 'Looking for patterns & insights...';
      default:
        return 'Analyzing your request...';
    }
  };

  return (
    <div className={`py-5 px-4 sm:px-6 flex space-x-3 sm:space-x-4 ${
      isUser 
        ? 'bg-slate-50/80 border-b border-slate-100' 
        : 'bg-white border-b border-slate-100'
    }`}>
      {/* Avatar */}
      <div className="shrink-0 mt-0.5">
        {isUser ? (
          <div className="w-9 h-9 rounded-2xl bg-indigo-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
            <User size={18} />
          </div>
        ) : (
          <div className="w-9 h-9 rounded-2xl bg-gradient-to-br from-emerald-500 via-indigo-500 to-purple-600 flex items-center justify-center text-white shadow-md shadow-indigo-500/20">
            <Sparkles size={18} />
          </div>
        )}
      </div>

      {/* Content Body */}
      <div className="flex-1 space-y-2.5 min-w-0 max-w-4xl">
        <div className="flex items-center space-x-2 flex-wrap gap-y-1">
          <span className="font-bold text-sm text-slate-800">
            {isUser ? 'You' : 'Data Analyst Companion'}
          </span>
          <span className="text-[11px] text-slate-400">
            {message.timestamp || 'Just now'}
          </span>

          {/* Model Badge */}
          {!isUser && (
            <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-slate-100 border border-slate-200 text-[10px] font-bold text-slate-700 shadow-2xs">
              <Cpu size={11} className="text-indigo-600" />
              <span>{message.model_badge || 'AI Engine'}</span>
            </span>
          )}

          {/* Data Source Badge */}
          {!isUser && message.data_source && (
            <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-indigo-50 border border-indigo-100 text-[10px] font-bold text-indigo-700 shadow-2xs">
              <Database size={11} className="text-indigo-500" />
              <span>
                {message.data_source.type === 'uploaded_file'
                  ? `Uploaded: ${message.data_source.name}`
                  : `SQLite: ${message.data_source.name}`}
              </span>
            </span>
          )}

          {/* Stopped Badge */}
          {!isUser && message.isStopped && (
            <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full bg-rose-50 border border-rose-200 text-[10px] font-bold text-rose-700">
              Request stopped
            </span>
          )}
        </div>

        {/* User Attached File Chip */}
        {isUser && message.attached_file_name && (
          <div className="inline-flex items-center space-x-2 px-3 py-1.5 rounded-xl bg-indigo-50 border border-indigo-200 text-indigo-900 text-xs font-semibold my-1 shadow-sm">
            <FileSpreadsheet size={15} className="text-indigo-600" />
            <span>Attached File: {message.attached_file_name}</span>
          </div>
        )}

        {/* User Query text */}
        {isUser ? (
          <p className="text-sm text-slate-800 leading-relaxed font-[450]">
            {message.content}
          </p>
        ) : (
          <div className="space-y-3.5">
            {/* Per-Request Processing Loading Bar with Stop Control */}
            {message.isPending && (
              <div className="flex items-center justify-between py-2.5 px-4 bg-indigo-50/80 rounded-2xl border border-indigo-100 text-xs font-medium text-indigo-900 shadow-2xs">
                <div className="flex items-center space-x-2.5 min-w-0">
                  <Loader2 size={15} className="animate-spin text-indigo-600 shrink-0" />
                  <span className="truncate">{message.processingStatus || "Understanding your question & analyzing database..."}</span>
                </div>
                {onStopRequest && message.requestId && (
                  <button
                    type="button"
                    onClick={() => onStopRequest(message.requestId)}
                    aria-label="Stop request"
                    title="Stop request"
                    className="px-2.5 py-1 rounded-xl bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-700 text-xs font-bold transition-all flex items-center space-x-1.5 shrink-0 ml-3 shadow-2xs"
                  >
                    <Square size={11} className="fill-rose-600 stroke-none" />
                    <span>Stop</span>
                  </button>
                )}
              </div>
            )}

            {/* Tool Activity Timeline Badges */}
            {message.tools_called && message.tools_called.length > 0 && (
              <div className="flex flex-wrap gap-2 pt-1">
                {message.tools_called.map((toolLog, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center space-x-1.5 px-3 py-1 rounded-full bg-indigo-50/80 border border-indigo-100 text-indigo-700 text-xs font-medium"
                  >
                    <Search size={12} className="text-indigo-500" />
                    <span>{getHumanizedLogLabel(toolLog.tool)}</span>
                    <CheckCircle size={12} className="text-emerald-600" />
                  </span>
                ))}
              </div>
            )}

            {/* Assistant Text Response */}
            {message.content && (
              <FormattedMarkdown content={message.content} />
            )}

            {/* SQL Transparency Card */}
            {message.sql_info && <SqlViewer sqlInfo={message.sql_info} />}

            {/* Embedded Visual Chart */}
            {message.chart && (
              <DynamicChart
                spec={message.chart}
                onPinToDashboard={onPinChart}
              />
            )}

            {/* Embedded Mermaid ER / Process Flow Diagram */}
            {message.flowchart && (
              <MermaidDiagram diagram={message.flowchart} />
            )}

            {/* Structured Insights & Proactive Advisory Suggestions */}
            {message.insights && (
              <InsightsCard
                insights={message.insights}
                onFollowupClick={onFollowupClick}
              />
            )}
          </div>
        )}
      </div>
    </div>
  );
}
