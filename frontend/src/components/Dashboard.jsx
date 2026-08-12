import React from 'react';
import DynamicChart from './DynamicChart';
import { LayoutDashboard, Trash2, PlusCircle } from 'lucide-react';

export default function Dashboard({ pinnedCharts, onUnpin, onSwitchToChat }) {
  if (!pinnedCharts || pinnedCharts.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-8 text-center bg-slate-50">
        <div className="p-4 rounded-3xl bg-indigo-50 border border-indigo-100 text-indigo-600 mb-4 shadow-sm">
          <LayoutDashboard size={40} />
        </div>
        <h2 className="text-xl font-bold text-slate-800 mb-2">Your Dashboard is Ready to Pin Visuals</h2>
        <p className="text-sm text-slate-500 max-w-md mb-6 leading-relaxed">
          Pin charts directly from your analyst chat sessions to build your custom business intelligence dashboard!
        </p>
        <button
          onClick={onSwitchToChat}
          className="px-5 py-2.5 rounded-2xl bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-sm flex items-center space-x-2 shadow-md shadow-indigo-500/25 transition-all"
        >
          <PlusCircle size={17} />
          <span>Ask Your Analyst a Question</span>
        </button>
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto p-6 bg-slate-50 space-y-6">
      <div className="flex items-center justify-between pb-4 border-b border-slate-200">
        <div>
          <div className="flex items-center space-x-2">
            <LayoutDashboard size={20} className="text-indigo-600" />
            <h1 className="text-xl font-bold text-slate-800">Your Business Analytics Dashboard</h1>
          </div>
          <p className="text-xs text-slate-500 mt-1">
            {pinnedCharts.length} active visualization card{pinnedCharts.length > 1 ? 's' : ''} pinned from your session.
          </p>
        </div>

        <button
          onClick={onSwitchToChat}
          className="px-4 py-2 rounded-xl bg-white hover:bg-slate-100 text-slate-700 text-xs font-semibold border border-slate-200 shadow-sm flex items-center space-x-1.5"
        >
          <span>Analyze Chat</span>
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {pinnedCharts.map((chartSpec, index) => (
          <div key={index} className="relative group">
            <button
              onClick={() => onUnpin(index)}
              title="Remove from Dashboard"
              className="absolute top-8 right-8 z-10 p-2 rounded-xl bg-white hover:bg-red-50 text-slate-400 hover:text-red-600 border border-slate-200 hover:border-red-200 transition-colors shadow-sm"
            >
              <Trash2 size={15} />
            </button>
            <DynamicChart spec={chartSpec} />
          </div>
        ))}
      </div>
    </div>
  );
}
