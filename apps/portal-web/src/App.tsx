import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { PortalLayout } from './components/layout/PortalLayout';
import { LoginPage } from './pages/LoginPage';
import { StudentLandingPage } from './pages/StudentLandingPage';
import { TeacherEntryPage } from './pages/TeacherEntryPage';
import { AdminEntryPage } from './pages/AdminEntryPage';
import { AccessDeniedPage } from './pages/AccessDeniedPage';
import { SessionExpiredPage } from './pages/SessionExpiredPage';
import { LogoutPage } from './pages/LogoutPage';

const DevRuntimePage = import.meta.env.DEV && import.meta.env.VITE_SHOW_DEV_TOOLS === 'true'
  ? React.lazy(() => import('./pages/DevRuntimePage').then((page) => ({ default: page.DevRuntimePage })))
  : null;

export const App: React.FC = () => {
  return (
    <Routes>
      <Route path="/" element={<PortalLayout />}>
        <Route index element={<LoginPage />} />
        <Route path="login" element={<LoginPage />} />
        <Route path="student" element={<StudentLandingPage />} />
        <Route path="teacher" element={<TeacherEntryPage />} />
        <Route path="teacher-entry" element={<TeacherEntryPage />} />
        <Route path="admin" element={<AdminEntryPage />} />
        <Route path="admin-entry" element={<AdminEntryPage />} />
        <Route path="logout" element={<LogoutPage />} />
        <Route path="dev/mobile" element={DevRuntimePage ? <React.Suspense fallback={null}><DevRuntimePage /></React.Suspense> : <Navigate to="/" replace />} />
        <Route path="dev/runtime" element={DevRuntimePage ? <React.Suspense fallback={null}><DevRuntimePage /></React.Suspense> : <Navigate to="/" replace />} />
        <Route path="access-denied" element={<AccessDeniedPage />} />
        <Route path="session-expired" element={<SessionExpiredPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
};

export default App;
