import { useState } from 'react';
import { Box } from '@mui/material';
import { Outlet } from 'react-router-dom';
import { AdminSidebar } from './AdminSidebar';
import { AdminNavigation } from './NavigationContext';

export const AdminLayout: React.FC = () => {
  const [navigationOpen, setNavigationOpen] = useState(false);
  return <AdminNavigation.Provider value={{ open: navigationOpen, show: () => setNavigationOpen(true) }}>
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
      <a href="#workspace-main" className="skip-link">Đến nội dung chính</a>
      <AdminSidebar open={navigationOpen} onClose={() => setNavigationOpen(false)} />
      <Box component="main" id="workspace-main" tabIndex={-1} sx={{ flexGrow: 1, minWidth: 0, outline: 'none' }}>
        <Outlet />
      </Box>
    </Box>
  </AdminNavigation.Provider>;
};
