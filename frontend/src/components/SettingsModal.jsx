import React from 'react';
import { X, Key, ShieldCheck, CheckCircle2, Server } from 'lucide-react';

export default function SettingsModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white w-full max-w-lg rounded-3xl p-6 border border-slate-200 shadow-2xl space-y-6">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div className="flex items-center space-x-2">
            <Server className="text-indigo-600" size={20} />
            <h2 className="text-lg font-bold text-slate-800">AI Data Analyst Engine Status</h2>
          </div>
          <button 
            onClick={onClose}
            className="p-1 rounded-xl hover:bg-slate-100 text-slate-400 hover:text-slate-700"
          >
            <X size={18} />
          </button>
        </div>

        <div className="space-y-4 text-xs">
          {/* Security Banner */}
          <div className="p-4 rounded-2xl bg-emerald-50/80 border border-emerald-100 text-emerald-900 space-y-2">
            <div className="font-bold flex items-center space-x-1.5 text-sm text-emerald-950">
              <ShieldCheck size={18} className="text-emerald-600" />
              <span>Enterprise Secure API Key Architecture</span>
            </div>
            <p className="text-emerald-900/90 leading-relaxed">
              For security compliance, API keys are resolved directly by the backend server from environment variables (<code className="bg-emerald-100 px-1 py-0.5 rounded text-[11px] font-mono">.env</code>). Permanent API keys are never stored in browser <code className="bg-emerald-100 px-1 py-0.5 rounded text-[11px] font-mono">localStorage</code>.
            </p>
          </div>

          {/* Engine Status Highlights */}
          <div className="space-y-2">
            <div className="font-bold text-slate-700 text-xs mb-2">Active AI Providers:</div>
            
            <div className="flex items-center justify-between p-3.5 rounded-2xl bg-slate-50 border border-slate-100">
              <div className="space-y-0.5">
                <div className="font-bold text-slate-800 text-xs">Thinking Engine</div>
                <div className="text-[11px] text-slate-500">Native API Tool Calling & Reasoning Engine</div>
              </div>
              <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-bold">
                <CheckCircle2 size={12} className="text-emerald-600" />
                <span>Primary</span>
              </span>
            </div>

            <div className="flex items-center justify-between p-3.5 rounded-2xl bg-slate-50 border border-slate-100">
              <div className="space-y-0.5">
                <div className="font-bold text-slate-800 text-xs">Smart Autonomous Engine</div>
                <div className="text-[11px] text-slate-500">Zero-Dependency Offline Text-to-SQL Fallback</div>
              </div>
              <span className="inline-flex items-center space-x-1 px-2.5 py-1 rounded-full bg-indigo-100 text-indigo-800 text-[10px] font-bold">
                <CheckCircle2 size={12} className="text-indigo-600" />
                <span>Offline Fallback</span>
              </span>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-end pt-4 border-t border-slate-100">
          <button
            onClick={onClose}
            className="px-5 py-2.5 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-semibold shadow-md shadow-indigo-500/30"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
