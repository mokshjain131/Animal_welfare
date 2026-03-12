// ui/Header.jsx
import React, { useEffect, useState } from 'react';
import { Moon, Sun } from 'lucide-react';
import logoUrl from '/logo.svg';

export default function Header() {
  const [theme, setTheme] = useState(() => 
    window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  );

  useEffect(() => {
    if (theme === 'dark') document.documentElement.classList.add('dark');
    else document.documentElement.classList.remove('dark');
  }, [theme]);

  const toggleTheme = () => setTheme(prev => prev === 'light' ? 'dark' : 'light');

  return (
    <header className="fixed top-0 w-full z-50 glass-panel !rounded-none !border-t-0 !border-x-0 bg-white/50 dark:bg-slate-900/60 flex items-center justify-between px-6 py-4">
      <div className="flex items-center gap-3 text-brand-accent dark:text-brand-light">
        <img src={logoUrl} alt="Animal Action Intel" className="w-8 h-8 rounded-lg" />
        <h1 className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
          Animal Action Intel
        </h1>
        <span className="bg-brand-accent/10 text-brand-accent dark:text-brand-light text-xs font-semibold px-2 py-0.5 rounded-full uppercase tracking-wide border border-brand-accent/20">
          Terminal
        </span>
      </div>
      <div>
        <button
          onClick={toggleTheme}
          className="p-2 rounded-full hover:bg-slate-200 dark:hover:bg-slate-800 transition-colors text-slate-600 dark:text-slate-300"
          aria-label="Toggle Theme"
        >
          {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </button>
      </div>
    </header>
  );
}