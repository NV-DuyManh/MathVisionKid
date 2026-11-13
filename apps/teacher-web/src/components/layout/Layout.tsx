import { useEffect, useRef, useState } from 'react';
import { Box } from '@mui/material';
import { Outlet } from 'react-router-dom';
import Sidebar from './Sidebar';
import Topbar from './Topbar';

export default function Layout() {
  const [navigationOpen, setNavigationOpen] = useState(false);
  const [uploadDraftActive, setUploadDraftActive] = useState(false);
  const leavingForLogout = useRef(false);
  useEffect(() => {
    if (!uploadDraftActive) return;
    const warnBeforeUnload = (event: BeforeUnloadEvent) => {
      if (leavingForLogout.current) return;
      event.preventDefault();
      event.returnValue = '';
    };
    window.addEventListener('beforeunload', warnBeforeUnload);
    return () => window.removeEventListener('beforeunload', warnBeforeUnload);
  }, [uploadDraftActive]);
  const confirmLogout = () => {
    if (uploadDraftActive && !window.confirm('Ảnh đang chuẩn bị sẽ bị mất khi đăng xuất. Bạn có muốn tiếp tục?')) return false;
    leavingForLogout.current = true;
    return true;
  };
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
    <Box className="teacher-workspace" sx={{ display: 'flex', minHeight: '100vh', bgcolor: 'background.default' }}>
      <a href="#workspace-main" className="skip-link" onClick={event => {
        event.preventDefault();
        document.getElementById('workspace-main')?.focus();
      }}>
        Đến nội dung chính
      </a>
      <Sidebar
        open={navigationOpen}
        onClose={() => setNavigationOpen(false)}
        collapsed={collapsed}
        onToggle={toggle}
      />
      <Box sx={{ flexGrow: 1, minWidth: 0, display: 'flex', flexDirection: 'column' }}>
        <Topbar onMenuClick={() => setNavigationOpen(true)} navigationOpen={navigationOpen}
          confirmLogout={confirmLogout} />
        <Box
          component="main"
          id="workspace-main"
          tabIndex={-1}
          className="workspace-content"
          sx={{ flexGrow: 1, p: { xs: 1.5, sm: 3, lg: 4 }, minWidth: 0, outline: 'none' }}
        >
          <Outlet context={{ setUploadDraftActive }} />
        </Box>
      </Box>
    </Box>
  );
}
