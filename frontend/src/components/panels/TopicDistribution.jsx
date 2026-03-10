// panels/TopicDistribution.jsx
import React, { useState } from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Cell } from 'recharts';
import { useApiData } from '../../hooks/useApiData';
import { GlassCard } from '../ui/GlassCard';

export default function TopicDistribution() {
  const [days, setDays] = useState(7);
  const { data: raw, loading } = useApiData('/topics/volume', { days }, { data: [] });
  const data = raw?.data || [];

  const ActionSelector = (
    <select 
      value={days} 
      onChange={(e) => setDays(Number(e.target.value))}
      className="text-xs bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md px-2 py-1 text-slate-700 dark:text-slate-300 outline-none"
    >
      <option value={7}>7 Days</option>
      <option value={14}>14 Days</option>
      <option value={30}>30 Days</option>
    </select>
  );

  return (
    <GlassCard className="col-span-12 lg:col-span-4 min-h-[350px]" title="Topic Volume" action={ActionSelector}>
      {loading ? (
        <div className="flex-1 flex items-center justify-center animate-pulse bg-slate-50/50 dark:bg-slate-800/20 rounded-xl" />
      ) : (
        <div className="flex-1 w-full h-[280px]">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart 
              data={data} 
              layout="vertical" 
              margin={{ top: 0, right: 10, left: 10, bottom: 0 }}
            >
              <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="currentColor" className="text-slate-200 dark:text-slate-700/50" />
              <XAxis type="number" hide />
              <YAxis 
                type="category" 
                dataKey="topic" 
                axisLine={false} 
                tickLine={false} 
                tick={{ fontSize: 11 }}
                width={100}
                className="text-slate-600 dark:text-slate-300 capitalize"
                tickFormatter={(val) => val.replace('_', ' ')}
              />
              <Tooltip 
                cursor={{ fill: 'currentColor', opacity: 0.05 }}
                contentStyle={{ backgroundColor: '#1e293b', borderRadius: '8px', border: 'none', color: '#fff' }}
              />
              <Bar dataKey="article_count" radius={[0, 4, 4, 0]} maxBarSize={30}>
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill="#6366f1" fillOpacity={1 - (index * 0.15)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </GlassCard>
  );
}