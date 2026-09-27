import React from 'react';
import { Header } from './Header';
import { Sidebar } from './Sidebar';
import { ToastContainer } from '@/components/common/ToastContainer';

export const AppShell: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <Header />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 p-8 overflow-y-auto max-w-7xl mx-auto w-full">
          {children}
        </main>
      </div>
      <ToastContainer />
    </div>
  );
};
