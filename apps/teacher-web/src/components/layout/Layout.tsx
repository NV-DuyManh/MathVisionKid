import { useState } from 'react';
import { Box } from '@mui/material';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Topbar from './Topbar';

export default function Layout() {
  const [navigationOpen, setNavigationOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(() => {
    try {
      return localStorage.getItem('mvk_teacher_sidebar') === 'collapsed';
    } catch {
      return false;
    }
  });

  const toggle = () => {
    setCollapsed((value) => {
      const next = !value;
      try {
        localStorage.setItem('mvk_teacher_sidebar', next ? 'collapsed' : 'expanded');
      } catch {
        // storage disabled
      }
      return next;
    });
  };

  return (
    <Box sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
      <a href="#workspace-main" className="skip-link">
        Đến nội dung chính
      </a>
      <Sidebar
        open={navigationOpen}
        onClose={() => setNavigationOpen(false)}
        collapsed={collapsed}
        onToggle={toggle}
      />
      <Box sx={{ flexGrow: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
        <Topbar onMenuClick={() => setNavigationOpen(true)} navigationOpen={navigationOpen} />
        <Box
          component="main"
          id="workspace-main"
          tabIndex={-1}
          className="workspace-content"
          sx={{ flexGrow: 1, p: { xs: 2, sm: 3, lg: 4 }, outline: 'none' }}
        >
          <Outlet />
        </Box>
      </Box>
    </Box>
  );
}
