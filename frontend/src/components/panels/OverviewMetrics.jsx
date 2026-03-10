// panels/OverviewMetrics.jsx
import React from 'react';
import { useApiData } from '../../hooks/useApiData';
import { GlassCard } from '../ui/GlassCard';
import { Activity, BarChart3, AlertTriangle, TrendingUp, TrendingDown, Layers, CheckCircle } from 'lucide-react';

export default function OverviewMetrics() {
  const { data: metrics, loading, error } = useApiData('/overview/metrics');

  if (loading) return <div className="animate-pulse h-32 glass-panel" />
  if (error || !metrics) return <div className="h-32 glass-panel border-state-negative/50 text-status-negative/80 flex items-center justify-center">Failed to load metrics</div>;

  const cards = [
    {
      label: 'Articles Today',
      value: metrics.articles_today.toLocaleString(),
      icon: Layers,
      color: 'text-brand-accent',
      bg: 'bg-brand-accent/10',
    },
    {
      label: 'Avg Sentiment',
      value: metrics.avg_sentiment !== null ? metrics.avg_sentiment.toFixed(2) : '-',
      subValue: metrics.avg_sentiment_label,
      subIcon: metrics.avg_sentiment_vs_yesterday > 0 ? TrendingUp : metrics.avg_sentiment_vs_yesterday < 0 ? TrendingDown : Activity,
      subColor: metrics.avg_sentiment_vs_yesterday > 0 ? 'text-status-positive' : metrics.avg_sentiment_vs_yesterday < 0 ? 'text-status-negative' : 'text-slate-400',
      icon: BarChart3,
      color: 'text-brand-light dark:text-brand-light',
      bg: 'bg-brand-light/10 dark:bg-brand-light/10',
    },
    {
      label: 'Active Topics',
      value: metrics.active_topics,
      icon: CheckCircle,
      color: 'text-brand-accent dark:text-brand-accent',
      bg: 'bg-brand-accent/10 dark:bg-brand-accent/10',
    },
    {
      label: 'Misinfo Alerts',
      value: metrics.misinfo_alerts,
      icon: AlertTriangle,
      color: metrics.misinfo_alerts > 0 ? 'text-status-negative' : 'text-brand-accent',
      bg: metrics.misinfo_alerts > 0 ? 'bg-status-negative/10 dark:bg-status-negative/20' : 'bg-brand-accent/10 dark:bg-brand-accent/10',
    }
  ];

  return (
    <div className="col-span-12 space-y-4">
      {metrics.active_spike && (
        <div className="flex items-center gap-3 p-4 bg-brand-accent/10 border border-brand-accent/30 rounded-lg shadow-sm backdrop-blur-md text-brand-accent dark:text-brand-light">
          <Activity className="w-5 h-5 animate-pulse" />
          <span className="font-semibold text-sm uppercase tracking-wide">Narrative Spike Detected:</span>
          <span className="text-sm font-medium">{metrics.active_spike.topic} ({metrics.active_spike.multiplier.toFixed(1)}x multiplier)</span>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {cards.map((c, i) => {
          const Icon = c.icon;
          const SubIcon = c.subIcon;
          return (
            <GlassCard key={i} className="flex flex-row items-center justify-between !p-5">
              <div>
                <p className="text-sm font-medium text-slate-500 dark:text-slate-400 mb-1">{c.label}</p>
                <div className="flex items-baseline gap-2">
                  <h4 className="text-3xl font-bold text-slate-800 dark:text-slate-100">{c.value}</h4>
                  {c.subValue && (
                    <span className={`text-xs font-semibold uppercase tracking-wider flex items-center gap-1 ${c.subColor}`}>
                      {SubIcon && <SubIcon className="w-3 h-3" />}
                      {c.subValue}
                    </span>
                  )}
                </div>
              </div>
              <div className={`p-3 rounded-xl ${c.bg}`}>
                <Icon className={`w-6 h-6 ${c.color}`} />
              </div>
            </GlassCard>
          );
        })}
      </div>
    </div>
  );
}