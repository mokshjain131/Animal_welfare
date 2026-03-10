// ui/GlassCard.jsx
import React from 'react';
import { clsx, clsx as cx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs) {
  return twMerge(cx(inputs));
}

export function GlassCard({ children, className, title, action }) {
  return (
    <div className={cn("glass-panel flex flex-col", className)}>
      {(title || action) && (
        <div className="flex items-center justify-between mb-4">
          {title && <h3 className="text-lg font-semibold text-slate-800 dark:text-slate-100">{title}</h3>}
          {action && <div>{action}</div>}
        </div>
      )}
      <div className="flex-1 flex flex-col min-h-0">
        {children}
      </div>
    </div>
  );
}
