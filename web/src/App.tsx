import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Header } from './components/Layout/Header';
import { Sidebar } from './components/Layout/Sidebar';
import { Dashboard } from './pages/Dashboard';
import { Upload } from './pages/Upload';
import { Profiles } from './pages/Profiles';
import { ApprovalQueue } from './pages/ApprovalQueue';
import { History } from './pages/History';
import { Stats } from './pages/Stats';
import Keywords from './pages/Keywords';
import Search from './pages/Search';
import AnalyticsEnhanced from './pages/AnalyticsEnhanced';
import PYLIDCIntegration from './pages/PYLIDCIntegration';
import Documents from './pages/Documents';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50">
          <Header />
          <div className="flex">
            <Sidebar />
            <main className="flex-1">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/upload" element={<Upload />} />
                <Route path="/profiles" element={<Profiles />} />
                <Route path="/approval-queue" element={<ApprovalQueue />} />
                <Route path="/history" element={<History />} />
                <Route path="/stats" element={<Stats />} />
                <Route path="/analytics" element={<AnalyticsEnhanced />} />
                <Route path="/keywords" element={<Keywords />} />
                <Route path="/search" element={<Search />} />
                <Route path="/pylidc" element={<PYLIDCIntegration />} />
                <Route path="/documents" element={<Documents />} />
                <Route path="/3d-viz" element={<div className="p-8">3D Visualization (Coming Soon)</div>} />
                <Route path="/export" element={<div className="p-8">Export (Coming Soon)</div>} />
              </Routes>
            </main>
          </div>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
