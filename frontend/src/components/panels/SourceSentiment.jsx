// panels/SourceSentiment.jsx
import React from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell } from 'recharts';
import { useApiData } from '../../hooks/useApiData';
import { GlassCard } from '../ui/GlassCard';

export default function SourceSentiment() {
  const { data: raw, loading } = useApiData('/sources/sentiment', { days: 7, limit: 10 }, { sources: [] });
  const data = raw?.sources || [];

  return (
    <GlassCard className="col-span-12 lg:col-span-3 h-[400px]" title="Source Bias Array">
      {loading ? (
        <div className="flex-1 flex items-center justify-center animate-pulse bg-slate-50/50 dark:bg-slate-800/20 rounded-xl" />
      ) : (
        <div className="flex-1 w-full relative">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart 
              data={data} 
              layout="vertical" 
              margin={{ top: 0, right: 10, left: -20, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="currentColor" className="text-slate-200 dark:text-slate-700/50" />
              <XAxis type="number" domain={[-1, 1]} hide />
              <YAxis 
                type="category" 
                dataKey="source_name" 
                axisLine={false} 
                tickLine={false} 
                tick={{ fontSize: 10 }}
                width={80}
                className="text-slate-600 dark:text-slate-300"
              />
              <Tooltip 
                cursor={{ fill: 'currentColor', opacity: 0.05 }}
                contentStyle={{ backgroundColor: '#1e293b', borderRadius: '8px', border: 'none', color: '#fff' }}
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