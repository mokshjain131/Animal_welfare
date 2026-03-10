// panels/TrendingKeywords.jsx
import React from 'react';
import { useApiData } from '../../hooks/useApiData';
import { GlassCard } from '../ui/GlassCard';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export default function TrendingKeywords() {
  const { data: raw, loading } = useApiData('/trending/keywords', {}, { keywords: [] });
  const keywords = raw?.keywords || [];

  return (
    <GlassCard className="col-span-12 md:col-span-6 min-h-[300px]" title="Trending Signals (TF-IDF)">
      {loading ? (
        <div className="space-y-2">
          {[1,2,3,4,5].map(i => <div key={i} className="h-8 bg-slate-100 dark:bg-slate-800/50 rounded animate-pulse" />)}
        </div>
      ) : (
        <div className="flex-1 overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-200 dark:border-slate-700/50 text-xs text-slate-500 uppercase tracking-wider">
                <th className="pb-2 font-semibold">Keyword</th>
                <th className="pb-2 font-semibold">Topic</th>
                <th className="pb-2 font-semibold text-right">Vol</th>
                <th className="pb-2 font-semibold text-center w-12">Trend</th>
              </tr>
            </thead>
            <tbody className="text-sm">
              {keywords && keywords.slice(0, 8).map((kw) => (
                <tr key={kw.id} className="border-b border-slate-100 dark:border-slate-800/50 last:border-0 hover:bg-slate-50/50 dark:hover:bg-slate-800/30 transition-colors">
                  <td className="py-2.5 font-medium text-slate-800 dark:text-slate-200">{kw.phrase}</td>
                  <td className="py-2.5 text-xs text-slate-500 capitalize">{kw.topic.replace('_', ' ')}</td>
                  <td className="py-2.5 text-right font-mono text-slate-600 dark:text-slate-400">{kw.article_count}</td>
                  <td className="py-2.5 text-center">
                    {kw.trend_direction === 'up' && <TrendingUp className="w-4 h-4 mx-auto text-status-positive" />}
                    {kw.trend_direction === 'down' && <TrendingDown className="w-4 h-4 mx-auto text-status-negative" />}
                    {kw.trend_direction === 'new' && <span className="text-[10px] uppercase font-bold text-brand-accent bg-brand-accent/10 px-1 rounded">New</span>}
                    {kw.trend_direction === 'stable' && <Minus className="w-4 h-4 mx-auto text-slate-400" />}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </GlassCard>
  );
}