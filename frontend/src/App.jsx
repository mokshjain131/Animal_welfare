import React from 'react';
import Header from './components/ui/Header';
import Dashboard from './components/Dashboard';

function App() {
  return (
    <div className="min-h-screen">
      <Header />
      <main>
        <Dashboard />
      </main>
    </div>
  );
}

export default App;
