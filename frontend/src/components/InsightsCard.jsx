import React from 'react';
import { Compass, ArrowRight, CheckCircle2, HelpCircle, Lightbulb } from 'lucide-react';

export default function InsightsCard({ insights, onFollowupClick }) {
  if (!insights) return null;

  const { highlights, recommended_followups, proactive_tip } = insights;

  return (
    <div className="space-y-3 my-4">
      {/* Executive Highlights Box */}
      <div className="rounded-3xl border border-indigo-100 bg-gradient-to-br from-indigo-50/50 to-slate-50 p-4 space-y-3 shadow-sm">
        <div className="flex items-center space-x-2 text-indigo-900 font-bold text-sm">
          <Compass size={17} className="text-indigo-600" />
          <span>Analyst Key Insights</span>
        </div>

        {highlights && highlights.length > 0 && (
          <ul className="space-y-1.5 text-xs text-slate-700">
            {highlights.map((item, idx) => (
              <li key={idx} className="flex items-start space-x-2">
                <CheckCircle2 size={14} className="text-emerald-600 shrink-0 mt-0.5" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Requirement: Standout Proactive Insights / Smart Next Step Box */}
      {proactive_tip && (
        <div className="rounded-3xl border border-amber-200/80 bg-amber-50/70 p-4 flex items-start space-x-3 shadow-sm">
          <div className="p-2 rounded-2xl bg-amber-100 text-amber-700 shrink-0 mt-0.5">
            <Lightbulb size={16} />
          </div>
          <div className="space-y-1">
            <div className="font-bold text-xs text-amber-900">Proactive Advisor Recommendation</div>
            <p className="text-xs text-amber-800 leading-relaxed font-medium">
              {proactive_tip}
            </p>
          </div>
        </div>
      )}

      {/* Friendly Follow-up Suggestions */}
      {recommended_followups && recommended_followups.length > 0 && (
        <div className="pt-2">
          <div className="flex items-center space-x-1.5 text-xs font-semibold text-slate-500 mb-2.5">
            <HelpCircle size={14} className="text-indigo-500" />
            <span>Suggested Next Steps to Explore:</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {recommended_followups.map((q, idx) => (
              <button
                key={idx}
                onClick={() => onFollowupClick && onFollowupClick(q)}
                className="px-3.5 py-2 rounded-2xl bg-white hover:bg-indigo-50 border border-slate-200 hover:border-indigo-200 text-xs text-slate-700 hover:text-indigo-700 transition-all shadow-sm flex items-center space-x-1.5 group text-left"
              >
                <span>{q}</span>
                <ArrowRight size={13} className="group-hover:translate-x-0.5 transition-transform text-indigo-500" />
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
