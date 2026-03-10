// panels/TopEntities.jsx
import React, { useState } from 'react';
import { useApiData } from '../../hooks/useApiData';
import { GlassCard } from '../ui/GlassCard';
import { Building2, MapPin, Target } from 'lucide-react';

export default function TopEntities() {
  const [days, setDays] = useState(7);
  // Default structure defined in data object
  const { data: raw, loading } = useApiData('/entities/top', { days, limit: 5 }, { organizations: [], locations: [], animals: [] });
  const data = raw || { organizations: [], locations: [], animals: [] };

  const ActionSelector = (
    <select 
      value={days} 
      onChange={(e) => setDays(Number(e.target.value))}
      className="text-xs bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md px-2 py-1 text-slate-700 dark:text-slate-300 outline-none"
    >
      <option value={7}>7 Days</option>
      <option value={30}>30 Days</option>
    </select>
  );

  const EntityList = ({ title, icon: Icon, items, colorClass }) => (
    <div className="flex-1 bg-slate-50/50 dark:bg-slate-800/30 rounded-xl p-4 border border-slate-100 dark:border-slate-700/30">
      <div className={`flex items-center gap-2 mb-3 text-sm font-semibold ${colorClass}`}>
        <Icon className="w-4 h-4" />
        {title}
      </div>
      <ul className="space-y-2">
        {items?.map((item, i) => (
          <li key={i} className="flex justify-between items-center text-sm group">
            <span className="text-slate-700 dark:text-slate-300 truncate pr-2 group-hover:text-brand-accent transition-colors">
              {item.name}
            </span>
            <span className="text-xs font-mono text-slate-400 bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded">
              {item.count}
            </span>
          </li>
        ))}
        {(!items || items.length === 0) && (
          <li className="text-xs text-slate-400 italic">No data</li>
        )}
      </ul>
    </div>
  );

  return (
    <GlassCard className="col-span-12 md:col-span-6 min-h-[300px]" title="Entity Extraction Target" action={ActionSelector}>
      {loading ? (
        <div className="flex gap-4 h-full">
          {[1,2,3].map(i => <div key={i} className="flex-1 bg-slate-100 dark:bg-slate-800/50 rounded-xl animate-pulse" />)}
        </div>
      ) : (
        <div className="flex flex-col sm:flex-row gap-4 h-full">
          <EntityList title="Organizations" icon={Building2} items={data.organizations} colorClass="text-indigo-500" />
          <EntityList title="Locations" icon={MapPin} items={data.locations} colorClass="text-emerald-500" />
          <EntityList title="Subjects" icon={Target} items={data.animals} colorClass="text-amber-500" />
        </div>
      )}
    </GlassCard>
  );
}