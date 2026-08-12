import React from 'react';
import { Database, RefreshCw, Sun, Moon } from 'lucide-react';

export default function Header({ 
  onReseedDb, 
  isReseeding,
  isDark,
  onToggleTheme
}) {
  return (
    <header className="h-14 bg-white/90 backdrop-blur-md border-b border-slate-200 px-6 flex items-center justify-between shrink-0 shadow-sm">
      <div className="flex items-center space-x-3">
        <div className="flex items-center space-x-2 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-100">
          <span className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
            <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
          </span>
          <span className="text-xs font-semibold text-emerald-800">AI Data Analyst Active</span>
        </div>

        <span className="text-slate-300">|</span>

        <div className="hidden sm:flex items-center space-x-1.5 text-xs text-slate-500 font-medium">
          <Database size={13} className="text-indigo-600" />
          <span>Database: e-commerce dataset</span>
        </div>
      </div>

      <div className="flex items-center space-x-3">
        {/* Re-seed Sample Database Button */}
        <button
          onClick={onReseedDb}
          disabled={isReseeding}
          aria-label="Reset sample database"
          title="Reset sample database"
          className="px-3 py-1.5 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-700 transition-colors border border-slate-200 text-xs font-semibold flex items-center space-x-1.5"
        >
          <RefreshCw size={13} className={isReseeding ? "animate-spin text-indigo-600" : "text-slate-500"} />
          <span className="hidden md:inline">Reset Data</span>
        </button>

        {/* Dark Theme Switcher Button */}
        <button
          onClick={onToggleTheme}
          aria-label={isDark ? "Switch to Light Theme" : "Switch to Dark Theme"}
          title={isDark ? "Switch to Light Theme" : "Switch to Dark Theme"}
          className="px-3 py-1.5 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-700 transition-all border border-slate-200 text-xs font-semibold flex items-center space-x-1.5 shadow-2xs cursor-pointer"
        >
          {isDark ? (
            <>
              <Sun size={14} className="text-amber-400 fill-amber-400" />
              <span>Light Mode</span>
            </>
          ) : (
            <>
              <Moon size={14} className="text-indigo-600 fill-indigo-600" />
              <span>Dark Mode</span>
            </>
          )}
        </button>
      </div>
    </header>
  );
}

