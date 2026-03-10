// panels/MisinfoAlerts.jsx
import React from 'react';
import { useApiData } from '../../hooks/useApiData';
import { GlassCard } from '../ui/GlassCard';
import { AlertCircle, ExternalLink } from 'lucide-react';
import { TopicBadge } from '../ui/Badges';

export default function MisinfoAlerts() {
  const { data: raw, loading } = useApiData('/articles/flagged', { limit: 5 }, { articles: [] });
  const alerts = raw?.articles || [];

  return (
    <GlassCard className="col-span-12 lg:col-span-4 min-h-[350px]" title="Misinfo Alerts">
      {loading ? (
        <div className="flex-1 space-y-3">
          {[1, 2, 3].map(i => <div key={i} className="h-16 bg-slate-100 dark:bg-slate-800/50 animate-pulse rounded-lg" />)}
        </div>
      ) : alerts.length === 0 ? (
        <div className="flex-1 flex flex-col items-center justify-center text-slate-400">
          <AlertCircle className="w-10 h-10 mb-2 opacity-50" />
          <p className="text-sm">No recent alerts</p>
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto space-y-3 pr-2 border-slate-100 dark:border-slate-800">
          {alerts.map((alert) => (
            <div key={alert.id} className="p-3 bg-white/40 dark:bg-slate-800/40 border border-status-negative/20 rounded-xl hover:border-status-negative/40 transition-colors">
              <div className="flex justify-between items-start mb-2">
                <TopicBadge label={alert.topic} size="sm" />
                <span className="text-[10px] text-slate-500 font-medium">Score: {(alert.suspicion_score * 100).toFixed(0)}%</span>
              </div>
              <h4 className="text-sm font-semibold text-slate-800 dark:text-slate-200 line-clamp-2 mb-2 leading-snug">
                {alert.title}
              </h4>
              <div className="flex items-center justify-between mt-2">
                <span className="text-[10px] text-status-negative bg-status-negative/10 px-2 py-0.5 rounded uppercase tracking-wider font-semibold truncate max-w-[150px]">
                  {alert.flag_reason}
                </span>
                <a href={alert.url} target="_blank" rel="noreferrer" className="text-brand-accent hover:text-brand-light flex items-center gap-1 text-[10px] font-medium transition-colors">
                  Review <ExternalLink className="w-3 h-3" />
                </a>
              </div>
            </div>
          ))}
        </div>
      )}
    </GlassCard>
  );
}