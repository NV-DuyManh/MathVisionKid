import { useState } from 'react';
import { Box } from '@mui/material';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Topbar from './Topbar';

export default function Layout() {
  const [navigationOpen, setNavigationOpen] = useState(false);
  return <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
    <a href="#workspace-main" className="skip-link">Đến nội dung chính</a>
    <Sidebar open={navigationOpen} onClose={() => setNavigationOpen(false)} />
    <Box sx={{ flexGrow: 1, minWidth: 0 }}>
      <Topbar onMenuClick={() => setNavigationOpen(true)} navigationOpen={navigationOpen} />
      <Box component="main" id="workspace-main" tabIndex={-1} className="workspace-content" sx={{ p: { xs: 2, sm: 3, lg: 4 }, outline: 'none' }}>
        <Outlet />
      </Box>
    </Box>
  </Box>;
}
