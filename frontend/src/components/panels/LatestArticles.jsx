// panels/LatestArticles.jsx
import React, { useState } from 'react';
import { useApiData } from '../../hooks/useApiData';
import { GlassCard } from '../ui/GlassCard';
import { SentimentBadge, TopicBadge } from '../ui/Badges';
import { ExternalLink, Clock } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

export default function LatestArticles() {
  const [topic, setTopic] = useState('');
  const [sentiment, setSentiment] = useState('');
  
  const { data: raw, loading } = useApiData('/articles/recent', { 
    topic: topic || undefined, 
    sentiment: sentiment || undefined,
    limit: 20
  }, { articles: [] });
  const articles = raw?.articles || [];

  const ActionSelector = (
    <div className="flex gap-2">
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
        value={sentiment} 
        onChange={(e) => setSentiment(e.target.value)}
        className="text-xs bg-slate-100 dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-md px-2 py-1 text-slate-700 dark:text-slate-300 outline-none"
      >
        <option value="">All Sentiment</option>
        <option value="positive">Positive</option>
        <option value="negative">Negative</option>
        <option value="neutral">Neutral</option>
      </select>
    </div>
  );

  return (
    <GlassCard className="col-span-12 lg:col-span-9 h-[500px]" title="Latest Recon" action={ActionSelector}>
      {loading ? (
        <div className="space-y-4 animate-pulse">
          {[1,2,3,4].map(i => <div key={i} className="h-16 bg-slate-100 dark:bg-slate-800/50 rounded-xl" />)}
        </div>
      ) : (
        <div className="flex-1 overflow-y-auto pr-2 space-y-3">
          {articles.map(article => (
            <div key={article.id} className="group relative flex items-start gap-4 p-4 rounded-xl bg-white/40 dark:bg-slate-800/30 hover:bg-white/60 dark:hover:bg-slate-800/60 border border-slate-200/50 dark:border-slate-700/50 transition-all">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                  <TopicBadge label={article.topic} size="sm" />
                  <SentimentBadge label={article.sentiment_label} size="sm" />
                  <span className="text-[10px] text-slate-500 font-medium bg-slate-100 dark:bg-slate-800 px-1.5 py-0.5 rounded ml-auto flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {formatDistanceToNow(new Date(article.published_at), { addSuffix: true })}
                  </span>
                </div>
                <h4 className="text-sm font-semibold text-slate-900 dark:text-white mb-1 line-clamp-1 group-hover:text-brand-accent transition-colors">
                  <a href={article.url} target="_blank" rel="noreferrer" className="after:absolute after:inset-0">
                    {article.title}
                  </a>
                </h4>
                <p className="text-xs text-slate-500 dark:text-slate-400 line-clamp-1">
                  <span className="font-medium mr-2">{article.source_name}</span>
                </p>
              </div>
              <div className="shrink-0 text-slate-400">
                <ExternalLink className="w-4 h-4" />
              </div>
            </div>
          ))}
        </div>
      )}
    </GlassCard>
  );
}