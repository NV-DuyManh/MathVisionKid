import { Box, Chip, Drawer, IconButton, List, ListItemButton, ListItemIcon, ListItemText, Tooltip, Typography, useMediaQuery, useTheme } from '@mui/material';
import { Dashboard, PeopleAlt, School, History, Analytics, Logout, Home } from '@mui/icons-material';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { appConfig } from '../../config/runtime';

const ITEMS = [
  { path: '/dashboard', label: 'Tổng quan', icon: <Dashboard /> },
  { path: '/recognition/analytics', label: 'Phân tích nhận dạng', icon: <Analytics /> },
  { path: '/users', label: 'Người dùng', icon: <PeopleAlt /> },
  { path: '/classes', label: 'Lớp học', icon: <School /> },
  { path: '/audit', label: 'Nhật ký hệ thống', icon: <History /> },
];
export const AdminSidebar: React.FC<{ open: boolean; onClose: () => void }> = ({ open, onClose }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const desktop = useMediaQuery(useTheme().breakpoints.up('md'));
  return <Drawer id="workspace-navigation" variant={desktop ? 'permanent' : 'temporary'} open={desktop || open} onClose={onClose}
    slotProps={{ paper: { 'aria-label': 'Điều hướng quản trị' } }}
    sx={{ width: { md: 248 }, flexShrink: 0, '& .MuiDrawer-paper': { width: 248, boxSizing: 'border-box', bgcolor: 'background.paper', borderRight: '1px solid', borderColor: 'divider' } }}>
    <Box sx={{ p: 3, pb: 2.5 }}>
      <Typography component="div" sx={{ fontWeight: 900, fontSize: 23, letterSpacing: '-.8px' }}>MathVision<span style={{ color: '#7040D5' }}>Kids</span></Typography>
      <Chip label="CỔNG QUẢN TRỊ" size="small" sx={{ mt: 1.2, height: 23, bgcolor: 'primary.light', color: 'primary.dark', fontSize: 10, letterSpacing: '.06em' }} />
    </Box>
    <Box component="nav" aria-label="Điều hướng quản trị" sx={{ px: 2, py: 1.5, flexGrow: 1 }}>
      <List disablePadding>{ITEMS.map(item => {
        const active = location.pathname.startsWith(item.path);
        return <ListItemButton key={item.path} selected={active} aria-current={active ? 'page' : undefined}
          onClick={() => { navigate(item.path); onClose(); }} sx={{ mb: .7, px: 1.7, minHeight: 50 }}>
          <ListItemIcon sx={{ minWidth: 36, color: active ? 'primary.main' : 'text.secondary', '& svg': { fontSize: 21 } }}>{item.icon}</ListItemIcon>
          <ListItemText primary={item.label} slotProps={{ primary: { sx: { fontSize: '.92rem', fontWeight: active ? 800 : 600 } } }} />
        </ListItemButton>;
      })}</List>
    </Box>
    <Box sx={{ px: 2, py: 1.5, borderTop: '1px solid', borderColor: 'divider' }}>
      <ListItemButton component="a" href={appConfig.portalOrigin}>
        <ListItemIcon sx={{ minWidth: 32, color: 'text.secondary' }}><Home fontSize="small" /></ListItemIcon>
        <ListItemText primary="Trang chủ MathVision Kids" slotProps={{ primary: { sx: { fontSize: '.8rem', fontWeight: 700 } } }} />
      </ListItemButton>
      <Box sx={{ mt: 1.5, px: 1, py: 1.5, display: 'flex', alignItems: 'center', gap: .5, bgcolor: '#F8F5FC', borderRadius: 2 }}>
        <Box sx={{ minWidth: 0, flexGrow: 1 }}>
          <Typography variant="body2" noWrap sx={{ fontWeight: 800 }}>{user?.displayName || 'Quản trị viên'}</Typography>
          <Typography variant="caption" sx={{ display: 'block', color: 'text.secondary', overflowWrap: 'anywhere' }}>{user?.email || ''}</Typography>
        </Box>
        <Tooltip title="Đăng xuất"><IconButton aria-label="Đăng xuất" onClick={async () => { await logout(); }} sx={{ color: 'text.secondary' }}><Logout fontSize="small" /></IconButton></Tooltip>
      </Box>
    </Box>
  </Drawer>;
};
