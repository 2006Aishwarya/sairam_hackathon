import React, { useRef } from 'react';
import { 
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, ScatterChart, Scatter, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';
import { Download, Pin, FileSpreadsheet, Check, Sparkles } from 'lucide-react';

export default function DynamicChart({ spec, onPinToDashboard, isPinned = false }) {
  const chartRef = useRef(null);
  const [copied, setCopied] = React.useState(false);

  if (!spec || !spec.data || spec.data.length === 0) {
    return (
      <div className="p-4 rounded-2xl bg-white border border-slate-200 text-slate-500 text-sm shadow-sm">
        No dataset records available to render graph.
      </div>
    );
  }

  const { chart_type, title, description, takeaway, x_key, y_keys, colors, data } = spec;
  const palette = colors || ["#4F46E5", "#10B981", "#F59E0B", "#8B5CF6", "#EC4899", "#3B82F6", "#14B8A6"];

  const handleExportCSV = () => {
    if (!data.length) return;
    const headers = Object.keys(data[0]).join(",");
    const rows = data.map(row => Object.values(row).map(val => `"${val}"`).join(","));
    const csvContent = "data:text/csv;charset=utf-8," + [headers, ...rows].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `${title.replace(/\s+/g, "_")}_data.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handlePin = () => {
    if (onPinToDashboard) {
      onPinToDashboard(spec);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const renderChartBody = () => {
    switch (chart_type?.toLowerCase()) {
      case 'line':
        return (
          <LineChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" opacity={0.7} />
            <XAxis dataKey={x_key} stroke="#64748b" tick={{ fill: '#64748b', fontSize: 12 }} />
            <YAxis stroke="#64748b" tick={{ fill: '#64748b', fontSize: 12 }} />
            <Tooltip contentStyle={{ backgroundColor: '#ffffff', borderColor: '#cbd5e1', borderRadius: '12px', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }} />
            <Legend wrapperStyle={{ color: '#334155' }} />
            {y_keys.map((key, index) => (
              <Line 
                key={key} 
                type="monotone" 
                dataKey={key} 
                stroke={palette[index % palette.length]} 
                strokeWidth={3} 
                activeDot={{ r: 7 }} 
              />
            ))}
          </LineChart>
        );

      case 'pie':
        return (
          <PieChart margin={{ top: 10, right: 10, left: 10, bottom: 10 }}>
            <Tooltip contentStyle={{ backgroundColor: '#ffffff', borderColor: '#cbd5e1', borderRadius: '12px', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }} />
            <Legend wrapperStyle={{ color: '#334155' }} />
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              innerRadius={50}
              outerRadius={90}
              paddingAngle={4}
              dataKey={y_keys[0] || "value"}
              nameKey={x_key || "name"}
              label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={palette[index % palette.length]} />
              ))}
            </Pie>
          </PieChart>
        );

      case 'scatter':
        return (
          <ScatterChart margin={{ top: 10, right: 30, left: 0, bottom: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" opacity={0.7} />
            <XAxis dataKey={x_key} type="number" name={x_key} stroke="#64748b" tick={{ fill: '#64748b', fontSize: 12 }} />
            <YAxis dataKey={y_keys[0]} type="number" name={y_keys[0]} stroke="#64748b" tick={{ fill: '#64748b', fontSize: 12 }} />
            <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ backgroundColor: '#ffffff', borderColor: '#cbd5e1', borderRadius: '12px' }} />
            <Scatter name={title} data={data} fill={palette[0]} />
          </ScatterChart>
        );

      case 'area':
        return (
          <AreaChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 10 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" opacity={0.7} />
            <XAxis dataKey={x_key} stroke="#64748b" tick={{ fill: '#64748b', fontSize: 12 }} />
            <YAxis stroke="#64748b" tick={{ fill: '#64748b', fontSize: 12 }} />
            <Tooltip contentStyle={{ backgroundColor: '#ffffff', borderColor: '#cbd5e1', borderRadius: '12px' }} />
            {y_keys.map((key, index) => (
              <Area 
                key={key} 
                type="monotone" 
                dataKey={key} 
                stroke={palette[index % palette.length]} 
                fill={palette[index % palette.length]} 
                fillOpacity={0.25} 
              />
            ))}
          </AreaChart>
        );

      case 'bar':
      default:
        return (
          <BarChart data={data} margin={{ top: 10, right: 30, left: 0, bottom: 25 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" opacity={0.7} />
            <XAxis dataKey={x_key} stroke="#64748b" tick={{ fill: '#64748b', fontSize: 11 }} angle={-15} textAnchor="end" />
            <YAxis stroke="#64748b" tick={{ fill: '#64748b', fontSize: 12 }} />
            <Tooltip contentStyle={{ backgroundColor: '#ffffff', borderColor: '#cbd5e1', borderRadius: '12px', boxShadow: '0 10px 15px -3px rgba(0,0,0,0.1)' }} />
            <Legend wrapperStyle={{ color: '#334155' }} />
            {y_keys.map((key, index) => (
              <Bar 
                key={key} 
                dataKey={key} 
                fill={palette[index % palette.length]} 
                radius={[8, 8, 0, 0]} 
              />
            ))}
          </BarChart>
        );
    }
  };

  return (
    <div ref={chartRef} className="bg-white rounded-3xl p-6 my-4 border border-slate-200/90 shadow-sm space-y-4">
      {/* Header & Controls */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider bg-indigo-50 text-indigo-700 border border-indigo-100">
              {chart_type} Chart
            </span>
            <h3 className="text-base font-bold text-slate-800">{title}</h3>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button 
            onClick={handleExportCSV}
            title="Export Dataset to CSV"
            className="px-2.5 py-1 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-600 border border-slate-200 transition-colors text-xs font-medium flex items-center space-x-1"
          >
            <FileSpreadsheet size={14} className="text-slate-500" />
            <span className="hidden sm:inline">CSV</span>
          </button>
          
          {onPinToDashboard && (
            <button 
              onClick={handlePin}
              title="Pin Chart"
              className={`px-2.5 py-1 rounded-xl text-xs font-medium transition-colors border flex items-center space-x-1 ${
                isPinned || copied 
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200' 
                  : 'bg-indigo-50 hover:bg-indigo-100 text-indigo-700 border-indigo-200'
              }`}
            >
              {copied ? <Check size={14} /> : <Pin size={14} />}
              <span className="hidden sm:inline">{copied ? "Pinned" : "Pin"}</span>
            </button>
          )}
        </div>
      </div>

      {/* Requirement: Plain one-sentence takeaway BEFORE the chart */}
      {takeaway && (
        <div className="p-3.5 rounded-2xl bg-indigo-50/60 border border-indigo-100 text-xs font-medium text-indigo-900 flex items-start space-x-2">
          <Sparkles size={15} className="text-indigo-600 shrink-0 mt-0.5" />
          <span>{takeaway}</span>
        </div>
      )}

      {/* Chart Canvas */}
      <div className="w-full h-72 pt-2">
        <ResponsiveContainer width="100%" height="100%">
          {renderChartBody()}
        </ResponsiveContainer>
      </div>
    </div>
  );
}
