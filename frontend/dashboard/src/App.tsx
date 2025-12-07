/**
 * Auto-SEO Dashboard Application
 */
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Components
import Layout from './components/layout/Layout';
import LoginForm from './components/auth/LoginForm';
import RegisterForm from './components/auth/RegisterForm';

// Pages
import Dashboard from './pages/Dashboard';
import Keywords from './pages/Keywords';
import Clustering from './pages/Clustering';
import ContentPlans from './pages/ContentPlans';
import Articles from './pages/Articles';
import Publishing from './pages/Publishing';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';
import SystemStatus from './pages/SystemStatus';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60, // 1 minute
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          {/* Auth routes */}
          <Route path="/login" element={<LoginForm />} />
          <Route path="/register" element={<RegisterForm />} />

          {/* Protected routes */}
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="keywords" element={<Keywords />} />
            <Route path="clustering" element={<Clustering />} />
            <Route path="content-plans" element={<ContentPlans />} />
            <Route path="articles" element={<Articles />} />
            <Route path="publishing" element={<Publishing />} />
            <Route path="analytics" element={<Analytics />} />
            <Route path="system-status" element={<SystemStatus />} />
            <Route path="settings" element={<Settings />} />
          </Route>

          {/* Catch all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
