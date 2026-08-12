import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';

export default function FormattedMarkdown({ content }) {
  if (!content) return null;

  // Pre-process: expand compressed markdown elements
  let processedContent = content;
  processedContent = processedContent.replace(/([^\n])\s*(---|\*\*\*)\s*/g, '$1\n\n---\n\n');
  processedContent = processedContent.replace(/([^\n])\s*(#{1,4}\s+)/g, '$1\n\n$2');
  processedContent = processedContent.replace(/([^\n])\s*(\d+\.\s+[A-Z`*])/g, '$1\n\n$2');
  processedContent = processedContent.replace(/([^\n])\s*(-\s+\*\*)/g, '$1\n\n$2');

  return (
    <div className="markdown-body text-sm leading-relaxed text-slate-800 dark:text-slate-100" style={{ fontFamily: "'Inter', 'Segoe UI', system-ui, sans-serif" }}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // ── Headings ──────────────────────────────────────────────────────
          h1: ({ children }) => (
            <h1 style={{
              fontSize: '1.25rem', fontWeight: 800, color: '#0f172a',
              marginTop: '1.5rem', marginBottom: '0.75rem',
              paddingBottom: '0.5rem', borderBottom: '2px solid #e2e8f0',
              letterSpacing: '-0.02em', lineHeight: 1.3
            }}>
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 style={{
              fontSize: '1.1rem', fontWeight: 700, color: '#1e293b',
              marginTop: '1.25rem', marginBottom: '0.5rem',
              paddingBottom: '0.35rem', borderBottom: '1px solid #e2e8f0',
              letterSpacing: '-0.015em', lineHeight: 1.4
            }}>
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 style={{
              fontSize: '0.975rem', fontWeight: 700, color: '#4338ca',
              marginTop: '1rem', marginBottom: '0.4rem', lineHeight: 1.4
            }}>
              {children}
            </h3>
          ),
          h4: ({ children }) => (
            <h4 style={{
              fontSize: '0.9rem', fontWeight: 700, color: '#334155',
              marginTop: '0.75rem', marginBottom: '0.3rem'
            }}>
              {children}
            </h4>
          ),

          // ── Paragraph ─────────────────────────────────────────────────────
          p: ({ children }) => (
            <p style={{
              fontSize: '0.875rem', color: '#334155',
              lineHeight: 1.75, margin: '0.5rem 0', fontWeight: 450
            }}>
              {children}
            </p>
          ),

          // ── Lists ─────────────────────────────────────────────────────────
          ul: ({ children }) => (
            <ul style={{
              paddingLeft: '1.4rem', margin: '0.6rem 0',
              listStyleType: 'disc', display: 'flex', flexDirection: 'column', gap: '0.3rem'
            }}>
              {children}
            </ul>
          ),
          ol: ({ children }) => (
            <ol style={{
              paddingLeft: '1.4rem', margin: '0.6rem 0',
              listStyleType: 'decimal', display: 'flex', flexDirection: 'column', gap: '0.3rem'
            }}>
              {children}
            </ol>
          ),
          li: ({ children }) => (
            <li style={{
              fontSize: '0.875rem', color: '#334155', lineHeight: 1.65,
              paddingLeft: '0.2rem'
            }}>
              {children}
            </li>
          ),

          // ── Inline formatting ──────────────────────────────────────────────
          strong: ({ children }) => (
            <strong style={{ fontWeight: 700, color: '#0f172a' }}>{children}</strong>
          ),
          em: ({ children }) => (
            <em style={{ fontStyle: 'italic', color: '#475569' }}>{children}</em>
          ),

          // ── Blockquote (used for callouts like > **Query:** ...) ──────────
          blockquote: ({ children }) => (
            <blockquote style={{
              borderLeft: '4px solid #6366f1',
              background: 'linear-gradient(to right, #eef2ff, #f8fafc)',
              padding: '0.6rem 1rem',
              margin: '0.75rem 0',
              borderRadius: '0 10px 10px 0',
              fontSize: '0.875rem',
              color: '#3730a3',
              fontStyle: 'normal'
            }}>
              {children}
            </blockquote>
          ),

          // ── Table ─────────────────────────────────────────────────────────
          table: ({ children }) => (
            <div style={{
              overflowX: 'auto', margin: '1rem 0',
              borderRadius: '12px', border: '1px solid #e2e8f0',
              boxShadow: '0 1px 4px rgba(0,0,0,0.06)'
            }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem' }}>
                {children}
              </table>
            </div>
          ),
          thead: ({ children }) => (
            <thead style={{
              background: 'linear-gradient(to right, #f1f5f9, #e2e8f0)',
              borderBottom: '2px solid #cbd5e1'
            }}>
              {children}
            </thead>
          ),
          th: ({ children }) => (
            <th style={{
              padding: '0.6rem 0.9rem', textAlign: 'left',
              fontWeight: 700, color: '#0f172a', fontSize: '0.78rem',
              borderRight: '1px solid #e2e8f0', whiteSpace: 'nowrap'
            }}>
              {children}
            </th>
          ),
          tbody: ({ children }) => (
            <tbody>{children}</tbody>
          ),
          tr: ({ children, ...props }) => (
            <tr style={{
              borderBottom: '1px solid #f1f5f9',
              transition: 'background 0.15s ease'
            }}
              onMouseEnter={e => e.currentTarget.style.background = '#f8faff'}
              onMouseLeave={e => e.currentTarget.style.background = 'transparent'}
            >
              {children}
            </tr>
          ),
          td: ({ children }) => (
            <td style={{
              padding: '0.5rem 0.9rem', color: '#334155',
              borderRight: '1px solid #f1f5f9', fontSize: '0.8rem',
              verticalAlign: 'middle'
            }}>
              {children}
            </td>
          ),

          // ── Code ──────────────────────────────────────────────────────────
          code: ({ inline, className, children, ...props }) => {
            const match = /language-(\w+)/.exec(className || '');
            const lang = match ? match[1] : '';
            const codeStr = String(children).replace(/\n$/, '');

            if (inline) {
              return (
                <code style={{
                  padding: '2px 7px', borderRadius: '6px',
                  background: '#eef2ff', color: '#4338ca',
                  fontFamily: "'Fira Code', 'Cascadia Code', monospace",
                  fontSize: '0.78rem', fontWeight: 600,
                  border: '1px solid #c7d2fe'
                }}>
                  {children}
                </code>
              );
            }

            return (
              <div style={{ margin: '0.75rem 0', borderRadius: '12px', overflow: 'hidden', boxShadow: '0 4px 12px rgba(0,0,0,0.15)' }}>
                {/* Top bar with language label and copy button */}
                <div style={{
                  background: '#1e293b', padding: '0.4rem 0.9rem',
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center'
                }}>
                  <span style={{ color: '#94a3b8', fontSize: '0.72rem', fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    {lang || 'code'}
                  </span>
                  <button
                    onClick={() => navigator.clipboard?.writeText(codeStr)}
                    style={{
                      background: 'transparent', border: '1px solid #334155',
                      color: '#94a3b8', fontSize: '0.7rem', padding: '2px 8px',
                      borderRadius: '6px', cursor: 'pointer', transition: 'all 0.15s'
                    }}
                    onMouseEnter={e => { e.target.style.background = '#334155'; e.target.style.color = '#fff'; }}
                    onMouseLeave={e => { e.target.style.background = 'transparent'; e.target.style.color = '#94a3b8'; }}
                  >
                    Copy
                  </button>
                </div>
                <SyntaxHighlighter
                  style={oneDark}
                  language={lang || 'text'}
                  PreTag="div"
                  customStyle={{
                    margin: 0, borderRadius: 0, fontSize: '0.8rem',
                    padding: '1rem', lineHeight: 1.6
                  }}
                  {...props}
                >
                  {codeStr}
                </SyntaxHighlighter>
              </div>
            );
          },

          // ── Divider ───────────────────────────────────────────────────────
          hr: () => (
            <hr style={{
              margin: '1rem 0', border: 'none',
              borderTop: '1px solid #e2e8f0'
            }} />
          ),
        }}
      >
        {processedContent}
      </ReactMarkdown>
    </div>
  );
}
