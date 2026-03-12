// panels/SentimentTrend.jsx
import React, { useState, useEffect } from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine, ReferenceArea } from 'recharts';
import { useApiData } from '../../hooks/useApiData';
import { GlassCard } from '../ui/GlassCard';
import { Info } from 'lucide-react';

const SENTIMENT_BANDS = [
  { y1:  0.6, y2:  1,   label: 'Very Positive', color: '#22c55e' },
  { y1:  0.2, y2:  0.6, label: 'Positive',      color: '#86efac' },
  { y1: -0.2, y2:  0.2, label: 'Neutral',        color: '#94a3b8' },
  { y1: -0.6, y2: -0.2, label: 'Negative',       color: '#fbbf24' },
  { y1: -1,   y2: -0.6, label: 'Very Negative',  color: '#ef4444' },
];

function SentimentGuide({ visible }) {
  if (!visible) return null;
  return (
    <div className="absolute right-2 top-10 z-20 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg shadow-lg p-3 text-xs w-52">
      <p className="font-semibold text-slate-700 dark:text-slate-200 mb-2">Sentiment Scale</p>
      <div className="space-y-1.5">
        {SENTIMENT_BANDS.map((b) => (
          <div key={b.label} className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-sm flex-shrink-0" style={{ backgroundColor: b.color }} />
            <span className="text-slate-600 dark:text-slate-300 flex-1">{b.label}</span>
            <span className="text-slate-400 dark:text-slate-500 font-mono tabular-nums">
              {b.y1 < 0 ? b.y1 : `+${b.y1}`} to {b.y2 < 0 ? b.y2 : `+${b.y2}`}
            </span>
          </div>
        ))}
      </div>
      <p className="mt-2 text-[10px] text-slate-400 dark:text-slate-500 leading-tight">
        Score reflects the average emotional tone of articles. Closer to +1 = more positive coverage, closer to −1 = more negative.
      </p>
    </div>
  );
}

function useDarkMode() {
  const [isDark, setIsDark] = useState(() => document.documentElement.classList.contains('dark'));
  useEffect(() => {
    const obs = new MutationObserver(() =>
      setIsDark(document.documentElement.classList.contains('dark'))
    );
    obs.observe(document.documentElement, { attributeFilter: ['class'] });
    return () => obs.disconnect();
  }, []);
  return isDark;
}

export default function SentimentTrend() {
  const [days, setDays] = useState(7);
  const [topic, setTopic] = useState('');
  const [showGuide, setShowGuide] = useState(false);
  const isDark = useDarkMode();
  
  const { data: raw, loading } = useApiData('/sentiment/trend', { days, topic: topic || undefined }, { data: [] });
  const data = raw?.data || [];

  const formatXAxis = (tickItem) => {
    return new Date(tickItem).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  };

  const ActionSelector = (
    <div className="flex items-center gap-2">
      <select 
        value={topic} 
        onChange={(e) => setTopic(e.target.value)}
        className="text-xs bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md px-2 py-1 text-slate-700 dark:text-slate-300 outline-none"
      >
        <option value="">All Topics</option>
        <option value="factory_farming">Factory Farming</option>
        <option value="wildlife">Wildlife</option>
        <option value="animal_testing">Animal Testing</option>
        <option value="pet_welfare">Pet Welfare</option>
      </select>
      <select 
        value={days} 
        onChange={(e) => setDays(Number(e.target.value))}
        className="text-xs bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md px-2 py-1 text-slate-700 dark:text-slate-300 outline-none"
      >
        <option value={7}>7 Days</option>
        <option value={14}>14 Days</option>
        <option value={30}>30 Days</option>
      </select>
      <button
        onClick={() => setShowGuide((v) => !v)}
        className="p-1 rounded-md hover:bg-slate-200 dark:hover:bg-slate-700 text-slate-500 dark:text-slate-400 transition-colors"
        title="Sentiment guide"
      >
        <Info size={16} />
      </button>
    </div>
  );

  return (
    <GlassCard className="col-span-12 lg:col-span-8 min-h-[350px] relative" title="Average Sentiment Trend" action={ActionSelector}>
      <SentimentGuide visible={showGuide} />
      {loading ? (
        <div className="flex-1 flex items-center justify-center animate-pulse bg-slate-50/50 dark:bg-slate-800/20 rounded-xl" />
      ) : (
        <div className="flex-1 w-full h-[280px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="currentColor" className="text-slate-200 dark:text-slate-700/50" />

              {/* Sentiment color bands — higher opacity in light mode for visibility */}
              <ReferenceArea y1={0.6}  y2={1}    fill="#22c55e" fillOpacity={isDark ? 0.07 : 0.14} />
              <ReferenceArea y1={0.2}  y2={0.6}  fill="#86efac" fillOpacity={isDark ? 0.06 : 0.12} />
              <ReferenceArea y1={-0.2} y2={0.2}  fill="#94a3b8" fillOpacity={isDark ? 0.05 : 0.08} />
              <ReferenceArea y1={-0.6} y2={-0.2} fill="#f59e0b" fillOpacity={isDark ? 0.06 : 0.13} />
              <ReferenceArea y1={-1}   y2={-0.6} fill="#ef4444" fillOpacity={isDark ? 0.07 : 0.14} />
              <XAxis 
                dataKey="date" 
                tickFormatter={formatXAxis} 
                axisLine={false} 
                tickLine={false} 
                tick={{ fontSize: 12 }} 
                className="text-slate-500 dark:text-slate-400"
                dy={10}
              />
              <YAxis 
                domain={[-1, 1]} 
                axisLine={false} 
                tickLine={false} 
                tick={{ fontSize: 12 }} 
                className="text-slate-500 dark:text-slate-400"
              />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1e293b', borderRadius: '8px', border: '1px solid #334155', color: '#f1f5f9', padding: '8px 12px' }}
                itemStyle={{ color: '#c7d2fe' }}
                labelStyle={{ color: '#94a3b8', marginBottom: 4, fontSize: 12 }}
                labelFormatter={(label) => new Date(label).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })}
                formatter={(value, name, props) => {
                  const count = props?.payload?.article_count;
                  const v = value ?? 0;
                  const label = v >= 0.6 ? 'Very Positive' : v >= 0.2 ? 'Positive' : v >= -0.2 ? 'Neutral' : v >= -0.6 ? 'Negative' : 'Very Negative';
                  return [
                    `${v.toFixed(4)} — ${label}  (${count} article${count !== 1 ? 's' : ''})`,
                    'Avg Sentiment'
                  ];
                }}
              />
              <ReferenceLine y={0} stroke="currentColor" className="text-slate-300 dark:text-slate-700" strokeDasharray="3 3"/>
              
              <Line 
                type="monotone" 
                dataKey="avg_sentiment" 
                stroke="#6366f1" 
                strokeWidth={3}
                dot={{ r: 4, fill: '#6366f1', strokeWidth: 2, stroke: '#fff' }}
                activeDot={{ r: 6, fill: '#4f46e5', stroke: '#fff' }}
                name="Sentiment"
              />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </GlassCard>
  );
}