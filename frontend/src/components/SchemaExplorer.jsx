import React, { useEffect, useState } from 'react';
import { Database, Table, Key, Link2, RefreshCw } from 'lucide-react';

export default function SchemaExplorer({ onSelectTable }) {
  const [schemaData, setSchemaData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTable, setActiveTable] = useState(null);

  const fetchSchema = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/schema');
      const data = await res.json();
      if (data.status === 'success') {
        setSchemaData(data.schema);
        const tableNames = Object.keys(data.schema.tables);
        if (tableNames.length > 0) {
          setActiveTable(tableNames[0]);
        }
      }
    } catch (err) {
      console.error("Schema fetch error:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSchema();
  }, []);

  if (loading) {
    return (
      <div className="p-4 text-xs text-slate-500 flex items-center space-x-2 animate-pulse">
        <RefreshCw size={14} className="animate-spin text-indigo-600" />
        <span>Loading schema explorer...</span>
      </div>
    );
  }

  if (!schemaData) return null;

  const tables = schemaData.tables;

  return (
    <div className="space-y-3 text-xs">
      <div className="flex items-center justify-between px-1">
        <div className="flex items-center space-x-1.5 text-indigo-900 font-bold">
          <Database size={14} className="text-indigo-600" />
          <span>Tables ({schemaData.table_count})</span>
        </div>
        <button 
          onClick={fetchSchema}
          title="Refresh Schema"
          className="p-1 rounded hover:bg-slate-100 text-slate-400 hover:text-slate-700"
        >
          <RefreshCw size={12} />
        </button>
      </div>

      <div className="flex flex-wrap gap-1.5 border-b border-slate-100 pb-3">
        {Object.keys(tables).map((tbl) => (
          <button
            key={tbl}
            onClick={() => setActiveTable(tbl)}
            className={`px-2.5 py-1 rounded-lg text-[11px] font-mono transition-all border ${
              activeTable === tbl
                ? 'bg-indigo-50 text-indigo-700 border-indigo-200 font-bold shadow-sm'
                : 'bg-white text-slate-600 hover:text-slate-900 border-slate-200'
            }`}
          >
            {tbl}
          </button>
        ))}
      </div>

      {activeTable && tables[activeTable] && (
        <div className="space-y-3 bg-slate-50/70 rounded-2xl p-3 border border-slate-200/80">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-1.5 font-mono text-slate-800 font-bold">
              <Table size={13} className="text-indigo-600" />
              <span>{activeTable}</span>
            </div>
            <span className="text-[10px] text-slate-600 bg-white px-2 py-0.5 rounded-full font-mono border border-slate-200">
              {tables[activeTable].total_rows} rows
            </span>
          </div>

          <div className="space-y-1 max-h-48 overflow-y-auto pr-1">
            {tables[activeTable].columns.map((col) => (
              <div key={col.name} className="flex items-center justify-between py-1 border-b border-slate-200/50 font-mono text-[11px]">
                <div className="flex items-center space-x-1.5">
                  {col.pk ? <Key size={11} className="text-amber-500 shrink-0" /> : <span className="w-3" />}
                  <span className={col.pk ? "text-amber-700 font-bold" : "text-slate-700"}>
                    {col.name}
                  </span>
                </div>
                <span className="text-slate-400 text-[10px] uppercase font-semibold">{col.type}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
