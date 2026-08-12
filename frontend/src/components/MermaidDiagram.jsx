import React, { useEffect, useRef, useState } from 'react';
import mermaid from 'mermaid';
import { Copy, Check, GitFork, Database } from 'lucide-react';

mermaid.initialize({
  startOnLoad: false,
  theme: 'default',
  securityLevel: 'loose',
  themeVariables: {
    fontFamily: 'Plus Jakarta Sans, sans-serif',
    primaryColor: '#e0e7ff',
    primaryTextColor: '#1e1b4b',
    primaryBorderColor: '#6366f1',
    lineColor: '#4f46e5',
    secondaryColor: '#d1fae5',
    tertiaryColor: '#f1f5f9'
  }
});

export default function MermaidDiagram({ diagram }) {
  const containerRef = useRef(null);
  const [copied, setCopied] = useState(false);
  const [svgContent, setSvgContent] = useState('');
  const [renderError, setRenderError] = useState(null);

  useEffect(() => {
    if (!diagram || !diagram.mermaid_code) return;

    const renderDiagram = async () => {
      try {
        setRenderError(null);
        let cleanCode = diagram.mermaid_code.trim();
        cleanCode = cleanCode.replace(/^```(?:mermaid)?\n?/i, '').replace(/\n?```$/i, '').trim();

        const uniqueId = `mermaid-${Math.random().toString(36).substring(2, 9)}`;
        const { svg } = await mermaid.render(uniqueId, cleanCode);
        setSvgContent(svg);
      } catch (err) {
        console.error("Mermaid Render Error:", err);
        setRenderError("Unable to render diagram markup.");
      }
    };

    renderDiagram();
  }, [diagram]);

  if (!diagram) return null;

  const { diagram_type, title, mermaid_code, explanation } = diagram;
  let displayCode = (mermaid_code || '').trim().replace(/^```(?:mermaid)?\n?/i, '').replace(/\n?```$/i, '').trim();

  const copyCode = () => {
    navigator.clipboard.writeText(displayCode);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="bg-white rounded-3xl p-6 my-4 border border-slate-200 shadow-sm space-y-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-100">
        <div>
          <div className="flex items-center space-x-2">
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wider bg-emerald-50 text-emerald-700 border border-emerald-100">
              {diagram_type === 'er_diagram' ? 'ER Diagram' : 'Process Flow'}
            </span>
            <h3 className="text-base font-bold text-slate-800">{title}</h3>
          </div>
          {explanation && <p className="text-xs text-slate-500 mt-1">{explanation}</p>}
        </div>

        <button 
          onClick={copyCode}
          className="px-2.5 py-1 rounded-xl bg-slate-50 hover:bg-slate-100 text-slate-600 border border-slate-200 transition-colors text-xs font-medium flex items-center space-x-1"
        >
          {copied ? <Check size={14} className="text-emerald-600" /> : <Copy size={14} />}
          <span className="hidden sm:inline">{copied ? "Copied" : "Copy Mermaid"}</span>
        </button>
      </div>

      <div className="w-full overflow-x-auto p-4 rounded-2xl bg-slate-50/70 border border-slate-200/80 flex flex-col justify-center items-center min-h-[220px]">
        {renderError ? (
          <div className="w-full space-y-2">
            <div className="text-amber-700 text-xs bg-amber-50 p-2.5 rounded-xl border border-amber-200 font-medium">
              💡 Note: Visual diagram rendering fallback active. Showing Mermaid specification structure below:
            </div>
            <pre className="text-xs text-slate-700 bg-slate-100 p-3 rounded-xl overflow-x-auto font-mono">
              {displayCode}
            </pre>
          </div>
        ) : (
          <div 
            ref={containerRef} 
            className="w-full flex justify-center [&_svg]:max-w-full [&_svg]:h-auto"
            dangerouslySetInnerHTML={{ __html: svgContent }} 
          />
        )}
      </div>
    </div>
  );
}
