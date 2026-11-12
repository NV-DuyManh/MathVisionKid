import { createBrowserRouter, createRoutesFromElements, RouterProvider, Outlet, Route, Navigate } from 'react-router-dom';
import Layout from './components/layout/Layout';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import ClassesPage from './pages/ClassesPage';
import ClassDetailPage from './pages/ClassDetailPage';
import AssignmentsPage from './pages/AssignmentsPage';
import AssignmentCreatePage from './pages/AssignmentCreatePage';
import BatchesPage from './pages/BatchesPage';
import BatchCreatePage from './pages/BatchCreatePage';
import BatchDetailPage from './pages/BatchDetailPage';
import ReviewQueuePage from './pages/ReviewQueuePage';
import SubmissionReviewPage from './pages/SubmissionReviewPage';
import SettingsPage from './pages/SettingsPage';
import { AuthProvider } from './components/layout/AuthContext';

const router = createBrowserRouter(createRoutesFromElements(
  <Route element={<AuthProvider><Outlet /></AuthProvider>}>
          <Route path="/login" element={<LoginPage />} />
          
          <Route path="/" element={<Layout />}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="classes" element={<ClassesPage />} />
            <Route path="classes/:id" element={<ClassDetailPage />} />
            <Route path="assignments" element={<AssignmentsPage />} />
            <Route path="assignments/create" element={<AssignmentCreatePage />} />
            <Route path="batches" element={<BatchesPage />} />
            <Route path="batches/create" element={<BatchCreatePage />} />
            <Route path="batches/:id" element={<BatchDetailPage />} />
            <Route path="batches/:id/review" element={<ReviewQueuePage />} />
            <Route path="submissions/:id" element={<SubmissionReviewPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Route>
  </Route>
));

function App() {
  return <RouterProvider router={router} />;
}

export default App;
