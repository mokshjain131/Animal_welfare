// panels/SentimentTrend.jsx
import React, { useState } from 'react';
import { ResponsiveContainer, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ReferenceLine } from 'recharts';
import { useApiData } from '../../hooks/useApiData';
import { GlassCard } from '../ui/GlassCard';

export default function SentimentTrend() {
  const [days, setDays] = useState(7);
  const [topic, setTopic] = useState('');
  
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
    </div>
  );

  return (
    <GlassCard className="col-span-12 lg:col-span-8 min-h-[350px]" title="Average Sentiment Trend" action={ActionSelector}>
      {loading ? (
        <div className="flex-1 flex items-center justify-center animate-pulse bg-slate-50/50 dark:bg-slate-800/20 rounded-xl" />
      ) : (
        <div className="flex-1 w-full h-[280px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="currentColor" className="text-slate-200 dark:text-slate-700/50" />
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
                  return [
                    `${value?.toFixed(4)}  (${count} article${count !== 1 ? 's' : ''})`,
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