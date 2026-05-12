import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import AppLayout from './components/AppLayout';
import ErrorBoundary from './components/ErrorBoundary';
import Overview from './pages/Overview';
import Architecture from './pages/Architecture';
import TryIt from './pages/TryIt';
import UseCases from './pages/UseCases';
import Operations from './pages/Operations';
import GovernanceAudit from './pages/GovernanceAudit';
import Overdrive from './pages/Overdrive';
import Docs from './pages/Docs';
import Tokenizer from './pages/Tokenizer';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: 1, staleTime: 30000 },
  },
});

export default function App() {
  return (
    <ErrorBoundary>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route index element={<Overview />} />
            <Route path="/architecture" element={<Architecture />} />
            <Route path="/try-it" element={<TryIt />} />
            <Route path="/use-cases" element={<UseCases />} />
            <Route path="/operations" element={<Operations />} />
            <Route path="/governance" element={<GovernanceAudit />} />
            <Route path="/overdrive" element={<Overdrive />} />
            <Route path="/tokenizer" element={<Tokenizer />} />
            <Route path="/docs" element={<Docs />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
    </ErrorBoundary>
  );
}
