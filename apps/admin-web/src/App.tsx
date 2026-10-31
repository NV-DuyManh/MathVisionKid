import { Routes, Route, Navigate } from 'react-router-dom';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { UsersPage } from './pages/UsersPage';
import { UserDetailPage } from './pages/UserDetailPage';
import { ClassesPage } from './pages/ClassesPage';
import { ClassDetailPage } from './pages/ClassDetailPage';
import { AuditPage } from './pages/AuditPage';
import { RecognitionAnalyticsPage } from './pages/RecognitionAnalyticsPage';
import { StatusPage } from './pages/StatusPage';
import { AdminLayout } from './components/layout/AdminLayout';
import { ProtectedRoute } from './components/common/ProtectedRoute';
export function App() {
  return <Routes>
    <Route path="/login" element={<LoginPage />} />
    <Route path="/403" element={<StatusPage code="403" />} />
    <Route path="/session-expired" element={<StatusPage code="expired" />} />
    <Route path="/" element={<ProtectedRoute><AdminLayout /></ProtectedRoute>}>
      <Route index element={<Navigate to="/dashboard" replace />} />
      <Route path="admin" element={<Navigate to="/dashboard" replace />} />
      <Route path="dashboard" element={<DashboardPage />} />
      <Route path="users" element={<UsersPage />} />
      <Route path="users/:userId" element={<UserDetailPage />} />
      <Route path="classes" element={<ClassesPage />} />
      <Route path="classes/:classId" element={<ClassDetailPage />} />
      <Route path="audit" element={<AuditPage />} />
      <Route path="recognition/analytics" element={<RecognitionAnalyticsPage />} />
      <Route path="*" element={<StatusPage />} />
    </Route>
  </Routes>;
}
