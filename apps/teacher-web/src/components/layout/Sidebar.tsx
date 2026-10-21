import { Box, Chip, Drawer, List, ListItemButton, ListItemIcon, ListItemText, Typography, useMediaQuery, useTheme } from '@mui/material';
import { Dashboard, School, Assignment, FactCheck, Settings, Home } from '@mui/icons-material';
import { useLocation, useNavigate } from 'react-router-dom';
import { appConfig } from '../../config/runtime';

const ITEMS = [
  { text: 'Tổng quan', icon: <Dashboard />, path: '/dashboard' },
  { text: 'Lớp học', icon: <School />, path: '/classes' },
  { text: 'Bài tập', icon: <Assignment />, path: '/assignments' },
  { text: 'Đợt chấm', icon: <FactCheck />, path: '/batches' },
  { text: 'Cài đặt', icon: <Settings />, path: '/settings' },
];
export default function Sidebar({ open, onClose }: { open: boolean; onClose: () => void }) {
  const location = useLocation();
  const navigate = useNavigate();
  const desktop = useMediaQuery(useTheme().breakpoints.up('md'));
  return <Drawer id="workspace-navigation" variant={desktop ? 'permanent' : 'temporary'} open={desktop || open} onClose={onClose}
    slotProps={{ paper: { 'aria-label': 'Điều hướng giáo viên' } }}
    sx={{ width: { md: 248 }, flexShrink: 0, '& .MuiDrawer-paper': { width: 248, boxSizing: 'border-box', borderRight: '1px solid', borderColor: 'divider', bgcolor: 'background.paper' } }}>
    <Box sx={{ p: 3, pb: 2.5 }}>
      <Typography component="div" sx={{ fontWeight: 900, fontSize: 23, letterSpacing: '-.8px', color: 'text.primary' }}>MathVision<span style={{ color: '#7040D5' }}>Kids</span></Typography>
      <Chip label="CỔNG GIÁO VIÊN" size="small" sx={{ mt: 1.2, height: 23, bgcolor: 'primary.light', color: 'primary.dark', fontSize: 10, letterSpacing: '.06em' }} />
    </Box>
    <Box component="nav" aria-label="Điều hướng giáo viên" sx={{ px: 2, py: 1.5, flexGrow: 1 }}>
      <List disablePadding>
        {ITEMS.map(item => {
          const active = location.pathname.startsWith(item.path);
          return <ListItemButton key={item.path} selected={active} aria-current={active ? 'page' : undefined}
            onClick={() => { navigate(item.path); onClose(); }} sx={{ mb: .7, px: 1.7, minHeight: 50 }}>
            <ListItemIcon sx={{ minWidth: 36, color: active ? 'primary.main' : 'text.secondary', '& svg': { fontSize: 21 } }}>{item.icon}</ListItemIcon>
            <ListItemText primary={item.text} slotProps={{ primary: { sx: { fontWeight: active ? 800 : 600, fontSize: '.92rem' } } }} />
          </ListItemButton>;
        })}
      </List>
    </Box>
    <Box sx={{ p: 2, borderTop: '1px solid', borderColor: 'divider' }}>
      <ListItemButton component="a" href={appConfig.portalOrigin} sx={{ minHeight: 48 }}>
        <ListItemIcon sx={{ minWidth: 32, color: 'text.secondary' }}><Home fontSize="small" /></ListItemIcon>
        <ListItemText primary="Trang chủ MathVision Kids" slotProps={{ primary: { sx: { fontSize: '.8rem', fontWeight: 700 } } }} />
      </ListItemButton>
    </Box>
  </Drawer>;
}
