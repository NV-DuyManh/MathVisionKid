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
import { DevRuntimePage } from './pages/DevRuntimePage';

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
        <Route path="dev/mobile" element={<DevRuntimePage />} />
        <Route path="dev/runtime" element={<DevRuntimePage />} />
        <Route path="access-denied" element={<AccessDeniedPage />} />
        <Route path="session-expired" element={<SessionExpiredPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
};

export default App;
