import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppLayout } from './components/layout/AppLayout';
import { DashboardPage } from './pages/DashboardPage';
import { ResumesPage } from './pages/ResumesPage';
import { JobsPage } from './pages/JobsPage';
import { MatchPage } from './pages/MatchPage';
import { TailorPage } from './pages/TailorPage';
import { ApplicationsPage } from './pages/ApplicationsPage';
import { ApplicationReviewPage } from './pages/ApplicationReviewPage';
import { SettingsPage } from './pages/SettingsPage';

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="resumes" element={<ResumesPage />} />
          <Route path="jobs" element={<JobsPage />} />
          <Route path="match" element={<MatchPage />} />
          <Route path="tailor" element={<TailorPage />} />
          <Route path="applications" element={<ApplicationsPage />} />
          <Route path="applications/:id/review" element={<ApplicationReviewPage />} />
          <Route path="settings" element={<SettingsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
