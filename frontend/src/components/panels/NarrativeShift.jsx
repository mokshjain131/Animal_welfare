// panels/NarrativeShift.jsx
import React, { useState } from 'react';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { useApiData } from '../../hooks/useApiData';
import { GlassCard } from '../ui/GlassCard';

const TOPIC_COLORS = {
  factory_farming: '#6366f1', // opacity heavy
  wildlife: '#818cf8',
  animal_testing: '#a5b4fc',
  pet_welfare: '#c7d2fe',
  animal_policy: '#e0e7ff',
  veganism: '#4f46e5',
};

export default function NarrativeShift() {
  const [days, setDays] = useState(14);
  const { data: raw, loading } = useApiData('/narrative/shifts', { days }, { dates: [], series: [] });
  const data = raw || { dates: [], series: [] };

  // Transform backend data { dates: [...], series: [{topic, data:[...] }] } 
  // into Recharts format: [{ date: '...', factory_farming: 10, wildlife: 5 }]
  const chartData = React.useMemo(() => {
    if (!data.dates || data.dates.length === 0) return [];
    return data.dates.map((date, idx) => {
      const point = { date };
      data.series.forEach(subj => {
        point[subj.topic] = subj.values[idx] || 0;
      });
      return point;
    });
  }, [data]);

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

  const formatXAxis = (tickItem) => new Date(tickItem).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });

  return (
    <GlassCard className="col-span-12 lg:col-span-8 min-h-[350px]" title="Narrative Shifts" action={ActionSelector}>
      {loading ? (
        <div className="flex-1 flex items-center justify-center animate-pulse bg-slate-50/50 dark:bg-slate-800/20 rounded-xl" />
      ) : (
        <div className="flex-1 w-full h-[280px]">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
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
                axisLine={false} 
                tickLine={false} 
                tick={{ fontSize: 12 }} 
                className="text-slate-500 dark:text-slate-400"
              />
              <Tooltip 
                contentStyle={{ backgroundColor: '#1e293b', borderRadius: '8px', border: 'none', color: '#fff' }}
                itemStyle={{ color: '#fff', textTransform: 'capitalize' }}
                labelFormatter={(label) => new Date(label).toLocaleDateString()}
              />
              
              {data.series && data.series.map((s) => (
                <Area 
                  key={s.topic}
                  type="monotone" 
                  dataKey={s.topic} 
                  stackId="1" 
                  stroke={TOPIC_COLORS[s.topic] || '#6366f1'} 
                  fill={TOPIC_COLORS[s.topic] || '#6366f1'} 
                  activeDot={{ r: 4 }}
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}
    </GlassCard>
  );
}