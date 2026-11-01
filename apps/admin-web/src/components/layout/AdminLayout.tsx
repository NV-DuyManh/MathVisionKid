import { useState } from 'react';
import { Box } from '@mui/material';
import { Outlet } from 'react-router-dom';
import { AdminSidebar } from './AdminSidebar';
import { AdminNavigation } from './NavigationContext';
export const AdminLayout = () => {
  const [open, setOpen] = useState(false);
  const [collapsed, setCollapsed] = useState(() => localStorage.getItem('mvk_admin_sidebar') === 'collapsed');
  const toggle = () => setCollapsed(value => {
    localStorage.setItem('mvk_admin_sidebar', value ? 'expanded' : 'collapsed');
    return !value;
  });
  return <AdminNavigation.Provider value={{ open, show: () => setOpen(true) }}>
    <Box sx={{ display: 'flex', minHeight: '100dvh' }}>
      <a href="#workspace-main" className="skip-link">Đến nội dung chính</a>
      <AdminSidebar open={open} onClose={() => setOpen(false)} collapsed={collapsed} onToggle={toggle} />
      <Box component="main" id="workspace-main" tabIndex={-1} sx={{ flex: 1, minWidth: 0, outline: 'none' }}><Outlet /></Box>
    </Box>
  </AdminNavigation.Provider>;
};
