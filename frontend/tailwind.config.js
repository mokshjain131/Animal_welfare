/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        background: {
          light: '#f8fafc', // slate-50
          dark: '#0f172a',  // slate-900
        },
        surface: {
          light: 'rgba(255, 255, 255, 0.7)',
          dark: 'rgba(30, 41, 59, 0.5)', // slate-800 with opacity
        },
        borderBase: {
          light: 'rgba(255, 255, 255, 0.2)',
          dark: 'rgba(51, 65, 85, 0.5)', // slate-700
        },
        brand: {
          accent: '#6366f1', // indigo-500
          light: '#818cf8',  // indigo-400
          dark: '#4f46e5',   // indigo-600
        },
        status: {
          positive: '#34d399', // emerald-400
          negative: '#fb7185', // rose-400
          neutral: '#94a3b8',  // slate-400
        }
      },
    },
  },
  plugins: [],
}