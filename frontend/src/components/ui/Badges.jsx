// ui/Badges.jsx
import React from 'react';
import { cn } from './GlassCard';

export function SentimentBadge({ label, size = 'md' }) {
  const isPositive = label === 'positive';
  const isNegative = label === 'negative';
  
  const colors = isPositive 
    ? "bg-status-positive/10 text-status-positive border-status-positive/20" 
    : isNegative 
      ? "bg-status-negative/10 text-status-negative border-status-negative/20"
      : "bg-status-neutral/10 text-status-neutral border-status-neutral/20";
      
  return (
    <span className={cn(
      "inline-flex items-center justify-center font-medium border rounded-full capitalize",
      size === 'sm' ? "text-[10px] px-2 py-0.5" : "text-xs px-2.5 py-1",
      colors
    )}>
      {label}
    </span>
  );
}

export function TopicBadge({ label, size = 'md' }) {
  return (
    <span className={cn(
      "inline-flex items-center justify-center font-medium capitalize",
      "text-brand-accent bg-brand-accent/10 border border-brand-accent/20 rounded-md",
      size === 'sm' ? "text-[10px] px-1.5 py-0.5" : "text-xs px-2 py-1"
    )}>
      {label}
    </span>
  );
}