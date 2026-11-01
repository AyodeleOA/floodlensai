import { Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { LandingPage } from './features/landing/LandingPage';
import { MapPage } from './features/map/MapPage';
import { ReportPage } from './features/reports/ReportPage';
import { ReportReceiptPage } from './features/reports/ReportReceiptPage';
import { DashboardPage } from './features/dashboard/DashboardPage';
import { DashboardReportsPage } from './features/dashboard/DashboardReportsPage';
import { DashboardReportDetailPage } from './features/dashboard/DashboardReportDetailPage';
import { DashboardHotspotsPage } from './features/dashboard/DashboardHotspotsPage';
import { DashboardDataPage } from './features/dashboard/DashboardDataPage';
import { ModelStatusPage } from './features/model-status/ModelStatusPage';
import { MethodologyPage } from './features/methodology/MethodologyPage';
import { NotFoundPage } from './components/NotFoundPage';

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<LandingPage />} />
        <Route path="/map" element={<MapPage />} />
        <Route path="/report" element={<ReportPage />} />
        <Route path="/report/:id" element={<ReportReceiptPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/dashboard/reports" element={<DashboardReportsPage />} />
        <Route path="/dashboard/reports/:id" element={<DashboardReportDetailPage />} />
        <Route path="/dashboard/hotspots" element={<DashboardHotspotsPage />} />
        <Route path="/dashboard/data" element={<DashboardDataPage />} />
        <Route path="/dashboard/model-status" element={<ModelStatusPage />} />
        <Route path="/about/methodology" element={<MethodologyPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  );
}
