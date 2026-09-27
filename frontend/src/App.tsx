import React from 'react';
import { AuthProvider } from '@/app/providers/AuthProvider';
import { ToastProvider } from '@/app/providers/ToastProvider';
import { AppRouter } from '@/app/router/AppRouter';

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <ToastProvider>
        <AppRouter />
      </ToastProvider>
    </AuthProvider>
  );
};

export default App;
