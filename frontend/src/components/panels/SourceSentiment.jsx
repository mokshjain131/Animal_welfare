// panels/SourceSentiment.jsx
import React from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell } from 'recharts';
import { useApiData } from '../../hooks/useApiData';
import { GlassCard } from '../ui/GlassCard';

/**
 * Extract the short brand name from a full source title.
 * e.g. "Al Jazeera – Breaking News, World News and Video from Al Jazeera" → "Al Jazeera"
 */
const SOURCE_ALIASES = {
  'nyt': 'NYT',
  'new york times': 'NYT',
  'bbc': 'BBC News',
  'al jazeera': 'Al Jazeera',
  'the guardian': 'The Guardian',
  'environment': 'The Guardian',
  'national geographic': 'Nat Geo',
  'globenewswire': 'GlobeNewswire',
};

function cleanSourceName(name) {
  if (!name) return 'Unknown';
  // Strip after common separators:  – | - : //
  let short = name.split(/\s*[–|\-:]\s*/)[0].trim();
  // Remove trailing domain parts like ".com", "Online"
  short = short.replace(/\.(com|org|net|co\.uk)$/i, '').trim();
  // Check known aliases
  const lower = short.toLowerCase();
  for (const [key, alias] of Object.entries(SOURCE_ALIASES)) {
    if (lower.includes(key)) return alias;
  }
  // Cap length
  return short.length > 16 ? short.slice(0, 16) + '…' : short;
}

export default function SourceSentiment() {
  const { data: raw, loading } = useApiData('/sources/sentiment', { days: 7, limit: 10 }, { sources: [] });
  const data = (raw?.sources || []).map(s => ({ ...s, source_name: cleanSourceName(s.source_name) }));

  return (
    <GlassCard className="col-span-12 lg:col-span-3 h-[500px]" title="Source Bias Array">
      {loading ? (
        <div className="flex-1 flex items-center justify-center animate-pulse bg-slate-50/50 dark:bg-slate-800/20 rounded-xl" />
      ) : (
        <div className="flex-1 w-full relative">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart 
              data={data} 
              layout="vertical" 
              margin={{ top: 0, right: 10, left: 0, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="currentColor" className="text-slate-200 dark:text-slate-700/50" />
              <XAxis type="number" domain={[-1, 1]} hide />
              <YAxis 
                type="category" 
                dataKey="source_name" 
                axisLine={false} 
                tickLine={false} 
                tick={{ fontSize: 11 }}
                width={110}
                className="text-slate-600 dark:text-slate-300"
              />
              <Tooltip 
                cursor={{ fill: 'currentColor', opacity: 0.05 }}
                contentStyle={{ backgroundColor: '#1e293b', borderRadius: '8px', border: '1px solid #334155', color: '#f1f5f9', padding: '8px 12px' }}
                itemStyle={{ color: '#f1f5f9' }}
                labelStyle={{ color: '#94a3b8', fontSize: 12, marginBottom: 4 }}
                formatter={(value) => [value?.toFixed(4), 'Avg Sentiment']}
              />
              <Bar dataKey="avg_sentiment" radius={[4, 4, 4, 4]} maxBarSize={20}>
                {data.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={entry.avg_sentiment > 0.1 ? '#34d399' : entry.avg_sentiment < -0.1 ? '#fb7185' : '#94a3b8'} 
                    fillOpacity={0.8}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </GlassCard>
  );
}